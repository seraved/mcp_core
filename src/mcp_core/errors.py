from __future__ import annotations


class MCPError(Exception):
    """Base error for all mcp_core-based server failures."""


class ConfigurationError(MCPError):
    pass


class SecretError(MCPError):
    pass


class MissingEnvError(SecretError):
    def __init__(self, var_name: str):
        self.var_name = var_name
        super().__init__(f"Required environment variable is not set: {var_name}")


class ConnectionError(MCPError):
    pass


class ToolError(MCPError):
    pass


class PluginError(MCPError):
    pass
