from pydantic import Field, BaseModel
from typing import Literal, Optional, List


class DeployedToken(BaseModel):
    blockchain: str
    total_pair_fees_paid: float
    ath_mcap_in_usd: float
    # dev_holds_percent: float
    dex_paid: bool
    # snipers_hold_percent: float
    pair_address: str
    token_address: str
    token_image: str
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


class TokenFeedBase(BaseModel):
    blockchain: str
    # total_pair_fees_paid: float
    # ath_mcap_in_usd: float
    dev_holds_percent: float
    # dex_paid: bool
    snipers_hold_percent: float
    pair_address: str
    token_address: str
    token_image: str
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


class TokenFeedSol(TokenFeedBase):
    pass

class TokenFeedBsc(TokenFeedBase):
    pass


