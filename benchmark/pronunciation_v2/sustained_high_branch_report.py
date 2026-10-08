"""Offline, single-issue sustained-high forensic replay and review artifacts.

Run after the unchanged production extraction is captured in private var/.
--extract reproduces that capture and decodes ONLY the named original M4A.
No provider, alternative tracker, VAD, model, or production mutation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import statistics
import subprocess
from pathlib import Path

import numpy as np
from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.pitch_evidence import (
    display_from_track,
    interpretation_eligibility,
    project_pitch,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence

from benchmark.pronunciation_v2.octave_ambiguity import branches, semitones
from benchmark.pronunciation_v2.octave_ambiguity_report import (
    CANONICAL,
    IDS,
    LOCAL,
    REPORT,
    ROOT,
    SAVED,
    check_preservation,
    dump,
    make_track,
    masked_track,
    metrics,
    old_rules,
    samples,
)
from benchmark.pronunciation_v2.sustained_high_branch import (
    nearest_candidate,
    period_evidence,
    run_features,
    screening_failures,
    spectral_evidence,
    spectral_slice,
)

OUT = LOCAL / "sustained-high"
ORIGINAL = CANONICAL.parent / "original/38fdbad3dc624c0997c2eac2bf802d80.m4a"
TARGET = CANONICAL / (IDS[1] + ".wav")


def extract() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    analyzer = PraatAcousticAnalyzer()
    result = analyzer.analyze(TARGET)
    baseline = json.loads((LOCAL / "before" / (IDS[1] + ".json")).read_text())
    assert result == baseline["result"], "Production extraction differs from prior baseline"
    track = make_track(result)
    dump(
        OUT / "production-exact.json",
        dict(
            sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),
            algorithm=analyzer.algorithm_version,
            parameters=analyzer.parameters,
            baseline_exact=True,
            result=result,
            track=track.model_dump(mode="json"),
            metrics=metrics(track, result["f0"]),
        ),
    )
    for name, flags in (
        ("original-native-mono.wav", []),
        ("original-recanonicalized.wav", ["-ar", "16000"]),
    ):
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-nostdin",
                "-y",
                "-i",
                str(ORIGINAL),
                "-ac",
                "1",
                *flags,
                "-c:a",
                "pcm_s16le",
                str(OUT / name),
            ],
            check=True,
        )
    dump(OUT / "original-native-result.json", analyzer.analyze(OUT / "original-native-mono.wav"))
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-y",
            "-i",
            str(TARGET),
            "-ss",
            "3.8",
            "-t",
            "0.8",
            "-c:a",
            "pcm_s16le",
            str(OUT / "private-3.8-4.6.wav"),
        ],
        check=True,
    )


def frame_table(result: dict, frames: list[dict], indices: list[int], ratio: float) -> list[dict]:
    guards = old_rules(result["f0"])
    before = [f for f in frames[: indices[0]] if f["selected_f0_hz"]][-5:]
    after = [f for f in frames[indices[-1] + 1 :] if f["selected_f0_hz"]][:5]
    anchors = {
        name: statistics.median(f["selected_f0_hz"] for f in fs) if fs else None
        for name, fs in (("preceding", before), ("following", after))
    }
    rows = []
    for i in indices:
        f = frames[i]
        alternate = nearest_candidate(f, ratio, 2.0)
        strict = nearest_candidate(f, ratio)
        row = dict(
            source_index=i,
            timestamp_seconds=f["timestamp_seconds"],
            tracker_selected_hz=f["raw_f0_hz"],
            selected_strength=f["periodicity"],
            production_selected_hz=f["selected_f0_hz"],
            alternate_hz=alternate["frequency_hz"] if alternate else None,
            alternate_strength=alternate["strength"] if alternate else None,
            alternate_status="within_1st"
            if strict
            else "near_half_or_double_but_not_octave_within_1st"
            if alternate
            else "absent_even_within_2st",
            strength_deficit=f["periodicity"] - alternate["strength"] if alternate else None,
            octave_ratio_error_st=alternate["octave_error_st"] if alternate else None,
            all_candidates=f["candidates"],
            other_strong_candidates=[
                c
                for c in f["candidates"]
                if c["strength"] >= 0.45
                and c["frequency_hz"]
                not in (f["raw_f0_hz"], alternate["frequency_hz"] if alternate else None)
            ],
            analyzer_reason=result["f0"][i]["selection_reason"],
            production_exclusion_reasons=f["exclusion_reasons"],
            energy_rms=f["energy_rms"],
            comparison_f0_hz=f["comparison_f0_hz"],
            old_guards=guards[i],
            display_semitones=f["display_semitones"],
            anchors_hz=anchors,
        )
        for name, anchor in anchors.items():
            row[f"{name}_selected_distance_st"] = (
                abs(semitones(f["raw_f0_hz"] / anchor)) if anchor else None
            )
            row[f"{name}_alternate_distance_st"] = (
                abs(semitones(alternate["frequency_hz"] / anchor)) if anchor and alternate else None
            )
        rows.append(row)
    return rows


def replay_one(result: dict, protected: set[float]) -> dict:
    track = make_track(result)
    frames = track.model_dump(mode="json")["frames"]
    features = [run_features(frames, run) for run in branches(frames)]
    flagged = set()
    for feature in features:
        for path in feature["paths"]:
            path["screen_failures"] = screening_failures(feature, path)
            if not path["screen_failures"]:
                flagged.update(feature["indices"])
    flagged_times = [frames[i]["timestamp_seconds"] for i in sorted(flagged)]
    selected = {f.timestamp_seconds for f in track.frames if f.selected_f0_hz}
    assert protected <= selected
    return dict(
        selected_frames=len(selected),
        protected_count=len(protected),
        screened_indices=sorted(flagged),
        screened_times=flagged_times,
        protected_screened=sorted(protected & set(flagged_times)),
        features=features,
    )


def signal_transition(rate: int, x: np.ndarray, timestamps: list[float]) -> list[dict]:
    rows = []
    for t in timestamps:
        f, p = spectral_slice(rate, x, t, 0.04)
        band = (f >= 40) & (f <= 4000)
        total = max(float(p[band].sum()), 1e-30)
        center = round(t * rate)
        z = x[max(0, center - round(rate * 0.02)) : center + round(rate * 0.02)]
        rows.append(
            dict(
                timestamp_seconds=t,
                rms=float(np.sqrt(np.mean(z**2))),
                centroid_hz=float((f[band] * p[band]).sum() / total),
                bands=[
                    float(p[(f >= lo) & (f < hi)].sum() / total)
                    for lo, hi in ((40, 150), (150, 300), (300, 500), (500, 1000), (1000, 4000))
                ],
            )
        )
    return rows


def make_plots(
    data: dict, target_track, low_track, x: np.ndarray, low_x: np.ndarray, low_rate: int
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10})
    tracks = [target_track, low_track]
    signals = [(16000, x), (low_rate, low_x)]
    windows = [(3.8, 4.65), (2.18, 2.83)]
    highlights = [(4.1002, 4.3402), (2.4824, 2.5124)]
    fig, axs = plt.subplots(5, 2, figsize=(16, 15), layout="constrained")
    for col, (track, (rate, values), win, event) in enumerate(
        zip(tracks, signals, windows, highlights, strict=True)
    ):
        a, b = win
        t = np.arange(len(values)) / rate
        mask = (t >= a) & (t <= b)
        axs[0, col].plot(t[mask], values[mask], lw=0.45, color="#314d69")
        axs[0, col].set_title(
            "8d252264: sustained high branch" if col == 0 else "7787300e: protected 54.610 Hz"
        )
        axs[0, col].set_ylabel("PCM amplitude")
        ts = np.arange(a, b, 0.0025)
        spectra = [spectral_slice(rate, values, ts_, 0.06) for ts_ in ts]
        freq = spectra[0][0]
        maskf = (freq >= 40) & (freq <= 1200)
        power = np.array([p[maskf] for _, p in spectra]).T
        db = 10 * np.log10(np.maximum(power / power.max(), 1e-8))
        axs[1, col].imshow(
            db,
            extent=(ts[0], ts[-1], freq[maskf][0], freq[maskf][-1]),
            origin="lower",
            aspect="auto",
            vmin=-45,
            vmax=0,
            cmap="magma",
        )
        axs[1, col].set_title("60 ms Hann / 2.5 ms hop; 16.7 Hz native bins")
        axs[1, col].set_ylabel("Spectrum Hz")
        fs = track.model_dump(mode="json")["frames"]
        for f in fs:
            if not a <= f["timestamp_seconds"] <= b:
                continue
            for c in f["candidates"]:
                if c["strength"] >= 0.45:
                    axs[2, col].scatter(
                        f["timestamp_seconds"],
                        c["frequency_hz"],
                        color="#b76800",
                        alpha=c["strength"],
                        s=12,
                    )
            alt = nearest_candidate(f, 0.5 if col == 0 else 2, 2)
            if event[0] <= f["timestamp_seconds"] <= event[1] and alt:
                axs[2, col].scatter(
                    f["timestamp_seconds"],
                    alt["frequency_hz"],
                    facecolors="none",
                    edgecolors="#8f36a5",
                    s=30,
                )
        times = [f.timestamp_seconds for f in track.frames]
        raw = [f.raw_f0_hz if f.raw_f0_hz else np.nan for f in track.frames]
        sel = [f.selected_f0_hz if f.selected_f0_hz else np.nan for f in track.frames]
        axs[2, col].plot(times, raw, ":", color="#555", lw=1, label="Raw tracker")
        axs[2, col].plot(
            times, sel, "o-", color="#007b8c", markersize=2, lw=1, label="Production selected"
        )
        axs[2, col].set_ylim(40, 550)
        axs[2, col].set_ylabel("Candidates Hz")
        axs[2, col].set_title(
            "Orange: strength ≥ .45; purple rings: measured near-octave alternate (≤2 st)"
        )
        axs[2, col].legend(loc="upper left", fontsize=8)
        for row in range(4):
            axs[row, col].set_xlim(a, b)
            axs[row, col].axvspan(*event, color="#fa9b4b", alpha=0.12)
        display = [
            f.display_semitones if f.display_semitones is not None else np.nan for f in track.frames
        ]
        domain = data["graph"]["before" if col == 0 else "protected"]["mine_domain"]
        axs[3, col].plot(times, display, color="#007b8c", lw=1.3, label="Before = actual after")
        axs[3, col].set_ylim(domain)
        axs[3, col].set_title(f"Actual graph domain unchanged: {domain[0]:.3f}…{domain[1]:.3f} st")
        axs[3, col].set_ylabel("Mine semitones")
        axs[3, col].legend(fontsize=8)
        axs[4, col].plot(times, display, color="#007b8c", lw=1, label="Current")
        if col == 0:
            after = masked_track(track, data["target"]["indices"])
            axs[4, col].plot(
                times,
                [
                    f.display_semitones if f.display_semitones is not None else np.nan
                    for f in after.frames
                ],
                color="#b34736",
                lw=1,
                label="Deletion-only illustration; NOT a rule",
            )
            axs[4, col].set_title("Whole-recording geometry; no alternate frequency is inserted")
        else:
            axs[4, col].set_title("Whole recording; all protected evidence retained")
        axs[4, col].set_ylim(domain)
        axs[4, col].set_ylabel("Mine semitones")
        axs[4, col].set_xlabel("Acoustic time (seconds)")
        axs[4, col].legend(fontsize=8)
    fig.suptitle(
        "Sustained-high forensics — production unchanged; no safe run-level rule", fontsize=16
    )
    fig.savefig(OUT / "comparison.png", dpi=150)
    fig.savefig(OUT / "comparison.pdf")
    plt.close(fig)

    # Representative slices include endpoints and late candidate-poor frames.
    selected = [("target", t) for t in (4.1002, 4.1702, 4.2102, 4.2602, 4.3102, 4.3402)] + [
        ("protected", t) for t in (2.5024, 2.5124)
    ]
    fig, axs = plt.subplots(len(selected), 3, figsize=(18, 21), layout="constrained")
    for row, (kind, stamp) in enumerate(selected):
        rate, values = signals[0 if kind == "target" else 1]
        source = data[kind]["acoustic"]
        e = next(e for e in source if e["timestamp_seconds"] == stamp)
        hz = e["selected_hz"]
        guides = (
            ((1, "#009190"), (0.5, "#9d4aae"), (0.25, "#8a8a8a"))
            if kind == "target"
            else ((1, "#009190"), (2, "#9d4aae"))
        )
        for width, color in ((0.06, "#234f70"), (0.1, "#bb8045")):
            f, p = spectral_slice(rate, values, stamp, width)
            m = (f >= 40) & (f <= 1200)
            axs[row, 0].plot(
                f[m],
                10 * np.log10(np.maximum(p[m] / p[m].max(), 1e-8)),
                color=color,
                lw=0.8,
                label=f"{width * 1000:.0f} ms",
            )
        for ratio, color in guides:
            axs[row, 0].axvline(hz * ratio, color=color, ls="--", lw=0.8)
        axs[row, 0].set_ylim(-50, 2)
        axs[row, 0].set_title(f"{kind} {stamp:.4f} s · selected {hz:.3f} Hz")
        axs[row, 0].set_ylabel("Relative dB")
        axs[row, 0].legend(fontsize=7)
        w = e["periodicity"]["0.06"]
        axs[row, 1].plot(w["lag_ms"], w["correlation"], color="#234f70")
        for ratio, color in guides:
            period = 1000 / (hz * ratio)
            if period < 23:
                axs[row, 1].axvline(period, color=color, ls="--", lw=0.8)
        axs[row, 1].set_ylim(-1, 1)
        axs[row, 1].set_title("Unfiltered waveform self-similarity (60 ms)")
        axs[row, 1].set_ylabel("Normalized correlation")
        c, half = round(stamp * rate), round(0.025 * rate)
        axs[row, 2].plot(
            np.arange(-half, half) / rate * 1000,
            values[c - half : c + half],
            color="#234f70",
            lw=0.7,
        )
        axs[row, 2].set_title("50 ms waveform; no pitch correction")
        axs[row, 2].set_ylabel("PCM amplitude")
    for col, title in enumerate(("Frequency Hz", "Lag ms", "Time from center ms")):
        axs[-1, col].set_xlabel(title)
    fig.suptitle(
        "Green: selected; purple: half (target) / double (control); gray: quarter (target)",
        fontsize=14,
    )
    fig.savefig(OUT / "spectral-periodicity.png", dpi=130)
    fig.savefig(OUT / "spectral-periodicity.pdf")
    plt.close(fig)

    native_rate, native = samples(OUT / "original-native-mono.wav")
    fig, axs = plt.subplots(3, 1, figsize=(13, 10), layout="constrained")
    for sr, signal, name, style in (
        (16000, x, "canonical 16 kHz", "-"),
        (native_rate, native, "original 44.1 kHz mono", "--"),
    ):
        ts = np.arange(len(signal)) / sr
        mask = (ts >= 4.19) & (ts <= 4.24)
        axs[0].plot(ts[mask], signal[mask], style, lw=0.8, label=name)
        f, p = spectral_slice(sr, signal, 4.2102, 0.06)
        m = (f >= 40) & (f <= 1000)
        axs[1].plot(
            f[m], 10 * np.log10(np.maximum(p[m] / p[m].max(), 1e-8)), style, lw=1, label=name
        )
    for field, label in (
        ("canonical_hz", "Canonical selected"),
        ("original_hz", "Native original selected"),
    ):
        rows = data["original_comparison"]["rows"]
        axs[2].plot(
            [r["timestamp_seconds"] for r in rows],
            [r[field] for r in rows],
            "o-" if field == "canonical_hz" else "x--",
            markersize=4,
            label=label,
        )
    axs[0].set_title("Direct waveform overlay; original stereo channels are sample-identical")
    axs[0].set_xlabel("Time seconds")
    axs[1].set_title("Harmonic-spacing overlay at 4.2102 s; 60 ms Hann")
    axs[1].set_ylim(-50, 2)
    axs[1].set_xlabel("Frequency Hz")
    axs[2].set_title(
        "Same Praat configuration, native-rate original vs canonical: all 25 raw selections"
    )
    axs[2].set_xlabel("Time seconds")
    for ax in axs:
        ax.legend()
    fig.savefig(OUT / "original-comparison.png", dpi=140)
    plt.close(fig)


def make_viewer(data: dict) -> None:
    fields = (
        "timestamp_seconds",
        "tracker_selected_hz",
        "selected_strength",
        "production_selected_hz",
        "alternate_hz",
        "alternate_strength",
        "strength_deficit",
        "octave_ratio_error_st",
        "all_candidates",
    )
    tables = []
    for key in ("target", "protected"):
        head = "<tr>" + "".join(f"<th>{html.escape(k)}</th>" for k in fields) + "</tr>"
        body = "".join(
            "<tr>"
            + "".join(f"<td>{html.escape(json.dumps(row[k]))}</td>" for k in fields)
            + "</tr>"
            for row in data[key]["table"]
        )
        tables.append(
            f"<h2>{key.title()} — every frame</h2>"
            f"<div class='table'><table>{head}{body}</table></div>"
        )
    template = (ROOT / "benchmark/pronunciation_v2/sustained_high_branch_viewer.html").read_text()
    (OUT / "viewer.html").write_text(template.replace("__FRAME_TABLES__", "\n".join(tables)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--plots", action="store_true")
    args = parser.parse_args()
    if args.extract:
        extract()
    exact = json.loads((OUT / "production-exact.json").read_text())
    original = json.loads((OUT / "original-native-result.json").read_text())
    assert (
        exact["result"] == json.loads((LOCAL / "before" / (IDS[1] + ".json")).read_text())["result"]
    )
    result = exact["result"]
    track = make_track(result)
    frames = track.model_dump(mode="json")["frames"]
    indices = [i for i, f in enumerate(frames) if 4.1002 <= f["timestamp_seconds"] <= 4.3402]
    manifest = {r["id"]: r for r in json.loads((SAVED / "manifest-local.json").read_text())}
    low_result = json.loads((SAVED / "production/7787300e.json").read_text())["result"]
    low_track = make_track(low_result)
    low_frames = low_track.model_dump(mode="json")["frames"]
    low_indices = [
        i for i, f in enumerate(low_frames) if 2.4824 <= f["timestamp_seconds"] <= 2.5124
    ]
    rate, x = samples(TARGET)
    native_rate, native = samples(OUT / "original-native-mono.wav")
    _, recanonicalized = samples(OUT / "original-recanonicalized.wav")
    low_rate, low_x = samples(Path(manifest["7787300e"]["audio_path"]))
    after = masked_track(track, indices)
    check_preservation(track, after)
    data = dict(
        production_changed=False,
        outcome="D",
        parameter_neighborhood="not warranted: target prerequisites fail",
        provenance=dict(
            canonical_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),
            original_sha256=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
            extraction_exact=exact["baseline_exact"],
            version=exact["algorithm"],
            parameters=exact["parameters"],
        ),
        target=run_features(frames, indices),
        protected=run_features(low_frames, low_indices),
        graph=dict(
            before=metrics(track, result["f0"]),
            actual_after=metrics(track, result["f0"]),
            deletion_only=metrics(after, result["f0"]),
            protected=metrics(low_track, low_result["f0"]),
        ),
    )
    graph = sentence_pitch_evidence(result["f0"], display_from_track(track), [], track=track)
    mine_times = {p.timestamp_seconds for s in graph.mine.segments for p in s}
    for key, rr, fs, ix, sr, signal, ratio in (
        ("target", result, frames, indices, rate, x, 0.5),
        ("protected", low_result, low_frames, low_indices, low_rate, low_x, 2),
    ):
        item = data[key]
        item["table"] = frame_table(rr, fs, ix, ratio)
        if key == "target":
            for row in item["table"]:
                row["mine_source_retained"] = row["production_selected_hz"] is not None
                row["mine_simplified_vertex"] = row["timestamp_seconds"] in mine_times
        else:
            low_graph = sentence_pitch_evidence(
                rr["f0"], display_from_track(low_track), [], track=low_track
            )
            low_mine_times = {p.timestamp_seconds for s in low_graph.mine.segments for p in s}
            for row in item["table"]:
                row["mine_source_retained"] = row["production_selected_hz"] is not None
                row["mine_simplified_vertex"] = row["timestamp_seconds"] in low_mine_times
        item["acoustic"] = [
            dict(
                timestamp_seconds=fs[i]["timestamp_seconds"],
                selected_hz=fs[i]["raw_f0_hz"],
                spectral=spectral_evidence(
                    sr, signal, fs[i]["timestamp_seconds"], fs[i]["raw_f0_hz"]
                ),
                periodicity={
                    str(width): period_evidence(
                        sr, signal, fs[i]["timestamp_seconds"], fs[i]["raw_f0_hz"], width
                    )
                    for width in (0.04, 0.06, 0.08)
                },
            )
            for i in ix
        ]
        item["transition_frames"] = [
            f
            for f in fs
            if fs[ix[0]]["timestamp_seconds"] - 0.31
            <= f["timestamp_seconds"]
            <= fs[ix[-1]]["timestamp_seconds"] + 0.31
        ]
        item["energy_timbre"] = signal_transition(
            sr, signal, [f["timestamp_seconds"] for f in item["transition_frames"]]
        )
        item["loose_path_count_within_2st"] = sum(
            nearest_candidate(fs[i], ratio, 2) is not None for i in ix
        )
        for path in item["paths"]:
            path["screen_failures"] = screening_failures(item, path)
    # Original vs canonical: same Praat configuration, native 44.1 kHz mono
    # decoded original vs canonical 16 kHz. No gain or normalization experiment.
    comparison = []
    for i in indices:
        f = result["f0"][i]
        o = min(original["f0"], key=lambda g: abs(g["timestamp_seconds"] - f["timestamp_seconds"]))
        comparison.append(
            dict(
                timestamp_seconds=f["timestamp_seconds"],
                original_timestamp=o["timestamp_seconds"],
                canonical_hz=f["tracker_f0_hz"],
                original_hz=o["tracker_f0_hz"],
                difference_st=semitones(f["tracker_f0_hz"] / o["tracker_f0_hz"]),
                strength_difference=f["voicing_probability"] - o["voicing_probability"],
                canonical_candidates=f["pitch_candidates"],
                original_candidates=o["pitch_candidates"],
            )
        )
    times = np.arange(round(4.1002 * rate), round(4.3402 * rate)) / rate
    canonical_segment = np.interp(times, np.arange(len(x)) / rate, x)
    native_segment = np.interp(times, np.arange(len(native)) / native_rate, native)
    native_track = make_track(original)
    stereo_bytes = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-nostdin",
            "-i",
            str(ORIGINAL),
            "-f",
            "f64le",
            "-acodec",
            "pcm_f64le",
            "-",
        ],
        check=True,
        capture_output=True,
    ).stdout
    stereo = np.frombuffer(stereo_bytes, dtype="<f8").reshape(-1, 2)
    matched_candidates, unmatched_candidates = [], []
    for row in comparison:
        for c in row["canonical_candidates"]:
            near = min(
                row["original_candidates"], key=lambda g: abs(g["frequency_hz"] - c["frequency_hz"])
            )
            if abs(near["frequency_hz"] - c["frequency_hz"]) <= 1:
                matched_candidates.append(
                    dict(
                        hz_difference=abs(near["frequency_hz"] - c["frequency_hz"]),
                        strength_difference=abs(near["strength"] - c["strength"]),
                    )
                )
            else:
                unmatched_candidates.append(
                    dict(timestamp_seconds=row["timestamp_seconds"], canonical_candidate=c)
                )
    data["original_comparison"] = dict(
        stereo_channels_sample_identical=bool(np.array_equal(stereo[:, 0], stereo[:, 1])),
        matched_candidates=matched_candidates,
        unmatched_candidates=unmatched_candidates,
        pcm_identical_after_recanonicalization=bool(np.array_equal(x, recanonicalized)),
        original_native_rate=native_rate,
        canonical_rate=rate,
        waveform_correlation=float(np.corrcoef(canonical_segment, native_segment)[0, 1]),
        waveform_relative_rms_difference=float(
            np.sqrt(
                np.mean((canonical_segment - native_segment) ** 2) / np.mean(canonical_segment**2)
            )
        ),
        max_selected_difference_st=max(abs(r["difference_st"]) for r in comparison),
        max_strength_difference=max(abs(r["strength_difference"]) for r in comparison),
        canonical_selected_times=[
            frames[i]["timestamp_seconds"] for i in indices if frames[i]["selected_f0_hz"]
        ],
        native_selected_times=[
            f.timestamp_seconds
            for f in native_track.frames
            if 4.1002 <= f.timestamp_seconds <= 4.3402 and f.selected_f0_hz
        ],
        rows=comparison,
        spectra=[
            dict(
                timestamp_seconds=t,
                spectral=spectral_evidence(native_rate, native, t, frames[i]["raw_f0_hz"]),
            )
            for i in indices
            if (t := frames[i]["timestamp_seconds"])
            in (4.1002, 4.1702, 4.2102, 4.2602, 4.3102, 4.3402)
        ],
    )
    protected = {
        r["recording"]: set(r["times"])
        for r in json.loads((SAVED / "low-f0-proxy-samples.json").read_text())
    }
    controls = []
    high_runs = []
    for file in sorted((SAVED / "production").glob("*.json")):
        saved = json.loads(file.read_text())
        rr = saved["result"]
        tt = make_track(rr)
        assert [f.timestamp_seconds for f in tt.frames if f.selected_f0_hz] == saved[
            "retained_times"
        ]
        control = replay_one(rr, protected.get(file.stem, set()))
        control.update(id=file.stem, kind=manifest[file.stem]["kind"])
        controls.append(control)
        fs = tt.model_dump(mode="json")["frames"]
        if file.stem in {"google_old", "f5dc0cc1"}:
            raw_runs = branches([dict(f, selected_f0_hz=f["raw_f0_hz"]) for f in fs])
            control["raw_run_features"] = [run_features(fs, run) for run in raw_runs]
            for feature in control["raw_run_features"]:
                for path in feature["paths"]:
                    path["screen_failures"] = screening_failures(feature, path)
        for feat in control["features"]:
            hs = [fs[i]["selected_f0_hz"] for i in feat["indices"]]
            if len(hs) >= 15 and (min(hs) > 220 or max(hs) / min(hs) > 1.7):
                high_runs.append(
                    dict(
                        id=file.stem,
                        kind=manifest[file.stem]["kind"],
                        min_hz=min(hs),
                        max_hz=max(hs),
                        **feat,
                    )
                )
    data["controls"] = controls
    data["protected_summary"] = dict(
        samples=sum(len(s) for s in protected.values()),
        screened=sum(len(c["protected_screened"]) for c in controls),
    )
    low_samples = json.loads(
        (
            ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json"
        ).read_text()
    )
    by_id = {c["id"]: c for c in controls}
    data["protected_under70"] = dict(
        samples=len(low_samples),
        screened=sum(
            r["timestamp"] in by_id[r["recording"]]["screened_times"] for r in low_samples
        ),
        note=("Saved list contains 11 entries, all in the 617 proxy set; prior prose said ten."),
        rows=low_samples,
    )
    data["high_movement_search"] = high_runs
    data["six_physical"] = []
    for id_ in IDS:
        rr = json.loads((LOCAL / "before" / (id_ + ".json")).read_text())["result"]
        current = make_track(rr)
        actual = metrics(current, rr["f0"])
        data["six_physical"].append(
            dict(id=id_, before=actual, actual_after=actual, diagnostic=replay_one(rr, set()))
        )
    data["eligibility"] = []
    for a, b in ((3.8, 4.6), (4.1, 4.35)):
        states = []
        for tt in (track, after):
            projection = project_pitch(tt, a, b, timing_source="acoustic_forensic_window")
            states.append(interpretation_eligibility(tt, projection).model_dump(mode="json"))
        data["eligibility"].append(
            dict(
                start=a,
                end=b,
                production=states[0],
                deletion_only=states[1],
                note="Acoustic windows only; no character timing invented",
            )
        )
    dump(OUT / "full-evidence.json", data)
    # Checkpoint summary excludes waveform samples and bulky lag arrays. Every
    # frame/candidate and all screening failures remain inspectable in JSON/CSV.
    compact = json.loads(json.dumps(data))
    for key in ("target", "protected"):
        for item in compact[key]["acoustic"]:
            for period in item["periodicity"].values():
                period.pop("lag_ms")
                period.pop("correlation")
    dump(REPORT / "sustained-high-evidence.json", compact)
    rows = [dict(case=key, **row) for key in ("target", "protected") for row in data[key]["table"]]
    with (REPORT / "sustained-high-frames.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                for k, v in row.items()
            }
            for row in rows
        )
    if args.plots:
        make_plots(data, track, low_track, x, low_x, low_rate)
    make_viewer(data)
    print(
        json.dumps(
            dict(
                exact=exact["baseline_exact"],
                target_raw=len(indices),
                target_selected=data["target"]["selected_frames"],
                protected=data["protected_summary"],
                historical_screened=sum(len(c["screened_indices"]) for c in controls),
                graph=data["graph"]["before"]["mine_domain"],
                deletion_only=data["graph"]["deletion_only"]["mine_domain"],
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
