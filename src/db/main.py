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
    async with async_session() as session:
        yield session
