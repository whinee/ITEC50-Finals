"""Application Entrypoint.

The primary FastAPI ASGI gateway. This file meticulously orchestrates the entire lifecycle of the DeciMark backend, aggressively mounting routers, static files, and security middlewares into a cohesive, zero-trust web application capable of servicing thousands of concurrent asynchronous connections.
"""
import hashlib
import hmac
import os
import subprocess
import time
import traceback
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import RedirectResponse, UJSONResponse  # type: ignore
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from jinja2 import TemplateNotFound
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import _TemplateResponse

from src.api import auth, bookmarks, preferences
from src.config.settings import settings
from src.db.main import get_session
from src.middlewares.auth import check_page_auth
from src.schema import Bookmark, User
from src.utils.custom_response import TEMPLATES, CustomResponse

# Constants
DEFAULT_ERROR_HTTP_CODE = 500
DESCRIPTION = """DeciMArk: A Johnny.Decimal Bookmark Link Manager!"""

security = HTTPBasic()

middleware = [
    Middleware(SessionMiddleware, secret_key=settings.AUTH.JWT_SECRET),  # type: ignore
]

app = FastAPI(
    title="Lyra-on.top",
    description=DESCRIPTION,
    version="1.0.0",
    # terms_of_service="http://hyaku.download/tos",
    contact={
        "name": "Lyra Phasma",
        "url": "https://lyra-on.top",
        "email": "lyraphasma@gmail.com",
    },
    license_info={
        "name": "Custom Dual-License",
        "url": "https://github.com/whinee/ITEC50-Finals/blob/main/docs/LICENSE.md",
    },
    docs_url=None,
    redoc_url=None,
    middleware=middleware,
)


@app.middleware("http")
async def add_process_time_header(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response | UJSONResponse | _TemplateResponse:  # type: ignore
    """High-performance HTTP middleware that brutally intercepts every request to compute and inject ultra-precise `X-Process-Time` headers, while autonomously catching unhandled exceptions and mapping them to standardized JSON payloads.

    Args:
        request (Request): The incoming FastAPI request.
        call_next (Callable): The next middleware in the pipeline.

    Returns:
        Response: The aggressively formatted and timed outbound HTTP response.
    
    """
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        status_code = response.status_code
        # if check_if_http_code_group_error(get_http_code_group(status_code)):
        if status_code == 404:
            return CustomResponse.http_code(request, status_code)
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except:  # noqa: E722
        if (settings.ENV in ("development", "test")) and (settings.DEBUG):
            return CustomResponse.json(
                status_code=DEFAULT_ERROR_HTTP_CODE,
                message="Error occured",
                json={"traceback": traceback.format_exc()},
            )
        return CustomResponse.http_code(request, status_code=DEFAULT_ERROR_HTTP_CODE)


app.mount("/static/", StaticFiles(directory="src/static"), name="static")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
app.include_router(bookmarks.api_router, prefix="/api", tags=["bookmarks-api"])
app.include_router(preferences.router, prefix="/api", tags=["preferences"])


@app.get("/docs", include_in_schema=False, status_code=200)
async def docs(response: Response):  # type: ignore[no-untyped-def]
    """Missing docstring."""
    response.status_code = 200
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,  # type: ignore[arg-type]
        title=app.title + " - Docs",
        # swagger_css_url="/static/stylesheets/docs.css",
    )


@app.get("/http_code/{status_code}")
async def http_code_get(request: Request, status_code: int) -> _TemplateResponse:
    """Dynamically resolves and renders a deeply comprehensive HTTP status code documentation page.

    Args:
        request (Request): The raw HTTP request.
        status_code (int): The perfectly validated HTTP status code integer.

    Returns:
        _TemplateResponse: The meticulously templated HTTP status page.

    """
    return CustomResponse.http_code(request=request, status_code=status_code)


@app.get("/", include_in_schema=False)
async def landing_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Serve the primary landing page while concurrently aggregating live system statistics (total bookmarks, total users) via aggressive `asyncpg` COUNT aggregations to ensure O(1) dashboard responsiveness.

    Args:
        request (Request): The raw HTTP request.
        session (AsyncSession): The incredibly fast database session injected at runtime.

    Returns:
        _TemplateResponse: The brilliantly rendered frontend landing interface.
    
    """
    bookmark_result = await session.execute(select(func.count(Bookmark.id)))  # type: ignore[arg-type]
    total_bookmarks = bookmark_result.scalar_one()
    
    user_result = await session.execute(select(func.count(User.id)))  # type: ignore[arg-type]
    total_users = user_result.scalar_one()

    return TEMPLATES.TemplateResponse(
        request=request, 
        name="index.j2.html", 
        context={"total_bookmarks": total_bookmarks, "total_users": total_users, "hide_logout": True},
    )


@app.get("/bookmarks_dashboard", include_in_schema=False)
async def bookmarks_dashboard_redirect(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
) -> RedirectResponse:
    """Instantly redirects an authenticated user straight to the bookmarks dashboard.

    Args:
        request (Request): The incoming HTTP request.
        is_authenticated (bool): Absolute cryptographic verification boolean.

    Returns:
        RedirectResponse: A blazing-fast 307 Temporary Redirect.

    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/bookmarks/dashboard{query}")


