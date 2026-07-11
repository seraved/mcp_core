# mcp_core

Shared scaffolding for MCP servers: config, errors, audit, logging, health, plugins.

Not a standalone server — a library other MCP server projects (e.g. `mcp_ssh`) build on.

## Install

```bash
poetry install
```

## Modules (`src/`)

- **application.py** — `MCPApplication`: wraps `mcp.server.fastmcp.FastMCP`, holds a `HealthAggregator` and plugin registry. `load_plugin()`, `register_tool(fn)`, `run(**kwargs)`.
- **plugins.py** — `Plugin` protocol (`name`, `register(app)`).
- **errors.py** — exception hierarchy rooted at `MCPError`: `ConfigurationError`, `SecretError` → `MissingEnvError`, `ConnectionError`, `ToolError`, `PluginError`.
- **secret_resolver.py** — `EnvSecretResolver`: reads secret from env, raises `MissingEnvError` if unset.
- **audit.py** — `AuditLogger(log_path)`: JSON-lines audit log, auto-redacts secrets/passwords/tokens before writing.
- **log.py** — `configure_logging(service, level="INFO")`: structlog JSON logging to stdout.
- **health.py** — `HealthAggregator`: registry of async `HealthCheck`s, `run()` returns `{"status", "checks"}`.
- **config/models.py** — `BaseConnectionConfig`, `CoreSettings` (env-driven), `AppConfig[TConn]`.
- **config/loader.py** — `load_config(path, connection_model, env=None)`: loads YAML into `AppConfig`, validates `*_env` fields exist in environment.
- **config/reload.py** — `watch_config(path, connection_model, on_reload, poll_interval=5.0)`: polls mtime, diffs connections, calls `on_reload(added, removed, new_config)`.
- **cli/connection_manager.py** — `ConnectionManagerCLI(model, config_path, secret_fields=None, env_file=None)`: interactive (questionary) CRUD for a project's `connections` map + secrets `.env` file. No packaged console script — a consuming project calls `.run()` itself.

## Tests

```bash
poetry run pytest
```

(`asyncio_mode = "auto"`, no extra setup for async tests.)
