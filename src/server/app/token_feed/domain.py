from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


@dataclass(frozen=True, slots=True)
class DeployedToken:
    blockchain: str
    total_pair_fees_paid: float | None
    ath_mcap_in_usd: float | None
    dex_paid: bool
    pair_address: str
    token_address: str
    token_image: str | None
    is_migrated: bool
    website: str | None
    telegram: str | None
    discord: str | None
    twitter: str | None
    token_name: str
    token_ticker: str
    twitter_admin_nickname: str | None
    twitter_admin_id: str | None
    dev_wallet: str
    protocol: str
    created_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class TokenFeedBase:
    blockchain: Literal["sol", "bsc"]
    indicator: Literal["Dev Migrations"] = "Dev Migrations"
    dev_holds_percent: Optional[float]
    snipers_hold_percent: Optional[float]
    pair_address: str
    token_address: str
    token_image: str | None
    is_migrated: bool
    website: str | None
    telegram: str | None
    discord: str | None
    twitter: str | None
    token_name: str
    token_ticker: str
    twitter_admin_nickname: str | None = None
    twitter_admin_id: str | None = None
    dev_wallet: str
    protocol: str
    last_deployed_tokens: list[DeployedToken] | None
    migrated_tokens_count: int
    all_tokens_count: int
    funding_wallet: str | None = None
    funding_deployed_tokens: list[DeployedToken] | None = None
    funding_migrated_tokens_count: int | None = None
    funding_all_tokens_count: int | None = None


@dataclass(frozen=True, slots=True)
class PairEvent:
    room: str
    content: PairData


@dataclass(frozen=True, slots=True)
class PairData:
    pair_address: str
    token_address: str
    created_at: datetime
    deployer_address: str
    token_name: str
    token_ticker: str
    protocol: str
    dev_holds_percent: float | None = None
    snipers_hold_percent: float | None = None
    token_image: str | None = None
    extra: bool = False
    website: str | None = None
    twitter: str | None = None
    telegram: str | None = None
    discord: str | None = None


@dataclass(frozen=True, slots=True)
class HistoryToken:
    pair_address: str
    token_address: str
    token_ticker: str
    token_name: str
    token_image_link: str
    current_protocol: str
    created_at: datetime
    is_migrated: bool
    ath_mcap_in_usd: float | None


@dataclass(frozen=True, slots=True)
class Counts:
    total_count: int
    migrated_count: int


@dataclass(frozen=True, slots=True)
class History:
    counts: Counts
    tokens: list[HistoryToken]


@dataclass(frozen=True, slots=True)
class PairDetails:
    funding_wallet: str | None = None
    token_image: str | None = None
    website: str | None = None
    telegram: str | None = None
    discord: str | None = None
    twitter: str | None = None


@dataclass(frozen=True, slots=True)
class TokenFees:
    total_pair_fees_paid: float
    dex_paid: bool
