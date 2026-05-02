from typing import Any

from fastapi import Request
from fastapi.responses import UJSONResponse
from pydantic import BaseModel
from starlette.templating import Jinja2Templates

from src.api.config.constants import STRINGS
from src.api.models.strings import HTTPGroupString

# Constants
STATUS_KEY_PRIORITY = ["phrase", "description", "spec", "spec_link"]
DEFAULT_DETAILS = {
    1: "Information",
    2: "Success",
    3: "Redirect",
    4: "Client Error",
    5: "Server Error",
    7: "Developer Error",
}
DEFAULT_MESSAGE = {
    4: "The client has erred.",
    5: "The server has erred.",
    7: "Thy underpaid yet overworked developer hath erred.",
}
DEFAULT_ERROR = {
    1: False,
    2: False,
    3: False,
    4: True,
    5: True,
    7: True,
}

def fetch_flash(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


TEMPLATES = Jinja2Templates(directory="src/api/templates")
TEMPLATES.env.globals["fetch_flash"] = fetch_flash


HTTPStrings = STRINGS.http
HTTPCodeStrings = HTTPStrings.code
HTTPGroupStrings = HTTPStrings.group

def normalize_http_status(code: int) -> int:
    group = code // 100
    if group == 1:
        return 200
    if group == 7:
        return 500
    return code

def extract_prioritized(
    source: BaseModel,
    keys: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    picked: dict[str, Any] = {}
    rest = source.model_dump()

    for key in keys:
        value = rest.pop(key, None)
        if value is not None:
            picked[key] = value

    return picked, rest

def build_status_meta(status_code: int) -> dict[str, Any]:
    code_group = str(status_code // 100)
    code_key = str(status_code)

    code_info = HTTPCodeStrings.get(code_key, None)
    if code_info is None:
        return {"code": status_code}

    ci, remaining_code_info = extract_prioritized(code_info, STATUS_KEY_PRIORITY)

    group_info = HTTPGroupStrings.get(code_group, HTTPGroupString(phrase="", description="", spec="", spec_link=""))
    gi, remaining_group = extract_prioritized(group_info, STATUS_KEY_PRIORITY)

    subgroup = group_info.subgroup
    if isinstance(subgroup, dict):
        sg = subgroup.get(code_key[1])
        if sg:
            gi["subgroup"] = sg

    return {
        "code": status_code,
        **ci,
        **remaining_code_info,
        "group": {
            **gi,
            **remaining_group,
        },
    }


class CustomResponse:
    @staticmethod
    def raw_json(
        status_code: int,
        detail: str | None = None,
        message: str | None = None,
        error: bool | None = None,
    ) -> tuple[int, dict[str, Any], dict[str, Any]]:

        code_group = status_code // 100

        if error is None:
            error = DEFAULT_ERROR.get(code_group, False)

        status = build_status_meta(status_code)
        status_code = normalize_http_status(status_code)

        content: dict[str, Any] = {}

        if detail or (detail := DEFAULT_DETAILS.get(code_group)):
            content["detail"] = detail

        if message or (message := DEFAULT_MESSAGE.get(code_group)):
            content["message"] = message

        content["error"] = error

        return status_code, content, status

    @staticmethod
    def json(  # type: ignore[no-untyped-def]
        status_code: int,
        detail: str | None = None,
        message: str | None = None,
        error: bool | None = None,
        json: dict[str, Any] | None = None,
        *args,
        **kwargs,
    ) -> UJSONResponse:
        if json is None:
            json = {}

        status_code, content, status = CustomResponse.raw_json(
            status_code,
            detail,
            message,
            error,
        )

        return UJSONResponse(  # type: ignore[misc]
            *args,
            status_code=status_code,
            content={
                **content,
                **json,
                "status": status,
            },
            **kwargs,
        )

    @staticmethod
    def template(
        request: Request,
        tpl: str,
    ):
        def inner(
            message: str,
            category: str = "primary",
            *args,
            **kwargs,
        ):
            if "_messages" not in request.session:
                request.session["_messages"] = []
            request.session["_messages"].append(
                {"message": message, "category": category},
            )
            return TEMPLATES.TemplateResponse(
                request,
                tpl,
                *args,
                **kwargs,
            )

        return inner

