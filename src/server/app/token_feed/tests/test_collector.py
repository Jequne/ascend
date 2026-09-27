import asyncio
from collections.abc import Callable
from dataclasses import replace

import pytest

from ..collector import TokenFeedCollector
from ..developer_history import select_developer_tokens
from ..domain import PairEvent, TokenFeedBase
from ..enrichment import FeedEnrichment
from .test_funding_history import FakeClient, _message


class PairSource:
    def __init__(self) -> None:
        self.callback: Callable[[PairEvent], None] | None = None

    def set_callback(self, callback: Callable[[PairEvent], None]) -> None:
        self.callback = callback

    def remove_callback(self, callback: Callable[[PairEvent], None]) -> None:
        self.callback = None


class ControlledUpdates(FeedEnrichment):
    def __init__(self, fail_developer: bool = False) -> None:
        super().__init__(FakeClient())
        self.developer_release = asyncio.Event()
        self.funding_release = asyncio.Event()
        self.fail_developer = fail_developer

    async def prepare_developer_update(
        self, event: PairEvent, base: TokenFeedBase
    ) -> TokenFeedBase | None:
        await self.developer_release.wait()
        if self.fail_developer:
            raise RuntimeError("upstream failure")
        return replace(base, all_tokens_count=2)

    async def prepare_funding_update(
        self, event: PairEvent, base: TokenFeedBase
    ) -> TokenFeedBase | None:
        await self.funding_release.wait()
        return replace(base, funding_wallet="funding-wallet")


@pytest.mark.asyncio
@pytest.mark.parametrize("funding_first", [True, False])
async def test_base_then_independent_updates_in_either_order(
    funding_first: bool,
) -> None:
    source = PairSource()
    updates = ControlledUpdates()
    collector = TokenFeedCollector(source, updates)
    await collector.start()
    try:
        assert source.callback is not None
        source.callback(_message())
        base = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert base.pair_address == "current-pair"
        assert (
            base.last_deployed_tokens is None and base.funding_wallet is None
        )
        first = (
            updates.funding_release
            if funding_first
            else updates.developer_release
        )
        second = (
            updates.developer_release
            if funding_first
            else updates.funding_release
        )
        first.set()
        update = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert update.pair_address == base.pair_address
        assert (update.funding_wallet is not None) == funding_first
        second.set()
        late = await asyncio.wait_for(collector.tokens_feed.get(), 1)
        assert late.pair_address == base.pair_address
        assert (late.all_tokens_count == 2) == funding_first
    finally:
        await collector.stop()
    assert source.callback is None


@pytest.mark.asyncio
async def test_enrichment_failure_and_shutdown_preserve_other_update() -> None:
    source = PairSource()
    updates = ControlledUpdates(fail_developer=True)
    collector = TokenFeedCollector(source, updates)
    await collector.start()
    assert source.callback is not None
    source.callback(_message())
    await asyncio.wait_for(collector.tokens_feed.get(), 1)
    updates.developer_release.set()
    updates.funding_release.set()
    result = await asyncio.wait_for(collector.tokens_feed.get(), 1)
    assert result.funding_wallet == "funding-wallet"
    await collector.stop()
    assert not collector._tasks


@pytest.mark.asyncio
async def test_new_events_and_runtime_queues_are_independent() -> None:
    first_source, second_source = PairSource(), PairSource()
    first = TokenFeedCollector(first_source, ControlledUpdates())
    second = TokenFeedCollector(second_source, ControlledUpdates())
    await first.start()
    await second.start()
    assert first_source.callback is not None
    first_source.callback(_message())
    event = _message()
    first_source.callback(
        replace(
            event, content=replace(event.content, pair_address="second-pair")
        )
    )
    try:
        one = await asyncio.wait_for(first.tokens_feed.get(), 1)
        two = await asyncio.wait_for(first.tokens_feed.get(), 1)
        assert {one.pair_address, two.pair_address} == {
            "current-pair",
            "second-pair",
        }
        assert second.tokens_feed.empty()
    finally:
        await first.stop()
        await second.stop()


@pytest.mark.asyncio
async def test_bsc_skips_funding_requests() -> None:
    provider = FakeClient()
    enrichment = FeedEnrichment(provider)
    event = replace(_message(), room="new_pairs_bnb")
    base = await enrichment.prepare_token_feed(event)
    assert base.blockchain == "bsc"
    assert await enrichment.prepare_funding_update(event, base) is None
    assert provider.requested_wallets == []


def test_developer_selection_preserves_current_pair_when_not_first() -> None:
    tokens = FakeClient().history
    assert select_developer_tokens(tokens, "current-pair") == tokens[1:]
    assert select_developer_tokens(
        list(reversed(tokens)), "current-pair"
    ) == list(reversed(tokens))


@pytest.mark.asyncio
async def test_isolated_caches_and_cancelled_waiter_preserve_request() -> None:
    class ControlledClient(FakeClient):
        def __init__(self) -> None:
            super().__init__()
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def dev_tokens_v3(
            self, dev_address: str, *, background: bool = False
        ):
            self.started.set()
            await self.release.wait()
            return await super().dev_tokens_v3(
                dev_address, background=background
            )

    one, two = ControlledClient(), ControlledClient()
    first, second = FeedEnrichment(one), FeedEnrichment(two)
    a = asyncio.create_task(first._get_cached_funding_tokens("wallet"))
    await one.started.wait()
    a.cancel()
    await asyncio.gather(a, return_exceptions=True)
    b = asyncio.create_task(first._get_cached_funding_tokens("wallet"))
    c = asyncio.create_task(second._get_cached_funding_tokens("wallet"))
    await two.started.wait()
    one.release.set()
    two.release.set()
    await asyncio.gather(b, c)
    assert one.requested_wallets == ["wallet"] and two.requested_wallets == [
        "wallet"
    ]
    await first.stop()
    await second.stop()
