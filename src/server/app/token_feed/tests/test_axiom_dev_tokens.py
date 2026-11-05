from unittest.mock import AsyncMock

import pytest

from app.token_feed.adapters.axiom import AxiomFeedAdapter
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens import (
    DevTokensResponse,
)
from third_party_apis.axiom_trade_api.tests.test_dev_tokens import (
    sample_response,
)


@pytest.mark.asyncio
async def test_adapter_maps_current_response_to_developer_history() -> None:
    client = AsyncMock()
    client.dev_tokens.return_value = DevTokensResponse.model_validate(
        sample_response()
    )
    adapter = AxiomFeedAdapter(client)
    history = await adapter.dev_tokens("developer")
    assert history is not None
    assert history.counts.migrated_count == 0
    assert history.tokens[0].pair_address == "pair-address"
    assert history.tokens[0].total_pair_fees_paid == 0.340612075
    assert history.tokens[0].ath_mcap_in_usd == 24871.405
    assert history.tokens[0].twitter == "https://x.com/example/status/1"
    assert history.funding_wallet == "11111111111111111111111111111111"
    client.dev_tokens.assert_awaited_once_with("developer")


@pytest.mark.asyncio
async def test_adapter_ignores_funding_for_another_wallet() -> None:
    payload = sample_response()
    payload["walletFunding"]["walletAddress"] = "another-wallet"
    client = AsyncMock()
    client.dev_tokens.return_value = DevTokensResponse.model_validate(payload)
    history = await AxiomFeedAdapter(client).dev_tokens("developer")
    assert history is not None
    assert history.funding_wallet is None


@pytest.mark.asyncio
async def test_null_best_pair_uses_fallback_or_skips_entry() -> None:
    payload = sample_response()
    fallback = sample_response()["tokens"][0]
    fallback["bestPair"] = None
    fallback["token"]["bestPairAddress"] = "fallback-pair"
    unusable = sample_response()["tokens"][0]
    unusable["bestPair"] = None
    unusable["token"].pop("bestPairAddress")
    payload["tokens"] = [unusable, fallback, payload["tokens"][0]]
    client = AsyncMock()
    client.dev_tokens.return_value = DevTokensResponse.model_validate(payload)
    history = await AxiomFeedAdapter(client).dev_tokens("developer")
    assert history is not None
    assert [token.pair_address for token in history.tokens] == [
        "fallback-pair",
        "pair-address",
    ]
    assert history.tokens[0].current_protocol == "Unknown"
    assert history.funding_wallet == "11111111111111111111111111111111"


@pytest.mark.asyncio
async def test_missing_name_and_ticker_fall_back_to_token_address() -> None:
    payload = sample_response()
    payload["tokens"][0]["token"]["tokenName"] = None
    payload["tokens"][0]["token"]["tokenTicker"] = None
    client = AsyncMock()
    client.dev_tokens.return_value = DevTokensResponse.model_validate(payload)
    history = await AxiomFeedAdapter(client).dev_tokens("developer")
    assert history is not None
    assert history.tokens[0].token_name == "token-address"
    assert history.tokens[0].token_ticker == "token-address"
    assert history.tokens[0].total_pair_fees_paid == 0.340612075
