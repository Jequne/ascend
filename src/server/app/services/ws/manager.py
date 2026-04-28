from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
import logging

from fastapi import WebSocket


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConnectionRef:
    websocket: WebSocket
    kid: str


class ConnectionManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._by_kid: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, *, kid: str) -> None:
        async with self._lock:
            self._by_kid[kid].add(websocket)

    async def disconnect(self, websocket: WebSocket, *, kid: str) -> None:
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

    async def broadcast_json(self, message: dict) -> None:
        async with self._lock:
            sockets: list[WebSocket] = []
            for bucket in self._by_kid.values():
                sockets.extend(list(bucket))

        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning("🔔 Problem sending message: %s", e)
                

