"""Small opt-in live evaluation using fixed synthetic text, without database/audio reads.

Run from services/api with --output PATH. Makes at most 24 requests, no retries.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from benma_api.assistant_generation.contracts import (
    AssistantResponseGenerationEvidence,
    AssistantResponseGenerationInput,
    validate_assistant_generation_evidence,
)
from benma_api.assistant_generation.factory import build_assistant_response_generator
from benma_api.assistant_generation.openai import (
    SYSTEM_PROMPT as GENERATE_PROMPT,
)
from benma_api.assistant_generation.openai import (
    _GenerationOutput,
    _response_output_text,
)
from benma_api.config import Settings
from benma_api.contextual_interpretation.contracts import (
    ContextualInterpretationEvidence,
    ContextualInterpretationInput,
    validate_contextual_interpretation_evidence,
)
from benma_api.contextual_interpretation.factory import build_contextual_interpreter
from benma_api.contextual_interpretation.openai import (
    PROMPT_VERSION,
    _InterpretationOutput,
)
from benma_api.contextual_interpretation.openai import (
    SYSTEM_PROMPT as INTERPRET_PROMPT,
)
from benma_api.errors import BenmaError

CASES = (
    ("coherent-odd-grammar", "我们可以睡觉一起。", [], "preserve", None),
    (
        "single-reading-near-miss",
        "你好，今天我们聊聊周谋吧。",
        [],
        "infer",
        "你好，今天我们聊聊周末吧。",
    ),
    (
        "ambiguous-reference",
        "明天我们去那里吧。",
        [{"role": "assistant", "text": "明天可以去图书馆，也可以去游泳馆。你想去哪儿？"}],
        "clarify",
        None,
    ),
    (
        "follow-up",
        "我周末喜欢去公园散步。你呢？",
        [
            {"role": "user", "text": "今天我们聊聊周末吧。"},
            {"role": "assistant", "text": "好呀，你周末喜欢做什么？"},
        ],
        "preserve",
        None,
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--combined", action="store_true", help="Research only; never persists runs"
    )
    parser.add_argument(
        "--efforts", nargs="+", choices=["medium", "low", "none"], default=["medium", "low", "none"]
    )
    parser.add_argument(
        "--contextual-near-miss",
        action="store_true",
        help="Additional explicitly supported near miss only",
    )
    args = parser.parse_args()
    settings = Settings()
    report: dict[str, Any] = {
        "prompt_version": PROMPT_VERSION,
        "combined": args.combined,
        "models": {
            "interpretation": settings.openai_contextual_interpretation_model,
            "generation": settings.openai_assistant_generation_model,
        },
        "cases": [],
        "limitations": "One sample per case/effort, not a quality guarantee.",
    }
    cases = (
        CASES
        if not args.contextual_near_miss
        else (
            (
                "context-supported-near-miss",
                "我周末喜欢去公元散步。",
                [{"role": "assistant", "text": "你周末一般去哪儿散步？公园还是河边？"}],
                "infer",
                "我周末喜欢去公园散步。",
            ),
        )
    )
    for effort in args.efforts:
        configured = settings.model_copy(
            update={
                "contextual_interpretation_provider": "openai",
                "assistant_generation_provider": "openai",
                "openai_contextual_interpretation_reasoning_effort": effort,
                "openai_assistant_generation_reasoning_effort": effort,
            }
        )
        interpreter = build_contextual_interpreter(configured)
        generator = build_assistant_response_generator(configured)
        for name, perceived, turns, expected, expected_text in cases:
            context = {"format": "benma.conversation-context", "version": 1, "turns": turns}
            row: dict[str, Any] = {"case": name, "effort": effort, "expected_decision": expected}
            started = time.perf_counter()
            try:
                interpretation_input = ContextualInterpretationInput(
                    perception_run_id=uuid.UUID(int=1),
                    perceived_transcript=perceived,
                    perception_evidence_snapshot={},
                    context_snapshot=context,
                )
                combined_output = None
                if args.combined:
                    combined_output = combined(configured, interpretation_input)
                    parsed = combined_output.interpretation
                    evidence = ContextualInterpretationEvidence(
                        decision=parsed.decision,
                        inferred_text=parsed.inferred_text,
                        uncertainty=parsed.uncertainty.model_dump(),
                        clarification_needed=parsed.clarification_needed,
                    )
                    validate_contextual_interpretation_evidence(
                        evidence, perceived_transcript=perceived
                    )
                else:
                    evidence = interpreter.interpret(interpretation_input)
                row["interpretation_ms"] = round((time.perf_counter() - started) * 1000)
                row["interpretation"] = dataclasses.asdict(evidence)
                row["semantic_pass"] = evidence.decision == expected and (
                    expected_text is None or evidence.inferred_text == expected_text
                )
                request = AssistantResponseGenerationInput(
                    conversation_context_snapshot=context,
                    perceived_transcript=perceived,
                    contextual_decision=evidence.decision,
                    resolved_semantic_text=(
                        None
                        if evidence.decision == "clarify"
                        else perceived
                        if evidence.decision == "preserve"
                        else evidence.inferred_text
                    ),
                    clarification_alternatives=tuple(evidence.uncertainty["alternatives"])
                    if evidence.decision == "clarify"
                    else (),
                    generation_type="clarification" if evidence.decision == "clarify" else "reply",
                )
                started = time.perf_counter()
                if combined_output:
                    output = combined_output.assistant_response
                    generated = AssistantResponseGenerationEvidence(
                        generation_type=output.generation_type,
                        generated_text=output.generated_text,
                        clarification_alternatives_used=tuple(
                            output.clarification_alternatives_used
                        ),
                    )
                    validate_assistant_generation_evidence(generated, request=request)
                    row["combined_ms"] = row.pop("interpretation_ms")
                else:
                    generated = generator.generate(request).evidence
                    row["generation_ms"] = round((time.perf_counter() - started) * 1000)
                row["generation"] = dataclasses.asdict(generated)
                row["generation_contract_pass"] = True
            except (BenmaError, ValueError, httpx.HTTPError) as exc:
                row["error_code"] = exc.code if isinstance(exc, BenmaError) else type(exc).__name__
                row["semantic_pass"] = False
            report["cases"].append(row)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(
                name,
                effort,
                row.get("interpretation_ms", row.get("combined_ms")),
                row.get("generation_ms"),
                row["semantic_pass"],
                row.get("error_code", "ok"),
                flush=True,
            )
    return 0


class CombinedOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    interpretation: _InterpretationOutput
    assistant_response: _GenerationOutput


def combined(settings: Settings, request: ContextualInterpretationInput) -> CombinedOutput:
    assert settings.openai_api_key
    body = {
        "model": settings.openai_contextual_interpretation_model,
        "store": False,
        "instructions": INTERPRET_PROMPT
        + "\n"
        + GENERATE_PROMPT
        + "\n"
        + (
            "Produce interpretation first, then assistant_response. Derive generation_type as "
            "clarification only for clarify, otherwise reply. For preserve resolve to perceived "
            "text; for infer resolve to inferred_text; for clarify meaning is unresolved and "
            "only interpretation.uncertainty.alternatives may be used as candidate phrases. "
            "Conversation history is only the supplied context_snapshot. These rules apply "
            "exactly as in two separate invocations. Return both objects in the supplied schema."
        ),
        "input": json.dumps(
            {
                "perceived_transcript": request.perceived_transcript,
                "perception_evidence_snapshot": request.perception_evidence_snapshot,
                "context_snapshot": request.context_snapshot,
            },
            ensure_ascii=False,
        ),
        "reasoning": {"effort": settings.openai_contextual_interpretation_reasoning_effort},
        "max_output_tokens": 1024,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "combined_research",
                "strict": True,
                "schema": CombinedOutput.model_json_schema(),
            }
        },
    }
    with httpx.Client(timeout=30) as client:
        response = client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"},
            json=body,
        )
        response.raise_for_status()
        return CombinedOutput.model_validate_json(_response_output_text(response.json()))


if __name__ == "__main__":
    raise SystemExit(main())
