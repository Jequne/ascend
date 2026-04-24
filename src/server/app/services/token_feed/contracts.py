from __future__ import annotations

from typing import Protocol

from app.schemas.token_feed import TokenFeedBuildRequest, TokenFeedSol
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens_v3 import (
    DevTokensV3Response,
)
from third_party_apis.axiom_trade_api.models.endpoints.pair_info import PairInfoResponse


class TokenFeedProvider(Protocol):
    provider_name: str

    async def build_sol_token_feed(self, request: TokenFeedBuildRequest) -> TokenFeedSol | None:
        """Build TokenFeedSol from provider-specific data sources."""


class DeployedTokenSourceItem(Protocol):
    pair_address: str
    token_address: str
    token_ticker: str
    token_name: str
    token_image_link: str
    current_protocol: str
    created_at: object
    is_migrated: bool
    ath_mcap_in_usd: float


class AxiomTradeTokenFeedClient(Protocol):
    async def dev_tokens_v3(self, dev_address: str) -> DevTokensV3Response | None:
        """Return developer token history for the given wallet address."""

    async def pair_info(self, pair_address: str) -> PairInfoResponse | None:
        """Return pair metadata for the current token."""