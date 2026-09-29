from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass

from .contracts import Connection

logger = logging.getLogger(__name__)
MAX_PENDING_MESSAGES = 64


@dataclass(slots=True)
class ConnectionState:
    kid: str
    pending: asyncio.Queue[dict[str, object]]
    sender: asyncio.Task[None]


class ConnectionManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._by_kid: dict[str, set[Connection]] = defaultdict(set)
        self._connections: dict[Connection, ConnectionState] = {}
        self._closing: set[asyncio.Task[None]] = set()

    async def connect(self, websocket: Connection, *, kid: str) -> None:
        async with self._lock:
            if websocket in self._connections:
                return
            pending: asyncio.Queue[dict[str, object]] = asyncio.Queue(
                maxsize=MAX_PENDING_MESSAGES
            )
            sender = asyncio.create_task(self._send_loop(websocket, pending))
            self._connections[websocket] = ConnectionState(
                kid, pending, sender
            )
            self._by_kid[kid].add(websocket)

    def _remove_locked(self, websocket: Connection) -> ConnectionState | None:
        state = self._connections.pop(websocket, None)
        if state is None:
            return None
        bucket = self._by_kid[state.kid]
        bucket.discard(websocket)
        if not bucket:
            self._by_kid.pop(state.kid, None)
        return state

    async def disconnect(self, websocket: Connection, *, kid: str) -> None:
        async with self._lock:
            state = self._connections.get(websocket)
            if state is None or state.kid != kid:
                return
            self._remove_locked(websocket)
        state.sender.cancel()
        await asyncio.gather(state.sender, return_exceptions=True)

    async def active_sessions_for_kid(self, kid: str) -> int:
        async with self._lock:
            return len(self._by_kid.get(kid, set()))

    async def _send_loop(
        self,
        websocket: Connection,
        pending: asyncio.Queue[dict[str, object]],
    ) -> None:
        try:
            while True:
                message = await pending.get()
                try:
                    await websocket.send_json(message)
                finally:
                    pending.task_done()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("WebSocket send failed", exc_info=True)
            async with self._lock:
                self._remove_locked(websocket)
            self._close_later(websocket)

    def _close_later(
        self,
        websocket: Connection,
        sender: asyncio.Task[None] | None = None,
    ) -> None:
        async def close() -> None:
            try:
                if sender is not None:
                    await asyncio.gather(sender, return_exceptions=True)
                await asyncio.wait_for(websocket.close(code=1013), timeout=1)
            except Exception:
                logger.debug("WebSocket close failed", exc_info=True)

        task = asyncio.create_task(close())
        self._closing.add(task)
        task.add_done_callback(self._closing.discard)

    async def broadcast_json(self, message: dict[str, object]) -> None:
        overflowed: list[tuple[Connection, ConnectionState]] = []
        async with self._lock:
            for websocket, state in tuple(self._connections.items()):
                try:
                    state.pending.put_nowait(message)
                except asyncio.QueueFull:
                    self._remove_locked(websocket)
                    overflowed.append((websocket, state))
        for websocket, state in overflowed:
            logger.warning("WebSocket send queue full; closing slow client")
            state.sender.cancel()
            self._close_later(websocket, state.sender)
