# CLI Scaffold Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the duplicated YAML I/O, validators, and main-loop scaffold shared by `mcp_ssh/manage_hosts.py` and `mcp_db/manage_connections.py` into `mcp_core.cli`, and rewire both scripts to use it without changing their behavior.

**Architecture:** Three small new modules under `mcp_core/src/mcp_core/cli/`: `yaml_store.py` (YAML load/save/path resolution), `validators.py` (three questionary validator functions), `app.py` (`run_cli_app` main-loop runner). Each consumer script keeps its own thin re-export/wrapper functions with the exact names and signatures its existing tests already import, so no test files need to change imports.

**Tech Stack:** Python, `ruamel.yaml`, `questionary`, `pytest`.

## Global Constraints

- No behavior change: existing scripts must work identically after the refactor (same env vars, same file formats, same prompts).
- `mcp_ssh/tests/test_manage_hosts.py` must pass unmodified — it imports `load_yaml, save_yaml, resolve_config_path, validate_port, validate_hostname, validate_regex, validate_nonempty` from `manage_hosts` with `resolve_config_path()` taking zero arguments.
- Do not migrate `mcp_db/manage_connections.py` onto `ConnectionManagerCLI` — out of scope per spec.
- Do not touch `validate_hostname`, `validate_regex`, `_parse_group_list`, `_maybe_int`, `validate_optional_int`, `_prompt_entry`, or any `do_test` logic — these stay local to each script.

---

### Task 1: `mcp_core.cli.yaml_store`

**Files:**
- Create: `mcp_core/src/mcp_core/cli/yaml_store.py`
- Test: `mcp_core/tests/test_yaml_store.py`

**Interfaces:**
- Produces: `make_yaml() -> YAML`, `resolve_config_path(env_var: str, default_filename: str) -> Path`, `load_yaml(path: Path, top_keys: tuple[str, ...] = ("connections", "settings")) -> CommentedMap`, `save_yaml(data: CommentedMap, path: Path) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# mcp_core/tests/test_yaml_store.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd mcp_core && poetry run pytest tests/test_yaml_store.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mcp_core.cli.yaml_store'`

- [ ] **Step 3: Implement `yaml_store.py`**

```python
# mcp_core/src/mcp_core/cli/yaml_store.py
from __future__ import annotations

import os
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def make_yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.default_flow_style = False
    return y


def resolve_config_path(env_var: str, default_filename: str) -> Path:
    env = os.environ.get(env_var)
    if env:
        return Path(env)
    return Path(default_filename)


def load_yaml(path: Path, top_keys: tuple[str, ...] = ("connections", "settings")) -> CommentedMap:
    if not path.exists():
        return CommentedMap({key: CommentedMap() for key in top_keys})
    y = make_yaml()
    with open(path, encoding="utf-8") as fh:
        data = y.load(fh)
    if data is None:
        data = CommentedMap({key: CommentedMap() for key in top_keys})
    for key in top_keys:
        if key not in data or data[key] is None:
            data[key] = CommentedMap()
    return data


def save_yaml(data: CommentedMap, path: Path) -> None:
    y = make_yaml()
    tmp = path.with_suffix(".yaml.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            y.dump(data, fh)
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd mcp_core && poetry run pytest tests/test_yaml_store.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
cd mcp_core
git add src/mcp_core/cli/yaml_store.py tests/test_yaml_store.py
git commit -m "feat: add shared yaml_store CLI helper to mcp_core"
```

---

### Task 2: `mcp_core.cli.validators`

**Files:**
- Create: `mcp_core/src/mcp_core/cli/validators.py`
- Test: `mcp_core/tests/test_validators.py`

**Interfaces:**
- Produces: `validate_port(val: str) -> bool | str`, `validate_nonempty(val: str) -> bool | str`, `warn_env_var(name: str) -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# mcp_core/tests/test_validators.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd mcp_core && poetry run pytest tests/test_validators.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mcp_core.cli.validators'`

- [ ] **Step 3: Implement `validators.py`**

