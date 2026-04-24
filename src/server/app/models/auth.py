from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field


class PrincipalType(str, Enum):
    ACCESS_KEY = "access_key"
    USER = "user"
    SERVICE_ACCOUNT = "service_account"


class AuthMethod(str, Enum):
    API_KEY = "api_key"
    JWT = "jwt"
    SESSION = "session"


class AccessKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AuthScope(str, Enum):
    AUTH_ADMIN = "auth:admin"
    ACCESS_KEYS_READ = "access_keys:read"
    ACCESS_KEYS_WRITE = "access_keys:write"
    TOKEN_FEED_READ = "token_feed:read"
    TOKEN_FEED_WRITE = "token_feed:write"
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"


def normalize_scope(scope: str) -> str:
    return scope.strip().lower()


def normalize_scopes(scopes: Sequence[str] | None) -> list[str]:
    if not scopes:
        return []
    normalized = {normalize_scope(scope) for scope in scopes if scope and scope.strip()}
    return sorted(normalized)


def scope_matches(granted_scope: str, required_scope: str) -> bool:
    granted = normalize_scope(granted_scope)
    required = normalize_scope(required_scope)
    if granted == "*" or granted == required:
        return True
    if granted.endswith("*"):
        return required.startswith(granted[:-1])
    return False


class AuthContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    principal_type: PrincipalType = PrincipalType.ACCESS_KEY
    principal_id: str
    auth_method: AuthMethod = AuthMethod.API_KEY
    scopes: list[str] = Field(default_factory=list)
    key_id: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    def has_scope(self, required_scope: str) -> bool:
        return any(scope_matches(granted, required_scope) for granted in self.scopes)

    def has_any_scope(self, required_scopes: Sequence[str]) -> bool:
        return any(self.has_scope(scope) for scope in required_scopes)

    def has_all_scopes(self, required_scopes: Sequence[str]) -> bool:
        return all(self.has_scope(scope) for scope in required_scopes)