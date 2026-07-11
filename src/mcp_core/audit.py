from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REDACT_RE_KEY_VALUE = re.compile(
    r"(password|passwd|pass|passphrase|token|secret|api[_-]?key|authorization|bearer|"
    r"cookie|session|credential|private[_-]?key|access[_-]?key|client[_-]?secret)"
    r"(\s*[=:]\s*)\S+",
    re.IGNORECASE,
)

_REDACT_RE_URL_USERINFO = re.compile(r"(://[^/\s:@]+):[^/\s@]+@")

_SENSITIVE_KEY_RE = re.compile(
    r"(password|passwd|pass|passphrase|token|secret|api[_-]?key|authorization|bearer|"
    r"cookie|session|credential|private[_-]?key|access[_-]?key|client[_-]?secret)",
    re.IGNORECASE,
)

_warned_paths: set[str] = set()


def _redact(value: str) -> str:
    value = _REDACT_RE_KEY_VALUE.sub(r"\1\2***", value)
    value = _REDACT_RE_URL_USERINFO.sub(r"\1:***@", value)
    return value


def _redact_value(key: str, value: Any) -> Any:
    if _SENSITIVE_KEY_RE.fullmatch(str(key)):
        return "***"
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, dict):
        return {k: _redact_value(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_redact_value(key, v) for v in value)
    if isinstance(value, bytes):
        return _redact(value.decode("utf-8", errors="replace"))
    return value


def _redact_extra(extra: dict) -> dict:
    return {k: _redact_value(k, v) for k, v in extra.items()}


class AuditLogger:
    def __init__(self, log_path: str):
        self._path = Path(log_path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        tool: str,
        status: str,
        duration: float = 0.0,
        **extra,
    ) -> None:
        record: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "status": status,
            "duration": duration,
            "extra": _redact_extra(extra),
        }
        path_str = str(self._path)
        try:
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:
            if path_str not in _warned_paths:
                _warned_paths.add(path_str)
                print(
                    f"[mcp-core] audit write failed for {path_str}: {exc} (further failures silenced)",
                    file=sys.stderr,
                    flush=True,
                )
