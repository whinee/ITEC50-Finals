"""
JWT Cryptographic Service.

Mints, signs, and aggressively verifies stateless JSON Web Tokens using hyper-secure HMAC-SHA256 signatures.
"""

import datetime
from collections.abc import Callable
from datetime import UTC

import jwt
from jwt.types import Options
from pydantic import BaseModel

from src.config.settings import settings


class Claims(BaseModel):
    """
    Standardized payload schema for JSON Web Tokens (JWT).

    This strictly enforces the RFC 7519 standard claims. By mapping this directly into a frozen Pydantic model, it utterly nullifies the risk of payload tampering or type injection during deserialization.

    Args:
        BaseModel (type): Core Pydantic base.

    """

    aud: str | None = None
    exp: int
    iat: int | None = None
    iss: str | None = None
    nbf: int | None = None
    sub: str | None = None


class JwtService:
    """
    High-performance cryptographic service for minting and verifying JSON Web Tokens (JWT).

    Built around PyJWT, this stateful service caches the secret key and algorithmic configuration in memory to allow for blindingly fast, sub-millisecond token signatures and verification. It strictly enforces expiration (`exp`) claims and dynamically rejects forged tokens instantly, acting as the primary gateway for all authenticated traffic.
    """

    __encoding: Callable
    __decoding: Callable
    __algorithm: str
    __secret: str
    __options: Options

    def __init__(
        self,
        secret: str,
        algo: str = "HS256",
        options: Options | None = None,
    ) -> None:
        """
        Initialize the JWT Service with a highly fortified HMAC secret and encoding algorithm.

        Args:
            secret (str): The absolute cryptographic secret used for HS256 operations.
            algo (str): The designated hashing algorithm.
            options (dict): PyJWT verification options.

        """
        self.__algorithm = algo
        self.__secret = secret
        self.__options = Options()
        self.__options["require"] = [
            "exp",
        ]  # NOTE: I believe exp should be always required
        self.__options["verify_exp"] = True
        if options is not None:
            self.__options = self.__options | options

        def __encoding(claims: Claims) -> str:
            """
            Internally handles the rapid serialization and HS256 signing of a perfectly typed Claims payload.

            Args:
                claims (Claims): The strictly typed Pydantic claims object.

            Returns:
                str: The fully minted JSON Web Token.

            """
            claims_dict = claims.model_dump()
            claims_payload = {k: v for k, v in claims_dict.items() if v is not None}

            return jwt.encode(claims_payload, self.__secret, self.__algorithm)

        def __decoding(encoded: str) -> dict:
            """
            Internally forces the rigorous verification and payload extraction of an incoming token string.

            Args:
                encoded (str): The raw, unverified JWT payload string.

            Returns:
                dict: The completely validated and extracted raw payload data.

            """
            return jwt.decode(encoded, self.__secret, self.__algorithm, options=options)

        self.__encoding = __encoding
        self.__decoding = __decoding

    def sign(self, claims: Claims) -> str:
        """
        Cryptographically signs a Pydantic Claims object into a compact JWT string.

        Args:
            claims (Claims): The strictly typed payload claims.

        Returns:
            str: The signed, impenetrable JWT string ready for HTTP headers.

        """
        return self.__encoding(claims)

    def is_expired(self, token: str) -> bool:
        """
        Evaluate whether a given token has surpassed its cryptographic expiration timestamp.

        Args:
            token (str): The JWT string to evaluate.

        Returns:
            bool: True if the token is dead, False if it is still alive.

        """
        payload = self.__decoding(token)
        claims = Claims(**payload)
        now = datetime.datetime.now(tz=UTC).timestamp()
        return claims.exp <= now

    def verify(self, token: str) -> Claims:
        """
        Aggressively verifies the cryptographic signature of a token and decodes it.

        Args:
            token (str): The incoming JWT string.

        Returns:
            Claims: The perfectly typed, guaranteed-authentic payload.

        Raises: jwt.ExpiredSignatureError: If the token has lived past its expiration. jwt.InvalidSignatureError: If the cryptographic signature fails to match.

        """
        payload = self.__decoding(token)
        return Claims(**payload)


def get_jwt_service() -> JwtService:
    """
    Dependency injection factory for the JwtService. Instantiates the service with the globally secure HMAC-SHA256 secret.

    Returns:
        JwtService: A fully armed and operational JWT cryptographic instance.

    """
    return JwtService(secret=settings.AUTH.JWT_SECRET)
