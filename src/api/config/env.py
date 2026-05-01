from os import environ


def require(name: str) -> str:
    value = environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def optional(name: str, default=None):
    return environ.get(name, default)