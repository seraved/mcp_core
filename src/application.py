from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from health import HealthAggregator
from plugins import Plugin


class MCPApplication:
    def __init__(self, name: str):
        self.name = name
        self.mcp = FastMCP(name)
        self.health = HealthAggregator()
        self.plugins: dict[str, Plugin] = {}
        self.registered_tools: list[str] = []

    def load_plugin(self, plugin: Plugin) -> None:
        plugin.register(self)
        self.plugins[plugin.name] = plugin

    def register_tool(self, fn) -> None:
        self.mcp.tool()(fn)
        self.registered_tools.append(fn.__name__)

    def run(self, **kwargs) -> None:
        self.mcp.run(**kwargs)
