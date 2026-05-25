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
    theme: Theme


def normalize_theme(value: str | None) -> Theme:
    return "dark" if value == "dark" else "light"


def set_theme_cookie(response: Response, theme: Theme) -> None:
    response.set_cookie(**theme_cookie_params(theme))


def theme_cookie_params(theme: Theme) -> dict:
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
