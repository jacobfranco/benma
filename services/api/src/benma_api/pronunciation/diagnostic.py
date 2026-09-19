"""Read-only development diagnostic: python -m benma_api.pronunciation.diagnostic.

Defaults to the latest utterance, or accepts --utterance-id UUID. No provider
calls or audio reads. Output is deliberately whitelisted and contains the user's
local transcript, but no keys, headers, storage paths, URLs or raw payloads.
"""

from __future__ import annotations

import argparse
import json
import uuid
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from benma_api.config import Settings
from benma_api.db.models import (
    AcousticRun,
    AudioAsset,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    Utterance,
)
from benma_api.pronunciation.perceived import perceived_syllables


def diagnostic(db: Session, utterance_id: uuid.UUID | None = None) -> dict[str, Any]:
    utterance = (
        db.get(Utterance, utterance_id)
        if utterance_id
        else db.scalar(select(Utterance).order_by(Utterance.created_at.desc()).limit(1))
    )
    if utterance is None:
        return {"status": "utterance_not_found"}
    perception = db.scalar(
        select(PerceptionRun)
        .where(PerceptionRun.utterance_id == utterance.id)
        .order_by(PerceptionRun.created_at.desc())
        .limit(1)
    )
    # Prefer the latest analysis of this utterance, identifying its exact source
    # perception explicitly (a later ASR experiment may not yet have an analysis).
    analysis = db.scalar(
        select(PerceivedSpeechAnalysis)
        .where(PerceivedSpeechAnalysis.utterance_id == utterance.id)
        .order_by(PerceivedSpeechAnalysis.created_at.desc())
        .limit(1)
    )
    if analysis:
        perception = db.get(PerceptionRun, analysis.perception_run_id)
    asset = db.get(AudioAsset, utterance.canonical_audio_asset_id)
    acoustic = db.get(AcousticRun, analysis.acoustic_run_id) if analysis else None
    text = perception.transcript or "" if perception else ""
    data = analysis.result if analysis else {}
    syllables = data.get("syllables") or [s.model_dump() for s in perceived_syllables(text, {})]
    return {
        "utterance_id": str(utterance.id),
        "duration_seconds": asset.duration_seconds if asset else None,
        "perception_run_id": str(perception.id) if perception else None,
        "perceived_text": text,
        "han_ratio": round(
            sum("\u3400" <= c <= "\u9fff" for c in text) / max(1, sum(c.isalnum() for c in text)), 3
        ),
        "provider": perception.provider if perception else None,
        "model": perception.product if perception else None,
        "analysis_id": str(analysis.id) if analysis else None,
        "analysis_status": analysis.status if analysis else "not_run",
        "timing_source": data.get("timing_source"),
        "timing_coverage": data.get("timing_coverage"),
        "timing_status": data.get("alignment_status"),
        "acoustic_tracker": acoustic.algorithm if acoustic else None,
        "acoustic_version": acoustic.algorithm_version if acoustic else None,
        "syllables": [
            {
                k: s.get(k)
                for k in (
                    "characters",
                    "pinyin",
                    "lexical_tone",
                    "expected_surface_tone",
                    "surface_rule",
                    "start_seconds",
                    "end_seconds",
                    "timing_source",
                    "observed_contour",
                )
            }
            for s in syllables
        ],
        "latencies_ms": {
            "asr": perception.latency_ms if perception else None,
            "acoustic": acoustic.latency_ms if acoustic else None,
            "alignment": data.get("alignment_latency_ms"),
            "analysis": analysis.latency_ms if analysis else None,
            **data.get("timings_ms", {}),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--utterance-id", type=uuid.UUID)
    args = parser.parse_args()
    settings = Settings()
    if settings.environment == "production":
        parser.error("This command is for a local development database.")
    engine = create_engine(settings.database_url, hide_parameters=True)
    try:
        with Session(engine) as db:
            print(json.dumps(diagnostic(db, args.utterance_id), ensure_ascii=False, indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
