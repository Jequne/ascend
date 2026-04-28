from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging

from .collector import TokenFeedCollector
from ..ws.manager import ConnectionManager


logger = logging.getLogger(__name__)


async def token_feed_broadcaster(
        manager: ConnectionManager, 
        *, 
        stop_event: asyncio.Event
        ) -> None:

    while not stop_event.is_set():
        try:
            item = \
                await asyncio.wait_for(
                    TokenFeedCollector.tokens_feed.get(), timeout=0.5
                    )
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error("ERORR NIGGER: %s", e)

        message = {
            "type": "token_feed",
            "payload": item.model_dump(mode="json"),
        }
        logger.debug(
            "message type: %s\n 'payload' type: %s", 
            type(message),
            type(message["payload"])
            )
        await manager.broadcast_json(message)

