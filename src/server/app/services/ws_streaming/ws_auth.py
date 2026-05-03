from __future__ import annotations

import asyncio
from dataclasses import dataclass

from fastapi import WebSocket
from sqlalchemy.orm import Session

from ..auth.api_keys import extract_raw_api_key, validate_api_key
from ...core.rate_limit import ws_connect_limiter


@dataclass(frozen=True, slots=True)
class WsAuthContext:
    raw_key: str
    kid: str
    max_active_sessions: int


async def await_auth_message(websocket: WebSocket, *, timeout_seconds: float = 5.0) -> str | None:
    try:
        data = await asyncio.wait_for(websocket.receive_json(), timeout=timeout_seconds)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("type") != "auth":
        return None
    api_key = data.get("api_key")
    if not isinstance(api_key, str):
        return None
    value = api_key.strip()
    return value or None


def map_validation_status_to_ws_reason(status: str) -> str:
    return {
        "invalid": "invalid_key",
        "expired": "expired",
        "revoked": "revoked",
        "rate_limited": "rate_limited",
        "valid": "ok",
    }.get(status, "invalid_key")


def is_ws_connect_rate_limited(websocket: WebSocket, *, limit: int = 12, window_seconds: float = 60.0) -> bool:
    client_host = websocket.client.host if websocket.client else "unknown"
    return not ws_connect_limiter.allow(f"ws:{client_host}", limit=limit, window_seconds=window_seconds)


async def extract_ws_api_key(websocket: WebSocket) -> str | None:
    raw = extract_raw_api_key(
        authorization=websocket.headers.get("authorization"),
        x_api_key=websocket.headers.get("x-api-key"),
        body_key=websocket.query_params.get("api_key"),
    )
    if raw:
        return raw
    return await await_auth_message(websocket)


def validate_ws_api_key(db: Session, raw_key: str) -> WsAuthContext | None:
    result = validate_api_key(db, raw_key)
    if result.status != "valid" or not result.kid:
        return None
    max_sessions = result.max_active_sessions or 1
    return WsAuthContext(raw_key=raw_key, kid=result.kid, max_active_sessions=max_sessions)


def validate_ws_api_key_with_status(db: Session, raw_key: str) -> tuple[WsAuthContext | None, str]:
    result = validate_api_key(db, raw_key)
    if result.status != "valid" or not result.kid:
        return None, result.status
    max_sessions = result.max_active_sessions or 1
    return WsAuthContext(raw_key=raw_key, kid=result.kid, max_active_sessions=max_sessions), "valid"


async def ws_key_watchdog(
    *,
    websocket: WebSocket,
    db: Session,
    raw_key: str,
    stop: asyncio.Event,
    close_fn,
    interval_seconds: float = 30.0,
) -> None:
    while not stop.is_set():
        await asyncio.sleep(interval_seconds)
        check = validate_api_key(db, raw_key)
        if check.status == "valid":
            continue
        reason = map_validation_status_to_ws_reason(check.status)
        await close_fn(websocket, reason)
        stop.set()
        break

