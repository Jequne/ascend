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


class TokenFeedCollectorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        while not TokenFeedCollector.tokens_feed.empty():
            TokenFeedCollector.tokens_feed.get_nowait()

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


if __name__ == "__main__":
    unittest.main()
