from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import logging 

from ...config import settings
from ...core.security import generate_api_key, hash_api_key
from ...database import get_db
from ...models.access_key import ApiKey
from ...schemas.auth import AdminCreateKeyRequest, AdminCreateKeyResponse

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post(
    "/admin/keys",
    response_model=AdminCreateKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    payload: AdminCreateKeyRequest,
    db: Session = Depends(get_db),
    x_admin_secret: str | None = Header(None, alias="X-Admin-Secret"),
) -> AdminCreateKeyResponse:
    if not settings.admin_secret:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Admin key creation disabled: set ADMIN_SECRET in environment",
        )
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid admin secret")

    raw_key, kid = generate_api_key()
    key_hash = hash_api_key(raw_key)

    expires_at: datetime | None = None
    if payload.expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    row = ApiKey(
        kid=kid,
        key_hash=key_hash,
        label=payload.label,
        status="active",
        expires_at=expires_at,
        max_active_sessions=payload.max_active_sessions,
    )
    db.add(row)
    db.commit()

    return AdminCreateKeyResponse(
        api_key=raw_key,
        kid=kid,
        expires_at=expires_at,
        max_active_sessions=payload.max_active_sessions,
        label=payload.label,
    )
