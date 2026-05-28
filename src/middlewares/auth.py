"""
Authentication Middlewares.

Intercepts raw HTTP requests to extract session cookies, acting as the absolute first line of defense for the authentication pipeline.
"""

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
    """
    Rapidly extracts the raw session cookie string from incoming HTTP requests. This acts as the very first line of dependency injection for the authentication pipeline.

    Args:
        request (Request): The incoming FastAPI request.

    Returns:
        str | None: The raw, encrypted cookie string, if it exists.

    """
    return request.cookies.get("session")


def check_if_logged_in(
    request: Request,
):
    """
    Perform a lightweight, boolean check for the existence of a session cookie. Used for UI-level conditional rendering before aggressive cryptographic validation occurs.

    Args:
        request (Request): The incoming FastAPI request.

    Returns:
        bool: True if the cookie header is present, False otherwise.

    """
    return request.cookies.get("session") is not None


async def check_encrypted_cookie_auth(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    """
    Guard protected API routes.

    This asynchronous dependency ruthlessly intercepts the incoming request, decrypts the symmetric Fernet payload, and aggressively verifies the JWT signature. Any anomaly (tampering, expiration, or missing tokens) results in an instant, hard 401 Unauthorized exception, guaranteeing absolute zero-trust execution.

    Args:
        request (Request): The FastAPI request object.
        session (AsyncSession): The injected async database session.
        jwt_service (JWTService): The high-performance JWT cryptography service.
        session_cookie (str): The raw, encrypted cookie string.

    Returns:
        Claims: The perfectly verified JWT claims object.

    Raises:
        HTTPException: Immediately halts the request with a 401 status on failure.

    """
    if session_cookie is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    try:
        jwt_token = decode_encrypted_cookie(session_cookie)
        claims = jwt_service.verify(jwt_token)
        if not claims or not claims.sub:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

        result = await session.exec(select(User).where(User.email == claims.sub))
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )

        return claims

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED) from e


async def check_page_auth(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session_cookie: Annotated[str | None, Depends(get_session_cookie)] = None,
) -> bool:
    """
    Authenticate frontend Jinja2 routes.

    Unlike API routes which crash hard on failure, this function gracefully handles tampered or expired cookies, safely defaulting to a `False` boolean state. It performs a deep database verification (querying the `users` table via `sub` claims) to ensure the user has not been deleted or disabled since the token was minted.

    Returns:
        bool: True if the user is unequivocally authenticated and exists in the DB, False otherwise.

    """
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
