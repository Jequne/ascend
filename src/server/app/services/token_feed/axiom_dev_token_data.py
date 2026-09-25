from  typing import Any, Awaitable, Callable, List, Optional
import asyncio
import logging
import math
import time
from ...schemas.token_feed_models import TokenFeedBase, DeployedToken
from third_party_apis.axiom_trade_api.client import AxiomTradeClient
from third_party_apis.axiom_trade_api.request_pacer import background_axiom_request
from third_party_apis.axiom_trade_api.models.endpoints.dev_tokens_v3 \
    import DevTokensV3Response, Token
from third_party_apis.axiom_trade_api.models.websockets.subscription_message \
    import NewPairsRoomMessage
from app.token_images.domain import validate_solana_address
from .funding_history import HistoricalTokenCandidate, select_previous_token_indexes


logger = logging.getLogger(__name__)


class AxiomDevTokenData():

    _client: AxiomTradeClient | None = None
    _cache_client: AxiomTradeClient | None = None
    _request_cache: dict[tuple[str, str], tuple[float, asyncio.Task[Any]]] = {}
    _pending_requests: set[asyncio.Task[Any]] = set()
    _request_cache_ttl_seconds = 3.0
    _cache_hits: dict[str, int] = {}
    _cache_misses: dict[str, int] = {}

    @classmethod
    def _get_client(cls) -> AxiomTradeClient:
        if cls._client is not None:
            return cls._client
        from app.core.axiom_client_provider import client_instance
        return client_instance

    @classmethod
    async def _get_cached_request(
        cls,
        kind: str,
        address: str,
        request: Callable[..., Awaitable[Any]],
        **kwargs: Any,
    ) -> Any:
        client = cls._get_client()
        if cls._cache_client is not client:
            cls._request_cache.clear()
            cls._cache_client = client
        now = time.monotonic()
        key = (kind, address)
        cached = cls._request_cache.get(key)
        cache_hit = bool(cached and (cached[0] > now or not cached[1].done()))
        if cache_hit:
            cls._cache_hits[kind] = cls._cache_hits.get(kind, 0) + 1
            logger.debug(
                "Axiom enrichment cache hit: %s hits=%s misses=%s",
                kind, cls._cache_hits[kind], cls._cache_misses.get(kind, 0),
            )
            assert cached is not None
            task = cached[1]
        else:
            cls._cache_misses[kind] = cls._cache_misses.get(kind, 0) + 1
            logger.debug(
                "Axiom enrichment cache miss: %s hits=%s misses=%s",
                kind, cls._cache_hits.get(kind, 0), cls._cache_misses[kind],
            )
            task = asyncio.create_task(cls._run_bounded_request(
                request,
                background=True,
                **kwargs,
            ))
            cls._pending_requests.add(task)
            task.add_done_callback(cls._pending_requests.discard)
            if len(cls._request_cache) >= 256:
                for old_key, (_, candidate) in list(cls._request_cache.items()):
                    if candidate.done():
                        del cls._request_cache[old_key]
                        break
            if len(cls._request_cache) < 256:
                cls._request_cache[key] = (now + cls._request_cache_ttl_seconds, task)
        try:
            result = await asyncio.shield(task)
            if cls._request_cache.get(key, (None, None))[1] is task and not cache_hit:
                if result is None:
                    cls._request_cache.pop(key, None)
                else:
                    cls._request_cache[key] = (
                        time.monotonic() + cls._request_cache_ttl_seconds, task
                    )
            return result
        except Exception:
            if cls._request_cache.get(key, (None, None))[1] is task:
                cls._request_cache.pop(key, None)
            raise

    @classmethod
    async def _get_cached_funding_tokens(
        cls, funding_wallet: str
    ) -> DevTokensV3Response | None:
        return await cls._get_cached_request(
            "funding_history", funding_wallet,
            cls._get_client().dev_tokens_v3, dev_address=funding_wallet,
        )

    @classmethod
    async def _run_bounded_request(
        cls,
        request: Callable[..., Awaitable[Any]],
        background: bool = False,
        **kwargs: Any,
    ) -> Any:
        if background:
            with background_axiom_request():
                return await request(**kwargs)
        return await request(**kwargs)

    @classmethod
    async def _get_full_info_about_recent_tokens(
        cls,
        tokens: list[Token],
        dev_wallet: str,
        blockchain: str,
        require_verified_fees: bool = True,
    ) -> list[DeployedToken]:
        tasks: list[asyncio.Task[Any]] = []
        for token in tokens:
            tasks.append(asyncio.create_task(cls._get_cached_request(
                "pair_info", token.pair_address,
                cls._get_client().pair_info, pair_address=token.pair_address,
            )))
            tasks.append(asyncio.create_task(cls._get_cached_request(
                "token_info", token.pair_address,
                cls._get_client().token_info, pair_address=token.pair_address,
            )))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        deployed_tokens: list[DeployedToken] = []
        for index, token in enumerate(tokens):
            pair_result = results[index * 2]
            token_result = results[index * 2 + 1]
            verified_token = (
                token_result is not None
                and not isinstance(token_result, BaseException)
                and math.isfinite(token_result.total_pair_fees_paid)
                and token_result.total_pair_fees_paid >= 0
            )
            if not verified_token and require_verified_fees:
                logger.warning("Previous token fees unavailable or invalid")
                continue
            fees = token_result.total_pair_fees_paid if verified_token else None
            pair_info = None if isinstance(pair_result, BaseException) else pair_result
            deployed_tokens.append(DeployedToken(
                blockchain=blockchain,
                total_pair_fees_paid=fees,
                ath_mcap_in_usd=token.ath_mcap_in_usd,
                dex_paid=token_result.dex_paid if verified_token else False,
                pair_address=token.pair_address,
                token_address=token.token_address,
                token_image=(pair_info.token_image if pair_info else None)
                    or token.token_image_link,
                is_migrated=token.is_migrated,
                website=pair_info.website if pair_info else None,
                telegram=pair_info.telegram if pair_info else None,
                discord=pair_info.discord if pair_info else None,
                twitter=pair_info.twitter if pair_info else None,
                token_name=token.token_name,
                token_ticker=token.token_ticker,
                twitter_admin_nickname=None,
                twitter_admin_id=None,
                dev_wallet=dev_wallet,
                protocol=token.current_protocol,
                created_at=token.created_at,
            ))
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
                dev_tokens.tokens[1:deployed_tokens_count_need + 1]
            else:
                recent_deployed_tokens = \
                    dev_tokens.tokens[:deployed_tokens_count_need]
            
            recent_deployed_tokens_data: List[DeployedToken] = \
                await cls._get_full_info_about_recent_tokens(
                    recent_deployed_tokens,
                    dev_wallet,
                    blockchain,
                    require_verified_fees=False,
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
    async def _get_funding_history(
        cls,
        new_pairs_data: NewPairsRoomMessage,
    ) -> tuple[str | None, list[DeployedToken] | None, int | None, int | None]:
        """Resolve only the immediate funder and its Axiom token history."""
        try:
            pair_info = await cls._run_bounded_request(
                cls._get_client().pair_info,
                pair_address=new_pairs_data.content.pair_address,
                background=True,
            )
            funding = pair_info.dev_wallet_funding if pair_info else None
            if funding is None:
                return None, None, None, None
            funding_wallet = validate_solana_address(
                funding.funding_wallet_address
            )
        except (ValueError, AttributeError):
            return None, None, None, None
        except Exception:
            logger.warning("Current pair funding lookup failed", exc_info=True)
            return None, None, None, None

        try:
            history = await cls._get_cached_funding_tokens(funding_wallet)
            if history is None:
                return funding_wallet, None, None, None
            migrated_count = history.counts.migrated_count
            total_count = history.counts.total_count
            candidates = [
                HistoricalTokenCandidate(
                    index=index,
                    pair_address=token.pair_address,
                    token_address=token.token_address,
                    created_at=token.created_at,
                )
                for index, token in enumerate(history.tokens)
            ]
            selected_indexes = select_previous_token_indexes(
                candidates,
                current_pair_address=new_pairs_data.content.pair_address,
                current_token_address=new_pairs_data.content.token_address,
                current_created_at=new_pairs_data.content.created_at,
            )
            if not selected_indexes:
                return funding_wallet, [], migrated_count, total_count
            selected_tokens = [history.tokens[index] for index in selected_indexes]
            tokens = await cls._get_full_info_about_recent_tokens(
                selected_tokens, funding_wallet, "sol"
            )
            return funding_wallet, tokens, migrated_count, total_count
        except Exception:
            logger.warning("Funding history lookup failed", exc_info=True)
            return funding_wallet, None, None, None

    @classmethod
    async def prepare_token_feed(
            cls, 
            new_pairs_data: NewPairsRoomMessage
            ) -> Optional[TokenFeedBase]:
        dev_wallet = new_pairs_data.content.deployer_address

        try:
            dev_tokens = await cls._run_bounded_request(
                cls._get_client().dev_tokens_v3,
                dev_address=dev_wallet,
            )
        except Exception:
            logger.warning("Developer token history lookup failed", exc_info=True)
            dev_tokens = None
        
        blockchain = cls._define_blockchain(new_pairs_data)

        try:
            last_deployed_tokens = await cls._prepared_last_deployed_tokens(
                blockchain=blockchain,
                dev_tokens=dev_tokens,
                dev_wallet=dev_wallet,
                new_token_pair_address=new_pairs_data.content.pair_address,
            ) if dev_tokens else None
        except Exception:
            logger.warning("Developer history enrichment failed", exc_info=True)
            last_deployed_tokens = None

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
            migrated_tokens_count=dev_tokens.counts.migrated_count if dev_tokens else 0,
            all_tokens_count=dev_tokens.counts.total_count if dev_tokens else 0,
            funding_wallet=None,
            funding_deployed_tokens=None,
        )

        return token_feed_base

    @classmethod
    async def prepare_funding_update(
        cls,
        new_pairs_data: NewPairsRoomMessage,
        base_feed: TokenFeedBase,
    ) -> TokenFeedBase | None:
        if base_feed.blockchain != "sol":
            return None
        funding_wallet, funding_deployed_tokens, migrated_count, total_count = await cls._get_funding_history(
            new_pairs_data
        )
        if funding_wallet is None:
            return None
        return base_feed.model_copy(update={
            "funding_wallet": funding_wallet,
            "funding_deployed_tokens": funding_deployed_tokens,
            "funding_migrated_tokens_count": migrated_count,
            "funding_all_tokens_count": total_count,
        })

    @classmethod
    async def stop(cls) -> None:
        tasks = [task for task in cls._pending_requests if not task.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        cls._request_cache.clear()
        cls._pending_requests.clear()
        cls._cache_client = None
        cls._cache_hits.clear()
        cls._cache_misses.clear()
    
    @classmethod
    def set_callback(cls, callback: Callable):
        cls._get_client().on_new_pairs(callback)

