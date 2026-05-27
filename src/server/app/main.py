from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import asyncio

from .api.v1 import router as api_v1_router
from .config import settings
from .database import init_db
from .services.token_feed.collector import TokenFeedCollector
from .services.token_feed.axiom_dev_token_data import AxiomDevTokenData
from .api.ws.streaming import router as ws_router
from .services.ws_streaming.manager import manager as ws_manager
from .services.ws_streaming.token_feed_broadcaster import token_feed_broadcaster
from .services.ws_streaming.ping_broadcaster import ping_broadcaster
from .services.ws_streaming.price_broadcaster import sol_price_broadcaster
from .core.expired_access_keys_cleaner import clean_expired_access_keys



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    collector = TokenFeedCollector([AxiomDevTokenData])
    await collector.start()

    sol_price_broadcaster()

    stop_event = asyncio.Event()
    access_keys_cleaner_task = asyncio.create_task(
        clean_expired_access_keys(stop_event=stop_event)
    )

    broadcaster_task = asyncio.create_task(
        token_feed_broadcaster(ws_manager, stop_event=stop_event)
    )
    ping_task = asyncio.create_task(
        ping_broadcaster(ws_manager, stop_event=stop_event, interval=30)
    )
    yield
    stop_event.set()
    broadcaster_task.cancel()
    ping_task.cancel()
    access_keys_cleaner_task.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}


