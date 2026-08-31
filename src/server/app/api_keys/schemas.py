from pydantic import BaseModel, Field

from datetime import datetime

from .domain import ApiKey, ApiKeyStatus


class CreateApiKeyRequest(BaseModel):
    expires_in_days: int = \
        Field(default=7, ge=1, le=ApiKey.MAX_EXPIRATION_DAYS) 
    
    max_active_sessions: int = \
        Field(default= 3, ge=1, le=ApiKey.MAX_ACTIVE_SESSIONS_LIMIT)

    label: str = None


class CreateApiKeyResponse(BaseModel):
    api_key: str
    kid: str
    expires_at: datetime 
    max_active_sessions: int
    label: str | None = None


class ValidApiKeyResponse(BaseModel):
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE
    expires_at: datetime