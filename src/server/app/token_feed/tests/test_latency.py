import asyncio
from dataclasses import replace

import pytest

from ..collector import TokenFeedCollector
from ..domain import Counts, History
from ..enrichment import FeedEnrichment
from .test_collector import PairSource
from .test_funding_history import FakeClient, _message, _token


class ImmediateDeveloperHistory(FakeClient):
    def __init__(self) -> None:
        super().__init__()
        self.funding_fees_release = asyncio.Event()
        self.funding_details_release = asyncio.Event()
        self.developer_requests = 0

    async def dev_tokens(self, dev_address: str, *, background: bool = False):
        self.developer_requests += 1
        return History(
            Counts(total_count=2, migrated_count=1),
            [
                self.history[0],
                replace(
                    self.history[1],
                    total_pair_fees_paid=2,
                    website="https://example.com",
                    is_migrated=True,
                ),
            ],
        )

    async def token_info(self, pair_address: str, *, background: bool = False):
        await self.funding_fees_release.wait()
        return await super().token_info(pair_address, background=background)

    async def pair_info(self, pair_address: str, *, background: bool = False):
        if pair_address != "current-pair":
            await self.funding_details_release.wait()
        return await super().pair_info(pair_address, background=background)


@pytest.mark.asyncio
async def test_developer_data_arrives_without_secondary_requests():
    provider = ImmediateDeveloperHistory()
    collector = TokenFeedCollector(PairSource(), FeedEnrichment(provider))
    try:
        await collector.collect_token_feed_data(_message())
        base = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert base.last_deployed_tokens is None
        developer = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert developer.last_deployed_tokens is not None
        token = developer.last_deployed_tokens[0]
        assert token.ath_mcap_in_usd == 100_000
        assert token.total_pair_fees_paid == 2
        assert token.website == "https://example.com"
        assert token.is_migrated
        assert provider.developer_requests == 1
        assert not provider.funding_fees_release.is_set()
    finally:
        await collector.stop()


@pytest.mark.asyncio
async def test_concurrent_developer_events_share_history():
    provider = ImmediateDeveloperHistory()
    enrichment = FeedEnrichment(provider)
    base = await enrichment.prepare_token_feed(_message())
    try:
        results = await asyncio.gather(
            *(
                enrichment.prepare_developer_update(_message(), base)
                for _ in range(2)
            )
        )
        assert all(result is not None for result in results)
        assert provider.developer_requests == 1
    finally:
        await enrichment.stop()


@pytest.mark.asyncio
async def test_developer_fees_arrive_with_history():
    class MultipleTokens(ImmediateDeveloperHistory):
        async def dev_tokens(
            self, dev_address: str, *, background: bool = False
        ):
            return History(
                Counts(total_count=3, migrated_count=1),
                [
                    _token("current-pair", "current-token", 0),
                    replace(
                        _token("first-pair", "first-token", 1),
                        total_pair_fees_paid=1.25,
                    ),
                    replace(
                        _token("second-pair", "second-token", 2),
                        total_pair_fees_paid=0.5,
                    ),
                ],
            )

    provider = MultipleTokens()
    enrichment = FeedEnrichment(provider)
    try:
        feed = await enrichment.prepare_developer_update(
            _message(), await enrichment.prepare_token_feed(_message())
        )
        assert feed is not None and feed.last_deployed_tokens is not None
        assert [t.total_pair_fees_paid for t in feed.last_deployed_tokens] == [
            1.25,
            0.5,
        ]
    finally:
        await enrichment.stop()
