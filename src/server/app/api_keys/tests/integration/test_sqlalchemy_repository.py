import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from datetime import datetime, timedelta, timezone

from ...repository import (
    ApiKeyAlreadyExistsError,
    ApiKeyNotFoundError,
    SqlAlchemyApiKeyRepository,
)
from ...domain import ApiKey, ApiKeyStatus
from ...models import ApiKeyModel


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_saving_new_api_key_in_db(session: AsyncSession) -> None:
    repository = SqlAlchemyApiKeyRepository(session=session)

    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=1,
        key_hash="key_hash",
        label="label"
    )

    await repository.save_new_api_key(api_key)

    stmt = select(ApiKeyModel).filter_by(kid=api_key.kid)
    result = await session.execute(stmt)
    saved_api_key = result.scalar_one()

    assert saved_api_key.kid == api_key.kid
    assert saved_api_key.key_hash == api_key.key_hash
    assert saved_api_key.label == api_key.label
    assert saved_api_key.status == api_key.status
    assert saved_api_key.expires_at.replace(tzinfo=timezone.utc) \
        == api_key.expires_at
    assert saved_api_key.max_active_sessions == api_key.max_active_sessions


@pytest.mark.asyncio
async def test_saving_api_key_which_already_in_db(session: AsyncSession) -> None:
    repository = SqlAlchemyApiKeyRepository(session=session)
    
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=1,
        key_hash="key_hash",
        label="label"
    )

    await repository.save_new_api_key(api_key)

    # Еще раз сохраняем и ожидаем ошибку
    with pytest.raises(ApiKeyAlreadyExistsError):
        await repository.save_new_api_key(api_key)


@pytest.mark.asyncio
async def test_get_api_key_by_kid_when_it_not_in_db(session: AsyncSession):
    repository = SqlAlchemyApiKeyRepository(session=session)

    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=1,
        key_hash="key_hash",
        label="old label",
    )
    api_key_from_db = await repository.get_api_key_by_kid(api_key.kid)
    assert api_key_from_db == None


@pytest.mark.asyncio
async def test_get_api_key_by_kid_when_it_in_db(session: AsyncSession):
    repository = SqlAlchemyApiKeyRepository(session=session)
    
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=1,
        key_hash="key_hash",
        label="old label",
    )

    await repository.save_new_api_key(api_key=api_key)

    api_key_from_db = await repository.get_api_key_by_kid(api_key.kid)
    api_key_from_db.expires_at = \
        api_key_from_db.expires_at.replace(tzinfo=timezone.utc)
    assert api_key_from_db == api_key


@pytest.mark.asyncio
async def test_updating_api_key_in_db(session: AsyncSession) -> None:
    repository = SqlAlchemyApiKeyRepository(session=session)
    api_key = ApiKey(
        kid="kid",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=1,
        key_hash="key_hash",
        label="old label",
    )
    await repository.save_new_api_key(api_key)

    api_key.label = "new label"
    api_key.status = ApiKeyStatus.REVOKED
    api_key.max_active_sessions = 2

    updated_api_key = await repository.update_api_key(api_key)

    result = await session.execute(
        select(ApiKeyModel).filter_by(kid=api_key.kid)
    )
    saved_api_key = result.scalar_one()

    assert updated_api_key == api_key
    assert saved_api_key.label == "new label"
    assert saved_api_key.status == ApiKeyStatus.REVOKED
    assert saved_api_key.max_active_sessions == 2


@pytest.mark.asyncio
async def test_updating_missing_api_key_raises_error(
    session: AsyncSession,
) -> None:
    repository = SqlAlchemyApiKeyRepository(session=session)
    api_key = ApiKey(
        kid="missing",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        max_active_sessions=1,
        key_hash="key_hash",
    )

    with pytest.raises(ApiKeyNotFoundError):
        await repository.update_api_key(api_key)
