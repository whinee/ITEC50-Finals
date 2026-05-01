from os import getenv

from dotenv import load_dotenv


def load_environment() -> str:
    """Load environment variables and return the active ENV. This must be called exactly once at app startup."""
    env = getenv("ENV", "production")

    if env == "development":
        load_dotenv(".env")

    if env not in {"development", "production", "test"}:
        raise RuntimeError(f"Invalid ENV: {env}")

    return env
