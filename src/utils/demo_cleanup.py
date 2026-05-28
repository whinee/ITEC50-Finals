"""
Demo Account Cleanup Utility.

Provides aggressive raw-SQL deletion mechanisms for wiping demo accounts and their 10,000+ generated artifacts, designed to be run asynchronously via Starlette BackgroundTasks or externally via a chron job.
"""

from sqlalchemy import text

from src.db.main import async_session


async def cleanup_demo_user(user_id: int) -> None:
    """
    Forcefully obliterate all data associated with a demo user via raw SQL.

    Args:
        user_id (int): The ID of the demo user to incinerate.

    """
    async with async_session() as session:
        await session.execute(
            text(
                "DELETE FROM bookmark_tag_junction WHERE bookmark_id IN (SELECT id FROM bookmarks WHERE user_id = :uid)",
            ),
            {"uid": user_id},
        )
        await session.execute(
            text(
                "DELETE FROM bookmark_jd_junction WHERE bookmark_id IN (SELECT id FROM bookmarks WHERE user_id = :uid)",
            ),
            {"uid": user_id},
        )
        await session.execute(
            text("DELETE FROM bookmarks WHERE user_id = :uid"),
            {"uid": user_id},
        )
        await session.execute(
            text("DELETE FROM tags WHERE user_id = :uid"),
            {"uid": user_id},
        )
        await session.execute(
            text("DELETE FROM jd_nodes WHERE user_id = :uid"),
            {"uid": user_id},
        )
        await session.execute(
            text("DELETE FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        await session.commit()
