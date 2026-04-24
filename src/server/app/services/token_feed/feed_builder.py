from __future__ import annotations

import asyncio

from app.schemas.token_feed import DeployedToken, TokenFeedBuildRequest, TokenFeedSol
from third_party_apis.axiom_trade_api.models.endpoints.pair_info import PairInfoResponse
from third_party_apis.axiom_trade_api.models.websockets.subscription_message import (
    NewPairsRoomContent,
)

from .contracts import AxiomTradeTokenFeedClient, DeployedTokenSourceItem


class TokenFeedBuilderUtils:
    @staticmethod
    def find_current_token(
        tokens: list[DeployedTokenSourceItem],
        token_address: str,
    ) -> DeployedTokenSourceItem | None:
        for token in tokens:
            if token.token_address == token_address:
                return token
        return tokens[0] if tokens else None

    @staticmethod
    def build_deployed_tokens(
        tokens: list[DeployedTokenSourceItem],
        *,
        blockchain: str,
        dev_wallet: str,
    ) -> list[DeployedToken] | None:
        if not tokens:
            return None

        return [
            DeployedToken(
                blockchain=blockchain,
                total_pair_fees_paid=0.0,
                ath_mcap_in_usd=token.ath_mcap_in_usd,
                dex_paid=False,
                pair_address=token.pair_address,
                token_address=token.token_address,
                token_image=token.token_image_link,
                is_migrated=token.is_migrated,
                website=None,
                telegram=None,
                discord=None,
                twitter=None,
                token_name=token.token_name,
                token_ticker=token.token_ticker,
                twitter_admin_nickname=None,
                twitter_admin_id=None,
                dev_wallet=dev_wallet,
                protocol=token.current_protocol,
                created_at=token.created_at,
            )
            for token in tokens
        ]


class AxiomTradeTokenFeedBuilder(TokenFeedBuilderUtils):
    provider_name = "axiom_trade_api"
    MAX_DEPLOYED_TOKENS = 3

    def __init__(self, client: AxiomTradeTokenFeedClient):
        self._client = client

    async def _load_pair_infos(self, pair_addresses: list[str]) -> dict[str, PairInfoResponse]:
        unique_addresses = list(dict.fromkeys(pair_addresses))
        responses = await asyncio.gather(
            *(self._client.pair_info(pair_address) for pair_address in unique_addresses),
            return_exceptions=True,
        )

        pair_infos: dict[str, PairInfoResponse] = {}
        for pair_address, result in zip(unique_addresses, responses):
            if isinstance(result, PairInfoResponse):
                pair_infos[pair_address] = result
        return pair_infos

    @staticmethod
    def _enrich_deployed_token_with_pair_info(
        token: DeployedToken,
        pair_info: PairInfoResponse,
    ) -> DeployedToken:
        return DeployedToken(
            blockchain=token.blockchain,
            total_pair_fees_paid=token.total_pair_fees_paid,
            ath_mcap_in_usd=token.ath_mcap_in_usd,
            dex_paid=pair_info.dex_paid,
            pair_address=pair_info.pair_address,
            token_address=pair_info.token_address,
            token_image=pair_info.token_image,
            is_migrated=token.is_migrated,
            website=pair_info.website,
            telegram=pair_info.telegram,
            discord=pair_info.discord,
            twitter=pair_info.twitter,
            token_name=pair_info.token_name,
            token_ticker=pair_info.token_ticker,
            twitter_admin_nickname=token.twitter_admin_nickname,
            twitter_admin_id=token.twitter_admin_id,
            dev_wallet=pair_info.deployer_address,
            protocol=pair_info.protocol,
            created_at=token.created_at,
        )

    def _build_axiom_deployed_tokens(
        self,
        tokens: list[DeployedTokenSourceItem],
        pair_infos: dict[str, PairInfoResponse],
        *,
        blockchain: str,
        dev_wallet: str,
    ) -> list[DeployedToken] | None:
        base_tokens = self.build_deployed_tokens(
            tokens,
            blockchain=blockchain,
            dev_wallet=dev_wallet,
        )
        if not base_tokens:
            return None

        enriched_tokens: list[DeployedToken] = []
        for token in base_tokens:
            pair_info = pair_infos.get(token.pair_address)
            if pair_info is None:
                enriched_tokens.append(token)
                continue
            enriched_tokens.append(self._enrich_deployed_token_with_pair_info(token, pair_info))

        return enriched_tokens

    async def build_sol_token_feed(self, request: TokenFeedBuildRequest) -> TokenFeedSol | None:
        new_pair = NewPairsRoomContent.model_validate(request.payload)
        dev_address = new_pair.deployer_address
        if not dev_address:
            raise ValueError("new_pairs payload is missing deployer_address")

        dev_tokens, pair_info = await asyncio.gather(
            self._client.dev_tokens_v3(dev_address),
            self._client.pair_info(new_pair.pair_address),
        )
        if dev_tokens is None:
            return None
        if pair_info is None:
            return None

        current_token = self.find_current_token(dev_tokens.tokens, pair_info.token_address)
        recent_tokens = dev_tokens.tokens[: self.MAX_DEPLOYED_TOKENS]
        pair_infos = await self._load_pair_infos([token.pair_address for token in recent_tokens])

        return TokenFeedSol(
            dev_holds_percent=new_pair.dev_holds_percent or 0.0,
            snipers_hold_percent=new_pair.snipers_hold_percent or 0.0,
            pair_address=pair_info.pair_address,
            token_address=pair_info.token_address,
            token_image=pair_info.token_image,
            is_migrated=current_token.is_migrated if current_token is not None else False,
            website=pair_info.website,
            telegram=pair_info.telegram,
            discord=pair_info.discord,
            twitter=pair_info.twitter,
            token_name=pair_info.token_name,
            token_ticker=pair_info.token_ticker,
            twitter_admin_nickname=None,
            twitter_admin_id=None,
            dev_wallet=pair_info.deployer_address,
            protocol=pair_info.protocol,
            last_deployed_tokens=self._build_axiom_deployed_tokens(
                recent_tokens,
                pair_infos,
                blockchain="sol",
                dev_wallet=pair_info.deployer_address,
            ),
            migrated_tokens_count=dev_tokens.counts.migrated_count,
            all_tokens_count=dev_tokens.counts.total_count,
        )