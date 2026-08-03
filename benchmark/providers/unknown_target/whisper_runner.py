"""Optional JSON stdout runner for the upstream ``openai-whisper`` package."""

from __future__ import annotations

import argparse
import json
from typing import Any


def _bool(value: str) -> bool:
    normalized = value.casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _segment_evidence(segment: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "id",
        "seek",
        "start",
        "end",
        "text",
        "tokens",
        "temperature",
        "avg_logprob",
        "compression_ratio",
        "no_speech_prob",
    )
    return {field: segment[field] for field in fields if field in segment}


def run(model_name: str, audio: str, *, condition_on_previous_text: bool) -> dict[str, Any]:
    try:
        import whisper  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional local package
        raise SystemExit("install the optional openai-whisper package to use this runner") from exc

    model = whisper.load_model(model_name)
    raw = model.transcribe(
        audio,
        language="zh",
        condition_on_previous_text=condition_on_previous_text,
    )
    return {
        "text": raw.get("text", ""),
        "language": raw.get("language"),
        "segments": [
            _segment_evidence(segment)
            for segment in raw.get("segments", [])
            if isinstance(segment, dict)
        ],
        "configuration": {
            "model": model_name,
            "language": "zh",
            "condition_on_previous_text": condition_on_previous_text,
            "initial_prompt_supplied": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--condition-on-previous-text", type=_bool, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.model,
                args.audio,
                condition_on_previous_text=args.condition_on_previous_text,
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
