import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import api_keys, streaming
from app.api_keys.adapters.sqlalchemy_repository import SqlAlchemyApiKeyRepository
from app.api_keys.api_key_hasher import ApiKeyHasher
from app.api_keys.router import router as keys_router
from app.database import Base, get_async_db, register_models

from ..adapters.api_keys_access import ApiKeysAccess
from ..domain import AccessResult, extract_raw_api_key
from ..router import router as ws_router


def test_http_key_connects_ws_limit_and_disconnect(tmp_path) -> None:
    register_models()
    database_path = tmp_path / "keys.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    engine.dispose()
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    sessions = async_sessionmaker(async_engine, expire_on_commit=False)
    from app.config import settings

    hasher = ApiKeyHasher(settings.api_key_pepper)
    access = ApiKeysAccess(
        sessions,
        lambda session: api_keys.ApiKeyManager(
            SqlAlchemyApiKeyRepository(session), hasher
        ),
    )
    manager = streaming.ConnectionManager()
    app = FastAPI()
    app.state.runtime = SimpleNamespace(
        manager=manager, auth=streaming.AuthStreamingProcessor(access, manager)
    )
    app.include_router(keys_router)
    app.include_router(ws_router)

    async def database():
        async with sessions() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_async_db] = database
    with TestClient(app) as client:
        response = client.post(
            "/api-keys/create-api-key",
            headers={"X-Admin-Secret": settings.admin_secret},
            json={"expires_in_days": 1, "max_active_sessions": 1},
        )
        assert response.status_code == 201
        key = response.json()["api_key"]
        validated = client.post(
            "/api-keys/validate-api-key", headers={"X-Api-Key": key}
        )
        assert set(validated.json()) == {"status", "expires_at"}
        with client.websocket_connect(f"/ws?api_key={key}"):
            with client.websocket_connect(f"/ws?api_key={key}") as refused:
                assert refused.receive_json() == {
                    "type": "error",
                    "payload": {"reason": "too_many_sessions"},
                }
                assert refused.receive()["code"] == 1008
        with client.websocket_connect(f"/ws?api_key={key}") as accepted:
            accepted.send_text("still connected")
        for suffix, reason in [
            ("", "the api key was not transferred"),
            ("?api_key=invalid", "api key is not valid"),
        ]:
            with client.websocket_connect(f"/ws{suffix}") as refused:
                assert refused.receive_json()["payload"]["reason"] == reason
                assert refused.receive()["code"] == 1008
    asyncio.run(async_engine.dispose())


def test_credentials_preserve_priority_and_whitespace_short_circuit() -> None:
    assert (
        extract_raw_api_key(
            body_key=" query ", x_api_key="header", authorization="Bearer bearer"
        )
        == "query"
    )
    assert extract_raw_api_key(body_key=" ", x_api_key="header") is None
    assert (
        extract_raw_api_key(x_api_key="header", authorization="Bearer bearer")
        == "header"
    )
    assert extract_raw_api_key(authorization="bEaReR bearer") == "bearer"


class RecordingConnection:
    def __init__(self):
        self.messages: list[dict[str, object]] = []
        self.code: int | None = None
        self.received = asyncio.Event()

    async def send_json(self, message: dict[str, object]) -> None:
        self.messages.append(message)
        self.received.set()

    async def close(self, code: int = 1008) -> None:
        self.code = code


class RevokedAccess:
    async def validate(self, raw_key: str) -> AccessResult:
        return AccessResult("revoked")


@pytest.mark.asyncio
async def test_watchdog_uses_injected_access_result() -> None:
    connection = RecordingConnection()
    stop = asyncio.Event()
    auth = streaming.AuthStreamingProcessor(
        RevokedAccess(), streaming.ConnectionManager()
    )
    await auth.ws_key_watchdog(
        connection=connection, raw_key="key", stop=stop, interval_seconds=0
    )
    assert connection.messages == [{"type": "error", "payload": {"reason": "revoked"}}]
    assert connection.code == 1008 and stop.is_set()


@pytest.mark.asyncio
async def test_known_watchdog_database_outage_failure_is_preserved() -> None:
    class UnavailableAccess:
        async def validate(self, raw_key: str) -> AccessResult | None:
            return None

    connection = RecordingConnection()
    auth = streaming.AuthStreamingProcessor(
        UnavailableAccess(), streaming.ConnectionManager()
    )
    with pytest.raises(AttributeError, match="status"):
        await auth.ws_key_watchdog(
            connection=connection,
            raw_key="key",
            stop=asyncio.Event(),
            interval_seconds=0,
        )
    assert connection.code is None
