import asyncio
import json
import os
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure the root directory is on the path so we can import 'src'
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from faker import Faker

from src.db.main import async_session
from src.schema import (
    Bookmark,
    JDNode,
    Tag,
    User,
)

fake = Faker()


def hash_password(password: str) -> str:
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
    print("Clearing existing data...")
    from sqlalchemy import text

    await session.execute(
        text(
            "TRUNCATE TABLE bookmark_jd_junction, bookmark_tag_junction, bookmarks, jd_nodes, tags, users CASCADE",
        ),
    )
    await session.commit()


async def create_users(session, count: int = 1000) -> list[User]:
    print(f"Creating {count} demo users...")
    now = datetime.now(UTC)
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

    # Generate additional users up to 'count'
    for n in range(max(0, count - preexisting_users_count)):
        print("User #", preexisting_users_count + n, sep="")
        users_data.append(
            {
                "username": fake.unique.user_name()[:32],
                "email": fake.unique.email(),
                "password": fake.password(
                    length=12,
                    special_chars=True,
                    digits=True,
                    upper_case=True,
                    lower_case=True,
                ),
                "role": secrets.SystemRandom().choice(["admin", "normal"]),
            },
        )

    created_users = []
    credentials = []

    for data in users_data:
        user = User(
            username=data["username"],
            email=data["email"],
            password=hash_password(data["password"]),
            role=data["role"],
            created_at=now,
            updated_at=now,
            disabled=False,
        )  # type: ignore
        session.add(user)
        created_users.append(user)
        credentials.append(
            {
                "username": data["username"],
                "email": data["email"],
                "password": data["password"],
                "role": data["role"],
            },
        )

    await session.commit()

    creds_path = Path(__file__).parent.parent / "seed_credentials.json"
    with open(creds_path, "w") as f:
        json.dump(credentials, f, indent=2)
    print(f"Saved {len(credentials)} user credentials to {creds_path}")

    return created_users


async def create_tags(
    session,
    users: list[User],
    user_tag_counts: dict[int, int],
) -> dict[int, list[Tag]]:
    print("Creating tags...")
    user_tags = {}

    for user in users:
        tags = []
        for _ in range(user_tag_counts.get(user.id, 5)):
            name = fake.unique.word()
            created = fake.date_time_between(
                start_date=user.created_at,
                end_date="now",
                tzinfo=UTC,
            )
            updated = (
                fake.date_time_between(start_date=created, end_date="now", tzinfo=UTC)
                if secrets.SystemRandom().random() > 0.5
                else created
            )
            tag = Tag(
                user_id=user.id,
                title=name[:32],  # max length constraint
                color=fake.hex_color(),
                note=fake.sentence(),
                created_at=created,
                updated_at=updated,
            )
            session.add(tag)
            tags.append(tag)
        fake.unique.clear()
        user_tags[user.id] = tags

    await session.commit()
    return user_tags


def generate_jd_code() -> str:
    part1 = "".join(
        str(secrets.SystemRandom().randint(0, 9))
        for _ in range(secrets.SystemRandom().randint(2, 5))
    )
    part2 = "".join(
        str(secrets.SystemRandom().randint(0, 9))
        for _ in range(secrets.SystemRandom().randint(2, 5))
    )
    code = f"{part1}.{part2}"
    if secrets.SystemRandom().random() > 0.5:
        code += f"+{fake.word()}"
    return code


async def create_jd_nodes(session, users: list[User]) -> dict[int, list[JDNode]]:
    print("Creating JD nodes...")
    user_nodes = {}

    for user in users:
        nodes = []
        for _ in range(secrets.SystemRandom().randint(5, 10)):
            node = JDNode(
                user_id=user.id,
                code=generate_jd_code(),
            )
            session.add(node)
            nodes.append(node)
        user_nodes[user.id] = nodes

    await session.commit()
    return user_nodes


async def create_bookmarks(
    session,
    users: list[User],
    user_tags: dict[int, list[Tag]],
    user_nodes: dict[int, list[JDNode]],
    user_bookmark_counts: dict[int, int],
) -> None:
    print("Creating bookmarks...")
    for user in users:
        tags_for_user = user_tags[user.id]
        nodes_for_user = user_nodes[user.id]

        for _ in range(user_bookmark_counts.get(user.id, 30)):
            created = fake.date_time_between(
                start_date=user.created_at,
                end_date="now",
                tzinfo=UTC,
            )
            updated = (
                fake.date_time_between(start_date=created, end_date="now", tzinfo=UTC)
                if secrets.SystemRandom().random() > 0.5
                else created
            )
            bookmark = Bookmark(
                user_id=user.id,
                title=fake.sentence(nb_words=6),
                url=fake.url(),
                note=(
                    fake.paragraph(nb_sentences=3)
                    if secrets.SystemRandom().random() > 0.5
                    else None
                ),
                created_at=created,
                updated_at=updated,
            )

            if tags_for_user:
                k_tags = secrets.SystemRandom().randint(1, min(3, len(tags_for_user)))
                bookmark.tags = secrets.SystemRandom().sample(tags_for_user, k=k_tags)

            if nodes_for_user:
                k_nodes = secrets.SystemRandom().randint(1, min(3, len(nodes_for_user)))
                bookmark.jd_nodes = secrets.SystemRandom().sample(
                    nodes_for_user,
                    k=k_nodes,
                )

            session.add(bookmark)

    await session.commit()


async def main() -> None:
    async with async_session() as session:
        await clear_data(session)
        users = await create_users(session, count=10000)

        user_bookmark_counts = {
            user.id: secrets.SystemRandom().randint(30000, 100000) for user in users
        }
        user_tag_counts = {
            user_id: max(
                1,
                secrets.SystemRandom().randint(int(bc * 0.1), int(bc * 0.2)),
            )
            for user_id, bc in user_bookmark_counts.items()
        }

        user_tags = await create_tags(session, users, user_tag_counts)
        user_nodes = await create_jd_nodes(session, users)
        await create_bookmarks(
            session,
            users,
            user_tags,
            user_nodes,
            user_bookmark_counts,
        )
        print("Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
