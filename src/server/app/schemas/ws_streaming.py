from pydantic import BaseModel, ConfigDict
from typing import Literal, Any, Union

from .token_feed_models import TokenFeedBase


class WsStreamingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["token_feed", "error", "ping"]
    payload: Union[TokenFeedBase, dict[str, Any], str] 