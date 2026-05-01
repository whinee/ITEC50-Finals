import time
from typing import Any, Union

import jwt
from fastapi import Cookie

from ..globals import ENV_VARS


async def verify_token(
    token: Union[str, None] = Cookie(default=None),
) -> Union[dict[str, Any], bool]:
    print(token)
    if token:
        try:
            decoded_token = jwt.decode(
                token,
                ENV_VARS["JWT_SECRET"],
                algorithms=["HS256"],
            )
            print(decoded_token["expires"], time.time())
            if decoded_token["expires"] >= time.time():
                return {"authorized": True, "token": decoded_token}
        except jwt.exceptions.InvalidSignatureError:
            return {
                "authorized": False,
                "status_code": 400,
                "detail": "Signature Verification Failed",
                "message": "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g., bad password), or your browser doesn't understand how to supply the credentials required.",
            }
    return {
        "authorized": False,
        "status_code": 401,
        "detail": "Unauthorized Access",
        "message": "You should first authorize before hitting this endpoint.",
    }
