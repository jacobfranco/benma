"""Local ASR command adapters with package-owned JSON runners.

No shell is used and no semantic prompt is accepted. The optional runners own
the stdout JSON contract instead of assuming third-party CLIs provide one.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
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


def funasr_paraformer_adapter(
    model: str = "paraformer-zh",
    *,
    vad_model: str | None = "fsmn-vad",
    punctuation_model: str | None = "ct-punc",
) -> JsonCommandPerceptionAdapter:
    command = [
        sys.executable,
        "-m",
        "benchmark.providers.unknown_target.funasr_runner",
        "--model",
        model,
        "--audio",
        "{audio}",
    ]
    if vad_model is not None:
        command.extend(("--vad-model", vad_model))
    if punctuation_model is not None:
        command.extend(("--punctuation-model", punctuation_model))
    return JsonCommandPerceptionAdapter(
        "funasr",
        model,
        tuple(command),
    )


def whisper_adapter(
    model: str = "turbo", *, condition_on_previous_text: bool = True
) -> JsonCommandPerceptionAdapter:
    return JsonCommandPerceptionAdapter(
        "openai_whisper_local",
        model,
        (
            sys.executable,
            "-m",
            "benchmark.providers.unknown_target.whisper_runner",
            "--model",
            model,
            "--audio",
            "{audio}",
            "--condition-on-previous-text",
            "true" if condition_on_previous_text else "false",
        ),
    )
