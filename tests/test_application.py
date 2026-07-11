import pytest

from mcp_core.application import MCPApplication


class DummyPlugin:
    name = "dummy"

    def register(self, app):
        app.register_tool(self.hello)

    def hello(self) -> str:
        return "hi"


def test_load_plugin_registers_tool_and_stores_plugin():
    app = MCPApplication(name="test-app")
    plugin = DummyPlugin()

    app.load_plugin(plugin)

    assert app.plugins["dummy"] is plugin
    assert "hello" in app.registered_tools


def test_register_tool_wraps_fastmcp_tool_decorator():
    app = MCPApplication(name="test-app")

    def my_tool() -> str:
        return "ok"

    app.register_tool(my_tool)

    assert "my_tool" in app.registered_tools


@pytest.mark.asyncio
async def test_health_aggregator_accessible_and_registrable():
    app = MCPApplication(name="test-app")

    class OkCheck:
        async def check(self):
            return {"status": "ok"}

    app.health.register("core", OkCheck())
    result = await app.health.run()

    assert result["status"] == "ok"
