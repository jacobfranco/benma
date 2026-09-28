"""Offline review of a local, read-only calibration snapshot; never calls providers.

Input DIR contains corpus.json and <utterance UUID>.wav canonical recordings.
corpus.json: [{id, acoustic: <persisted normalized result>, spans: [{characters,
start_seconds, end_seconds, expected_surface_tone, locally_recomputed_contour}]}].
This is a developer snapshot, NOT a labeled pilot corpus. No pilot count is changed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import parselmouth

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.evidence_region import select_tone_evidence
from benma_api.schemas import ObservedContour


def distribution(values):
    ordered = sorted(values)
    return {
        "median_ms": statistics.median(ordered),
        "p95_ms": ordered[min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1)],
        "maximum_ms": max(ordered),
    }


def tracker_comparison(sound, persisted, spans):
    """Diagnostic alternatives, NOT replacements for the production quality pipeline.

    Gaussian experiment follows Praat's documented .03 ** (f / 800) ** 2 filter.
    Bundled Praat 6.1.38 predates the official filtered-AC command. This experiment
    is labeled separately and is not claimed to reproduce modern Praat exactly.
    """
    params = {
        k: v
        for k, v in PraatAcousticAnalyzer().parameters.items()
        if k not in {"energy_gate", "quality_gate"}
    }
    values, rate = sound.values[0], sound.sampling_frequency
    outputs = {}
    for name in ["raw_ac", "default_jump_ac", "raw_cc", "gaussian_experiment"]:
        samples = []
        for _ in range(3):
            started = time.perf_counter()
            source, options = sound, params
            if name == "default_jump_ac":
                options = {**params, "octave_jump_cost": 0.35}
            elif name == "gaussian_experiment":
                n = 2 ** math.ceil(math.log2(len(values) * 2))
                frequencies = np.fft.rfftfreq(n, 1 / rate)
                filtered = np.fft.irfft(
                    np.fft.rfft(values, n) * 0.03 ** ((frequencies / 800) ** 2), n
                )
                source = parselmouth.Sound(filtered[: len(values)], rate)
                options = {
                    **params,
                    "pitch_ceiling": 800,
                    "voicing_threshold": 0.5,
                    "octave_cost": 0.055,
                    "silence_threshold": 0.09,
                    "octave_jump_cost": 0.35,
                }
            pitch = (
                source.to_pitch_cc(**options) if name == "raw_cc" else source.to_pitch_ac(**options)
            )
            samples.append((time.perf_counter() - started) * 1000)
        raw = []
        threshold = persisted.get("energy_gate", {}).get("threshold_rms", 0.003)
        for t, hz, strength in zip(
            pitch.xs(),
            pitch.selected_array["frequency"],
            pitch.selected_array["strength"],
            strict=True,
        ):
            center, width = round(t * rate), round(rate * 0.02)
            rms = float(np.sqrt(np.mean(values[max(0, center - width) : center + width] ** 2)))
            raw.append(
                {
                    "timestamp_seconds": round(float(t), 4),
                    "f0_hz": float(hz) if hz and rms >= threshold else None,
                    "voicing_probability": float(strength),
                }
            )
        outputs[name] = {
            "timing": distribution(samples),
            "syllables": [
                classify_contour(
                    display_contour(raw), s["start_seconds"], s["end_seconds"], raw=raw
                ).model_dump()
                for s in spans
            ],
        }
    return outputs


def apply_timing_authority(syllable, source):
    """Keep hypothetical DSP probes outside learner truth for rejected timing."""
    production = source.get("locally_recomputed_contour") or {}
    authorized = (
        bool(production)
        and production.get("reason")
        not in {
            "timing_unavailable",
            "synthetic_timing",
        }
        and source.get("timing_resolution", {}).get("accepted", True)
    )
    syllable["timing_authorized"] = bool(authorized)
    if authorized:
        return
    keys = ["old", "new", "from_audio", "from_audio_before", "region", "from_audio_region"]
    syllable["diagnostic_only_unvalidated_timing_probe"] = {k: syllable[k] for k in keys}
    for key in keys[:4]:
        syllable[key] = production or ObservedContour(reason="timing_unavailable").model_dump()
    for key in keys[4:]:
        syllable[key] = {"method": "timing_rejected", "start": None, "end": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline-contours", type=Path, required=True)
    parser.add_argument("--compare-trackers", action="store_true")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("baseline_contours", args.baseline_contours)
    assert spec and spec.loader
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    corpus = json.loads((args.corpus / "corpus.json").read_text())
    analyzer = PraatAcousticAnalyzer()
    output = []
    for row in corpus:
        path = args.corpus / (row["id"] + ".wav")
        new = analyzer.analyze(path)
        latencies = {"before": [], "after": []}
        for name, classifier in [
            ("before", baseline.classify_contour),
            ("after", classify_contour),
        ]:
            for _ in range(7):
                started = time.perf_counter()
                fresh = analyzer.analyze(path)
                contour = display_contour(fresh["f0"])
                for s in row["spans"]:
                    classifier(contour, s["start_seconds"], s["end_seconds"], raw=fresh["f0"])
                latencies[name].append((time.perf_counter() - started) * 1000)
        syllables = []
        for s in row["spans"]:
            a, b = s["start_seconds"], s["end_seconds"]
            old_raw = row["acoustic"]["f0"]
            old = baseline.classify_contour(display_contour(old_raw), a, b, raw=old_raw)
            current = classify_contour(display_contour(old_raw), a, b, raw=old_raw)
            recomputed = classify_contour(display_contour(new["f0"]), a, b, raw=new["f0"])
            recomputed_before = baseline.classify_contour(
                display_contour(new["f0"]), a, b, raw=new["f0"]
            )
            syllables.append(
                {
                    "text": s["characters"],
                    "expected": s.get("expected_surface_tone"),
                    "production_before": s.get("locally_recomputed_contour"),
                    "old": old.model_dump(),
                    "new": current.model_dump(),
                    "from_audio": recomputed.model_dump(),
                    "from_audio_before": recomputed_before.model_dump(),
                    "region": asdict(select_tone_evidence(old_raw, a, b)),
                    "from_audio_region": asdict(select_tone_evidence(new["f0"], a, b)),
                }
            )
            apply_timing_authority(syllables[-1], s)
        item = {
            "utterance_id": row["id"],
            "syllables": syllables,
            "latency": {k: distribution(v) for k, v in latencies.items()},
        }
        if args.compare_trackers:
            item["tracker_experiments"] = tracker_comparison(
                parselmouth.Sound(str(path)), row["acoustic"], row["spans"]
            )
        output.append(item)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "recomputation.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"{len(output)} recordings / {sum(len(r['syllables']) for r in output)} syllables; "
        "no pilot labels inferred"
    )
    for name in ["before", "after"]:
        print(name, distribution([r["latency"][name]["median_ms"] for r in output]))


if __name__ == "__main__":
    main()
