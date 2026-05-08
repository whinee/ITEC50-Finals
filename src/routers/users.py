import time
from typing import Any

import jwt
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse

from src.middlewares import auth
from src.models.user import UserReg, comp_pw, hash_pw
from src.utils import TEMPLATES, CustomResponse

router = APIRouter()


@router.post("/register", status_code=200)
async def register(user: UserReg, response: Response):
    emails = DB.get("emails") or []

    if user.email in emails:
        response.status_code = 400
        return CustomResponse.json(
            400,
            details="E-mail Error",
            message="E-mail already used. Try again.",
        )
    
    emails.append(user.email)

    if DB.get(user.username):
        response.status_code = 400
        return CustomResponse.json(
            400,
            details="Username Error",
            message="Username already exists. Try again.",
        )

    if user.confirm_password != user.password:
        response.status_code = 400
        return CustomResponse.json(
            400,
            details="Password Error",
            message="Password does not match. Try again.",
        )

    DB.put(
        {
            "email": user.email,
            "passwd": hash_pw(user.password).decode("utf-8"),
        },
        user.username,
    )

    return CustomResponse.json(200)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return TEMPLATES.TemplateResponse(request, "login.j2.html")


@router.post("/login", status_code=200)
async def login_post(
    request: Request,
    response: Response,
    username: str = Form(),
    password: str = Form(),
):
    response.delete_cookie("token")
    flash = CustomResponse.template(request, "login.j2.html")
    if du := DB.get(username):
        if comp_pw(password, du["passwd"]):
            payload = {
                "username": username,
                "role": "user",
                "expires": time.time() + (60 * 60 * 3),
            }
            return flash(
                "Login Successful",
                "success",
                headers={
                    "Set-Cookie": "token="
                    + jwt.encode(payload, ENV_VARS["JWT_SECRET"], algorithm="HS256")
                    + "; Max-Age=10800",
                },
            )
    return flash("Make sure that you are entering the correct credentials.", "danger")


@router.get("/me", status_code=200)
async def me(token: dict[str, Any] = Depends(auth.verify_token)):
    if token.pop("authorized"):
        return CustomResponse.json(200, json={"username": token["token"]["username"]})
    return CustomResponse.json(**token)
