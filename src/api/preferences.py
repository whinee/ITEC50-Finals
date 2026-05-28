"""User Preferences Endpoints.

Handles real-time, asynchronous theme toggling by persisting preferences to PostgreSQL and reflecting them via secure cookies.
"""

from typing import Annotated, Literal

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, Request, Response
from jwt import InvalidTokenError
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.models.cookies import decode_encrypted_cookie
from src.schema import User
from src.security.jwt_service import JwtService, get_jwt_service

router = APIRouter()

Theme = Literal["light", "dark"]
THEME_COOKIE = "theme"
THEME_COOKIE_MAX_AGE = 60 * 60 * 24 * 180


class ThemePayload(BaseModel):
    """Strictly typed JSON validation schema for user theme mutation requests.

    Args:
        BaseModel (type): Core Pydantic inheritance.

    """

    theme: Theme


def normalize_theme(value: str | None) -> Theme:
    """Sanitizes theme strings to rigidly enforce `light` or `dark`.

    Args:
        value (str | None): The unsafe input theme state.

    Returns:
        Theme: The safely resolved Literal value.

    """
    return "dark" if value == "dark" else "light"


def set_theme_cookie(response: Response, theme: Theme) -> None:
    """Dynamically mutates an outbound FastAPI response object to inject a rock-solid, six-month theme preference cookie.

    Args:
        response (Response): The mutable outbound response.
        theme (Theme): The normalized theme constant.

    """
    response.set_cookie(**theme_cookie_params(theme))


def theme_cookie_params(theme: Theme) -> dict:
    """Construct the highly secure, unencrypted but strictly bounded configuration dictionary for the frontend theme cookie.

    Args:
        theme (Theme): The validated visual style string.

    Returns:
        dict: The perfectly formatted cookie injection schema.

    """
    return {
        "key": THEME_COOKIE,
        "value": theme,
        "max_age": THEME_COOKIE_MAX_AGE,
        "path": "/",
        "samesite": "lax",
        "secure": False,
        "httponly": False,
    }


async def get_optional_user(
    request: Request,
    session: AsyncSession,
    jwt_service: JwtService,
) -> User | None:
    """Fetch the authenticated User.

    This gracefully absorbs token tampering, missing cookies, or database faults by returning `None` instead of throwing HTTP exceptions, perfect for routes that need to serve both logged-in and anonymous states (like theme togglers).

    Args:
        request (Request): Raw HTTP request.
        session (AsyncSession): Database channel.
        jwt_service (JwtService): The cryptographic processor.

    Returns:
        User | None: The perfectly validated User object, or None if anonymous.

    """
    session_cookie = request.cookies.get("session")
    if session_cookie is None:
        return None

    try:
        claims = jwt_service.verify(decode_encrypted_cookie(session_cookie))
    except (InvalidToken, InvalidTokenError, ValueError):
        return None

    if claims.sub is None:
        return None

    result = await session.exec(select(User).where(User.email == claims.sub))
    return result.first()


@router.get("/settings/theme")
async def get_theme(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
):
    """Resolve the current theme for the client in real-time.

    It intelligently queries the database for persisted preferences if the user is authenticated, falling back to an unencrypted browser cookie if they are anonymous. It guarantees that the browser is always issued an updated `theme` cookie in response.

    Args:
        request (Request): The incoming request payload.
        response (Response): The mutable outbound response payload.
        session (AsyncSession): High-speed database pipe.
        jwt_service (JwtService): JWT validation factory.

    Returns:
        UJSONResponse: The fully synthesized theme JSON dictionary.

    """
    user = await get_optional_user(
        request=request,
        session=session,
        jwt_service=jwt_service,
    )
    theme = normalize_theme(user.theme if user else request.cookies.get(THEME_COOKIE))
    set_theme_cookie(response=response, theme=theme)
    return {"theme": theme}


@router.put("/settings/theme")
async def update_theme(
    payload: ThemePayload,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
):
    """Asynchronously mutates the application theme for the active user.

    This immediately cascades the updated theme into the PostgreSQL database and simultaneously injects a fresh, 180-day `theme` cookie back into the client for instantaneous UI reactivity.

    Args:
        payload (ThemePayload): The validated theme switch target.
        request (Request): The HTTP request object.
        response (Response): The mutable HTTP response.
        session (AsyncSession): PostgreSQL engine.
        jwt_service (JwtService): The cryptographic orchestrator.

    Returns:
        UJSONResponse: The meticulously updated theme echo dictionary.

    """
    theme = normalize_theme(payload.theme)
    user = await get_optional_user(
        request=request,
        session=session,
        jwt_service=jwt_service,
    )

    if user is not None:
        user.theme = theme
        session.add(user)
        await session.commit()

    set_theme_cookie(response=response, theme=theme)
    return {"theme": theme}
