from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .application import MCPApplication


class Plugin(Protocol):
    name: str

    def register(self, app: "MCPApplication") -> None: ...
