import asyncio
import time
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from .. import AuthManager, AxiomAgentData, AxiomTradeClient


@pytest.mark.asyncio
async def test_parallel_validation_refreshes_once_and_updates_tokens() -> None:
    agent = AxiomAgentData.create_with_flat_params("test-agent", "refresh")
    client = AxiomTradeClient([agent])
    auth = AuthManager()
    token = jwt.encode(
        {"exp": int(time.time()) + 3600},
        "test-only-key-with-at-least-32-bytes",
        algorithm="HS256",
    )
    started, release = asyncio.Event(), asyncio.Event()

    async def refresh(session_and_agent) -> str:
        started.set()
        await release.wait()
        return token

    try:
        with patch.object(
            auth._refresh_client,
            "refresh_access_token",
            AsyncMock(side_effect=refresh),
        ) as refreshed:
            session_and_agent = (
                client._agent_selector.get_agents_and_sessions()[0]
            )
            first = asyncio.create_task(
                auth.ensure_validation(session_and_agent)
            )
            await started.wait()
            second = asyncio.create_task(
                auth.ensure_validation(session_and_agent)
            )
            release.set()
            assert await asyncio.gather(first, second) == [True, True]
            refreshed.assert_awaited_once()
            assert agent.cookies.auth_access_token is not None
            assert agent.cookies.auth_access_token.cookie == token
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_unexpected_reader_failure_still_closes_owned_sessions() -> None:
    client = AxiomTradeClient(
        [AxiomAgentData.create_with_flat_params("test-agent", "refresh")]
    )
    session = client._agent_selector.get_agents_and_sessions()[0][0]

    async def failed_reader() -> None:
        raise RuntimeError("reader failure")

    client._ws_task = asyncio.create_task(failed_reader())
    await asyncio.sleep(0)
    with patch.object(
        session, "close", AsyncMock(wraps=session.close)
    ) as closed:
        with pytest.raises(RuntimeError, match="reader failure"):
            await client.close()
        closed.assert_awaited_once()
    assert client._ws_task is None
