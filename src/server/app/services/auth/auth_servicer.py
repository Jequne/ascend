from fastapi import APIRouter, Body, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.auth import ValidateKeyRequest, ValidateKeyResponse
from ...core.rate_limit import validate_key_limiter
from ...core.authenticator import extract_raw_api_key, validate_api_key_async


class AuthServicer:

    @staticmethod
    async def validate_key(
        request: Request,
        response: Response,
        db: AsyncSession,
        body: ValidateKeyRequest,
        authorization: str,
        x_api_key: str 
    ) -> ValidateKeyResponse:
        client_host = request.client.host if request.client else "unknown"
        if not validate_key_limiter.allow(
            f"validate:{client_host}",
            limit=40,
            window_seconds=60.0,
        ):
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return ValidateKeyResponse(status="rate_limited")

        raw = extract_raw_api_key(
            body_key=body.api_key if body else None,
            authorization=authorization,
            x_api_key=x_api_key,
        )
        if not raw:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return ValidateKeyResponse(status="invalid")

        result = await validate_api_key_async(db, raw)

        if result.status != "valid":
            response.status_code = status.HTTP_401_UNAUTHORIZED

        return ValidateKeyResponse(
            status=result.status,  
            kid=result.kid,
            expires_at=result.expires_at,
            max_active_sessions=result.max_active_sessions,
            label=result.label,
        )