import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from collections.abc import AsyncGenerator

from ....database import Base, get_async_db
from ...router import router as api_keys_router



@pytest_asyncio.fixture
async def get_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(get_engine) -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(get_engine, expire_on_commit=False)

    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client(
    session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    app = FastAPI()
    app.include_router(api_keys_router)

    async def override_get_async_db():
        yield session

    app.dependency_overrides[get_async_db] = override_get_async_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()