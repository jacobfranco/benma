from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import pytest

from benma_api.api import blocking
from benma_api.config import Settings


def test_production_speech_work_uses_bounded_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}

    async def fake_run_sync[ResultT](
        operation: Callable[[], ResultT], *, limiter: object
    ) -> ResultT:
        observed["limiter"] = limiter
        return operation()

    monkeypatch.setattr(blocking.to_thread, "run_sync", fake_run_sync)
    result = asyncio.run(
        blocking.run_bounded_speech_work(
            Settings(environment="development", database_url="sqlite://"), lambda: 7
        )
    )
    assert result == 7
    assert observed["limiter"] is blocking.BLOCKING_SPEECH_LIMITER


def test_replay_tests_do_not_require_a_platform_worker_bridge() -> None:
    settings = Settings(environment="test", database_url="sqlite://")
    assert asyncio.run(blocking.run_bounded_speech_work(settings, lambda: 9)) == 9
