"""Run only RMVPE against the frozen corpus; reuse prior tracks and alignments."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.f0_foundation import (
    basic_metrics,
    extract_utterance_pitch,
    known_f0_metrics,
    sample_nearest,
    track_record,
)
from benchmark.pronunciation_v2.f0_foundation_rmvpe import (
    ROOT,
    SWEEP_THRESHOLDS,
    confidence_view,
    load_model,
)
from benchmark.pronunciation_v2.f0_foundation_run import dump, load_track, pair_metrics


def read(root: Path, name: str):
    return json.loads((root / f"{name}.json").read_text())


def verify_corpus(root: Path):
    rows = read(root, "manifest")
    frozen = read(root.parent, "manifest")
    assert len(rows) == len(frozen) == 49
    assert {r["id"]: r["sha256"] for r in rows} == {r["id"]: r["sha256"] for r in frozen}
    for row in rows:
        assert hashlib.sha256(Path(row["audio_path"]).read_bytes()).hexdigest() == row["sha256"]
    return rows


def verify(root: Path):
    """Fresh process timing and four-context real-waveform invariant before bakeoff."""
    cases = {r["id"]: r for r in verify_corpus(root)}
    started = time.perf_counter()
    model = load_model()
    result = {"explicit_initialization_seconds": time.perf_counter() - started, "warm_runs": []}
    started = time.perf_counter()
    first = extract_utterance_pitch(Path(cases["native_24k"]["audio_path"]), "rmvpe")
    result["first_inference_seconds"] = time.perf_counter() - started
    result["first_evidence_sha256"] = hashlib.sha256(first.canonical_bytes()).hexdigest()
    for case in ("native_24k", "human_control"):
        for iteration in range(3):
            started, cpu = time.perf_counter(), time.process_time()
            track = extract_utterance_pitch(Path(cases[case]["audio_path"]), "rmvpe")
            seconds = time.perf_counter() - started
            result["warm_runs"].append(
                {
                    "recording": case,
                    "iteration": iteration,
                    "duration_seconds": cases[case]["duration_seconds"],
                    "wall_seconds": seconds,
                    "cpu_seconds": time.process_time() - cpu,
                    "real_time_factor": seconds / cases[case]["duration_seconds"],
                    "evidence_sha256": hashlib.sha256(track.canonical_bytes()).hexdigest(),
                }
            )
    contexts = [
        {"transcript": "贵州", "pinyin": "gui4 zhou1", "tone": [4, 1]},
        {"transcript": "鬼粥", "pinyin": "invented", "tone": [1, 4]},
        {"transcript": "", "target": None},
        {"transcript": "zxq gibberish 123 !", "target": "nonsense", "expected_contour": "fake"},
    ]
    case = cases["f5dc0cc1"]
    outputs = [
        track_record({"audio_path": case["audio_path"], **c}, "rmvpe").canonical_bytes()
        for c in contexts
    ]
    assert all(o == outputs[0] for o in outputs), "STOP: metadata invariant failed"
    for name in ("native_24k", "human_control"):
        assert (
            len({r["evidence_sha256"] for r in result["warm_runs"] if r["recording"] == name}) == 1
        )
    assert result["first_evidence_sha256"] == result["warm_runs"][0]["evidence_sha256"]
    # Confirm adapter native decode is exactly the upstream public method.
    from benchmark.pronunciation_v2.f0_foundation import read_audio

    audio, rate = read_audio(Path(case["audio_path"]))
    assert rate == 16000
    native = model.infer_from_audio(audio.astype(np.float32), thred=0.03)
    wrapped = np.array([f["f0_hz"] or 0 for f in json.loads(outputs[0])["frames"]])
    np.testing.assert_array_equal(native, wrapped)
    result["invariance"] = {
        "recording": case["id"],
        "audio_sha256": case["sha256"],
        "contexts": contexts,
        "byte_identical": True,
        "evidence_sha256": hashlib.sha256(outputs[0]).hexdigest(),
    }
    result["upstream_public_method_identical"] = True
    result["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["median_warm_rtf"] = float(
        np.median([r["real_time_factor"] for r in result["warm_runs"]])
    )
    dump(root / "verification-rmvpe.json", result)
    print(
        "PASS: four metadata contexts, cold/warm determinism, upstream decoder equality", flush=True
    )


def extract_all(root: Path):
    rows = verify_corpus(root)
    assert read(root, "verification-rmvpe")["invariance"]["byte_identical"]
    timings = []
    started = time.perf_counter()
    load_model()
    initialization = time.perf_counter() - started
    for row in rows:
        destination = root / "tracks" / f"{row['id']}--rmvpe.json"
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite raw extraction: {destination}")
        started, cpu = time.perf_counter(), time.process_time()
        track = extract_utterance_pitch(
            Path(row["audio_path"]),
            "rmvpe",
            activations_path=root / "activations" / f"{row['id']}.npz",
        )
        seconds = time.perf_counter() - started
        destination.write_bytes(track.canonical_bytes())
        timings.append(
            {
                "recording": row["id"],
                "wall_seconds": seconds,
                "cpu_seconds": time.process_time() - cpu,
                "real_time_factor": seconds / row["duration_seconds"],
                "duration_seconds": row["duration_seconds"],
                "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
        )
        dump(
            root / "timings.json", {"initialization_seconds": initialization, "recordings": timings}
        )
        print(f"{len(timings)}/49 {row['id']}: {seconds:.3f}s", flush=True)


def proxy_metrics(track, values, sample):
    query, reference = np.array(sample["times"]), np.array(sample["baseline_hz"])
    ts, _, conf = track.arrays()
    selected = sample_nearest(ts, values, query)
    confidence = sample_nearest(ts, conf, query)
    mask = np.isfinite(selected)
    difference = 12 * np.log2(selected[mask] / reference[mask])
    continuity = basic_metrics(query, selected, confidence, cadence_seconds=0.01)
    return {
        "proxy_frames": len(query),
        "covered_frames": int(mask.sum()),
        "missing_frames": int((~mask).sum()),
        "median_hz": continuity["median_hz"],
        "baseline_median_hz": float(np.median(reference)),
        "median_abs_disagreement_st": float(np.median(abs(difference)))
        if len(difference)
        else None,
        "doubled_frames": int((difference > 9).sum()),
        "halved_frames": int((difference < -9).sum()),
        "confidence_median": continuity["confidence_median"],
        "all_proxy_confidence_median": float(np.median(confidence)),
        "proxy_islands": continuity["islands"],
        "longest_proxy_run_seconds": continuity["longest_run_seconds"],
    }


def analyze(root: Path):
    """Only new numerical rows; never rerun previous estimators, alignment or filters."""
    rows = verify_corpus(root)
    annotations = json.loads(Path(__file__).with_name("f0_acoustic_windows.json").read_text())[
        "recordings"
    ]
    samples = read(root.parent, "low-f0-proxy-samples")
    tracks, views = {}, {}
    metrics, windows, support, low, lowest, sweep = [], [], [], [], [], []
    for row in rows:
        ident = row["id"]
        track = tracks[ident] = load_track(root / "tracks" / f"{ident}--rmvpe.json")
        times, hz, conf = track.arrays()
        views[ident] = {"raw": hz, "minimal": confidence_view(track)}
        for variant, values in views[ident].items():
            common = {"recording": ident, "tracker": "rmvpe", "variant": variant}
            measured = basic_metrics(times, values, conf)
            if row.get("truth"):
                measured.update(known_f0_metrics(times, values, row["truth"]))
            metrics.append({**common, "kind": row["kind"], **measured})
            for window in row.get("diagnostic_windows", []):
                mask = (times >= window["start"]) & (times < window["end"])
                valid = values[mask][np.isfinite(values[mask])]
                n = max(1, round(len(valid) * 0.2))
                windows.append(
                    {
                        **common,
                        **window,
                        **basic_metrics(times[mask], values[mask], conf[mask]),
                        "last_finite_seconds": float(times[mask][np.isfinite(values[mask])][-1])
                        if len(valid)
                        else None,
                        "first_last_quintile_change_st": float(
                            12 * np.log2(np.median(valid[-n:]) / np.median(valid[:n]))
                        )
                        if len(valid) > 1
                        else None,
                    }
                )
            if ident in annotations:
                annotation = annotations[ident]
                for kind in ("clearly_voiced", "nonvoiced"):
                    mask = np.zeros(len(times), bool)
                    for start, end in annotation[kind]:
                        mask |= (times >= start) & (times < end)
                    support.append(
                        {
                            **common,
                            "region_kind": kind,
                            **basic_metrics(
                                times[mask], values[mask], conf[mask], cadence_seconds=0.01
                            ),
                        }
                    )
                total = emitted = supported = 0
                for start, end, lower, upper in annotation.get("harmonic_support", []):
                    mask = (times >= start) & (times < end)
                    total += int(mask.sum())
                    emitted += int((mask & np.isfinite(values)).sum())
                    supported += int((mask & (values >= lower) & (values <= upper)).sum())
                if total:
                    support.append(
                        {
                            **common,
                            "region_kind": "coarse_harmonic_band",
                            "frames": total,
                            "emitted_frames": emitted,
                            "supported_frames": supported,
                            "supported_fraction": supported / total,
                        }
                    )
            for sample in (s for s in samples if s["recording"] == ident):
                low.append({**common, **proxy_metrics(track, values, sample)})
                mask = np.array(sample["baseline_hz"]) <= 70
                if mask.any():
                    subset = {
                        k: np.array(sample[k])[mask].tolist() for k in ("times", "baseline_hz")
                    }
                    lowest.append({**common, **proxy_metrics(track, values, subset)})
        evidence = np.load(root / "activations" / f"{ident}.npz")
        for threshold in SWEEP_THRESHOLDS:
            values = np.where(evidence["confidence"] > threshold, evidence["ungated_f0_hz"], np.nan)
            item = {
                "recording": ident,
                "threshold": threshold,
                "kind": row["kind"],
                **basic_metrics(times, values, conf),
            }
            if row.get("truth"):
                item.update(known_f0_metrics(times, values, row["truth"]))
            for sample in (s for s in samples if s["recording"] == ident):
                item["proxy"] = proxy_metrics(track, values, sample)
                mask = np.array(sample["baseline_hz"]) <= 70
                if mask.any():
                    subset = {
                        k: np.array(sample[k])[mask].tolist() for k in ("times", "baseline_hz")
                    }
                    item["under70"] = proxy_metrics(track, values, subset)
            if ident in annotations:
                annotation = annotations[ident]
                item["harmonic_frames"] = item["harmonic_supported_frames"] = 0
                for start, end, lower, upper in annotation.get("harmonic_support", []):
                    mask = (times >= start) & (times < end)
                    item["harmonic_frames"] += int(mask.sum())
                    item["harmonic_supported_frames"] += int(
                        (mask & (values >= lower) & (values <= upper)).sum()
                    )
            sweep.append(item)
    pairs = []
    for path in sorted((root.parent / "alignments").glob("*.json")):
        a, b = path.stem.split("--")
        alignment = json.loads(path.read_text())
        for variant in ("raw", "minimal"):
            pairs.append(
                {
                    "a": a,
                    "b": b,
                    "tracker": "rmvpe",
                    "variant": variant,
                    "spectral_cosine": alignment["spectral_cosine"],
                    "log_energy_correlation": alignment["log_energy_correlation"],
                    **pair_metrics(
                        tracks[a], views[a][variant], tracks[b], views[b][variant], alignment
                    ),
                }
            )
    perturbations = []
    for row in (r for r in rows if r["kind"] == "perturbation"):
        a, b = "native_24k", row["id"]
        query = np.arange(0.03, 0.99, 0.01)
        alignment = {"times_a": query, "times_b": query, "active": np.ones(len(query), bool)}
        for variant in ("raw", "minimal"):
            perturbations.append(
                {
                    "a": a,
                    "b": b,
                    "tracker": "rmvpe",
                    "variant": variant,
                    **pair_metrics(
                        tracks[a], views[a][variant], tracks[b], views[b][variant], alignment
                    ),
                }
            )
    for name, values in (
        ("metrics", metrics),
        ("windows", windows),
        ("acoustic-support", support),
        ("low-f0-proxy", low),
        ("low-f0-under70", lowest),
        ("threshold-sweep", sweep),
        ("repeatability", pairs),
        ("perturbations", perturbations),
    ):
        dump(root / f"{name}.json", values)
    print("Saved RMVPE metrics; all previous results and alignment paths reused.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["verify", "extract", "analyze"])
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    {"verify": verify, "extract": extract_all, "analyze": analyze}[args.phase](args.output)
