from datetime import datetime, timezone

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import ApiKeyModel


class ExpiryCleanup:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self._sessions = sessions

    async def remove_expired(self) -> bool | None:
        async with self._sessions() as session:
            try:
                ids = (
                    await session.scalars(
                        select(ApiKeyModel.id)
                        .where(
                            or_(
                                ApiKeyModel.status == "expired",
                                and_(
                                    ApiKeyModel.expires_at.is_not(None),
                                    ApiKeyModel.expires_at
                                    < datetime.now(timezone.utc),
                                ),
                            )
                        )
                        .limit(200)
                    )
                ).all()
                if not ids:
                    return False
                await session.execute(
                    delete(ApiKeyModel).where(ApiKeyModel.id.in_(ids))
                )
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                return None
