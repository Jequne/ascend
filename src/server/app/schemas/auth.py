from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.auth import AccessKeyStatus, normalize_scopes


class AccessKeyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    owner_type: str | None = Field(default=None, max_length=64)
    owner_id: str | None = Field(default=None, max_length=128)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None

    @field_validator("scopes", mode="before")
    @classmethod
    def normalize_requested_scopes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return normalize_scopes([str(item) for item in value])
        if isinstance(value, str):
            return normalize_scopes([value])
        raise TypeError("scopes must be a list of strings")


class AccessKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    owner_type: str | None
    owner_id: str | None
    status: AccessKeyStatus
    scopes: list[str]
    token_prefix: str
    version: int
    issued_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
    last_used_ip: str | None
    usage_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_revoked: bool
    is_expired: bool


class IssuedAccessKey(BaseModel):
    access_key: str
    secret: str
    key: AccessKeyRead


class AccessKeyRotateResponse(BaseModel):
    access_key: str
    secret: str
    key: AccessKeyRead


class AuthContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    principal_type: str
    principal_id: str
    auth_method: str
    scopes: list[str]
    key_id: str | None
    issued_at: datetime | None
    expires_at: datetime | None
    metadata: dict[str, str]


class ScopeCheckRequest(BaseModel):
    required_scopes: list[str] = Field(default_factory=list)

    @field_validator("required_scopes", mode="before")
    @classmethod
    def normalize_required_scopes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return normalize_scopes([str(item) for item in value])
        if isinstance(value, str):
            return normalize_scopes([value])
        raise TypeError("required_scopes must be a list of strings")