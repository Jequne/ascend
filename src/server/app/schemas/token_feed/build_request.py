from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TokenFeedBuildRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    provider_name: str
    payload: dict[str, object]