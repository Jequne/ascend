from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass

from .contracts import Connection

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConnectionRef:
    websocket: Connection
    kid: str


class ConnectionManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._by_kid: dict[str, set[Connection]] = defaultdict(set)

    async def connect(self, websocket: Connection, *, kid: str) -> None:
        async with self._lock:
            self._by_kid[kid].add(websocket)

    async def disconnect(self, websocket: Connection, *, kid: str) -> None:
        async with self._lock:
            bucket = self._by_kid.get(kid)
            if not bucket:
                return
            bucket.discard(websocket)
            if not bucket:
                self._by_kid.pop(kid, None)

    async def active_sessions_for_kid(self, kid: str) -> int:
        async with self._lock:
            return len(self._by_kid.get(kid, set()))

    async def broadcast_json(self, message: dict[str, object]) -> None:
        async with self._lock:
            sockets: list[Connection] = []
            for bucket in self._by_kid.values():
                sockets.extend(list(bucket))

        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning("🔔 Problem sending message: %s", e)
