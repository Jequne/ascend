from pydantic import BaseModel, Field, ConfigDict, model_validator, model_serializer
from typing import Optional, Dict
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


class PairChartV2Response(BaseModel):
    model_config=ConfigDict(extra="allow", populate_by_name=True)

    