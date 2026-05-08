import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/bookmarks")
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

# async engine for queries
async_engine = create_async_engine(DATABASE_URL, echo=True)

# sync engine ONLY for table creation
sync_engine = create_engine(SYNC_DATABASE_URL)

async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False  # important for async!
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def init_db():
    SQLModel.metadata.create_all(sync_engine)