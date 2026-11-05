from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens import (
    DevTokensResponse,
)
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens_v3 import (
    DevTokensV3Response,
)


def sample_response() -> dict:
    return {
        "counts": {"totalCount": 1, "migratedCount": 0},
        "tokens": [
            {
                "allTimeHighMarketcapUsd": 24871.405,
                "bestPair": {
                    "pairAddress": "pair-address",
                    "displayProtocol": "Pump",
                },
                "isMigrated": False,
                "totalPairFeesPaid": 0.340612075,
                "token": {
                    "tokenAddress": "token-address",
                    "bestPairAddress": "pair-address",
                    "tokenTicker": "Simpson",
                    "tokenName": "Simpson",
                    "tokenImage": "https://example.com/token.webp",
                    "tokenCreatedAt": "2026-11-05T19:46:04.986Z",
                    "dexPaid": False,
                    "twitter": "https://x.com/example/status/1",
                    "website": None,
                },
            }
        ],
        "walletFunding": {
            "walletAddress": "developer",
            "fundingWalletAddress": "11111111111111111111111111111111",
            "amountNative": 9.779,
        },
    }


def test_new_response_reads_object_tokens_and_preserves_old_schema() -> None:
    response = DevTokensResponse.model_validate(sample_response())
    token = response.tokens[0]
    assert response.counts.total_count == 1
    assert token.all_time_high_marketcap_usd == 24871.405
    assert token.total_pair_fees_paid == 0.340612075
    assert token.is_migrated is False
    assert response.wallet_funding is not None
    assert (
        response.wallet_funding.funding_wallet_address
        == "11111111111111111111111111111111"
    )
    assert token.token.token_created_at == datetime(
        2026, 11, 5, 19, 46, 4, 986000, tzinfo=timezone.utc
    )
    with pytest.raises(ValidationError):
        DevTokensV3Response.model_validate(sample_response())


def test_null_best_pair_does_not_reject_other_tokens_or_funding() -> None:
    payload = sample_response()
    missing_pair = sample_response()["tokens"][0]
    missing_pair["bestPair"] = None
    payload["tokens"].insert(0, missing_pair)
    response = DevTokensResponse.model_validate(payload)
    assert response.tokens[0].best_pair is None
    assert response.tokens[0].token.best_pair_address == "pair-address"
    assert len(response.tokens) == 2
    assert response.wallet_funding is not None


def test_null_token_name_and_ticker_do_not_reject_history() -> None:
    payload = sample_response()
    payload["tokens"][0]["token"]["tokenName"] = None
    payload["tokens"][0]["token"]["tokenTicker"] = None
    payload["tokens"].append(sample_response()["tokens"][0])
    response = DevTokensResponse.model_validate(payload)
    assert len(response.tokens) == 2
    assert response.tokens[0].token.token_name is None
    assert response.tokens[0].token.token_ticker is None
    assert response.wallet_funding is not None
