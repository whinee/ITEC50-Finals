"""Authentication Endpoints.

Exposes lightning-fast endpoints for user registration, login, session termination, and identity verification, secured by Argon2id.
"""

import datetime
import random
from datetime import UTC
from typing import Annotated

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_301_MOVED_PERMANENTLY,
    HTTP_401_UNAUTHORIZED,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from wonderwords import RandomWord

from src.api.preferences import normalize_theme, theme_cookie_params
from src.db.main import get_session
from src.middlewares.auth import check_if_logged_in, get_session_cookie
from src.models.cookies import (
    decode_encrypted_cookie,
    set_default_cookie_params,
    set_default_cookie_params_with_encryption,
)
from src.schema import BaseUsers, User
from src.security.constants import COOKIE_EXPIRES_AFTER
from src.security.jwt_service import Claims, JwtService, get_jwt_service
from src.security.kdf_pass import get_kdf
from src.utils.custom_response import CustomResponse

router = APIRouter()

_rw = RandomWord()

ADJECTIVES = _rw.filter(
    include_parts_of_speech=["adjectives"],
    word_max_length=14,
    exclude_with_spaces=True,
)
NOUNS = _rw.filter(
    include_parts_of_speech=["nouns"],
    word_max_length=14,
    exclude_with_spaces=True,
)

random.shuffle(ADJECTIVES)
random.shuffle(NOUNS)

_adj_pool = list(ADJECTIVES)
_noun_pool = list(NOUNS)

email_adapter = TypeAdapter(EmailStr)


class LoginData(BaseModel):
    """Strictly typed payload for incoming authentication requests.

    Args:
        BaseModel (type): Pydantic inheritance.

    """

    identifier: str
    password: str


async def generate_username(session: AsyncSession) -> str:  # noqa: C901
    """Dynamically generates a globally unique, human-readable username.

    Leverages `wonderwords` to stitch together randomized adjective-noun combinations (e.g., 'fast_cheetah_42'). It aggressively polls the database in a loop to guarantee absolute collision avoidance before returning the minted username.

    Args:
        session (AsyncSession): The ultra-fast async database session.

    Returns:
        str: A mathematically unique human-readable username.
    
    """
    while True:
        if not _adj_pool:
            _adj_pool.extend(ADJECTIVES)
            random.shuffle(_adj_pool)
        if not _noun_pool:
            _noun_pool.extend(NOUNS)
            random.shuffle(_noun_pool)

        adj = _adj_pool.pop()
        noun = _noun_pool.pop()
        number = random.randint(1, 99)  # noqa: S311
        username = f"{adj}_{noun}_{number}"

        if len(username) > 32:
            continue

        result = await session.exec(select(User).where(User.username == username))
        if result.first() is None:
            return username


