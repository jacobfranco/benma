"""Regenerate numerical report tables from the frozen local research artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.f0_foundation import TRACKERS


def load(root, name):
    original = json.loads((root / (name + ".json")).read_text())
    addition = root / "rmvpe" / (name + ".json")
    if addition.exists() and name in {
        "metrics",
        "repeatability",
        "windows",
        "low-f0-proxy",
        "low-f0-under70",
        "acoustic-support",
        "perturbations",
    }:
        return original + json.loads(addition.read_text())
    return original


def fmt(value):
    if value is None:
        return "NA"
    if isinstance(value, (float, np.floating)):
        return f"{value:.3f}"
    return str(value)


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join("---" for _ in headers) + " |",
                *("| " + " | ".join(map(fmt, row)) + " |" for row in rows),
            ]
        )
        + "\n"
    )


def csv_rows(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def rmvpe_exports(root: Path, report: Path):
    """Additional saved-evidence tables; preserve the five historical timing rows."""
    addition = root / "rmvpe"
    sweep_path = addition / "threshold-sweep.json"
    if not sweep_path.exists():
        return
    sweep = json.loads(sweep_path.read_text())
    flat = []
    for item in sweep:
        row = {k: v for k, v in item.items() if k not in {"proxy", "under70"}}
        for prefix in ("proxy", "under70"):
            row.update({f"{prefix}_{k}": v for k, v in item.get(prefix, {}).items()})
        flat.append(row)
    csv_rows(report / "rmvpe-threshold-sweep.csv", flat)
    summary = []
    for threshold in sorted({r["threshold"] for r in sweep}):
        rows = [r for r in sweep if r["threshold"] == threshold]
        negatives = [r for r in rows if r["kind"] == "negative"]
        speech = [r for r in rows if r["kind"] in {"capture", "direct"}]
        summary.append(
            {
                "threshold": threshold,
                "negative_pitch_frames": sum(r["emitted_frames"] for r in negatives),
                "negative_frames": sum(r["frames"] for r in negatives),
                "speech_emitted": sum(r["emitted_frames"] for r in speech),
                "speech_frames": sum(r["frames"] for r in speech),
                "low_proxy_retained": sum(
                    r.get("proxy", {}).get("covered_frames", 0) for r in rows
                ),
                "low_proxy_doubled": sum(r.get("proxy", {}).get("doubled_frames", 0) for r in rows),
                "lowest_retained": sum(r.get("under70", {}).get("covered_frames", 0) for r in rows),
                "lowest_doubled": sum(r.get("under70", {}).get("doubled_frames", 0) for r in rows),
                "harmonic_support_retained": sum(
                    r.get("harmonic_supported_frames", 0) for r in rows
                ),
                "harmonic_support_frames": sum(r.get("harmonic_frames", 0) for r in rows),
            }
        )
    csv_rows(report / "rmvpe-threshold-summary.csv", summary)
    (addition / "threshold-summary.json").write_text(json.dumps(summary, indent=2))
    timing = json.loads((addition / "verification-rmvpe.json").read_text())
    warm = timing["warm_runs"]
    with (report / "runtime.csv").open() as stream:
        previous = [r for r in csv.DictReader(stream) if r["tracker"] != "rmvpe"]
    previous.append(
        {
            "tracker": "rmvpe",
            "explicit_model_import_and_load_s": timing["explicit_initialization_seconds"],
            "first_call_s": timing["first_inference_seconds"],
            "warm_native_median_s": float(
                np.median([r["wall_seconds"] for r in warm if r["recording"] == "native_24k"])
            ),
            "warm_human_median_s": float(
                np.median([r["wall_seconds"] for r in warm if r["recording"] == "human_control"])
            ),
            "median_wall_rtf": timing["median_warm_rtf"],
            "median_cpu_time_rtf": float(
                np.median([r["cpu_seconds"] / r["duration_seconds"] for r in warm])
            ),
            "peak_process_rss_mib": timing["process_peak_rss_kib"] / 1024,
            "metadata_invariant": True,
        }
    )
    csv_rows(report / "runtime.csv", previous)
    csv_rows(
        report / "rmvpe-per-file-runtime.csv",
        json.loads((addition / "timings.json").read_text())["recordings"],
    )


def generate(root: Path, report: Path):
    report.mkdir(parents=True, exist_ok=True)
    rmvpe_exports(root, report)
    metrics = load(root, "metrics")
    repeated = load(root, "repeatability")
    windows = load(root, "windows")
    low = load(root, "low-f0-proxy")
    under70 = load(root, "low-f0-under70")
    support = load(root, "acoustic-support")
    perturbations = load(root, "perturbations")
    for name, rows in [
        ("per-recording-metrics", metrics),
        ("pairwise-repeatability", repeated),
        ("diagnostic-windows", windows),
        ("low-f0-proxy", low),
        ("low-f0-under70", under70),
        ("acoustic-support", support),
        ("source-perturbations", perturbations),
    ]:
        csv_rows(report / (name + ".csv"), rows)
    summary = []
    previous_summary = load(root, "aggregate") if (root / "rmvpe/metrics.json").exists() else []
    for name in TRACKERS:
        if not any(r["tracker"] == name for r in metrics):
            continue
        for variant in (
            ("raw", "minimal", "production") if name == "praat_ac" else ("raw", "minimal")
        ):
            saved = [
                r for r in previous_summary if r["tracker"] == name and r["variant"] == variant
            ]
            if saved:
                summary.extend(saved)
                continue
            selected = [r for r in metrics if r["tracker"] == name and r["variant"] == variant]
            speech = [r for r in selected if r["kind"] in {"capture", "direct"}]
            negative = [r for r in selected if r["kind"] == "negative"]
            synthetic = [r for r in selected if r["kind"] == "synthetic"]
            proxy = [r for r in low if r["tracker"] == name and r["variant"] == variant]
            summary.append(
                {
                    "tracker": name,
                    "variant": variant,
                    "speech_islands": sum(r["islands"] for r in speech),
                    "speech_jumps_gt9": sum(r["jumps_gt9"] for r in speech),
                    "speech_nearby_jumps_gt9": sum(r["nearby_jumps_gt9"] for r in speech),
                    "negative_pitch_frames": sum(r["emitted_frames"] for r in negative),
                    "negative_total_frames": sum(r["frames"] for r in negative),
                    "synthetic_octave_frames": sum(r["octave_error_frames"] for r in synthetic),
                    "synthetic_compared_frames": sum(r["compared_frames"] for r in synthetic),
                    "synthetic_voiced_coverage": sum(r["compared_frames"] for r in synthetic)
                    / sum(r["known_voiced_frames"] for r in synthetic),
                    "low_proxy_coverage": sum(r["covered_frames"] for r in proxy)
                    / sum(r["proxy_frames"] for r in proxy),
                    "low_proxy_doubled": sum(r["doubled_frames"] for r in proxy),
                }
            )
    aggregate_path = (
        root / "rmvpe/aggregate-six.json" if previous_summary else root / "aggregate.json"
    )
    aggregate_path.write_text(json.dumps(summary, indent=2))
    csv_rows(report / "aggregate.csv", summary)
    native = [r for r in metrics if r["recording"] in {"native_24k", "native_16k"}]
    (report / "raw-tables.md").write_text(
        "# Raw, cleanup and production tables\n\n"
        "Native coverage is finite frames / native frames, including silence and boundaries. "
        "It is not voiced-speech accuracy. CREPE raw has no unvoiced decision. "
        "Jump counts are discontinuity proxies, not measured real-speech octave-error rates.\n\n"
        + table(
            [
                "File",
                "Tracker",
                "View",
                "F0 frames",
                "Total",
                "Median Hz",
                "Islands",
                "Adjacent >9 st",
                "Near-gap >9 st",
            ],
            [
                [
                    r["recording"],
                    r["tracker"],
                    r["variant"],
                    r["emitted_frames"],
                    r["frames"],
                    r["median_hz"],
                    r["islands"],
                    r["jumps_gt9"],
                    r["nearby_jumps_gt9"],
                ]
                for r in native
            ],
        )
        + "\n## Whole-corpus safety and continuity\n\n"
        + table(
            [
                "Tracker",
                "View",
                "Speech islands",
                "Speech adjacent >9 st",
                "Negative emitted / total",
                "Synthetic >9-st errors / voiced comparisons",
                "Low proxy coverage",
                "Low proxy doubled",
            ],
            [
                [
                    r["tracker"],
                    r["variant"],
                    r["speech_islands"],
                    r["speech_jumps_gt9"],
                    f"{r['negative_pitch_frames']}/{r['negative_total_frames']}",
                    f"{r['synthetic_octave_frames']}/{r['synthetic_compared_frames']}",
                    r["low_proxy_coverage"],
                    r["low_proxy_doubled"],
                ]
                for r in summary
            ],
        )
        + "\n## Production filter ablation\n\n"
        + table(
            [
                "Recording",
                "Raw frames",
                "Retained",
                "Removed",
                "Raw/retained islands",
                "Raw/retained nearby >9-st jumps",
            ],
            [
                [
                    r["recording"],
                    r["raw"]["emitted_frames"],
                    r["retained"]["emitted_frames"],
                    r["removed_frames"],
                    f"{r['raw']['islands']}/{r['retained']['islands']}",
                    f"{r['raw']['nearby_jumps_gt9']}/{r['retained']['nearby_jumps_gt9']}",
                ]
                for r in load(root, "ablation")
            ],
        )
    )
    newest = [r for r in repeated if r["a"].startswith("take_") and r["b"].startswith("take_")]
    (report / "repeatability-tables.md").write_text(
        "# Audio-only repeatability tables\n\n"
        "Metrics are conditional on mutually finite aligned frames; read shared coverage and "
        "voicing agreement beside pitch disagreement. Broad correlation uses a 50-ms local median, "
        "without filling gaps. Raw and cleanup are separate.\n\n"
        + table(
            [
                "Pair",
                "Tracker",
                "View",
                "Mutual / active",
                "Mutual seconds",
                "Median st",
                "p90 st",
                "Correlation",
                "V/UV agreement",
                ">9-st count / rate",
                "Island difference",
            ],
            [
                [
                    r["a"] + "/" + r["b"],
                    r["tracker"],
                    r["variant"],
                    f"{r['mutual_frames']}/{r['active_frames']}",
                    r["mutually_voiced_aligned_seconds"],
                    r["median_st"],
                    r["p90_st"],
                    r["broad_contour_correlation"],
                    r["voicing_agreement"],
                    f"{r['octave_disagreement_count']}/{fmt(r['octave_disagreement_rate'])}",
                    r["island_difference"],
                ]
                for r in newest
            ],
        )
        + "\n## Deterministic source perturbations\n\n"
        + table(
            [
                "Variant",
                "Tracker",
                "View",
                "Mutual coverage",
                "Median st",
                "p90 st",
                "Correlation",
                "V/UV agreement",
                ">9-st disagreement",
            ],
            [
                [
                    r["b"],
                    r["tracker"],
                    r["variant"],
                    r["mutual_coverage"],
                    r["median_st"],
                    r["p90_st"],
                    r["broad_contour_correlation"],
                    r["voicing_agreement"],
                    r["octave_disagreement_rate"],
                ]
                for r in perturbations
            ],
        )
    )
    synthetic = [r for r in metrics if r["kind"] == "synthetic"]
    (report / "synthetic-tables.md").write_text(
        "# Known-F0 accuracy\n\n"
        "Absolute errors in semitones (1 st = 100 cents); edges ±80 ms excluded. "
        "Octave error is >9 st absolute error. Halving/doubling events are contiguous native runs "
        "with signed error in -15 to -9 / +9 to +15 st. "
        "Coverage includes all known-voiced core frames.\n\n"
        + table(
            [
                "Signal",
                "Tracker",
                "View",
                "Coverage",
                "Median abs Hz",
                "Median cents",
                "p95 st",
                "Max st",
                "Halving events / frames",
                "Doubling events / frames",
                "Octave errors",
                "False gaps",
                "False pitch / negative frames",
            ],
            [
                [
                    r["recording"],
                    r["tracker"],
                    r["variant"],
                    r["voiced_coverage"],
                    r["median_absolute_hz_error"],
                    r["median_error_cents"],
                    r["p95_error_st"],
                    r["max_error_st"],
                    f"{r['octave_halving_events']}/{r['octave_halving_frames']}",
                    f"{r['octave_doubling_events']}/{r['octave_doubling_frames']}",
                    r["octave_error_frames"],
                    r["false_gap_frames"],
                    f"{r['false_voiced_frames']}/{r['negative_frames']}",
                ]
                for r in synthetic
            ],
        )
    )
    negatives = [r for r in metrics if r["kind"] == "negative"]
    (report / "safety-tables.md").write_text(
        "# Low-F0 and no-speech tables\n\n"
        "Confidence is tracker-specific; NA is unavailable. Longest runs are hop-weighted. "
        "All emitted frames in known no-speech recordings are counted, "
        "including periodic background.\n\n"
        + table(
            [
                "Negative",
                "Tracker",
                "View",
                "Pitch frames",
                "Total",
                "Emitted fraction",
                "Median Hz",
                "Confidence median/max",
                "Longest run s",
                "Islands",
            ],
            [
                [
                    r["recording"],
                    r["tracker"],
                    r["variant"],
                    r["emitted_frames"],
                    r["frames"],
                    r["coverage"],
                    r["median_hz"],
                    f"{fmt(r['confidence_median'])}/{fmt(r['confidence_max'])}",
                    r["longest_run_seconds"],
                    r["islands"],
                ]
                for r in negatives
            ],
        )
        + "\n## Semi-blinded acoustic support masks\n\n"
        + table(
            ["Recording", "Region", "Tracker", "View", "Emitted/total", "Median Hz", "Islands"],
            [
                [
                    r["recording"],
                    r["region_kind"],
                    r["tracker"],
                    r["variant"],
                    f"{r['emitted_frames']}/{r['frames']}",
                    r["median_hz"],
                    r["islands"],
                ]
                for r in support
                if r["region_kind"] != "coarse_harmonic_band"
            ],
        )
        + "\n## Coarse harmonic support\n\n"
        + table(
            ["Recording", "Tracker", "View", "Within band / all frames", "Emitted frames"],
            [
                [
                    r["recording"],
                    r["tracker"],
                    r["variant"],
                    f"{r['supported_frames']}/{r['frames']}",
                    r["emitted_frames"],
                ]
                for r in support
                if r["region_kind"] == "coarse_harmonic_band"
            ],
        )
        + "\n## Protected baseline proxy at or below 70 Hz\n\n"
        + table(
            [
                "Recording",
                "Tracker",
                "View",
                "Covered / proxy",
                "Median Hz",
                "Doubled frames",
                "Native confidence median (including rejected frames)",
            ],
            [
                [
                    r["recording"],
                    r["tracker"],
                    r["variant"],
                    f"{r['covered_frames']}/{r['proxy_frames']}",
                    r["median_hz"],
                    r["doubled_frames"],
                    r.get("all_proxy_confidence_median", r["confidence_median"]),
                ]
                for r in under70
            ],
        )
        + "\nThe 18-recording low-F0 proxy cohort is in [low-f0-proxy.csv](low-f0-proxy.csv). "
        "It is selected by baseline acoustic agreement and is not independent ground truth.\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("/tmp/benma-f0-bakeoff"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/research/pronunciation-v2/2026-10-05-f0-foundation"),
    )
    args = parser.parse_args()
    generate(args.output, args.report)
