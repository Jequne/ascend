from curl_cffi import AsyncSession
from typing import Any, Awaitable, Callable, List, Literal, Optional, TypeVar
import logging
import asyncio

from .models.auth import AxiomAgentData
from .auth.auth_manager import AuthManager
from .agent_selector import AgentSelector
from .endpoints.ws import AxiomTradeWebsocket
from .endpoints.endpoints import AxiomTradeEndpoints
from .models.endpoints.pair_chart_v2 import PairChartV2Params, PairChartV2Response
from .models.endpoints.dev_tokens_v3 import DevTokensV3Response
from .models.endpoints.token_info import TokenInfoResponse
from .models.endpoints.pair_info import PairInfoResponse


FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logger = logging.getLogger(__name__)
ResponseModelT = TypeVar("ResponseModelT")


class AxiomTradeClient:
    def __init__(
            self,
            agents: List[AxiomAgentData],
            ):
        self._auth_manager = AuthManager()
        self._agent_selector = AgentSelector()
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
        random_session_and_agent = self._agent_selector.random_websocket_agent()

        self._ws_task = asyncio.create_task(
            self._wsocket.start(
                session_and_agent=random_session_and_agent, 
                rooms=rooms
                )
        )
    
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
        random_session_and_agent = self._agent_selector.random_agent()
        return await endpoint_method(
            session_and_agent=random_session_and_agent, **kwargs
            )

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
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
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
    



    
