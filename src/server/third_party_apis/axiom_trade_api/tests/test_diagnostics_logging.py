import logging

import pytest

from .. import AxiomTradeClient
from ..request_pacer import AxiomRequestPacer
from .test_rate_limit_routing import _agent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "level, visible", [(logging.INFO, False), (logging.DEBUG, True)]
)
async def test_http_diagnostics_are_only_visible_at_debug(
    level: int, visible: bool, caplog: pytest.LogCaptureFixture
) -> None:
    client = AxiomTradeClient([_agent(1, "socks5://test-proxy")])
    client._request_pacer = AxiomRequestPacer(interval_seconds=0)
    client._http_attempts["endpoint"] = 24

    async def endpoint(session_and_agent, **kwargs) -> str:
        return "ok"

    try:
        with caplog.at_level(level, logger="third_party_apis.axiom_trade_api.client"):
            assert await client._call_with_random_agent(endpoint) == "ok"
        diagnostics = [
            record
            for record in caplog.records
            if "Axiom HTTP diagnostics:" in record.getMessage()
        ]
        assert bool(diagnostics) is visible
        if visible:
            assert diagnostics[0].levelno == logging.DEBUG
            assert "'endpoint': 25" in diagnostics[0].getMessage()
    finally:
        await client.close()
