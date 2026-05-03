from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.access_key import ApiKey


def get_api_key_by_kid(db: Session, kid: str) -> ApiKey | None:
    return db.scalars(select(ApiKey).where(ApiKey.kid == kid)).first()

