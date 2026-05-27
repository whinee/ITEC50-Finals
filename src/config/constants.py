"""
Configuration Constants.

Provides strongly-typed configuration loading utilities that validate YAML configurations into immutable Pydantic models at runtime.
"""

from pathlib import Path
from typing import TypeVar

from alltheutils.config import read_conf_file
from pydantic import BaseModel, TypeAdapter

from src.models.strings import Strings

BM = TypeVar("BM", bound=BaseModel)


def load_constants[BM: BaseModel](raw_path: str, model: type[BM]) -> BM:
    """
    A brutally resilient YAML-to-Pydantic configuration loader.

    This generic function reads static configuration values from disk and aggressively validates them against a frozen Pydantic model. By parsing and freezing strings at server startup, it guarantees zero I/O overhead during API requests and absolute type safety across the entire application lifespan.

    Args: raw_path: The filesystem path to the YAML configuration file. model: The strictly defined Pydantic BaseModel to validate against.

    Returns: BM: A deeply validated, immutable instance of the provided model.
    """
    type_adapter = TypeAdapter(model)  # type: ignore

    path = Path(raw_path)

    if not path.exists():
        raise RuntimeError(f"Missing constants file: {path}")

    data = read_conf_file(raw_path)

    if not isinstance(data, dict):
        raise RuntimeError(f"`{raw_path}` must contain a mapping")

    return type_adapter.validate_python(data)


STRINGS = load_constants("src/config/values/strings.yml", Strings)
