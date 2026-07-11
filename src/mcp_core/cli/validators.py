from __future__ import annotations

import os


def validate_port(val: str) -> bool | str:
    try:
        n = int(val)
    except ValueError:
        return "Must be a number"
    if 1 <= n <= 65535:
        return True
    return "Port must be between 1 and 65535"


def validate_nonempty(val: str) -> bool | str:
    if val.strip():
        return True
    return "Required"


def warn_env_var(name: str) -> None:
    if name and name.strip() and name.strip() not in os.environ:
        print(f"\033[33mWarning: env var '{name.strip()}' not found in current environment.\033[0m")
