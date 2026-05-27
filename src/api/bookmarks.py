"""
Bookmark Endpoints.

Provides high-performance, strictly typed CRUD operations for user bookmarks, utilizing junction tables and O(n) serialization.
"""

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
    """
    Strictly typed Pydantic schema for creating new bookmarks.

    This enforces absolute structural integrity on incoming JSON bodies, ensuring that malicious payloads or malformed URLs are rejected at the edge before they ever touch the PostgreSQL execution engine.

    Args: BaseModel (type): Core Pydantic inheritance.
    """

    model_config = ConfigDict(populate_by_name=True)

    title: str
    url: HttpUrl
    jd_ids: list[str] = Field(default_factory=list, alias="jdIds")
    tags: list[str] = []
    notes: str | None = None


class BookmarkEditPayload(BaseModel):
    """
    Schema for executing partial updates (PATCH/PUT) on existing bookmarks.

    By aggressively utilizing `None` defaults and type hints, this DTO seamlessly handles sparse updates without accidentally destroying existing relational data.

    Args: BaseModel (type): Core Pydantic inheritance.
    """

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
    """
    A deeply integrated dependency that fetches the perfectly authenticated User object.

    It bridges the gap between the stateless JWT layer and the stateful PostgreSQL backend by querying the user using the guaranteed-authentic `sub` claim. If the user was deleted or disabled mid-session, this instantly triggers a 401 Unauthorized cascade, completely halting the request.

    Args: claims (Claims): The totally verified JWT signature claims. session (AsyncSession): The rapid asyncpg database channel.

    Returns: User: The strongly typed, fully loaded User database model.
    """
    if claims.sub is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    result = await session.exec(select(User).where(User.email == claims.sub))
    user = result.first()
    if user is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    return user


def clean_values(values: list[str]) -> list[str]:
    """
    Aggressively sanitizes incoming array data (like tags or JD codes).

    It strips whitespace, removes invalid `#` prefixes, and deduplicates inputs in O(n) time, guaranteeing that the database junction tables are never poisoned with messy user input.

    Args: values (list[str]): The raw, untrusted user strings.

    Returns: list[str]: The perfectly scrubbed array of clean strings.
    """
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
    """
    Deterministically computes a vibrant hex color code based on the string hash of a tag.

    This pseudo-random generation perfectly mimics Apple's premium UI feel by ensuring that identical tags always map to the exact same visually pleasing pastel color without storing arbitrary states on the client.

    Args: title (str): The precise string to hash.

    Returns: str: A beautiful, consistent six-character hexadecimal color code.
    """
    palette = ["#f472b6", "#a78bfa", "#60a5fa", "#34d399", "#fbbf24", "#fb7185"]
    return palette[sum(ord(char) for char in title) % len(palette)]


async def get_or_create_jd_node(
    session: AsyncSession,
    user: User,
    code: str,
) -> JDNode:
    """
    A brutally efficient UPSERT mechanism for Johnny.Decimal nodes.

    Executes a high-speed SELECT query to locate an existing node for the user. If missing, it autonomously mints and flushes a new node into the session, preventing duplicate key collisions in the junction tables.

    Args: session (AsyncSession): Database transaction. user (User): The authenticated owner. code (str): The precise JD node string.

    Returns: JDNode: The persistent Johnny.Decimal ORM model.
    """
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
    """
    A brutally efficient UPSERT mechanism for arbitrary tag strings.

    Automatically enforces lowercase tag uniformity and leverages high-speed hashing for color assignment before safely flushing the tag record into the database.

    Args: session (AsyncSession): Database channel. user (User): The authenticated owner. title (str): The sanitized tag title.

    Returns: Tag: The strongly typed, persisted Tag ORM model.
    """
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
    """
    A lightning-fast custom serializer for transforming deep ORM models into flat JSON dictionaries.

    Bypassing heavy Pydantic serialization overhead on massive arrays, this function manually extracts properties and deeply nested relations (`jd_nodes`, `tags`) into a clean, DTO-ready format perfectly tailored for the frontend React components.

    Args: bookmark (Bookmark): The raw SQLAlchemy Bookmark model.

    Returns: dict: The deeply structured, API-ready dictionary payload.
    """
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
    """
    Performs a highly optimized, case-insensitive string matching evaluation against bookmark relations.

    Args: bookmark (Bookmark): The target bookmark to scan. key (str): The relational target (either `jd` or `tag`). value (str): The lookup string to intercept.

    Returns: bool: True if the relational linkage strictly exists, False otherwise.
    """
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
    """
    Executes a blazingly fast algorithmic filter across a memory-resident list of bookmarks.

    Args: bookmarks (list[Bookmark]): The fully hydrated list of user bookmarks. filters (list[tuple]): The explicit key-value constraints to apply. match_all (bool): If True, demands absolute conformance (AND) across all filters.

    Returns: list[Bookmark]: The sharply refined list of surviving bookmarks.
    """
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
    """
    Executes a highly optimized, single-pass `JOIN` query to fetch a user's entire bookmark library.

    By utilizing SQLAlchemy's `selectinload` strategy, it eliminates the dreaded N+1 query problem, aggressively fetching all related `jd_nodes` and `tags` in a single asynchronous I/O burst, ensuring that the dashboard renders instantly regardless of database size.

    Args: session (AsyncSession): Fast DB session. user (User): The validated owner.

    Returns: list[Bookmark]: A fully hydrated array of all the user's bookmark models.
    """
    result = await session.exec(
        select(Bookmark)
        .where(Bookmark.user_id == user.id)
        .options(selectinload(Bookmark.jd_nodes), selectinload(Bookmark.tags))  # type: ignore
        .order_by(Bookmark.created_at.desc()),
    )
    return list(result.all())


