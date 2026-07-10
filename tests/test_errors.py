from errors import (
    MCPError,
    ConfigurationError,
    SecretError,
    MissingEnvError,
    ConnectionError,
    ToolError,
    PluginError,
)


def test_hierarchy():
    assert issubclass(ConfigurationError, MCPError)
    assert issubclass(SecretError, MCPError)
    assert issubclass(MissingEnvError, SecretError)
    assert issubclass(ConnectionError, MCPError)
    assert issubclass(ToolError, MCPError)
    assert issubclass(PluginError, MCPError)


def test_missing_env_error_message():
    exc = MissingEnvError("DB_PASSWORD")
    assert exc.var_name == "DB_PASSWORD"
    assert str(exc) == "Required environment variable is not set: DB_PASSWORD"
