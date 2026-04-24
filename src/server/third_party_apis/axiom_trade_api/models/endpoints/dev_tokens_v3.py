from pydantic import BaseModel, Field, model_validator
from typing import Any, Optional, List, Union
from datetime import datetime


class Counts(BaseModel):
    total_count: int = Field(..., alias="totalCount")
    migrated_count: int = Field(..., alias="migratedCount")


class MigrationInfo(BaseModel):
    migrated_from: str = Field(..., alias="migratedFrom")
    pump_deployer_address: str = Field(..., alias="pumpDeployerAddress")


class Token(BaseModel):
    pair_address: str
    token_address: str
    token_ticker: str
    token_name: str
    token_image_link: str
    current_protocol: str
    supply: float
    migration_info: Optional[MigrationInfo]
    created_at: datetime
    is_migrated: bool
    current_price_in_sol: Union[float, int]  
    ath_mcap_in_usd: Optional[float]

    @model_validator(mode="before")
    @classmethod
    def set_model_fields_from_list(cls, data: list[Any]) -> dict[str, Any]:
        if not isinstance(data, list):
            raise ValueError(f"{data} is not a list")

        result = {}

        result["pair_address"] = data[0]
        result["token_address"] = data[1]
        result["token_ticker"] = data[2]
        result["token_name"] = data[3]
        result["token_image_link"] = data[4]
        result["current_protocol"] = data[5]
        result["supply"] = data[6]
        result["migration_info"] = data[7]
        result["created_at"] = data[8]
        result["is_migrated"] = data[9]
        result["current_price_in_sol"] = data[13]
        result["ath_mcap_in_usd"] = data[14]

        return result


class DevTokensV3Response(BaseModel):
    counts: Counts
    tokens: List[Token]