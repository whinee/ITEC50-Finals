from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def split_csv(v) -> set[str]:
    if isinstance(v, str):
        return {i.strip() for i in v.split(",")}
    if isinstance(v, set):
        return v
    raise ValueError("field is not of type set or str")


class AuthConfig(BaseModel):
    JWT_SECRET: Annotated[str, Field()] = ""
    COOKIE_SECRET: Annotated[str, Field()] = ""
    WEBHOOK_SECRET: Annotated[str, Field()] = ""


class Settings(BaseSettings):
    DEBUG: Annotated[bool, Field()] = False
    AUTH: Annotated[AuthConfig, Field()] = AuthConfig()
    PG_SYNC_URL: Annotated[str, Field()] = ""
    PG_ASYNC_URL: Annotated[str, Field()] = ""
    ORIGINS: Annotated[str | set[str], Field()] = set()
    API_ROOT: Annotated[str, Field()] = "/api"
    PORT: Annotated[int, Field()] = 8080
    HOST: Annotated[str, Field()] = "localhost"

    @field_validator("ORIGINS", mode="before")
    @classmethod
    def parse_csv_origins(cls, value: str) -> set[str]:
        return split_csv(value)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )


settings = Settings()