```python
# mcp_core/src/mcp_core/cli/validators.py
from __future__ import annotations

import os


def validate_port(val: str) -> bool | str:
    try:
        n = int(val)
    except ValueError:
        return "Must be a number"
    if 1 <= n <= 65535:
        return True
    return "Port must be between 1 and 65535"


def validate_nonempty(val: str) -> bool | str:
    if val.strip():
        return True
    return "Required"


def warn_env_var(name: str) -> None:
    if name and name.strip() and name.strip() not in os.environ:
        print(f"\033[33mWarning: env var '{name.strip()}' not found in current environment.\033[0m")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd mcp_core && poetry run pytest tests/test_validators.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
cd mcp_core
git add src/mcp_core/cli/validators.py tests/test_validators.py
git commit -m "feat: add shared validators CLI helper to mcp_core"
```

---

### Task 3: `mcp_core.cli.app`

**Files:**
- Create: `mcp_core/src/mcp_core/cli/app.py`
- Test: `mcp_core/tests/test_app.py`

**Interfaces:**
- Consumes: nothing from Tasks 1-2.
- Produces: `run_cli_app(actions: dict[str, Callable[[], None] | None], bye_msg: str = "Bye.") -> None`.

- [ ] **Step 1: Write the failing tests**

```python
# mcp_core/tests/test_app.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd mcp_core && poetry run pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mcp_core.cli.app'`

- [ ] **Step 3: Implement `app.py`**

```python
# mcp_core/src/mcp_core/cli/app.py
from __future__ import annotations

import sys
from typing import Callable, Optional

import questionary


def run_cli_app(
    actions: dict[str, Optional[Callable[[], None]]],
    bye_msg: str = "Bye.",
) -> None:
    try:
        while True:
            choice = questionary.select("Action:", choices=list(actions.keys())).ask()

            if choice is None or actions[choice] is None:
                break

            actions[choice]()
            print()
    except KeyboardInterrupt:
        print(f"\n{bye_msg}")
        sys.exit(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd mcp_core && poetry run pytest tests/test_app.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd mcp_core
git add src/mcp_core/cli/app.py tests/test_app.py
git commit -m "feat: add shared run_cli_app main-loop helper to mcp_core"
```

---

### Task 4: Rewire `mcp_ssh/manage_hosts.py`

**Files:**
- Modify: `mcp_ssh/manage_hosts.py:1-65` (imports and I/O section), `mcp_ssh/manage_hosts.py:383-419` (`main()` and `if __name__ == "__main__":` block)
- Test: `mcp_ssh/tests/test_manage_hosts.py` (must pass unmodified — do not edit)

**Interfaces:**
- Consumes: `mcp_core.cli.yaml_store.{make_yaml, resolve_config_path, load_yaml, save_yaml}`, `mcp_core.cli.validators.{validate_port, validate_nonempty, warn_env_var}`, `mcp_core.cli.app.run_cli_app`.
- Produces: `manage_hosts.load_yaml`, `manage_hosts.save_yaml`, `manage_hosts.resolve_config_path` (zero-arg wrapper), `manage_hosts.validate_port`, `manage_hosts.validate_nonempty` — same names/signatures the existing test file imports.

- [ ] **Step 1: Replace the I/O section (lines 1-65)**

Replace the block from the top of the file through the end of `resolve_config_path`/`load_yaml`/`save_yaml` (currently lines 1-65: `_make_yaml`, `resolve_config_path`, `load_yaml`, `save_yaml`) with:

```python
#!/usr/bin/env python3
"""Interactive CRUD manager for hosts.yaml."""
from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

import asyncssh
from ruamel.yaml.comments import CommentedMap

import questionary

from mcp_ssh.connection import build_connect_kwargs
from mcp_core.cli.connection_manager import ConnectionManagerCLI
from mcp_core.cli.app import run_cli_app
from mcp_core.cli.validators import validate_port, validate_nonempty, warn_env_var
from mcp_core.cli.yaml_store import load_yaml as _core_load_yaml, save_yaml, resolve_config_path as _core_resolve_config_path
from mcp_core.errors import MCPError
from mcp_ssh.models import HostConfig, Settings


def resolve_config_path() -> Path:
    return _core_resolve_config_path("MCP_SSH_CONFIG", "hosts.yaml")


def load_yaml(path: Path) -> CommentedMap:
    return _core_load_yaml(path)
```

