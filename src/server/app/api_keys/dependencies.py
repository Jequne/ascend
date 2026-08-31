from fastapi import Header, HTTPException, status, Depends

from typing import Annotated

from ..config import settings
from .api_key_manager import ApiKeyManager
from .repository import ApiKeyRepository, SqlAlchemyApiKeyRepository
from ..database import get_async_db



def require_admin_credentials(
    x_admin_secret: Annotated[str | None, Header(alias="X-Admin-Secret")] = None
) -> None:
    if x_admin_secret is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No X-Admin-Secret"
        )

    if x_admin_secret != settings.admin_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect X-Admin-Secret"
        )


def get_sqlalchemy_repository(
    session = Depends(get_async_db)
) -> ApiKeyRepository:
    sql_alchemy_repository = SqlAlchemyApiKeyRepository(
        session=session
    )
    return sql_alchemy_repository


def get_api_key_manager(
    repository = Depends(get_sqlalchemy_repository)
) -> ApiKeyManager:
    return ApiKeyManager(
        repository=repository
    )


def require_x_api_key_credentials(
    x_api_key: Annotated[
        str | None, 
        Header(alias="X-Api-Key", max_length=70)
    ] = None
) -> str:
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No X-Api-Secret"
        )
    
    return x_api_key