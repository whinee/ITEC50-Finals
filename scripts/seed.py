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
from sqlmodel import delete

from src.db.main import async_session
from src.schema import (
    Bookmark,
    BookmarkJDJunction,
    BookmarkTagJunction,
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
    await session.exec(delete(BookmarkJDJunction))
    await session.exec(delete(BookmarkTagJunction))
    await session.exec(delete(Bookmark))
    await session.exec(delete(JDNode))
    await session.exec(delete(Tag))
    await session.exec(delete(User))
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

    # Generate additional users up to 'count'
    for _ in range(max(0, count - len(users_data))):
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
        )
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


async def create_tags(session, users: list[User]) -> dict[int, list[Tag]]:
    print("Creating tags...")
    tag_names = [
        "#tech",
        "#news",
        "#recipes",
        "#programming",
        "#funny",
        "#books",
        "#todo",
    ]
    user_tags = {}

    for user in users:
        tags = []
        for name in tag_names:
            tag = Tag(
                user_id=user.id,
                title=name,
                color=fake.hex_color(),
                note=fake.sentence(),
            )
            session.add(tag)
            tags.append(tag)
        user_tags[user.id] = tags

    await session.commit()
    return user_tags


async def create_jd_nodes(session, users: list[User]) -> dict[int, list[JDNode]]:
    print("Creating JD nodes...")
    jd_codes = ["10-19 Technology", "11.01 Web Dev", "20-29 Personal", "21.05 Recipes"]
    user_nodes = {}

    for user in users:
        nodes = []
        for code in jd_codes:
            node = JDNode(
                user_id=user.id,
                code=code,
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
    count_per_user: int = 30,
) -> None:
    print("Creating bookmarks...")
    for user in users:
        tags_for_user = user_tags[user.id]
        nodes_for_user = user_nodes[user.id]

        for _ in range(count_per_user):
            bookmark = Bookmark(
                user_id=user.id,
                title=fake.sentence(nb_words=6),
                url=fake.url(),
                note=(
                    fake.paragraph(nb_sentences=3)
                    if secrets.SystemRandom().random() > 0.5
                    else None
                ),
            )

            # Select 1-3 random tags
            selected_tags = secrets.SystemRandom().sample(
                tags_for_user,
                k=secrets.SystemRandom().randint(1, 3),
            )
            bookmark.tags = selected_tags

            # Select 1 random JD node sometimes
            if secrets.SystemRandom().random() > 0.3:
                bookmark.jd_nodes = [secrets.SystemRandom().choice(nodes_for_user)]

            session.add(bookmark)

    await session.commit()


async def main() -> None:
    async with async_session() as session:
        await clear_data(session)
        users = await create_users(session, count=1000)
        user_tags = await create_tags(session, users)
        user_nodes = await create_jd_nodes(session, users)
        await create_bookmarks(
            session,
            users,
            user_tags,
            user_nodes,
            count_per_user=100,
        )
        print("Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
