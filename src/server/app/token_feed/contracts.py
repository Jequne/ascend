from collections.abc import AsyncIterator, Callable
from typing import Protocol

from .domain import History, PairDetails, PairEvent, TokenFeedBase, TokenFees


class HistoryProvider(Protocol):
    async def dev_tokens_v3(
        self, dev_address: str, *, background: bool = False
    ) -> History | None: ...
    async def pair_info(
        self, pair_address: str, *, background: bool = False
    ) -> PairDetails | None: ...
    async def token_info(
        self, pair_address: str, *, background: bool = False
    ) -> TokenFees | None: ...


class PairSource(Protocol):
    def set_callback(self, callback: Callable[[PairEvent], None]) -> None: ...
    def remove_callback(
        self, callback: Callable[[PairEvent], None]
    ) -> None: ...


class FeedPreparer(Protocol):
    async def prepare_token_feed(self, event: PairEvent) -> TokenFeedBase: ...
    def developer_updates(
        self, event: PairEvent, base: TokenFeedBase
    ) -> AsyncIterator[TokenFeedBase]: ...
    def funding_updates(
        self, event: PairEvent, base: TokenFeedBase
    ) -> AsyncIterator[TokenFeedBase]: ...
    async def stop(self) -> None: ...
