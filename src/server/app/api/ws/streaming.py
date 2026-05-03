from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket

from ...services.ws_streaming.manager import ConnectionManager
from ...services.auth.ws_logic import AuthStreamingProcessor
from ...services.ws_streaming.manager import manager


router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    ctx = await AuthStreamingProcessor.connect_if_allowed(websocket)
    
    if not ctx:
        return 
            
    stop = asyncio.Event()

    watchdog_task = asyncio.create_task(
        AuthStreamingProcessor.ws_key_watchdog(
            websocket=websocket,
            raw_key=ctx.raw_key,
            stop=stop
        )
    )

    try:
        while not stop.is_set():
            await websocket.receive()

    except Exception:
        pass
    finally:
        stop.set()
        watchdog_task.cancel()
        await manager.disconnect(websocket, kid=ctx.kid)


