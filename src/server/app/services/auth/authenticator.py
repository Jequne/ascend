from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Header
from sqlalchemy.orm import Session

from ...core.access_keys_helpers import hash_api_key, parse_prefixed_api_key
from ...models.access_key import ApiKey
from ...repositories.access_keys import get_api_key_by_kid


@dataclass(frozen=True, slots=True)
class ApiKeyValidationResult:
    status: str
    kid: str | None = None
    expires_at: datetime | None = None
    max_active_sessions: int | None = None
    label: str | None = None


def extract_raw_api_key(
    *,
    body_key: str | None = None,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> str | None:
    if body_key:
        value = body_key.strip()
        return value or None
    if x_api_key:
        value = x_api_key.strip()
        return value or None
    if authorization:
        value = authorization.strip()
        scheme, sep, credentials = value.partition(" ")
        if sep and scheme.lower() == "bearer":
            token = credentials.strip()
            return token or None
    return None


def validate_api_key(db: Session, raw_key: str) -> ApiKeyValidationResult:
    parsed = parse_prefixed_api_key(raw_key)
    if not parsed:
        return ApiKeyValidationResult(status="invalid")

    kid, full_key = parsed
    expected_hash = hash_api_key(full_key)
    row = get_api_key_by_kid(db, kid)
    if row is None or row.key_hash != expected_hash:
        return ApiKeyValidationResult(status="invalid")

    if row.status == "revoked":
        return ApiKeyValidationResult(
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
            return ApiKeyValidationResult(
                status="expired",
                kid=kid,
                expires_at=row.expires_at,
                max_active_sessions=row.max_active_sessions,
                label=row.label,
            )

    return ApiKeyValidationResult(
        status="valid",
        kid=kid,
        expires_at=row.expires_at,
        max_active_sessions=row.max_active_sessions,
        label=row.label,
    )

