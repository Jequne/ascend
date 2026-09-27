"""Shared pacing for authenticated Axiom HTTP calls."""

import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
import heapq
import itertools
import logging
import time
from typing import Iterator


_request_priority: ContextVar[int] = ContextVar("axiom_request_priority", default=0)
logger = logging.getLogger(__name__)
MAX_FOREGROUND_BURST = 10


@contextmanager
def background_axiom_request() -> Iterator[None]:
    token = _request_priority.set(1)
    try:
        yield
    finally:
        _request_priority.reset(token)


class AxiomRequestPacer:
    def __init__(
        self, interval_seconds: float = 0.1, max_concurrency: int = 50
    ) -> None:
        if interval_seconds < 0 or max_concurrency < 1:
            raise ValueError("Axiom pacing requires a nonnegative interval and slots")
        self.interval_seconds = interval_seconds
        self.max_concurrency = max_concurrency
        self._pending: list[tuple[int, int, float, asyncio.Future[None]]] = []
        self._sequence = itertools.count()
        self._worker: asyncio.Task[None] | None = None
        self._last_start = 0.0
        self._active = 0
        self._slot_released = asyncio.Event()
        self._foreground_streak = 0

    async def wait_turn(self) -> None:
        queued_at = time.monotonic()
        priority = _request_priority.get()
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        heapq.heappush(
            self._pending, (priority, next(self._sequence), queued_at, future)
        )
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._release_waiters())
        try:
            await future
            logger.debug(
                "Axiom HTTP request waited %.3fs; priority=%s pending=%s",
                time.monotonic() - queued_at, priority, self.queue_stats()[0],
            )
        except asyncio.CancelledError:
            if future.done() and not future.cancelled():
                self.release_turn()
            future.cancel()
            raise

    async def _release_waiters(self) -> None:
        while self._pending:
            if self._active >= self.max_concurrency:
                self._slot_released.clear()
                await self._slot_released.wait()
                continue
            delay = self._last_start + self.interval_seconds - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            if not self._pending:
                break
            background_positions = (
                [
                    index for index, item in enumerate(self._pending)
                    if item[0] == 1 and not item[3].cancelled()
                ]
                if self._foreground_streak >= MAX_FOREGROUND_BURST else []
            )
            if background_positions:
                position = min(
                    background_positions,
                    key=lambda index: self._pending[index][1],
                )
                priority, _, _, future = self._pending.pop(position)
                heapq.heapify(self._pending)
            else:
                priority, _, _, future = heapq.heappop(self._pending)
            if future.cancelled():
                continue
            self._foreground_streak = (
                self._foreground_streak + 1 if priority == 0 else 0
            )
            self._active += 1
            self._last_start = time.monotonic()
            future.set_result(None)

    def release_turn(self) -> None:
        self._active = max(0, self._active - 1)
        self._slot_released.set()

    def queue_stats(self) -> tuple[int, float]:
        """Return active waiters and age of the oldest queued HTTP request."""
        queued_at = [item[2] for item in self._pending if not item[3].cancelled()]
        if not queued_at:
            return 0, 0.0
        return len(queued_at), time.monotonic() - min(queued_at)

    async def close(self) -> None:
        if self._worker is not None and not self._worker.done():
            self._worker.cancel()
            await asyncio.gather(self._worker, return_exceptions=True)
        for _, _, _, future in self._pending:
            if not future.done():
                future.cancel()
        self._pending.clear()
