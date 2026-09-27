import asyncio
import unittest
from datetime import datetime, timedelta, timezone

from app.token_feed.domain import (
    Counts,
    History,
    HistoryToken,
    PairData,
    PairDetails,
    PairEvent,
    TokenFees,
)
from app.token_feed.enrichment import FeedEnrichment
from app.token_feed.funding_history import (
    HistoricalTokenCandidate,
    select_previous_token_indexes,
)
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens_v3 import (
    DevTokensV3Response,
    Token,
)

NOW = datetime(2026, 9, 21, tzinfo=timezone.utc)
FUNDING_WALLET = "11111111111111111111111111111111"


def _token(pair: str, address: str, days_ago: int) -> HistoryToken:
    token = Token.model_validate(
        [
            pair,
            address,
            address,
            address,
            "",
            "pump",
            1,
            None,
            (NOW - timedelta(days=days_ago)).isoformat(),
            False,
            None,
            None,
            None,
            0,
            100_000,
        ]
    )
    return HistoryToken(
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


def _message() -> PairEvent:
    return PairEvent(
        room="new_pairs",
        content=PairData(
            pair_address="current-pair",
            token_address="current-token",
            created_at=NOW,
            deployer_address="developer",
            dev_holds_percent=5,
            snipers_hold_percent=None,
            token_image=None,
            extra=False,
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
        self.history = [
            _token("current-pair", "current-token", 0),
            _token("previous-pair", "previous-token", 1),
        ]

    async def dev_tokens_v3(self, dev_address: str, *, background: bool = False):
        self.requested_wallets.append(dev_address)
        tokens = self.history if dev_address == FUNDING_WALLET else []
        return History(
            tokens=tokens,
            counts=Counts(total_count=len(tokens), migrated_count=1 if tokens else 0),
        )

    async def pair_info(self, pair_address: str, *, background: bool = False):
        if pair_address == "current-pair":
            return PairDetails(funding_wallet=self.funding_address)
        return PairDetails(
            token_image=None,
            website=None,
            telegram=None,
            discord=None,
            twitter=None,
        )

    async def token_info(self, pair_address: str, *, background: bool = False):
        return TokenFees(total_pair_fees_paid=self.fees, dex_paid=False)


class FundingSelectionTests(unittest.TestCase):
    def test_existing_axiom_parser_extracts_addresses_and_date(self) -> None:
        token = _token("previous-pair", "previous-token", 1)
        response = DevTokensV3Response.model_validate(
            {
                "counts": {"totalCount": 1, "migratedCount": 0},
                "tokens": [
                    [
                        token.pair_address,
                        token.token_address,
                        token.token_ticker,
                        token.token_name,
                        token.token_image_link,
                        token.current_protocol,
                        1,
                        None,
                        token.created_at.isoformat(),
                        False,
                        None,
                        None,
                        None,
                        0,
                        token.ath_mcap_in_usd,
                    ]
                ],
            }
        )
        self.assertEqual(response.tokens[0].pair_address, "previous-pair")
        self.assertEqual(response.tokens[0].token_address, "previous-token")
        self.assertEqual(response.tokens[0].created_at, NOW - timedelta(days=1))

    def test_selects_three_newest_previous_distinct_tokens(self) -> None:
        candidates = [
            HistoricalTokenCandidate(0, "old", "old-token", NOW - timedelta(days=4)),
            HistoricalTokenCandidate(1, "current-pair", "current-token", NOW),
            HistoricalTokenCandidate(
                2, "recent", "recent-token", NOW - timedelta(days=1)
            ),
            HistoricalTokenCandidate(
                3, "duplicate", "recent-token", NOW - timedelta(days=2)
            ),
            HistoricalTokenCandidate(
                4, "middle", "middle-token", NOW - timedelta(days=3)
            ),
            HistoricalTokenCandidate(
                5, "future", "future-token", NOW + timedelta(days=1)
            ),
            HistoricalTokenCandidate(
                6, "oldest", "oldest-token", NOW - timedelta(days=5)
            ),
        ]
        self.assertEqual(
            select_previous_token_indexes(
                candidates,
                current_pair_address="current-pair",
                current_token_address="current-token",
                current_created_at=NOW,
            ),
            [2, 4, 0],
        )

    def test_empty_history_does_not_select_any_token(self) -> None:
        self.assertEqual(
            select_previous_token_indexes(
                [],
                current_pair_address="pair",
                current_token_address="token",
                current_created_at=NOW,
            ),
            [],
        )


class FundingEnrichmentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        if hasattr(self, "enrichment"):
            await self.enrichment.stop()

    async def test_resolves_funder_and_enriches_previous_token(self) -> None:
        fake = FakeClient()
        self.enrichment = FeedEnrichment(fake)
        initial = await self.enrichment.prepare_token_feed(_message())
        self.assertIsNone(initial.funding_wallet)
        feed = await self.enrichment.prepare_funding_update(_message(), initial)
        self.assertEqual(fake.requested_wallets, [FUNDING_WALLET])
        assert feed is not None and feed.funding_deployed_tokens is not None
        self.assertEqual(feed.funding_wallet, FUNDING_WALLET)
        self.assertEqual(len(feed.funding_deployed_tokens), 1)
        self.assertEqual(feed.funding_deployed_tokens[0].pair_address, "previous-pair")
        self.assertEqual(feed.funding_deployed_tokens[0].total_pair_fees_paid, 2.0)
        self.assertEqual(feed.funding_migrated_tokens_count, 1)
        self.assertEqual(feed.funding_all_tokens_count, 2)
        self.assertEqual(feed.migrated_tokens_count, 0)

    async def test_invalid_funder_does_not_cancel_developer_feed(self) -> None:
        fake = FakeClient(funding_address="invalid")
        self.enrichment = FeedEnrichment(fake)
        initial = await self.enrichment.prepare_token_feed(_message())
        feed = await self.enrichment.prepare_funding_update(_message(), initial)
        self.assertEqual(fake.requested_wallets, [])
        self.assertIsNone(feed)

    async def test_invalid_fees_are_not_treated_as_zero(self) -> None:
        fake = FakeClient(fees=float("nan"))
        self.enrichment = FeedEnrichment(fake)
        initial = await self.enrichment.prepare_token_feed(_message())
        feed = await self.enrichment.prepare_funding_update(_message(), initial)
        assert feed is not None
        self.assertEqual(feed.funding_deployed_tokens, [])

    async def test_developer_history_keeps_ath_when_fees_are_unavailable(self) -> None:
        fake = FakeClient(fees=float("nan"))
        self.enrichment = FeedEnrichment(fake)

        async def developer_history(dev_address: str, *, background: bool = False):
            return History(
                tokens=fake.history,
                counts=Counts(total_count=2, migrated_count=0),
            )

        from unittest.mock import patch

        patcher = patch.object(fake, "dev_tokens_v3", developer_history)
        patcher.start()
        self.addCleanup(patcher.stop)
        initial = await self.enrichment.prepare_token_feed(_message())
        feed = await self.enrichment.prepare_developer_update(_message(), initial)
        assert feed is not None and feed.last_deployed_tokens is not None
        self.assertEqual(len(feed.last_deployed_tokens), 1)
        self.assertIsNone(feed.last_deployed_tokens[0].total_pair_fees_paid)
        self.assertEqual(feed.last_deployed_tokens[0].ath_mcap_in_usd, 100_000)

    async def test_initial_feed_does_not_wait_for_developer_history(self) -> None:
        class SlowClient(FakeClient):
            async def dev_tokens_v3(
                self, dev_address: str, *, background: bool = False
            ):
                await asyncio.Event().wait()

        self.enrichment = FeedEnrichment(SlowClient())
        feed = await asyncio.wait_for(
            self.enrichment.prepare_token_feed(_message()), 0.1
        )
        self.assertEqual(feed.pair_address, "current-pair")
        self.assertIsNone(feed.last_deployed_tokens)

    async def test_concurrent_funding_tokens_share_one_request(self) -> None:
        class SlowClient(FakeClient):
            def __init__(self):
                super().__init__()
                self.started = asyncio.Event()
                self.release = asyncio.Event()

            async def dev_tokens_v3(
                self, dev_address: str, *, background: bool = False
            ):
                if dev_address == FUNDING_WALLET:
                    self.started.set()
                    await self.release.wait()
                return await super().dev_tokens_v3(dev_address)

        fake = SlowClient()
        self.enrichment = FeedEnrichment(fake)
        first = asyncio.create_task(
            self.enrichment._get_cached_funding_tokens(FUNDING_WALLET)
        )
        await fake.started.wait()
        second = asyncio.create_task(
            self.enrichment._get_cached_funding_tokens(FUNDING_WALLET)
        )
        await asyncio.sleep(0)
        fake.release.set()
        await asyncio.gather(first, second)
        await self.enrichment._get_cached_funding_tokens(FUNDING_WALLET)
        self.assertEqual(fake.requested_wallets, [FUNDING_WALLET])

    async def test_concurrent_tokens_share_previous_pair_enrichment(self) -> None:
        class CountingClient(FakeClient):
            def __init__(self):
                super().__init__()
                self.previous_pair_info_calls = 0
                self.previous_token_info_calls = 0

            async def pair_info(self, pair_address: str, *, background: bool = False):
                if pair_address == "previous-pair":
                    self.previous_pair_info_calls += 1
                    await asyncio.sleep(0)
                return await super().pair_info(pair_address)

            async def token_info(self, pair_address: str, *, background: bool = False):
                if pair_address == "previous-pair":
                    self.previous_token_info_calls += 1
                    await asyncio.sleep(0)
                return await super().token_info(pair_address)

        fake = CountingClient()
        self.enrichment = FeedEnrichment(fake)
        initial = await self.enrichment.prepare_token_feed(_message())
        first, second = await asyncio.gather(
            self.enrichment.prepare_funding_update(_message(), initial),
            self.enrichment.prepare_funding_update(_message(), initial),
        )
        assert first is not None and first.funding_deployed_tokens is not None
        assert second is not None and second.funding_deployed_tokens is not None
        self.assertEqual(len(first.funding_deployed_tokens), 1)
        self.assertEqual(len(second.funding_deployed_tokens), 1)
        self.assertEqual(fake.requested_wallets.count(FUNDING_WALLET), 1)
        self.assertEqual(fake.previous_pair_info_calls, 1)
        self.assertEqual(fake.previous_token_info_calls, 1)

    async def test_failed_enrichment_is_retried_on_later_update(self) -> None:
        class RecoveringClient(FakeClient):
            def __init__(self):
                super().__init__()
                self.token_info_calls = 0

            async def token_info(self, pair_address: str, *, background: bool = False):
                self.token_info_calls += 1
                if self.token_info_calls == 1:
                    raise RuntimeError("temporary Axiom failure")
                return await super().token_info(pair_address)

        fake = RecoveringClient()
        self.enrichment = FeedEnrichment(fake)
        initial = await self.enrichment.prepare_token_feed(_message())
        unavailable = await self.enrichment.prepare_funding_update(_message(), initial)
        recovered = await self.enrichment.prepare_funding_update(_message(), initial)

        assert unavailable is not None
        assert recovered is not None and recovered.funding_deployed_tokens is not None
        self.assertEqual(unavailable.funding_deployed_tokens, [])
        self.assertEqual(len(recovered.funding_deployed_tokens), 1)
        self.assertEqual(fake.token_info_calls, 2)


if __name__ == "__main__":
    unittest.main()
