import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from .sessions import ConnectionManager

logger = logging.getLogger(__name__)


async def token_feed_broadcaster(
    manager: ConnectionManager,
    next_payload: Callable[[], Awaitable[dict[str, object]]],
    *,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        try:
            payload = await asyncio.wait_for(next_payload(), timeout=3)
        except asyncio.TimeoutError:
            continue
        await manager.broadcast_json(
            {"type": "token_feed", "payload": payload}
        )


async def ping_broadcaster(
    manager: ConnectionManager,
    *,
    stop_event: asyncio.Event,
    interval: float = 30,
) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            pass
        try:
            await manager.broadcast_json(
                {
                    "type": "ping",
                    "payload": {
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                }
            )
        except Exception:
            logger.exception("Error in ping_broadcaster")
