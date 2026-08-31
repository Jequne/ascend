from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar
from enum import StrEnum

from .exceptions import InvalidApiKeyFormat


class ApiKeyStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(slots=True)
class ApiKey:
    kid: str
    expires_at: datetime
    key_hash: str
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE 
    label: str = None
    max_active_sessions: int = 3
    revoked_at: datetime = None

    # Чтобы не было видно, что это поле класса при создании объекта ApiKey
    MAX_ACTIVE_SESSIONS_LIMIT: ClassVar[int] = 5 
    MAX_EXPIRATION_DAYS: ClassVar[int] = 30

    def __post_init__(self):
        if self.max_active_sessions < 1 or \
            self.max_active_sessions >= self.MAX_ACTIVE_SESSIONS_LIMIT:
            raise ValueError(
                f"{self.max_active_sessions} \
                should be less than or \
                equal to {self.MAX_ACTIVE_SESSIONS_LIMIT}"
            )

    def current_status(self, now: datetime = None) -> ApiKeyStatus:
        if now is None:
            now = datetime.now(timezone.utc)

        if self.revoked_at is not None and self.status == ApiKeyStatus.REVOKED:
            return ApiKeyStatus.REVOKED

        if now >= self.expires_at:
            self.status = ApiKeyStatus.EXPIRED
            return ApiKeyStatus.EXPIRED

        return ApiKeyStatus.ACTIVE
        

class ApiKeyFormat:
    @staticmethod
    def parse(api_key: str) -> tuple[str, str]:
        if not api_key.startswith("asc_"): 
            raise InvalidApiKeyFormat("api key format should start with asc_")

        parts = api_key.split("_", 2)
        if len(parts) != 3 or parts[0] != "asc":
            raise InvalidApiKeyFormat("invalid api key format")

        _, kid, secret = parts

        if not kid or not secret:
            raise InvalidApiKeyFormat("invalid api key format")

        return kid, secret

        
