import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....config import settings
from ...adapters.models import ApiKeyModel

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_api_key_success(
    client: AsyncClient, session: AsyncSession
) -> None:
    response = await client.post(
        "/api-keys/create-api-key",
        headers={
            "X-Admin-Secret": settings.admin_secret,
        },
        json={
            "expires_in_days": 7,
            "max_active_sessions": 3,
            "label": "Test key",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["api_key"] is not None
    assert body["kid"] is not None
    assert body["max_active_sessions"] == 3
    assert body["label"] == "Test key"

    result = await session.execute(
        select(ApiKeyModel).filter_by(kid=body["kid"])
    )
    saved_api_key = result.scalar_one()

    assert saved_api_key.kid == body["kid"]
    assert saved_api_key.label == "Test key"
    assert saved_api_key.max_active_sessions == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, excepted_status_code",
    [
        pytest.param(
            {"X-Admin-Secret": "incorrect-admin-secret"},
            401,
            id="incorrect-admin-secret",
        ),
        pytest.param(
            {"X-Admin-Secret": ""}, 401, id="empty-string-admin-secret"
        ),
        pytest.param({}, 401, id="empty-x-admin-secret-header"),
        pytest.param(None, 401, id="headers-is-none"),
    ],
)
async def test_create_test_when_no_x_admin_secret(
    client: AsyncClient, session: AsyncSession, headers, excepted_status_code
) -> None:
    response = await client.post(
        "/api-keys/create-api-key",
        headers=headers,
        json={
            "expires_in_days": 7,
            "max_active_sessions": 3,
            "label": "Test key",
        },
    )

    assert response.status_code == excepted_status_code


@pytest.mark.asyncio
async def test_request_label_and_session_boundaries_preserve_current_contract(
    client: AsyncClient,
) -> None:
    headers = {"X-Admin-Secret": settings.admin_secret}
    omitted = await client.post(
        "/api-keys/create-api-key",
        headers=headers,
        json={"max_active_sessions": 4},
    )
    assert omitted.status_code == 201 and omitted.json()["label"] is None
    explicit_null = await client.post(
        "/api-keys/create-api-key", headers=headers, json={"label": None}
    )
    assert explicit_null.status_code == 422
    assert explicit_null.json()["detail"][0]["type"] == "string_type"
    zero = await client.post(
        "/api-keys/create-api-key",
        headers=headers,
        json={"max_active_sessions": 0},
    )
    assert zero.status_code == 422
    # Existing DTO/domain disagreement; deliberately retained, not fixed here.
    with pytest.raises(ValueError):
        await client.post(
            "/api-keys/create-api-key",
            headers=headers,
            json={"max_active_sessions": 5},
        )
