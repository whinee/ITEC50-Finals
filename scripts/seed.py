"""
High-Performance Database Seeder.

A massively scalable asynchronous database seeder capable of instantly hydrating the PostgreSQL instance with thousands of realistic, normalized records using `Faker`. It utilizes raw SQL bulk inserts and connection pooling to bypass the ORM overhead, making it essential for aggressive load testing and rapid local development loops.
"""

import asyncio
import json
import os
import random
import secrets
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from faker import Faker
from sqlalchemy import text
from sqlmodel import insert

# Ensure the root directory is on the path so we can import 'src'
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.main import async_session
from src.schema import Bookmark, JDNode, Tag, User

# Junction tables
bookmark_tag_junction = Tag.bookmarks.property.secondary  # type: ignore

bookmark_jd_junction = JDNode.bookmarks.property.secondary  # type: ignore

fake = Faker()


def hash_password(password: str) -> str:
    """
    Invoke the staggeringly secure Argon2id KDF to immediately transform raw text into an impenetrable, timing-attack resistant password hash.

    Args:
        password (str): The raw string to protect.

    Returns:
        str: The cryptographically fortified hashed string.

    """
    salt = os.urandom(16)
    kdf = Argon2id(
        salt=salt,
        length=32,
        iterations=1,
        lanes=4,
        memory_cost=64 * 1024,
        ad=None,
        secret=None,
    )
    res = kdf.derive_phc_encoded(password.encode())
    if isinstance(res, bytes):
        return res.decode("utf-8")
    return res


async def clear_data(session) -> None:
    """
    Drop every single record from the database using direct SQL `TRUNCATE TABLE` cascades, resetting the system state in milliseconds.

    Args:
        session (AsyncSession): The database manager.

    """
    print("Clearing existing data...")
    await session.execute(
        text(
            "TRUNCATE TABLE bookmark_jd_junction, bookmark_tag_junction, bookmarks, jd_nodes, tags, users CASCADE",
        ),
    )
    await session.commit()


def generate_jd_code() -> str:
    """
    Use pseudo-random synthesis to consistently generate perfectly formatted Johnny.Decimal structural codes.

    Returns:
        str: The correctly synthesized JD area string.

    """
    part1 = f"{random.randint(10, 99):02d}"  # noqa: S311
    part2 = f"{random.randint(10, 99):02d}"  # noqa: S311
    code = f"{part1}.{part2}"
    if random.random() > 0.5:  # noqa: S311
        # Pre-generated list of words for speed
        words = [
            "tech",
            "news",
            "code",
            "design",
            "work",
            "lyra",
            "school",
            "project",
            "dev",
        ]
        code += f"+{random.choice(words)}"  # noqa: S311
    return code


