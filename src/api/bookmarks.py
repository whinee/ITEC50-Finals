import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from src.db.main import get_session
from src.middlewares.auth import check_encrypted_cookie_auth, check_page_auth
from src.schema import Bookmark, JDNode, Tag, User
from src.security.jwt_service import Claims
from src.utils.custom_response import CustomResponse

router = APIRouter()
api_router = APIRouter()


class BookmarkPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    url: HttpUrl
    jd_ids: list[str] = Field(default_factory=list, alias="jdIds")
    tags: list[str] = []
    notes: str | None = None


class BookmarkEditPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    url: HttpUrl | None = None
    jd_ids: list[str] | None = Field(default=None, alias="jdIds")
    tags: list[str] | None = None
    notes: str | None = None


async def get_current_user(
    claims: Annotated[Claims, Depends(check_encrypted_cookie_auth)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if claims.sub is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    result = await session.exec(select(User).where(User.email == claims.sub))
    user = result.first()
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    return user


def clean_values(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        item = value.strip()
        if item.startswith("#"):
            item = item[1:]
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            cleaned.append(item)
    return cleaned


def tag_color(title: str) -> str:
    palette = ["#f472b6", "#a78bfa", "#60a5fa", "#34d399", "#fbbf24", "#fb7185"]
    return palette[sum(ord(char) for char in title) % len(palette)]


async def get_or_create_jd_node(
    session: AsyncSession,
    user: User,
    code: str,
) -> JDNode:
    result = await session.exec(
        select(JDNode).where(JDNode.user_id == user.id, JDNode.code == code),
    )
    jd_node = result.first()
    if jd_node is not None:
        return jd_node

    jd_node = JDNode(user_id=user.id, code=code)
    session.add(jd_node)
    await session.flush()
    return jd_node


async def get_or_create_tag(session: AsyncSession, user: User, title: str) -> Tag:
    result = await session.exec(
        select(Tag).where(Tag.user_id == user.id, Tag.title == title),
    )
    tag = result.first()
    if tag is not None:
        return tag

    tag = Tag(user_id=user.id, title=title, color=tag_color(title))
    session.add(tag)
    await session.flush()
    return tag


def serialize_bookmark(bookmark: Bookmark) -> dict:
    jd_ids = [node.code for node in bookmark.jd_nodes]
    return {
        "id": bookmark.id,
        "title": bookmark.title or bookmark.url,
        "url": bookmark.url,
        "jdIds": jd_ids,
        "tags": [tag.title for tag in bookmark.tags],
        "notes": bookmark.note,
        "createdAt": bookmark.created_at.isoformat(),
        "updatedAt": bookmark.updated_at.isoformat(),
    }


def bookmark_matches(bookmark: Bookmark, key: str, value: str) -> bool:
    if key == "jd":
        return any(value in node.code.lower() for node in bookmark.jd_nodes)
    if key == "tag":
        return any(value in item.title.lower() for item in bookmark.tags)
    if key == "title":
        return value in (bookmark.title or "").lower()
    return False


def filter_bookmarks(
    bookmarks: list[Bookmark],
    filters: list[tuple[str, str]],
    match_all: bool,
) -> list[Bookmark]:
    active = [(key, value) for key, value in filters if value]
    if not active:
        return bookmarks

    found = []
    for bookmark in bookmarks:
        checks = [
            bookmark_matches(bookmark=bookmark, key=key, value=value)
            for key, value in active
        ]
        if all(checks) if match_all else any(checks):
            found.append(bookmark)

    return found


async def list_user_bookmarks(session: AsyncSession, user: User) -> list[Bookmark]:
    result = await session.exec(
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .options(selectinload(Bookmark.jd_nodes), selectinload(Bookmark.tags))
        .order_by(Bookmark.created_at.desc()),
    )
    return list(result.all())


@router.get("")
async def bookmarks_home(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/dashboard.j2.html")


@router.get("/dashboard")
async def bookmarks_dashboard(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/dashboard.j2.html")


@router.get("/add")
async def bookmarks_add(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/add.j2.html")


@router.get("/edit")
async def bookmarks_edit_page(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/edit.j2.html")


@router.get("/jd")
async def bookmarks_jd(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/jd.j2.html")


@router.get("/tag")
async def bookmarks_tag(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/tag.j2.html")


@router.get("/search")
async def bookmarks_search_page(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/search.j2.html")


@api_router.get("/bookmarks")
async def list_bookmarks(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    bookmarks = await list_user_bookmarks(session=session, user=user)
    return [serialize_bookmark(bookmark) for bookmark in bookmarks]


@api_router.post("/bookmarks", status_code=HTTP_201_CREATED)
async def create_bookmark(
    payload: BookmarkPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    jd_nodes = [
        await get_or_create_jd_node(session=session, user=user, code=code)
        for code in clean_values(payload.jd_ids)
    ]
    tags = [
        await get_or_create_tag(session=session, user=user, title=title)
        for title in clean_values(payload.tags)
    ]

    now = datetime.datetime.now(datetime.UTC)
    bookmark = Bookmark(
        user_id=user.id,
        title=payload.title.strip(),
        url=str(payload.url),
        note=payload.notes,
        created_at=now,
        updated_at=now,
        jd_nodes=jd_nodes,
        tags=tags,
    )
    session.add(bookmark)
    await session.commit()
    await session.refresh(bookmark)

    bookmarks = await list_user_bookmarks(session=session, user=user)
    created = next(item for item in bookmarks if item.id == bookmark.id)
    return serialize_bookmark(created)


@api_router.patch("/bookmarks/{bookmark_id}")
async def update_bookmark(  # noqa: C901
    bookmark_id: int,
    payload: BookmarkEditPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    result = await session.exec(
        select(Bookmark)
        .where(Bookmark.id == bookmark_id)
        .where(Bookmark.user_id == user.id)
        .options(selectinload(Bookmark.jd_nodes), selectinload(Bookmark.tags)),
    )
    bookmark = result.first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    if payload.title is not None:
        bookmark.title = payload.title.strip()
    if payload.url is not None:
        bookmark.url = str(payload.url)
    if payload.notes is not None:
        bookmark.note = payload.notes
    if payload.jd_ids is not None:
        jd_nodes = [
            await get_or_create_jd_node(session=session, user=user, code=code)
            for code in clean_values(payload.jd_ids)
        ]
        bookmark.jd_nodes = jd_nodes
    if payload.tags is not None:
        tags = [
            await get_or_create_tag(session=session, user=user, title=title)
            for title in clean_values(payload.tags)
        ]
        bookmark.tags = tags

    bookmark.updated_at = datetime.datetime.now(datetime.UTC)
    session.add(bookmark)
    await session.commit()
    await session.refresh(bookmark)

    bookmarks = await list_user_bookmarks(session=session, user=user)
    updated = next(item for item in bookmarks if item.id == bookmark.id)
    return serialize_bookmark(updated)


@api_router.get("/bookmarks/search")
async def search_bookmarks(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    jd_id: Annotated[str | None, Query(alias="jdId")] = None,
    tag: str | None = None,
    title: str | None = None,
    match_all: Annotated[bool, Query(alias="matchAll")] = True,
):
    bookmarks = await list_user_bookmarks(session=session, user=user)
    filters = [
        ("jd", jd_id.strip().lower() if jd_id else ""),
        ("tag", tag.strip().lower() if tag else ""),
        ("title", title.strip().lower() if title else ""),
    ]
    found = filter_bookmarks(
        bookmarks=bookmarks,
        filters=filters,
        match_all=match_all,
    )

    return [serialize_bookmark(bookmark) for bookmark in found]
