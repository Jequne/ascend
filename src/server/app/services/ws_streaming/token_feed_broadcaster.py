from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging

from ..token_feed.collector import TokenFeedCollector
from .manager import ConnectionManager
from ...schemas.ws_streaming import WsStreamingResponse


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

        ws_streaming_response = WsStreamingResponse(
            type="token_feed",
            payload=item
        )

        await manager.broadcast_json(
            ws_streaming_response.model_dump(mode="json")
            )

        # message = {
        #     "type": "token_feed",
        #     "payload": item.model_dump(mode="json"),
        # }
        # logger.debug(
        #     "message type: %s\n 'payload' type: %s", 
        #     type(message),
        #     type(message["payload"])
        #     )
        # await manager.broadcast_json(message)

