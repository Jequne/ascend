from typing import Protocol, Callable, Optional

from ...schemas.token_feed_models import TokenFeedBase, DeployedToken
from third_party_apis.axiom_trade_api.models.websockets.subscription_message \
    import NewPairsRoomMessage


class TokenFeedPreparer(Protocol):

    @classmethod
    async def prepare_token_feed(
            cls, 
            new_pairs_data: NewPairsRoomMessage
            ) -> Optional[TokenFeedBase]:
        pass
    
    @classmethod
    def set_callback(cls, callback: Callable):
        pass
