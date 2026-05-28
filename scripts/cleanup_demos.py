#!/usr/bin/env python3
"""
Cron-ready Demo Account Sweeper.

Scans the database for expired demo accounts (accounts untouched for > 60 minutes) and forcefully completely purges them via the cleanup_demo_user utility. Intended to be invoked externally via cron.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Ensure root directory is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

from src.db.main import async_session
from src.schema import User
from src.utils.demo_cleanup import cleanup_demo_user


async def main() -> None:
    """Execute the chronological sweep for stale demo data."""
    print(f"[{datetime.now(UTC).isoformat()}] Starting demo account sweep...")

    expiration_threshold = datetime.now(UTC) - timedelta(minutes=60)
    deleted_count = 0

    async with async_session() as session:
        # Find demo accounts where updated_at < expiration_threshold
        query = select(User).where(
            User.email.endswith("@demo.decimark.com"),
            User.updated_at < expiration_threshold,
        )
        result = await session.execute(query)
        expired_users = result.scalars().all()

        if not expired_users:
            print("No expired demo accounts found.")
            return

        print(f"Found {len(expired_users)} expired demo account(s). Purging...")

        for user in expired_users:
            print(f"Purging user: {user.email} (ID: {user.id})")
            await cleanup_demo_user(user.id)
            deleted_count += 1

    print(
        f"[{datetime.now(UTC).isoformat()}] Sweep complete. {deleted_count} account(s) incinerated.",
    )


if __name__ == "__main__":
    asyncio.run(main())
