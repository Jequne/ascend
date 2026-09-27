from datetime import datetime, timedelta, timezone

import pytest

from ...api_key_hasher import ApiKeyHasher
from ...api_key_manager import ApiKeyManager
from ...domain import ApiKey, ApiKeyStatus
from ...exceptions import ApiKeyRevocationError


@pytest.mark.parametrize("limit", [0, 5])
def test_rejects_session_boundary(limit: int) -> None:
    with pytest.raises(ValueError):
        ApiKey("kid", datetime.now(timezone.utc), "hash", max_active_sessions=limit)


@pytest.mark.parametrize("limit", [1, 4])
def test_accepts_session_boundary(limit: int) -> None:
    assert (
        ApiKey(
            "kid", datetime.now(timezone.utc), "hash", max_active_sessions=limit
        ).max_active_sessions
        == limit
    )


def test_expiry_at_exact_boundary_and_existing_revocation_semantics() -> None:
    now = datetime.now(timezone.utc)
    key = ApiKey("kid", now, "hash")
    assert key.current_status(now) == ApiKeyStatus.EXPIRED
    key = ApiKey("kid", now, "hash", status=ApiKeyStatus.REVOKED, revoked_at=now)
    assert key.current_status(now) == ApiKeyStatus.REVOKED
    key.revoked_at = None
    assert key.current_status(now) == ApiKeyStatus.EXPIRED


class MemoryRepository:
    def __init__(self, key: ApiKey):
        self.key = key
        self.updated = False

    async def save_new_api_key(self, api_key: ApiKey) -> None:
        self.key = api_key

    async def get_api_key_by_kid(self, kid: str) -> ApiKey | None:
        return self.key if self.key.kid == kid else None

    async def update_api_key(self, api_key: ApiKey) -> ApiKey:
        self.updated = True
        return api_key


@pytest.mark.asyncio
async def test_internal_access_result_and_revoked_record_update() -> None:
    hasher = ApiKeyHasher("pepper")
    repository = MemoryRepository(
        ApiKey(
            "kid",
            datetime.now(timezone.utc) + timedelta(days=1),
            hasher.hash("asc_kid_secret"),
            max_active_sessions=4,
        )
    )
    manager = ApiKeyManager(repository, hasher)
    result = await manager.validate("asc_kid_secret")
    assert (result.kid, result.max_active_sessions) == ("kid", 4)
    assert repository.updated
    repository.key.status = ApiKeyStatus.REVOKED
    repository.updated = False
    with pytest.raises(ApiKeyRevocationError):
        await manager.validate("asc_kid_secret")
    assert repository.updated
