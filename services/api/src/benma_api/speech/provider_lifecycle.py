"""Auditable provider maturity; capability and calibration scope stay separate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class ProviderLifecycle(StrEnum):
    DOCUMENTED = "documented"
    IMPLEMENTED = "implemented"
    FIXTURE_VALIDATED = "fixture_validated"
    LIVE_VALIDATED = "live_validated"
    PILOT_EVALUATED = "pilot_evaluated"
    CALIBRATED = "calibrated"
    DISQUALIFIED = "disqualified"


class CalibrationMaturity(StrEnum):
    RAW_EVIDENCE = "raw_evidence"
    EXPERIMENTAL = "experimental"
    CALIBRATED = "calibrated"


class CalibrationScope(StrEnum):
    NONE = "none"
    PERSONAL = "personal"
    PILOT_POPULATION = "pilot_population"
    GENERAL = "general"


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    provider: str
    product: str
    mode: str | None
    lifecycle: ProviderLifecycle
    calibration_maturity: CalibrationMaturity = CalibrationMaturity.RAW_EVIDENCE
    calibration_scope: CalibrationScope = CalibrationScope.NONE
    live_run_count: int = 0
    notes: str = ""

    def normalized(self) -> dict[str, Any]:
        return asdict(self)


# Static repository claims only. A real captured run is required before raising a lifecycle
# beyond FIXTURE_VALIDATED. Live/pilot state belongs in generated calibration manifests.
PROVIDER_STATUS: tuple[ProviderStatus, ...] = (
    ProviderStatus(
        "tencent_soe_n",
        "Smart Oral Evaluation-New Age",
        "sentence_tone_detection",
        ProviderLifecycle.FIXTURE_VALIDATED,
        notes="SOE-N product 1774 only; eval_mode=1 and F_TDET=true",
    ),
    ProviderStatus(
        "tencent_soe_n",
        "Smart Oral Evaluation-New Age",
        "pinyin_tone_detection",
        ProviderLifecycle.FIXTURE_VALIDATED,
        notes="SOE-N product 1774 only; eval_mode=8 and F_TDET=true",
    ),
    ProviderStatus(
        "iflytek_ise",
        "Streaming Pronunciation Assessment",
        "mandarin_full_dimension",
        ProviderLifecycle.FIXTURE_VALIDATED,
        notes="Current /v2/open-ise streaming product with full-dimension abilities",
    ),
    ProviderStatus(
        "azure_speech",
        "Pronunciation Assessment zh-CN",
        "scripted_phoneme",
        ProviderLifecycle.FIXTURE_VALIDATED,
    ),
    ProviderStatus(
        "alibaba_ssecp",
        "Smart Science and Education Content Platform",
        "cn.raw.score/cn.word.score",
        ProviderLifecycle.DOCUMENTED,
        notes="Live transport requires purchased access and warrant/SDK provisioning",
    ),
    ProviderStatus(
        "speechsuper",
        "Mandarin Scripted Pronunciation Assessment",
        None,
        ProviderLifecycle.DOCUMENTED,
        notes="Trial credentials and complete accessible API documentation are unavailable",
    ),
)


def provider_status_manifest() -> list[dict[str, Any]]:
    return [status.normalized() for status in PROVIDER_STATUS]
