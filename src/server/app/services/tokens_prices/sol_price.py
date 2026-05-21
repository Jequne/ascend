import asyncio
from typing import Callable, Protocol, List

from third_party_apis.axiom_trade_api.models.websockets.subscription_message \
    import SolPriceRoomMessage
from ...schemas.ws_streaming import WsStreamingResponse
from app.core.axiom_client_provider import client_instance
from third_party_apis.axiom_trade_api.client import AxiomTradeClient
from ..ws_streaming.manager import ConnectionManager, manager as ws_manager


class PriceHelper(Protocol):
    def __init__(self, client_instance, ws_manager: ConnectionManager):
        self._client = client_instance
        self._ws_manager = ws_manager

    def _prepare_price_data(
            self,
            sol_price_message
    ):
        pass

    async def _broadcast_price_callback(self, sol_price_message):
        ws_streaming_response = self._prepare_price_data(sol_price_message)
        pass

    def set_callback(self, callback: Callable):
        pass


class AxiomSolPriceHelper(PriceHelper):
    def __init__(
            self, 
            client_instance: AxiomTradeClient, 
            ws_manager: ConnectionManager
            ):
        self._client = client_instance
        self._ws_manager = ws_manager

    def _prepare_price_data(
            self,
            sol_price_message: SolPriceRoomMessage
            ) -> WsStreamingResponse:

        ws_streaming_response = WsStreamingResponse(
            type="sol_price",
            payload=sol_price_message.content
        )
        return ws_streaming_response
    
    async def _broadcast_price_callback(
            self, 
            sol_price_message: SolPriceRoomMessage
            ):
        ws_streaming_response = self._prepare_price_data(sol_price_message)

        await self._ws_manager.broadcast_json(
            ws_streaming_response.model_dump(mode="json")
            )

    def set_callback(self, callback: Callable):
        self._client.on_sol_price(callback)
    

class SolPriceBroadcastStarter():
    def __init__(self, price_helpers: List[PriceHelper]):
        self._price_helpers = price_helpers

    def start(self):
        for price_helper in self._price_helpers:
            price_helper.set_callback(price_helper._broadcast_price_callback)


axiom_sol_price_helper = AxiomSolPriceHelper(
    client_instance=client_instance,
    ws_manager=ws_manager
    )


sol_price_broadcast_starter = SolPriceBroadcastStarter(
    price_helpers=[axiom_sol_price_helper]
    )












