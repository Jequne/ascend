import asyncio

import pytest

from ..delivery import ping_broadcaster, token_feed_broadcaster
from ..sessions import MAX_PENDING_MESSAGES, ConnectionManager
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
    await asyncio.wait_for(connection.received.wait(), 1)
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
        def __init__(self) -> None:
            super().__init__()
            self.closed = asyncio.Event()

        async def send_json(self, message: dict[str, object]) -> None:
            raise OSError("disconnected")

        async def close(self, code: int = 1008) -> None:
            await super().close(code)
            self.closed.set()

    manager = ConnectionManager()
    good, failed = RecordingConnection(), FailedConnection()
    await manager.connect(failed, kid="failed")
    await manager.connect(good, kid="good")
    await manager.broadcast_json({"type": "sol_price", "payload": 150.25})
    await asyncio.wait_for(good.received.wait(), 1)
    assert good.messages == [{"type": "sol_price", "payload": 150.25}]
    await asyncio.wait_for(failed.closed.wait(), 1)
    assert await manager.active_sessions_for_kid("failed") == 0


@pytest.mark.asyncio
async def test_slow_client_cannot_delay_feed_updates_or_other_clients() -> (
    None
):
    class SlowConnection(RecordingConnection):
        def __init__(self) -> None:
            super().__init__()
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def send_json(self, message: dict[str, object]) -> None:
            self.started.set()
            await self.release.wait()
            await super().send_json(message)

    manager = ConnectionManager()
    slow, fast = SlowConnection(), RecordingConnection()
    await manager.connect(slow, kid="slow")
    await manager.connect(fast, kid="fast")
    try:
        await manager.broadcast_json({"type": "token_feed", "payload": 1})
        await asyncio.wait_for(slow.started.wait(), 1)
        await asyncio.wait_for(fast.received.wait(), 1)
        fast.received.clear()
        await manager.broadcast_json({"type": "token_feed", "payload": 2})
        await asyncio.wait_for(fast.received.wait(), 1)
        assert [item["payload"] for item in fast.messages] == [1, 2]
        assert slow.messages == []
    finally:
        await manager.disconnect(slow, kid="slow")
        await manager.disconnect(fast, kid="fast")


@pytest.mark.asyncio
async def test_full_send_queue_closes_only_slow_client() -> None:
    class StalledConnection(RecordingConnection):
        def __init__(self) -> None:
            super().__init__()
            self.closed = asyncio.Event()

        async def send_json(self, message: dict[str, object]) -> None:
            await asyncio.Event().wait()

        async def close(self, code: int = 1008) -> None:
            await super().close(code)
            self.closed.set()

    manager = ConnectionManager()
    stalled, fast = StalledConnection(), RecordingConnection()
    await manager.connect(stalled, kid="stalled")
    await manager.connect(fast, kid="fast")
    try:
        for index in range(MAX_PENDING_MESSAGES + 2):
            fast.received.clear()
            await manager.broadcast_json(
                {"type": "token_feed", "payload": index}
            )
            await asyncio.wait_for(fast.received.wait(), 1)
        await asyncio.wait_for(stalled.closed.wait(), 1)
        assert stalled.code == 1013
        assert await manager.active_sessions_for_kid("stalled") == 0
        assert await manager.active_sessions_for_kid("fast") == 1
    finally:
        await manager.disconnect(stalled, kid="stalled")
        await manager.disconnect(fast, kid="fast")
