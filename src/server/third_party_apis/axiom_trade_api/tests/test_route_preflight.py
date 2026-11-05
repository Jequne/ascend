from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ..auth.exceptions import AxiomRefreshTokenError
from ..client import AxiomTradeClient
from ..endpoints.exceptions import AxiomHTTPStatusError
from ..models.auth import AxiomAgentData


def _agent(name: str) -> AxiomAgentData:
    return AxiomAgentData.create_with_flat_params(
        user_agent="",
        auth_refresh_token=f"refresh-{name}",
        proxy=f"http://proxy-{name}:8080",
        agent_name=name,
    )


@pytest.mark.asyncio
async def test_public_route_probe_uses_chrome136() -> None:
    with patch(
        "third_party_apis.axiom_trade_api.client.AsyncSession"
    ) as session_factory:
        session = session_factory.return_value.__aenter__.return_value
        session.get = AsyncMock(return_value=SimpleNamespace(status_code=200))

        status = await AxiomTradeClient._probe_public_route(_agent("one"))

    assert status == 200
    assert session.get.call_args.kwargs["impersonate"] == "chrome136"


@pytest.mark.asyncio
async def test_public_404_route_is_excluded_from_http_and_websocket() -> None:
    client = AxiomTradeClient([_agent("working"), _agent("bad")])

    async def probe(agent: AxiomAgentData) -> int:
        return 200 if agent.agent_name == "working" else 404

    try:
        with patch.object(client, "_probe_public_route", side_effect=probe):
            assert await client.exclude_unavailable_routes() == {
                "working": 200,
                "bad": 404,
            }
        selected = client._agent_selector.acquire_agent()
        assert selected is not None
        assert selected[1].agent_name == "working"
        assert (
            client._agent_selector.random_websocket_agent()[1].agent_name
            == "working"
        )
        client._agent_selector.release_agent(selected)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_no_successful_public_probe_keeps_routes_available() -> None:
    client = AxiomTradeClient([_agent("first"), _agent("second")])

    async def probe(agent: AxiomAgentData) -> int:
        return 404

    try:
        with patch.object(client, "_probe_public_route", side_effect=probe):
            assert await client.exclude_unavailable_routes() == {
                "first": 404,
                "second": 404,
            }
        assert not client._agent_selector._disabled_routes
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["pair", "refresh"])
async def test_runtime_404_excludes_bad_route_and_retries(
    failure: str,
) -> None:
    client = AxiomTradeClient([_agent("bad"), _agent("working")])
    called: list[str] = []

    async def probe(agent: AxiomAgentData) -> int:
        return 404 if agent.agent_name == "bad" else 200

    async def endpoint(session_and_agent):
        name = session_and_agent[1].agent_name
        called.append(name)
        if name == "bad":
            if failure == "refresh":
                raise AxiomRefreshTokenError("refresh 404", status_code=404)
            raise AxiomHTTPStatusError("pair 404", status_code=404)
        return "ok"

    try:
        with patch.object(client, "_probe_public_route", side_effect=probe):
            assert await client._call_with_random_agent(endpoint) == "ok"
        assert called == ["bad", "working"]
        assert (
            client._agent_selector.random_websocket_agent()[1].agent_name
            == "working"
        )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_genuine_pair_404_does_not_exclude_healthy_route() -> None:
    client = AxiomTradeClient([_agent("working"), _agent("other")])

    async def endpoint(session_and_agent):
        raise AxiomHTTPStatusError("pair 404", status_code=404)

    try:
        with patch.object(client, "_probe_public_route", return_value=200):
            with pytest.raises(AxiomHTTPStatusError, match="pair 404"):
                await client._call_with_random_agent(endpoint)
        assert not client._agent_selector._disabled_routes
    finally:
        await client.close()
