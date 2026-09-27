import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import api_keys, streaming, token_feed, token_images, token_prices
from third_party_apis import axiom_trade_api as axiom

from .api_keys.adapters.expiry_cleanup import ExpiryCleanup
from .api_keys.adapters.sqlalchemy_repository import SqlAlchemyApiKeyRepository
from .api_keys.api_key_hasher import ApiKeyHasher
from .config import settings
from .database import AsyncSessionLocal
from .streaming.adapters.api_keys_access import ApiKeysAccess
from .token_feed.adapters.axiom import AxiomFeedAdapter
from .token_images.adapters.axiom_http import AxiomTokenImageProvider
from .token_prices.adapters.axiom import AxiomPriceSource


class Runtime:
    def __init__(
        self,
        client: axiom.AxiomTradeClient,
        sessions: async_sessionmaker[AsyncSession],
        pepper: str,
    ):
        self.client = client
        self.manager = streaming.ConnectionManager()
        hasher = ApiKeyHasher(pepper)
        self.access = ApiKeysAccess(
            sessions,
            lambda session: api_keys.ApiKeyManager(
                SqlAlchemyApiKeyRepository(session), hasher
            ),
        )
        self.auth = streaming.AuthStreamingProcessor(self.access, self.manager)
        self.cleanup = ExpiryCleanup(sessions)
        adapter = AxiomFeedAdapter(client)
        self.feed = token_feed.TokenFeedCollector(
            adapter, token_feed.FeedEnrichment(adapter)
        )
        self.prices = token_prices.PriceService(
            AxiomPriceSource(client), self._price
        )
        self.images: token_images.TokenImageProvider = (
            AxiomTokenImageProvider()
        )
        self._stop = asyncio.Event()
        self._tasks: list[asyncio.Task[None]] = []
        self._closed = False

    async def _price(self, price: token_prices.SolPrice) -> None:
        await self.manager.broadcast_json(
            {"type": "sol_price", "payload": price.value}
        )

    async def _next_payload(self) -> dict[str, object]:
        return token_feed.serialize(await self.feed.tokens_feed.get())

    async def start(self) -> None:
        try:
            await self.feed.start()
            self.prices.start()
            self.client.connect_websocket()
            self._tasks = [
                asyncio.create_task(
                    api_keys.clean_expired_access_keys(
                        self._stop, self.cleanup.remove_expired
                    )
                ),
                asyncio.create_task(
                    streaming.token_feed_broadcaster(
                        self.manager, self._next_payload, stop_event=self._stop
                    )
                ),
                asyncio.create_task(
                    streaming.ping_broadcaster(
                        self.manager, stop_event=self._stop
                    )
                ),
            ]
        except BaseException:
            await self.stop()
            raise

    async def stop(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._stop.set()
        self.prices.stop()
        try:
            await self.feed.stop()
        finally:
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
            await self.client.close()


def build_runtime() -> Runtime:
    client = axiom.AxiomTradeClient(
        settings.axiom_api_config.load_axiom_api_agents()
    )
    return Runtime(client, AsyncSessionLocal, settings.api_key_pepper)
