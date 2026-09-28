"""Offline F0 experiments. No DB, provider, production writes, target-based DSP or interpolation.

Run with services/api/.venv/bin/python from repository root. Input is the read-only
export at /tmp/benma-f0-corpus. Research-only analyzers reuse the exact current
production analyze body, substituting only its two pitch-generation calls. The
identity substitution is asserted equal to production, including all quality fields.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import math
import statistics
import textwrap
import time
from collections import Counter
from dataclasses import asdict
from itertools import pairwise
from pathlib import Path

import numpy as np
import parselmouth
from benma_api.pronunciation import acoustics
from benma_api.pronunciation.acoustics import (
    AutocorrelationAcousticAnalyzer,
    PraatAcousticAnalyzer,
    reject_terminal_octave_ambiguity,
)
from benma_api.pronunciation.contours import classify_contour, display_contour, syllable_contour
from benma_api.pronunciation.evidence_region import select_tone_evidence

OUT = Path(__file__).resolve().parent
CORPUS = Path("/tmp/benma-f0-corpus")
FRESH = [r["utterance_id"] for r in json.loads((OUT / "fresh-diagnostics.json").read_text())]
PARAMETERS = {
    k: v
    for k, v in PraatAcousticAnalyzer().parameters.items()
    if k not in {"energy_gate", "quality_gate"}
}
DP = {
    "dp_balanced": {
        "jump_per_st": 0.03,
        "excess_jump_squared": 0.015,
        "octave_penalty": 0.25,
        "uv_transition": 0.14,
    },
    "dp_continuity": {
        "jump_per_st": 0.03,
        "excess_jump_squared": 0.015,
        "octave_penalty": 0.25,
        "uv_transition": 0.30,
    },
}


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def quantiles(values):
    return {
        f"p{q}": round(float(np.percentile(values, q)), 6) if values else None
        for q in [10, 50, 90, 95]
    }


def sequence_path(states, intensity, config):
    """Viterbi over measured (Hz,strength) states; UV always allowed, no filling.

    Hard .45 minimum is the unchanged downstream periodicity gate. UV local score
    follows Praat's documented intensity/silence relationship; voiced score uses
    strength minus .45 and a .01/octave preference for higher periodicity. Neither
    alignment nor target metadata is an input. First-order UV deliberately has no
    hidden interpolated frequency. Thus it can lose octave memory across a gap.
    """
    scores = None
    back = []
    previous = None
    for frame, level in zip(states, intensity, strict=True):
        hz = np.array([c[0] for c in frame])
        strength = np.array([c[1] for c in frame])
        voiced = hz > 0
        local = np.full(len(frame), max(0.0, 2.0 - level / (0.03 / 1.45)))
        local[voiced] = strength[voiced] - 0.45 - 0.01 * np.log2(550.0 / hz[voiced])
        local[voiced & (strength < 0.45)] = -np.inf
        if scores is None:
            scores = local
            back.append(np.zeros(len(frame), dtype=int))
        else:
            old = np.array([c[0] for c in previous])
            both = (old[:, None] > 0) & voiced[None, :]
            jumps = np.abs(12 * np.log2(np.maximum(old[:, None], 1) / np.maximum(hz[None, :], 1)))
            cost = (
                config["jump_per_st"] * jumps
                + config["excess_jump_squared"] * np.maximum(0, jumps - 2) ** 2
            )
            cost += config["octave_penalty"] * ((jumps >= 10) & (jumps <= 14))
            cost = np.where(
                both,
                cost,
                np.where((old[:, None] > 0) != voiced[None, :], config["uv_transition"], 0.0),
            )
            total = scores[:, None] - cost
            indices = np.argmax(total, axis=0)
            scores = local + total[indices, np.arange(len(frame))]
            back.append(indices)
        previous = frame
    if scores is None:
        return []
    index = int(np.argmax(scores))
    path = [index]
    for links in reversed(back[1:]):
        index = int(links[index])
        path.append(index)
    return list(reversed(path))


def dp_pitch(sound, name, **parameters):
    pitch = sound.to_pitch_ac(**parameters)
    states = [
        [
            (float(c.frequency), float(c.strength))
            for c in frame.candidates
            if c.frequency == 0
            or parameters["pitch_floor"] <= c.frequency <= parameters["pitch_ceiling"]
        ]
        for frame in pitch
    ]
    path = sequence_path(states, [float(f.intensity) for f in pitch], DP[name])
    for frame, candidates, index in zip(pitch, states, path, strict=True):
        hz = candidates[index][0]
        frame.select(next(c for c in frame.candidates if float(c.frequency) == hz))
    return pitch


def analyzer_for(name):
    engine = PraatAcousticAnalyzer()
    if name == "production":
        return engine

    def pitch(source, **parameters):
        if name == "identity":
            return source.to_pitch_ac(**parameters)
        if name == "cc":
            return source.to_pitch_cc(**parameters)
        return dp_pitch(source, name, **parameters)

    source = textwrap.dedent(inspect.getsource(PraatAcousticAnalyzer.analyze))
    assert source.count(".to_pitch_ac(**pitch_parameters)") == 2
    source = source.replace(
        "sound.to_pitch_ac(**pitch_parameters)", "_experiment_pitch(sound, **pitch_parameters)"
    )
    source = source.replace(
        "filtered.to_pitch_ac(**pitch_parameters)",
        "_experiment_pitch(filtered, **pitch_parameters)",
    )
    scope = {**vars(acoustics), "_experiment_pitch": pitch}
    exec(compile(source, "<offline-identical-quality-pipeline>", "exec"), scope)
    engine.analyze = scope["analyze"].__get__(engine, type(engine))
    return engine


def legacy_with_quality(path, baseline):
    """Independent existing estimator plus frozen gates on its own time grid.

    Spectral/energy/comparison facts come from nearest baseline frame <=5.1ms,
    not interpolated F0. This is a witness with an explicitly asymmetric AC
    comparison; it is not a candidate for deployment. Missing edge comparison
    remains unknown. The legacy .32 extraction gate is unchanged; downstream .45
    still applies. Keep original witness output separately for forensic inspection.
    """
    result = AutocorrelationAcousticAnalyzer().analyze(path)
    original = copy.deepcopy(result["f0"])
    threshold = baseline["energy_gate"]["threshold_rms"]
    for point in result["f0"]:
        t = point["timestamp_seconds"]
        nearest = min(baseline["f0"], key=lambda p: abs(p["timestamp_seconds"] - t))
        known = abs(nearest["timestamp_seconds"] - t) <= 0.0051
        hz = point["f0_hz"]
        check = nearest.get("comparison_f0_hz") if known else None
        rms = nearest["energy_rms"] if known else point["energy_rms"]
        low = nearest["low_frequency_energy_fraction"] if known else 0.0
        disagreement = abs(12 * math.log2(hz / check)) if hz and check else 0.0
        contaminated = bool(hz and ((hz < 80 and low > 0.7) or disagreement > 6))
        point.update(
            tracker_f0_hz=hz,
            f0_hz=hz if rms >= threshold else None,
            energy_rms=rms,
            energy_gated=bool(hz and rms < threshold),
            comparison_f0_hz=check,
            filter_disagreement_st=disagreement,
            low_frequency_energy_fraction=low,
            quality_usable=not contaminated,
            low_frequency_contaminated=contaminated,
            selected_f0_hz=hz if rms >= threshold and not contaminated else None,
            selection_reason="low_frequency_contamination"
            if contaminated
            else "below_energy_gate"
            if rms < threshold
            else "legacy_selected",
            comparison_nearest_frame=known,
        )
    # No candidate sets: existing terminal ambiguity rule deliberately fails closed.
    reject_terminal_octave_ambiguity(result["f0"], threshold)
    return result, original


def gap_records(points, start, end, valid_times):
    window = [p for p in points if start <= p["timestamp_seconds"] < end]
    indices = [i for i, p in enumerate(window) if p["timestamp_seconds"] in valid_times]
    gaps = []
    for left, right in pairwise(indices):
        if right == left + 1:
            continue
        missing = window[left + 1 : right]
        a, b = window[left]["timestamp_seconds"], window[right]["timestamp_seconds"]
        gaps.append(
            {
                "left_seconds": a,
                "right_seconds": b,
                "first_missing_center": missing[0]["timestamp_seconds"],
                "last_missing_center": missing[-1]["timestamp_seconds"],
                "missing_frames": len(missing),
                "missing_seconds": round(len(missing) * 0.01, 4),
                "endpoint_interval_seconds": round(b - a, 4),
            }
        )
    return gaps


def span_metrics(raw, span, authorized):
    start, end = span["start_seconds"], span["end_seconds"]
    observed = classify_contour(None, start, end, raw=raw, timing_reliable=authorized).model_dump()
    region = select_tone_evidence(raw, start, end) if authorized else None
    a, b = (region.start, region.end) if region else (start, end)
    contour = syllable_contour(display_contour(raw), a, b)
    retained = {p.timestamp_seconds for seg in contour.segments for p in seg}
    window = [p for p in raw if a <= p["timestamp_seconds"] < b]
    raw_voiced = [p for p in window if p.get("f0_hz")]
    jumps = [
        abs(12 * math.log2(y["f0_hz"] / x["f0_hz"]))
        for x, y in pairwise(raw_voiced)
        if 0 < y["timestamp_seconds"] - x["timestamp_seconds"] <= 0.12
    ]
    gaps = gap_records(raw, a, b, retained)
    core = max(retained) - min(retained) + 0.01 if retained else 0.0
    reason = observed["reason"]
    return {
        "observed": observed,
        "region": asdict(region) if region else None,
        "metrics": {
            "retained_frames": len(retained),
            "raw_voiced_frames": len(raw_voiced),
            "voiced_coverage": min(1.0, len(retained) * 0.01 / (b - a)),
            "core_coverage": len(retained) * 0.01 / core if core else 0.0,
            "gaps": gaps,
            "internal_missing_seconds": sum(g["missing_seconds"] for g in gaps),
            "large_jumps": sum(j > 6 for j in jumps),
            "octave_like_events": sum(10 <= j <= 14 for j in jumps),
            "max_jump_st": max(jumps, default=0),
            "contaminated_frames": sum(
                p.get("low_frequency_contaminated", False) for p in raw_voiced
            ),
            "raw_filter_disagreement_st": quantiles(
                [p["filter_disagreement_st"] for p in raw_voiced if p.get("comparison_f0_hz")]
            ),
            "raw_filter_disagreement_over6": sum(
                p.get("filter_disagreement_st", 0) > 6 for p in raw_voiced
            ),
            "severely_fragmented": len(gaps) >= 2
            or max((g["missing_seconds"] for g in gaps), default=0) > 0.08,
            "sufficient_quality": authorized
            and reason
            in {
                "acoustic_shape_only",
                "ambiguous_shape",
                "sustained_level_after_onset",
                "short_coherent_fall",
                "shallow_coherent_valley",
                "coherent_short_gap",
                "isolated_filtered_glitch",
            },
        },
        "timing_authorized": authorized,
    }


def authority(span):
    observed = span.get("locally_recomputed_contour") or {}
    return (
        bool(observed)
        and observed.get("reason") not in {"timing_unavailable", "synthetic_timing"}
        and span.get("timing_resolution", {}).get("accepted", True)
    )


def agreement(baseline, alternate, a, b):
    strong = [
        p
        for p in baseline
        if a <= p["timestamp_seconds"] < b
        and p.get("f0_hz")
        and p.get("quality_usable")
        and p["voicing_probability"] >= 0.8
    ]
    errors = []
    missing = 0
    for p in strong:
        q = min(alternate, key=lambda q: abs(q["timestamp_seconds"] - p["timestamp_seconds"]))
        if (
            abs(q["timestamp_seconds"] - p["timestamp_seconds"]) > 0.0051
            or not q.get("f0_hz")
            or not q.get("quality_usable")
            or q["voicing_probability"] < 0.45
        ):
            missing += 1
            continue
        errors.append(abs(12 * math.log2(q["f0_hz"] / p["f0_hz"])))
    return {
        "strong_baseline_frames": len(strong),
        "alternate_missing": missing,
        "matched_frames": len(errors),
        "within_1st": sum(v <= 1 for v in errors),
        "octave_disagreements": sum(10 <= v <= 14 for v in errors),
        "error_st": quantiles(errors),
    }


def main():
    corpus = json.loads((CORPUS / "corpus.json").read_text())
    methods = ["production", "dp_balanced", "dp_continuity", "cc", "legacy_nac"]
    engines = {name: analyzer_for(name) for name in methods if name != "legacy_nac"}
    engines["production"].analyze(CORPUS / (corpus[0]["id"] + ".wav"))  # import/cache warmup
    output = []
    fresh_traces = {}
    latency = {name: [] for name in methods}
    span_latency = {name: [] for name in methods}
    equal_baseline = 0
    for row in corpus:
        path = CORPUS / (row["id"] + ".wav")
        tracks = {}
        timings = {}
        # Rotate order to reduce ordering bias; three observations, whole audio.
        rotate = len(output) % 4
        order = methods[:4][rotate:] + methods[:4][:rotate]
        for name in order:
            times = []
            for _ in range(3):
                started = time.perf_counter()
                tracks[name] = engines[name].analyze(path)
                times.append((time.perf_counter() - started) * 1000)
            timings[name] = times
        identity = analyzer_for("identity").analyze(path)
        assert identity == tracks["production"], "Research adapter changed baseline quality gates"
        started = time.perf_counter()
        tracks["legacy_nac"], original = legacy_with_quality(path, tracks["production"])
        timings["legacy_nac"] = [(time.perf_counter() - started) * 1000]
        if row["id"] in FRESH:
            fresh_traces[row["id"]] = {"tracks": tracks, "legacy_original": original}
        numeric = [
            s
            for s in row["spans"]
            if isinstance(s.get("start_seconds"), (int, float))
            and isinstance(s.get("end_seconds"), (int, float))
        ]
        item = {
            "utterance_id": row["id"],
            "attempt_id": row["attempt_id"],
            "created_at": row["created_at"],
            "target": (row["diagnostic"].get("target") or {}).get("persisted_text"),
            "perceived_text": row["diagnostic"]["perceived_text"],
            "audio_sha256": row["audio_sha256"],
            "duration_seconds": tracks["production"]["duration_seconds"],
            "timings_ms": timings,
            "spans": [],
        }
        for index, s in enumerate(numeric):
            authorized = authority(s)
            unit = {
                "index": index,
                "text": s["characters"],
                "expected": s.get("expected_surface_tone"),
                "start_seconds": s["start_seconds"],
                "end_seconds": s["end_seconds"],
                "timing_authorized": authorized,
                "methods": {},
            }
            for name in methods:
                result = span_metrics(tracks[name]["f0"], s, authorized)
                result["agreement"] = agreement(
                    tracks["production"]["f0"],
                    tracks[name]["f0"],
                    s["start_seconds"],
                    s["end_seconds"],
                )
                unit["methods"][name] = result
            old = classify_contour(
                None,
                s["start_seconds"],
                s["end_seconds"],
                raw=row["acoustic"]["f0"],
                timing_reliable=authorized,
            ).model_dump()
            unit["persisted_raw_recomputed"] = old
            equal_baseline += old == unit["methods"]["production"]["observed"]
            item["spans"].append(unit)
        for name in methods:
            latency[name].append(statistics.median(timings[name]))
            if numeric:
                span_latency[name].append(statistics.median(timings[name]) / len(numeric))
        output.append(item)
        # Preserve reproducible full tracks outside repo, without inflating report.
        (CORPUS / (row["id"] + ".tracks.json")).write_text(json.dumps(tracks))
        print(len(output), row["id"], len(numeric), "spans", flush=True)
    write("comparison.json", output)
    write("fresh-traces.json", fresh_traces)
    summary = {
        "recordings": len(corpus),
        "all_syllable_rows": sum(len(r["spans"]) for r in corpus),
        "timed_recordings": sum(bool(r["spans"]) for r in output),
        "numeric_spans": sum(len(r["spans"]) for r in output),
        "timing_authorized": sum(s["timing_authorized"] for r in output for s in r["spans"]),
        "persisted_recompute_equal": equal_baseline,
        "methods": {},
    }
    changes = []
    for name in methods:
        units = [s["methods"][name] for r in output for s in r["spans"] if s["timing_authorized"]]
        metrics = [s["metrics"] for s in units]
        summary["methods"][name] = {
            "sufficient_quality": sum(m["sufficient_quality"] for m in metrics),
            "classified": sum(s["observed"]["classification"] != "unclear" for s in units),
            "classification": dict(Counter(s["observed"]["classification"] for s in units)),
            "quality_reasons": dict(Counter(s["observed"]["reason"] for s in units)),
            "voiced_coverage": quantiles([m["voiced_coverage"] for m in metrics]),
            "core_coverage": quantiles([m["core_coverage"] for m in metrics]),
            "internal_gaps": sum(len(m["gaps"]) for m in metrics),
            "internal_missing_seconds": sum(m["internal_missing_seconds"] for m in metrics),
            "gap_duration_seconds": quantiles(
                [g["missing_seconds"] for m in metrics for g in m["gaps"]]
            ),
            "severely_fragmented": sum(m["severely_fragmented"] for m in metrics),
            "large_jumps": sum(m["large_jumps"] for m in metrics),
            "octave_like_events": sum(m["octave_like_events"] for m in metrics),
            "contaminated_spans": sum(m["contaminated_frames"] > 0 for m in metrics),
            "raw_filter_disagreement_frames_over6": sum(
                m["raw_filter_disagreement_over6"] for m in metrics
            ),
            "strong_agreement": {
                k: sum(s["agreement"][k] for s in units)
                for k in [
                    "strong_baseline_frames",
                    "alternate_missing",
                    "matched_frames",
                    "within_1st",
                    "octave_disagreements",
                ]
            },
            "recording_extraction_ms": quantiles(latency[name]),
            "amortized_extraction_per_numeric_span_ms": quantiles(span_latency[name]),
        }
        for row in output:
            for s in row["spans"]:
                old, new = s["methods"]["production"], s["methods"][name]
                keys = ["classification", "confidence", "reason"]
                if tuple(old["observed"][k] for k in keys) != tuple(
                    new["observed"][k] for k in keys
                ):
                    changes.append(
                        {
                            "method": name,
                            "utterance_id": row["utterance_id"],
                            "attempt_id": row["attempt_id"],
                            "target": row["target"],
                            "perceived_text": row["perceived_text"],
                            "span_index": s["index"],
                            "text": s["text"],
                            "expected": s["expected"],
                            "timing_authorized": s["timing_authorized"],
                            "old": old,
                            "new": new,
                        }
                    )
    write("summary.json", summary)
    write("classification-changes.json", changes)
    write(
        "experiment-provenance.json",
        {
            "parselmouth": parselmouth.VERSION,
            "praat": parselmouth.PRAAT_VERSION,
            "production_parameters": PARAMETERS,
            "dp_configs": DP,
            "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "production_analyze_sha256": hashlib.sha256(
                inspect.getsource(PraatAcousticAnalyzer.analyze).encode()
            ).hexdigest(),
            "new_dependencies": [],
            "interpolated_grading_points": 0,
            "identity_adapter_checked_recordings": len(corpus),
            "timing_note": "Three rotated whole-WAV repetitions; legacy once. Per-span = amortized recording cost, not cropped extraction.",
        },
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
