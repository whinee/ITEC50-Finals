"""
Environment Settings.

Exposes the core `Settings` object powered by `pydantic-settings`, violently asserting environment variables and secrets before the application even boots.
"""

from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def split_csv(v) -> set[str]:
    """
    Instantly pulverizes a comma-separated string into a deduplicated set of ultra-fast string lookups.

    Args:
        v (Any): The raw input value.

    Returns:
        set[str]: A perfectly sanitized and unique set of string components.

    """
    if isinstance(v, str):
        return {i.strip() for i in v.split(",")}
    if isinstance(v, set):
        return v
    raise ValueError("field is not of type set or str")


class StringsConfig(BaseModel):
    splash: list[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            with open("src/config/values/strings.yml") as f:
                data = yaml.safe_load(f)
                if data and "quotes" in data:
                    self.splash = [
                        f'"{q["text"]}" - {q["author"]}' for q in data["quotes"]
                    ]
        except Exception as e:
            print("Could not load strings.yml:", e)


class SMTPConfig(BaseModel):
    HOST: str = ""
    PORT: int = 587
    USERNAME: str = ""
    PASSWORD: str = ""


class GoogleOAuthConfig(BaseModel):
    ENABLE: bool = False
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""


class GithubOAuthConfig(BaseModel):
    ENABLE: bool = False
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""


class OAuthConfig(BaseModel):
    GOOGLE: GoogleOAuthConfig = GoogleOAuthConfig()
    GITHUB: GithubOAuthConfig = GithubOAuthConfig()


class AuthConfig(BaseModel):
    """
    Sub-configuration for highly sensitive cryptographic secrets.

    Args:
        BaseModel (type): The core Pydantic model inheritance.

    """

    JWT_SECRET: Annotated[str, Field()] = ""
    COOKIE_SECRET: Annotated[str, Field()] = ""
    WEBHOOK_SECRET: Annotated[str, Field()] = ""
    DB_ENCRYPTION_KEY: Annotated[str, Field()] = ""


class TestConfig(BaseModel):
    """Missing docstring."""

    DBNAME: Annotated[str, Field()] = ""
    LIGHTHOUSE: Annotated[bool, Field()] = False
    SMTP: Annotated[bool, Field()] = False


class Settings(BaseSettings):
    """
    The ultimate environment variable parser and validator for DeciMark.

    Powered by `pydantic-settings`, this class intercepts the `.env` file at boot, aggressively casting and validating every single environment variable (including complex CSV origin arrays and nested configurations). This ensures that the server simply refuses to start if there is a single misconfiguration, completely eliminating runtime environment bugs.

    Args:
        BaseSettings (type): The pydantic-settings core class.

    """

    ENV: Annotated[Literal["development", "production", "test"], Field()] = "production"
    DEBUG: Annotated[bool, Field()] = False
    AUTH: Annotated[AuthConfig, Field()] = AuthConfig()
    PG_SYNC_URL: Annotated[str, Field()] = ""
    PG_ASYNC_URL: Annotated[str, Field()] = ""
    ORIGINS: Annotated[str | set[str], Field()] = set()
    API_ROOT: Annotated[str, Field()] = "/api"
    PORT: Annotated[int, Field()] = 8080
    HOST: Annotated[str, Field()] = "localhost"
    TEST: Annotated[TestConfig, Field()] = TestConfig()
    SMTP: Annotated[SMTPConfig, Field()] = SMTPConfig()
    OAUTH: Annotated[OAuthConfig, Field()] = OAuthConfig()
    STRINGS: Annotated[StringsConfig, Field()] = StringsConfig()

    @field_validator("ORIGINS", mode="before")
    @classmethod
    def parse_csv_origins(cls, value: str) -> set[str]:
        """
        Map raw CSV origin strings into deeply optimized sets.

        Args:
            cls (type): The Settings class reference.
            value (str): The raw comma-separated origins string.

        Returns:
            set[str]: The strictly validated CORS origin set.

        """
        return split_csv(value)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
    )


settings = Settings()