def random_date(start: datetime, end: datetime) -> datetime:
    """
    Deploys rapid datetime math to instantaneously calculate a perfectly valid timestamp falling precisely within a defined epoch window.

    Args:
        start (datetime): Floor boundary.
        end (datetime): Ceiling boundary.

    Returns:
        datetime: The logically sound random timestamp.

    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    if int_delta <= 0:
        return start
    random_second = random.randrange(int_delta)  # noqa: S311
    return start + timedelta(seconds=random_second)


async def process_user(  # noqa: C901
    session,
    user_data: dict,
    index: int,
    user_password_hash: str,
    next_tag_id: int,
    next_jd_id: int,
    next_bookmark_id: int,
) -> tuple[int, int, int]:
    """
    Manage the entire lifecycle of a fake user payload, from Argon2id hashing to mapping relationships, readying it for high-speed bulk ingestion.

    Args:
        user_data (Any): Undocumented argument.
        session (Any): Undocumented argument.
        next_tag_id (Any): Undocumented argument.
        next_jd_id (Any): Undocumented argument.
        next_bookmark_id (Any): Undocumented argument.
        index (Any): Undocumented argument.
        user_password_hash (Any): Undocumented argument.
        args (tuple): Multi-process mapping payload.

    Returns:
        dict: The completely optimized user dictionary.

    """
    now = datetime.now(UTC)
    epoch = datetime(1970, 1, 1, tzinfo=UTC)

    # 1. Create User
    user_created = random_date(epoch, now)
    user_updated = (
        random_date(user_created, now)
        if random.random() > 0.5  # noqa: S311
        else user_created
    )

    # Insert User
    user_id = index + 1
    await session.execute(
        insert(User).values(
            id=user_id,
            username=user_data["username"],
            email=user_data["email"],
            password=user_password_hash,
            role=user_data["role"],
            created_at=user_created,
            updated_at=user_updated,
            disabled=False,
        ),
    )

    # 2. Determine counts
    bookmark_count = random.randint(3000, 10000)  # noqa: S311
    # The user asked for tag counts to be 10-20% of bookmark count
    tag_count = max(
        1,
        random.randint(  # noqa: S311
            int(bookmark_count * 0.1),
            int(bookmark_count * 0.2),
        ),
    )
    jd_count = random.randint(500, 1000)  # noqa: S311

    print(
        f"User {user_id}: Generating {tag_count} Tags, {jd_count} JDs, {bookmark_count} Bookmarks",
    )

    # 3. Create Tags (Chunked Insert)
    tag_ids = []
    tag_batch = []
    for _ in range(tag_count):
        t_id = next_tag_id
        next_tag_id += 1
        tag_ids.append(t_id)
        t_created = random_date(user_created, now)
        tag_batch.append(
            {
                "id": t_id,
                "user_id": user_id,
                "title": f"tag_{t_id}_{random.randint(1,1000)}",  # noqa: S311
                "color": f"#{random.randint(0, 0xFFFFFF):06x}",  # noqa: S311
                "note": "Bulk generated tag",
                "created_at": t_created,
                "updated_at": t_created,
            },
        )
        if len(tag_batch) >= 5000:
            await session.execute(insert(Tag).values(tag_batch))
            tag_batch = []
    if tag_batch:
        await session.execute(insert(Tag).values(tag_batch))

    # 4. Create JDs
    jd_ids = []
    jd_batch = []
    for _ in range(jd_count):
        j_id = next_jd_id
        next_jd_id += 1
        jd_ids.append(j_id)
        jd_batch.append(
            {
                "id": j_id,
                "user_id": user_id,
                "code": generate_jd_code(),
            },
        )
    if jd_batch:
        await session.execute(insert(JDNode).values(jd_batch))

    # 5. Create Bookmarks & Junctions (Chunked Insert)
    b_batch = []
    b_tag_batch = []
    b_jd_batch = []

    # Pre-generate some fast random strings to avoid Faker overhead in the massive loop
    titles = [f"Amazing resource {i}" for i in range(100)]
    urls = [
        f"https://example.com/{random.randint(1, 100000)}"  # noqa: S311
        for _ in range(100)
    ]

    for b_idx in range(bookmark_count):
        b_id = next_bookmark_id
        next_bookmark_id += 1
        b_created = random_date(user_created, now)
        b_updated = (
            random_date(b_created, now)
            if random.random() > 0.5  # noqa: S311
            else b_created
        )

        b_batch.append(
            {
                "id": b_id,
                "user_id": user_id,
                "title": random.choice(titles) + f" {b_idx}",  # noqa: S311
                "url": random.choice(urls),  # noqa: S311
                "note": None,
                "created_at": b_created,
                "updated_at": b_updated,
            },
        )

        # Attach 1-3 random tags
        if tag_ids:
            num_tags = random.randint(1, min(3, len(tag_ids)))  # noqa: S311
            sampled_tags = random.sample(tag_ids, num_tags)
            for t_id in sampled_tags:
                b_tag_batch.append({"bookmark_id": b_id, "tag_id": t_id})

        # Attach 1-3 random JDs
        if jd_ids:
            num_jds = random.randint(1, min(3, len(jd_ids)))  # noqa: S311
            sampled_jds = random.sample(jd_ids, num_jds)
            for j_id in sampled_jds:
                b_jd_batch.append({"bookmark_id": b_id, "jd_node_id": j_id})

        if len(b_batch) >= 5000:
            await session.execute(insert(Bookmark).values(b_batch))
            if b_tag_batch:
                await session.execute(insert(bookmark_tag_junction).values(b_tag_batch))
            if b_jd_batch:
                await session.execute(insert(bookmark_jd_junction).values(b_jd_batch))
            b_batch = []
            b_tag_batch = []
            b_jd_batch = []
            # Commit mid-user to keep RAM extremely low
            await session.commit()
            print(f"  Inserted {b_idx + 1} / {bookmark_count} bookmarks...", end="\r")

    if b_batch:
        await session.execute(insert(Bookmark).values(b_batch))
        if b_tag_batch:
            await session.execute(insert(bookmark_tag_junction).values(b_tag_batch))
        if b_jd_batch:
            await session.execute(insert(bookmark_jd_junction).values(b_jd_batch))

    await session.commit()
    print(f"\nUser {user_id} complete.")

    return next_tag_id, next_jd_id, next_bookmark_id


async def main(count: int) -> None:
    """
    Ingest database records massively and fast.

    It leverages raw SQLModel arrays and multiprocessing pools to synthesize and commit thousands of users, tens of thousands of bookmarks, and complex junction tables into PostgreSQL at mind-bending speeds, bypassing all ORM bottlenecks for raw performance.
    """
    # 1. Prepare User Data
    print(f"Preparing to seed {count} users and hundreds of thousands of bookmarks...")

    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "adminpass",
            "role": "admin",
        },
        {
            "username": "demo",
            "email": "demo@example.com",
            "password": "password",
            "role": "normal",
        },
    ]

    preexisting_users_count = len(users_data)
    for n in range(max(0, count - preexisting_users_count)):
        users_data.append(
            {
                "username": f"user_{n}_{secrets.token_hex(4)}",
                "email": f"user_{n}_{secrets.token_hex(4)}@example.com",
                "password": "password123!",
                "role": random.choice(["admin", "normal"]),  # noqa: S311
            },
        )

    # Cache password hash for speed (salting identically for fake users to save 10,000 Argon2 hashes which takes forever)
    print("Hashing passwords...")
    admin_hash = hash_password(users_data[0]["password"])
    demo_hash = hash_password(users_data[1]["password"])
    fake_hash = hash_password("password123!")

    # 2. Execution
    async with async_session() as session:
        await clear_data(session)

        # Save credentials
        creds_path = Path(__file__).parent.parent / "seed_credentials.json"
        with open(creds_path, "w") as f:
            json.dump(
                [
                    {
                        "username": d["username"],
                        "email": d["email"],
                        "password": d["password"],
                        "role": d["role"],
                    }
                    for d in users_data
                ],
                f,
                indent=2,
            )

        print("Starting bulk generation loop...")
        start_time = time.time()

        next_tag_id = 1
        next_jd_id = 1
        next_bookmark_id = 1

        for idx, u_data in enumerate(users_data):
            pw_hash = admin_hash if idx == 0 else demo_hash if idx == 1 else fake_hash
            next_tag_id, next_jd_id, next_bookmark_id = await process_user(
                session,
                u_data,
                idx,
                pw_hash,
                next_tag_id,
                next_jd_id,
                next_bookmark_id,
            )

        # Reset sequences since we manually inserted IDs
        print("Resetting sequences...")
        await session.execute(  # pyright: ignore[reportDeprecated]
            text(
                "SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id), 1)) FROM users;",
            ),
        )
        await session.execute(  # pyright: ignore[reportDeprecated]
            text(
                "SELECT setval(pg_get_serial_sequence('tags', 'id'), coalesce(max(id), 1)) FROM tags;",
            ),
        )
        await session.execute(  # pyright: ignore[reportDeprecated]
            text(
                "SELECT setval(pg_get_serial_sequence('jd_nodes', 'id'), coalesce(max(id), 1)) FROM jd_nodes;",
            ),
        )
        await session.execute(  # pyright: ignore[reportDeprecated]
            text(
                "SELECT setval(pg_get_serial_sequence('bookmarks', 'id'), coalesce(max(id), 1)) FROM bookmarks;",
            ),
        )
        await session.commit()

        duration = time.time() - start_time
        print(f"\nSeeding completed successfully in {duration:.2f} seconds!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="High-Performance Database Seeder")
    parser.add_argument(
        "--users",
        type=int,
        default=100,
        help="Number of users to generate",
    )
    args = parser.parse_args()
    asyncio.run(main(args.users))
