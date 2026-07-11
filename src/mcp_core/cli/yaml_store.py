from __future__ import annotations

import os
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def make_yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.default_flow_style = False
    return y


def resolve_config_path(env_var: str, default_filename: str) -> Path:
    env = os.environ.get(env_var)
    if env:
        return Path(env)
    return Path(default_filename)


def load_yaml(path: Path, top_keys: tuple[str, ...] = ("connections", "settings")) -> CommentedMap:
    if not path.exists():
        return CommentedMap({key: CommentedMap() for key in top_keys})
    y = make_yaml()
    with open(path, encoding="utf-8") as fh:
        data = y.load(fh)
    if data is None:
        data = CommentedMap({key: CommentedMap() for key in top_keys})
    for key in top_keys:
        if key not in data or data[key] is None:
            data[key] = CommentedMap()
    return data


def save_yaml(data: CommentedMap, path: Path) -> None:
    y = make_yaml()
    tmp = path.with_suffix(".yaml.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            y.dump(data, fh)
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
