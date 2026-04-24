import logging
import asyncio
from typing import Any, Optional
from curl_cffi import AsyncSession, exceptions
import json

from ..auth.auth_manager import AuthManager
from ..models.auth import AxiomAgentData
from ..urls import AxiomWssUrls
from ..models.websockets.subscription_message import (
    RoomSubscribeRequest,
)
from .ws_router import (
    MessageCallback,
    MessageCallbackDecorator,
    WebsocketMessageRouter,
)

FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logger = logging.getLogger(__name__)


class AxiomTradeWebsocket():
    def __init__(
            self, 
            async_http_session: AsyncSession,
            auth_manager: AuthManager
            ) -> None:
        self._async_http_session = async_http_session
        self._auth_manager = auth_manager
        self._wsocket: Optional[Any] = None
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
            callback: MessageCallback
            ) -> None:
        self._message_router.register_callback(room, callback)

    def unregister_callback(
            self,
            room: str,
            callback: MessageCallback
            ) -> None:
        self._message_router.unregister_callback(room, callback)

    async def connect(
            self,
            agent_data: AxiomAgentData
            ) -> bool:
        if self._wsocket:
            logger.info(
                "✅ %s already connected to axiom websocket", 
                agent_data.agent_name
                )
            return True
        
        if not await self._auth_manager.ensure_validation(agent_data):
            logger.warning(
                "🟨 %s need to refresh all cookies for " \
                "connecting to websocket",
                agent_data.agent_name
                )
            return False
        
        try:
            self._wsocket = \
                await self._async_http_session.ws_connect(
                    url=AxiomWssUrls.WSS_URL1,
                    headers=agent_data.headers.model_dump(by_alias=True),
                    cookies=agent_data.cookies.get_cookies_for_request(),
                    timeout=15,
                    impersonate="chrome124",
                    proxy=agent_data.proxy
                )
            
            logger.info(
                "✅ %s successfully connected to websocket",
                agent_data.agent_name
                )
            return True

        except Exception as e:
            logger.error(
                "❌ %s problem with connecting to websocket: %s\n"
                "probably your proxy not working with websockets (try SOCKS5)",
                agent_data.agent_name, e
                )
            return False
        
    async def close(self) -> bool:
        if self._wsocket:
            try:
                await self._wsocket.close()
                self._wsocket = None
                logger.info("✅ disconnected from websocket")
                return True
            
            except Exception as e:
                logger.error("🟨 can't close websocket connection: %s", e)
                return False
        
        return True

    async def _messages_handler(self) -> None:
        if not self._wsocket:
            logger.warning(
                "🟨 Not active wsocket connection. Cant handle messages"
                )
            return 
        
        try:
            async for message in self._wsocket:
                try:
                    data: dict[str, Any] = json.loads(message)
                except json.JSONDecodeError:
                    logger.warning(
                        "🟨 Skip non-JSON websocket message: %s",
                        message
                        )
                    continue

                validated_data = self._message_router.validate_room_message(data)
                if not validated_data:
                    continue

                await self._message_router.dispatch_message(validated_data)
        
        except exceptions.SessionClosed as e:
            logger.warning("❌ websocket connection closed: %s", e)

        except Exception as e:
            logger.error("🟨 websocket message handling error: %s", e)

        finally:
            await self.close()
            self._wsocket = None

    async def subscribe(
            self, 
            subscription_message: RoomSubscribeRequest
            ) -> bool:
        if not self._wsocket:
            logger.warning(
                "🟨 cant subscribe to room %s cause not connected to websocket",
                subscription_message.room
                )
            return False
        
        try:
            await self._wsocket.send(subscription_message.model_dump_json())
            logger.debug("✅ Subscribed to room %s", subscription_message.room)

            return True

        except Exception as e:
            logger.warning(
                "❌ cant send message %s and subscribe: %s", 
                subscription_message.model_dump_json(), e
                )
            
            return False
        
    async def start(
            self, 
            agent_data: AxiomAgentData,
            rooms: list[str] = ["new_pairs", "sol_price", "migrations"],
            reconnecting_time_in_sec: int = 2
            ) -> None:
        while True:
            try:
                connect = await self.connect(agent_data)
                if not connect or not self._wsocket:
                    await asyncio.sleep(reconnecting_time_in_sec)
                    continue
                
                all_subscribed = True
                for room in rooms:
                    subscription_message = RoomSubscribeRequest(room=room)
                    is_subscribed = await self.subscribe(subscription_message)
                    if not is_subscribed:
                        all_subscribed = False
                        break
                
                if all_subscribed:
                    await self._messages_handler()
            
            except Exception as e:
                logger.error("❌ Websocket error: %s", e)
                self._wsocket = None
            
            finally:
                await asyncio.sleep(reconnecting_time_in_sec)



        

        

        
            
        
        



                    
