import httpx
import pytest

from app.token_images.provider import (
    AXIOM_IMAGE_BASE_URL,
    AxiomTokenImageProvider,
    TokenImageUpstreamError,
)


TOKEN_ADDRESS = "9LoWfvBgTzwqAMzNeMRwVY8YFBY8hEZjyvo3Mvb8pump"


@pytest.mark.asyncio
async def test_fetches_only_the_expected_axiom_image() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == (
            f"{AXIOM_IMAGE_BASE_URL}/{TOKEN_ADDRESS}.webp"
        )
        return httpx.Response(
            200,
            headers={"content-type": "image/webp"},
            content=b"webp-image",
        )

    provider = AxiomTokenImageProvider(httpx.MockTransport(handler))

    image = await provider.fetch(TOKEN_ADDRESS)

    assert image is not None
    assert image.content == b"webp-image"
    assert image.media_type == "image/webp"


@pytest.mark.asyncio
async def test_rejects_an_invalid_address_before_request() -> None:
    async def unexpected_request(_: httpx.Request) -> httpx.Response:
        pytest.fail("invalid addresses must not reach the network")

    provider = AxiomTokenImageProvider(
        httpx.MockTransport(unexpected_request)
    )

    with pytest.raises(ValueError, match="invalid Solana token address"):
        await provider.fetch("../../metadata")


@pytest.mark.asyncio
async def test_rejects_non_image_responses() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"not an image",
        )
    )
    provider = AxiomTokenImageProvider(transport)

    with pytest.raises(
        TokenImageUpstreamError,
        match="non-image",
    ):
        await provider.fetch(TOKEN_ADDRESS)
