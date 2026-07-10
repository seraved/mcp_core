import json

import structlog

from log import configure_logging


def test_configure_logging_emits_json_with_service_field(capsys):
    configure_logging(service="mcp_ssh", level="INFO")
    log = structlog.get_logger()
    log.info("tool_executed", tool="ssh_run", duration=1.2)

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    record = json.loads(line)
    assert record["service"] == "mcp_ssh"
    assert record["tool"] == "ssh_run"
    assert record["event"] == "tool_executed"
    assert record["level"] == "info"
