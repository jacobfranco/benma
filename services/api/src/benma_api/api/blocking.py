"""Bounded worker boundary for blocking audio and provider operations."""

from __future__ import annotations

from collections.abc import Callable

from anyio import CapacityLimiter, to_thread

from benma_api.config import Settings

BLOCKING_SPEECH_LIMITER = CapacityLimiter(2)


async def run_bounded_speech_work[ResultT](
    settings: Settings, operation: Callable[[], ResultT]
) -> ResultT:
    """Keep CPU, subprocess, filesystem, and sync HTTP work off the event loop.

    The test runtime used by this repository cannot enter AnyIO's worker bridge,
    so deterministic replay operations execute inline there. Development and
    production use the same bounded worker path.
    """

    if settings.environment == "test":
        return operation()
    return await to_thread.run_sync(operation, limiter=BLOCKING_SPEECH_LIMITER)
