from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Header, Request
from sqlalchemy.orm import Session

from ...core.rate_limit import validate_key_limiter
from ...services.auth.api_keys import extract_raw_api_key, validate_api_key
from ...database import get_db
from ...schemas.auth import ValidateKeyRequest, ValidateKeyResponse

router = APIRouter()


@router.post("/auth/validate-key", response_model=ValidateKeyResponse)
def validate_key(
    request: Request,
    db: Session = Depends(get_db),
    body: ValidateKeyRequest | None = Body(None),
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> ValidateKeyResponse:
    client_host = request.client.host if request.client else "unknown"
    if not validate_key_limiter.allow(
        f"validate:{client_host}",
        limit=40,
        window_seconds=60.0,
    ):
        return ValidateKeyResponse(status="rate_limited")

    raw = extract_raw_api_key(
        body_key=body.api_key if body else None,
        authorization=authorization,
        x_api_key=x_api_key,
    )
    if not raw:
        return ValidateKeyResponse(status="invalid")

    result = validate_api_key(db, raw)
    return ValidateKeyResponse(
        status=result.status,  
        kid=result.kid,
        expires_at=result.expires_at,
        max_active_sessions=result.max_active_sessions,
        label=result.label,
    )
