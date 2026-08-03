"""Optional JSON stdout runner for FunASR's current ``AutoModel`` API."""

from __future__ import annotations

import argparse
import json
from typing import Any


def run(
    model_name: str,
    audio: str,
    *,
    vad_model: str | None,
    punctuation_model: str | None,
) -> dict[str, Any]:
    try:
        from funasr import AutoModel  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional local package
        raise SystemExit("install the optional funasr package to use this runner") from exc

    model = AutoModel(
        model=model_name,
        vad_model=vad_model,
        punc_model=punctuation_model,
        disable_update=True,
        disable_pbar=True,
    )
    generated = model.generate(input=audio, batch_size_s=300)
    results = generated if isinstance(generated, list) else []
    transcript = "".join(
        item.get("text", "") for item in results if isinstance(item, dict)
    )
    return {
        "text": transcript,
        "results": results,
        "configuration": {
            "model": model_name,
            "vad_model": vad_model,
            "punctuation_model": punctuation_model,
            "semantic_hints_supplied": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--vad-model")
    parser.add_argument("--punctuation-model")
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.model,
                args.audio,
                vad_model=args.vad_model,
                punctuation_model=args.punctuation_model,
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
