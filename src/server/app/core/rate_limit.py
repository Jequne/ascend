from __future__ import annotations

import time
from collections import defaultdict


class SlidingWindowLimiter:
    """In-process limiter; достаточно для одного воркера MVP."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str, *, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - window_seconds
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


validate_key_limiter = SlidingWindowLimiter()

ws_connect_limiter = SlidingWindowLimiter()
