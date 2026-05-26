from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from src.db.main import get_session
from src.models.cookies import decode_encrypted_cookie
from src.schema import User
from src.security.jwt_service import JwtService, get_jwt_service


def get_session_cookie(
    request: Request,
):
    return request.cookies.get("session")


def check_if_logged_in(
    request: Request,
):
    return request.cookies.get("session") is not None


async def check_encrypted_cookie_auth(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    if session_cookie is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    try:
        jwt_token = decode_encrypted_cookie(session_cookie)
        return jwt_service.verify(jwt_token)

    except Exception as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED) from e


async def check_page_auth(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session_cookie: Annotated[str | None, Depends(get_session_cookie)] = None,
) -> bool:
    if session_cookie is None:
        return False

    try:
        jwt_token = decode_encrypted_cookie(session_cookie)
        claims = jwt_service.verify(jwt_token)
        if claims is None or claims.sub is None:
            return False

        result = await session.exec(select(User).where(User.email == claims.sub))
        user = result.first()

        return user is not None

    except Exception:  # noqa: BLE001
        return False
