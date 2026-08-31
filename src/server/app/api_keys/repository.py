from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from datetime import timezone

from typing import Protocol

from .domain import ApiKey, ApiKeyStatus
from .models import ApiKeyModel
from .exceptions import ApiKeyAlreadyExistsError, ApiKeyNotFoundError


class ApiKeyRepository(Protocol):
    def __init__(self):
        ...

    async def save_new_api_key(self, api_key: ApiKey) -> None:
        ...

    async def get_api_key_by_kid(self, kid: str) -> ApiKey | None:
        ...

    async def update_api_key(self, api_key: ApiKey) -> ApiKey:
        ...


class SqlAlchemyApiKeyRepository(ApiKeyRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_new_api_key(self, api_key: ApiKey) -> None:
        try:
            api_key_model = ApiKeyModel(
                kid=api_key.kid,
                key_hash=api_key.key_hash,
                label=api_key.label,
                status=api_key.status,
                expires_at=api_key.expires_at,
                max_active_sessions=api_key.max_active_sessions
            )

            self._session.add(api_key_model)

            await self._session.flush()

        except IntegrityError:
            await self._session.rollback()

            raise ApiKeyAlreadyExistsError(
                f"api_key with kid {api_key.kid} already exists"
            )

    async def get_api_key_by_kid(self, kid: str) -> ApiKey | None:
        result = await self._session.execute(
            select(ApiKeyModel).filter_by(kid=kid)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row is not None else None

    async def update_api_key(self, api_key: ApiKey) -> ApiKey:
        result = await self._session.execute(
            select(ApiKeyModel).filter_by(kid=api_key.kid)
        )
        api_key_model = result.scalar_one_or_none()

        if api_key_model is None:
            raise ApiKeyNotFoundError(
                f"api_key with kid {api_key.kid} does not exist"
            )

        api_key_model.key_hash = api_key.key_hash
        api_key_model.label = api_key.label
        api_key_model.status = api_key.status
        api_key_model.expires_at = api_key.expires_at
        api_key_model.max_active_sessions = api_key.max_active_sessions

        await self._session.flush()

        return self._to_domain(api_key_model)

    @staticmethod
    def _to_domain(api_key_model: ApiKeyModel) -> ApiKey:
        expires_at = api_key_model.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return ApiKey(
            kid=api_key_model.kid,
            key_hash=api_key_model.key_hash,
            label=api_key_model.label,
            status=ApiKeyStatus(api_key_model.status),
            expires_at=expires_at,
            max_active_sessions=api_key_model.max_active_sessions,
        )

