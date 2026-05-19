from collections.abc import Mapping
from typing import Any, Literal, Protocol

from fastapi import Request
from fastapi.responses import UJSONResponse  # type: ignore
from starlette.background import BackgroundTask
from starlette.templating import Jinja2Templates, _TemplateResponse

from src.utils.http_code import (
    build_status_meta,
    check_if_http_code_group_error,
    get_http_code_group,
    get_http_code_group_details,
    get_http_code_group_message,
    normalize_http_status,
)


def fetch_flash(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


TEMPLATES = Jinja2Templates(directory="src/templates")
TEMPLATES.env.globals["fetch_flash"] = fetch_flash


class TemplateFlashInnerCallable(Protocol):
    def __call__(
        self,
        message: str,
        category: Literal["success", "info", "warning", "error"] = "info",
        context: dict[str, Any] | None = None,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        cookie_params: dict[str, Any] | None = None,
    ) -> Jinja2Templates.TemplateResponse: ...


class CustomResponse:
    @staticmethod
    def raw_json(
        status_code: int,
        details: str | None = None,
        message: str | None = None,
        error: bool | None = None,
    ) -> tuple[int, dict[str, Any], dict[str, Any]]:

        code_group = get_http_code_group(status_code)

        status = build_status_meta(status_code)
        status_code = normalize_http_status(status_code)

        content: dict[str, Any] = {
            "detail": get_http_code_group_details(code_group, details),
            "message": get_http_code_group_message(code_group, message),
            "error": check_if_http_code_group_error(code_group, error),
        }

        return status_code, content, status

    @staticmethod
    def json(  # type: ignore[no-untyped-def]
        status_code: int,
        detail: str | None = None,
        message: str | None = None,
        error: bool | None = None,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        cookie_params: dict[str, Any] | None = None,
    ) -> UJSONResponse:  # type: ignore
        if json is None:
            json = {}

        status_code, content, status = CustomResponse.raw_json(
            status_code,
            detail,
            message,
            error,
        )

        response = UJSONResponse(  # type: ignore[misc]
            content={
                **content,
                **json,
                "status": status,
            },
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

        if cookie_params:
            for key, value in cookie_params.items():
                response.set_cookie(key, value)

        return response

    @staticmethod
    def json_flash(
        status_code: int,
        detail: str | None = None,
        message: str | None = None,
        category: Literal["success", "info", "warning", "error"] = "info",
        error: bool | None = None,
        json: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        cookie_params: dict[str, Any] | None = None,
    ) -> UJSONResponse:  # type: ignore
        return CustomResponse.json(
            status_code=status_code,
            detail=detail,
            message=message,
            json={**({} if json is None else json), "category": category},
            error=error,
            headers=headers,
            media_type=media_type,
            background=background,
            cookie_params=cookie_params,
        )

    @staticmethod
    def http_code(
        request: Request,
        status_code: int,
        details: str | None = None,
        message: str | None = None,
        error: bool | None = None,
    ) -> _TemplateResponse:
        status_code, content, status = CustomResponse.raw_json(
            status_code=status_code,
            details=details,
            message=message,
            error=error,
        )
        return TEMPLATES.TemplateResponse(
            name="code.j2.html",
            request=request,
            context={
                "content": content,
                "status": {"code": status_code, **status.copy()},
            },
            status_code=status_code,
        )

    @staticmethod
    def template(
        request: Request,
        name: str,
        context: dict[str, Any] | None = None,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        cookie_params: dict[str, Any] | None = None,
    ) -> Jinja2Templates.TemplateResponse:
        response = TEMPLATES.TemplateResponse(
            request=request,
            name=name,
            context=context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

        if cookie_params:
            for key, value in cookie_params.items():
                response.set_cookie(key, value)

        return response

    @staticmethod
    def template_flash(
        request: Request,
        name: str,
    ) -> TemplateFlashInnerCallable:
        def inner(
            message: str,
            category: Literal["success", "info", "warning", "error"] = "info",
            context: dict[str, Any] | None = None,
            status_code: int = 200,
            headers: Mapping[str, str] | None = None,
            media_type: str | None = None,
            background: BackgroundTask | None = None,
            cookie_params: dict[str, Any] | None = None,
        ) -> Jinja2Templates.TemplateResponse:
            if "_messages" not in request.session:
                request.session["_messages"] = []
            request.session["_messages"].append(
                {"message": message, "category": category},
            )

            return CustomResponse.template(
                request=request,
                name=name,
                context=context,
                status_code=status_code,
                headers=headers,
                media_type=media_type,
                background=background,
                cookie_params=cookie_params,
            )

        return inner
