from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.access_key import ApiKey


def get_api_key_by_kid(db: Session, kid: str) -> ApiKey | None:
    return db.scalars(select(ApiKey).where(ApiKey.kid == kid)).first()


async def get_api_key_by_kid_async(db: AsyncSession, kid: str) -> ApiKey | None:
    result = await db.scalars(select(ApiKey).where(ApiKey.kid == kid))
    return result.first()


def set_api_key_status_as_expired(db: Session, kid: str):
    pass

