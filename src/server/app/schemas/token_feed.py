from pydantic import Field, BaseModel
from typing import Literal, Optional, List
from datetime import datetime


class DeployedToken(BaseModel):
    blockchain: str
    total_pair_fees_paid: float
    ath_mcap_in_usd: Optional[float]
    # dev_holds_percent: float
    dex_paid: bool
    # snipers_hold_percent: float
    pair_address: str
    token_address: str
    token_image: Optional[str]
    is_migrated: bool
    website: Optional[str]
    telegram: Optional[str]
    discord: Optional[str]
    twitter: Optional[str]
    token_name: str
    token_ticker: str
    twitter_admin_nickname: Optional[str]
    twitter_admin_id: Optional[str]
    dev_wallet: str
    protocol: str
    created_at: datetime


class TokenFeedBase(BaseModel):
    # total_pair_fees_paid: float
    # ath_mcap_in_usd: float
    dev_holds_percent: float
    # dex_paid: bool
    snipers_hold_percent: float
    pair_address: str
    token_address: str
    token_image: Optional[str]
    is_migrated: bool
    website: Optional[str]
    telegram: Optional[str]
    discord: Optional[str]
    twitter: Optional[str]
    token_name: str
    token_ticker: str
    twitter_admin_nickname: Optional[str]
    twitter_admin_id: Optional[str]
    dev_wallet: str
    protocol: str
    last_deployed_tokens: Optional[List[DeployedToken]]
    migrated_tokens_count: int
    all_tokens_count: int

class TokenFeedSol(TokenFeedBase):
    blockchain: str = "sol"


class TokenFeedBsc(TokenFeedBase):
    blockchain: str = "bsc"


