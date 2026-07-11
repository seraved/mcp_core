from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import TypeVar

from .loader import load_config
from .models import AppConfig, BaseConnectionConfig, CoreSettings

TConn = TypeVar("TConn", bound=BaseConnectionConfig)
TSettings = TypeVar("TSettings", bound=CoreSettings)

OnReload = Callable[[set[str], set[str], set[str], "AppConfig"], Awaitable[None]]


async def watch_config(
    path: str,
    connection_model: type[TConn],
    on_reload: OnReload,
    settings_model: type[TSettings] = CoreSettings,
    poll_interval: float = 5.0,
    env: Mapping[str, str] | None = None,
) -> None:
    last_mtime = Path(path).stat().st_mtime
    known_connections = load_config(
        path, connection_model, settings_model=settings_model, env=env
    ).connections

    while True:
        await asyncio.sleep(poll_interval)
        current_mtime = Path(path).stat().st_mtime
        if current_mtime == last_mtime:
            continue
        last_mtime = current_mtime

        new_config = load_config(path, connection_model, settings_model=settings_model, env=env)
        new_connections = new_config.connections
        new_keys = set(new_connections.keys())
        known_keys = set(known_connections.keys())
        added = new_keys - known_keys
        removed = known_keys - new_keys
        changed = {
            name for name in new_keys & known_keys
            if new_connections[name] != known_connections[name]
        }
        known_connections = new_connections

        if added or removed or changed:
            await on_reload(added, removed, changed, new_config)