Delete the old `validate_port` and `warn_env_var` function definitions further down the file (they are now imported); keep `validate_hostname`, `validate_regex`, `validate_nonempty` — wait, `validate_nonempty` is now imported too, so delete its old local definition and keep only `validate_hostname` and `validate_regex` as local functions in the validators section.

- [ ] **Step 2: Replace `main()` and the bottom block (former lines 383-419)**

```python
def main() -> None:
    path = resolve_config_path()

    try:
        data = load_yaml(path)
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)

    ACTIONS = {
        "List hosts": lambda: do_list(data),
        "Add host": lambda: do_add(data, path),
        "Edit host": lambda: do_edit(data, path),
        "Delete host": lambda: do_delete(data, path),
        "Test connection": lambda: do_test(data),
        "Exit": None,
    }

    run_cli_app(ACTIONS)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the existing test suite to verify nothing broke**

Run: `cd mcp_ssh && poetry run pytest tests/test_manage_hosts.py -v`
Expected: PASS, same test count as before the change (all imports of `load_yaml, save_yaml, resolve_config_path, validate_port, validate_hostname, validate_regex, validate_nonempty` from `manage_hosts` still resolve).

- [ ] **Step 4: Manual smoke check**

Run: `cd mcp_ssh && poetry run python -c "import manage_hosts; print(manage_hosts.resolve_config_path())"`
Expected: prints `hosts.yaml` (no exception)

- [ ] **Step 5: Commit**

```bash
cd mcp_ssh
git add manage_hosts.py
git commit -m "refactor: use mcp_core.cli scaffold in manage_hosts.py"
```

---

### Task 5: Rewire `mcp_db/manage_connections.py`

**Files:**
- Modify: `mcp_db/manage_connections.py:1-101` (imports and I/O section), `mcp_db/manage_connections.py:304-339` (`main()` and `if __name__ == "__main__":` block)
- Test: Create `mcp_db/tests/test_manage_connections.py`

**Interfaces:**
- Consumes: `mcp_core.cli.yaml_store.{resolve_config_path, load_yaml, save_yaml}`, `mcp_core.cli.validators.{validate_port, validate_nonempty, warn_env_var}`, `mcp_core.cli.app.run_cli_app`.
- Produces: `manage_connections.load_yaml`, `manage_connections.save_yaml`, `manage_connections.resolve_config_path` (zero-arg wrapper) for the new test file to import.

- [ ] **Step 1: Write the new test file first**

```python
# mcp_db/tests/test_manage_connections.py
import os
import sys
from pathlib import Path

import pytest
from ruamel.yaml.comments import CommentedMap

sys.path.insert(0, str(Path(__file__).parent.parent))

from manage_connections import load_yaml, save_yaml, resolve_config_path, validate_port, validate_nonempty


@pytest.fixture
def chdir(tmp_path):
    old = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old)


def test_load_yaml_existing(tmp_path):
    f = tmp_path / "db_connections.yaml"
    f.write_text("connections:\n  mydb:\n    driver: postgresql\n    host: 1.2.3.4\n    port: 5432\nsettings: {}\n")
    data = load_yaml(f)
    assert data["connections"]["mydb"]["driver"] == "postgresql"


def test_save_yaml_roundtrip(tmp_path):
    f = tmp_path / "db_connections.yaml"
    f.write_text("connections:\n  mydb:\n    port: 5432\nsettings: {}\n")
    data = load_yaml(f)
    data["connections"]["mydb"]["port"] = 5433
    save_yaml(data, f)
    data2 = load_yaml(f)
    assert data2["connections"]["mydb"]["port"] == 5433


def test_resolve_config_path_env(tmp_path, monkeypatch):
    p = tmp_path / "custom.yaml"
    p.touch()
    monkeypatch.setenv("MCP_DB_CONFIG", str(p))
    assert resolve_config_path() == p


def test_resolve_config_path_default(monkeypatch, chdir):
    monkeypatch.delenv("MCP_DB_CONFIG", raising=False)
    result = resolve_config_path()
    assert result.name == "db_connections.yaml"


