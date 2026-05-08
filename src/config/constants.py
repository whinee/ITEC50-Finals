from pathlib import Path
from typing import TypeVar

from alltheutils.config import read_conf_file
from pydantic import BaseModel, TypeAdapter

from src.models.strings import Strings

BM = TypeVar("BM", bound=BaseModel)


def load_constants[BM: BaseModel](raw_path: str, model: type[BM]) -> BM:
    type_adapter = TypeAdapter(model)  # type: ignore

    path = Path(raw_path)

    if not path.exists():
        raise RuntimeError(f"Missing constants file: {path}")

    data = read_conf_file(raw_path)

    if not isinstance(data, dict):
        raise RuntimeError(f"`{raw_path}` must contain a mapping")

    return type_adapter.validate_python(data)


STRINGS = load_constants("src/api/config/values/strings.yml", Strings)
