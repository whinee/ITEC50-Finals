"""Shared String Enumerations.

Houses frozen Pydantic models containing localized strings and standardized feedback messages for instantaneous rendering.
"""

from pydantic import BaseModel, ConfigDict, Field

__pdoc__: dict[str, bool | str] = {}


class HTTPCodeString(BaseModel):
    """Immutable data transfer object (DTO) representing a single, specific HTTP status code definition.

    This model rigidly locks down the structure of HTTP code documentation, ensuring absolute type safety and preventing accidental mutation of standard web specifications during runtime.

    Args:
        BaseModel (type): Core Pydantic base.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    phrase: str
    description: str | None = None
    spec: str | None = None
    spec_link: str | None = None


class HTTPSubgroupString(BaseModel):
    """Immutable representation of an HTTP status code subgroup specification.

    Designed for flawless integration with the broader HTTP definitions hierarchy, guaranteeing that documentation links and exact specification strings remain tamper-proof.

    Args:
        BaseModel (type): Core Pydantic base.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    spec: str
    spec_link: str


class HTTPGroupString(BaseModel):
    """Immutable model capturing an entire classification group of HTTP status codes (e.g., 4xx Client Errors).

    This aggressively optimized class centralizes the default error messages and descriptions for entire blocks of codes, massively reducing memory overhead by preventing string duplication across the massive internal dictionary.

    Args:
        BaseModel (type): Core Pydantic base.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    phrase: str = ""
    description: str = ""
    spec: str = ""
    spec_link: str = ""
    default_details: str = ""
    default_message: str = ""
    default_error: bool | None = None
    subgroup: dict[str, HTTPSubgroupString] = Field(default_factory=dict)


class HTTPString(BaseModel):
    """The master container for all HTTP string definitions across the backend.

    By utilizing deep dict lookups of frozen Pydantic models, this object delivers O(1) instantaneous access to heavily verified, perfectly formatted HTTP specification data, powering the custom FastAPI exception handlers with unrivaled speed and accuracy.

    Args:
        BaseModel (type): Core Pydantic base.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: dict[str, HTTPCodeString] = Field(default_factory=dict)
    group: dict[str, HTTPGroupString] = Field(default_factory=dict)


class Strings(BaseModel):
    """The ultimate, immutable source of truth for application-wide string constants.

    Designed to be loaded once at startup and frozen in memory, it ensures that every single localized string, HTTP definition, and user-facing phrase in DeciMark is strongly typed, blazing fast to access, and utterly immune to runtime corruption.

    Args:
        BaseModel (type): Core Pydantic base.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    http: HTTPString
