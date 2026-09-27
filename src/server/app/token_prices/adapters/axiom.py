from third_party_apis import axiom_trade_api as axiom

from ..contracts import PriceCallback
from ..domain import SolPrice


class AxiomPriceSource:
    def __init__(self, client: axiom.AxiomTradeClient):
        self._client = client
        self._callback: PriceCallback | None = None

    async def _on_price(self, message: axiom.SolPriceRoomMessage) -> None:
        if self._callback:
            await self._callback(SolPrice(message.content))

    def subscribe(self, callback: PriceCallback) -> None:
        self._callback = callback
        self._client.on_sol_price(self._on_price)

    def unsubscribe(self, callback: PriceCallback) -> None:
        self._client.off_sol_price(self._on_price)
        self._callback = None
