from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from .api.v1 import router as api_v1_router
from .config import settings
from .database import init_db
from .services.token_feed.collector import TokenFeedCollector
from .services.token_feed.axiom_dev_token_data import AxiomDevTokenData
from .api.ws.router import router as ws_router, manager as ws_manager
from .services.token_feed.token_feed_broadcaster import token_feed_broadcaster
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    collector = TokenFeedCollector([AxiomDevTokenData])
    await collector.start()

    stop_event = asyncio.Event()
    broadcaster_task = asyncio.create_task(
        token_feed_broadcaster(ws_manager, stop_event=stop_event)
    )
    yield
    stop_event.set()
    broadcaster_task.cancel()


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

templates = Jinja2Templates(directory="app/templates")

posts = ["num1", "num2"]


@app.get("/health")
def health():
    return {"status": "ok"}


