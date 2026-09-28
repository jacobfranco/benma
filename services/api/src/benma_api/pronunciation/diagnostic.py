"""Read-only development diagnostic: python -m benma_api.pronunciation.diagnostic.

Defaults to the latest utterance, or accepts --utterance-id UUID. No provider
calls or audio reads. Output is deliberately whitelisted and contains the user's
local transcript, but no keys, headers, storage paths, URLs or raw payloads.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import uuid
from dataclasses import asdict
from itertools import pairwise
from pathlib import Path
from typing import Any, Never

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from benma_api.config import Settings
from benma_api.db.models import (
    AcousticRun,
    AudioAsset,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    PronunciationAttempt,
    Utterance,
)
from benma_api.pronunciation.contours import CLASSIFIER_VERSION, classify_contour, display_contour
from benma_api.pronunciation.evidence_region import select_tone_evidence
from benma_api.pronunciation.laboratory import PronunciationLaboratoryService
from benma_api.pronunciation.perceived import perceived_syllables


class _NoAudioStore:
    """Fail closed if a future result implementation tries to access audio."""

    def put(self, key: str, data: bytes) -> Never:
        raise RuntimeError("Diagnostic must not write audio")

    def read(self, key: str) -> Never:
        raise RuntimeError("Diagnostic must not read audio")

    def path_for_processing(self, key: str) -> Path:
        raise RuntimeError("Diagnostic must not process audio")

    def delete(self, key: str) -> Never:
        raise RuntimeError("Diagnostic must not delete audio")


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
    attempt = db.scalar(
        select(PronunciationAttempt)
        .where(PronunciationAttempt.utterance_id == utterance.id)
        .order_by(PronunciationAttempt.created_at.desc())
    )
    diagnostic_syllables = []
    timing_resolution: dict[str, Any] = {}
    result = None
    if attempt:
        # result() is read-only: use the same evidence lineage/timing validation
        # as the API, never analyze(), which could invoke providers.
        settings = Settings()
        result = PronunciationLaboratoryService(db, _NoAudioStore(), settings).result(
            account_id=attempt.account_id, attempt_id=attempt.id
        )
        acoustic = db.get(AcousticRun, result.acoustic.id) if result.acoustic else None
        timing_resolution = result.overall_evidence.get("timing_resolution", {})
        syllables = [{**s.model_dump(), **(s.timing or {})} for s in result.syllables]
    raw = (acoustic.normalized_result or {}).get("f0", []) if acoustic else []
    display = display_contour(raw)
    for syllable in syllables:
        observed = syllable.get("observed_contour")
        a, b = syllable.get("start_seconds"), syllable.get("end_seconds")
        recomputed = None
        if attempt:
            recomputed = observed  # result() already recomputes with validated timing.
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            recomputed = classify_contour(
                display,
                a,
                b,
                raw=raw,
                timing_reliable=data.get("evidence_status") != "synthetic_replay",
            ).model_dump()
        features = recomputed.get("features", {}) if recomputed else {}
        window = [
            p
            for p in raw
            if isinstance(a, (int, float))
            and isinstance(b, (int, float))
            and a <= p.get("timestamp_seconds", -1) < b
        ]
        voiced = [p for p in window if p.get("f0_hz")]
        strengths = [
            p["voicing_probability"] for p in voiced if p.get("voicing_probability") is not None
        ]
        retained = [
            p
            for segment in display.segments
            for p in segment
            if isinstance(a, (int, float))
            and isinstance(b, (int, float))
            and a <= p.timestamp_seconds < b
        ]
        gaps = [
            y.timestamp_seconds - x.timestamp_seconds
            for x, y in pairwise(retained)
            if y.timestamp_seconds - x.timestamp_seconds > 0.015
        ]
        events = [
            {
                "from_seconds": x["timestamp_seconds"],
                "to_seconds": y["timestamp_seconds"],
                "from_hz": x["f0_hz"],
                "to_hz": y["f0_hz"],
                "jump_st": round(12 * math.log2(y["f0_hz"] / x["f0_hz"]), 4),
            }
            for x, y in pairwise(voiced)
            if 0 < y["timestamp_seconds"] - x["timestamp_seconds"] <= 0.12
            and 9 <= abs(12 * math.log2(y["f0_hz"] / x["f0_hz"])) <= 15
        ]
        uses_region = features.get("evidence_region_selected") == 1
        uses_core = bool(recomputed and recomputed.get("reason") == "sustained_level_after_onset")
        graph = {
            "tone_evidence_region": asdict(select_tone_evidence(raw, a, b))
            if isinstance(a, (int, float)) and isinstance(b, (int, float))
            else None,
            # Measured fallback is distinct from the client's broad-bin graph.
            "primary_display_policy": "classifier_bins_or_segmented_measured_fallback",
            "broad_gesture_bins": [
                {
                    "timestamp_seconds": features.get(
                        f"{'core_bin' if uses_core else 'bin'}_{i}_seconds"
                    ),
                    "normalized_semitones": features.get(
                        f"{'core_bin' if uses_core else 'bin'}_{i}_st"
                    ),
                }
                for i in range(1, 6)
            ],
            "measured_display_basis": "tone_evidence_region"
            if uses_region
            else "reliable_core"
            if uses_core
            else "full_contour",
            "measured_display_start_seconds": features.get(
                "evidence_start_seconds"
                if uses_region
                else "first_reliable_core_seconds"
                if uses_core
                else "first_retained_seconds"
            ),
            "measured_display_end_seconds": features.get(
                "evidence_end_seconds" if uses_region else "last_retained_seconds"
            ),
            "onset_frames_excluded": (
                features.get("retained_display_frames", 0) - features.get("reliable_core_frames", 0)
            )
            if uses_core
            else features.get("excluded_onset_frames", 0)
            if uses_region
            else 0,
            "instability_decision": "unavailable"
            if not features
            else "reject"
            if features.get("tracker_instability_rejected")
            else "pass",
            "instability_decision_reason": (
                "unresolved_or_repeated_large_jumps"
                if features.get("tracker_instability_rejected")
                else "isolated_glitch_removed_coherent_core"
                if features.get("isolated_filtered_glitch")
                else "no_large_jumps"
                if features
                else "insufficient_evidence"
            ),
        }
        diagnostic_syllables.append(
            {
                **{
                    k: syllable.get(k)
                    for k in (
                        "characters",
                        "pinyin",
                        "lexical_tone",
                        "expected_surface_tone",
                        "surface_rule",
                        "start_seconds",
                        "end_seconds",
                        "timing_source",
                    )
                },
                "timing_source": syllable.get("source")
                if attempt
                else syllable.get("timing_source"),
                **graph,
                "timing_resolution": timing_resolution
                if attempt
                else {
                    "source_record_type": "PerceivedSpeechAnalysis",
                    "source_record_id": str(analysis.id) if analysis else None,
                    "reason": data.get("alignment_status"),
                },
                "f0_evidence": {
                    "raw_voiced_frames": len(voiced),
                    "strength_minimum": min(strengths) if strengths else None,
                    "strength_median": statistics.median(strengths) if strengths else None,
                    "octave_events": events,
                    "candidate_frames": sum("pitch_candidates" in p for p in window),
                    "repaired_frame_count": 0,
                    "artifact_rejected_frames": [
                        {
                            k: p.get(k)
                            for k in (
                                "timestamp_seconds",
                                "f0_hz",
                                "selected_f0_hz",
                                "selection_reason",
                            )
                        }
                        for p in window
                        if p.get("selection_reason", "").startswith("terminal_octave")
                    ],
                    "gap_count": len(gaps),
                    "longest_gap_seconds": round(max(gaps, default=0), 4),
                    "gap_policy": "missing_observations_no_interpolation",
                    "low_frequency_contaminated_frames": sum(
                        p.get("low_frequency_contaminated", p.get("quality_usable") is False)
                        for p in voiced
                    ),
                },
                "observed_contour": observed,
                "locally_recomputed_contour": recomputed,
                "classification_decision_path": recomputed.get("reason") if recomputed else None,
                "rejected_rule": recomputed.get("reason")
                if recomputed and recomputed.get("classification") == "unclear"
                else None,
            }
        )
    return {
        "practice_mode": "known_target" if attempt else "free",
        "target_id": str(attempt.target_id) if attempt else None,
        "pronunciation_attempt_id": str(attempt.id) if attempt else None,
        "target": {
            "id": str(result.target.id),
            "persisted_text": result.target.text,
            "normalization": "no_character_substitution",
            "pinyin_syllables": result.target.pinyin_syllables,
            "lexical_tones": result.target.lexical_tones,
            "pinyin_source": result.target.pinyin_source,
            "created_at": result.target.created_at.isoformat(),
            "attempt_target_id": str(attempt.target_id) if attempt else None,
            "attempt_created_at": attempt.created_at.isoformat() if attempt else None,
        }
        if result
        else None,
        "local_classifier_version": CLASSIFIER_VERSION,
        "utterance_id": str(utterance.id),
        "duration_seconds": asset.duration_seconds if asset else None,
        "canonical_audio": {
            "sample_rate_hz": asset.sample_rate_hz,
            "channel_count": asset.channels,
            "sample_width_bits": asset.sample_width_bits,
        }
        if asset
        else None,
        "perception_run_id": str(perception.id) if perception else None,
        "perceived_text": text,
        "han_ratio": round(
            sum("\u3400" <= c <= "\u9fff" for c in text) / max(1, sum(c.isalnum() for c in text)), 3
        ),
        "provider": perception.provider if perception else None,
        "model": perception.product if perception else None,
        "analysis_id": (str(result.interpretation.id) if result.interpretation else None)
        if result
        else str(analysis.id)
        if analysis
        else None,
        "analysis_status": result.overall_evidence["statuses"]["interpretation"]
        if result
        else analysis.status
        if analysis
        else "not_run",
        "known_target_statuses": result.overall_evidence["statuses"] if result else None,
        "observed_contour_basis": "local_known_target_result"
        if result
        else "persisted_free_analysis",
        "timing_source": "+".join(timing_resolution.get("sources", []))
        if result
        else data.get("timing_source"),
        "timing_resolution": timing_resolution if result else None,
        "timing_coverage": data.get("timing_coverage"),
        "timing_status": ("accepted" if timing_resolution.get("accepted") else "rejected")
        if result
        else data.get("alignment_status"),
        "acoustic_tracker": acoustic.algorithm if acoustic else None,
        "acoustic_version": acoustic.algorithm_version if acoustic else None,
        "acoustic_run_id": str(acoustic.id) if acoustic else None,
        "acoustic_created_at": acoustic.created_at.isoformat() if acoustic else None,
        "acoustic_parameters": acoustic.parameters if acoustic else None,
        "audio_evidence": {
            k: (acoustic.normalized_result or {}).get(k)
            for k in (
                "duration_seconds",
                "sample_rate_hz",
                "channel_count",
                "recording_quality",
                "energy_gate",
                "selection",
            )
        }
        if acoustic
        else None,
        "syllables": diagnostic_syllables,
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
