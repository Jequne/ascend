from pydantic import BaseModel, ConfigDict
from typing import Literal, Any

from .token_feed_models import TokenFeedBase


class WsStreamingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["token_feed"]
    payload: BaseModel | dict[str,Any]