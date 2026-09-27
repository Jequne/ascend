import httpx
import pytest

from app.token_images.adapters.axiom_http import (
    AXIOM_IMAGE_BASE_URL,
    MAX_IMAGE_BYTES,
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

    provider = AxiomTokenImageProvider(httpx.MockTransport(unexpected_request))

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


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [403, 404])
async def test_missing_upstream_image(status_code: int) -> None:
    provider = AxiomTokenImageProvider(
        httpx.MockTransport(lambda _: httpx.Response(status_code))
    )
    assert await provider.fetch(TOKEN_ADDRESS) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code",
    [500, 302, 200],
    ids=["server-error", "redirect", "oversized"],
)
async def test_upstream_failure_redirect_and_size_limit(
    status_code: int,
) -> None:
    body = b"x" * (MAX_IMAGE_BYTES + 1) if status_code == 200 else b""
    provider = AxiomTokenImageProvider(
        httpx.MockTransport(
            lambda _: httpx.Response(
                status_code,
                headers={
                    "content-type": "image/webp",
                    "location": "https://untrusted.invalid/image",
                },
                content=body,
            )
        )
    )
    with pytest.raises(TokenImageUpstreamError):
        await provider.fetch(TOKEN_ADDRESS)
