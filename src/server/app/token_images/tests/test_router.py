from collections.abc import AsyncGenerator

from fastapi import FastAPI
import httpx
import pytest
import pytest_asyncio

from app.token_images.domain import TokenImage
from app.token_images.router import get_token_image_provider, router


TOKEN_ADDRESS = "9LoWfvBgTzwqAMzNeMRwVY8YFBY8hEZjyvo3Mvb8pump"


class StubProvider:
    async def fetch(self, token_address: str) -> TokenImage | None:
        assert token_address == TOKEN_ADDRESS
        return TokenImage(b"webp-image", "image/webp")


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_token_image_provider] = StubProvider
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_returns_cacheable_image(client: httpx.AsyncClient) -> None:
    response = await client.get(f"/api/v1/token-images/{TOKEN_ADDRESS}")

    assert response.status_code == 200
    assert response.content == b"webp-image"
    assert response.headers["content-type"] == "image/webp"
    assert response.headers["cache-control"] == "public, max-age=3600"
