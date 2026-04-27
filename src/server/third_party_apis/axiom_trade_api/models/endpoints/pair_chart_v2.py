from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Any, Optional, List


class PairChartV2Params(BaseModel):
    model_config=ConfigDict(extra="allow", populate_by_name=True)

    pair_address: str = Field(..., alias="pairAddress")
    chart_from: int = Field(..., alias="from")
    chart_to: int = Field(..., alias="to")
    currency: str = Field(default="USD")
    interval: str = Field(default="24h")
    count_bars: int = Field(default=500, alias="countBars")
    open_trading: Optional[int] = Field(None, alias="openTrading")
    last_transaction_time: Optional[int] = Field(None, alias="lastTransactionTime")

    @model_validator(mode="before")
    @classmethod
    def set_chart_range_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        if data.get("open_trading") is None and data.get("openTrading") is None:
            chart_from = data.get("from", data.get("chart_from"))
            if chart_from is not None:
                data["openTrading"] = chart_from

        if data.get("last_transaction_time") is None \
            and data.get("lastTransactionTime") is None:
            chart_to = \
                data.get(
                    "to", data.get("chart_to")
                    )
            if chart_to is not None:
                data["lastTransactionTime"] = chart_to

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
    def name_fields_from_bar_list(cls, data: list[Any]) -> dict[str, Any]:
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