from __future__ import annotations

from dataclasses import dataclass
import re


SOLANA_ADDRESS_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


@dataclass(frozen=True)
class TokenImage:
    content: bytes
    media_type: str


def validate_solana_address(token_address: str) -> str:
    normalized = token_address.strip()
    if not SOLANA_ADDRESS_PATTERN.fullmatch(normalized):
        raise ValueError("invalid Solana token address")
    return normalized
