from __future__ import annotations

from benchmark.models import RunStatus, UnknownTargetPerceptionResult
from benchmark.providers.base import (
    MalformedProviderResponseError,
    MissingCredentialsError,
    UnknownTargetPerceptionProvider,
    UnsupportedConfigurationError,
)
from benchmark.runner import run_unknown_target


class RaisingProvider(UnknownTargetPerceptionProvider):
    provider_name = "fixture"
    product_name = "raiser"

    def __init__(self, error: Exception) -> None:
        self.error = error

    def perceive(self, request):  # type: ignore[no-untyped-def]
        raise self.error


class SuccessProvider(UnknownTargetPerceptionProvider):
    provider_name = "fixture"
    product_name = "success"

    def perceive(self, request):  # type: ignore[no-untyped-def]
        return UnknownTargetPerceptionResult(transcript="你好"), {"verbatim": [1, 2]}


def test_runner_preserves_raw_success(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    run = run_unknown_target(SuccessProvider(), recorded_sample)
    assert run.status == RunStatus.SUCCEEDED
    assert run.raw_response == {"verbatim": [1, 2]}
    assert "target_text" not in run.request_configuration


def test_runner_records_timeout_as_retryable(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    error = UnsupportedConfigurationError("timeout", retryable=True, code="408")
    run = run_unknown_target(RaisingProvider(error), recorded_sample)
    assert run.status == RunStatus.FAILED
    assert run.error and run.error.retryable and run.error.provider_code == "408"


def test_runner_records_malformed_response(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    run = run_unknown_target(
        RaisingProvider(MalformedProviderResponseError("bad response")), recorded_sample
    )
    assert run.error and run.error.error_type == "MalformedProviderResponseError"


def test_runner_records_missing_credentials(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    run = run_unknown_target(RaisingProvider(MissingCredentialsError("missing")), recorded_sample)
    assert run.status == RunStatus.FAILED
    assert run.error and not run.error.retryable
