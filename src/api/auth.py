import datetime
import random
from datetime import UTC
from typing import Annotated

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound
from sqlmodel import or_, select
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

from src.db.main import get_session
from src.middlewares.auth import check_if_logged_in, get_session_cookie
from src.models.cookies import (
    decode_encrypted_cookie,
    set_default_cookie_params,
    set_default_cookie_params_with_encryption,
)
from src.schema import BaseUsers, User
from src.security.jwt_service import Claims, JwtService, get_jwt_service
from src.security.kdf_pass import get_kdf
from src.utils.custom_response import CustomResponse

router = APIRouter()

_rw = RandomWord()

# pre-filter the lists once at startup, not on every call
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

# shuffle so we exhaust randomly
random.shuffle(ADJECTIVES)
random.shuffle(NOUNS)

_adj_pool = list(ADJECTIVES)
_noun_pool = list(NOUNS)

class LoginData(BaseModel):
    username: str
    password: str

async def generate_username(session: AsyncSession) -> str:  # noqa: C901
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

        # check db
        result = await session.exec(select(User).where(User.username == username))
        if result.first() is None:
            return username

@router.post(path="/login", status_code=HTTP_200_OK)
async def login_user(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    kdf: Annotated[Argon2id, Depends(get_kdf)],
    data: Annotated[LoginData, Form()],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
):
    flash = CustomResponse.template_flash(request, "login.j2.html")
    if is_logged_in:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="You must logout first.",
        )

    statement = select(User).where(
        or_(User.username == data.username, User.email == data.username),
    )
    result = await session.exec(statement)
    try:
        user = result.one()
        kdf.verify_phc_encoded(data.password.encode(), user.password)
    except InvalidKey:
        return flash(
            "Username or password is invalid",
            "danger",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    except NoResultFound:
        return flash(
            "Username or password is invalid",
            "danger",
            status_code=HTTP_401_UNAUTHORIZED,
        )
    except BaseException:  # noqa: BLE001
        return flash(
            "Something went wrong",
            "danger",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )
    issued_at = int(datetime.datetime.now(datetime.UTC).timestamp())
    expires_at = issued_at + (60 * 60 * 24)
    claims = Claims(exp=expires_at, sub=user.email, iat=issued_at)
    token = jwt_service.sign(claims=claims)
    cookie_params = set_default_cookie_params_with_encryption(
        name="session",
        value=token,
        expires_at=datetime.datetime.fromtimestamp(expires_at, tz=datetime.UTC),
    )

    response.set_cookie(**cookie_params)
    return flash(
        "Username or password is invalid",
        "success",
        status_code=HTTP_301_MOVED_PERMANENTLY,
        headers={
            "Location": "/",
        },
        cookie_params=cookie_params,
    )


@router.get(path="/decrypt_cookie")
async def decrypt_cookie(
    request: Request,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    if not is_logged_in:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    jwt_token = decode_encrypted_cookie(session_cookie)
    return jwt_service.verify(jwt_token)


@router.get(path="/logout")
async def logout_user(
    request: Request,
    response: Response,
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    is_logged_in: Annotated[bool, Depends(check_if_logged_in)],
    session_cookie: Annotated[str, Depends(get_session_cookie)],
):
    if not is_logged_in:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)

    jwt_token = decode_encrypted_cookie(session_cookie)
    if jwt_service.verify(jwt_token) is not None:
        cookie_params = set_default_cookie_params(name="session")
        # NOTE: `delete_cookie` does not have the following params:
        # - value
        # - expires
        del cookie_params["value"]
        del cookie_params["expires"]
        response.delete_cookie(**cookie_params)
        response.headers["Location"] = "/"
        response.status_code = HTTP_301_MOVED_PERMANENTLY
        return response
    raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR)


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
    if is_logged_in:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE,
            detail="You must logout first.",
        )

    if payload.username:
        statement = select(User).where(
            or_(User.username == payload.username, User.email == payload.email),
        )
    else:
        statement = select(User).where(User.email == payload.email)
    results = await session.exec(statement)
    has_first = results.first()
    if has_first:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="User with email or username already exists",
        )

    created_at = datetime.datetime.now(tz=UTC)
    updated_at = created_at
    user = User(created_at=created_at, updated_at=updated_at, **payload.model_dump())
    key = kdf.derive_phc_encoded(payload.password.encode())
    user.password = key
    user.disabled = False
    session.add(user)
    await session.commit()
    await session.refresh(user)
    response = Response(status_code=HTTP_301_MOVED_PERMANENTLY)
    response.headers["Location"] = "/"
    return response