@router.post(path="/login", status_code=HTTP_200_OK)
async def login_user(  # noqa: C901
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    kdf: Annotated[Argon2id, Depends(get_kdf)],
    data: Annotated[LoginData, Form()],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
):
    """Authenticate users logging into DeciMark.

    This route performs a hyper-secure authentication sequence. It accepts either an E-mail or Username, dynamically routing the query based on Pydantic validation. It then defers to the Argon2id Key Derivation Function to rigorously verify the password hash against timing attacks. Upon success, it mints a symmetrically encrypted JWT and injects it securely into an HTTPOnly cookie.

    Args:
        request (Request): The raw HTTP request.
        response (Response): The FastAPI response endpoint.
        session (AsyncSession): Database session.
        jwt_service (JwtService): The cryptographic token engine.
        kdf (Argon2id): The state-of-the-art password hasher.
        data (LoginData): The strictly typed form data.
        is_logged_in (bool): Boolean context.

    Returns:
        UJSONResponse: The brilliantly formatted custom response.

    """
    if is_logged_in:
        return CustomResponse.json_flash(
            message="You must logout first.",
            category="error",
            status_code=HTTP_406_NOT_ACCEPTABLE,
        )

    identifier = data.identifier.strip().lower()

    try:
        email_adapter.validate_python(identifier)
        is_email = True
    except ValidationError:
        is_email = False

    if is_email:
        statement = select(User).where(User.email == identifier)
    else:
        statement = select(User).where(User.username == identifier)

    result = await session.exec(statement)
    try:
        user = result.one()
        kdf.verify_phc_encoded(data.password.encode(), user.password)
    except InvalidKey:
        return CustomResponse.json_flash(
            message="Username, E-mail, or password is invalid",
            category="error",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    except NoResultFound:
        return CustomResponse.json_flash(
            message="Username, E-mail, or password is invalid",
            category="error",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    except BaseException:  # noqa: BLE001
        return CustomResponse.json_flash(
            message="Something went wrong",
            category="error",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )
    issued_at = int(datetime.datetime.now(datetime.UTC).timestamp())
    expires_at = issued_at + COOKIE_EXPIRES_AFTER
    claims = Claims(exp=expires_at, sub=user.email, iat=issued_at)
    token = jwt_service.sign(claims=claims)
    cookie_params = set_default_cookie_params_with_encryption(
        name="session",
        value=token,
        expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
    )

    return CustomResponse.json_flash(
        message="Login successful!",
        category="success",
        status_code=HTTP_200_OK,
        cookie_params=[cookie_params, theme_cookie_params(normalize_theme(user.theme))],
    )


@router.get(path="/decrypt_cookie")
async def decrypt_cookie(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    """Introspect the client's current session token.

    Primarily used for debugging or deep frontend state synchronization, this route safely unwraps the Fernet-encrypted cookie and returns the verified JWT claims without exposing any sensitive cryptographic secrets.

    Args:
        request (Request): The incoming request.
        jwt_service (JwtService): The cryptographic engine.
        is_logged_in (bool): Login state.
        session_cookie (str): The raw encrypted token.

    Returns:
        UJSONResponse: The decoded token payload claims.

    """
    if not is_logged_in:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    return jwt_service.verify(decode_encrypted_cookie(session_cookie))


@router.get(path="/logout")
async def logout_user(
    request: Request,
    response: Response,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    """Securely terminates a user session.

    Intercepts the request, validates the existing JWT signature, and commands the browser to aggressively purge the HTTPOnly session cookie. It then forcefully redirects the client back to the login perimeter.

    Args:
        request (Request): Incoming request.
        response (Response): The HTTP response to modify.
        jwt_service (JwtService): Token engine.
        is_logged_in (bool): Boolean state.
        session_cookie (str): The actual cookie payload to annihilate.

    Returns:
        RedirectResponse: The fast redirect back to `/login`.

    """
    if not is_logged_in:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    if jwt_service.verify(decode_encrypted_cookie(session_cookie)) is not None:
        cookie_params = set_default_cookie_params(name="session")
        # NOTE: `delete_cookie` does not have the following params:
        # - value
        # - expires
        del cookie_params["value"]
        del cookie_params["expires"]
        response.delete_cookie(**cookie_params)
        response.headers["Location"] = "/login"
        response.status_code = HTTP_301_MOVED_PERMANENTLY
        return response
    return CustomResponse.http_code(
        request=request,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


@router.post(
    "/register",
    status_code=HTTP_201_CREATED,
)
async def register_new_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    kdf: Annotated[Argon2id, Depends(get_kdf)],
    payload: Annotated[BaseUsers, Form()],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
):
    """Register a brand new user into the DeciMark ecosystem.

    This route aggressively validates incoming form data against strictly typed Pydantic models. It executes high-speed `asyncpg` queries to ensure absolute uniqueness of the Email and Username before invoking the heavy Argon2id hashing mechanism on the password. If no username is provided, it autonomously falls back to the dynamic username generator.

    Args:
        request (Request): Incoming request.
        session (AsyncSession): High-speed database channel.
        kdf (Argon2id): Password derivation module.
        payload (BaseUsers): The strictly mapped new user schema.
        is_logged_in (bool): Login context state.

    Returns:
        UJSONResponse: The successfully formatted onboarding response.

    """
    if is_logged_in:
        return CustomResponse.json_flash(
            message="You must logout first.",
            category="warning",
            status_code=HTTP_406_NOT_ACCEPTABLE,
        )

    email_statement = select(User).where(User.email == payload.email)
    email_results = await session.exec(email_statement)
    email_has_first = email_results.first()
    if email_has_first:
        return CustomResponse.json_flash(
            message="User with E-mail already exists.",
            category="warning",
            status_code=HTTP_409_CONFLICT,
        )

    if payload.username:
        username_statement = select(User).where(User.username == payload.username)
        username_results = await session.exec(username_statement)
        username_has_first = username_results.first()
        if username_has_first:
            return CustomResponse.json_flash(
                message="User with this username already exists.",
                category="warning",
                status_code=HTTP_409_CONFLICT,
            )
    else:
        payload.username = await generate_username(session=session)

    created_at = datetime.datetime.now(tz=UTC)
    updated_at = created_at
    theme = normalize_theme(request.cookies.get("theme"))
    user = User(
        created_at=created_at,
        updated_at=updated_at,
        role="normal",
        theme=theme,
        **payload.model_dump(),
    )
    key = kdf.derive_phc_encoded(payload.password.encode())
    user.password = key
    user.disabled = False
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return CustomResponse.json_flash(
        message="Logged in successfully!",
        category="success",
        status_code=HTTP_301_MOVED_PERMANENTLY,
        headers={
            "Location": "/",
        },
        cookie_params=theme_cookie_params(theme),
    )
