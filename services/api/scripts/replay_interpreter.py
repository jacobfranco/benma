"""Replay the current interpreter over immutable stored evidence and emit a diff."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from benma_api.config import get_settings
from benma_api.db.models import (
    AcousticRun,
    AlignmentRun,
    AssessmentRun,
    PronunciationAttempt,
    PronunciationInterpretationRun,
    PronunciationTarget,
)
from benma_api.db.session import get_session_factory
from benma_api.pronunciation.interpretation import (
    INTERPRETER_VERSION,
    diff_observations,
    interpret_evidence,
    interpreter_configuration,
)


def _evidence(db: Session, model: type[Any], value: str | None) -> Any | None:
    if not value:
        return None
    try:
        evidence_id = uuid.UUID(value)
    except ValueError:
        return None
    return db.get(model, evidence_id)


def replay(db: Session) -> dict[str, Any]:
    settings = get_settings()
    stored = db.query(PronunciationInterpretationRun).order_by(
        PronunciationInterpretationRun.created_at
    )
    rows: list[dict[str, Any]] = []
    for baseline in stored:
        attempt = db.get(PronunciationAttempt, baseline.pronunciation_attempt_id)
        target = db.get(PronunciationTarget, attempt.target_id) if attempt else None
        if target is None:
            rows.append({"interpretation_run_id": str(baseline.id), "error": "target missing"})
            continue
        identifiers = baseline.input_evidence_run_ids
        assessment = _evidence(db, AssessmentRun, identifiers.get("assessment_run_id"))
        acoustic = _evidence(db, AcousticRun, identifiers.get("acoustic_run_id"))
        alignment = _evidence(db, AlignmentRun, identifiers.get("alignment_run_id"))
        observations, capability = interpret_evidence(
            target=target,
            assessment=assessment,
            acoustic=acoustic,
            alignment=alignment,
            settings=settings,
        )
        rows.append(
            {
                "interpretation_run_id": str(baseline.id),
                "attempt_id": str(baseline.pronunciation_attempt_id),
                "baseline_version": baseline.interpreter_version,
                "baseline_configuration": baseline.interpreter_configuration,
                "replay_version": INTERPRETER_VERSION,
                "replay_configuration": interpreter_configuration(settings),
                "input_evidence_run_ids": identifiers,
                "assessment_raw_payload_sha256": (
                    assessment.raw_payload_sha256 if assessment else None
                ),
                "baseline_capability": baseline.capability_state,
                "replay_capability": capability.value,
                "diff": diff_observations(baseline.structured_observations, observations),
            }
        )
    return {
        "interpreter_version": INTERPRETER_VERSION,
        "interpreter_configuration": interpreter_configuration(settings),
        "stored_interpretation_count": len(rows),
        "changed_count": sum(bool(row.get("diff", {}).get("changed")) for row in rows),
        "replays": rows,
        "mutated_evidence": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benma-replay-interpreter")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    with get_session_factory()() as db:
        result = replay(db)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"replayed {result['stored_interpretation_count']} interpretations; "
        f"{result['changed_count']} changed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
