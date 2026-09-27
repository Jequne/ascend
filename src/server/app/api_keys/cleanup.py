import asyncio
from collections.abc import Awaitable, Callable


async def clean_expired_access_keys(
    stop_event: asyncio.Event,
    remove_expired: Callable[[], Awaitable[bool | None]],
) -> None:
    while not stop_event.is_set():
        await remove_expired()
        await asyncio.sleep(7200)
