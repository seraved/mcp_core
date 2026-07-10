import asyncio

import pytest

from config.models import BaseConnectionConfig
from config.reload import watch_config


class HostConfig(BaseConnectionConfig):
    host: str


async def _write(path, content):
    path.write_text(content, encoding="utf-8")


@pytest.mark.asyncio
async def test_watch_config_detects_added_and_removed_connections(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    await _write(
        yaml_path,
        "connections:\n  server1:\n    host: a.example.com\nsettings: {}\n",
    )

    calls = []

    async def on_reload(added, removed, config):
        calls.append((added, removed))

    task = asyncio.create_task(
        watch_config(str(yaml_path), HostConfig, on_reload, poll_interval=0.05)
    )
    await asyncio.sleep(0.1)

    await _write(
        yaml_path,
        "connections:\n  server2:\n    host: b.example.com\nsettings: {}\n",
    )
    await asyncio.sleep(0.2)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert (frozenset({"server2"}), frozenset({"server1"})) in [
        (frozenset(a), frozenset(r)) for a, r in calls
    ]
