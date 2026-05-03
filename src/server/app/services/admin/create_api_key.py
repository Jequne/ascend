from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from ...config import settings
from ...schemas.auth import AdminCreateKeyRequest, AdminCreateKeyResponse
from ...core.access_keys_helpers import generate_api_key, hash_api_key
from ...models.access_key import ApiKey


class AdminServices:
    def _check_admin_secret(x_admin_secret: str):
        if not settings.admin_secret:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Admin key creation disabled: set ADMIN_SECRET in environment",
            )
        if x_admin_secret != settings.admin_secret:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid admin secret")
    
    @classmethod
    def create_api_key(
            cls,
            payload: AdminCreateKeyRequest, 
            db: Session,
            x_admin_secret: str
            ) -> AdminCreateKeyResponse:
        cls._check_admin_secret(x_admin_secret)

        raw_key, kid = generate_api_key()
        key_hash = hash_api_key(raw_key)

        expires_at: datetime | None = None
        if payload.expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) \
                + timedelta(days=payload.expires_in_days)

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

