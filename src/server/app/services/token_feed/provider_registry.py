from __future__ import annotations

from app.schemas.token_feed import TokenFeedBuildRequest, TokenFeedSol

from .contracts import TokenFeedProvider


class TokenFeedProviderRegistry:
    def __init__(self, providers: list[TokenFeedProvider] | None = None):
        self._providers: dict[str, TokenFeedProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: TokenFeedProvider) -> None:
        provider_name = provider.provider_name.strip().lower()
        if not provider_name:
            raise ValueError("provider_name must not be empty")
        if provider_name in self._providers:
            raise ValueError(f"token feed provider already registered for '{provider_name}'")
        self._providers[provider_name] = provider

    def get(self, provider_name: str) -> TokenFeedProvider:
        normalized_provider = provider_name.strip().lower()
        if not normalized_provider:
            raise ValueError("provider_name must not be empty")

        try:
            return self._providers[normalized_provider]
        except KeyError as exc:
            raise KeyError(f"no token feed provider registered for '{normalized_provider}'") from exc

    async def build_sol_token_feed(
        self,
        request: TokenFeedBuildRequest,
    ) -> TokenFeedSol | None:
        provider_name = request.provider_name
        provider = self.get(provider_name)
        return await provider.build_sol_token_feed(request)


class TokenFeedService(TokenFeedProviderRegistry):
    """Backward-compatible alias for registry usage from app services."""