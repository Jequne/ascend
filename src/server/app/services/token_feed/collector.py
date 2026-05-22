import asyncio
from typing import Any, List, Optional
import logging

from ...schemas.token_feed_models import TokenFeedBase
from .token_feed_preparer import TokenFeedPreparer
from ...config import settings


logger = logging.getLogger(__name__)


class TokenFeedCollector():
    tokens_feed: asyncio.Queue[TokenFeedBase] = asyncio.Queue()
    _lock = asyncio.Lock()

    def __init__(self, token_feed_sources: List[TokenFeedPreparer]):
        self.token_feed_sources: List[TokenFeedPreparer] = token_feed_sources
        
    @staticmethod
    def _str_token_feed_data_for_print(prepared_token_feed: TokenFeedBase) -> str:
        if prepared_token_feed.all_tokens_count != 0:
            migrated_percentage = (prepared_token_feed.migrated_tokens_count \
                  / prepared_token_feed.all_tokens_count) * 100

        else:
            migrated_percentage = f"⁉️ Zero Division cant detect"  

        info = f'\n'
        info += f'🔍 {prepared_token_feed.token_address} ; '
        info += f'{prepared_token_feed.token_ticker} ({prepared_token_feed.token_name}) ; '
        info += f'dev holds: {prepared_token_feed.dev_holds_percent} %\n'
        info += f'🛠️ dev: {prepared_token_feed.dev_wallet} '
        info += f'({migrated_percentage} migrated): \n'

        if prepared_token_feed.last_deployed_tokens:
            for deployed_token in prepared_token_feed.last_deployed_tokens:
                info += f'|- 🪙 {deployed_token.token_ticker} ({deployed_token.token_name}); '
                info += f'total fees paid: {deployed_token.total_pair_fees_paid}\n'
        
        else:
            info += f"Tokens not found for dev {prepared_token_feed.dev_wallet}\n"
        
        return info

    async def _add_to_tokens_feed(
            cls,
            prepared_token_feed: TokenFeedBase,
            ttl_in_minutes: float = 1
            ):
        await cls.tokens_feed.put(prepared_token_feed)

    async def collect_token_feed_data(
            self, 
            websocket_message_data: Any
            ) -> None:
        logger.debug("collect_token_feed_data_called")

        logger.debug("message for callback:\n %s", websocket_message_data)

        for token_feed_source in self.token_feed_sources:
            prepared_token_feed: Optional[TokenFeedBase] = await \
                token_feed_source.prepare_token_feed(websocket_message_data)
            
            if prepared_token_feed:

                await self._add_to_tokens_feed(prepared_token_feed)

                logger.debug("prepared token feed: %s", prepared_token_feed)
                logger.info(
                    TokenFeedCollector._str_token_feed_data_for_print(
                        prepared_token_feed
                        )
                    )

    async def start(self):
        for token_feed_source in self.token_feed_sources:
            token_feed_source.set_callback(self.collect_token_feed_data)


async def main():
    from .axiom_dev_token_data import AxiomDevTokenData


    axiom_token_feed_collector = TokenFeedCollector([AxiomDevTokenData])
    
    await axiom_token_feed_collector.start()

    await asyncio.sleep(1500)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        pass
    

    


