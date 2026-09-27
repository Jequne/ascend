from typing import Protocol

from .domain import ApiKey


class ApiKeyRepository(Protocol):
    async def save_new_api_key(self, api_key: ApiKey) -> None: ...

    async def get_api_key_by_kid(self, kid: str) -> ApiKey | None: ...

    async def update_api_key(self, api_key: ApiKey) -> ApiKey: ...


class KeyHasher(Protocol):
    def hash(self, api_key: str) -> str: ...
