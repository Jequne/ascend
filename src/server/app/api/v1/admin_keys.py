from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import logging 

from ...config import settings
from ...core.access_keys_helpers import generate_api_key, hash_api_key
from ...database import get_db
from ...models.access_key import ApiKey
from ...schemas.auth import AdminCreateKeyRequest, AdminCreateKeyResponse
from ...services.admin import AdminServices

router = APIRouter(prefix="/admin")

logger = logging.getLogger(__name__)

@router.post(
    "/create-api-key",
    response_model=AdminCreateKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    payload: AdminCreateKeyRequest,
    db: Session = Depends(get_db),
    x_admin_secret: str | None = Header(None, alias="X-Admin-Secret"),
) -> AdminCreateKeyResponse:
    
    return AdminServices.create_api_key(
        payload=payload,
        db=db,
        x_admin_secret=x_admin_secret
    )
