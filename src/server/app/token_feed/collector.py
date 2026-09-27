import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Coroutine

from .contracts import FeedPreparer, PairSource
from .domain import PairEvent, TokenFeedBase
from .token_logging import format_token_log

logger = logging.getLogger(__name__)


class TokenFeedCollector:
    def __init__(self, source: PairSource, preparer: FeedPreparer):
        self.tokens_feed: asyncio.Queue[TokenFeedBase] = asyncio.Queue()
        self._source = source
        self._preparer = preparer
        self._tasks: set[asyncio.Task[None]] = set()
        self._accepting = False

    async def start(self) -> None:
        self._accepting = True
        self._source.set_callback(self.schedule_token_feed_data)

    def _spawn(self, work: Coroutine[object, object, None]) -> None:
        task = asyncio.create_task(work)
        self._tasks.add(task)
        task.add_done_callback(self._finished)

    def _finished(self, task: asyncio.Task[None]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        try:
            task.result()
        except Exception:
            logger.exception("Token feed preparation failed")

    def schedule_token_feed_data(self, event: PairEvent) -> None:
        if self._accepting:
            self._spawn(self.collect_token_feed_data(event))

    async def collect_token_feed_data(self, event: PairEvent) -> None:
        base = await self._preparer.prepare_token_feed(event)
        await self.tokens_feed.put(base)
        logger.info("%s", format_token_log(base))
        for update in (
            self._preparer.developer_updates,
            self._preparer.funding_updates,
        ):
            self._spawn(self._emit_update(update, event, base))

    async def _emit_update(
        self,
        update: Callable[
            [PairEvent, TokenFeedBase], AsyncIterator[TokenFeedBase]
        ],
        event: PairEvent,
        base: TokenFeedBase,
    ) -> None:
        try:
            async for feed in update(event, base):
                await self.tokens_feed.put(feed)
                logger.info("%s", format_token_log(feed))
        except Exception:
            logger.exception("Token feed enrichment failed")

    async def stop(self) -> None:
        self._accepting = False
        self._source.remove_callback(self.schedule_token_feed_data)
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        await self._preparer.stop()
