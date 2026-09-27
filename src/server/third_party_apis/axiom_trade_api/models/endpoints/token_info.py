from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TokenInfoResponse(BaseModel):
    bundlers_hold_percent: float = Field(..., alias="bundlersHoldPercent")
    dev_holds_percent: float = Field(..., alias="devHoldsPercent")
    dex_paid: bool = Field(..., alias="dexPaid")
    dex_paid_time: Optional[datetime] = Field(None, alias="dexPaidTime")
    insiders_hold_percent: float = Field(..., alias="insidersHoldPercent")
    num_bot_users: int = Field(..., alias="numBotUsers")
    num_holders: int = Field(..., alias="numHolders")
    snipers_hold_percent: float = Field(..., alias="snipersHoldPercent")
    top10_holders_percent: float = Field(..., alias="top10HoldersPercent")
    total_pair_fees_paid: float = Field(..., alias="totalPairFeesPaid")
