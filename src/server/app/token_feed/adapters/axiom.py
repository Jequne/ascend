from collections.abc import Callable
from contextlib import nullcontext

from third_party_apis import axiom_trade_api as axiom

from ..domain import (
    Counts,
    History,
    HistoryToken,
    PairData,
    PairDetails,
    PairEvent,
    TokenFees,
)


class AxiomFeedAdapter:
    def __init__(self, client: axiom.AxiomTradeClient):
        self._client = client
        self._callback: Callable[[PairEvent], None] | None = None

    def set_callback(self, callback: Callable[[PairEvent], None]) -> None:
        self._callback = callback
        self._client.on_new_pairs(self._on_pair)

    def remove_callback(self, callback: Callable[[PairEvent], None]) -> None:
        self._client.off_new_pairs(self._on_pair)
        self._callback = None

    def _on_pair(self, message: axiom.NewPairsRoomMessage) -> None:
        data = message.content
        # The old transport rejects a missing developer; keep invalid events out.
        if data.deployer_address is None:
            raise ValueError("developer address missing")
        event = PairEvent(
            message.room,
            PairData(
                pair_address=data.pair_address,
                token_address=data.token_address,
                created_at=data.created_at,
                deployer_address=data.deployer_address,
                token_name=data.token_name,
                token_ticker=data.token_ticker,
                protocol=data.protocol,
                dev_holds_percent=data.dev_holds_percent,
                snipers_hold_percent=data.snipers_hold_percent,
                token_image=data.token_image,
                extra=bool(data.extra),
                website=data.website,
                twitter=data.twitter,
                telegram=data.telegram,
                discord=data.discord,
            ),
        )
        if self._callback is not None:
            self._callback(event)

    async def dev_tokens_v3(
        self, dev_address: str, *, background: bool = False
    ) -> History | None:
        with axiom.background_axiom_request() if background else nullcontext():
            result = await self._client.dev_tokens_v3(dev_address)
        if result is None:
            return None
        return History(
            Counts(result.counts.total_count, result.counts.migrated_count),
            [
                HistoryToken(
                    token.pair_address,
                    token.token_address,
                    token.token_ticker,
                    token.token_name,
                    token.token_image_link,
                    token.current_protocol,
                    token.created_at,
                    token.is_migrated,
                    token.ath_mcap_in_usd,
                )
                for token in result.tokens
            ],
        )

    async def pair_info(
        self, pair_address: str, *, background: bool = False
    ) -> PairDetails | None:
        with axiom.background_axiom_request() if background else nullcontext():
            result = await self._client.pair_info(pair_address)
        if result is None:
            return None
        return PairDetails(
            result.dev_wallet_funding.funding_wallet_address
            if result.dev_wallet_funding
            else None,
            result.token_image,
            result.website,
            result.telegram,
            result.discord,
            result.twitter,
        )

    async def token_info(
        self, pair_address: str, *, background: bool = False
    ) -> TokenFees | None:
        with axiom.background_axiom_request() if background else nullcontext():
            result = await self._client.token_info(pair_address)
        return (
            TokenFees(result.total_pair_fees_paid, result.dex_paid) if result else None
        )
