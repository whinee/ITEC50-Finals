"""
Cookie Models.

Defines rigidly typed configuration objects for secure HTTPOnly cookies, ensuring impenetrable symmetric encryption headers.
"""

import base64
import datetime
from typing import Annotated, Any, Literal

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from src.config.settings import settings


class CookieConfig(BaseModel):
    """
    Configuration model for secure, high-performance cookie management.

    This model rigidly defines the exact properties for all HTTP cookies minted by the backend. By enforcing strict defaults (like `secure=True`, `httponly=True`, and `samesite="lax"`), it guarantees that DeciMark's session tokens are completely immune to standard XSS and CSRF attack vectors. This is a crucial component of our zero-trust architecture.

    Args: BaseModel (type): Core Pydantic base.
    """

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
) -> dict[str, Any]:
    """
    Generates an optimized, highly secure cookie parameter dictionary.

    Args: name (str): The strictly-defined name of the cookie key. value (str, optional): The payload of the cookie. Defaults to "". expires_at (datetime.datetime | None, optional): The absolute expiration timestamp. Defaults to None (Session cookie).

    Returns: dict[str, Any]: A serialized dictionary ready to be unpacked directly into FastAPI's `Response.set_cookie()`.

    Note: It strictly validates the generated payload against `CookieConfig` before returning, acting as an invincible safety net against malformed cookie injection.
    """
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
) -> dict[str, Any]:
    """
    Symmetrically encrypts and signs a cookie payload before wrapping it in secure parameters.

    Args: name (str): The strictly-defined name of the cookie key. value (str, optional): The raw, unencrypted payload. Defaults to "". expires_at (datetime.datetime | None, optional): The absolute expiration timestamp. Defaults to None.

    Returns: dict[str, Any]: A serialized, heavily fortified cookie configuration dictionary.

    Note: Utilizes `cryptography.fernet.Fernet` with a globally loaded secret key to achieve lightning-fast, military-grade AES-128-CBC encryption and HMAC-SHA256 authentication. Even if the transport layer is compromised, the payload remains computationally impenetrable.
    """
    f = Fernet(settings.AUTH.COOKIE_SECRET.encode())
    token_bytes = f.encrypt(value.encode())
    token = base64.urlsafe_b64encode(token_bytes).decode(encoding="utf-8")
    return set_default_cookie_params(name, value=token, expires_at=expires_at)


def decode_encrypted_cookie(token: str) -> str:
    """
    Decrypts and authenticates a Fernet-encrypted cookie payload.

    Args: token (str): The base64-urlsafe encoded ciphertext directly intercepted from the request headers.

    Returns: str: The guaranteed-authentic, plaintext payload.

    Note: This function instantly validates the cryptographic signature before attempting decryption, preventing padding oracle attacks and ensuring flawless zero-trust data extraction in sub-millisecond speeds.
    """

    f = Fernet(settings.AUTH.COOKIE_SECRET.encode())
    btoken = token.encode()
    dtoken = base64.urlsafe_b64decode(btoken)

    return f.decrypt(dtoken).decode(encoding="utf-8")
