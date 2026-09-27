import asyncio
import logging
import math
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import ParamSpec, TypeVar, cast

from .base import prepare_base
from .contracts import HistoryProvider
from .developer_history import select_developer_tokens
from .domain import (
    DeployedToken,
    History,
    HistoryToken,
    PairEvent,
    TokenFeedBase,
)
from .funding_history import (
    HistoricalTokenCandidate,
    select_previous_token_indexes,
)

logger = logging.getLogger(__name__)
P = ParamSpec("P")
T = TypeVar("T")
FUNDING_ADDRESS = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def validate_funding_address(address: str) -> str:
    address = address.strip()
    if not FUNDING_ADDRESS.fullmatch(address):
        raise ValueError("invalid funding address")
    return address


class FeedEnrichment:
    def __init__(self, provider: HistoryProvider):
        self._provider = provider
        self._request_cache: dict[
            tuple[str, str], tuple[float, asyncio.Task[object]]
        ] = {}
        self._pending_requests: set[asyncio.Task[object]] = set()
        self._cache_hits: dict[str, int] = {}
        self._cache_misses: dict[str, int] = {}
        self._request_cache_ttl_seconds = 3.0

    async def _get_cached_request(
        self,
        kind: str,
        address: str,
        request: Callable[P, Awaitable[T | None]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T | None:
        now = time.monotonic()
        key = (kind, address)
        cached = self._request_cache.get(key)
        cache_hit = bool(cached and (cached[0] > now or not cached[1].done()))
        if cache_hit:
            self._cache_hits[kind] = self._cache_hits.get(kind, 0) + 1
            assert cached is not None
            # Each (kind, address) has a single provider result type.
            task = cast(asyncio.Task[T | None], cached[1])
        else:
            self._cache_misses[kind] = self._cache_misses.get(kind, 0) + 1
            task = asyncio.create_task(
                self._run_bounded_request(request, *args, **kwargs)
            )
            stored_task = cast(asyncio.Task[object], task)
            self._pending_requests.add(stored_task)
            task.add_done_callback(self._pending_requests.discard)
            if len(self._request_cache) >= 256:
                for old_key, (_, candidate) in list(
                    self._request_cache.items()
                ):
                    if candidate.done():
                        del self._request_cache[old_key]
                        break
            if len(self._request_cache) < 256:
                self._request_cache[key] = (
                    now + self._request_cache_ttl_seconds,
                    stored_task,
                )
        logger.debug(
            "Enrichment cache %s: %s hits=%s misses=%s",
            "hit" if cache_hit else "miss",
            kind,
            self._cache_hits.get(kind, 0),
            self._cache_misses.get(kind, 0),
        )
        try:
            result = await asyncio.shield(task)
            entry = self._request_cache.get(key)
            if entry is not None and entry[1] is task and not cache_hit:
                if result is None:
                    self._request_cache.pop(key, None)
                else:
                    self._request_cache[key] = (
                        time.monotonic() + self._request_cache_ttl_seconds,
                        cast(asyncio.Task[object], task),
                    )
            return result
        except Exception:
            entry = self._request_cache.get(key)
            if entry is not None and entry[1] is task:
                self._request_cache.pop(key, None)
            raise

    async def _get_cached_funding_tokens(self, wallet: str) -> History | None:
        return await self._get_cached_request(
            "funding_history",
            wallet,
            self._provider.dev_tokens_v3,
            dev_address=wallet,
            background=True,
        )

    async def _run_bounded_request(
        self,
        request: Callable[P, Awaitable[T | None]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T | None:
        return await request(*args, **kwargs)

    async def _get_full_info_about_recent_tokens(
        self,
        tokens: list[HistoryToken],
        dev_wallet: str,
        blockchain: str,
        require_verified_fees: bool = True,
    ) -> list[DeployedToken]:
        async def enrich(token: HistoryToken) -> DeployedToken | None:
            pair_result, token_result = await asyncio.gather(
                self._get_cached_request(
                    "pair_info",
                    token.pair_address,
                    self._provider.pair_info,
                    pair_address=token.pair_address,
                    background=True,
                ),
                self._get_cached_request(
                    "token_info",
                    token.pair_address,
                    self._provider.token_info,
                    pair_address=token.pair_address,
                    background=True,
                ),
                return_exceptions=True,
            )
            pair_info = (
                None if isinstance(pair_result, BaseException) else pair_result
            )
            fees_info = (
                None
                if isinstance(token_result, BaseException)
                else token_result
            )
            verified = (
                fees_info is not None
                and math.isfinite(fees_info.total_pair_fees_paid)
                and fees_info.total_pair_fees_paid >= 0
            )
            if not verified and require_verified_fees:
                logger.warning("Previous token fees unavailable or invalid")
                return None
            return DeployedToken(
                blockchain=blockchain,
                total_pair_fees_paid=fees_info.total_pair_fees_paid
                if verified and fees_info
                else None,
                ath_mcap_in_usd=token.ath_mcap_in_usd,
                dex_paid=fees_info.dex_paid
                if verified and fees_info
                else False,
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
            )

        results = await asyncio.gather(*(enrich(token) for token in tokens))
        return [token for token in results if token is not None]

    async def _prepared_last_deployed_tokens(
        self,
        new_token_pair_address: str,
        blockchain: str,
        dev_tokens: History,
        dev_wallet: str,
    ) -> list[DeployedToken] | None:
        if dev_tokens:
            recent_deployed_tokens = select_developer_tokens(
                dev_tokens.tokens, new_token_pair_address
            )
            recent_deployed_tokens_data: list[
                DeployedToken
            ] = await self._get_full_info_about_recent_tokens(
                recent_deployed_tokens,
                dev_wallet,
                blockchain,
                require_verified_fees=False,
            )

            return recent_deployed_tokens_data

        return None

    async def _get_funding_history(
        self,
        new_pairs_data: PairEvent,
    ) -> tuple[str | None, list[DeployedToken] | None, int | None, int | None]:
        """Resolve only the immediate funder and its Axiom token history."""
        try:
            pair_info = await self._run_bounded_request(
                self._provider.pair_info,
                pair_address=new_pairs_data.content.pair_address,
                background=True,
            )
            funding = pair_info.funding_wallet if pair_info else None
            if funding is None:
                return None, None, None, None
            funding_wallet = validate_funding_address(funding)
        except (ValueError, AttributeError):
            return None, None, None, None
        except Exception:
            logger.warning("Current pair funding lookup failed", exc_info=True)
            return None, None, None, None

        try:
            history = await self._get_cached_funding_tokens(funding_wallet)
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
            selected_tokens = [
                history.tokens[index] for index in selected_indexes
            ]
            tokens = await self._get_full_info_about_recent_tokens(
                selected_tokens, funding_wallet, "sol"
            )
            return funding_wallet, tokens, migrated_count, total_count
        except Exception:
            logger.warning("Funding history lookup failed", exc_info=True)
            return funding_wallet, None, None, None

    async def prepare_token_feed(
        self, new_pairs_data: PairEvent
    ) -> TokenFeedBase:
        return prepare_base(new_pairs_data)

    async def prepare_developer_update(
        self, new_pairs_data: PairEvent, base_feed: TokenFeedBase
    ) -> TokenFeedBase | None:
        dev_wallet = new_pairs_data.content.deployer_address
        try:
            dev_tokens = await self._run_bounded_request(
                self._provider.dev_tokens_v3,
                dev_address=dev_wallet,
            )
        except Exception:
            logger.warning(
                "Developer token history lookup failed", exc_info=True
            )
            return None
        if dev_tokens is None:
            return None
        try:
            last_deployed_tokens = await self._prepared_last_deployed_tokens(
                blockchain=base_feed.blockchain,
                dev_tokens=dev_tokens,
                dev_wallet=dev_wallet,
                new_token_pair_address=base_feed.pair_address,
            )
        except Exception:
            logger.warning(
                "Developer history enrichment failed", exc_info=True
            )
            last_deployed_tokens = None
        return replace(
            base_feed,
            last_deployed_tokens=last_deployed_tokens,
            migrated_tokens_count=dev_tokens.counts.migrated_count,
            all_tokens_count=dev_tokens.counts.total_count,
        )

    async def prepare_funding_update(
        self,
        new_pairs_data: PairEvent,
        base_feed: TokenFeedBase,
    ) -> TokenFeedBase | None:
        if base_feed.blockchain != "sol":
            return None
        (
            funding_wallet,
            funding_deployed_tokens,
            migrated_count,
            total_count,
        ) = await self._get_funding_history(new_pairs_data)
        if funding_wallet is None:
            return None
        return replace(
            base_feed,
            funding_wallet=funding_wallet,
            funding_deployed_tokens=funding_deployed_tokens,
            funding_migrated_tokens_count=migrated_count,
            funding_all_tokens_count=total_count,
        )

    async def stop(self) -> None:
        tasks = tuple(self._pending_requests)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._request_cache.clear()
        self._pending_requests.clear()
        self._cache_hits.clear()
        self._cache_misses.clear()
