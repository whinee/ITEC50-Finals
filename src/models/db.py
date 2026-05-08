import datetime

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users" # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=32, unique=True)
    email: str = Field(max_length=254, unique=True)
    password: str
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    bookmarks: list["Bookmark"] = Relationship(back_populates="user")
    tags: list["Tag"] = Relationship(back_populates="user")


class JDNode(SQLModel, table=True):
    __tablename__ = "jd_nodes" # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    code: str = Field(max_length=256)
    parent_id: int | None = Field(default=None, foreign_key="jd_nodes.id")

    bookmarks: list["Bookmark"] = Relationship(back_populates="jd_node")


class BookmarkTagJunction(SQLModel, table=True):
    __tablename__ = "bookmark_tag_junction" # type: ignore[assignment]
    bookmark_id: int = Field(foreign_key="bookmarks.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)


class Bookmark(SQLModel, table=True):
    __tablename__ = "bookmarks" # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    jd_id: int | None = Field(default=None, foreign_key="jd_nodes.id")
    title: str | None = Field(default=None, max_length=256)
    url: str
    note: str | None = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    user: User | None = Relationship(back_populates="bookmarks")
    jd_node: JDNode | None = Relationship(back_populates="bookmarks")
    tags: list["Tag"] = Relationship(back_populates="bookmarks", link_model=BookmarkTagJunction)


class Tag(SQLModel, table=True):
    __tablename__ = "tags" # type: ignore[assignment]
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str = Field(max_length=32)
    color: str = Field(max_length=16)
    note: str | None = None
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    user: User | None = Relationship(back_populates="tags")
    bookmarks: list[Bookmark] = Relationship(back_populates="tags", link_model=BookmarkTagJunction)
