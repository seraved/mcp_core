import pytest
from pydantic import BaseModel

from mcp_core.cli.connection_manager import ConnectionManagerCLI
from mcp_core.config.models import BaseConnectionConfig


class AuthConfig(BaseModel):
    method: str
    password_env: str | None = None


class HostConfig(BaseConnectionConfig):
    host: str
    auth: AuthConfig


def test_add_writes_new_connection_to_yaml(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text("connections: {}\nsettings: {}\n", encoding="utf-8")
    cli = ConnectionManagerCLI(model=HostConfig, config_path=str(yaml_path))

    cli.add("server1", {"host": "example.com", "auth": {"method": "key"}})

    result = cli.list()
    assert result["server1"]["host"] == "example.com"


def test_add_validates_against_model(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text("connections: {}\nsettings: {}\n", encoding="utf-8")
    cli = ConnectionManagerCLI(model=HostConfig, config_path=str(yaml_path))

    with pytest.raises(Exception):
        cli.add("server1", {"host": "example.com"})  # missing required 'auth'


def test_add_with_secret_writes_env_file(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text("connections: {}\nsettings: {}\n", encoding="utf-8")
    env_path = tmp_path / ".env"
    cli = ConnectionManagerCLI(
        model=HostConfig,
        config_path=str(yaml_path),
        secret_fields=["auth.password_env"],
        env_file=str(env_path),
    )

    cli.add(
        "server1",
        {"host": "example.com", "auth": {"method": "password", "password_env": "SERVER1_PASS"}},
        secrets={"SERVER1_PASS": "hunter2"},
    )

    env_content = env_path.read_text(encoding="utf-8")
    assert "SERVER1_PASS=hunter2" in env_content


def test_add_upserts_existing_env_key(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text("connections: {}\nsettings: {}\n", encoding="utf-8")
    env_path = tmp_path / ".env"
    env_path.write_text("SERVER1_PASS=old\nOTHER=keep\n", encoding="utf-8")
    cli = ConnectionManagerCLI(
        model=HostConfig,
        config_path=str(yaml_path),
        secret_fields=["auth.password_env"],
        env_file=str(env_path),
    )

    cli.add(
        "server1",
        {"host": "example.com", "auth": {"method": "password", "password_env": "SERVER1_PASS"}},
        secrets={"SERVER1_PASS": "new"},
    )

    env_content = env_path.read_text(encoding="utf-8")
    assert "SERVER1_PASS=new" in env_content
    assert "SERVER1_PASS=old" not in env_content
    assert "OTHER=keep" in env_content


def test_list_returns_all_connections(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text(
        "connections:\n  server1:\n    host: a.example.com\n    auth:\n      method: key\n"
        "settings: {}\n",
        encoding="utf-8",
    )
    cli = ConnectionManagerCLI(model=HostConfig, config_path=str(yaml_path))

    result = cli.list()

    assert list(result.keys()) == ["server1"]


def test_remove_deletes_connection(tmp_path):
    yaml_path = tmp_path / "hosts.yaml"
    yaml_path.write_text(
        "connections:\n  server1:\n    host: a.example.com\n    auth:\n      method: key\n"
        "settings: {}\n",
        encoding="utf-8",
    )
    cli = ConnectionManagerCLI(model=HostConfig, config_path=str(yaml_path))

    cli.remove("server1")

    assert cli.list() == {}


from typing import Literal, Union

from pydantic import BaseModel

from mcp_core.cli.connection_manager import discriminator_field_name


class KeyAuth(BaseModel):
    method: Literal["key"] = "key"
    key_path: str


class PasswordAuth(BaseModel):
    method: Literal["password"] = "password"
    password_env: str


def test_discriminator_field_name_detects_literal_field():
    assert discriminator_field_name(KeyAuth) == "method"


def test_discriminator_field_name_returns_none_when_absent():
    class Plain(BaseModel):
        host: str

    assert discriminator_field_name(Plain) is None
