"""Central capability maturity and provider-candidate status."""

from __future__ import annotations

from typing import Any


def pronunciation_provider_statuses() -> list[dict[str, Any]]:
    return [
        {
            "provider": "azure_speech",
            "product": "pronunciation_assessment_zh-CN",
            "documented": True,
            "implemented": True,
            "fixture_validated": True,
            "live_validated": False,
            "calibrated": False,
            "tone_hypothesis": "unavailable",
        },
        {
            "provider": "tencent",
            "product": "SOE-N",
            "documented": True,
            "implemented": False,
            "fixture_validated": False,
            "live_validated": False,
            "calibrated": False,
        },
        {
            "provider": "iflytek",
            "product": "ISE streaming",
            "documented": True,
            "implemented": False,
            "fixture_validated": False,
            "live_validated": False,
            "calibrated": False,
        },
        {
            "provider": "alibaba",
            "product": "Chinese/Pinyin evaluation",
            "documented": True,
            "implemented": False,
            "fixture_validated": False,
            "live_validated": False,
            "calibrated": False,
        },
        {
            "provider": "speechsuper",
            "product": "Mandarin evaluation",
            "documented": True,
            "implemented": False,
            "fixture_validated": False,
            "live_validated": False,
            "calibrated": False,
        },
    ]
