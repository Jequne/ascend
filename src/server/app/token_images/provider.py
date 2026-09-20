from __future__ import annotations

from typing import Protocol

import httpx

from .domain import TokenImage, validate_solana_address


AXIOM_IMAGE_BASE_URL = (
    "https://axiomtrading.sfo3.cdn.digitaloceanspaces.com"
)
MAX_IMAGE_BYTES = 2 * 1024 * 1024


class TokenImageProvider(Protocol):
    async def fetch(self, token_address: str) -> TokenImage | None: ...


class TokenImageUpstreamError(RuntimeError):
    pass


class AxiomTokenImageProvider:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self._transport = transport

    async def fetch(self, token_address: str) -> TokenImage | None:
        address = validate_solana_address(token_address)
        url = f"{AXIOM_IMAGE_BASE_URL}/{address}.webp"

        try:
            async with httpx.AsyncClient(
                follow_redirects=False,
                timeout=10,
                transport=self._transport,
            ) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code in {403, 404}:
                        return None
                    response.raise_for_status()

                    media_type = response.headers.get(
                        "content-type",
                        "",
                    ).partition(";")[0].strip().lower()
                    if not media_type.startswith("image/"):
                        raise TokenImageUpstreamError(
                            "Axiom returned a non-image response"
                        )

                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_IMAGE_BYTES:
                            raise TokenImageUpstreamError(
                                "Axiom image exceeds the size limit"
                            )

        except TokenImageUpstreamError:
            raise
        except httpx.HTTPError as exc:
            raise TokenImageUpstreamError(
                "Axiom image request failed"
            ) from exc

        return TokenImage(bytes(content), media_type)
