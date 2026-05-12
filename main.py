import hashlib
import hmac
import os
import subprocess
import time
import traceback
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import UJSONResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from jinja2 import TemplateNotFound
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import _TemplateResponse

from src.api import auth
from src.config.settings import settings
from src.utils.custom_response import TEMPLATES, CustomResponse
from src.utils.http_code import check_if_http_code_group_error, get_http_code_group

# Constants
DEFAULT_ERROR_HTTP_CODE = 500
DESCRIPTION = """
Lyra Phasma's Website and Blog :3
"""

security = HTTPBasic()

middleware = [
    Middleware(SessionMiddleware, secret_key=settings.AUTH.JWT_SECRET),  # type: ignore
]

app = FastAPI(
    title="Lyra-on.top",
    description=DESCRIPTION,
    version="1.0.0",
    # terms_of_service="http://hyaku.download/tos",
    contact={
        "name": "Lyra Phasma",
        "url": "https://lyra-on.top",
        "email": "lyraphasma@gmail.com",
    },
    license_info={
        "name": "Custom Dual-License",
        "url": "https://github.com/whinee/ITEC50-Finals/blob/main/docs/LICENSE.md",
    },
    docs_url=None,
    redoc_url=None,
    middleware=middleware,
)


def _code_get(request: Request, status_code: int) -> _TemplateResponse:
    status_code, content, status = CustomResponse.raw_json(status_code=status_code)
    return TEMPLATES.TemplateResponse(
        name="code.j2.html",
        request=request,
        context={
            "content": content,
            "status": {"code": status_code, **status.copy()},
        },
        status_code=status_code,
    )


@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response | UJSONResponse | _TemplateResponse:
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        status_code = response.status_code
        if check_if_http_code_group_error(get_http_code_group(status_code)):
            return _code_get(request, status_code)
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except:  # noqa: E722
        if (settings.ENV in ("development", "test")) and (settings.DEBUG):
            return CustomResponse.json(
                status_code=DEFAULT_ERROR_HTTP_CODE,
                message="Error occured",
                json={"traceback": traceback.format_exc()},
            )
        return _code_get(request, status_code=DEFAULT_ERROR_HTTP_CODE)


app.mount("/static/", StaticFiles(directory="src/static"), name="static")
app.include_router(auth.router, prefix="/auth", tags=["auth"])


# @app.get("/{page}")
# async def serve_page(request: Request, page: str):
#     try:
#         return TEMPLATES.TemplateResponse(request=request, name=f"{page}.j2.html")
#     except TemplateNotFound as e:
#         raise HTTPException(status_code=404) from e


@app.get("/docs", include_in_schema=False, status_code=200)
async def docs(response: Response):  # type: ignore[no-untyped-def]
    response.status_code = 200
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,  # type: ignore[arg-type]
        title=app.title + " - Docs",
        # swagger_css_url="/static/stylesheets/docs.css",
    )


@app.get("/code/{status_code}")
async def code_get(request: Request, status_code: int) -> _TemplateResponse:
    return _code_get(request=request, status_code=status_code)


@app.post("/code/{status_code}")
async def code_post(status_code: int):  # type: ignore[no-untyped-def]
    return CustomResponse.json(status_code=status_code)


@app.post("/webhook")
async def handle_webhook(request: Request):  # type: ignore[no-untyped-def]
    payload = await request.body()
    secret = settings.AUTH.WEBHOOK_SECRET
    signature = request.headers.get("X-Hub-Signature-256")
    exp_signature = (
        "sha256="
        + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(exp_signature, signature):  # type: ignore[type-var]
        raise HTTPException(status_code=403, detail="Invalid signature")
    subprocess.Popen(f"kill -9 {os.getpid()}", shell=True)  # noqa: S602
    return {"message": "Webhook received successfully!"}
