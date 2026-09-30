"""Offline Luilui forensics: imported frozen acoustics, never target-conditioned.

Run with services/api/.venv/bin/python. No network, training, production writes,
audio persistence, or model loading. All T3/T4 test items are selected by identity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import asdict
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api/src"))

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer, _pcm16_mono  # noqa: E402
from benma_api.pronunciation.contours import (  # noqa: E402
    classify_contour,
    display_contour,
    simplify_display,
    syllable_contour,
)
from benma_api.pronunciation.evidence_region import select_tone_evidence  # noqa: E402

EXPERIMENT = ROOT / "docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec"
OUTPUT = ROOT / "docs/research/pronunciation-v2/2026-09-30-luilui-t3-forensics"
SOURCE = "lingualibre:Q301531"


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_analysis_set(manifest, predictions):
    """Selection never reads prediction/correctness; join predictions afterward."""
    selected = sorted(
        (
            r
            for r in manifest
            if r["speaker_id"] == SOURCE
            and r["partition"] == "test"
            and str(r["tone"]) in {"3", "4"}
            and str(r["included"]) == "True"
        ),
        key=lambda r: r["source_asset_id"],
    )
    if Counter(str(r["tone"]) for r in selected) != {"3": 13, "4": 21}:
        raise ValueError("Expected exactly all 13 T3 and all 21 T4 test clips")
    by_id = {r["source_asset_id"]: r for r in predictions}
    if len(by_id) != len(predictions) or len({r["source_asset_id"] for r in selected}) != 34:
        raise ValueError("Duplicate identity")
    result = []
    for row in selected:
        pred = by_id[row["source_asset_id"]]
        if any(row[k] != pred[k] for k in ("speaker_id", "text", "pinyin", "tone")):
            raise ValueError("Frozen prediction metadata mismatch")
        result.append(
            {**row, **{k: pred[k] for k in ("prediction", "p_T1", "p_T2", "p_T3", "p_T4")}}
        )
    return result


def extract(path):
    """The extraction boundary takes only audio: no text, target, or predictions."""
    with tempfile.TemporaryDirectory(prefix="benma-forensics-") as tmp:
        canonical = Path(tmp) / "canonical.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(path),
                "-map",
                "0:a:0",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(canonical),
            ],
            check=True,
        )
        rate, samples = _pcm16_mono(canonical)
        acoustics = PraatAcousticAnalyzer().analyze(canonical)
        duration = len(samples) / rate
        return derive(acoustics, duration) | {
            "canonical_pcm16_wav_sha256": sha256(canonical),
            "peak": max(map(abs, samples)),
        }


def derive(acoustics, duration):
    raw = acoustics["f0"]
    display = display_contour(raw)
    region = select_tone_evidence(raw, 0, duration)
    observed = classify_contour(display, 0, duration, raw=raw, timing_reliable=True)
    evidence = syllable_contour(display, region.start, region.end)
    # Match laboratory.py: full resolution for detail; simplified syllable for Mine.
    simplified = simplify_display(
        syllable_contour(display, 0, duration),
        preserve_seconds=observed.features.get("first_reliable_core_seconds"),
    )
    retained = {p.timestamp_seconds: p for s in evidence.segments for p in s}
    # Preserve a null at EVERY excluded/missing frame. Do not reverse smoothing
    # into Hz and misrepresent it as an original measurement.
    measured = [
        {
            "timestamp_seconds": p["timestamp_seconds"],
            "f0_hz": p["f0_hz"] if p["timestamp_seconds"] in retained else None,
            "smoothed_semitones": retained[p["timestamp_seconds"]].normalized_semitones
            if p["timestamp_seconds"] in retained
            else None,
        }
        for p in raw
    ]
    return {
        "acoustics": acoustics,
        "duration_seconds": duration,
        "evidence_region": asdict(region),
        "observed": observed.model_dump(),
        "filtered_measured_frames": measured,
        "full_display_contour": display.model_dump(),
        "evidence_contour": evidence.model_dump(),
        "syllable_display_contour": simplified.model_dump(),
    }


def analyze_clip(row):
    path = Path(row["local_path"])
    if sha256(path) != row["audio_sha256"]:
        raise ValueError(f"Audio changed: {path}")
    extracted = extract(path)
    # Labels enter ONLY after extraction and all production decisions have ended.
    return {
        "identity": {
            k: row[k]
            for k in ("source_asset_id", "text", "pinyin", "tone", "local_path", "audio_sha256")
        },
        "wav2vec": {
            "prediction": int(row["prediction"]),
            "correct": row["prediction"] == row["tone"],
            **{k: float(row[k]) for k in ("p_T1", "p_T2", "p_T3", "p_T4")},
        },
        **extracted,
    }


def gap_spans(points, key="f0_hz"):
    """Missing frame support, 10-ms hops; internal excludes leading/trailing loss."""
    voiced = [i for i, p in enumerate(points) if p.get(key) is not None]
    spans = []
    i = 0
    while i < len(points):
        if points[i].get(key) is not None:
            i += 1
            continue
        first = i
        while i < len(points) and points[i].get(key) is None:
            i += 1
        spans.append(
            {
                "start": round(points[first]["timestamp_seconds"] - 0.005, 4),
                "end": round(points[i - 1]["timestamp_seconds"] + 0.005, 4),
                "duration": round((i - first) * 0.01, 4),
                "frames": i - first,
                "internal": bool(voiced and first > voiced[0] and i - 1 < voiced[-1]),
            }
        )
    return spans


def mean(values):
    return statistics.fmean(values) if values else None


def shape(points, key, prefix):
    voiced = [(p["timestamp_seconds"], p[key]) for p in points if p.get(key) is not None]
    if not voiced:
        return {}
    times, values = zip(*voiced, strict=True)
    start, end = times[0], times[-1]
    thirds = [
        mean([v for t, v in voiced if min(2, int(3 * (t - start) / max(end - start, 1e-9))) == i])
        for i in range(3)
    ]
    result = {
        "start": values[0],
        "minimum": min(values),
        "maximum": max(values),
        "end": values[-1],
        "range": max(values) - min(values),
        "minimum_position": (times[values.index(min(values))] - start) / max(end - start, 1e-9),
        "first_third": thirds[0],
        "middle_third": thirds[1],
        "final_third": thirds[2],
        "start_to_end": values[-1] - values[0],
        "end_minus_minimum": values[-1] - min(values),
        "voiced_span_seconds": end - start + 0.01,
    }
    if all(v is not None for v in thirds):
        result.update(first_to_middle=thirds[1] - thirds[0], middle_to_final=thirds[2] - thirds[1])
    return {f"{prefix}_{k}": v for k, v in result.items()}


def summarize(clip):
    a, o = clip["acoustics"], clip["observed"]
    raw = a["f0"]
    filtered = clip["filtered_measured_frames"]
    voiced = [p for p in raw if p["f0_hz"] is not None]
    active_gate = max(a["energy_gate"]["threshold_rms"], max(p["energy_rms"] for p in raw) * 0.2)
    active = [p for p in raw if p["energy_rms"] >= active_gate]
    raw_gaps = [g for g in gap_spans(raw) if g["internal"]]
    filtered_gaps = [g for g in gap_spans(filtered) if g["internal"]]
    selected = [p for p in filtered if p["f0_hz"] is not None]
    adjacent = [(x, y) for x, y in pairwise(raw) if x["f0_hz"] and y["f0_hz"]]
    jumps = [abs(12 * math.log2(y["f0_hz"] / x["f0_hz"])) for x, y in adjacent]
    ambiguous = [
        p
        for p in voiced
        if any(
            abs(abs(12 * math.log2(c["frequency_hz"] / p["f0_hz"])) - 12) <= 1
            and c["strength"] >= 0.45
            and c["strength"] >= p["voicing_probability"] - 0.1
            for c in p["pitch_candidates"]
        )
    ]
    row = {
        **clip["identity"],
        **clip["wav2vec"],
        "duration_seconds": clip["duration_seconds"],
        "v1_category": o["classification"],
        "v1_confidence": o["confidence"],
        "v1_reason": o["reason"],
        "recording_quality": a["recording_quality"]["status"],
        "quality_issues": ";".join(a["recording_quality"]["issues"]),
        "rms": a["recording_quality"]["rms"],
        "peak": clip["peak"],
        "clipping_fraction": a["recording_quality"]["clipping_fraction"],
        "silence_fraction": a["recording_quality"]["silence_fraction"],
        "frame_count": len(raw),
        "tracker_missing_frame_count": sum(p["tracker_f0_hz"] is None for p in raw),
        "energy_gated_frame_count": sum(p["energy_gated"] for p in raw),
        "raw_voiced_frame_count": len(voiced),
        "filtered_retained_frame_count": len(selected),
        "filtered_removed_frame_count": len(voiced) - len(selected),
        "voiced_fraction": len(voiced) / len(raw),
        "missing_f0_fraction": 1 - len(voiced) / len(raw),
        "retained_frame_fraction": len(selected) / len(raw),
        "active_missing_fraction": sum(p["f0_hz"] is None for p in active) / len(active)
        if active
        else None,
        "active_gate_rms": active_gate,
        "active_periodicity_mean": mean([p["voicing_probability"] for p in active]),
        "voiced_periodicity_mean": mean([p["voicing_probability"] for p in voiced]),
        "low_confidence_voiced_fraction": sum(p["voicing_probability"] < 0.65 for p in voiced)
        / len(voiced)
        if voiced
        else None,
        "octave_candidate_ambiguity_fraction": len(ambiguous) / len(voiced) if voiced else None,
        "adjacent_f0_delta_median_st": statistics.median(jumps) if jumps else None,
        "adjacent_large_jump_count": sum(j > 6 for j in jumps),
        "f0_median_hz": statistics.median(p["f0_hz"] for p in voiced) if voiced else None,
        "below_100hz_voiced_fraction": sum(p["f0_hz"] < 100 for p in voiced) / len(voiced)
        if voiced
        else None,
        "longest_tracked_period_ms": max(1000 / p["f0_hz"] for p in voiced) if voiced else None,
        "raw_internal_gap_count": len(raw_gaps),
        "raw_internal_gap_seconds": sum(g["duration"] for g in raw_gaps),
        "raw_largest_internal_gap_seconds": max((g["duration"] for g in raw_gaps), default=0),
        "filtered_internal_gap_count": len(filtered_gaps),
        "filtered_internal_gap_seconds": sum(g["duration"] for g in filtered_gaps),
        "filtered_largest_internal_gap_seconds": max(
            (g["duration"] for g in filtered_gaps), default=0
        ),
        "evidence_start": clip["evidence_region"]["start"],
        "evidence_end": clip["evidence_region"]["end"],
        "evidence_method": clip["evidence_region"]["method"],
        **{f"classifier_{k}": v for k, v in o["features"].items()},
        **shape(raw, "f0_hz", "raw_hz"),
        **shape(raw, "normalized_semitones", "raw_st"),
        **shape(filtered, "f0_hz", "retained_hz"),
        **shape(filtered, "smoothed_semitones", "evidence_st"),
    }
    # Fixed diagnostic thirds of the energy-active span; no timing/classifier changes.
    if active:
        first, last = active[0]["timestamp_seconds"], active[-1]["timestamp_seconds"]
        envelope = [p for p in raw if first <= p["timestamp_seconds"] <= last]
        thirds = [
            mean(
                [
                    p["energy_rms"]
                    for p in envelope
                    if min(2, int(3 * (p["timestamp_seconds"] - first) / max(last - first, 1e-9)))
                    == i
                ]
            )
            for i in range(3)
        ]
        row.update(
            energy_active_span_seconds=last - first + 0.01,
            energy_onset_rms=thirds[0],
            energy_middle_rms=thirds[1],
            energy_ending_rms=thirds[2],
            energy_end_start_ratio=thirds[2] / thirds[0] if thirds[0] else None,
        )
    clip["missing_spans"] = {"raw": gap_spans(raw), "filtered": gap_spans(filtered)}
    return row


METRICS = [
    "duration_seconds",
    "voiced_fraction",
    "missing_f0_fraction",
    "retained_frame_fraction",
    "active_missing_fraction",
    "raw_internal_gap_count",
    "raw_internal_gap_seconds",
    "raw_largest_internal_gap_seconds",
    "filtered_internal_gap_count",
    "classifier_tracker_instability_rejected",
    "classifier_maximum_tracker_jump_st",
    "classifier_octave_like_jump_count",
    "f0_median_hz",
    "below_100hz_voiced_fraction",
    "raw_hz_minimum",
    "raw_st_start_to_end",
    "raw_st_first_to_middle",
    "raw_st_middle_to_final",
    "raw_st_minimum_position",
    "evidence_st_first_to_middle",
    "evidence_st_middle_to_final",
    "evidence_st_minimum_position",
    "evidence_st_range",
    "classifier_post_minimum_recovery_st",
    "classifier_voiced_duration_seconds",
    "active_periodicity_mean",
    "voiced_periodicity_mean",
    "low_confidence_voiced_fraction",
    "adjacent_f0_delta_median_st",
    "octave_candidate_ambiguity_fraction",
    "longest_tracked_period_ms",
    "rms",
    "peak",
    "silence_fraction",
    "clipping_fraction",
    "energy_active_span_seconds",
    "energy_onset_rms",
    "energy_middle_rms",
    "energy_ending_rms",
    "energy_end_start_ratio",
]


def distributions(groups):
    import numpy as np

    output = []
    for group, rows in groups.items():
        for metric in METRICS:
            values = [r[metric] for r in rows if r.get(metric) is not None]
            if values:
                output.append(
                    dict(
                        group=group,
                        metric=metric,
                        n=len(values),
                        mean=mean(values),
                        median=statistics.median(values),
                        minimum=min(values),
                        q25=float(np.quantile(values, 0.25)),
                        q75=float(np.quantile(values, 0.75)),
                        maximum=max(values),
                    )
                )
    return output


def run(output=OUTPUT):
    rows = select_analysis_set(
        read_csv(EXPERIMENT / "clean-corpus-manifest.csv"),
        read_csv(EXPERIMENT / "test-results.csv"),
    )
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("drawer-payloads", "plots"):
        (output / folder).mkdir(exist_ok=True)
    write_json(
        output / "selection.json",
        {
            "rule": "All included test items of lingualibre:Q301531 with lexical tone 3 or 4; "
            "sorted asset ID. No prediction selection.",
            "counts": {"T3": 13, "T4": 21},
            "asset_ids": [r["source_asset_id"] for r in rows],
            "manifest_sha256": sha256(EXPERIMENT / "clean-corpus-manifest.csv"),
            "predictions_sha256": sha256(EXPERIMENT / "test-results.csv"),
        },
    )
    clips = [analyze_clip(row) for row in rows]
    summaries = [summarize(c) for c in clips]
    projection = subprocess.run(
        ["node", str(Path(__file__).with_name("drawer_projection.cjs"))],
        input=json.dumps(
            [
                {
                    "display_contour": c["syllable_display_contour"],
                    "observed_contour": c["observed"],
                    "lexical_tone": int(c["identity"]["tone"]),
                }
                for c in clips
            ]
        ),
        text=True,
        capture_output=True,
        check=True,
    )
    from forensics_plots import make_artifacts

    historic = {r["source_asset_id"]: r for r in read_csv(EXPERIMENT / "v1-results.csv")}
    for clip, row, ui in zip(clips, summaries, json.loads(projection.stdout), strict=True):
        clip["drawer_projection"] = ui
        row["drawer_verdict"] = ui["verdict"]
        row["drawer_method"] = ui["primary_contour"]["method"]
        old = historic[row["source_asset_id"]]
        if (row["v1_category"], row["v1_confidence"], row["v1_reason"]) != (
            old["v1_observed"],
            old["v1_ordinal_confidence"],
            old["v1_reason"],
        ):
            raise ValueError("Frozen V1 reproduction mismatch")
        row["frozen_v1_category_confidence_reason_match"] = True
        clip["research_timing"] = {
            "method": "whole isolated clip, known single syllable, no alignment provider",
            "start_seconds": 0,
            "end_seconds": clip["duration_seconds"],
            "production_alignment_reproduced": False,
        }
        clip["drawer_input_subset"] = {
            "note": "Acoustic fields with the mobile API shape; not a live API response. "
            "No provider score, reference audio, IDs, or alignment provenance is fabricated.",
            "target": {"text": row["text"], "display_pinyin": row["pinyin"]},
            "acoustic": {"normalized_result": clip["acoustics"]},
            "display_contour": clip["full_display_contour"],
            "syllables": [
                {
                    "syllable_index": 0,
                    "characters": row["text"],
                    "pinyin": row["pinyin"],
                    "lexical_tone": int(row["tone"]),
                    "expected_surface_tone": int(row["tone"]),
                    "timing": clip["research_timing"],
                    "display_contour": clip["syllable_display_contour"],
                    "observed_contour": clip["observed"],
                }
            ],
            "overall_evidence": {"recording_quality": clip["acoustics"]["recording_quality"]},
        }
        write_json(
            output / "drawer-payloads" / (row["source_asset_id"].replace(":", "-") + ".json"), clip
        )
    write_csv(output / "per-clip.csv", summaries)
    write_csv(
        output / "t3-vs-t4-summary.csv",
        distributions({f"T{t}": [r for r in summaries if r["tone"] == str(t)] for t in (3, 4)}),
    )
    write_csv(
        output / "t3-correct-vs-wrong.csv",
        distributions(
            {
                f"T3_{label}": [
                    r for r in summaries if r["tone"] == "3" and r["correct"] == correct
                ]
                for label, correct in (("correct", True), ("wrong", False))
            }
        ),
    )
    tracked = subprocess.check_output(
        [
            "git",
            "ls-files",
            "services/api",
            "apps/mobile",
            "docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    write_json(
        output / "provenance.json",
        {
            "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "python": sys.version,
            "platform": platform.platform(),
            "analyzer_version": PraatAcousticAnalyzer().algorithm_version,
            "analyzer_parameters": PraatAcousticAnalyzer().parameters,
            "protected_file_sha256": {p: sha256(ROOT / p) for p in tracked if (ROOT / p).is_file()},
            "research_code_sha256": {
                p.name: sha256(p) for p in Path(__file__).parent.glob("*forensic*.py")
            },
            "drawer_bridge_sha256": sha256(Path(__file__).with_name("drawer_projection.cjs")),
        },
    )
    make_artifacts(output, clips, summaries)
    print(json.dumps({"analyzed": len(clips), "output": str(output), "frozen_v1_matches": 34}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    run(parser.parse_args().output)
