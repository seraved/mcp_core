from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConnectionConfig(BaseModel):
    """Marker base class. Projects subclass this with their own connection fields
    (e.g. HostConfig for mcp_ssh, DBConnectionConfig for mcp_database)."""


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="allow")

    log_level: str = "INFO"


TConn = TypeVar("TConn", bound=BaseConnectionConfig)


class AppConfig(BaseModel, Generic[TConn]):
    connections: dict[str, TConn]
    settings: CoreSettings = Field(default_factory=CoreSettings)
