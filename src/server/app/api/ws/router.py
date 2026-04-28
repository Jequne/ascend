from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket
from sqlalchemy.orm import Session

from ...database import SessionLocal
from ...services.ws.ws_auth import (
    extract_ws_api_key,
    is_ws_connect_rate_limited,
    map_validation_status_to_ws_reason,
    validate_ws_api_key_with_status,
    ws_key_watchdog,
)
from ...services.ws.manager import ConnectionManager


router = APIRouter()
manager = ConnectionManager()


async def _ws_send_error_and_close(websocket: WebSocket, reason: str, *, code: int = 1008) -> None:
    try:
        await websocket.send_json({"type": "error", "reason": reason})
    except Exception:
        pass
    try:
        await websocket.close(code=code)
    except Exception:
        pass


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    if is_ws_connect_rate_limited(websocket, limit=12, window_seconds=60.0):
        await _ws_send_error_and_close(websocket, "rate_limited", code=1013)
        return

    raw = await extract_ws_api_key(websocket)
    if not raw:
        await _ws_send_error_and_close(websocket, "invalid_key")
        return

    db: Session = SessionLocal()
    try:
        ctx, status = validate_ws_api_key_with_status(db, raw)
        if ctx is None:
            reason = map_validation_status_to_ws_reason(status)
            await _ws_send_error_and_close(websocket, reason)
            return

        active = await manager.active_sessions_for_kid(ctx.kid)
        if active >= ctx.max_active_sessions:
            await _ws_send_error_and_close(websocket, "too_many_sessions")
            return

        await manager.connect(websocket, kid=ctx.kid)

        stop = asyncio.Event()
        watchdog_task = asyncio.create_task(
            ws_key_watchdog(
                websocket=websocket,
                db=db,
                raw_key=ctx.raw_key,
                stop=stop,
                close_fn=_ws_send_error_and_close,
                interval_seconds=30.0,
            )
        )

        try:
            while not stop.is_set():
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if message.get("type") == "websocket.receive":
                    if "text" in message and message["text"] == "ping":
                        await websocket.send_text("pong")
        except Exception:
            pass
        finally:
            stop.set()
            watchdog_task.cancel()
            await manager.disconnect(websocket, kid=ctx.kid)
    finally:
        db.close()

