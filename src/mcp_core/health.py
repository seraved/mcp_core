from __future__ import annotations

from typing import Protocol


class HealthCheck(Protocol):
    async def check(self) -> dict: ...


class HealthAggregator:
    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register(self, name: str, check: HealthCheck) -> None:
        self._checks[name] = check

    async def run(self) -> dict:
        results = {}
        for name, check in self._checks.items():
            results[name] = await check.check()

        overall = "ok" if all(r.get("status") == "ok" for r in results.values()) else "degraded"
        return {"status": overall, "checks": results}
