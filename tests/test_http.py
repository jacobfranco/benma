from __future__ import annotations

import pytest

from benchmark.providers.base import ProviderAdapterError
from benchmark.providers.http import json_request


def test_http_timeout_is_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise TimeoutError("timed out")

    monkeypatch.setattr("benchmark.providers.http.urlopen", timeout)
    with pytest.raises(ProviderAdapterError) as captured:
        json_request("https://provider.invalid", payload={}, headers={}, timeout=0.1)
    assert captured.value.retryable
