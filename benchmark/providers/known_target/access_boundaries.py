"""Explicit credential/setup boundaries for unvalidated commercial transports.

These classes intentionally do not manufacture results. They make missing setup
machine-checkable while replay fixtures exercise the rest of the harness.
"""

from __future__ import annotations

import os

from benchmark.models import KnownTargetAssessmentRequest, KnownTargetAssessmentResult
from benchmark.providers.base import (
    KnownTargetPronunciationProvider,
    MissingCredentialsError,
    UnsupportedConfigurationError,
)


class _AccessGatedAdapter(KnownTargetPronunciationProvider):
    required_variables: tuple[str, ...]
    setup_document: str = "docs/benchmark/providers.md"

    def assess(
        self, request: KnownTargetAssessmentRequest
    ) -> tuple[KnownTargetAssessmentResult, object]:
        del request
        missing = [name for name in self.required_variables if not os.environ.get(name)]
        if missing:
            raise MissingCredentialsError(f"missing required credentials: {', '.join(missing)}")
        raise UnsupportedConfigurationError(
            f"credentials are present, but live transport/raw-schema validation is pending; "
            f"follow {self.setup_document} and add a redacted response fixture before enabling"
        )


class TencentSoenAccessBoundary(_AccessGatedAdapter):
    provider_name = "tencent"
    product_name = "SOE-N"
    required_variables = (
        "TENCENT_SECRET_ID",
        "TENCENT_SECRET_KEY",
        "TENCENT_SOE_APP_ID",
    )


class IFlytekIseAccessBoundary(_AccessGatedAdapter):
    provider_name = "iflytek"
    product_name = "ISE-streaming"
    required_variables = (
        "IFLYTEK_APP_ID",
        "IFLYTEK_API_KEY",
        "IFLYTEK_API_SECRET",
    )


class SpeechSuperAccessBoundary(_AccessGatedAdapter):
    provider_name = "speechsuper"
    product_name = "mandarin-pronunciation-assessment"
    required_variables = ("SPEECHSUPER_APP_KEY", "SPEECHSUPER_SECRET_KEY")
