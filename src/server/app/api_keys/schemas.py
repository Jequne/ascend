from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from .domain import ApiKey, ApiKeyStatus


class CreateApiKeyRequest(BaseModel):
    expires_in_days: int = Field(default=7, ge=1, le=ApiKey.MAX_EXPIRATION_DAYS)

    max_active_sessions: int = Field(
        default=3, ge=1, le=ApiKey.MAX_ACTIVE_SESSIONS_LIMIT
    )

    label: str | None = None

    @field_validator("label")
    @classmethod
    def reject_explicit_null_label(cls, value: str | None) -> str:
        # The previous str field defaulted to None but rejected explicit null.
        if value is None:
            raise PydanticCustomError("string_type", "Input should be a valid string")
        return value


class CreateApiKeyResponse(BaseModel):
    api_key: str
    kid: str
    expires_at: datetime
    max_active_sessions: int
    label: str | None = None


class ValidApiKeyResponse(BaseModel):
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE
    expires_at: datetime
