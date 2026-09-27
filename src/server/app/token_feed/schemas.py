from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class DeployedToken(BaseModel):
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


class TokenFeedBase(BaseModel):
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
