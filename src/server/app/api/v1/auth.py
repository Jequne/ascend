from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.rate_limit import validate_key_limiter
from ...core.security import hash_api_key, parse_prefixed_api_key
from ...database import get_db
from ...models.api_key import ApiKey
from ...schemas.auth import ValidateKeyRequest, ValidateKeyResponse

router = APIRouter()


def _extract_raw_key(
    body: ValidateKeyRequest | None,
    authorization: str | None,
    x_api_key: str | None,
) -> str | None:
    if body and body.api_key:
        return body.api_key.strip()
    if x_api_key:
        return x_api_key.strip()
    if authorization:
        value = authorization.strip()
        scheme, sep, credentials = value.partition(" ")
        if sep and scheme.lower() == "bearer":
            token = credentials.strip()
            return token or None
    return None


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

    raw = _extract_raw_key(body, authorization, x_api_key)
    if not raw:
        return ValidateKeyResponse(status="invalid")

    parsed = parse_prefixed_api_key(raw)
    if not parsed:
        return ValidateKeyResponse(status="invalid")

    kid, full_key = parsed
    expected_hash = hash_api_key(full_key)
    row = db.scalars(select(ApiKey).where(ApiKey.kid == kid)).first()
    if row is None or row.key_hash != expected_hash:
        return ValidateKeyResponse(status="invalid")

    if row.status == "revoked":
        return ValidateKeyResponse(
            status="revoked",
            kid=kid,
            expires_at=row.expires_at,
            max_active_sessions=row.max_active_sessions,
            label=row.label,
        )

    if row.expires_at is not None:
        now = datetime.now(timezone.utc)
        exp = row.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if now > exp:
            return ValidateKeyResponse(
                status="expired",
                kid=kid,
                expires_at=row.expires_at,
                max_active_sessions=row.max_active_sessions,
                label=row.label,
            )

    return ValidateKeyResponse(
        status="valid",
        kid=kid,
        expires_at=row.expires_at,
        max_active_sessions=row.max_active_sessions,
        label=row.label,
    )
