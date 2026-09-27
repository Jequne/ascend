"""Selection rules for the history associated with a funding wallet."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence


@dataclass(frozen=True)
class HistoricalTokenCandidate:
    index: int
    pair_address: str
    token_address: str
    created_at: datetime


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def select_previous_token_indexes(
    candidates: Sequence[HistoricalTokenCandidate],
    *,
    current_pair_address: str,
    current_token_address: str,
    current_created_at: datetime,
    limit: int = 3,
) -> list[int]:
    """Return newest distinct tokens strictly older than the current token."""
    seen_pairs = {current_pair_address}
    seen_tokens = {current_token_address}
    cutoff = _utc(current_created_at)
    selected: list[int] = []

    for candidate in sorted(
        candidates,
        key=lambda item: _utc(item.created_at),
        reverse=True,
    ):
        if len(selected) >= limit:
            break
        if (
            not candidate.pair_address
            or not candidate.token_address
            or _utc(candidate.created_at) >= cutoff
            or candidate.pair_address in seen_pairs
            or candidate.token_address in seen_tokens
        ):
            continue
        seen_pairs.add(candidate.pair_address)
        seen_tokens.add(candidate.token_address)
        selected.append(candidate.index)

    return selected
