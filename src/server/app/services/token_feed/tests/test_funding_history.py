import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.token_feed.axiom_dev_token_data import AxiomDevTokenData
from app.services.token_feed.funding_history import (
    HistoricalTokenCandidate,
    select_previous_token_indexes,
)
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens_v3 import (
    DevTokensV3Response,
    Token,
)


NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)
FUNDING_WALLET = "11111111111111111111111111111111"


def _token(pair: str, address: str, days_ago: int) -> Token:
    return Token.model_validate([
        pair, address, address, address, "", "pump", 1, None,
        (NOW - timedelta(days=days_ago)).isoformat(), False,
        None, None, None, 0, 100_000,
    ])


def _message() -> SimpleNamespace:
    return SimpleNamespace(
        room="new_pairs",
        content=SimpleNamespace(
            pair_address="current-pair",
            token_address="current-token",
            created_at=NOW,
            deployer_address="developer",
            dev_holds_percent=5,
            snipers_hold_percent=None,
            token_image=None,
            extra=None,
            website=None,
            twitter=None,
            telegram=None,
            discord=None,
            token_name="Current",
            token_ticker="NEW",
            protocol="pump",
        ),
    )


class FakeClient:
    def __init__(self, funding_address: str = FUNDING_WALLET, fees: float = 2.0):
        self.funding_address = funding_address
        self.fees = fees
        self.requested_wallets: list[str] = []
        self.history = [_token("current-pair", "current-token", 0),
                        _token("previous-pair", "previous-token", 1)]

    async def dev_tokens_v3(self, dev_address: str):
        self.requested_wallets.append(dev_address)
        tokens = self.history if dev_address == FUNDING_WALLET else []
        return SimpleNamespace(
            tokens=tokens,
            counts=SimpleNamespace(total_count=len(tokens), migrated_count=0),
        )

    async def pair_info(self, pair_address: str):
        if pair_address == "current-pair":
            return SimpleNamespace(dev_wallet_funding=SimpleNamespace(
                funding_wallet_address=self.funding_address,
            ))
        return SimpleNamespace(
            token_image=None, website=None, telegram=None,
            discord=None, twitter=None,
        )

    async def token_info(self, pair_address: str):
        return SimpleNamespace(total_pair_fees_paid=self.fees, dex_paid=False)


class FundingSelectionTests(unittest.TestCase):
    def test_existing_axiom_parser_extracts_addresses_and_date(self) -> None:
        token = _token("previous-pair", "previous-token", 1)
        response = DevTokensV3Response.model_validate({
            "counts": {"totalCount": 1, "migratedCount": 0},
            "tokens": [[
                token.pair_address, token.token_address, token.token_ticker,
                token.token_name, token.token_image_link, token.current_protocol,
                token.supply, None, token.created_at.isoformat(), False,
                None, None, None, 0, token.ath_mcap_in_usd,
            ]],
        })
        self.assertEqual(response.tokens[0].pair_address, "previous-pair")
        self.assertEqual(response.tokens[0].token_address, "previous-token")
        self.assertEqual(response.tokens[0].created_at, NOW - timedelta(days=1))

    def test_selects_three_newest_previous_distinct_tokens(self) -> None:
        candidates = [
            HistoricalTokenCandidate(0, "old", "old-token", NOW - timedelta(days=4)),
            HistoricalTokenCandidate(1, "current-pair", "current-token", NOW),
            HistoricalTokenCandidate(2, "recent", "recent-token", NOW - timedelta(days=1)),
            HistoricalTokenCandidate(3, "duplicate", "recent-token", NOW - timedelta(days=2)),
            HistoricalTokenCandidate(4, "middle", "middle-token", NOW - timedelta(days=3)),
            HistoricalTokenCandidate(5, "future", "future-token", NOW + timedelta(days=1)),
            HistoricalTokenCandidate(6, "oldest", "oldest-token", NOW - timedelta(days=5)),
        ]
        self.assertEqual(select_previous_token_indexes(
            candidates,
            current_pair_address="current-pair",
            current_token_address="current-token",
            current_created_at=NOW,
        ), [2, 4, 0])

    def test_empty_history_does_not_select_any_token(self) -> None:
        self.assertEqual(select_previous_token_indexes(
            [], current_pair_address="pair", current_token_address="token",
            current_created_at=NOW,
        ), [])


class FundingEnrichmentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        AxiomDevTokenData._client = None

    async def test_resolves_funder_and_enriches_previous_token(self) -> None:
        fake = FakeClient()
        AxiomDevTokenData._client = fake
        feed = await AxiomDevTokenData.prepare_token_feed(_message())
        self.assertEqual(fake.requested_wallets, ["developer", FUNDING_WALLET])
        self.assertEqual(feed.funding_wallet, FUNDING_WALLET)
        self.assertEqual(len(feed.funding_deployed_tokens), 1)
        self.assertEqual(feed.funding_deployed_tokens[0].pair_address, "previous-pair")
        self.assertEqual(feed.funding_deployed_tokens[0].total_pair_fees_paid, 2.0)

    async def test_invalid_funder_does_not_cancel_developer_feed(self) -> None:
        fake = FakeClient(funding_address="invalid")
        AxiomDevTokenData._client = fake
        feed = await AxiomDevTokenData.prepare_token_feed(_message())
        self.assertEqual(fake.requested_wallets, ["developer"])
        self.assertIsNone(feed.funding_wallet)
        self.assertIsNone(feed.funding_deployed_tokens)

    async def test_invalid_fees_are_not_treated_as_zero(self) -> None:
        fake = FakeClient(fees=float("nan"))
        AxiomDevTokenData._client = fake
        feed = await AxiomDevTokenData.prepare_token_feed(_message())
        self.assertEqual(feed.funding_deployed_tokens, [])


if __name__ == "__main__":
    unittest.main()
