from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from fastapi import WebSocket

from ...database import AsyncSessionLocal
from ...core.authenticator import extract_raw_api_key, validate_api_key_async
from ...core.rate_limit import ws_connect_limiter
from ...schemas.ws_streaming import WsStreamingResponse
from ...database import get_db
from ...services.ws_streaming.manager import manager


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WsAuthContext:
    raw_key: str
    kid: str
    max_active_sessions: int


class AuthStreamingProcessor:
    db = None

    @classmethod
    def map_validation_status_to_ws_reason(cls, status: str) -> str:
        return {
            "invalid": "invalid_key",
            "expired": "expired",
            "revoked": "revoked",
            "rate_limited": "rate_limited",
            "valid": "ok",
        }.get(status, "invalid_key")

    @classmethod
    def is_ws_connect_rate_limited(
            cls,
            websocket: WebSocket, 
            *, 
            limit: int = 12, 
            window_seconds: float = 60.0
            ) -> bool:
        
        client_host = websocket.client.host \
            if websocket.client else "unknown"
        
        return not ws_connect_limiter.allow(
            f"ws:{client_host}", 
            limit=limit, 
            window_seconds=window_seconds
            )

    @classmethod
    async def _ws_send_error_and_close(
            cls,
            websocket: WebSocket, 
            reason: str, 
            *, 
            code: int = 1008
            ) -> None:
        try:
            ws_streaming_response = WsStreamingResponse(
                type="error",
                payload={"reason": reason}
            )
            await websocket.send_json(
                ws_streaming_response.model_dump(mode="json")
                )
        except Exception:
            pass
        try:
            await websocket.close(code=code)
        except Exception:
            pass
    
    @classmethod
    async def extract_ws_api_key(cls, websocket: WebSocket) -> str | None:
        raw = extract_raw_api_key(
            authorization=websocket.headers.get("authorization"),
            x_api_key=websocket.headers.get("x-api-key"),
            body_key=websocket.query_params.get("api_key"),
        )
        if raw:
            return raw
    
    @classmethod
    async def validate_ws_api_key(cls, raw_key: str) -> WsAuthContext | None:
        try:
            async with AsyncSessionLocal() as session:
                result = await validate_api_key_async(session, raw_key)
        except Exception:
            return None

        if result.status != "valid" or not result.kid:
            return None
        max_sessions = result.max_active_sessions or 1
        return WsAuthContext(
            raw_key=raw_key,
            kid=result.kid,
            max_active_sessions=max_sessions,
        )
    
    @classmethod
    async def connect_if_allowed(
        cls, 
        websocket: WebSocket
        ) -> WsAuthContext | False:

        api_key = await cls.extract_ws_api_key(websocket)

        if not api_key:
            await cls._ws_send_error_and_close(
                websocket, 
                reason="the api key was not transferred"
                )
            return False

        ctx: WsAuthContext | None = await cls.validate_ws_api_key(api_key)
        if not ctx:
            await cls._ws_send_error_and_close(
                websocket,
                reason="api key is not valid"
            )
            return False

        active_sessions = await manager.active_sessions_for_kid(ctx.kid)
        if active_sessions >= ctx.max_active_sessions:
            await cls._ws_send_error_and_close(websocket, "too_many_sessions")
            return False

        await manager.connect(websocket, kid=ctx.kid)
        return ctx

    @classmethod
    async def ws_key_watchdog(
        cls,
        *,
        websocket: WebSocket,
        raw_key: str,
        stop: asyncio.Event,
        interval_seconds: float = 30.0,
    ) -> None:
        while not stop.is_set():
            await asyncio.sleep(interval_seconds)

            try:
                async with AsyncSessionLocal() as session:
                    check = await validate_api_key_async(session, raw_key)
            except Exception:
                # on DB errors treat as invalid
                check = None
            if check and check.status == "valid":
                continue
            reason = cls.map_validation_status_to_ws_reason(check.status)
            await cls._ws_send_error_and_close(websocket, reason)
            stop.set()
            break
