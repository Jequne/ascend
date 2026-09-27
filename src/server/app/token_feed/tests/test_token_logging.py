import asyncio
import logging
from dataclasses import replace

import pytest

from ..base import prepare_base
from ..collector import TokenFeedCollector
from ..enrichment import FeedEnrichment
from ..token_logging import format_token_log
from .test_collector import PairSource
from .test_funding_history import FakeClient, _message


@pytest.mark.parametrize("total, expected", [(0, "⁉️ no history"), (4, "50.0%")])
def test_token_log_includes_identity_holds_and_migration_share(
    total: int, expected: str
) -> None:
    base = replace(
        prepare_base(_message()), migrated_tokens_count=2, all_tokens_count=total
    )
    text = format_token_log(base)
    assert "🔍 current-token ; NEW (Current) ; dev holds: 5 %" in text
    assert f"🛠️ dev: developer ({expected} migrated):" in text
    assert "Tokens not found for dev developer" in text


@pytest.mark.asyncio
async def test_collector_logs_base_and_enriched_history_at_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    collector = TokenFeedCollector(PairSource(), FeedEnrichment(FakeClient()))
    try:
        with caplog.at_level(logging.INFO, logger="app.token_feed.collector"):
            await collector.collect_token_feed_data(_message())
            for _ in range(3):
                await asyncio.wait_for(collector.tokens_feed.get(), timeout=1)
        messages = [
            record
            for record in caplog.records
            if record.name == "app.token_feed.collector"
        ]
        assert len(messages) == 3
        assert all(record.levelno == logging.INFO for record in messages)
        assert "🔍 current-token" in messages[0].getMessage()
        assert "💰 funding:" in caplog.text
        assert (
            "|- 🪙 previous-token (previous-token); total fees paid: 2.0" in caplog.text
        )
    finally:
        await collector.stop()
