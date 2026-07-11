from __future__ import annotations

import hmac
import os

import pytest
from starlette.testclient import TestClient

from mcp_core.application import MCPApplication
from mcp_core.transport import run_stdio_or_network


def test_stdio_default_calls_app_run(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    called = {}

    class FakeApp:
        def run(self, **kwargs):
            called["kwargs"] = kwargs

    run_stdio_or_network(FakeApp(), host="127.0.0.1")
    assert called["kwargs"] == {"host": "127.0.0.1"}


def test_sse_without_token_exits(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "sse")
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)

    class FakeApp:
        pass

    with pytest.raises(SystemExit, match="MCP_AUTH_TOKEN"):
        run_stdio_or_network(FakeApp())


def test_sse_middleware_rejects_bad_token_accepts_good(monkeypatch):
    from mcp_core.transport import build_sse_asgi_app

    app = MCPApplication("test-app")

    @app.mcp.tool()
    async def ping() -> str:
        return "pong"

    asgi_app = build_sse_asgi_app(app, auth_token="s3cr3t")
    client = TestClient(asgi_app)

    resp = client.get("/sse", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401

    resp = client.get("/sse", headers={})
    assert resp.status_code == 401


def test_sse_middleware_accepts_good_token(monkeypatch):
    from mcp_core.transport import build_sse_asgi_app

    app = MCPApplication("test-app")

    @app.mcp.tool()
    async def ping() -> str:
        return "pong"

    asgi_app = build_sse_asgi_app(app, auth_token="s3cr3t")
    client = TestClient(asgi_app, raise_server_exceptions=False)

    resp = client.get("/sse", headers={"Authorization": "Bearer s3cr3t"})
    assert resp.status_code != 401
