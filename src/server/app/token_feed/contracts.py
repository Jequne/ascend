from collections.abc import Callable
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
    def remove_callback(self, callback: Callable[[PairEvent], None]) -> None: ...


class FeedPreparer(Protocol):
    async def prepare_token_feed(self, event: PairEvent) -> TokenFeedBase: ...
    async def prepare_developer_update(
        self, event: PairEvent, base: TokenFeedBase
    ) -> TokenFeedBase | None: ...
    async def prepare_funding_update(
        self, event: PairEvent, base: TokenFeedBase
    ) -> TokenFeedBase | None: ...
    async def stop(self) -> None: ...
