"""Post-hoc Experiment 2 diagnostics. No encoder, learned head, fitting or inference.

Run with services/api/.venv/bin/python; only existing local audio is read.
Acoustic extraction accepts a path alone; metadata and saved predictions join later.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import platform
import statistics
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import acoustic_forensics as af
import numpy as np

ROOT = af.ROOT
BASE = ROOT / "docs/research/pronunciation-v2"
PREFLIGHT = BASE / "2026-09-30-experiment-2-preflight"
EXPERIMENT = BASE / "2026-09-30-experiment-2-temporal-pooling"
OUTPUT = BASE / "2026-09-30-experiment-2-error-audit"
MANIFEST = PREFLIGHT / "sealed-test-manifest.csv"
PREDICTIONS = EXPERIMENT / "fresh-test-predictions.csv"
IDENTITY = ("source_asset_id", "speaker_id", "speaker_name", "text", "pinyin", "tone")
POLICY = {
    "block_seconds": 0.01,
    "relative_peak_rms": 0.2,
    "absolute_floor_rms": 0.003,
    "noise_floor_multiplier": 3,
    "noise_gate_peak_cap": 0.15,
    "description": "10-ms nonoverlapping waveform blocks including partial final block; "
    "gate=max(.003, min(3*10th-percentile block RMS, .15*peak block RMS), .2*peak block RMS). "
    "Active means block RMS >= gate. No smoothing, label inputs, or fitted parameters. "
    "Low energy is a proxy, not verified silence or phonetic speech segmentation.",
}


def boundaries(samples, rate):
    """Waveform-only measurement with complete sample coverage and no pitch dependency."""
    values = np.asarray(samples, dtype=np.float64)
    width = round(rate * POLICY["block_seconds"])
    blocks = [values[i : i + width] for i in range(0, len(values), width)]
    rms = np.array([np.sqrt(np.mean(b * b)) for b in blocks])
    gate = max(
        POLICY["absolute_floor_rms"],
        min(
            POLICY["noise_floor_multiplier"] * float(np.quantile(rms, 0.1)),
            POLICY["noise_gate_peak_cap"] * float(rms.max()),
        ),
        POLICY["relative_peak_rms"] * float(rms.max()),
    )
    mask = rms >= gate
    indices = np.flatnonzero(mask)
    duration = len(values) / rate
    active_count = sum(len(b) for b, keep in zip(blocks, mask, strict=True) if keep)
    active_energy = sum(float(np.dot(b, b)) for b, keep in zip(blocks, mask, strict=True) if keep)
    first = int(indices[0]) * width / rate if len(indices) else None
    last = min(len(values), (int(indices[-1]) + 1) * width) / rate if len(indices) else None
    # No-active clips have undefined boundaries, rather than double-counted silence.
    trailing = duration - last if last is not None else None
    edge = first + trailing if first is not None else None
    span = last - first if first is not None else 0.0
    return (
        {
            "waveform_active_gate_rms": gate,
            "no_active_blocks": not bool(len(indices)),
            "leading_low_energy_seconds": first,
            "trailing_low_energy_seconds": trailing,
            "leading_low_energy_fraction": first / duration if first is not None else None,
            "trailing_low_energy_fraction": trailing / duration if trailing is not None else None,
            "edge_low_energy_seconds": edge,
            "edge_low_energy_fraction": edge / duration if edge is not None else None,
            "active_speech_seconds": active_count / rate,
            "active_speech_fraction": active_count / len(values),
            "active_span_seconds": span,
            "active_span_fraction": span / duration,
            "internal_low_energy_seconds": span - active_count / rate,
            "whole_clip_rms": float(np.sqrt(np.mean(values * values))),
            "active_speech_rms": math.sqrt(active_energy / active_count) if active_count else None,
        },
        mask,
        width,
    )


def extract(path):
    """Only audio crosses this boundary; Benma parameters and decisions stay unchanged."""
    with tempfile.TemporaryDirectory(prefix="benma-error-audit-") as tmp:
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
        rate, samples = af._pcm16_mono(canonical)
        a = af.PraatAcousticAnalyzer().analyze(canonical)
        clip = af.derive(a, len(samples) / rate)
        clip.update(identity={}, wav2vec={}, peak=max(map(abs, samples)))
        row = af.summarize(clip)
        boundary, mask, width = boundaries(samples, rate)
        active = [
            p
            for p in a["f0"]
            if mask[min(len(mask) - 1, round(p["timestamp_seconds"] * rate) // width)]
        ]
        periodicity = [p["voicing_probability"] for p in active]
        features = clip["observed"]["features"]
        geometry = (
            0 < features.get("minimum_position", 0) < 1
            and features.get("pre_minimum_fall_st", 0) >= 1.5
            and features.get("post_minimum_recovery_st", 0) >= 1.5
        )
        thirds = (
            row.get("evidence_st_first_to_middle", 0) <= -1
            and row.get("evidence_st_middle_to_final", 0) >= 1
        )
        unstable = bool(features.get("tracker_instability_rejected", 0))
        return (
            row
            | boundary
            | {
                "canonical_pcm16_wav_sha256": af.sha256(canonical),
                "active_f0_frame_count": len(active),
                "active_speech_missing_f0_fraction": sum(p["f0_hz"] is None for p in active)
                / len(active)
                if active
                else None,
                "active_periodicity_mean_waveform": af.mean(periodicity),
                "active_periodicity_median_waveform": statistics.median(periodicity)
                if periodicity
                else None,
                "tracker_instability_flag": unstable,
                "tracker_instability_reason": "production_tracker_instability_rejected"
                if unstable
                else "not_flagged",
                "maximum_tracker_jump_st": features.get("maximum_tracker_jump_st"),
                "octave_like_jump_count": features.get("octave_like_jump_count"),
                "minimum_tracked_f0_hz": row.get("raw_hz_minimum"),
                "retained_semitone_range": row.get("evidence_st_range"),
                "dip_recovery_bin_geometry": geometry,
                "dip_recovery_thirds_geometry": thirds,
                "v1_recognizes_dip": clip["observed"]["classification"] == "3-like",
            }
        )


def select_rows(manifest, predictions, expected=118):
    """Validate immutable identity/labels and use every manifest row, sorted by ID."""
    by_id = {r["source_asset_id"]: r for r in predictions}
    ids = {r["source_asset_id"] for r in manifest}
    if len(manifest) != expected or len(ids) != expected or len(by_id) != len(predictions):
        raise ValueError("Unexpected coverage or duplicate identity")
    if ids != set(by_id):
        raise ValueError("Prediction/manifest coverage mismatch")
    result = []
    for row in sorted(manifest, key=lambda r: r["source_asset_id"]):
        pred = by_id[row["source_asset_id"]]
        if any(row[k] != pred[k] for k in IDENTITY):
            raise ValueError("Frozen identity/label mismatch")
        result.append({**row, **{k: v for k, v in pred.items() if k.startswith("A_")}})
    return result


def analyze_row(row):
    path = ROOT / row["local_path"]
    if af.sha256(path) != row["audio_sha256"]:
        raise ValueError(f"Audio hash mismatch: {row['source_asset_id']}")
    acoustic = extract(path)
    probabilities = [float(row[f"A_p_T{i}"]) for i in range(1, 5)]
    ordered = sorted(probabilities, reverse=True)
    prediction = int(row["A_prediction"])
    correct = prediction == int(row["tone"])
    if (
        prediction != int(np.argmax(probabilities)) + 1
        or not math.isclose(sum(probabilities), 1)
        or not math.isclose(ordered[0], float(row["A_confidence"]))
        or correct != (row["A_correct"] == "True")
    ):
        raise ValueError("Frozen prediction arithmetic mismatch")
    return {
        **{k: row[k] for k in IDENTITY},
        "audio_sha256": row["audio_sha256"],
        "A_prediction": prediction,
        "A_confidence": ordered[0],
        "A_correct": correct,
        "A_margin": ordered[0] - ordered[1],
        **{f"A_p_T{i}": p for i, p in enumerate(probabilities, 1)},
        **acoustic,
    }


METRICS = list(
    dict.fromkeys(
        [
            "A_confidence",
            "A_margin",
            "duration_seconds",
            "leading_low_energy_seconds",
            "trailing_low_energy_seconds",
            "edge_low_energy_seconds",
            "edge_low_energy_fraction",
            "active_speech_seconds",
            "active_speech_fraction",
            "active_span_fraction",
            "whole_clip_rms",
            "active_speech_rms",
            "active_speech_missing_f0_fraction",
            "active_periodicity_mean_waveform",
            "active_periodicity_median_waveform",
            "tracker_instability_flag",
            "maximum_tracker_jump_st",
            "octave_like_jump_count",
            "minimum_tracked_f0_hz",
            "retained_semitone_range",
            "dip_recovery_bin_geometry",
            "dip_recovery_thirds_geometry",
            "v1_recognizes_dip",
            *af.METRICS,
        ]
    )
)


def distributions(groups):
    rows = []
    for group, clips in groups.items():
        for metric in METRICS:
            values = [float(r[metric]) for r in clips if r.get(metric) is not None]
            rows.append(
                {
                    "group": group,
                    "metric": metric,
                    "group_n": len(clips),
                    "n": len(values),
                    "missing_n": len(clips) - len(values),
                    **dict(
                        zip(
                            ("minimum", "q25", "median", "q75", "maximum"),
                            np.quantile(values, [0, 0.25, 0.5, 0.75, 1]).tolist()
                            if values
                            else [None] * 5,
                            strict=True,
                        )
                    ),
                }
            )
    return rows


def group_rows(rows, stress):
    groups = {
        "A_correct": [r for r in rows if r["A_correct"]],
        "A_wrong": [r for r in rows if not r["A_correct"]],
        "T3_correct": [r for r in rows if r["tone"] == "3" and r["A_correct"]],
        "T3_to_T4": [r for r in rows if r["tone"] == "3" and r["A_prediction"] == 4],
        "T3_other_errors": [r for r in rows if r["tone"] == "3" and r["A_prediction"] in (1, 2)],
        "T2_correct": [r for r in rows if r["tone"] == "2" and r["A_correct"]],
        "T2_errors": [r for r in rows if r["tone"] == "2" and not r["A_correct"]],
        "Luilui_T3_all": stress,
        "Luilui_T3_correct": [r for r in stress if r["A_correct"]],
        "Luilui_T3_to_T4": [r for r in stress if r["A_prediction"] == 4],
    }
    for speaker in sorted({r["speaker_name"] for r in rows}):
        subset = [r for r in rows if r["speaker_name"] == speaker]
        groups[f"speaker:{speaker}"] = subset
        for correct in (True, False):
            groups[f"speaker:{speaker}:A_{'correct' if correct else 'wrong'}"] = [
                r for r in subset if r["A_correct"] == correct
            ]
        for tone in range(1, 5):
            for correct in (True, False):
                groups[f"speaker:{speaker}:T{tone}:A_{'correct' if correct else 'wrong'}"] = [
                    r for r in subset if int(r["tone"]) == tone and r["A_correct"] == correct
                ]
    return groups


def speaker_summary(rows):
    result = []
    for speaker in sorted({r["speaker_name"] for r in rows}):
        subset = [r for r in rows if r["speaker_name"] == speaker]
        for tone in (None, 1, 2, 3, 4):
            clips = [r for r in subset if tone is None or int(r["tone"]) == tone]
            result.append(
                {
                    "speaker": speaker,
                    "tone": tone or "all",
                    "n": len(clips),
                    "correct": sum(r["A_correct"] for r in clips),
                    "accuracy": sum(r["A_correct"] for r in clips) / len(clips),
                    "unique_texts": len({r["text"] for r in clips}),
                    "unique_pinyin": len({r["pinyin"] for r in clips}),
                    "text_pinyin": ";".join(sorted({r["text"] + ":" + r["pinyin"] for r in clips})),
                    **{
                        f"predicted_T{i}": sum(r["A_prediction"] == i for r in clips)
                        for i in range(1, 5)
                    },
                }
            )
    return result


def human_items(manifest):
    """Strict whitelist: no prediction/diagnostic rows are passed to HTML generation."""
    return [
        {**{k: r[k] for k in IDENTITY}, "audio_filename": Path(r["local_path"]).name}
        for r in sorted(manifest, key=lambda r: r["source_asset_id"])
    ]


def write_human_audit(output, manifest):
    output.mkdir(parents=True, exist_ok=True)
    data = json.dumps(human_items(manifest), ensure_ascii=False).replace("<", "\\u003c")
    template = Path(__file__).with_suffix(".html").read_text()
    (output / "index.html").write_text(template.replace("__ITEMS__", data))
    af.write_csv(
        output / "annotations-template.csv",
        [
            {**{k: r[k] for k in IDENTITY}, "realized_tone": "", "confidence": "", "note": ""}
            for r in human_items(manifest)
        ],
    )


def run(output=OUTPUT):
    manifest = af.read_csv(MANIFEST)
    selected = select_rows(manifest, af.read_csv(PREDICTIONS))
    stress_manifest = [
        r
        for r in af.read_csv(af.EXPERIMENT / "clean-corpus-manifest.csv")
        if r["speaker_id"] == af.SOURCE
        and r["partition"] == "test"
        and r["included"] == "True"
        and r["tone"] == "3"
    ]
    stress_ids = {r["source_asset_id"] for r in stress_manifest}
    stress_predictions = [
        r
        for r in af.read_csv(EXPERIMENT / "stress-predictions.csv")
        if r["source_asset_id"] in stress_ids
    ]
    stress_selected = select_rows(stress_manifest, stress_predictions, expected=13)
    rows = [analyze_row(r) for r in selected]
    stress = [analyze_row(r) for r in stress_selected]
    if len(rows) != 118 or sum(r["A_correct"] for r in rows) != 81:
        raise ValueError("Baseline result mismatch")
    output.mkdir(parents=True, exist_ok=True)
    af.write_csv(output / "per-clip.csv", rows)
    af.write_csv(output / "t3-audit.csv", [r for r in rows if r["tone"] == "3"])
    af.write_csv(output / "luilui-t3-comparison.csv", stress)
    af.write_csv(output / "error-groups.csv", distributions(group_rows(rows, stress)))
    af.write_csv(output / "speaker-summary.csv", speaker_summary(rows))
    write_human_audit(output / "human-audit", manifest)
    inputs = [
        MANIFEST,
        PREDICTIONS,
        EXPERIMENT / "stress-predictions.csv",
        af.EXPERIMENT / "clean-corpus-manifest.csv",
    ]
    sources = [
        Path(__file__),
        Path(__file__).with_suffix(".html"),
        Path(af.__file__),
        *[
            ROOT / f"services/api/src/benma_api/pronunciation/{name}.py"
            for name in ("acoustics", "contours", "evidence_region")
        ],
    ]
    protected = subprocess.check_output(
        [
            "git",
            "ls-files",
            "services/api",
            "apps/mobile",
            str(PREFLIGHT.relative_to(ROOT)),
            str(EXPERIMENT.relative_to(ROOT)),
            str(af.EXPERIMENT.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    af.write_json(
        output / "provenance.json",
        {
            "scope": "Post-hoc diagnostic audit of all 118 OPENED/INSPECTED fresh clips. "
            "Luilui T3 is an already-inspected stress comparison. No new classifier.",
            "head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "branch": subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=ROOT, text=True
            ).strip(),
            "input_sha256": {str(p.relative_to(ROOT)): af.sha256(p) for p in inputs},
            "source_sha256": {str(p.relative_to(ROOT)): af.sha256(p) for p in sources},
            "protected_file_sha256": {p: af.sha256(ROOT / p) for p in protected},
            "audio": [
                {
                    "source_asset_id": r["source_asset_id"],
                    "local_path": r["local_path"],
                    "verified_sha256": r["audio_sha256"],
                }
                for r in selected + stress_selected
            ],
            "boundary_policy": POLICY,
            "analyzer_parameters": af.PraatAcousticAnalyzer().parameters,
            "analyzer_version": af.PraatAcousticAnalyzer().algorithm_version,
            "research_timing": "Whole isolated clip; no provider alignment reproduced",
            "fresh_counts": {
                "n": len(rows),
                "A_correct": sum(r["A_correct"] for r in rows),
                "tone": dict(Counter(r["tone"] for r in rows)),
            },
            "runtime": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "ffmpeg": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[
                    0
                ],
                "packages": {
                    p: importlib.metadata.version(p)
                    for p in ("numpy", "praat-parselmouth", "pydantic", "pytest")
                },
            },
            "generated_artifact_sha256": {
                str(p.relative_to(output)): af.sha256(p)
                for p in sorted(output.rglob("*"))
                if p.is_file() and p.suffix in {".csv", ".html"}
            },
            "human_annotations": "All blank; no listening annotations fabricated",
        },
    )
    print(f"Wrote {len(rows)} fresh and {len(stress)} stress diagnostics to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    run(parser.parse_args().output)
