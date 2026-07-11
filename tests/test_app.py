import pytest

from mcp_core.cli.app import run_cli_app


def test_run_cli_app_calls_action_then_exits(monkeypatch):
    calls = []

    def action():
        calls.append("called")

    answers = iter(["Do it", "Exit"])

    class FakeSelect:
        def __init__(self, *a, **k):
            pass

        def ask(self):
            return next(answers)

    monkeypatch.setattr("questionary.select", lambda *a, **k: FakeSelect())

    run_cli_app({"Do it": action, "Exit": None})

    assert calls == ["called"]


def test_run_cli_app_exits_on_none_answer(monkeypatch):
    class FakeSelect:
        def ask(self):
            return None

    monkeypatch.setattr("questionary.select", lambda *a, **k: FakeSelect())

    run_cli_app({"Anything": lambda: None})
    # must return without raising or looping forever


def test_run_cli_app_prints_bye_on_keyboard_interrupt(monkeypatch, capsys):
    def action():
        raise KeyboardInterrupt

    answers = iter(["Boom"])

    class FakeSelect:
        def ask(self):
            return next(answers)

    monkeypatch.setattr("questionary.select", lambda *a, **k: FakeSelect())

    with pytest.raises(SystemExit) as exc_info:
        run_cli_app({"Boom": action}, bye_msg="See ya.")

    assert exc_info.value.code == 0
    assert "See ya." in capsys.readouterr().out
