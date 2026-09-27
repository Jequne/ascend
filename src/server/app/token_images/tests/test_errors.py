import httpx
import pytest
from fastapi import FastAPI

from ..contracts import TokenImageUpstreamError
from ..domain import TokenImage
from ..router import get_token_image_provider, router
from .test_provider import TOKEN_ADDRESS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mode, expected", [("invalid", 422), ("missing", 404), ("upstream", 502)]
)
async def test_router_errors(mode: str, expected: int) -> None:
    class Provider:
        async def fetch(self, address: str) -> TokenImage | None:
            if mode == "upstream":
                raise TokenImageUpstreamError("failed")
            return None

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_token_image_provider] = Provider
    address = "invalid" if mode == "invalid" else TOKEN_ADDRESS
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.get(f"/token-images/{address}")
    assert response.status_code == expected
