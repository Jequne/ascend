from fastapi import APIRouter, status, Depends, HTTPException

from .schemas import (
    CreateApiKeyResponse, 
    CreateApiKeyRequest,
    ValidApiKeyResponse
    )
from .dependencies import (
    require_admin_credentials, 
    get_api_key_manager,
    require_x_api_key_credentials
)
from .api_key_manager import (
    ApiKeyManager, 
    CreateApiKeyCommand,
    ValidApiKeyResult
)

from .exceptions import *


router = APIRouter(tags=["api-keys"], prefix="/api-keys")


@router.post(
    "/create-api-key",
    response_model=CreateApiKeyResponse,
    status_code=status.HTTP_201_CREATED
    )
async def create_api_key(
    payload: CreateApiKeyRequest,
    _ = Depends(require_admin_credentials),
    api_key_manager: ApiKeyManager = Depends(get_api_key_manager),
) -> CreateApiKeyResponse:
    try:
        created_api_key = await api_key_manager.create(
            CreateApiKeyCommand(
                expires_in_days=payload.expires_in_days,
                max_active_sessions=payload.max_active_sessions,
                label=payload.label
            )
        )

        return CreateApiKeyResponse(
            api_key=created_api_key.api_key,
            kid=created_api_key.kid,
            expires_at=created_api_key.expires_at,
            max_active_sessions=created_api_key.max_active_sessions,
            label=created_api_key.label
        )

    except ApiKeyAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Api Key Creation Error"
        ) from exc


@router.post(
    "/validate-api-key",
    response_model=ValidApiKeyResponse,
    status_code=status.HTTP_200_OK
)
async def validate_api_key(
    x_api_key: str = Depends(require_x_api_key_credentials),
    api_key_manager: ApiKeyManager = Depends(get_api_key_manager)
) -> ValidApiKeyResponse:
    try:
        validate_api_key_result: ValidApiKeyResult = \
            await api_key_manager.validate(
                x_api_key
            )

        return ValidApiKeyResponse(
            status=validate_api_key_result.status,
            expires_at=validate_api_key_result.expires_at
        )

    except (ApiKeyNotFoundError, InvalidApiKeyFormat, ApiKeyRevocationError,
            ApiKeyExpirationError, InvalidApiKeyError
        ) as exc:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
                ) from exc


    