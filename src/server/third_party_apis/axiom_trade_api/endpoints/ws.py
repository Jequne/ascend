import asyncio
import json
import logging
from typing import Any, Sequence

from curl_cffi import AsyncSession
from curl_cffi.curl import CurlError
from curl_cffi.requests.websockets import (
    AsyncWebSocket,
    WebSocketError,
)

from ..auth import AuthManager
from .exceptions import (
    AxiomWebSocketCloseError,
    AxiomWebSocketConnectionError,
    AxiomWebSocketNotConnectedError,
    AxiomWebSocketReceiveError,
    AxiomWebSocketSubscriptionError,
)
from ..models import (
    RoomSubscribeRequest,
    AxiomAgentData
)
from ..urls import AxiomWssUrls
from .endpoints import AxiomTradeEndpoints
from .ws_router import (
    MessageCallback,
    MessageCallbackDecorator,
    WebsocketMessageRouter,
)


logger = logging.getLogger(__name__)


class AxiomTradeWebsocket:
    def __init__(
        self,
        auth_manager: AuthManager,
        endpoints: AxiomTradeEndpoints,
    ) -> None:
        self._endpoints = endpoints
        self._auth_manager = auth_manager
        self._wsocket: AsyncWebSocket | None = None
        self._message_router = WebsocketMessageRouter()

    def on(self, room: str) -> MessageCallbackDecorator:
        """Decorator to register callback for a room.

        Usage:
            @ws.on("sol_price")
            async def handle_sol_price(data):
                pass
        """
        return self._message_router.on(room)

    def register_callback(
        self,
        room: str,
        callback: MessageCallback,
    ) -> None:
        self._message_router.register_callback(
            room,
            callback,
        )

    def unregister_callback(
        self,
        room: str,
        callback: MessageCallback,
    ) -> None:
        self._message_router.unregister_callback(
            room,
            callback,
        )

    async def _warm_up_before_connect(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
    ) -> None:
        await self._endpoints.server_time(
            session_and_agent,
        )
        await self._endpoints.get_announcement(
            session_and_agent,
        )

    async def connect(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
    ) -> None:
        session, agent_data = session_and_agent

        if self._wsocket:
            logger.debug(
                "%s already connected to Axiom WebSocket",
                agent_data.agent_name,
            )
            return

        is_valid = await self._auth_manager.ensure_validation(
            session_and_agent,
        )

        if not is_valid:
            raise AxiomWebSocketConnectionError(
                f"{agent_data.agent_name}: "
                "authentication validation failed before WebSocket connection"
            )

        try:
            await self._warm_up_before_connect(
                session_and_agent,
            )

            self._wsocket = await session.ws_connect(
                url=AxiomWssUrls.WSS_URL1,
                headers=agent_data.headers.headers_for_wss,
                cookies=agent_data.cookies.get_cookies_for_request(),
                timeout=15,
                impersonate="chrome136",
                proxy=agent_data.proxy,
            )

        except CurlError as exc:
            raise AxiomWebSocketConnectionError(
                f"{agent_data.agent_name}: "
                "failed to connect to Axiom WebSocket"
            ) from exc

        logger.info(
            "%s connected to Axiom WebSocket",
            agent_data.agent_name,
        )

    async def close(self) -> None:
        if not self._wsocket:
            return

        try:
            await self._wsocket.close()

        except CurlError as exc:
            raise AxiomWebSocketCloseError(
                "Failed to close Axiom WebSocket connection"
            ) from exc

        finally:
            self._wsocket = None

        logger.info(
            "Disconnected from Axiom WebSocket"
        )

    async def _messages_handler(self) -> None:
        if not self._wsocket:
            raise AxiomWebSocketNotConnectedError(
                "Cannot handle messages without an active WebSocket connection"
            )

        try:
            async for message in self._wsocket:
                try:
                    data: Any = json.loads(message)

                except json.JSONDecodeError:
                    logger.warning(
                        "Skipping non-JSON WebSocket message: %r",
                        message[:200],
                    )
                    continue

                if not isinstance(data, dict):
                    logger.warning(
                        "Skipping WebSocket message because "
                        "JSON payload is not an object"
                    )
                    continue

                validated_data = (
                    self._message_router.validate_room_message(
                        data
                    )
                )

                if validated_data is None:
                    continue

                await self._message_router.dispatch_message(
                    validated_data
                )

        except WebSocketError as exc:
            raise AxiomWebSocketReceiveError(
                "Error while receiving WebSocket messages"
            ) from exc

    async def subscribe(
        self,
        subscription_message: RoomSubscribeRequest,
    ) -> None:
        if not self._wsocket:
            raise AxiomWebSocketNotConnectedError(
                f"Cannot subscribe to room "
                f"{subscription_message.room}: "
                "WebSocket is not connected"
            )

        try:
            await self._wsocket.send_str(
                subscription_message.model_dump_json()
            )

        except CurlError as exc:
            raise AxiomWebSocketSubscriptionError(
                f"Failed to subscribe to room "
                f"{subscription_message.room}"
            ) from exc

        logger.debug(
            "Subscription request sent for room %s",
            subscription_message.room,
        )

    async def start(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        rooms: Sequence[str] = (
            "new_pairs",
            "sol_price",
            "migrations",
        ),
        reconnecting_time_in_sec: int = 3,
        max_retry_count: int = 3,
    ) -> None:
        _, agent_data = session_and_agent

        retry_count = 0

        while True:
            try:
                await self.connect(
                    session_and_agent,
                )

                for room in rooms:
                    await self.subscribe(
                        RoomSubscribeRequest(
                            room=room,
                        )
                    )

                # Connection and subscriptions succeeded.
                # Previous failed attempts no longer matter.
                retry_count = 0

                await self._messages_handler()

                logger.warning(
                    "%s WebSocket connection closed, reconnecting",
                    agent_data.agent_name,
                )

            except (
                AxiomWebSocketConnectionError,
                AxiomWebSocketNotConnectedError,
                AxiomWebSocketSubscriptionError,
                AxiomWebSocketReceiveError,
            ) as exc:
                retry_count += 1

                if retry_count >= max_retry_count:
                    raise AxiomWebSocketConnectionError(
                        f"{agent_data.agent_name}: "
                        f"WebSocket failed after "
                        f"{retry_count} consecutive attempts"
                    ) from exc

                logger.warning(
                    "%s WebSocket problem: %s. "
                    "Retrying (%s/%s)",
                    agent_data.agent_name,
                    exc,
                    retry_count,
                    max_retry_count,
                )

            finally:
                try:
                    await self.close()

                except AxiomWebSocketCloseError as exc:
                    logger.warning(
                        "Failed to cleanly close WebSocket: %s",
                        exc,
                    )

            await asyncio.sleep(
                reconnecting_time_in_sec
            )