from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# synchronous engine/session (existing)
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    register_models()

    Base.metadata.create_all(bind=engine)


# --- Async setup ---
# For SQLite we'll switch the driver to aiosqlite (sqlite+aiosqlite:///...)

async_engine = create_async_engine(settings.database_async_url, future=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()

        except Exception as e:
            await session.rollback()
            raise e


def register_models() -> None:
    from .api_keys.adapters.models import ApiKeyModel  # noqa: F401
