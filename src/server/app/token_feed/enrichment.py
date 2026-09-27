import asyncio
import logging
import math
import re
import time
from collections.abc import AsyncGenerator, Callable, Coroutine
from dataclasses import dataclass, replace
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
    TokenFees,
)
from .funding_history import (
    HistoricalTokenCandidate,
    select_previous_token_indexes,
)

logger = logging.getLogger(__name__)
P = ParamSpec("P")
T = TypeVar("T")
REQUEST_CACHE_LIMIT = 256
FUNDING_ADDRESS = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def validate_funding_address(address: str) -> str:
    address = address.strip()
    if not FUNDING_ADDRESS.fullmatch(address):
        raise ValueError("invalid funding address")
    return address


@dataclass(frozen=True, slots=True)
class CachedRequest:
    expires_at: float
    task: asyncio.Task[object]


class FeedEnrichment:
    def __init__(self, provider: HistoryProvider):
        self._provider = provider
        self._request_cache: dict[tuple[str, str], CachedRequest] = {}
        self._pending_requests: set[asyncio.Task[object]] = set()
        self._cache_hits: dict[str, int] = {}
        self._cache_misses: dict[str, int] = {}
        self._request_cache_ttl_seconds = 3.0

    async def _get_cached_request(
        self,
        kind: str,
        address: str,
        request: Callable[P, Coroutine[object, object, T | None]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T | None:
        now = time.monotonic()
        key = (kind, address)
        cached = self._request_cache.get(key)
        if cached is not None and (
            cached.expires_at > now or not cached.task.done()
        ):
            cache_hit = True
            self._cache_hits[kind] = self._cache_hits.get(kind, 0) + 1
            # Each (kind, address) has a single provider result type.
            task = cast(asyncio.Task[T | None], cached.task)
        else:
            cache_hit = False
            self._cache_misses[kind] = self._cache_misses.get(kind, 0) + 1
            task = asyncio.create_task(request(*args, **kwargs))
            stored_task = cast(asyncio.Task[object], task)
            self._pending_requests.add(stored_task)
            task.add_done_callback(self._pending_requests.discard)
            self._remember_request(key, now, stored_task)
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
            if entry is not None and entry.task is task and not cache_hit:
                if result is None:
                    self._request_cache.pop(key, None)
                else:
                    self._request_cache[key] = CachedRequest(
                        expires_at=(
                            time.monotonic() + self._request_cache_ttl_seconds
                        ),
                        task=cast(asyncio.Task[object], task),
                    )
            return result
        except Exception:
            entry = self._request_cache.get(key)
            if entry is not None and entry.task is task:
                self._request_cache.pop(key, None)
            raise

    def _remember_request(
        self,
        key: tuple[str, str],
        now: float,
        task: asyncio.Task[object],
    ) -> None:
        # Make room by evicting a completed request, never shared active work.
        if len(self._request_cache) >= REQUEST_CACHE_LIMIT:
            for old_key, cached in self._request_cache.items():
                if cached.task.done():
                    del self._request_cache[old_key]
                    break
        if len(self._request_cache) < REQUEST_CACHE_LIMIT:
            self._request_cache[key] = CachedRequest(
                expires_at=now + self._request_cache_ttl_seconds,
                task=task,
            )

    async def _get_cached_funding_tokens(self, wallet: str) -> History | None:
        return await self._get_cached_request(
            "wallet_history",
            wallet,
            self._provider.dev_tokens_v3,
            dev_address=wallet,
            background=False,
        )

    async def _enrich_history_tokens(
        self,
        tokens: list[HistoryToken],
        dev_wallet: str,
        blockchain: str,
        require_verified_fees: bool = True,
    ) -> list[DeployedToken]:
        results = await asyncio.gather(
            *(
                self._enrich_history_token(
                    token, dev_wallet, blockchain, require_verified_fees
                )
                for token in tokens
            )
        )
        return [token for token in results if token is not None]

    async def _enrich_history_token(
        self,
        token: HistoryToken,
        dev_wallet: str,
        blockchain: str,
        require_verified_fees: bool,
    ) -> DeployedToken | None:
        try:
            fees_info = await self._get_cached_request(
                "token_info",
                token.pair_address,
                self._provider.token_info,
                pair_address=token.pair_address,
                background=False,
            )
        except Exception:
            fees_info = None
        if fees_info is not None and (
            not math.isfinite(fees_info.total_pair_fees_paid)
            or fees_info.total_pair_fees_paid < 0
        ):
            fees_info = None
        if fees_info is None and require_verified_fees:
            logger.warning("Previous token fees unavailable or invalid")
            return None
        return self._history_token(token, dev_wallet, blockchain, fees_info)

    @staticmethod
    def _history_token(
        token: HistoryToken,
        dev_wallet: str,
        blockchain: str,
        fees_info: TokenFees | None = None,
    ) -> DeployedToken:
        return DeployedToken(
            blockchain=blockchain,
            total_pair_fees_paid=fees_info.total_pair_fees_paid
            if fees_info is not None
            else None,
            ath_mcap_in_usd=token.ath_mcap_in_usd,
            dex_paid=fees_info.dex_paid if fees_info is not None else False,
            pair_address=token.pair_address,
            token_address=token.token_address,
            token_image=token.token_image_link,
            is_migrated=token.is_migrated,
            website=None,
            telegram=None,
            discord=None,
            twitter=None,
            token_name=token.token_name,
            token_ticker=token.token_ticker,
            twitter_admin_nickname=None,
            twitter_admin_id=None,
            dev_wallet=dev_wallet,
            protocol=token.current_protocol,
            created_at=token.created_at,
        )

    async def _add_history_details(
        self, tokens: list[DeployedToken]
    ) -> list[DeployedToken]:
        async def add_details(token: DeployedToken) -> DeployedToken:
            try:
                details = await self._get_cached_request(
                    "pair_info",
                    token.pair_address,
                    self._provider.pair_info,
                    pair_address=token.pair_address,
                    background=True,
                )
            except Exception:
                return token
            if details is None:
                return token
            return replace(
                token,
                token_image=details.token_image or token.token_image,
                website=details.website,
                telegram=details.telegram,
                discord=details.discord,
                twitter=details.twitter,
            )

        return list(await asyncio.gather(*(add_details(t) for t in tokens)))

    async def _get_funding_history(
        self,
        new_pairs_data: PairEvent,
    ) -> tuple[str | None, list[DeployedToken] | None, int | None, int | None]:
        """Resolve only the immediate funder and its Axiom token history."""
        try:
            pair_info = await self._get_cached_request(
                "pair_info",
                new_pairs_data.content.pair_address,
                self._provider.pair_info,
                pair_address=new_pairs_data.content.pair_address,
                background=False,
            )
            funding = pair_info.funding_wallet if pair_info else None
            if funding is None:
                return None, None, None, None
            funding_wallet = validate_funding_address(funding)
        except ValueError, AttributeError:
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
            tokens = await self._enrich_history_tokens(
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
        result = None
        async for feed in self.developer_updates(new_pairs_data, base_feed):
            result = feed
        return result

    async def developer_updates(
        self, new_pairs_data: PairEvent, base_feed: TokenFeedBase
    ) -> AsyncGenerator[TokenFeedBase, None]:
        dev_wallet = new_pairs_data.content.deployer_address
        try:
            dev_tokens = await self._get_cached_request(
                "wallet_history",
                dev_wallet,
                self._provider.dev_tokens_v3,
                dev_address=dev_wallet,
            )
        except Exception:
            logger.warning(
                "Developer token history lookup failed", exc_info=True
            )
            return
        if dev_tokens is None:
            return
        recent_tokens = select_developer_tokens(
            dev_tokens.tokens, base_feed.pair_address
        )
        preview = replace(
            base_feed,
            last_deployed_tokens=[
                self._history_token(token, dev_wallet, base_feed.blockchain)
                for token in recent_tokens
            ],
            migrated_tokens_count=dev_tokens.counts.migrated_count,
            all_tokens_count=dev_tokens.counts.total_count,
        )
        yield preview
        if not recent_tokens:
            return
        try:
            last_deployed_tokens = await self._enrich_history_tokens(
                recent_tokens,
                dev_wallet,
                base_feed.blockchain,
                require_verified_fees=False,
            )
        except Exception:
            logger.warning(
                "Developer history enrichment failed", exc_info=True
            )
            return
        verified = replace(
            preview,
            last_deployed_tokens=last_deployed_tokens,
            migrated_tokens_count=dev_tokens.counts.migrated_count,
            all_tokens_count=dev_tokens.counts.total_count,
        )
        yield verified
        detailed = await self._add_history_details(last_deployed_tokens)
        if detailed != last_deployed_tokens:
            yield replace(verified, last_deployed_tokens=detailed)

    async def prepare_funding_update(
        self,
        new_pairs_data: PairEvent,
        base_feed: TokenFeedBase,
    ) -> TokenFeedBase | None:
        result = None
        async for feed in self.funding_updates(new_pairs_data, base_feed):
            result = feed
        return result

    async def funding_updates(
        self, new_pairs_data: PairEvent, base_feed: TokenFeedBase
    ) -> AsyncGenerator[TokenFeedBase, None]:
        if base_feed.blockchain != "sol":
            return
        (
            funding_wallet,
            funding_deployed_tokens,
            migrated_count,
            total_count,
        ) = await self._get_funding_history(new_pairs_data)
        if funding_wallet is None:
            return
        verified = replace(
            base_feed,
            funding_wallet=funding_wallet,
            funding_deployed_tokens=funding_deployed_tokens,
            funding_migrated_tokens_count=migrated_count,
            funding_all_tokens_count=total_count,
        )
        yield verified
        if funding_deployed_tokens:
            detailed = await self._add_history_details(funding_deployed_tokens)
            if detailed != funding_deployed_tokens:
                yield replace(verified, funding_deployed_tokens=detailed)

    async def stop(self) -> None:
        tasks = tuple(self._pending_requests)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._request_cache.clear()
        self._pending_requests.clear()
        self._cache_hits.clear()
        self._cache_misses.clear()
