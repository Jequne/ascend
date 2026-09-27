from dataclasses import asdict

from .domain import TokenFeedBase
from .schemas import TokenFeedBase as TokenFeedSchema


def serialize(feed: TokenFeedBase) -> dict[str, object]:
    return TokenFeedSchema.model_validate(asdict(feed)).model_dump(mode="json")
