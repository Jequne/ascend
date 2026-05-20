from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from .manager import ConnectionManager
from ...schemas.ws_streaming import WsStreamingResponse

logger = logging.getLogger(__name__)

async def ping_broadcaster(
        manager: ConnectionManager, 
        *, 
        stop_event: asyncio.Event,
        interval: int = 12
) -> None:
    logger.info("Ping broadcaster started.")
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            break 
        except asyncio.TimeoutError:
            pass  

        try:
            ws_streaming_response = WsStreamingResponse(
                type="ping",
                payload={"timestamp": datetime.now(timezone.utc).isoformat()}
            )
            await manager.broadcast_json(ws_streaming_response.model_dump(mode="json"))
        except Exception as e:
            logger.error("Error in ping_broadcaster: %s", e)
