from typing import Protocol

from .domain import TokenImage


class TokenImageProvider(Protocol):
    async def fetch(self, token_address: str) -> TokenImage | None: ...


class TokenImageUpstreamError(RuntimeError):
    pass
