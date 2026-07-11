from __future__ import annotations

import os
from collections.abc import Mapping

from .errors import MissingEnvError


class EnvSecretResolver:
    def __init__(self, env: Mapping[str, str] | None = None):
        self._env = env if env is not None else os.environ

    def get(self, var_name: str) -> str:
        value = self._env.get(var_name)
        if value is None:
            raise MissingEnvError(var_name)
        return value
