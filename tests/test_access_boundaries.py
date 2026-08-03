from __future__ import annotations

import pytest

from benchmark.models import KnownTargetAssessmentRequest
from benchmark.providers.base import MissingCredentialsError, UnsupportedConfigurationError
from benchmark.providers.known_target.access_boundaries import (
    IFlytekIseAccessBoundary,
    SpeechSuperAccessBoundary,
    TencentSoenAccessBoundary,
)


@pytest.mark.parametrize(
    "adapter",
    [TencentSoenAccessBoundary(), IFlytekIseAccessBoundary(), SpeechSuperAccessBoundary()],
)
def test_unavailable_known_target_adapters_name_missing_setup(
    adapter,
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    for variable in adapter.required_variables:
        monkeypatch.delenv(variable, raising=False)
    assert recorded_sample.audio
    request = KnownTargetAssessmentRequest(
        sample_id=recorded_sample.sample_id,
        audio=recorded_sample.audio,
        target_text="你好",
    )
    with pytest.raises(MissingCredentialsError) as captured:
        adapter.assess(request)
    for variable in adapter.required_variables:
        assert variable in str(captured.value)


def test_access_boundary_never_fakes_result_when_credentials_exist(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    adapter = TencentSoenAccessBoundary()
    for variable in adapter.required_variables:
        monkeypatch.setenv(variable, "test-only")
    assert recorded_sample.audio
    request = KnownTargetAssessmentRequest(
        sample_id=recorded_sample.sample_id,
        audio=recorded_sample.audio,
        target_text="你好",
    )
    with pytest.raises(UnsupportedConfigurationError, match="raw-schema validation"):
        adapter.assess(request)
