import os

from mcp_core.config.models import AppConfig, BaseConnectionConfig, CoreSettings


class DummyConnectionConfig(BaseConnectionConfig):
    host: str
    port: int = 22


def test_base_connection_config_is_a_pydantic_model():
    conn = DummyConnectionConfig(host="example.com")
    assert conn.host == "example.com"
    assert conn.port == 22


def test_core_settings_defaults():
    settings = CoreSettings()
    assert settings.log_level == "INFO"


def test_core_settings_env_override(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = CoreSettings()
    assert settings.log_level == "DEBUG"


def test_app_config_generic_over_connection_type():
    raw = {
        "connections": {"server1": {"host": "example.com", "port": 2222}},
        "settings": {},
    }
    config = AppConfig[DummyConnectionConfig, CoreSettings].model_validate(raw)
    assert config.connections["server1"].host == "example.com"
    assert config.connections["server1"].port == 2222
    assert isinstance(config.settings, CoreSettings)
