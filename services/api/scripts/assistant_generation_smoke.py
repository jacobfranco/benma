"""Developer-only live smoke for the three assistant-generation decision paths."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from pydantic import ValidationError

from benma_api.assistant_generation.contracts import AssistantResponseGenerationInput
from benma_api.assistant_generation.factory import build_assistant_response_generator
from benma_api.config import Settings
from benma_api.errors import BenmaError


def _context(turns: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "format": "benma.conversation-context",
        "version": 1,
        "turns": turns,
    }


CASES = (
    (
        "infer-buy-fruit",
        AssistantResponseGenerationInput(
            conversation_context_snapshot=_context(
                [{"role": "assistant", "text": "你今天要去超市吗？"}]
            ),
            perceived_transcript="我想卖水果。",
            contextual_decision="infer",
            resolved_semantic_text="我想买水果。",
            clarification_alternatives=(),
            generation_type="reply",
        ),
    ),
    (
        "clarify-unresolved",
        AssistantResponseGenerationInput(
            conversation_context_snapshot=_context([]),
            perceived_transcript="糟妹。",
            contextual_decision="clarify",
            resolved_semantic_text=None,
            clarification_alternatives=(),
            generation_type="clarification",
        ),
    ),
    (
        "preserve-unusual-order",
        AssistantResponseGenerationInput(
            conversation_context_snapshot=_context([]),
            perceived_transcript="我们可以睡觉一起。",
            contextual_decision="preserve",
            resolved_semantic_text="我们可以睡觉一起。",
            clarification_alternatives=(),
            generation_type="reply",
        ),
    ),
)


def main() -> int:
    try:
        settings = Settings(assistant_generation_provider="openai")
    except ValidationError as exc:
        print("BLOCKED_EXTERNAL: OpenAI assistant generation configuration unavailable")
        print(str(exc).splitlines()[0])
        return 2
    generator = build_assistant_response_generator(settings)
    results: list[dict[str, Any]] = []
    for name, request in CASES:
        try:
            response = generator.generate(request)
        except BenmaError as exc:
            print(
                json.dumps(
                    {
                        "status": "provider_error",
                        "case": name,
                        "code": exc.code,
                        "message": exc.message,
                        "retryable": exc.retryable,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1
        results.append(
            {
                "case": name,
                "provider": generator.provider_name,
                "generator_version": generator.generator_version,
                "generator_configuration": generator.generator_configuration,
                "provider_version": response.provider_version,
                "evidence": dataclasses.asdict(response.evidence),
            }
        )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
