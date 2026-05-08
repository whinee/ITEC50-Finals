from pydantic import BaseModel, ConfigDict, Field

__pdoc__: dict[str, bool | str] = {}


class HTTPCodeString(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phrase: str
    description: str | None = None
    spec: str | None = None
    spec_link: str | None = None

class HTTPSubgroupString(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    spec: str
    spec_link: str

class HTTPGroupString(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phrase: str
    description: str
    spec: str
    spec_link: str
    subgroup: dict[str, HTTPSubgroupString] = Field(default_factory=dict)

class HTTPString(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: dict[str, HTTPCodeString] = Field(default_factory=dict)
    group: dict[str, HTTPGroupString] = Field(default_factory=dict)

class Strings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    http: HTTPString
