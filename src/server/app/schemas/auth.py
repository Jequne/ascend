from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ValidateKeyRequest(BaseModel):
    api_key: str | None = Field(
        default=None,
        description="Если не передан — берётся из Authorization / X-API-Key",
    )


class ValidateKeyResponse(BaseModel):
    status: Literal["valid", "invalid", "expired", "revoked", "rate_limited"]
    kid: str | None = None
    expires_at: datetime | None = None
    max_active_sessions: int | None = None
    label: str | None = None


class AdminCreateKeyRequest(BaseModel):
    label: str | None = None
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        description="None = без срока истечения",
    )
    max_active_sessions: int = Field(default=3, ge=1, le=1000)


class AdminCreateKeyResponse(BaseModel):
    api_key: str
    kid: str
    expires_at: datetime | None = None
    max_active_sessions: int
    label: str | None = None
