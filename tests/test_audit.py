import json

from audit import AuditLogger


def test_log_writes_jsonl_with_base_fields(tmp_path):
    log_path = tmp_path / "audit.log"
    logger = AuditLogger(str(log_path))

    logger.log(tool="ssh_run", status="allowed", duration=1.5, host="server1", command="ls -la")

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["tool"] == "ssh_run"
    assert record["status"] == "allowed"
    assert record["duration"] == 1.5
    assert record["extra"]["host"] == "server1"
    assert record["extra"]["command"] == "ls -la"
    assert "ts" in record


def test_log_redacts_secrets_in_extra_string_fields(tmp_path):
    log_path = tmp_path / "audit.log"
    logger = AuditLogger(str(log_path))

    logger.log(tool="ssh_run", status="allowed", command="mysql -p secret=hunter2 --host db")

    record = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert "hunter2" not in record["extra"]["command"]
    assert "***" in record["extra"]["command"]


def test_log_appends_multiple_records(tmp_path):
    log_path = tmp_path / "audit.log"
    logger = AuditLogger(str(log_path))

    logger.log(tool="a", status="ok")
    logger.log(tool="b", status="ok")

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2


def test_log_creates_parent_dirs(tmp_path):
    log_path = tmp_path / "nested" / "dir" / "audit.log"
    logger = AuditLogger(str(log_path))

    logger.log(tool="a", status="ok")

    assert log_path.exists()


def test_log_write_failure_is_silenced_after_first_warning(tmp_path, capsys, monkeypatch):
    log_path = tmp_path / "audit.log"
    logger = AuditLogger(str(log_path))

    def broken_open(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", broken_open)

    logger.log(tool="a", status="ok")
    logger.log(tool="a", status="ok")

    captured = capsys.readouterr()
    assert captured.err.count("audit write failed") == 1
