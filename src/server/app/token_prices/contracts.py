from collections.abc import Awaitable, Callable
from typing import Protocol

from .domain import SolPrice

PriceCallback = Callable[[SolPrice], Awaitable[None]]


class PriceSource(Protocol):
    def subscribe(self, callback: PriceCallback) -> None: ...
    def unsubscribe(self, callback: PriceCallback) -> None: ...
