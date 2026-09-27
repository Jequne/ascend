from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from ...adapters.expiry_cleanup import ExpiryCleanup
from ...adapters.models import ApiKeyModel
from ...adapters.sqlalchemy_repository import SqlAlchemyApiKeyRepository


@pytest.mark.asyncio
async def test_cleanup_preserves_batch_size_and_existing_conditions(
    get_engine: AsyncEngine,
) -> None:
    sessions = async_sessionmaker(get_engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    async with sessions() as session:
        for index in range(201):
            session.add(
                ApiKeyModel(
                    kid=f"expired-{index}",
                    key_hash="hash",
                    status="active",
                    expires_at=now - timedelta(days=1),
                    max_active_sessions=1,
                )
            )
        session.add(
            ApiKeyModel(
                kid="revoked",
                key_hash="hash",
                status="revoked",
                expires_at=now + timedelta(days=1),
                revoked_at=now,
                max_active_sessions=1,
            )
        )
        session.add(
            ApiKeyModel(
                kid="status-expired",
                key_hash="hash",
                status="expired",
                expires_at=now + timedelta(days=1),
                max_active_sessions=1,
            )
        )
        await session.commit()
    cleanup = ExpiryCleanup(sessions)
    assert await cleanup.remove_expired() is True
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(ApiKeyModel)) == 3
    assert await cleanup.remove_expired() is True
    assert await cleanup.remove_expired() is False
    async with sessions() as session:
        key = await SqlAlchemyApiKeyRepository(session).get_api_key_by_kid("revoked")
        assert key is not None and key.revoked_at is None
        row = await session.scalar(
            select(ApiKeyModel).where(ApiKeyModel.kid == "revoked")
        )
        assert row is not None and row.revoked_at is not None
