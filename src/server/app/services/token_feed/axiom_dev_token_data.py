from  typing import List, Callable, Optional
import asyncio
from  datetime import datetime, timedelta, timezone
import logging
from pydantic import ValidationError

from ...schemas.token_feed_models import TokenFeedBase, DeployedToken
from third_party_apis.axiom_trade_api.client import AxiomTradeClient
from third_party_apis.axiom_trade_api.models.auth import AxiomAgentData
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens_v3 \
    import DevTokensV3Response, Token
from third_party_apis.axiom_trade_api.models.websockets.subscription_message \
    import NewPairsRoomMessage
from ...config import settings
from app.core.axiom_client_provider import client_instance


logger = logging.getLogger(__name__)


class AxiomDevTokenData():

    _client: AxiomTradeClient = client_instance
    
    @staticmethod
    def _get_timestamp_interval_for_token_chart_data(
        interval_in_years_to_current_time: int = 3
        ) -> tuple[int, int]:
        now_utc = datetime.now(timezone.utc)
        current_timestamp = int(now_utc.timestamp())

        interval_start = \
            now_utc - timedelta(days=interval_in_years_to_current_time * 365)
        data_from_timestamp = int(interval_start.timestamp())

        return data_from_timestamp, current_timestamp
    
    @classmethod
    async def _get_full_info_about_recent_tokens(
            cls,
            tokens: list[Token],
            dev_wallet: str,
            blockchain: str

            ) -> list[DeployedToken]:

        chart_from, chart_to = \
            cls._get_timestamp_interval_for_token_chart_data()
        
        requests_by_token = []

        for token in tokens:
            pair_info_task = asyncio.create_task(
                cls._client.pair_info(token.pair_address)
            )
            token_info_task = asyncio.create_task(
                cls._client.token_info(token.pair_address)
            )
            pair_chart_task = asyncio.create_task(
                cls._client.pair_chart_v2(
                    pair_address=token.pair_address,
                    chart_from=chart_from,
                    chart_to=chart_to
                )
            )

            requests_by_token.append(
                (token, pair_info_task, token_info_task, pair_chart_task)
            )

        deployed_tokens: list[DeployedToken] = []

        for token, pair_info_task, token_info_task, pair_chart_task \
            in requests_by_token:

            try:
                pair_info_data, token_info_data, _ = await asyncio.gather(
                    pair_info_task,
                    token_info_task,
                    pair_chart_task,
                )

            except Exception as e:
                logger.warning("⚠️ api endpoint coroutine runtime error: %s", e)
                continue
            
            if pair_info_data is None or token_info_data \
                is None or pair_chart_task is None:
                continue

            deployed_tokens.append(
                DeployedToken(
                    blockchain=blockchain,
                    total_pair_fees_paid=\
                        token_info_data.total_pair_fees_paid,
                    ath_mcap_in_usd=token.ath_mcap_in_usd,
                    dex_paid=token_info_data.dex_paid,
                    pair_address=token.pair_address,
                    token_address=token.token_address,
                    token_image=pair_info_data.token_image \
                        or token.token_image_link,
                    is_migrated=token.is_migrated,
                    website=pair_info_data.website,
                    telegram=pair_info_data.telegram,
                    discord=pair_info_data.discord,
                    twitter=pair_info_data.twitter,
                    token_name=token.token_name,
                    token_ticker=token.token_ticker,
                    twitter_admin_nickname=None,
                    twitter_admin_id=None,
                    dev_wallet=dev_wallet,
                    protocol=token.current_protocol,
                    created_at=token.created_at,
                )
            )

        return deployed_tokens

    @classmethod
    async def _prepared_last_deployed_tokens(
            cls,
            new_token_pair_address: str,
            blockchain: str,
            dev_tokens: DevTokensV3Response,
            dev_wallet: str
            ) -> List[DeployedToken] | None:
        deployed_tokens_count_need = 3

        if dev_tokens:
            if len(dev_tokens.tokens) >=1 \
                and dev_tokens.tokens[0].pair_address ==  new_token_pair_address:
                
                recent_deployed_tokens = \
                dev_tokens.tokens[1:deployed_tokens_count_need]
            else:
                recent_deployed_tokens = \
                    dev_tokens.tokens[:deployed_tokens_count_need]
            
            recent_deployed_tokens_data: List[DeployedToken] = \
                await cls._get_full_info_about_recent_tokens(
                    recent_deployed_tokens,
                    dev_wallet,
                    blockchain
                    )
            
            return recent_deployed_tokens_data
    
    @staticmethod
    def _define_blockchain( 
            new_pairs_data: NewPairsRoomMessage
            ) -> str:
        room = new_pairs_data.room

        if "bnb" in room:
            return "bsc"
        
        else:
            return "sol"

    @classmethod
    async def prepare_token_feed(
            cls, 
            new_pairs_data: NewPairsRoomMessage
            ) -> Optional[TokenFeedBase]:
        dev_wallet = new_pairs_data.content.deployer_address

        dev_tokens = await cls._client.dev_tokens_v3(
            dev_address=dev_wallet
            )
        if not dev_tokens:
            return
        
        blockchain = cls._define_blockchain(new_pairs_data)

        last_deployed_tokens = await cls._prepared_last_deployed_tokens(
            blockchain=blockchain,
            dev_tokens=dev_tokens,
            dev_wallet=dev_wallet,
            new_token_pair_address=new_pairs_data.content.pair_address
        )

        token_feed_base = TokenFeedBase(
            blockchain=blockchain,
            dev_holds_percent=new_pairs_data.content.dev_holds_percent,
            snipers_hold_percent=new_pairs_data.content.snipers_hold_percent,
            pair_address=new_pairs_data.content.pair_address,
            token_address=new_pairs_data.content.token_address,
            token_image=new_pairs_data.content.token_image,
            is_migrated=True if new_pairs_data.content.extra else False,
            website=new_pairs_data.content.website,
            twitter=new_pairs_data.content.twitter,
            telegram=new_pairs_data.content.telegram,
            discord=new_pairs_data.content.discord,
            token_name=new_pairs_data.content.token_name,
            token_ticker=new_pairs_data.content.token_ticker,
            dev_wallet=new_pairs_data.content.deployer_address,
            protocol=new_pairs_data.content.protocol,
            last_deployed_tokens=last_deployed_tokens,
            migrated_tokens_count=dev_tokens.counts.migrated_count,
            all_tokens_count=dev_tokens.counts.total_count
        )

        return token_feed_base
    
    @classmethod
    def set_callback(cls, callback: Callable):
        cls._client.on_new_pairs(callback)