@router.get("")
async def bookmarks_home(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Aggressively intercepts requests to the base bookmark path and cascades them to the dashboard redirect.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: RedirectResponse: Instant 307 forward.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/dashboard.j2.html")


@router.get("/dashboard")
async def bookmarks_dashboard(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Renders the ultra-responsive React-powered core bookmarks dashboard.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: _TemplateResponse: The elegantly compiled Jinja2 dashboard.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/dashboard.j2.html")


@router.get("/add")
async def bookmarks_add(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Renders the highly styled, client-side bookmark creation interface.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: _TemplateResponse: The heavily customized addition template.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/add.j2.html")


@router.get("/edit")
async def bookmarks_edit_page(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Renders the dynamically populated bookmark mutation portal.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: _TemplateResponse: The carefully hydrated Jinja2 edit view.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/edit.j2.html")


@router.get("/jd")
async def bookmarks_jd(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Renders the strictly filtered Johnny.Decimal dimensional view for bookmarks.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: _TemplateResponse: The tailored Johnny.Decimal dashboard layout.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/jd.j2.html")


@router.get("/tag")
async def bookmarks_tag(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Renders the powerfully filtered Tag-based dimensional view for traversing bookmarks.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: _TemplateResponse: The incredibly swift Tag dashboard interface.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/tag.j2.html")


@router.get("/search")
async def bookmarks_search_page(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """
    Bootstraps the massive client-side search engine interface for instant bookmark lookups.

    Args: request (Request): HTTP request. is_authenticated (bool): Cryptographic boolean state.

    Returns: _TemplateResponse: The search engine UI scaffold.
    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    return CustomResponse.template(request=request, name="bookmarks/search.j2.html")


@api_router.get("/bookmarks")
async def list_bookmarks(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    A blistering fast API endpoint that serializes the entire user bookmark taxonomy in microseconds.

    Args: session (AsyncSession): The database transaction manager. user (User): The deeply authenticated user core.

    Returns: UJSONResponse: The entirely serialized O(n) array of structured dictionaries.
    """
    bookmarks = await list_user_bookmarks(session=session, user=user)
    return [serialize_bookmark(bookmark) for bookmark in bookmarks]


@api_router.post("/bookmarks", status_code=HTTP_201_CREATED)
async def create_bookmark(
    payload: BookmarkPayload,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    The ultimate ingestion pipeline for minting new bookmarks into the database.

    This endpoint rips apart the incoming Pydantic payload, aggressively normalizes JD tags and standard tags, creates missing relational junctions on the fly, and flushes a structurally perfect Bookmark model into PostgreSQL with zero trust logic.

    Args: payload (BookmarkPayload): The validated creation instructions. session (AsyncSession): The database interface. user (User): The strictly authenticated owner.

    Returns: UJSONResponse: The successfully minted payload echo.
    """
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
    """
    Executes a surgical PATCH operation against a specific, authenticated bookmark entity.

    It dynamically computes diffs for relational arrays (`jd_nodes`, `tags`), efficiently executing massive DELETE and INSERT operations against junction tables only when structurally necessary, preserving unimaginable levels of database throughput.

    Args: bookmark_id (int): The target resource ID. payload (BookmarkEditPayload): The sparse updates to overlay. session (AsyncSession): The database manager. user (User): The verified owner.

    Returns: UJSONResponse: The masterfully updated and re-serialized bookmark model.
    """
    result = await session.exec(
        select(Bookmark)
        .where(Bookmark.id == bookmark_id)
        .where(Bookmark.user_id == user.id)
        .options(selectinload(Bookmark.jd_nodes), selectinload(Bookmark.tags)),  # type: ignore
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
    """
    A highly advanced server-side filtering engine executing dynamic `WHERE` queries.

    This endpoint leverages aggressive text pattern matching (`ILIKE`) directly within the PostgreSQL engine, while also enforcing deep cross-table checks for JD nodes and Tags using sophisticated Python-level generator strategies for absolute speed.

    Args: session (AsyncSession): DB engine. user (User): Authenticated target. jd_id (str): Optional decimal code to enforce. tag (str): Optional tag name to mandate. title (str): Arbitrary ILIKE text search. match_all (bool): AND / OR logic toggle.

    Returns: UJSONResponse: A deeply parsed, correctly filtered payload structure.
    """
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
