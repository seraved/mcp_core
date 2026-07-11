import os

from mcp_core.cli.validators import validate_port, validate_nonempty, warn_env_var


def test_validate_port_valid():
    assert validate_port("22") is True
    assert validate_port("1") is True
    assert validate_port("65535") is True


def test_validate_port_invalid():
    assert validate_port("0") != True
    assert validate_port("65536") != True
    assert validate_port("abc") != True
    assert validate_port("") != True


def test_validate_nonempty():
    assert validate_nonempty("hello") is True
    assert validate_nonempty("") != True
    assert validate_nonempty("   ") != True


def test_warn_env_var_missing(capsys, monkeypatch):
    monkeypatch.delenv("MY_TEST_VAR_XYZ", raising=False)
    warn_env_var("MY_TEST_VAR_XYZ")
    out = capsys.readouterr().out
    assert "MY_TEST_VAR_XYZ" in out
    assert "Warning" in out


def test_warn_env_var_present(capsys, monkeypatch):
    monkeypatch.setenv("MY_TEST_VAR_XYZ", "1")
    warn_env_var("MY_TEST_VAR_XYZ")
    out = capsys.readouterr().out
    assert out == ""


def test_warn_env_var_blank_name(capsys):
    warn_env_var("")
    out = capsys.readouterr().out
    assert out == ""
