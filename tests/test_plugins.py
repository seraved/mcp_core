from mcp_core.plugins import Plugin


class DummyPlugin:
    name = "dummy"

    def register(self, app):
        app.registered = True


def test_dummy_plugin_satisfies_protocol():
    plugin: Plugin = DummyPlugin()
    assert plugin.name == "dummy"

    class FakeApp:
        pass

    fake_app = FakeApp()
    plugin.register(fake_app)
    assert fake_app.registered is True
