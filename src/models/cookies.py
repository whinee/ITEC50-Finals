import base64
import datetime
from typing import Annotated, Any, Literal

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from src.config.settings import settings


class CookieConfig(BaseModel):
    key: Annotated[str | None, Field()] = None
    value: Annotated[str | None, Field()] = None
    expires: Annotated[datetime.datetime | None, Field()] = None
    path: Annotated[str, Field()] = "/"
    samesite: Annotated[Literal["none", "lax", "strict"], Field()] = "lax"
    secure: Annotated[bool, Field()] = True
    httponly: Annotated[bool, Field()] = True


def set_default_cookie_params(
    name: str,
    value: str = "",
    expires_at: datetime.datetime | None = None,
) -> dict:
    cookie: dict[str, Any] = {}
    cookie["key"] = name
    cookie["value"] = value
    cookie["expires"] = expires_at
    cookie["secure"] = True
    cookie["httponly"] = True
    cookie["samesite"] = "lax"
    cookie["path"] = "/"
    CookieConfig(**cookie)
    return cookie


def set_default_cookie_params_with_encryption(
    name: str,
    value: str = "",
    expires_at: datetime.datetime | None = None,
):
    f = Fernet(settings.AUTH.COOKIE_SECRET.encode())
    token_bytes = f.encrypt(value.encode())
    token = base64.urlsafe_b64encode(token_bytes).decode(encoding="utf-8")
    return set_default_cookie_params(name, value=token, expires_at=expires_at)


def decode_encrypted_cookie(token: str) -> str:

    f = Fernet(settings.AUTH.COOKIE_SECRET.encode())
    btoken = token.encode()
    dtoken = base64.urlsafe_b64decode(btoken)

    return f.decrypt(dtoken).decode(encoding="utf-8")
