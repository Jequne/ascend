from typing import Protocol

from .domain import AccessResult


class Connection(Protocol):
    async def send_json(self, message: dict[str, object]) -> None: ...
    async def close(self, code: int = 1008) -> None: ...


class AccessChecker(Protocol):
    async def validate(self, raw_key: str) -> AccessResult | None: ...
