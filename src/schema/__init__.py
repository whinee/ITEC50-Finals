import datetime
from typing import Annotated, Literal

import sqlalchemy as sa
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlmodel import Column, Field, Relationship, SQLModel


class AllPhone(PhoneNumber):
    default_region_code = "PH"
    supported_regions: list[str] = []  # noqa: RUF012
    phone_format = "INTERNATIONAL"


class BaseUsers(SQLModel, table=False):
    username: str = Field(max_length=32, unique=True)
    email: EmailStr = Field(unique=True)
    contact_number: AllPhone | None = Field(default=None, unique=True)
    password: str


class User(BaseUsers, table=True):
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
    __tablename__ = "bookmark_jd_junction"  # type: ignore[assignment]
    bookmark_id: int = Field(foreign_key="bookmarks.id", primary_key=True)
    jd_node_id: int = Field(foreign_key="jd_nodes.id", primary_key=True)


class JDNode(SQLModel, table=True):
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
    __tablename__ = "bookmark_tag_junction"  # type: ignore[assignment]
    bookmark_id: int = Field(foreign_key="bookmarks.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)


class Bookmark(SQLModel, table=True):
    __tablename__ = "bookmarks"  # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str | None = Field(default=None, max_length=256)
    url: str
    note: str | None = None
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
    __tablename__ = "tags"  # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=32)
    color: str = Field(max_length=16)
    note: str | None = None
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
