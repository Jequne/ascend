import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from ...models import ApiKeyModel
from ...api_key_hasher import ApiKeyHasher
from ...domain import ApiKeyStatus
from ...schemas import ValidApiKeyResponse


pytestmark = pytest.mark.integration


async def api_key_created_model(
        session: AsyncSession, 
        expires_at: datetime | None,
        kid: str = "kid",
        key_hash: str = "key_hash",
        status: str = "active",
        max_active_sessions: int = 3,
        label: str = "label",
        revoked_at: datetime | None = None
    ):
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    api_key_model = ApiKeyModel(
        kid=kid,
        key_hash=key_hash,
        status=status,
        expires_at=expires_at,
        max_active_sessions=max_active_sessions,
        label=label,
        revoked_at=revoked_at
    )

    session.add(api_key_model)
    await session.flush()


def create_correct_api_key() -> str:
    return "asc_dbce908380eb_fznq0xKECiV0ZlA0IVdMrnRrUpV5SlNe"


@pytest.mark.asyncio
async def test_validate_api_key_if_api_key_is_valid(
    session: AsyncSession,
    client: AsyncClient
) -> None:
    api_key = create_correct_api_key()

    expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    api_key_model_created = await api_key_created_model(
        session, 
        key_hash=ApiKeyHasher.hash(api_key),
        kid=api_key.split("_")[1],
        expires_at=expires_at
    )

    response = await client.post(
        "/api-keys/validate-api-key",
        headers = {"X-Api-Key": api_key}
    )

    assert response.status_code == 200

    result = response.json()

    print(result)

    validate_api_key_response = ValidApiKeyResponse(**result)

    print(validate_api_key_response)

    assert validate_api_key_response.status == ApiKeyStatus.ACTIVE
    assert \
        validate_api_key_response.expires_at.replace(
            tzinfo=timezone.utc
        ) == expires_at 


@pytest.mark.asyncio
async def test_validate_api_key_if_input_api_key_is_incorrect_returns_401_status(
    client: AsyncClient,
) -> None:
    response_1 = await client.post(
            "/api-keys/validate-api-key",
            headers = {"X-Api-Key": ""}
        )
    assert response_1.status_code == 401

    response_2 = await client.post(
            "/api-keys/validate-api-key",
            headers = {"X-Api-Key": "incorrect-format-api-key"}
        )
    assert response_2.status_code == 401

    response_3 = await client.post(
            "/api-keys/validate-api-key",
        )
    assert response_3.status_code == 401


@pytest.mark.asyncio
async def test_validate_api_key_if_expired(
    session: AsyncSession,
    client: AsyncClient,
) -> None:
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)

    api_key = create_correct_api_key()
    
    await api_key_created_model(
        session=session,
        expires_at=expires_at,
        kid=api_key.split("_")[1],
        status=ApiKeyStatus.ACTIVE,
        key_hash=ApiKeyHasher.hash(api_key)
    )

    response = await client.post(
        "/api-keys/validate-api-key",
        headers = {"X-Api-Key": api_key}
    )

    assert response.status_code == 401

    result = response.json()

    with pytest.raises(ValidationError):
        validate_api_key_response = ValidApiKeyResponse(**result)


@pytest.mark.asyncio
async def test_validate_api_key_if_revoked(
    session: AsyncSession,
    client: AsyncClient
) -> None:
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    revoked_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        
    api_key = create_correct_api_key()

    await api_key_created_model(
        session=session,
        expires_at=expires_at,
        kid=api_key.split("_")[1],
        key_hash=ApiKeyHasher.hash(api_key),
        status=ApiKeyStatus.REVOKED,
        revoked_at=revoked_at
    )

    response = await client.post(
        "/api-keys/validate-api-key",
        headers = {"X-Api-Key": api_key}
    )

    assert response.status_code == 401
