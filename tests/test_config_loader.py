import pytest
from pydantic import BaseModel

from mcp_core.config.loader import load_config
from mcp_core.config.models import BaseConnectionConfig
from mcp_core.errors import MissingEnvError


class AuthConfig(BaseModel):
    method: str
    password_env: str | None = None


class HostConfig(BaseConnectionConfig):
    host: str
    auth: AuthConfig


def test_load_config_reads_yaml_and_validates(tmp_path, monkeypatch):
    monkeypatch.setenv("HOST1_PASS", "secret")
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text(
        """
connections:
  server1:
    host: example.com
    auth:
      method: password
      password_env: HOST1_PASS
""",
        encoding="utf-8",
    )

    config = load_config(str(yaml_path), connection_model=HostConfig)

    assert config.connections["server1"].host == "example.com"


def test_load_config_raises_missing_env_error(tmp_path, monkeypatch):
    monkeypatch.delenv("HOST1_PASS", raising=False)
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text(
        """
connections:
  server1:
    host: example.com
    auth:
      method: password
      password_env: HOST1_PASS
""",
        encoding="utf-8",
    )

    with pytest.raises(MissingEnvError) as exc_info:
        load_config(str(yaml_path), connection_model=HostConfig)
    assert exc_info.value.var_name == "HOST1_PASS"


def test_load_config_empty_env_ref_is_skipped(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text(
        """
connections:
  server1:
    host: example.com
    auth:
      method: key
""",
        encoding="utf-8",
    )

    config = load_config(str(yaml_path), connection_model=HostConfig)
    assert config.connections["server1"].auth.password_env is None
