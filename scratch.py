import asyncio

from sqlmodel import func, select

from src.db.main import async_session
from src.schema import Bookmark, User


async def main():
    print("Connecting...")
    async with async_session() as session:
        print("Connected!")
        bookmark_result = await session.exec(select(func.count(Bookmark.id)))
        print("bookmark_result:", bookmark_result)
        total_bookmarks = bookmark_result.one()
        print("Total bookmarks:", total_bookmarks)
        
        user_result = await session.exec(select(func.count(User.id)))
        total_users = user_result.one()
        print("Total users:", total_users)

asyncio.run(main())