def test_validate_port_valid():
    assert validate_port("5432") is True


def test_validate_port_invalid():
    assert validate_port("abc") != True


def test_validate_nonempty():
    assert validate_nonempty("x") is True
    assert validate_nonempty("") != True
```

- [ ] **Step 2: Run the new test to verify it fails**

Run: `cd mcp_db && poetry run pytest tests/test_manage_connections.py -v`
Expected: FAIL — `manage_connections` still defines its own `load_yaml`/`save_yaml`/`resolve_config_path`/`validate_port`/`validate_nonempty` at this point, so this actually may PASS already for some cases; the real gate is Step 5 below. Note this and proceed to the refactor regardless (test asserts the *contract*, not the *source*).

- [ ] **Step 3: Replace the I/O section (lines 1-101, keep `DRIVERS`/`MODES`/`GROUPS` and `_parse_group_list`/`_maybe_int`/`validate_optional_int`)**

```python
#!/usr/bin/env python3
"""Interactive CRUD manager for db_connections.yaml."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from ruamel.yaml.comments import CommentedMap

import questionary

from secret_resolver import EnvSecretResolver
from mcp_db.drivers.clickhouse_http import ClickHouseDriver
from mcp_db.drivers.postgresql import PostgreSQLDriver
from mcp_core.cli.app import run_cli_app
from mcp_core.cli.validators import validate_port, validate_nonempty, warn_env_var
from mcp_core.cli.yaml_store import load_yaml as _core_load_yaml, save_yaml, resolve_config_path as _core_resolve_config_path

DRIVERS = ["postgresql", "clickhouse_http"]
MODES = ["unrestricted", "readonly", "restricted"]
GROUPS = ["DQL", "DML", "DDL", "DCL"]


def resolve_config_path() -> Path:
    return _core_resolve_config_path("MCP_DB_CONFIG", "db_connections.yaml")


def load_yaml(path: Path) -> CommentedMap:
    return _core_load_yaml(path)


def _maybe_int(val: str) -> int | None:
    val = val.strip()
    return int(val) if val else None


def validate_optional_int(val: str) -> bool | str:
    v = val.strip()
    if not v:
        return True
    if not v.isdigit():
        return "Must be a number"
    return True


def _parse_group_list(val: str) -> list[str]:
    return [g.strip().upper() for g in val.split(",") if g.strip()]
```

Delete the old local `_make_yaml`, `validate_port`, `validate_nonempty`, `warn_env_var` definitions further down (now imported).

- [ ] **Step 4: Replace `main()` and the bottom block (former lines 304-339)**

```python
def main() -> None:
    path = resolve_config_path()

    try:
        data = load_yaml(path)
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)

    ACTIONS = {
        "List connections": lambda: do_list(data),
        "Add connection": lambda: do_add(data, path),
        "Edit connection": lambda: do_edit(data, path),
        "Delete connection": lambda: do_delete(data, path),
        "Test connection": lambda: do_test(data),
        "Exit": None,
    }

    run_cli_app(ACTIONS)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd mcp_db && poetry run pytest tests/test_manage_connections.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Manual smoke check**

Run: `cd mcp_db && poetry run python -c "import manage_connections; print(manage_connections.resolve_config_path())"`
Expected: prints `db_connections.yaml` (no exception)

- [ ] **Step 7: Commit**

```bash
cd mcp_db
git add manage_connections.py tests/test_manage_connections.py
git commit -m "refactor: use mcp_core.cli scaffold in manage_connections.py"
```

---

### Task 6: Full regression pass

**Files:** none (verification only)

- [ ] **Step 1: Run mcp_core's full unit suite**

Run: `cd mcp_core && poetry run pytest`
Expected: all PASS

- [ ] **Step 2: Run mcp_ssh's fast unit suite**

Run: `cd mcp_ssh && poetry run pytest -m "not integration"`
Expected: all PASS

- [ ] **Step 3: Run mcp_db's suite**

Run: `cd mcp_db && poetry run pytest`
Expected: all PASS

- [ ] **Step 4: No commit needed (verification-only task)**
