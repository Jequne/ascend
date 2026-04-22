from pydantic import BaseModel, Field, ConfigDict, model_validator, model_serializer
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time


class PairChartV2Params(BaseModel):
    model_config=ConfigDict(extra="allow", populate_by_name=True)

    pair_address: str = Field(..., alias="pairAddress")
    chart_from: Optional[int] = Field(default=None, alias="from")
    chart_to: Optional[int] = Field(default=None, alias="to")
    currency: str = Field(default="USD")
    interval: str = Field(default="24h")
    count_bars: int = Field(default=500, alias="countBars")
    open_trading: int = Field(..., alias="openTrading")
    last_transaction_time: int = Field(..., alias="lastTransactionTime")

    @model_validator(mode="before")
    @classmethod
    def set_chart_range_defaults(cls, data):
        if not isinstance(data, dict):
            return data

        if data.get("from") is None and data.get("chart_from") is None:
            open_trading = data.get("openTrading", data.get("open_trading"))
            if open_trading is not None:
                data["from"] = open_trading

        if data.get("to") is None and data.get("chart_to") is None:
            last_transaction_time = \
                data.get(
                    "lastTransactionTime", data.get("last_transaction_time")
                    )
            if last_transaction_time is not None:
                data["to"] = last_transaction_time

        return data

    def to_http_query_string(self, sep: str = "&") -> str:
        data = self.model_dump(by_alias=True, exclude_none=True)

        return sep.join(f"{k}={v}" for k, v in data.items())


class PairChartV2Bar(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @model_validator(mode="before")
    @classmethod
    def name_fields_from_bar_list(cls, data: List) -> dict:
        if not isinstance(data, list):
            raise ValueError(f"{data} is not a list")
        
        if len(data) != 6:
            raise ValueError(f"Expected 6 values, got {len(data)}: {data}")

        result = {}
        
        for field_name, value_from_data \
            in zip(cls.model_fields.keys(), data):
            result[field_name] = value_from_data
        
        return result


class PairChartV2Response(BaseModel):
    model_config=ConfigDict(extra="ignore", populate_by_name=True)

    bars: List[PairChartV2Bar]