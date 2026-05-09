from app.middlewares.auth import check_if_logged_in, get_session_cookie
from app.core.security.jwt_service import JwtService, Claims, get_jwt_service
from sqlalchemy.exc import NoResultFound
from datetime import UTC
import datetime
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_200_OK,
    HTTP_409_CONFLICT,
    HTTP_201_CREATED,
    HTTP_406_NOT_ACCEPTABLE, HTTP_301_MOVED_PERMANENTLY,
)
from cryptography.exceptions import InvalidKey
from src.security.kdf_pass import get_kdf
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from app.models.users import Users, BaseUsers

from src.db.main import get_session
from src.models.cookies import (
    set_default_cookie_params,
    set_default_cookie_params_with_encryption,
    decode_encrypted_cookie,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, Literal
from fastapi import APIRouter, Form, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from sqlmodel import select, or_

router = APIRouter()


class LoginData(BaseModel):
    username: str
    password: str
    role: Literal["professional", "patient"]


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
    if is_logged_in:
        raise HTTPException(
            status_code=HTTP_406_NOT_ACCEPTABLE, detail="You must logout first."
        )

    statement = select(Users).where(
        or_(Users.username == data.username, Users.email == data.username)
    )
    result = await session.exec(statement)
    try:
        user = result.one()
        kdf.verify_phc_encoded(data.password.encode(), user.password)
    except InvalidKey:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Username or password is invalid"
        )
    except NoResultFound:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Username or password is invalid"
        )
    except BaseException:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong"
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
    response.headers["Location"] = "/"
    response.status_code = HTTP_301_MOVED_PERMANENTLY
    return response


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
        # NOTE: `delete_cookie` does not have the following params
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
            status_code=HTTP_406_NOT_ACCEPTABLE, detail="You must logout first."
        )

    if payload.username:
        statement = select(Users).where(
            or_(Users.username == payload.username, Users.email == payload.email)
        )
    else:
        statement = select(Users).where(Users.email == payload.email)
    results = await session.exec(statement)
    has_first = results.first()
    if has_first:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="User with email or username already exists",
        )

    created_at = datetime.datetime.now(tz=UTC)
    updated_at = created_at
    user = Users(created_at=created_at, updated_at=updated_at, **payload.model_dump())
    key = kdf.derive_phc_encoded(payload.password.encode())
    if payload.professional_license_id:
        user.role = ["professional"]
    else:
        user.role = ["patient"]
    user.password = key
    user.disabled = False
    if user.username == "":
        user.username = None
    if user.professional_license_id == "":
        user.professional_license_id = None
    session.add(user)
    await session.commit()
    await session.refresh(user)
    # payload = UserWithoutPassword(
    #     username=user.username,
    #     email=user.email,
    #     contact_number=user.contact_number,
    #     professional_license_id=user.professional_license_id,
    # )
    response = Response(status_code=HTTP_301_MOVED_PERMANENTLY)
    response.headers["Location"] = "/"
    return response
