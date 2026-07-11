from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import TypeVar

from .loader import load_config
from .models import AppConfig, BaseConnectionConfig

TConn = TypeVar("TConn", bound=BaseConnectionConfig)

OnReload = Callable[[set[str], set[str], "AppConfig"], Awaitable[None]]


async def watch_config(
    path: str,
    connection_model: type[TConn],
    on_reload: OnReload,
    poll_interval: float = 5.0,
    env: Mapping[str, str] | None = None,
) -> None:
    last_mtime = Path(path).stat().st_mtime
    known_keys: set[str] = set(load_config(path, connection_model, env).connections.keys())

    while True:
        await asyncio.sleep(poll_interval)
        current_mtime = Path(path).stat().st_mtime
        if current_mtime == last_mtime:
            continue
        last_mtime = current_mtime

        new_config = load_config(path, connection_model, env)
        new_keys = set(new_config.connections.keys())
        added = new_keys - known_keys
        removed = known_keys - new_keys
        known_keys = new_keys

        if added or removed:
            await on_reload(added, removed, new_config)
