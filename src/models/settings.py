from pydantic import BaseModel, ConfigDict

from src.config.constants import STRINGS
from src.config.env import optional, require
from src.config.loader import load_environment
from src.models.strings import Strings


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Meta
    ENV: str

    # Secrets
    JWT_SECRET: str
    WEBHOOK_SECRET: str

    # Optional config
    DEBUG: bool = False

    # Constants
    STRINGS: Strings = STRINGS


def load_settings() -> Settings:
    env = load_environment()

    return Settings(
        ENV=env,
        JWT_SECRET=require("JWT_SECRET"),
        WEBHOOK_SECRET=require("JWT_SECRET"),
        DEBUG=optional("DEBUG", "false").lower() == "true",
        STRINGS=STRINGS,
    )


settings = load_settings()
