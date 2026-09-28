from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict

class NaturalLanguageRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=500
    )

class StockQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supported:bool 
    unsupported_reason: str | None 

    snapshot_date: date | None = None

    min_change_percent: float | None = Field(
        default=None,
        description="最低涨幅，单位为百分点，例如3%写成3",
    )

    max_market_cap: float | None = Field(
        default=None,
        ge=0,
        description="最大总市值，单位为元",
    )

    min_turnover_amount: float | None = Field(
        default=None,
        ge=0,
        description="最低成交额，单位为元",
    )

    exclude_st: bool = False

    sort_by:Literal[
        "change_percent",
        "turnover_amount",
        "market_cap",
        "turnover_rate",
    ] = "change_percent"

    order: Literal["asc", "desc"] = "desc"

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
    )