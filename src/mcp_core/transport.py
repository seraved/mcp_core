from __future__ import annotations

import hmac
import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response

from .application import MCPApplication


class BearerAuthMiddleware:
    def __init__(self, app, auth_token: str):
        self.app = app
        self._auth_token = auth_token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        authorization = headers.get(b"authorization", b"").decode("latin-1")
        provided = authorization[7:] if authorization.startswith("Bearer ") else ""
        if not hmac.compare_digest(provided, self._auth_token):
            response = Response("Unauthorized", status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def build_sse_asgi_app(app: MCPApplication, auth_token: str) -> Starlette:
    sse_app = app.mcp.sse_app()
    return Starlette(
        routes=sse_app.routes,
        middleware=[Middleware(BearerAuthMiddleware, auth_token=auth_token)],
    )


def build_http_asgi_app(app: MCPApplication, auth_token: str):
    http_app = app.mcp.streamable_http_app()
    http_app.add_middleware(BearerAuthMiddleware, auth_token=auth_token)
    return http_app


def run_stdio_or_network(app: MCPApplication, **fastmcp_run_kwargs) -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport not in ("sse", "http"):
        app.run(**fastmcp_run_kwargs)
        return

    auth_token = os.environ.get("MCP_AUTH_TOKEN", "")
    if not auth_token:
        raise SystemExit(
            "ERROR: MCP_AUTH_TOKEN must be set when running in SSE/HTTP mode. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))

    import uvicorn

    if transport == "http":
        asgi_app = build_http_asgi_app(app, auth_token)
    else:
        asgi_app = build_sse_asgi_app(app, auth_token)
    uvicorn.run(asgi_app, host=host, port=port)
