"""Fixed local corpus, native extraction, and separate character-free comparisons.

Run with the isolated environment documented in the report; never calls providers.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import resource
import subprocess
import time
from collections import Counter
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.f0_foundation import (
    ORIGINAL_TRACKERS as TRACKERS,
)
from benchmark.pronunciation_v2.f0_foundation import (
    PitchFrame,
    UtterancePitchTrack,
    basic_metrics,
    extract_utterance_pitch,
    known_f0_metrics,
    minimal_cleanup,
    read_audio,
    sample_nearest,
    synthetic_signals,
    write_audio,
)

REPO = Path(__file__).resolve().parents[2]
ROOT = Path("/tmp/benma-f0-bakeoff")
OLD = REPO / "services/api/var/capture-robustness"
LABELS = {
    "48c71bb4": "take_1",
    "cabf8d61": "take_2",
    "0cb79e67": "take_3",
    "c19a5a74": "google_old",
    "422877d2": "human_control",
    "de4b999e": "silence_original",
    "ab6c16ab": "silence_periodic",
    "7e489fd3": "silence_accidental",
}
NEGATIVE = {"de4b999e", "ab6c16ab", "7e489fd3"}


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def prepare(root: Path):
    from scipy.signal import butter, sosfiltfilt

    source = json.loads((OLD / "inventory-all.json").read_text())
    rows = []
    for item in source["recordings"]:
        prefix = item["perception"]["id"][:8]
        path = Path(item["canonical"]["path"])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["canonical"]["sha256"]
        original = Path(item["original"]["path"])
        assert hashlib.sha256(original.read_bytes()).hexdigest() == item["original"]["sha256"]
        analyses = [a for a in item["analyses"] if a.get("result")]
        syllables = analyses[-1]["result"].get("syllables", []) if analyses else []
        windows = [
            {"label": s["characters"], "start": s["start_seconds"], "end": s["end_seconds"]}
            for s in syllables
            if s.get("start_seconds") is not None and s["characters"] in {"苹", "一", "州", "吧"}
        ]
        text = item["perception"].get("transcript") or ""
        rows.append(
            {
                "id": LABELS.get(prefix, prefix),
                "audio_path": str(path),
                "perception_id": item["perception"]["id"],
                "utterance_id": item["utterance"]["id"],
                "created_at": item["perception"]["created_at"],
                "original_sha256": item["original"]["sha256"],
                "kind": "negative" if prefix in NEGATIVE else "capture",
                "apple_family": "苹果" in text and prefix not in NEGATIVE,
                "source_provenance": (
                    "user-identified Google playback"
                    if prefix == "c19a5a74"
                    else "user-identified human"
                    if prefix == "422877d2"
                    else "clean playback; exact provider/source unencoded"
                    if prefix in {"48c71bb4", "cabf8d61", "0cb79e67"}
                    else "user-identified no-speech"
                    if prefix in NEGATIVE
                    else "existing capture; speaker/playback source not proven by persistence"
                ),
                "lookup_text_only": text,
                "diagnostic_windows": windows,
            }
        )
    reference = source["references"][0]["audio"]
    native = Path(reference["path"])
    assert hashlib.sha256(native.read_bytes()).hexdigest() == reference["sha256"]
    rows.insert(
        0,
        {
            "id": "native_24k",
            "audio_path": str(native),
            "kind": "direct",
            "source_provenance": "cached Azure digital reference; exact bytes",
        },
    )
    audio, rate = read_audio(native)
    canonical = root / "audio/native_16k.wav"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    # Exact command used by audio.service.canonicalize; no ingest/guard/database call.
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-y",
            "-i",
            str(native),
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
    assert hashlib.sha256(canonical.read_bytes()).hexdigest() == (
        "88e6b9325b545a1c16e893f18b65b7645d2cfd7ccab7f35fb5df1b6788228fbe"
    )
    write_audio(root / "audio/native_gain.wav", audio * 0.25, rate)
    sos = butter(3, [100, 3500], btype="bandpass", fs=rate, output="sos")
    write_audio(root / "audio/native_bandlimit.wav", sosfiltfilt(sos, audio), rate)
    for name in ("native_16k", "native_gain", "native_bandlimit"):
        rows.append(
            {
                "id": name,
                "audio_path": str(root / "audio" / (name + ".wav")),
                "kind": "perturbation",
                "parent": "native_24k",
                "source_provenance": "deterministic transform of cached direct digital bytes",
            }
        )
    rows.extend(synthetic_signals(root / "audio"))
    for row in rows:
        path = Path(row["audio_path"])
        audio, rate = read_audio(path)
        row.update(
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            sample_rate_hz=rate,
            duration_seconds=len(audio) / rate,
            size_bytes=path.stat().st_size,
        )
    dump(root / "manifest.json", rows)
    return rows


def load_track(path: Path):
    data = json.loads(path.read_text())
    data["frames"] = tuple(
        PitchFrame(**{**f, "candidates": tuple(map(tuple, f["candidates"]))})
        for f in data["frames"]
    )
    return UtterancePitchTrack(**data)


def extract(root: Path, rows, only=None):
    """Raw phase. No Benma filter or cleanup is imported or evaluated here."""
    import importlib.metadata as metadata

    (root / "tracks").mkdir(exist_ok=True)
    (root / "activations").mkdir(exist_ok=True)
    timings_path = root / "timings.json"
    timings = json.loads(timings_path.read_text()) if timings_path.exists() else {}
    for tracker in [only] if only else TRACKERS:
        began = time.perf_counter()
        if tracker == "crepe_full":
            import torch
            import torchcrepe

            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            torch.use_deterministic_algorithms(True)
            torchcrepe.load.model("cpu", "full")
        timings.setdefault(tracker, {})["explicit_initialization_seconds"] = (
            time.perf_counter() - began
        )
        timings[tracker].setdefault("recordings", {})
        for row in rows:
            dest = root / "tracks" / f"{row['id']}--{tracker}.json"
            if dest.exists():
                continue
            started = time.perf_counter()
            cpu = time.process_time()
            track = extract_utterance_pitch(
                Path(row["audio_path"]),
                tracker,
                activations_path=root / "activations" / (row["id"] + ".npz")
                if tracker == "crepe_full"
                else None,
            )
            seconds = time.perf_counter() - started
            cpu_seconds = time.process_time() - cpu
            dest.write_bytes(track.canonical_bytes())
            timings[tracker]["recordings"][row["id"]] = {
                "wall_seconds": seconds,
                "cpu_seconds": cpu_seconds,
                "real_time_factor": seconds / row["duration_seconds"],
                "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
            dump(timings_path, timings)
            print(tracker, row["id"], round(seconds, 3), flush=True)
    packages = {}
    for name in (
        "numpy",
        "scipy",
        "praat-parselmouth",
        "librosa",
        "pyworld",
        "torch",
        "torchaudio",
        "numba",
        "llvmlite",
        "matplotlib",
        "resampy",
    ):
        dist = metadata.distribution(name)
        packages[name] = {
            "version": dist.version,
            "license": dist.metadata.get("License-Expression") or dist.metadata.get("License"),
            "location": str(dist.locate_file("")),
        }
    dump(
        root / "environment.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": packages,
            "threads": 1,
            "cpu": Path("/proc/cpuinfo").read_text().split("model name")[1].splitlines()[0],
        },
    )


def spectral_features(path: Path):
    """Audio-only utterance support and spectra; no tracker/text/timing access."""
    from scipy.signal import resample_poly

    audio, rate = read_audio(path)
    if rate != 16000:
        from math import gcd

        common = gcd(rate, 16000)
        audio = resample_poly(audio, 16000 // common, rate // common)
    frame, hop = 640, 160
    padded = np.pad(audio, (frame // 2, frame // 2))
    windows = np.lib.stride_tricks.sliding_window_view(padded, frame)[::hop]
    times = np.arange(len(windows)) * 0.01
    rms = np.sqrt(np.mean(windows**2, axis=1))
    power = abs(np.fft.rfft(windows * np.hanning(frame), n=1024)) ** 2
    frequencies = np.fft.rfftfreq(1024, 1 / 16000)
    edges = np.geomspace(80, 4000, 33)
    bands = np.column_stack(
        [
            power[:, (frequencies >= a) & (frequencies < b)].sum(axis=1)
            for a, b in itertools.pairwise(edges)
        ]
    )
    log = np.log(np.maximum(bands, 1e-10))
    log -= log.mean(axis=1, keepdims=True)
    log /= np.maximum(np.linalg.norm(log, axis=1, keepdims=True), 1e-12)
    active = np.flatnonzero(rms >= max(0.0015, 0.08 * np.quantile(rms, 0.95)))
    start, end = (
        (max(0, active[0] - 15), min(len(times), active[-1] + 16))
        if len(active)
        else (0, len(times))
    )
    return times[start:end], log[start:end], rms[start:end]


def align_audio(path_a: Path, path_b: Path):
    ta, a, ea = spectral_features(path_a)
    tb, b, eb = spectral_features(path_b)
    cost = 1 - np.clip(a @ b.T, -1, 1)
    n, m = cost.shape
    dp = np.full((n + 1, m + 1), np.inf)
    parent = np.zeros((n, m), np.int8)
    dp[0, 0] = 0
    for i in range(n):
        for j in range(m):
            if abs(i / max(n - 1, 1) - j / max(m - 1, 1)) > 0.25:
                continue
            choices = (dp[i, j], dp[i, j + 1] + 0.025, dp[i + 1, j] + 0.025)
            k = int(np.argmin(choices))
            dp[i + 1, j + 1] = cost[i, j] + choices[k]
            parent[i, j] = k
    i, j = n - 1, m - 1
    pairs = []
    while i >= 0 and j >= 0:
        pairs.append((i, j))
        step = parent[i, j]
        i -= step != 2
        j -= step != 1
    pairs.reverse()
    # One comparison per A frame: prevent long DTW holds from multiplying samples.
    aa = np.unique([p[0] for p in pairs])
    bb = np.array([round(np.median([y for x, y in pairs if x == i])) for i in aa])
    active = (ea[aa] >= max(0.0015, 0.08 * np.quantile(ea, 0.95))) & (
        eb[bb] >= max(0.0015, 0.08 * np.quantile(eb, 0.95))
    )
    return {
        "times_a": ta[aa].tolist(),
        "times_b": tb[bb].tolist(),
        "active": active.tolist(),
        "spectral_cosine": float(np.mean(1 - cost[aa[active], bb[active]])),
        "log_energy_correlation": float(
            np.corrcoef(np.log(ea[aa] + 1e-8), np.log(eb[bb] + 1e-8))[0, 1]
        ),
        "support_a": [float(ta[0]), float(ta[-1])],
        "support_b": [float(tb[0]), float(tb[-1])],
        "dtw_path_length": len(pairs),
        "unique_a_frames": len(aa),
    }


def pair_metrics(track_a, hz_a, track_b, hz_b, alignment):
    a = sample_nearest(track_a.arrays()[0], hz_a, np.array(alignment["times_a"]))
    b = sample_nearest(track_b.arrays()[0], hz_b, np.array(alignment["times_b"]))
    active = np.array(alignment["active"])
    mutual = np.isfinite(a) & np.isfinite(b) & active
    error = abs(12 * np.log2(a[mutual] / b[mutual]))
    # Broad contour: 50-ms local medians, only existing mutually voiced samples.
    logs_a = np.where(mutual, 12 * np.log2(a), np.nan)
    logs_b = np.where(mutual, 12 * np.log2(b), np.nan)
    smooth = []
    for logs in (logs_a, logs_b):
        smooth.append(
            np.array(
                [
                    np.median(v[np.isfinite(v)])
                    for i in np.flatnonzero(mutual)
                    if len(v := logs[max(0, i - 2) : i + 3])
                ]
            )
        )
    correlation = (
        float(np.corrcoef(*smooth)[0, 1])
        if len(error) > 2 and all(np.std(s) > 1e-8 for s in smooth)
        else None
    )
    return {
        "mutual_frames": int(mutual.sum()),
        "mutually_voiced_aligned_seconds": float(
            mutual.sum() * np.median(np.diff(alignment["times_a"]))
        ),
        "active_frames": int(active.sum()),
        "mutual_coverage": float(mutual.sum() / max(1, active.sum())),
        "median_st": float(np.median(error)) if len(error) else None,
        "p90_st": float(np.quantile(error, 0.9)) if len(error) else None,
        "octave_disagreement_rate": float((error > 9).mean()) if len(error) else None,
        "octave_disagreement_count": int((error > 9).sum()),
        "broad_contour_correlation": correlation,
        "voicing_agreement": float(np.mean((np.isfinite(a) == np.isfinite(b))[active])),
        "island_difference": abs(
            basic_metrics(track_a.arrays()[0], hz_a, track_a.arrays()[2])["islands"]
            - basic_metrics(track_b.arrays()[0], hz_b, track_b.arrays()[2])["islands"]
        ),
    }


def analyze(root: Path, rows):
    from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
    from benma_api.pronunciation.contours import display_contour

    summary = []
    tracks = {}
    clean = {}
    production = {}
    ablation = []
    window_rows = []
    (root / "production").mkdir(exist_ok=True)
    for row in rows:
        audio, _ = read_audio(Path(row["audio_path"]))
        for name in TRACKERS:
            track = load_track(root / "tracks" / f"{row['id']}--{name}.json")
            tracks[row["id"], name] = track
            times, hz, conf = track.arrays()
            cleaned = minimal_cleanup(track, audio)
            clean[row["id"], name] = cleaned
            for variant, values in (("raw", hz), ("minimal", cleaned)):
                metrics = basic_metrics(times, values, conf)
                if row.get("truth"):
                    metrics.update(known_f0_metrics(times, values, row["truth"]))
                summary.append(
                    {
                        "recording": row["id"],
                        "kind": row["kind"],
                        "tracker": name,
                        "variant": variant,
                        **metrics,
                    }
                )
                for window in row.get("diagnostic_windows", []):
                    mask = (times >= window["start"]) & (times < window["end"])
                    cut = values[mask]
                    valid = cut[np.isfinite(cut)]
                    n = max(1, round(len(valid) * 0.2))
                    change = (
                        float(12 * np.log2(np.median(valid[-n:]) / np.median(valid[:n])))
                        if len(valid) > 1
                        else None
                    )
                    window_rows.append(
                        {
                            "recording": row["id"],
                            "tracker": name,
                            "variant": variant,
                            **window,
                            **basic_metrics(times[mask], cut, conf[mask]),
                            "last_finite_seconds": float(times[mask][np.isfinite(cut)][-1])
                            if len(valid)
                            else None,
                            "first_last_quintile_change_st": change,
                        }
                    )
        # A separate call to the unchanged production analyzer, never used by candidates.
        result = PraatAcousticAnalyzer().analyze(Path(row["audio_path"]))
        diagnostics = []
        display = display_contour(result["f0"], diagnostics=diagnostics)
        retained = {p.timestamp_seconds for seg in display.segments for p in seg}
        times = np.array([p["timestamp_seconds"] for p in result["f0"]])
        hz = np.array([p["tracker_f0_hz"] for p in result["f0"]], dtype=float)
        selected = np.array(
            [p["f0_hz"] if p["timestamp_seconds"] in retained else None for p in result["f0"]],
            dtype=float,
        )
        conf = np.array([p["voicing_probability"] for p in result["f0"]])
        raw = tracks[row["id"], "praat_ac"].arrays()
        assert np.allclose(raw[0], times, atol=0.000051, rtol=0)
        assert np.allclose(raw[1], hz, atol=0.000501, rtol=0, equal_nan=True)
        # Preserve unrounded native frequencies; apply only the actual production retention mask.
        production[row["id"]] = np.where(np.isfinite(selected), raw[1], np.nan)
        production_metrics = basic_metrics(raw[0], production[row["id"]], raw[2])
        if row.get("truth"):
            production_metrics.update(known_f0_metrics(raw[0], production[row["id"]], row["truth"]))
        summary.append(
            {
                "recording": row["id"],
                "kind": row["kind"],
                "tracker": "praat_ac",
                "variant": "production",
                **production_metrics,
            }
        )
        dump(
            root / "production" / f"{row['id']}.json",
            {"result": result, "diagnostics": diagnostics, "retained_times": sorted(retained)},
        )
        ablation.append(
            {
                "recording": row["id"],
                "raw": basic_metrics(times, hz, conf),
                "retained": basic_metrics(times, selected, conf),
                "removed_frames": int((np.isfinite(hz) & ~np.isfinite(selected)).sum()),
                "reasons_overlapping": dict(Counter(r for d in diagnostics for r in d["reasons"])),
            }
        )
        for window in row.get("diagnostic_windows", []):
            mask = (times >= window["start"]) & (times < window["end"])
            valid = selected[mask][np.isfinite(selected[mask])]
            n = max(1, round(len(valid) * 0.2))
            window_rows.append(
                {
                    "recording": row["id"],
                    "tracker": "praat_ac",
                    "variant": "production",
                    **window,
                    **basic_metrics(times[mask], selected[mask], conf[mask]),
                    "last_finite_seconds": float(times[mask][np.isfinite(selected[mask])][-1])
                    if len(valid)
                    else None,
                    "first_last_quintile_change_st": float(
                        12 * np.log2(np.median(valid[-n:]) / np.median(valid[:n]))
                    )
                    if len(valid) > 1
                    else None,
                }
            )
    dump(root / "metrics.json", summary)
    dump(root / "ablation.json", ablation)
    dump(root / "windows.json", window_rows)
    pairs = []
    apple = [r for r in rows if r.get("apple_family")]
    (root / "alignments").mkdir(exist_ok=True)
    for a, b in itertools.combinations(apple, 2):
        alignment = align_audio(Path(a["audio_path"]), Path(b["audio_path"]))
        dump(root / "alignments" / f"{a['id']}--{b['id']}.json", alignment)
        for name in TRACKERS:
            for variant in (
                ("raw", "minimal", "production") if name == "praat_ac" else ("raw", "minimal")
            ):
                ta, tb = tracks[a["id"], name], tracks[b["id"], name]
                ha, hb = (
                    (ta.arrays()[1], tb.arrays()[1])
                    if variant == "raw"
                    else (clean[a["id"], name], clean[b["id"], name])
                )
                if variant == "production":
                    ha, hb = production[a["id"]], production[b["id"]]
                pairs.append(
                    {
                        "a": a["id"],
                        "b": b["id"],
                        "tracker": name,
                        "variant": variant,
                        "spectral_cosine": alignment["spectral_cosine"],
                        "log_energy_correlation": alignment["log_energy_correlation"],
                        **pair_metrics(ta, ha, tb, hb, alignment),
                    }
                )
    dump(root / "repeatability.json", pairs)
    perturbations = []
    for row in rows:
        if row["kind"] != "perturbation":
            continue
        queries = np.arange(0.03, 0.99, 0.01)
        alignment = {"times_a": queries, "times_b": queries, "active": np.ones(len(queries), bool)}
        for name in TRACKERS:
            a, b = tracks["native_24k", name], tracks[row["id"], name]
            for variant in ("raw", "minimal"):
                ha, hb = (
                    (a.arrays()[1], b.arrays()[1])
                    if variant == "raw"
                    else (clean["native_24k", name], clean[row["id"], name])
                )
                perturbations.append(
                    {
                        "a": "native_24k",
                        "b": row["id"],
                        "tracker": name,
                        "variant": variant,
                        **pair_metrics(a, ha, b, hb, alignment),
                    }
                )
    dump(root / "perturbations.json", perturbations)
    support_metrics(root, rows, tracks, clean, production)


def support_metrics(root, rows, tracks, clean, production):
    """Post-extraction acoustic review and the previous audit's low-F0 proxy cohort."""
    annotations = json.loads(Path(__file__).with_name("f0_acoustic_windows.json").read_text())
    annotated = []
    for row in rows:
        windows = annotations["recordings"].get(row["id"])
        if not windows:
            continue
        if "sha256" in windows:
            assert row["sha256"] == windows["sha256"]
        for name in TRACKERS:
            track = tracks[row["id"], name]
            times, hz, conf = track.arrays()
            views = [("raw", hz), ("minimal", clean[row["id"], name])]
            if name == "praat_ac":
                views.append(("production", production[row["id"]]))
            for variant, values in views:
                for kind in ("clearly_voiced", "nonvoiced"):
                    mask = np.zeros(len(times), dtype=bool)
                    for start, end in windows[kind]:
                        mask |= (times >= start) & (times < end)
                    annotated.append(
                        {
                            "recording": row["id"],
                            "tracker": name,
                            "variant": variant,
                            "region_kind": kind,
                            **basic_metrics(
                                times[mask],
                                values[mask],
                                conf[mask],
                                cadence_seconds=track.frame_cadence_seconds,
                            ),
                        }
                    )
                total = supported = emitted = 0
                for start, end, lower_hz, upper_hz in windows.get("harmonic_support", []):
                    mask = (times >= start) & (times < end)
                    total += int(mask.sum())
                    emitted += int((mask & np.isfinite(values)).sum())
                    supported += int((mask & (values >= lower_hz) & (values <= upper_hz)).sum())
                if total:
                    annotated.append(
                        {
                            "recording": row["id"],
                            "tracker": name,
                            "variant": variant,
                            "region_kind": "coarse_harmonic_band",
                            "frames": total,
                            "emitted_frames": emitted,
                            "supported_frames": supported,
                            "supported_fraction": supported / total,
                        }
                    )
    dump(root / "acoustic-support.json", annotated)
    inventory = json.loads((OLD / "inventory-all.json").read_text())
    proxy_rows = []
    low_70 = []
    proxy_samples = []
    for item in inventory["recordings"]:
        prefix = item["perception"]["id"][:8]
        if prefix in NEGATIVE:
            continue
        record = LABELS.get(prefix, prefix)
        analyses = [a for a in item["analyses"] if a.get("result")]
        if not analyses:
            continue
        units = analyses[-1]["result"].get("syllables", [])
        saved = json.loads((root / "production" / f"{record}.json").read_text())
        keep = set(saved["retained_times"])
        low = [
            p
            for p in saved["result"]["f0"]
            if p["timestamp_seconds"] in keep
            and p["f0_hz"] < 100
            and p["voicing_probability"] >= 0.8
            and p.get("comparison_f0_hz")
            and abs(12 * np.log2(p["f0_hz"] / p["comparison_f0_hz"])) <= 0.5
            and any(
                s.get("start_seconds") is not None
                and s["start_seconds"] <= p["timestamp_seconds"] < s["end_seconds"]
                for s in units
            )
        ]
        if not low:
            continue
        query = np.array([p["timestamp_seconds"] for p in low])
        reference = np.array([p["f0_hz"] for p in low])
        proxy_samples.append(
            {"recording": record, "times": query.tolist(), "baseline_hz": reference.tolist()}
        )
        for name in TRACKERS:
            track = tracks[record, name]
            ts, hz, conf = track.arrays()
            views = [("raw", hz), ("minimal", clean[record, name])]
            if name == "praat_ac":
                views.append(("production", production[record]))
            for variant, values in views:
                selected = sample_nearest(ts, values, query)
                confidence = sample_nearest(ts, conf, query)
                mask = np.isfinite(selected)
                difference = 12 * np.log2(selected[mask] / reference[mask])
                finite_conf = confidence[mask & np.isfinite(confidence)]
                continuity = basic_metrics(query, selected, confidence, cadence_seconds=0.01)
                proxy_rows.append(
                    {
                        "recording": record,
                        "tracker": name,
                        "variant": variant,
                        "proxy_frames": len(query),
                        "covered_frames": int(mask.sum()),
                        "median_hz": float(np.median(selected[mask])) if mask.any() else None,
                        "baseline_median_hz": float(np.median(reference)),
                        "median_abs_disagreement_st": float(np.median(abs(difference)))
                        if len(difference)
                        else None,
                        "doubled_frames": int((difference > 9).sum()),
                        "halved_frames": int((difference < -9).sum()),
                        "confidence_median": float(np.median(finite_conf))
                        if len(finite_conf)
                        else None,
                        "proxy_islands": continuity["islands"],
                        "longest_proxy_run_seconds": continuity["longest_run_seconds"],
                    }
                )
                under70 = reference <= 70
                if under70.any():
                    subset = selected[under70]
                    finite = np.isfinite(subset)
                    signed = 12 * np.log2(subset[finite] / reference[under70][finite])
                    scores = confidence[under70]
                    scores = scores[np.isfinite(scores)]
                    low_70.append(
                        {
                            "recording": record,
                            "tracker": name,
                            "variant": variant,
                            "proxy_frames": int(under70.sum()),
                            "covered_frames": int(finite.sum()),
                            "median_hz": float(np.median(subset[finite])) if finite.any() else None,
                            "doubled_frames": int((signed > 9).sum()),
                            "confidence_median": float(np.median(scores)) if len(scores) else None,
                        }
                    )
    dump(root / "low-f0-proxy.json", proxy_rows)
    dump(root / "low-f0-proxy-samples.json", proxy_samples)
    dump(root / "low-f0-under70.json", low_70)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "extract", "analyze"])
    parser.add_argument("--output", type=Path, default=ROOT)
    parser.add_argument("--tracker", choices=TRACKERS)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stage == "prepare":
        rows = prepare(args.output)
        print(len(rows), "fixed audio files")
    else:
        rows = json.loads((args.output / "manifest.json").read_text())
        if args.stage == "extract":
            extract(args.output, rows, args.tracker)
        else:
            analyze(args.output, rows)


if __name__ == "__main__":
    main()
