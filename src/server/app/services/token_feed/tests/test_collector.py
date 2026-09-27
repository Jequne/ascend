import asyncio
import unittest

from app.schemas.token_feed_models import TokenFeedBase
from app.services.token_feed.collector import TokenFeedCollector


def _feed(pair_address: str) -> TokenFeedBase:
    return TokenFeedBase(
        blockchain="sol",
        dev_holds_percent=1,
        snipers_hold_percent=2,
        pair_address=pair_address,
        token_address=f"token-{pair_address}",
        token_image=None,
        is_migrated=False,
        website=None,
        twitter=None,
        telegram=None,
        discord=None,
        token_name=pair_address,
        token_ticker=pair_address,
        dev_wallet="developer",
        protocol="pump",
        last_deployed_tokens=[],
        migrated_tokens_count=0,
        all_tokens_count=1,
    )


class _ControlledSource:
    def __init__(self) -> None:
        self.callback = None
        self.started: list[str] = []
        self.releases: dict[str, asyncio.Event] = {}

    def set_callback(self, callback) -> None:
        self.callback = callback

    async def prepare_token_feed(self, message: str) -> TokenFeedBase:
        self.started.append(message)
        release = self.releases.setdefault(message, asyncio.Event())
        await release.wait()
        return _feed(message)


class _LateFundingSource(_ControlledSource):
    def __init__(self) -> None:
        super().__init__()
        self.funding_release = asyncio.Event()

    async def prepare_funding_update(
        self, message: str, base_feed: TokenFeedBase
    ) -> TokenFeedBase:
        await self.funding_release.wait()
        return base_feed.model_copy(update={"funding_wallet": "funding-wallet"})


class _ParallelUpdatesSource(_LateFundingSource):
    def __init__(self) -> None:
        super().__init__()
        self.developer_release = asyncio.Event()

    async def prepare_developer_update(
        self, message: str, base_feed: TokenFeedBase
    ) -> TokenFeedBase:
        await self.developer_release.wait()
        return base_feed.model_copy(update={"all_tokens_count": 2})


class TokenFeedCollectorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        TokenFeedCollector.tokens_feed = asyncio.Queue()

    async def test_new_messages_start_without_waiting_for_previous_enrichment(
        self,
    ) -> None:
        source = _ControlledSource()
        collector = TokenFeedCollector([source])
        await collector.start()

        self.assertIsNotNone(source.callback)
        source.callback("first")
        source.callback("second")
        await asyncio.sleep(0)

        self.assertEqual(source.started, ["first", "second"])

        source.releases["first"].set()
        first = await asyncio.wait_for(
            TokenFeedCollector.tokens_feed.get(),
            timeout=0.1,
        )
        source.releases["second"].set()
        second = await asyncio.wait_for(
            TokenFeedCollector.tokens_feed.get(),
            timeout=0.1,
        )

        self.assertEqual(
            [first.pair_address, second.pair_address],
            ["first", "second"],
        )
        await collector.stop()

    async def test_emits_base_before_funding_update_for_same_token(self) -> None:
        source = _LateFundingSource()
        collector = TokenFeedCollector([source])
        await collector.start()
        source.callback("pair")
        await asyncio.sleep(0)
        source.releases["pair"].set()

        base = await asyncio.wait_for(TokenFeedCollector.tokens_feed.get(), 0.1)
        self.assertEqual(base.pair_address, "pair")
        self.assertIsNone(base.funding_wallet)

        source.funding_release.set()
        update = await asyncio.wait_for(TokenFeedCollector.tokens_feed.get(), 0.1)
        self.assertEqual(update.pair_address, "pair")
        self.assertEqual(update.funding_wallet, "funding-wallet")
        await collector.stop()

    async def test_funding_can_arrive_before_slow_developer_history(self) -> None:
        source = _ParallelUpdatesSource()
        collector = TokenFeedCollector([source])
        await collector.start()
        source.callback("pair")
        await asyncio.sleep(0)
        source.releases["pair"].set()
        base = await asyncio.wait_for(TokenFeedCollector.tokens_feed.get(), 0.1)
        self.assertIsNone(base.funding_wallet)
        source.funding_release.set()
        funding = await asyncio.wait_for(TokenFeedCollector.tokens_feed.get(), 0.1)
        self.assertEqual(funding.funding_wallet, "funding-wallet")
        source.developer_release.set()
        developer = await asyncio.wait_for(TokenFeedCollector.tokens_feed.get(), 0.1)
        self.assertEqual(developer.all_tokens_count, 2)
        await collector.stop()


if __name__ == "__main__":
    unittest.main()
