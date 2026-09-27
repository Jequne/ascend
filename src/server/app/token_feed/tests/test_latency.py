import asyncio

import pytest

from ..collector import TokenFeedCollector
from ..domain import Counts, History, PairDetails
from ..enrichment import FeedEnrichment
from .test_collector import PairSource
from .test_funding_history import FakeClient, _message


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
