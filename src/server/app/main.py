from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api_keys.router import router as api_keys_router
from .composition import Runtime, build_runtime
from .config import settings
from .database import init_db
from .streaming.router import router as ws_router
from .token_images.router import router as token_images_router


def create_app(
    runtime_factory: Callable[[], Runtime] = build_runtime,
    initialize_database: Callable[[], None] = init_db,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        runtime = runtime_factory()
        app.state.runtime = runtime
        try:
            initialize_database()
            await runtime.start()
            yield
        finally:
            await runtime.stop()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_keys_router, prefix="/api/v1")
    app.include_router(token_images_router, prefix="/api/v1")
    app.include_router(ws_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
