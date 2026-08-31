"""Append contextual hypotheses without changing perception evidence."""

from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

from benma_api.contextual_interpretation.contracts import (
    ContextualInterpretationEvidence,
    ContextualInterpretationInput,
    ContextualInterpretationPort,
    validate_contextual_interpretation_evidence,
)
from benma_api.contextual_interpretation.repository import (
    ContextualInterpretationRepository,
)
from benma_api.db.models import ContextualInterpretationRun, PerceptionRun
from benma_api.errors import AnalysisUnsupportedError, AuthorizationError

NORMALIZED_PERCEPTION_EVIDENCE_FIELDS = (
    "alternatives",
    "tokens",
    "segments",
    "provider_uncertainty",
    "detected_language",
    "evidence_status",
)


def perception_evidence_snapshot(perception: PerceptionRun) -> dict[str, Any]:
    """Copy normalized downstream evidence without exposing provider raw payloads."""
    normalized = perception.normalized_result or {}
    snapshot = {
        field: deepcopy(normalized[field])
        for field in NORMALIZED_PERCEPTION_EVIDENCE_FIELDS
        if field in normalized
    }
    if "alternatives" not in snapshot and perception.alternatives is not None:
        snapshot["alternatives"] = deepcopy(perception.alternatives)
    if (
        "provider_uncertainty" not in snapshot
        and perception.provider_uncertainty is not None
    ):
        snapshot["provider_uncertainty"] = deepcopy(perception.provider_uncertainty)
    return snapshot


class ContextualInterpretationService:
    def __init__(self, repository: ContextualInterpretationRepository) -> None:
        self.repository = repository

    def run(
        self,
        *,
        account_id: uuid.UUID,
        perception_run_id: uuid.UUID,
        context_snapshot: dict[str, Any],
        interpreter: ContextualInterpretationPort,
    ) -> ContextualInterpretationRun:
        """Execute an abstract interpreter over downstream-only inputs and append its evidence."""
        run = self.build_run(
            account_id=account_id,
            perception_run_id=perception_run_id,
            context_snapshot=context_snapshot,
            interpreter=interpreter,
        )
        self.repository.append_run(run)
        return run

    def build_run(
        self,
        *,
        account_id: uuid.UUID,
        perception_run_id: uuid.UUID,
        context_snapshot: dict[str, Any],
        interpreter: ContextualInterpretationPort,
    ) -> ContextualInterpretationRun:
        """Execute interpretation and construct, but do not persist, its evidence run."""
        perception = self._load_perception(account_id, perception_run_id)
        assert perception.transcript is not None
        used_context_snapshot = deepcopy(context_snapshot)
        interpreter_input = ContextualInterpretationInput(
            perception_run_id=perception.id,
            perceived_transcript=perception.transcript,
            perception_evidence_snapshot=perception_evidence_snapshot(perception),
            context_snapshot=deepcopy(used_context_snapshot),
        )
        evidence = interpreter.interpret(interpreter_input)
        validate_contextual_interpretation_evidence(
            evidence,
            perceived_transcript=perception.transcript,
        )
        return self._build_run(
            perception=perception,
            context_snapshot=used_context_snapshot,
            evidence=evidence,
            interpreter=interpreter.interpreter_name,
            interpreter_version=interpreter.interpreter_version,
            interpreter_configuration=interpreter.interpreter_configuration,
        )

    def _load_perception(
        self, account_id: uuid.UUID, perception_run_id: uuid.UUID
    ) -> PerceptionRun:
        perception = self.repository.load_perception(account_id, perception_run_id)
        if perception is None:
            raise AuthorizationError("perception run was not found")
        if perception.transcript is None:
            raise AnalysisUnsupportedError("perception run has no transcript to interpret")
        return perception

    def _build_run(
        self,
        *,
        perception: PerceptionRun,
        context_snapshot: dict[str, Any],
        evidence: ContextualInterpretationEvidence,
        interpreter: str,
        interpreter_version: str,
        interpreter_configuration: dict[str, Any],
    ) -> ContextualInterpretationRun:
        run = ContextualInterpretationRun(
            account_id=perception.account_id,
            perception_run_id=perception.id,
            interpreter=interpreter,
            interpreter_version=interpreter_version,
            interpreter_configuration=deepcopy(interpreter_configuration),
            context_snapshot=deepcopy(context_snapshot),
            decision=evidence.decision,
            inferred_text=evidence.inferred_text,
            uncertainty=deepcopy(evidence.uncertainty),
            clarification_needed=evidence.clarification_needed,
        )
        return run
