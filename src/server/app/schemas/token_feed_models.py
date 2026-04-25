from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DeployedToken(BaseModel):
    blockchain: str
    total_pair_fees_paid: float
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
    dev_holds_percent: float
    snipers_hold_percent: float
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
    last_deployed_tokens: list[DeployedToken] | None
    migrated_tokens_count: int
    all_tokens_count: int


class TokenFeedSol(TokenFeedBase):
    blockchain: str = "sol"


class TokenFeedBsc(TokenFeedBase):
    blockchain: str = "bsc"