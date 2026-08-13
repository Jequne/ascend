from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from ..database import AsyncSessionLocal
from ..repositories.api_keys import remove_expired_access_keys


async def clean_expired_access_keys(stop_event: asyncio.Event):
    while not stop_event.is_set():
        async with AsyncSessionLocal() as session:
            await remove_expired_access_keys(session)

        await asyncio.sleep(7200)

        


