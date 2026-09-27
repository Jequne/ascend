import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.composition import Runtime
from app.database import Base, register_models
from app.main import create_app
from app.streaming.tests.test_access import RecordingConnection
from third_party_apis import axiom_trade_api as axiom


@pytest_asyncio.fixture
async def sessions(
    tmp_path: Path,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    register_models()
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'runtime.db'}"
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def message() -> axiom.NewPairsRoomMessage:
    return axiom.NewPairsRoomMessage.model_validate(
        {
            "room": "new_pairs",
            "content": {
                "pair_address": "pair",
                "token_address": "token",
                "token_name": "Token",
                "token_ticker": "TOK",
                "protocol": "pump",
                "deployer_address": "developer",
                "created_at": "2026-09-27T00:00:00Z",
                "updated_at": "2026-09-27T00:00:00Z",
                "open_trading": "2026-09-27T00:00:00Z",
            },
        }
    )


@pytest.mark.asyncio
async def test_two_runtimes_delivery_callbacks_and_shutdown(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    clients = [axiom.AxiomTradeClient([]), axiom.AxiomTradeClient([])]
    runtimes = [Runtime(client, sessions, "pepper") for client in clients]
    for client in clients:
        with (
            patch.object(client, "connect_websocket"),
            patch.object(
                client, "dev_tokens_v3", AsyncMock(return_value=None)
            ),
            patch.object(client, "pair_info", AsyncMock(return_value=None)),
        ):
            await runtimes[clients.index(client)].start()
    connection = RecordingConnection()
    await runtimes[0].manager.connect(connection, kid="kid")
    try:
        await clients[0]._wsocket._message_router.dispatch_message(message())
        await clients[0]._wsocket._message_router.dispatch_message(
            axiom.SolPriceRoomMessage(room="sol_price", content=123.5)
        )
        async with asyncio.timeout(1):
            while len(connection.messages) < 2:
                connection.received.clear()
                await connection.received.wait()
        feed = next(
            item
            for item in connection.messages
            if item["type"] == "token_feed"
        )
        assert isinstance(feed["payload"], dict)
        assert feed["payload"]["pair_address"] == "pair"
        assert feed["payload"]["last_deployed_tokens"] is None
        assert {"type": "sol_price", "payload": 123.5} in connection.messages
        assert runtimes[1].feed.tokens_feed.empty()
        assert await runtimes[1].manager.active_sessions_for_kid("kid") == 0
    finally:
        await asyncio.gather(*(runtime.stop() for runtime in runtimes))
    for client, runtime in zip(clients, runtimes):
        assert not client._wsocket._message_router._callbacks
        assert not runtime._tasks and not runtime.feed._tasks


@pytest.mark.asyncio
async def test_partial_startup_releases_resources(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    client = axiom.AxiomTradeClient([])
    runtime = Runtime(client, sessions, "")
    with (
        patch.object(
            client,
            "connect_websocket",
            side_effect=RuntimeError("startup failure"),
        ),
        patch.object(client, "close", wraps=client.close) as close,
    ):
        with pytest.raises(RuntimeError, match="startup failure"):
            await runtime.start()
        close.assert_awaited_once()
    assert not client._wsocket._message_router._callbacks
    assert not runtime._tasks
    await runtime.stop()


@pytest.mark.asyncio
async def test_lifespan_routes_without_credentials_or_live_axiom(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    client = axiom.AxiomTradeClient([])
    runtime = Runtime(client, sessions, "")
    app = create_app(lambda: runtime, lambda: None)
    with patch.object(client, "connect_websocket"):
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url="http://test"
            ) as http:
                assert (await http.get("/health")).json() == {"status": "ok"}
            paths = set(app.openapi()["paths"])
            assert {
                "/health",
                "/api/v1/api-keys/create-api-key",
                "/api/v1/token-images/{token_address}",
            } <= paths
    assert runtime._closed


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_stage", ["database", "runtime"])
async def test_lifespan_cleanup_on_initialization_failure(
    sessions: async_sessionmaker[AsyncSession], failure_stage: str
) -> None:
    client = axiom.AxiomTradeClient([])
    runtime = Runtime(client, sessions, "")

    def initialize_database() -> None:
        if failure_stage == "database":
            raise RuntimeError("initialization failure")

    app = create_app(lambda: runtime, initialize_database)
    with (
        patch.object(
            runtime,
            "start",
            AsyncMock(side_effect=RuntimeError("initialization failure")),
        ) as start,
        patch.object(runtime, "stop", wraps=runtime.stop) as stop,
    ):
        with pytest.raises(RuntimeError, match="initialization failure"):
            async with app.router.lifespan_context(app):
                pytest.fail("Failed startup must not enter the lifespan")
        if failure_stage == "database":
            start.assert_not_awaited()
        else:
            start.assert_awaited_once()
        stop.assert_awaited_once()
    assert runtime._closed
