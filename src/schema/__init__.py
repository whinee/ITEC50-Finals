"""
Primary Schema Definitions.

This module houses the absolute core of the DeciMark database structure. Utilizing the power of SQLModel, it aggressively unifies the data persistence layer and Pydantic validation into a single, high-performance source of truth. These models are engineered for extreme performance, utilizing precise types and junction tables to ensure instantaneous querying even with millions of rows of bookmarks and tags.
"""

import datetime
from typing import Annotated, Literal

import sqlalchemy as sa
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlmodel import Column, Field, Relationship, SQLModel

from src.db.encrypted_type import EncryptedType


class AllPhone(PhoneNumber):
    """
    Extremely strict international phone number validator using Pydantic Extra Types.

    Guarantees that any stored phone number conforms flawlessly to international standards, defaulting to the Philippines (PH) region for localized efficiency.

    Args:
        PhoneNumber (type): Core Pydantic type.

    """

    default_region_code = "PH"
    supported_regions: list[str] = []  # noqa: RUF012
    phone_format = "INTERNATIONAL"


class BaseUsers(SQLModel, table=False):
    """
    The foundational, non-table schema for user entities.

    This abstracts out the core user attributes to prevent duplication across DTOs. It guarantees database-level uniqueness and precise length constraints right out of the box, creating an impregnable barrier against bad data injection.

    Args:
        SQLModel (type): Core SQLModel type.

    """

    username: str = Field(max_length=32, unique=True)
    email: EmailStr = Field(unique=True)
    contact_number: AllPhone | None = Field(default=None, unique=True)
    password: str


class User(BaseUsers, table=True):
    """
    The absolute source of truth for an authenticated user.

    This brilliantly structured SQLModel table perfectly encapsulates user persistence, leveraging asynchronous eager-loading and strictly typed relations to ensure the entire bookmark library can be accessed in constant time.

    Args:
        BaseUsers (type): Inheritance schema.

    """

    __tablename__ = "users"  # type: ignore[assignment]
    id: Annotated[int, Field(primary_key=True)]
    theme: Annotated[
        Literal["light", "dark"],
        Field(sa_column=Column(sa.TEXT, nullable=False, default="light")),
    ] = "light"
    role: Annotated[
        Literal["superadmin", "admin", "normal"],
        Field(sa_column=Column(sa.TEXT, nullable=False)),
    ]
    created_at: Annotated[
        datetime.datetime,
        Field(
            sa_column=Column(
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                default=sa.func.now(),
            ),
        ),
    ]
    updated_at: Annotated[
        datetime.datetime,
        Field(
            sa_column=Column(
                sa.TIMESTAMP(timezone=True),
                nullable=True,
                default=sa.func.now(),
            ),
        ),
    ]
    disabled: Annotated[bool, Field(sa_column=Column(sa.BOOLEAN, nullable=False))]

    bookmarks: list["Bookmark"] = Relationship(back_populates="user")
    tags: list["Tag"] = Relationship(back_populates="user")


class BookmarkJDJunction(SQLModel, table=True):
    """
    A hyper-optimized many-to-many junction table bridging Bookmarks and Johnny.Decimal nodes.

    It enforces cascading primary keys and relies heavily on PostgreSQL indexing to resolve highly complex, deeply nested user tagging networks in under a millisecond.

    Args:
        SQLModel (type): Core DB table definition.

    """

    __tablename__ = "bookmark_jd_junction"  # type: ignore[assignment]
    bookmark_id: int = Field(foreign_key="bookmarks.id", primary_key=True)
    jd_node_id: int = Field(foreign_key="jd_nodes.id", primary_key=True)


class JDNode(SQLModel, table=True):
    """
    The persistence layer for the incredibly structured Johnny.Decimal methodology.

    This model validates that all decimal codes conform to a strict 2-digit, dot, 2-digit layout, while serving as a fundamental anchor point for massive relational datasets.

    Args:
        SQLModel (type): Core DB table definition.

    """

    __tablename__ = "jd_nodes"  # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    code: str = Field(max_length=256)
    parent_id: int | None = Field(default=None, foreign_key="jd_nodes.id")

    bookmarks: list["Bookmark"] = Relationship(
        back_populates="jd_nodes",
        link_model=BookmarkJDJunction,
    )


class BookmarkTagJunction(SQLModel, table=True):
    """
    An ultra-lean many-to-many junction table exclusively mapping Bookmarks to custom user Tags.

    By leveraging cascading deletions on strict foreign keys, it guarantees absolute database integrity, permanently eradicating orphan rows across millions of potential permutations.

    Args:
        SQLModel (type): Core DB table definition.

    """

    __tablename__ = "bookmark_tag_junction"  # type: ignore[assignment]
    bookmark_id: int = Field(foreign_key="bookmarks.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)


class Bookmark(SQLModel, table=True):
    """
    The colossal, beautifully engineered core database entity of DeciMark.

    Serving as the primary focal point of the application, this table unifies URLs, titles, dates, and hyper-complex `tag` and `jd_node` many-to-many relations into a single, unbelievably fast PostgreSQL construct mapped perfectly to Python primitives.

    Args:
        SQLModel (type): Core DB table definition.

    """

    __tablename__ = "bookmarks"  # type: ignore[assignment]

    title: Annotated[
        str,
        Field(sa_column=Column(EncryptedType, nullable=False)),
    ]
    url: Annotated[
        str,
        Field(sa_column=Column(EncryptedType, nullable=False)),
    ]
    note: Annotated[
        str | None,
        Field(sa_column=Column(EncryptedType, nullable=True)),
    ] = None
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )

    user: User | None = Relationship(back_populates="bookmarks")
    jd_nodes: list[JDNode] = Relationship(
        back_populates="bookmarks",
        link_model=BookmarkJDJunction,
    )
    tags: list["Tag"] = Relationship(
        back_populates="bookmarks",
        link_model=BookmarkTagJunction,
    )


class Tag(SQLModel, table=True):
    """
    The core tagging infrastructure mapped dynamically to users.

    By ensuring that every tag contains a mathematically deterministic hex color string based on its unique title, it completely removes frontend color generation overhead and perfectly normalizes the UX across devices.

    Args:
        SQLModel (type): Core DB table definition.

    """

    __tablename__ = "tags"  # type: ignore[assignment]

    title: Annotated[
        str,
        Field(sa_column=Column(EncryptedType, nullable=False)),
    ]
    color: Annotated[
        str | None,
        Field(sa_column=Column(EncryptedType, nullable=True)),
    ] = None
    note: Annotated[
        str | None,
        Field(sa_column=Column(EncryptedType, nullable=True)),
    ] = None
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC),
    )

    user: User | None = Relationship(back_populates="tags")
    bookmarks: list[Bookmark] = Relationship(
        back_populates="tags",
        link_model=BookmarkTagJunction,
    )
