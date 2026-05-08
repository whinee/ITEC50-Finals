from app.core.config import settings
from datetime import UTC
from jwt.types import Options
from typing import Callable
import datetime
import jwt

from pydantic import BaseModel


class Claims(BaseModel):
    aud: str | None = None
    exp: int
    iat: int | None = None
    iss: str | None = None
    nbf: int | None = None
    sub: str | None = None


class JwtService:
    __encoding: Callable
    __decoding: Callable
    __algorithm: str
    __secret: str
    __options: Options

    def __init__(
        self, secret: str, algo: str = "HS256", options: Options | None = None
    ):
        self.__algorithm = algo
        self.__secret = secret
        self.__options = Options()
        self.__options["require"] = [
            "exp"
        ]  # NOTE: I believe exp should be always required
        self.__options["verify_exp"] = True
        if options is not None:
            self.__options = self.__options | options

        def __encoding(claims: Claims) -> str:
            claims_dict = claims.model_dump()
            claims_payload = {k: v for k, v in claims_dict.items() if v is not None}

            return jwt.encode(claims_payload, self.__secret, self.__algorithm)

        def __decoding(encoded: str) -> dict:
            return jwt.decode(encoded, self.__secret, self.__algorithm, options=options)

        self.__encoding = __encoding
        self.__decoding = __decoding

    def sign(self, claims: Claims) -> str:
        return self.__encoding(claims)

    def is_expired(self, token: str) -> bool:
        payload = self.__decoding(token)
        claims = Claims(**payload)
        now = datetime.datetime.now(tz=UTC).timestamp()
        return claims.exp <= now

    def verify(self, token: str) -> Claims:
        payload = self.__decoding(token)
        claims = Claims(**payload)
        return claims


def get_jwt_service() -> JwtService:
    return JwtService(secret=settings.AUTH.JWT_SECRET)
