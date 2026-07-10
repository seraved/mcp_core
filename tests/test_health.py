import pytest

from health import HealthAggregator


class OkCheck:
    async def check(self):
        return {"status": "ok"}


class FailingCheck:
    async def check(self):
        return {"status": "error", "detail": "connection refused"}


@pytest.mark.asyncio
async def test_run_reports_ok_when_all_checks_pass():
    aggregator = HealthAggregator()
    aggregator.register("application", OkCheck())

    result = await aggregator.run()

    assert result["status"] == "ok"
    assert result["checks"]["application"]["status"] == "ok"


@pytest.mark.asyncio
async def test_run_reports_degraded_when_any_check_fails():
    aggregator = HealthAggregator()
    aggregator.register("application", OkCheck())
    aggregator.register("ssh_pool", FailingCheck())

    result = await aggregator.run()

    assert result["status"] == "degraded"
    assert result["checks"]["ssh_pool"]["status"] == "error"
