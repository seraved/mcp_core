import pytest

from mcp_core.errors import MissingEnvError
from mcp_core.secrets import EnvSecretResolver


def test_get_returns_env_value(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "hunter2")
    resolver = EnvSecretResolver()
    assert resolver.get("MY_SECRET") == "hunter2"


def test_get_raises_missing_env_error(monkeypatch):
    monkeypatch.delenv("UNSET_SECRET", raising=False)
    resolver = EnvSecretResolver()
    with pytest.raises(MissingEnvError) as exc_info:
        resolver.get("UNSET_SECRET")
    assert exc_info.value.var_name == "UNSET_SECRET"
