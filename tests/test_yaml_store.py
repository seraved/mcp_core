import os
from pathlib import Path

import pytest
from ruamel.yaml.comments import CommentedMap

from mcp_core.cli.yaml_store import load_yaml, save_yaml, resolve_config_path, make_yaml


def test_make_yaml_settings():
    y = make_yaml()
    assert y.preserve_quotes is True
    assert y.default_flow_style is False


def test_load_yaml_existing(tmp_path):
    f = tmp_path / "data.yaml"
    f.write_text("connections:\n  foo:\n    host: 1.2.3.4\nsettings: {}\n")
    data = load_yaml(f)
    assert data["connections"]["foo"]["host"] == "1.2.3.4"


def test_load_yaml_missing_creates_defaults(tmp_path):
    f = tmp_path / "nonexistent.yaml"
    data = load_yaml(f)
    assert isinstance(data["connections"], CommentedMap)
    assert isinstance(data["settings"], CommentedMap)


def test_load_yaml_missing_top_key(tmp_path):
    f = tmp_path / "data.yaml"
    f.write_text("settings: {}\n")
    data = load_yaml(f)
    assert isinstance(data["connections"], CommentedMap)


def test_load_yaml_custom_top_keys(tmp_path):
    f = tmp_path / "nonexistent.yaml"
    data = load_yaml(f, top_keys=("connections",))
    assert "connections" in data
    assert "settings" not in data


def test_save_yaml_roundtrip(tmp_path):
    f = tmp_path / "data.yaml"
    f.write_text("connections:\n  foo:\n    port: 22\nsettings: {}\n")
    data = load_yaml(f)
    data["connections"]["foo"]["port"] = 2222
    save_yaml(data, f)
    data2 = load_yaml(f)
    assert data2["connections"]["foo"]["port"] == 2222


def test_save_yaml_atomic_no_leftover_tmp(tmp_path):
    f = tmp_path / "data.yaml"
    f.write_text("connections: {}\nsettings: {}\n")
    data = load_yaml(f)
    save_yaml(data, f)
    assert not f.with_suffix(".yaml.tmp").exists()


def test_resolve_config_path_env(tmp_path, monkeypatch):
    p = tmp_path / "custom.yaml"
    p.touch()
    monkeypatch.setenv("MY_CONFIG", str(p))
    assert resolve_config_path("MY_CONFIG", "default.yaml") == p


def test_resolve_config_path_default(monkeypatch):
    monkeypatch.delenv("MY_CONFIG", raising=False)
    result = resolve_config_path("MY_CONFIG", "default.yaml")
    assert result == Path("default.yaml")
