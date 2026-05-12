from typing import Any

from fastapi import Request
from pydantic import BaseModel

from src.config.constants import STRINGS
from src.models.strings import HTTPGroupString

# Constants
STATUS_KEY_PRIORITY = ["phrase", "description", "spec", "spec_link"]


def fetch_flash(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


HTTPStrings = STRINGS.http
HTTPCodeStrings = HTTPStrings.code
HTTPGroupStrings = HTTPStrings.group


def get_http_code_group(status_code: int) -> int:
    return status_code // 100


def normalize_http_status(status_code: int) -> int:
    group = get_http_code_group(status_code)
    if group == 1:
        return 200
    if group == 7:
        return 500
    return status_code


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


def get_group_info(code_group: int) -> HTTPGroupString:
    return HTTPGroupStrings.get(str(code_group), HTTPGroupString())


def build_status_meta(status_code: int) -> dict[str, Any]:
    code_key = str(status_code)

    code_info = HTTPCodeStrings.get(code_key, None)
    if code_info is None:
        return {"code": status_code}

    ci, remaining_code_info = extract_prioritized(code_info, STATUS_KEY_PRIORITY)

    group_info = get_group_info(get_http_code_group(status_code))
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


def get_http_code_group_details(
    code_group: int,
    override_details: str | None = None,
) -> str:
    if override_details is None:
        return get_group_info(code_group).default_details
    return override_details


def get_http_code_group_message(
    code_group: int,
    override_message: str | None = None,
) -> str:
    if override_message is None:
        return get_group_info(code_group).default_details
    return override_message


def check_if_http_code_group_error(
    code_group: int,
    default_error: bool | None = None,
) -> bool:
    group_info = get_group_info(code_group)
    if group_info.default_error is None:
        if default_error is None:
            return False
        return default_error
    return group_info.default_error
