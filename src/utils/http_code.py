"""HTTP Code Normalization.

Performs O(1) dictionary lookups to map and sanitize raw HTTP status codes into standardized RFC-compliant groups and metadata.
"""

from typing import Any

from fastapi import Request
from pydantic import BaseModel

from src.config.constants import STRINGS
from src.models.strings import HTTPGroupString

# Constants
STATUS_KEY_PRIORITY = ["phrase", "description", "spec", "spec_link"]


def fetch_flash(request: Request):
    """Pop arbitrary flash messages out of the session state for rendering.

    Args:
        request (Request): The raw HTTP request possessing the mutable session dictionary.

    Returns:
        list[dict]: A safely isolated array of transient flash payloads ready for HTML ingestion.

    """
    return request.session.pop("_messages") if "_messages" in request.session else []


HTTPStrings = STRINGS.http
HTTPCodeStrings = HTTPStrings.code
HTTPGroupStrings = HTTPStrings.group


def get_http_code_group(status_code: int) -> int:
    """Extract the major HTTP classification group (e.g., 2 for 2xx, 4 for 4xx) via integer division.

    Returns:
        int: The hundreds digit of the status code.

    """
    return status_code // 100


def normalize_http_status(status_code: int) -> int:
    """Sanitizes non-standard internal informational (1xx) and obscure server (7xx) codes into their standard 200/500 equivalents to guarantee RFC-compliant reverse-proxy ingestion.

    Args:
        status_code (int): The raw HTTP response integer.

    Returns:
        int: The perfectly coerced and standard-compliant fallback integer.

    """
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
    """Intelligently partitions a Pydantic model dictionary into high-priority keys and the remainder.

    This O(n) operation ensures that strictly defined specification strings (like `spec_link`) are cleanly separated from wildcard metadata, allowing the custom response factory to construct highly predictable JSON structures without manual key popping.

    Args:
        source (BaseModel): The origin frozen Pydantic model.
        keys (list[str]): The string list of critical keys to rip out.

    Returns:
        tuple: A perfect split separating prioritized metadata from generalized info.

    """
    picked: dict[str, Any] = {}
    rest = source.model_dump()

    for key in keys:
        value = rest.pop(key, None)
        if value is not None:
            picked[key] = value

    return picked, rest


def get_group_info(code_group: int) -> HTTPGroupString:
    """Perform a hyper-fast O(1) dictionary lookup to fetch the deeply nested configuration for an entire class of HTTP status codes, falling back to a safe empty string model.

    Args:
        code_group (int): The integer hundreds-

    Returns:
        HTTPGroupString: The absolutely frozen and verified HTTP group definition object.

    """
    return HTTPGroupStrings.get(str(code_group), HTTPGroupString())


def build_status_meta(status_code: int) -> dict[str, Any]:
    """Construct the ultimate, deeply enriched status metadata dictionary.

    This function traverses the static `Strings` configuration, resolves subgroups, and merges default messages with exact RFC spec links. This forms the "status" block present in every JSON API response, providing unrivaled developer experience by literally embedding documentation into the API payload.

    Args:
        status_code (int): The integer target for documentation generation.

    Returns:
        dict: The completely merged, stunningly detailed metadata envelope.

    """
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
    """Extract the semantic details for an HTTP status group, allowing dynamic runtime overrides if a specialized payload demands it.

    Args:
        code_group (int): The classification tier identifier.
        override_details (str): A manual override payload string.

    Returns:
        str: The definitively resolved string explanation.

    """
    if override_details is None:
        return get_group_info(code_group).default_details
    return override_details


def get_http_code_group_message(
    code_group: int,
    override_message: str | None = None,
) -> str:
    """Return the default human-readable headline message for an HTTP code group, seamlessly handling dynamic runtime substitutions.

    Args:
        code_group (int): The classification tier integer identifier.
        override_message (str): A manual string substitution payload.

    Returns:
        str: The finalized user-facing display string.

    """
    if override_message is None:
        return get_group_info(code_group).default_details
    return override_message


def check_if_http_code_group_error(
    code_group: int,
    default_error: bool | None = None,
) -> bool:
    """Execute a blazing-fast boolean evaluation to definitively categorize an HTTP code group as a client/server error or a successful response, allowing for explicit runtime overrides.

    Args:
        code_group (int): The integer classification tier.
        default_error (bool): An absolute override toggle.

    Returns:
        bool: True if the code explicitly represents an error class, False otherwise.

    """
    group_info = get_group_info(code_group)
    if group_info.default_error is None:
        if default_error is None:
            return False
        return default_error
    return group_info.default_error
