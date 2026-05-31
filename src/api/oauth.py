import datetime
import secrets
from datetime import UTC
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.responses import RedirectResponse
from starlette.status import HTTP_301_MOVED_PERMANENTLY, HTTP_404_NOT_FOUND

from src.api.auth import generate_username
from src.config.settings import settings
from src.db.main import get_session
from src.models.cookies import set_default_cookie_params_with_encryption
from src.schema import User
from src.security.constants import COOKIE_EXPIRES_AFTER
from src.security.jwt_service import Claims, JwtService, get_jwt_service
from src.security.kdf_pass import get_kdf

router = APIRouter(prefix="/oauth")


@router.get("/google")
async def google_login():
    """
    Redirect to Google OAuth portal.

    Returns:
        RedirectResponse: Redirection to Google.

    """
    if not settings.OAUTH.GOOGLE.ENABLE:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Google OAuth is not enabled.",
        )
    client_id = settings.OAUTH.GOOGLE.CLIENT_ID
    redirect_uri = "http://localhost:8000/auth/oauth/google/callback"
    url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=email%20profile"
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    kdf: Annotated[any, Depends(get_kdf)],
):
    """
    Handle Google OAuth callback.

    Args:
        request (Request): HTTP request.
        code (str): OAuth code.
        session (AsyncSession): Database session.
        jwt_service (JwtService): JWT Service.
        kdf (any): Key Derivation Function.

    Returns:
        RedirectResponse: Redirection to home page.

    """
    if not settings.OAUTH.GOOGLE.ENABLE:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Google OAuth is not enabled.",
        )
    token_url = "https://oauth2.googleapis.com/token"  # noqa: S105
    data = {
        "client_id": settings.OAUTH.GOOGLE.CLIENT_ID,
        "client_secret": settings.OAUTH.GOOGLE.CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:8000/auth/oauth/google/callback",
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data)
        access_token = token_res.json().get("access_token")

        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_res = await client.get(user_info_url, headers=headers)
        user_info = user_info_res.json()

    email = user_info.get("email")
    return await handle_oauth_user(email, session, jwt_service, kdf)


@router.get("/github")
async def github_login():
    """
    Redirect to GitHub OAuth portal.

    Returns:
        RedirectResponse: Redirection to GitHub.

    """
    if not settings.OAUTH.GITHUB.ENABLE:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="GitHub OAuth is not enabled.",
        )
    client_id = settings.OAUTH.GITHUB.CLIENT_ID
    redirect_uri = "http://localhost:8000/auth/oauth/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=user:email"
    return RedirectResponse(url)


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    kdf: Annotated[any, Depends(get_kdf)],
):
    """
    Handle GitHub OAuth callback.

    Args:
        request (Request): HTTP request.
        code (str): OAuth code.
        session (AsyncSession): Database session.
        jwt_service (JwtService): JWT Service.
        kdf (any): Key Derivation Function.

    Returns:
        RedirectResponse: Redirection to home page.

    """
    if not settings.OAUTH.GITHUB.ENABLE:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="GitHub OAuth is not enabled.",
        )
    token_url = "https://github.com/login/oauth/access_token"  # noqa: S105
    data = {
        "client_id": settings.OAUTH.GITHUB.CLIENT_ID,
        "client_secret": settings.OAUTH.GITHUB.CLIENT_SECRET,
        "code": code,
        "redirect_uri": "http://localhost:8000/auth/oauth/github/callback",
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data=data, headers=headers)
        access_token = token_res.json().get("access_token")

        user_emails_url = "https://api.github.com/user/emails"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        user_emails_res = await client.get(user_emails_url, headers=headers)
        emails = user_emails_res.json()

    email = next((e["email"] for e in emails if e.get("primary")), emails[0]["email"])
    return await handle_oauth_user(email, session, jwt_service, kdf)


async def handle_oauth_user(
    email: str,
    session: AsyncSession,
    jwt_service: JwtService,
    kdf: any,
):
    """
    Core logic to provision or authenticate a user from an OAuth provider.

    Args:
        email (str): The verified email from the provider.
        session (AsyncSession): Database session.
        jwt_service (JwtService): JWT Service.
        kdf (any): Key Derivation Function.

    Returns:
        RedirectResponse: Redirection to home page.

    """
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    user = result.first()

    if not user:
        # Auto-provision new user
        username = await generate_username(session)
        raw_pass = secrets.token_urlsafe(32)
        hashed_pass = kdf.derive_phc_encoded(raw_pass.encode())

        user = User(
            username=username,
            email=email,
            password=hashed_pass,
            role="normal",
            theme="light",
            disabled=False,
            created_at=datetime.datetime.now(tz=UTC),
            updated_at=datetime.datetime.now(tz=UTC),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Issue real session JWT
    issued_at = int(datetime.datetime.now(datetime.UTC).timestamp())
    expires_at = issued_at + COOKIE_EXPIRES_AFTER
    claims = Claims(exp=expires_at, sub=user.email, iat=issued_at)
    session_token = jwt_service.sign(claims=claims)

    cookie_params = set_default_cookie_params_with_encryption(
        name="session",
        value=session_token,
        expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
    )

    response = RedirectResponse(url="/", status_code=HTTP_301_MOVED_PERMANENTLY)
    response.set_cookie(**cookie_params)
    return response
