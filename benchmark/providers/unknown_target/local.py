"""Local FunASR and Whisper command adapters.

No shell is used and no semantic prompt is accepted. Commands must emit one
JSON object to stdout with at least a ``text`` field.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import cast

from benchmark.models import UnknownTargetPerceptionRequest, UnknownTargetPerceptionResult
from benchmark.providers.base import (
    MalformedProviderResponseError,
    UnknownTargetPerceptionProvider,
    UnsupportedConfigurationError,
)


class JsonCommandPerceptionAdapter(UnknownTargetPerceptionProvider):
    adapter_version = "1.0.0"

    def __init__(self, provider_name: str, product_name: str, command: tuple[str, ...]) -> None:
        self.provider_name = provider_name
        self.product_name = product_name
        self.command = command

    def perceive(
        self, request: UnknownTargetPerceptionRequest
    ) -> tuple[UnknownTargetPerceptionResult, object]:
        executable = self.command[0]
        if shutil.which(executable) is None:
            raise UnsupportedConfigurationError(f"local executable not found: {executable}")
        args = [part.replace("{audio}", str(request.audio.asset_path)) for part in self.command]
        try:
            completed = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise UnsupportedConfigurationError("local ASR timed out", retryable=True) from exc
        except subprocess.CalledProcessError as exc:
            raise UnsupportedConfigurationError(
                f"local ASR failed: {exc.stderr[-500:]}", code=str(exc.returncode)
            ) from exc
        try:
            raw = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise MalformedProviderResponseError("local ASR did not emit JSON") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            raise MalformedProviderResponseError("local ASR JSON has no text string")
        return UnknownTargetPerceptionResult(transcript=cast(str, raw["text"])), raw


def funasr_paraformer_adapter() -> JsonCommandPerceptionAdapter:
    return JsonCommandPerceptionAdapter(
        "funasr",
        "paraformer-zh",
        ("funasr", "++model=paraformer-zh", "++input={audio}", "++output_format=json"),
    )


def whisper_adapter(model: str = "turbo") -> JsonCommandPerceptionAdapter:
    return JsonCommandPerceptionAdapter(
        "openai_whisper_local",
        model,
        ("whisper", "{audio}", "--model", model, "--language", "zh", "--output_format", "json"),
    )
