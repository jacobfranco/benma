"""Append-only assistant generation over persisted conversational evidence."""

from __future__ import annotations

import time
import uuid
from copy import deepcopy

from benma_api.assistant_generation.contracts import (
    AssistantResponseGenerationInput,
    AssistantResponseGenerationPort,
    validate_assistant_generation_evidence,
)
from benma_api.assistant_generation.repository import AssistantGenerationRepository
from benma_api.conversation.context import resolved_user_turn_text
from benma_api.db.models import AssistantGenerationRun
from benma_api.errors import AuthorizationError, BenmaError
from benma_api.speech.raw_evidence import encode_raw_payload


class AssistantGenerationService:
    def __init__(self, repository: AssistantGenerationRepository) -> None:
        self.repository = repository

    def run(
        self,
        *,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        triggering_user_turn_id: uuid.UUID,
        generator: AssistantResponseGenerationPort,
    ) -> AssistantGenerationRun:
        """Generate from persisted state and construct immutable provenance."""
        loaded = self.repository.load_triggering_turn_evidence(
            account_id,
            conversation_id,
            triggering_user_turn_id,
        )
        if loaded is None:
            raise AuthorizationError("triggering conversation turn was not found")
        _, perception, interpretation = loaded
        resolved_text = resolved_user_turn_text(
            perceived_transcript=perception.transcript,
            decision=interpretation.decision,
            inferred_text=interpretation.inferred_text,
        )
        assert perception.transcript is not None
        clarification_alternatives = _clarification_alternatives(
            interpretation.uncertainty
        )
        request = AssistantResponseGenerationInput(
            conversation_context_snapshot=deepcopy(interpretation.context_snapshot),
            perceived_transcript=perception.transcript,
            contextual_decision=interpretation.decision,  # type: ignore[arg-type]
            resolved_semantic_text=resolved_text,
            clarification_alternatives=(
                clarification_alternatives
                if interpretation.decision == "clarify"
                else ()
            ),
            generation_type=(
                "clarification" if interpretation.decision == "clarify" else "reply"
            ),
        )
        input_snapshot = request.snapshot()
        started = time.perf_counter()
        try:
            response = generator.generate(request)
            validate_assistant_generation_evidence(response.evidence, request=request)
        except BenmaError as exc:
            failed = self._base_run(
                account_id=account_id,
                conversation_id=conversation_id,
                triggering_user_turn_id=triggering_user_turn_id,
                generator=generator,
                generation_type=request.generation_type,
                input_snapshot=input_snapshot,
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="failed",
                error_code=exc.code,
                error_message=exc.message,
            )
            self.repository.add_run(failed)
            # The triggering user turn and failed provenance remain durable for retries/audit.
            self.repository.commit()
            raise
        except ValueError as exc:
            # A provider-neutral contract violation is still a malformed provider result.
            from benma_api.errors import ProviderMalformedResponseError

            error = ProviderMalformedResponseError(
                "assistant generator violated its output contract"
            )
            failed = self._base_run(
                account_id=account_id,
                conversation_id=conversation_id,
                triggering_user_turn_id=triggering_user_turn_id,
                generator=generator,
                generation_type=request.generation_type,
                input_snapshot=input_snapshot,
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="failed",
                error_code=error.code,
                error_message=error.message,
            )
            self.repository.add_run(failed)
            self.repository.commit()
            raise error from exc

        raw = encode_raw_payload(response.raw_payload)
        run = self._base_run(
            account_id=account_id,
            conversation_id=conversation_id,
            triggering_user_turn_id=triggering_user_turn_id,
            generator=generator,
            generation_type=request.generation_type,
            input_snapshot=input_snapshot,
            generated_text=response.evidence.generated_text,
            normalized_result=response.evidence.normalized(),
            raw_payload_json=raw.json_value,
            raw_payload_text=raw.text_value,
            raw_payload_sha256=raw.sha256,
            provider_version=response.provider_version,
            latency_ms=round((time.perf_counter() - started) * 1000),
            status="succeeded",
        )
        self.repository.add_run(run)
        return run

    @staticmethod
    def _base_run(
        *,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        triggering_user_turn_id: uuid.UUID,
        generator: AssistantResponseGenerationPort,
        generation_type: str,
        input_snapshot: dict[str, object],
        latency_ms: int,
        status: str,
        generated_text: str | None = None,
        normalized_result: dict[str, str | list[str]] | None = None,
        raw_payload_json: object | None = None,
        raw_payload_text: str | None = None,
        raw_payload_sha256: str | None = None,
        provider_version: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AssistantGenerationRun:
        configuration = deepcopy(generator.generator_configuration)
        model = configuration.get("model")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("assistant generator configuration requires a model")
        return AssistantGenerationRun(
            account_id=account_id,
            conversation_id=conversation_id,
            triggering_user_turn_id=triggering_user_turn_id,
            provider=generator.provider_name,
            product=generator.product_name,
            provider_version=provider_version,
            adapter_version=generator.adapter_version,
            model=model,
            generator_version=generator.generator_version,
            generator_configuration=configuration,
            generation_type=generation_type,
            input_snapshot=deepcopy(input_snapshot),
            generated_text=generated_text,
            normalized_result=deepcopy(normalized_result),
            raw_payload_json=deepcopy(raw_payload_json),
            raw_payload_text=raw_payload_text,
            raw_payload_sha256=raw_payload_sha256,
            latency_ms=latency_ms,
            status=status,
            error_code=error_code,
            error_message=error_message,
        )


def _clarification_alternatives(uncertainty: dict[str, object]) -> tuple[str, ...]:
    """Allowlist only normalized alternatives from persisted contextual evidence."""
    raw = uncertainty.get("alternatives")
    if not isinstance(raw, list):
        return ()
    alternatives: list[str] = []
    for candidate in raw:
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip()
        if normalized and normalized not in alternatives:
            alternatives.append(normalized)
    return tuple(alternatives)
