import hashlib
import hmac
import os
import subprocess
import time
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from src.config import env
from src.models.settings import settings
from src.routers import users
from src.utils import TEMPLATES, CustomResponse

description = """
Lyra Phasma's Website and Blog :3
"""

env.load_environment()

security = HTTPBasic()

middleware = [
    Middleware(SessionMiddleware, secret_key=settings.JWT_SECRET),  # type: ignore
]
app = FastAPI(
    title="Lyra-on.top",
    description=description,
    version="1.0.0",
    # terms_of_service="http://hyaku.download/tos",
    contact={
        "name": "Lyra Phasma",
        "url": "https://lyra-on.top",
        "email": "whinyaan@disroot.org",
    },
    license_info={
        "name": "MIT",
        "url": "https://choosealicense.com/licenses/mit/",
    },
    docs_url=None,
    redoc_url=None,
    middleware=middleware,
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next) -> Any:  # type: ignore[no-untyped-def]
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        if response.status_code == 404:
            status_code, content, status = CustomResponse.raw_json(status_code=404)
            return TEMPLATES.TemplateResponse(
                request=request,
                name="code.j2.html",
                context={
                    "content": content,
                    "status": {"code": status_code, **status.copy()},
                },
                status_code=status_code,
            )
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except:  # noqa: E722
        return CustomResponse.json(
            status_code=500,
            message="Error occured",
            json={"traceback": traceback.format_exc()},
        )

app.mount("/static/", StaticFiles(directory="src/static"), name="static")
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/{page}")
async def serve_page(request: Request, page: str):
    return TEMPLATES.TemplateResponse(request=request, name=f"{page}.j2.html")


@app.get("/docs", include_in_schema=False, status_code=200)
async def docs(response: Response):  # type: ignore[no-untyped-def]
    response.status_code = 200
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,  # type: ignore[arg-type]
        title=app.title + " - Docs",
        swagger_css_url="/static/stylesheets/docs.css",
    )


@app.get("/code/{code}")
async def code_get(request: Request, code: int):  # type: ignore[no-untyped-def]
    status_code, content, status = CustomResponse.raw_json(status_code=code)
    return TEMPLATES.TemplateResponse(
        name="code.j2.html",
        request=request,
        context={
            "content": content,
            "status": {"code": status_code, **status.copy()},
        },
        status_code=status_code,
    )


@app.post("/code/{code}")
async def code_post(code: int): # type: ignore[no-untyped-def]
    return CustomResponse.json(status_code=code)


@app.post("/webhook")
async def handle_webhook(request: Request): # type: ignore[no-untyped-def]
    payload = await request.body()
    secret = settings.WEBHOOK_SECRET
    signature = request.headers.get("X-Hub-Signature-256")
    exp_signature = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(exp_signature, signature): # type: ignore[type-var]
        raise HTTPException(status_code=403, detail="Invalid signature")
    subprocess.Popen(f"kill -9 {os.getpid()}", shell=True)  # noqa: S602
    return {"message": "Webhook received successfully!"}
