"""Central capability maturity and provider-candidate status."""

from __future__ import annotations

from typing import Any

from benma_api.speech.provider_lifecycle import provider_status_manifest


def pronunciation_provider_statuses() -> list[dict[str, Any]]:
    return provider_status_manifest()
