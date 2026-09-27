"""Shared pacing for authenticated Axiom HTTP calls."""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from itertools import chain

FOREGROUND = 0
BACKGROUND = 1

_request_priority: ContextVar[int] = ContextVar(
    "axiom_request_priority", default=FOREGROUND
)
logger = logging.getLogger(__name__)
MAX_FOREGROUND_BURST = 10


@dataclass(slots=True)
class PendingRequest:
    queued_at: float
    ready: asyncio.Future[None]


@contextmanager
def background_axiom_request() -> Generator[None, None, None]:
    token = _request_priority.set(BACKGROUND)
    try:
        yield
    finally:
        _request_priority.reset(token)


class AxiomRequestPacer:
    def __init__(
        self, interval_seconds: float = 0.1, max_concurrency: int = 50
    ) -> None:
        if interval_seconds < 0 or max_concurrency < 1:
            raise ValueError(
                "Axiom pacing requires a nonnegative interval and slots"
            )
        self.interval_seconds = interval_seconds
        self.max_concurrency = max_concurrency
        self._foreground: deque[PendingRequest] = deque()
        self._background: deque[PendingRequest] = deque()
        self._worker: asyncio.Task[None] | None = None
        self._last_start = 0.0
        self._active = 0
        self._slot_released = asyncio.Event()
        self._foreground_streak = 0

    async def wait_turn(self) -> None:
        queued_at = time.monotonic()
        priority = _request_priority.get()
        future: asyncio.Future[None] = (
            asyncio.get_running_loop().create_future()
        )
        queue = (
            self._background if priority == BACKGROUND else self._foreground
        )
        queue.append(PendingRequest(queued_at, future))
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._release_waiters())
        try:
            await future
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Axiom HTTP request waited %.3fs; priority=%s pending=%s",
                    time.monotonic() - queued_at,
                    priority,
                    self.queue_stats()[0],
                )
        except asyncio.CancelledError:
            if future.done() and not future.cancelled():
                self.release_turn()
            future.cancel()
            raise

    async def _release_waiters(self) -> None:
        while self._foreground or self._background:
            if self._active >= self.max_concurrency:
                self._slot_released.clear()
                await self._slot_released.wait()
                continue
            delay = self._last_start + self.interval_seconds - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            request = self._next_request()
            if request is None:
                break
            self._active += 1
            self._last_start = time.monotonic()
            request.ready.set_result(None)

    def _next_request(self) -> PendingRequest | None:
        # Each queue is FIFO; cancelled entries never consume a turn.
        for queue in (self._foreground, self._background):
            while queue and queue[0].ready.cancelled():
                queue.popleft()

        if self._background and (
            not self._foreground
            or self._foreground_streak >= MAX_FOREGROUND_BURST
        ):
            self._foreground_streak = 0
            return self._background.popleft()
        if self._foreground:
            self._foreground_streak += 1
            return self._foreground.popleft()
        return None

    def release_turn(self) -> None:
        self._active = max(0, self._active - 1)
        self._slot_released.set()

    def queue_stats(self) -> tuple[int, float]:
        """Return active waiters and age of the oldest queued HTTP request."""
        queued_at = [
            request.queued_at
            for request in chain(self._foreground, self._background)
            if not request.ready.cancelled()
        ]
        if not queued_at:
            return 0, 0.0
        return len(queued_at), time.monotonic() - min(queued_at)

    async def close(self) -> None:
        if self._worker is not None and not self._worker.done():
            self._worker.cancel()
            await asyncio.gather(self._worker, return_exceptions=True)
        for queue in (self._foreground, self._background):
            for request in queue:
                if not request.ready.done():
                    request.ready.cancel()
            queue.clear()
