from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

import os
import yaml
from pydantic import BaseModel

from ..errors import MissingEnvError
from .models import AppConfig, BaseConnectionConfig

TConn = TypeVar("TConn", bound=BaseConnectionConfig)


def load_config(
    path: str,
    connection_model: type[TConn],
    env: Mapping[str, str] | None = None,
) -> AppConfig[TConn]:
    if env is None:
        env = os.environ
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    config = AppConfig[connection_model].model_validate(raw)
    _check_env_refs(config, env)
    return config


def _check_env_refs(config: AppConfig, env: Mapping[str, str]) -> None:
    for conn in config.connections.values():
        for var in _collect_env_ref_values(conn):
            if var and var not in env:
                raise MissingEnvError(var)


def _collect_env_ref_values(model: BaseModel, depth: int = 0) -> list[str | None]:
    values: list[str | None] = []
    for field_name in type(model).model_fields:
        value = getattr(model, field_name)
        if field_name.endswith("_env"):
            values.append(value)
        elif isinstance(value, BaseModel) and depth < 1:
            values.extend(_collect_env_ref_values(value, depth + 1))
    return values
