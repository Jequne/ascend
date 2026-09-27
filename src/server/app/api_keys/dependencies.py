from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_async_db
from .adapters.sqlalchemy_repository import SqlAlchemyApiKeyRepository
from .api_key_hasher import ApiKeyHasher
from .api_key_manager import ApiKeyManager
from .contracts import ApiKeyRepository


def require_admin_credentials(
    x_admin_secret: Annotated[str | None, Header(alias="X-Admin-Secret")] = None,
) -> None:
    if x_admin_secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No X-Admin-Secret"
        )

    if x_admin_secret != settings.admin_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect X-Admin-Secret"
        )


def get_sqlalchemy_repository(
    session: AsyncSession = Depends(get_async_db),
) -> ApiKeyRepository:
    sql_alchemy_repository = SqlAlchemyApiKeyRepository(session=session)
    return sql_alchemy_repository


def get_api_key_manager(
    repository: ApiKeyRepository = Depends(get_sqlalchemy_repository),
) -> ApiKeyManager:
    return ApiKeyManager(
        repository=repository, api_key_hasher=ApiKeyHasher(settings.api_key_pepper)
    )


def require_x_api_key_credentials(
    x_api_key: Annotated[str | None, Header(alias="X-Api-Key", max_length=70)] = None,
) -> str:
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No X-Api-Secret"
        )

    return x_api_key
