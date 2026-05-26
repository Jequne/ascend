from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
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
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from .models import ApiKey  # noqa: F401

    Base.metadata.create_all(bind=engine)


# --- Async setup ---
# For SQLite we'll switch the driver to aiosqlite (sqlite+aiosqlite:///...)

async_engine = create_async_engine(settings.database_async_url, future=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session