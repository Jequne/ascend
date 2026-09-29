import asyncio

import pytest

from ..collector import TokenFeedCollector
from ..domain import Counts, History, PairDetails
from ..enrichment import FeedEnrichment
from .test_collector import PairSource
from .test_funding_history import FakeClient, _message, _token


class DelayedDetails(FakeClient):
    def __init__(self) -> None:
        super().__init__()
        self.fees_release = asyncio.Event()
        self.details_release = asyncio.Event()
        self.details_started = asyncio.Event()
        self.requests: list[tuple[str, bool]] = []

    async def dev_tokens_v3(
        self, dev_address: str, *, background: bool = False
    ):
        self.requests.append(("history", background))
        self.requested_wallets.append(dev_address)
        return History(Counts(total_count=2, migrated_count=1), self.history)

    async def token_info(self, pair_address: str, *, background: bool = False):
        self.requests.append(("fees", background))
        await self.fees_release.wait()
        return await super().token_info(pair_address, background=background)

    async def pair_info(self, pair_address: str, *, background: bool = False):
        self.requests.append(("details", background))
        if pair_address == "current-pair":
            return await super().pair_info(pair_address, background=background)
        self.details_started.set()
        await self.details_release.wait()
        return PairDetails(website="https://example.com")


@pytest.mark.asyncio
async def test_collector_emits_ath_then_fees_without_waiting_for_details():
    provider = DelayedDetails()
    collector = TokenFeedCollector(PairSource(), FeedEnrichment(provider))
    try:
        await collector.collect_token_feed_data(_message())
        base = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert base.last_deployed_tokens is None
        preview = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert preview.last_deployed_tokens is not None
        assert preview.last_deployed_tokens[0].ath_mcap_in_usd == 100_000
        assert preview.last_deployed_tokens[0].total_pair_fees_paid is None
        provider.fees_release.set()
        verified = [
            await asyncio.wait_for(collector.tokens_feed.get(), 1)
            for _ in range(2)
        ]
        developer = next(f for f in verified if f.last_deployed_tokens)
        funding = next(f for f in verified if f.funding_deployed_tokens)
        assert developer.last_deployed_tokens is not None
        assert developer.last_deployed_tokens[0].total_pair_fees_paid == 2
        assert funding.funding_deployed_tokens is not None
        assert funding.funding_deployed_tokens[0].total_pair_fees_paid == 2
        assert not provider.details_release.is_set()
        await asyncio.wait_for(provider.details_started.wait(), 1)
        assert provider.requests.count(("fees", False)) == 1
        assert ("details", False) in provider.requests
        assert ("details", True) in provider.requests
        assert ("history", True) not in provider.requests
        provider.details_release.set()
        detailed = [
            await asyncio.wait_for(collector.tokens_feed.get(), 1)
            for _ in range(2)
        ]
        for feed in detailed:
            tokens = feed.last_deployed_tokens or feed.funding_deployed_tokens
            assert tokens is not None
            assert tokens[0].website == "https://example.com"
    finally:
        await collector.stop()


@pytest.mark.asyncio
async def test_developer_events_share_history_and_fees():
    provider = DelayedDetails()
    enrichment = FeedEnrichment(provider)
    base = await enrichment.prepare_token_feed(_message())
    streams = [
        enrichment.developer_updates(_message(), base) for _ in range(2)
    ]
    try:
        await asyncio.gather(*(anext(stream) for stream in streams))
        assert provider.requested_wallets == ["developer"]
        provider.fees_release.set()
        await asyncio.gather(*(anext(stream) for stream in streams))
        assert provider.requests.count(("fees", False)) == 1
    finally:
        await asyncio.gather(*(stream.aclose() for stream in streams))
        await enrichment.stop()


@pytest.mark.asyncio
async def test_developer_fees_arrive_per_token_without_waiting_for_slow_fee():
    class StaggeredFees(FakeClient):
        def __init__(self) -> None:
            super().__init__()
            self.slow_fee = asyncio.Event()
            self.fee_pairs: list[str] = []
            self.history = [
                _token("current-pair", "current-token", 0),
                _token("fast-pair", "fast-token", 1),
                _token("slow-pair", "slow-token", 2),
            ]

        async def dev_tokens_v3(
            self, dev_address: str, *, background: bool = False
        ):
            return History(
                Counts(total_count=3, migrated_count=1), self.history
            )

        async def token_info(
            self, pair_address: str, *, background: bool = False
        ):
            self.fee_pairs.append(pair_address)
            if pair_address == "slow-pair":
                await self.slow_fee.wait()
            return await super().token_info(
                pair_address, background=background
            )

        async def pair_info(
            self, pair_address: str, *, background: bool = False
        ):
            return None

    provider = StaggeredFees()
    enrichment = FeedEnrichment(provider)
    stream = enrichment.developer_updates(
        _message(), await enrichment.prepare_token_feed(_message())
    )
    try:
        preview = await asyncio.wait_for(anext(stream), 1)
        partial = await asyncio.wait_for(anext(stream), 1)
        assert preview.last_deployed_tokens is not None
        assert partial.last_deployed_tokens is not None
        assert [
            token.total_pair_fees_paid
            for token in preview.last_deployed_tokens
        ] == [
            None,
            None,
        ]
        assert [
            token.total_pair_fees_paid
            for token in partial.last_deployed_tokens
        ] == [
            2,
            None,
        ]
        assert provider.fee_pairs == ["fast-pair", "slow-pair"]
        provider.slow_fee.set()
        complete = await asyncio.wait_for(anext(stream), 1)
        assert complete.last_deployed_tokens is not None
        assert [
            token.total_pair_fees_paid
            for token in complete.last_deployed_tokens
        ] == [
            2,
            2,
        ]
    finally:
        provider.slow_fee.set()
        await stream.aclose()
        await enrichment.stop()
