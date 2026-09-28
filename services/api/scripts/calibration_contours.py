"""Read persisted calibration evidence; never calls providers or writes to the DB.

Run from services/api: .venv/bin/python scripts/calibration_contours.py --output DIR
Intended labels are report metadata only; they never enter the classifier.
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select

from benma_api.db.models import AcousticRun, PerceivedSpeechAnalysis, PerceptionRun
from benma_api.db.session import get_session_factory
from benma_api.pronunciation.contours import (
    CLASSIFIER_VERSION,
    classify_contour,
    display_contour,
    syllable_contour,
)
from benma_api.pronunciation.diagnostic import diagnostic

SAMPLES = {
    "computer": [
        "c75f00c8-a680-4cf8-a37a-93455a9a14b6",
        "9957925d-83ba-4502-84d7-8adca750b81d",
        "4fbf587d-4960-4f6f-a5db-f15fd883292f",
        "0a512317-7e6d-4a25-bff0-8a7718ecdc44",
    ],
    "mobile": [
        "e7a4c6c9-d081-4590-95eb-b426c169e5ed",
        "2a6fc058-86c9-415a-ac35-8c333bf9d7dd",
        "c7b73e45-f474-4955-9a68-3f59ad032dfc",
        "b7bfdb6a-8d07-4fe1-82ea-132a18afac9a",
    ],
}

FRESH_SAMPLES = {
    "fresh": [
        "4bf0e5af-b0a2-4cde-9fe5-8595e1030983",
        "e64c4f8f-d69b-4245-b38f-e32c2a1b4424",
        "338b4758-5828-40ca-95b3-d5ee7eb30112",
        "02701fde-5dae-49d5-8c61-0d0ea21b8537",
    ]
}


def report(samples: dict[str, list[str]] = SAMPLES) -> list[dict[str, Any]]:
    rows = []
    with get_session_factory()() as db:
        for microphone, identifiers in samples.items():
            for tone, identifier in enumerate(identifiers, 1):
                analysis = db.scalar(
                    select(PerceivedSpeechAnalysis)
                    .where(PerceivedSpeechAnalysis.utterance_id == uuid.UUID(identifier))
                    .order_by(PerceivedSpeechAnalysis.created_at.desc())
                )
                if analysis is None:
                    raise ValueError(f"No persisted analysis: {identifier}")
                acoustic = db.get(AcousticRun, analysis.acoustic_run_id)
                perception = db.get(PerceptionRun, analysis.perception_run_id)
                if acoustic is None or not acoustic.normalized_result or perception is None:
                    raise ValueError(f"Missing evidence: {identifier}")
                raw = acoustic.normalized_result["f0"]
                display = display_contour(raw)
                for syllable in analysis.result["syllables"]:
                    start, end = syllable["start_seconds"], syllable["end_seconds"]
                    contour = syllable_contour(display, start, end)
                    points = [p for segment in contour.segments for p in segment]
                    measured = classify_contour(contour, start, end, raw=raw)
                    rows.append(
                        {
                            "utterance_id": identifier,
                            "safe_diagnostic": diagnostic(db, uuid.UUID(identifier)),
                            "raw_pitch_in_alignment": [
                                {
                                    k: p.get(k)
                                    for k in (
                                        "timestamp_seconds",
                                        "f0_hz",
                                        "voicing_probability",
                                        "quality_usable",
                                    )
                                }
                                for p in raw
                                if start <= p["timestamp_seconds"] < end
                            ],
                            "full_display_in_alignment": contour.model_dump(),
                            "intended_delivery_user_reported": f"ma{tone}",
                            "microphone": microphone,
                            "perceived_text": perception.transcript,
                            "analysis_id": str(analysis.id),
                            "acoustic_run_id": str(acoustic.id),
                            "timing_source": analysis.result.get("timing_source"),
                            "azure_start_seconds": start,
                            "azure_end_seconds": end,
                            "first_reliable_voiced_seconds": points[0].timestamp_seconds,
                            "last_reliable_voiced_seconds": points[-1].timestamp_seconds,
                            "retained_segments": [len(segment) for segment in contour.segments],
                            "persisted_observed": syllable.get("observed_contour"),
                            "recomputed_observed": measured.model_dump(),
                            "recomputed_classifier": CLASSIFIER_VERSION,
                            "five_bin_contour_st": [
                                measured.features[f"bin_{i}_st"] for i in range(1, 6)
                            ],
                            "persisted_latency_ms": {
                                "asr": perception.latency_ms,
                                "acoustics": acoustic.latency_ms,
                                "alignment": analysis.result.get("alignment_latency_ms"),
                                "analysis_wall": analysis.latency_ms,
                                **analysis.result.get("timings_ms", {}),
                            },
                        }
                    )
        # No flush, commit, provider invocation, or rewrite of historical evidence.
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    rows = report(FRESH_SAMPLES if args.fresh else SAMPLES)
    stem = "four-fresh-samples" if args.fresh else "eight-samples"
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{stem}.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Persisted free-Practice calibration evidence",
        "",
        "Intended labels are user-reported delivery, not semantic or pronunciation truth.",
        "Historical evidence was not rewritten. No provider calls were made.",
        "",
        "| Mic / intent | Heard | Azure span (s) | Raw / retained frames |"
        " Full / core coverage |"
        " Before | Local recomputation |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        old, new = row["persisted_observed"], row["recomputed_observed"]
        f = new["features"]
        lines.append(
            f"| {row['microphone']} / {row['intended_delivery_user_reported']} "
            f"| {row['perceived_text']} | {row['azure_start_seconds']:.3f}-"
            f"{row['azure_end_seconds']:.3f} | {f['raw_voiced_frames']:.0f} / "
            f"{f['retained_display_frames']:.0f} | {new['voiced_coverage']:.3f} / "
            f"{f['active_core_coverage']:.3f} | {old['classification']} ({old['reason']}) "
            f"| {new['classification']} ({new['reason']}) |"
        )
    for row in rows:
        f = row["recomputed_observed"]["features"]
        lines.extend(
            [
                "",
                f"## {row['microphone']} / {row['intended_delivery_user_reported']}",
                "",
                f"Utterance: `{row['utterance_id']}`. Heard: {row['perceived_text']}.",
                "",
                f"Reliable timestamps: {row['first_reliable_voiced_seconds']:.4f}-"
                f"{row['last_reliable_voiced_seconds']:.4f} s. "
                f"Retained segment frame counts: {row['retained_segments']}.",
                "",
                "| Measure | Value |",
                "|---|---|",
                *[f"| {key} | {value} |" for key, value in f.items()],
                "",
                f"Five bins (st): {row['five_bin_contour_st']}",
                "",
                f"Persisted server timings (ms): `{json.dumps(row['persisted_latency_ms'])}`",
            ]
        )
    (args.output / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} read-only calibration rows to {args.output}")


if __name__ == "__main__":
    main()
