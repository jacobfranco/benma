"""Developer-only live contextual interpretation smoke command."""

from __future__ import annotations

import argparse
import dataclasses
import json
import uuid
from typing import Any

from pydantic import ValidationError

from benma_api.config import Settings
from benma_api.contextual_interpretation.contracts import ContextualInterpretationInput
from benma_api.contextual_interpretation.factory import build_contextual_interpreter
from benma_api.errors import BenmaError


def _json_object(value: str) -> dict[str, Any]:
    try:
        parsed: object = json.loads(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("value must be a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="benma-contextual-interpretation-smoke")
    parser.add_argument("--perceived", required=True, help="immutable perceived transcript")
    parser.add_argument("--context-json", required=True, type=_json_object)
    parser.add_argument("--evidence-json", default="{}", type=_json_object)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = Settings(contextual_interpretation_provider="openai")
    except ValidationError as exc:
        print("BLOCKED_EXTERNAL: OpenAI contextual interpretation configuration unavailable")
        print(str(exc).splitlines()[0])
        return 2
    interpreter = build_contextual_interpreter(settings)
    try:
        evidence = interpreter.interpret(
            ContextualInterpretationInput(
                perception_run_id=uuid.uuid4(),
                perceived_transcript=args.perceived,
                perception_evidence_snapshot=args.evidence_json,
                context_snapshot=args.context_json,
            )
        )
    except BenmaError as exc:
        print(
            json.dumps(
                {
                    "status": "provider_error",
                    "code": exc.code,
                    "message": exc.message,
                    "retryable": exc.retryable,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "interpreter": interpreter.interpreter_name,
                "interpreter_version": interpreter.interpreter_version,
                "interpreter_configuration": interpreter.interpreter_configuration,
                "evidence": dataclasses.asdict(evidence),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
