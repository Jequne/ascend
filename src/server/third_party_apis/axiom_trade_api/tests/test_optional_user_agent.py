import pytest

from ..models.auth import AxiomAgentData


@pytest.mark.parametrize("user_agent", [None, "", "   ", "custom-agent/1"])
def test_agent_headers_only_include_nonempty_user_agent(
    user_agent: str | None,
) -> None:
    source_headers = {"Accept": "application/json"}
    if user_agent is not None:
        source_headers["User-Agent"] = user_agent

    agent = AxiomAgentData.model_validate(
        {
            "headers": source_headers,
            "cookies": {"auth-refresh-token": {"cookie": "test-token"}},
        }
    )

    expected = user_agent if user_agent and user_agent.strip() else None
    assert agent.headers.request_headers.get("User-Agent") == expected
    assert agent.headers.headers_for_wss.get("User-Agent") == expected
    assert (
        agent.get_http_request_context()["headers"].get("User-Agent")
        == expected
    )
    assert agent.headers.request_headers["Accept"] == "application/json"
