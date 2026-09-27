import asyncio

import pytest

from ..delivery import ping_broadcaster, token_feed_broadcaster
from ..sessions import ConnectionManager
from .test_access import RecordingConnection


@pytest.mark.asyncio
async def test_feed_and_heartbeat_envelopes() -> None:
    manager = ConnectionManager()
    connection = RecordingConnection()
    await manager.connect(connection, kid="kid")
    stop = asyncio.Event()

    async def payload() -> dict[str, object]:
        stop.set()
        return {"pair_address": "pair", "funding_deployed_tokens": None}

    await token_feed_broadcaster(manager, payload, stop_event=stop)
    assert connection.messages == [
        {
            "type": "token_feed",
            "payload": {
                "pair_address": "pair",
                "funding_deployed_tokens": None,
            },
        }
    ]
    stop.clear()
    ping = asyncio.create_task(
        ping_broadcaster(manager, stop_event=stop, interval=0.001)
    )
    try:
        async with asyncio.timeout(1):
            while len(connection.messages) < 2:
                connection.received.clear()
                await connection.received.wait()
    finally:
        stop.set()
        await ping
    assert connection.messages[1]["type"] == "ping"
    assert "timestamp" in str(connection.messages[1]["payload"])


@pytest.mark.asyncio
async def test_send_failure_keeps_session_and_delivers_to_others() -> None:
    class FailedConnection(RecordingConnection):
        async def send_json(self, message: dict[str, object]) -> None:
            raise OSError("disconnected")

    manager = ConnectionManager()
    good, failed = RecordingConnection(), FailedConnection()
    await manager.connect(failed, kid="failed")
    await manager.connect(good, kid="good")
    await manager.broadcast_json({"type": "sol_price", "payload": 150.25})
    assert good.messages == [{"type": "sol_price", "payload": 150.25}]
    assert await manager.active_sessions_for_kid("failed") == 1
