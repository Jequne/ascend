from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from functools import wraps

from .api_key_generator import ApiKeyGenerator, GeneratedApiKey
from .api_key_hasher import ApiKeyHasher
from .domain import ApiKey, ApiKeyStatus, ApiKeyFormat
from .repository import ApiKeyRepository
from .exceptions import (
    ApiKeyNotFoundError, 
    InvalidApiKeyError, 
    ApiKeyExpirationError,
    ApiKeyRevocationError
)


@dataclass(frozen=True, slots=True)
class CreateApiKeyCommand:
    expires_in_days: int
    max_active_sessions: int
    label: str = None


@dataclass(frozen=True, slots=True)
class CreatedApiKey:
    api_key: str
    kid: str
    expires_at: datetime 
    max_active_sessions: int
    label: str | None = None


@dataclass(frozen=True, slots=True)
class ValidApiKeyResult:
    status: ApiKeyStatus
    expires_at: datetime | None


def _check_api_key_format(func):
    @wraps(func)
    async def wrapper(self, x_api_key: str):
        kid, _ = ApiKeyFormat.parse(api_key=x_api_key)
        return await func(self, x_api_key, kid)

    return wrapper


class ApiKeyManager():
    def __init__(
        self,
        repository: ApiKeyRepository,
        api_key_generator: ApiKeyGenerator = ApiKeyGenerator(),
        api_key_hasher: ApiKeyHasher = ApiKeyHasher(),
    ):
        self._api_key_generator = api_key_generator 
        self._api_key_hasher = api_key_hasher
        self._repository = repository

    async def create(self, command: CreateApiKeyCommand) -> CreatedApiKey:
        generated_api_key: GeneratedApiKey = \
            self._api_key_generator.generate()

        api_key_hash: str = \
            self._api_key_hasher.hash(generated_api_key.api_key)

        expires_at = \
            datetime.now(timezone.utc) + timedelta(days=command.expires_in_days)

        api_key = ApiKey(
            kid=generated_api_key.kid,
            expires_at=expires_at,
            max_active_sessions=command.max_active_sessions,
            status=ApiKeyStatus.ACTIVE,
            key_hash=api_key_hash,
            label=command.label
        )

        await self._repository.save_new_api_key(api_key)

        return CreatedApiKey(
            api_key=generated_api_key.api_key,
            kid=generated_api_key.kid,
            expires_at=expires_at,
            max_active_sessions=command.max_active_sessions,
            label=command.label
        )

    @_check_api_key_format
    async def validate(
        self, 
        api_key_string: str, 
        kid: str
    ) -> ValidApiKeyResult:
        api_key = await self._repository.get_api_key_by_kid(
            kid=kid
        )

        if api_key is None:
            raise ApiKeyNotFoundError(f"Api Key Not Found")

        if self._api_key_hasher.hash(api_key_string) != api_key.key_hash:
            raise InvalidApiKeyError("Invalid Api Key")

        api_key.current_status()
        updated_api_key = await self._repository.update_api_key(api_key=api_key)

        if api_key.status == ApiKeyStatus.EXPIRED:
            raise ApiKeyExpirationError("Api Key Expired")

        if api_key.status == ApiKeyStatus.REVOKED:
            raise ApiKeyRevocationError("Api Key Revoked")

        return ValidApiKeyResult(
            status=updated_api_key.status,
            expires_at=updated_api_key.expires_at
        )

        