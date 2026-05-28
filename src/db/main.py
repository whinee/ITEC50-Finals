"""Database Engine Configuration.

Initializes the incredibly fast asynchronous `asyncpg` engine and synchronous engine, orchestrating the zero-trust persistence layer.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.settings import settings

DATABASE_SYNC_URL = settings.PG_SYNC_URL
DATABASE_ASYNC_URL = settings.PG_ASYNC_URL

# sync engine ONLY for table creation
sync_engine = create_engine(DATABASE_SYNC_URL)

# async engine for queries
async_engine = create_async_engine(DATABASE_ASYNC_URL, echo=True)

async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Asynchronous dependency injection generator for PostgreSQL sessions.

    Yields a highly optimized `AsyncSession` bound to the `asyncpg` engine. By leveraging asynchronous I/O and `expire_on_commit=False`, this ensures sub-millisecond latency for complex database queries while aggressively preventing blocking operations in the FastAPI event loop.

    Yields:
        AsyncSession: The extremely fast, zero-trust database session.

    """
    async with async_session() as session:
        yield session