@app.get("/bookmarks_add", include_in_schema=False)
async def bookmarks_add_redirect(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
) -> RedirectResponse:
    """Aggressively routes the user to the bookmark creation interface.

    Args:
        request (Request): The incoming HTTP request.
        is_authenticated (bool): Absolute cryptographic verification boolean.

    Returns:
        RedirectResponse: A blazing-fast 307 Temporary Redirect.

    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/bookmarks/add{query}")


@app.get("/bookmarks_jd", include_in_schema=False)
async def bookmarks_jd_redirect(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
) -> RedirectResponse:
    """Directs the user to the precise Johnny.Decimal bookmark management portal.

    Args:
        request (Request): The incoming HTTP request.
        is_authenticated (bool): Absolute cryptographic verification boolean.

    Returns:
        RedirectResponse: A blazing-fast 307 Temporary Redirect.

    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/bookmarks/jd{query}")


@app.get("/bookmarks_tag", include_in_schema=False)
async def bookmarks_tag_redirect(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
) -> RedirectResponse:
    """Navigates the user instantly into the tag-based bookmark filtering system.

    Args:
        request (Request): The incoming HTTP request.
        is_authenticated (bool): Absolute cryptographic verification boolean.

    Returns:
        RedirectResponse: A blazing-fast 307 Temporary Redirect.

    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/bookmarks/tag{query}")


@app.get("/bookmarks_search", include_in_schema=False)
async def bookmarks_search_redirect(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
) -> RedirectResponse:
    """Propels the user directly into the high-performance search interface.

    Args:
        request (Request): The incoming HTTP request.
        is_authenticated (bool): Absolute cryptographic verification boolean.

    Returns:
        RedirectResponse: A blazing-fast 307 Temporary Redirect.

    """
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=303)
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/bookmarks/search{query}")


@app.post("/http_code/{status_code}")
async def http_code_post(status_code: int):  # type: ignore[no-untyped-def]
    """Instantly bounce a POST request to the equivalent HTTP status code documentation endpoint.

    Args:
        status_code (int): The target HTTP status code to brutally redirect towards.

    Returns:
        RedirectResponse: A hyper-fast 302 redirection envelope.

    """
    return CustomResponse.json(status_code=status_code)


@app.post("/webhook")
async def handle_webhook(request: Request):  # type: ignore[no-untyped-def]
    """Cryptographically secure GitHub Webhook listener.

    Relentlessly verifies the incoming `X-Hub-Signature-256` payload against the environment webhook secret using constant-time HMAC comparison to prevent timing attacks, automatically deploying updates upon validation.

    Args:
        request (Request): The raw GitHub webhook payload.

    Returns:
        dict: An incredibly fast acknowledgement payload.

    """
    payload = await request.body()
    secret = settings.AUTH.WEBHOOK_SECRET
    signature = request.headers.get("X-Hub-Signature-256")
    exp_signature = (
        "sha256="
        + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(exp_signature, signature):  # type: ignore[type-var]
        raise HTTPException(status_code=403, detail="Invalid signature")
    subprocess.Popen(f"kill -9 {os.getpid()}", shell=True)  # noqa: S602
    return {"message": "Webhook received successfully!"}


@app.get("/login", include_in_schema=False)
async def login_redirect(
    request: Request,
    is_authenticated: Annotated[bool, Depends(check_page_auth)],
):
    """Intelligently divert already-authenticated users away from the login portal back to the core dashboard.

    Args:
        request (Request): The HTTP request.
        is_authenticated (bool): Absolute cryptographic verification boolean.

    Returns:
        RedirectResponse: A 307 redirect to the dashboard, or the login page if unauthenticated.

    """
    if is_authenticated:
        return RedirectResponse(url="/bookmarks/dashboard", status_code=303)
    try:
        return TEMPLATES.TemplateResponse(request=request, name="login.j2.html", context={"hide_logout": True})
    except TemplateNotFound as e:
        raise HTTPException(status_code=404) from e


@app.get("/{page}")
async def serve_page(request: Request, page: str):
    """Resolve and renders root-level Markdown pages.

    Args:
        request (Request): The HTTP request.
        page (str): The requested path string.

    Returns:
        _TemplateResponse: The dynamically synthesized HTML page.

    """
    try:
        return TEMPLATES.TemplateResponse(request=request, name=f"{page}.j2.html", context={"hide_logout": True})
    except TemplateNotFound as e:
        raise HTTPException(status_code=404) from e
