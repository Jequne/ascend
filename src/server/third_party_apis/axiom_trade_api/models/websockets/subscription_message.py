from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RoomSubscribeRequest(BaseModel):
    action: str = "join"
    room: Literal["new_pairs", "sol_price", "migrations"]


class SolPriceRoomMessage(BaseModel):
    room: Literal["sol_price"]
    content: float


class NewPairsRoomContent(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    pair_address: str
    token_address: str
    token_name: str
    token_ticker: str
    protocol: str
    created_at: datetime
    open_trading: datetime
    updated_at: datetime

    signature: Optional[str] = None
    token_image: Optional[str] = None
    token_uri: Optional[str] = None
    token_decimals: Optional[int] = None
    pair_sol_account: Optional[str] = None
    pair_token_account: Optional[str] = None
    protocol_details: Optional[Dict[str, Any]] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    discord: Optional[str] = None
    mint_authority: Optional[str] = None
    deployer_address: Optional[str] = None
    supply: Optional[float] = None
    initial_liquidity_sol: Optional[float] = None
    initial_liquidity_token: Optional[float] = None
    top_10_holders: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("top_10_holders", "top10_holders", "top10Holders")
    )
    lp_burned: Optional[float] = None
    freeze_authority: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    slot: Optional[int] = None
    display_protocol: Optional[str] = None
    dev_holds_percent: Optional[float] = None
    snipers_hold_percent: Optional[float] = None


class NewPairsRoomMessage(BaseModel):
    room: Literal["new_pairs"]
    content: NewPairsRoomContent