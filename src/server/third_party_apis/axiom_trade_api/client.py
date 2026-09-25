from typing import Any, Awaitable, Callable, List, Literal, Optional, TypeVar
from collections import Counter
import logging
import asyncio
import time

from .auth import AuthManager
from .agent_selector import AgentSelector
from .request_pacer import AxiomRequestPacer
from .models import *
from .endpoints import *
from .endpoints.exceptions import (
    AxiomHTTPStatusError,
    AxiomRequestError,
    AxiomWebSocketError,
)


logger = logging.getLogger(__name__)
ResponseModelT = TypeVar("ResponseModelT")


class AxiomTradeClient:
    def __init__(
            self,
            agents: List[AxiomAgentData],
            ):
        self._auth_manager = AuthManager()
        self._agent_selector = AgentSelector()
        self._request_pacer = AxiomRequestPacer()
        self._http_attempts: Counter[str] = Counter()
        self._http_rate_limits: Counter[str] = Counter()
        self._endpoints = AxiomTradeEndpoints(
            self._auth_manager
        )
        self._wsocket = AxiomTradeWebsocket(
            self._auth_manager,
            self._endpoints
        )
        self._ws_task: Optional[asyncio.Task[Any]] = None

        self.add_agents(agents=agents)

    def add_agents(self, agents: List[AxiomAgentData]) -> None:
        self._agent_selector.add_agents(agents)

    def connect_websocket(
        self,
        rooms: List[Literal["new_pairs", "sol_price", "migrations"]] = \
            ["new_pairs", "sol_price", "migrations"]
    ) -> None:
        """Connect to WebSocket and run stream in background"""
        if self._ws_task is not None and not self._ws_task.done():
            logger.debug("Axiom WebSocket task is already running")
            return

        random_session_and_agent = self._agent_selector.random_websocket_agent()

        self._ws_task = asyncio.create_task(
            self._wsocket.start(
                session_and_agent=random_session_and_agent, 
                rooms=rooms
                )
        )
        self._ws_task.add_done_callback(self._handle_websocket_task_done)

    @staticmethod
    def _handle_websocket_task_done(task: asyncio.Task[Any]) -> None:
        """Retrieve background errors so asyncio never reports an orphan task."""
        if task.cancelled():
            return

        try:
            exception = task.exception()
        except asyncio.CancelledError:
            return

        if exception is not None:
            logger.error(
                "Axiom WebSocket background task stopped: %s",
                exception,
                exc_info=(
                    type(exception),
                    exception,
                    exception.__traceback__,
                ),
            )

    async def ensure_validation(self):
        sessions_and_agents = self._agent_selector.get_agents_and_sessions()

        for session_and_agent in sessions_and_agents:
            await self._auth_manager.ensure_validation(session_and_agent)

    def on_sol_price(self, callback: Callable[[Any], Any]) -> None:
        """Register callback for SOL price updates"""
        self._wsocket.register_callback("sol_price", callback)

    def on_new_pairs(self, callback: Callable[[Any], Any]) -> None:
        """Register callback for new pairs response messages"""
        self._wsocket.register_callback("new_pairs", callback)

    async def _call_with_random_agent(
        self,
        endpoint_method: Callable[..., Awaitable[Optional[ResponseModelT]]],
        **kwargs: Any,
    ) -> Optional[ResponseModelT]:
        max_attempts = min(max(self._agent_selector.route_count, 2), 3)
        endpoint_name = endpoint_method.__name__
        excluded_routes: set[str] = set()
        retry_deadline = time.monotonic() + 120.0
        last_retry_error: AxiomHTTPStatusError | AxiomRequestError | None = None

        for attempt in range(max_attempts):
            session_and_agent = self._agent_selector.acquire_agent(
                excluded_routes=excluded_routes
            )

            if session_and_agent is None:
                # Every unused route is cooling down. Once all routes have
                # been tried, allow the quickest one to recover for a retry.
                excluded_routes.clear()
                while session_and_agent is None:
                    delay = self._agent_selector.next_available_delay()
                    remaining = retry_deadline - time.monotonic()
                    if remaining <= 0:
                        if last_retry_error is not None:
                            raise last_retry_error
                        raise TimeoutError("No Axiom route became available")
                    await asyncio.sleep(min(max(delay, 0.01), remaining))
                    session_and_agent = self._agent_selector.acquire_agent()

            try:
                await self._request_pacer.wait_turn()
                try:
                    self._http_attempts[endpoint_name] += 1
                    request_count = sum(self._http_attempts.values())
                    if request_count % 25 == 0:
                        pending, oldest_age = self._request_pacer.queue_stats()
                        rate_limited_count = sum(self._http_rate_limits.values())
                        logger.info(
                            "Axiom HTTP diagnostics: attempts=%s 429=%s "
                            "rate_limited=%.1f%% "
                            "pending=%s oldest_wait=%.3fs",
                            dict(self._http_attempts),
                            dict(self._http_rate_limits),
                            rate_limited_count / request_count * 100,
                            pending, oldest_age,
                        )
                    return await endpoint_method(
                        session_and_agent=session_and_agent,
                        **kwargs,
                    )
                finally:
                    self._request_pacer.release_turn()
            except AxiomHTTPStatusError as exc:
                if exc.status_code != 429:
                    raise

                self._agent_selector.mark_rate_limited(
                    session_and_agent,
                    retry_after=exc.retry_after,
                )
                self._http_rate_limits[endpoint_name] += 1
                last_retry_error = exc
                if attempt == max_attempts - 1:
                    raise

                excluded_routes.add(
                    self._agent_selector.route_key(session_and_agent)
                )
                logger.warning(
                    "%s rate limited; retrying via another proxy route",
                    session_and_agent[1].agent_name,
                )
            except AxiomRequestError as exc:
                self._agent_selector.mark_unavailable(session_and_agent)
                last_retry_error = exc
                if attempt == max_attempts - 1:
                    raise

                excluded_routes.add(
                    self._agent_selector.route_key(session_and_agent)
                )
                logger.warning(
                    "%s request failed; retrying via another proxy route",
                    session_and_agent[1].agent_name,
                )
            finally:
                self._agent_selector.release_agent(session_and_agent)

        raise RuntimeError("unreachable")

    async def pair_chart_v2(
        self,
        pair_address: str,
        chart_from: int,
        chart_to: int
    ) -> Optional[PairChartV2Response]:
        """Get chart data for a pair"""
        pair_chart_v2_params = PairChartV2Params(
            pair_address=pair_address,
            chart_from=chart_from,
            chart_to=chart_to
        )
        
        return await self._call_with_random_agent(
            self._endpoints.pair_chart_v2,
            pair_chart_v2_params=pair_chart_v2_params
        )
    
    async def dev_tokens_v3(
        self,
        dev_address: str
    ) -> Optional[DevTokensV3Response]:
        return await self._call_with_random_agent(
            self._endpoints.dev_tokens_v3,
            dev_address=dev_address
        )
    
    async def token_info(
        self,
        pair_address: str
    ) -> Optional[TokenInfoResponse]:
        return await self._call_with_random_agent(
            self._endpoints.token_info,
            pair_address=pair_address
        )
    
    async def pair_info(
        self,
        pair_address: str
    ) -> Optional[PairInfoResponse]:
        return await self._call_with_random_agent(
            self._endpoints.pair_info,
            pair_address=pair_address
        )
    
    async def close(self) -> None:
        """Close all connections"""
        await self._request_pacer.close()
        if self._ws_task:
            if not self._ws_task.done():
                self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            except AxiomWebSocketError:
                # The task callback has already logged the terminal error.
                pass
            finally:
                self._ws_task = None
        # await self._session.close()

        cancel_tasks = []
        for session_and_agent in self._agent_selector.get_agents_and_sessions():
            cancel_tasks.append(
                session_and_agent[0].close()
            )

        await asyncio.gather(*cancel_tasks)
    
    async def __aenter__(self) -> "AxiomTradeClient":
        return self
    
    async def __aexit__(self, *args: object) -> None:
        await self.close()
    



    
