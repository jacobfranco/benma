"""Target-free, offline acoustic measurements. No provider, reading or pitch extractor imports."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np

VERSION = "independent-phonetic-evidence-v1"
RATE = 16000
FRAME = 400
HOP = 160
FORMANT_PARAMETERS = {
    "time_step": 0.01,
    "max_number_of_formants": 5,
    "maximum_formant": 5500,
    "window_length": 0.025,
    "pre_emphasis_from": 50,
}


@dataclass(frozen=True, slots=True)
class Span:
    start_ms: float
    end_ms: float


@dataclass(frozen=True, slots=True)
class SavedFrame:
    timestamp_seconds: float
    f0_hz: float | None
    selected_f0_hz: float | None
    quality_usable: bool
    voicing_probability: float | None
    energy_rms: float | None

    def __post_init__(self):
        values = asdict(self)
        if any(v is not None and not math.isfinite(v) for v in values.values()):
            raise ValueError("Nonfinite saved acoustic frame")
        if any(v is not None and v <= 0 for v in (self.f0_hz, self.selected_f0_hz)):
            raise ValueError("Pitch must be positive or absent")


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode(path):
    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            str(RATE),
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-",
        ],
        timeout=30,
    )
    return np.frombuffer(raw, dtype="<f4").copy()


def stats(values):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if not len(a):
        return None
    return {
        "count": len(a),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "min": float(a.min()),
        "max": float(a.max()),
        "iqr": float(np.percentile(a, 75) - np.percentile(a, 25)),
    }


def spectral_frames(crop):
    rows = []
    frequencies = np.fft.rfftfreq(512, 1 / RATE)
    for offset in range(0, len(crop) - FRAME + 1, HOP):
        frame = crop[offset : offset + FRAME].astype(float)
        centered = frame - frame.mean()
        power = abs(np.fft.rfft(centered * np.hanning(FRAME), n=512)) ** 2
        total = power.sum()
        centroid = float(np.dot(power, frequencies) / total) if total > 0 else None
        rows.append(
            {
                "time_ms": (offset + FRAME / 2) / RATE * 1000,
                "rms": float(np.sqrt(np.mean(frame**2))),
                "zcr": float(np.mean(np.signbit(centered[1:]) != np.signbit(centered[:-1]))),
                "centroid_hz": centroid,
                "bandwidth_hz": float(np.sqrt(np.dot(power, (frequencies - centroid) ** 2) / total))
                if total > 0
                else None,
                "rolloff85_hz": float(frequencies[np.searchsorted(np.cumsum(power), 0.85 * total)])
                if total > 0
                else None,
                "high_frequency_fraction": float(power[frequencies >= 4000].sum() / total)
                if total > 0
                else None,
            }
        )
    return rows


def spectral_summary(rows):
    return {
        k: stats([r[k] for r in rows if r[k] is not None])
        for k in (
            "rms",
            "zcr",
            "centroid_hz",
            "bandwidth_hz",
            "rolloff85_hz",
            "high_frequency_fraction",
        )
    }


def runs(frames):
    result = []
    current = []
    for p in frames:
        if p.selected_f0_hz is None or not p.quality_usable:
            if current:
                result.append(current)
            current = []
        else:
            if current and p.timestamp_seconds - current[-1].timestamp_seconds > 0.015:
                result.append(current)
                current = []
            current.append(p)
    if current:
        result.append(current)
    return result


def pitch_evidence(frames, span):
    if any(b.timestamp_seconds <= a.timestamp_seconds for a, b in pairwise(frames)):
        raise ValueError("Saved frames must be strictly time ordered")
    frames = tuple(p for p in frames if span.start_ms <= p.timestamp_seconds * 1000 < span.end_ms)
    usable = [p for p in frames if p.selected_f0_hz is not None and p.quality_usable]
    longest = max(runs(frames), key=len, default=[])
    midpoint = (span.start_ms + span.end_ms) / 2
    mid = min(usable, key=lambda p: abs(p.timestamp_seconds * 1000 - midpoint), default=None)
    if mid is not None and abs(mid.timestamp_seconds * 1000 - midpoint) > 10:
        mid = None

    def point(p):
        return {"time_ms": p.timestamp_seconds * 1000 - span.start_ms, "hz": p.selected_f0_hz}

    slope = None
    if len(longest) >= 5:
        slope = float(
            np.polyfit(
                [p.timestamp_seconds - longest[0].timestamp_seconds for p in longest],
                [p.selected_f0_hz for p in longest],
                1,
            )[0]
        )
    n = len(frames)
    raw_count = sum(p.f0_hz is not None for p in frames)
    return {
        "source": "saved_whole_recording_slice_no_retracking",
        "frame_count": n,
        "raw_voiced_frame_count": raw_count,
        "usable_frame_count": len(usable),
        "raw_voiced_fraction": raw_count / n if n else None,
        "raw_missing_fraction": 1 - raw_count / n if n else None,
        "selected_missing_fraction": 1 - len(usable) / n if n else None,
        "tracker_instability_frames": sum(not p.quality_usable for p in frames),
        "saved_candidate_strength": stats(
            [p.voicing_probability for p in frames if p.voicing_probability is not None]
        ),
        "selected_hz": stats([p.selected_f0_hz for p in usable]),
        "first_usable": point(usable[0]) if usable else None,
        "midpoint_usable": point(mid) if mid else None,
        "last_usable": point(usable[-1]) if usable else None,
        "longest_run_frames": len(longest),
        "longest_run_support_ms": (longest[-1].timestamp_seconds - longest[0].timestamp_seconds)
        * 1000
        + 10
        if longest
        else 0,
        "longest_run_slope_hz_per_second": slope,
        "frames": [
            dict(asdict(p), timestamp_seconds=p.timestamp_seconds - span.start_ms / 1000)
            for p in frames
        ],
    }, longest


def analysis_windows(longest, span):
    if len(longest) < 5:
        return []
    duration = span.end_ms - span.start_ms
    start = max(0, longest[0].timestamp_seconds * 1000 - span.start_ms - 5)
    end = min(duration, longest[-1].timestamp_seconds * 1000 - span.start_ms + 5)
    candidate = {
        "kind": "voiced_nucleus_candidate",
        "start_ms": start,
        "end_ms": end,
        "semantics": "analysis_window_not_phoneme_boundary",
    }
    windows = [candidate]
    if start >= 25:
        windows.append(dict(candidate, kind="prefix", start_ms=0, end_ms=start))
    if duration - end >= 25:
        windows.append(dict(candidate, kind="tail", start_ms=end, end_ms=duration))
    return windows


def _burg_rows(crop, centers):
    import parselmouth
    from parselmouth.praat import call

    formants = parselmouth.Sound(crop.astype(float), RATE).to_formant_burg(**FORMANT_PARAMETERS)
    rows = []
    for t in centers:
        f = [float(formants.get_value_at_time(k, t)) for k in (1, 2, 3)]
        b = [
            float(call(formants, "Get bandwidth at time", k, t, "Hertz", "Linear"))
            for k in (1, 2, 3)
        ]
        rows.append(
            {
                "time_ms": t * 1000,
                "hz": [v if math.isfinite(v) else None for v in f],
                "bandwidth_hz": [v if math.isfinite(v) else None for v in b],
            }
        )
    return rows


def formant_evidence(crop, windows):
    candidate = next((w for w in windows if w["kind"] == "voiced_nucleus_candidate"), None)
    result = {
        "candidate_exists": candidate is not None,
        "parameters": FORMANT_PARAMETERS,
        "status": "no_candidate",
        "attempted_frames": 0,
        "usable_frames": 0,
        "usable_center_span_ms": 0,
        "availability_f1_f2_f3": [0, 0, 0],
        "sanity_rejected_frames": 0,
        "adjacent_jump_count": 0,
        "reason_flags": [],
        "summary_hz": None,
        "frames": [],
    }
    if candidate is None:
        return result
    centers = np.arange(25, len(crop) / RATE * 1000 - 25 + 1e-6, 10)
    centers = (
        centers[
            (centers >= candidate["start_ms"] + 25 - 1e-6)
            & (centers <= candidate["end_ms"] - 25 + 1e-6)
        ]
        / 1000
    )
    result["attempted_frames"] = len(centers)
    if not len(centers):
        result["status"] = "insufficient_support"
        return result
    try:
        rows = _burg_rows(crop, centers)
    except (RuntimeError, ValueError, ImportError):
        result["status"] = "extraction_failed"
        return result
    bounds = ((150, 1200), (500, 3500), (1200, 4500))
    for row in rows:
        f, b = row["hz"], row["bandwidth_hz"]
        row["sanity_pass"] = (
            all(v is not None and lo <= v <= hi for v, (lo, hi) in zip(f, bounds, strict=True))
            and all(
                v is not None and 0 < v <= hi for v, hi in zip(b, (500, 700, 1000), strict=True)
            )
            and f[1] - f[0] >= 100
            and f[2] - f[1] >= 100
        )
    valid = [r for r in rows if r["sanity_pass"]]
    jumps = sum(
        a["sanity_pass"]
        and b["sanity_pass"]
        and b["time_ms"] - a["time_ms"] <= 10.001
        and any(abs(y - x) / x > 0.25 for x, y in zip(a["hz"], b["hz"], strict=True))
        for a, b in pairwise(rows)
    )
    feasible = len(valid) >= 3 and len(valid) / len(rows) >= 0.7 and jumps == 0
    reasons = []
    if len(valid) < 3:
        reasons.append("insufficient_passing_frames")
    if len(valid) / len(rows) < 0.7:
        reasons.append("insufficient_sanity_pass_fraction")
    if jumps:
        reasons.append("adjacent_formant_instability")
    result.update(
        status="feasible_numeric_track" if feasible else "quality_abstention",
        usable_frames=len(valid),
        usable_center_span_ms=valid[-1]["time_ms"] - valid[0]["time_ms"] if valid else 0,
        availability_f1_f2_f3=[sum(r["hz"][i] is not None for r in rows) for i in range(3)],
        sanity_rejected_frames=len(rows) - len(valid),
        adjacent_jump_count=jumps,
        reason_flags=reasons,
        summary_hz=[stats([r["hz"][i] for r in valid]) for i in range(3)] if feasible else None,
        frames=rows,
    )
    return result


def extract_observed(audio: np.ndarray, span: Span, saved_frames: tuple[SavedFrame, ...] = ()):
    """Only waveform, timing and typed saved acoustics. No Unit or metadata dictionary."""
    if type(span) is not Span or any(type(p) is not SavedFrame for p in saved_frames):
        raise TypeError("Only target-free Span and SavedFrame inputs are accepted")
    result = {
        "version": VERSION,
        "status": "abstained",
        "quality_flags": [],
        "duration_ms": None,
        "pitch": None,
        "spectrum": None,
        "formants": None,
        "analysis_windows": [],
    }
    if (
        not all(math.isfinite(v) for v in (span.start_ms, span.end_ms))
        or span.start_ms < 0
        or span.end_ms <= span.start_ms
    ):
        result["quality_flags"] = ["invalid_span"]
        return result
    if audio.ndim != 1 or not np.isfinite(audio).all():
        result["quality_flags"] = ["invalid_audio"]
        return result
    if span.end_ms > len(audio) / RATE * 1000:
        result["quality_flags"] = ["span_outside_audio"]
        return result
    start, end = (round(v / 1000 * RATE) for v in (span.start_ms, span.end_ms))
    crop = audio[start:end].astype(float)
    duration = span.end_ms - span.start_ms
    result["duration_ms"] = duration
    if len(crop) < FRAME:
        result["quality_flags"] = ["timing_valid", "insufficient_duration"]
        return result
    pitch, longest = pitch_evidence(saved_frames, span)
    windows = analysis_windows(longest, span)
    spectrum = spectral_frames(crop)
    formants = formant_evidence(crop, windows)
    prefix = next((w for w in windows if w["kind"] == "prefix"), None)
    onset = {
        "status": "unresolved",
        "frames": 0,
        "spectrum": None,
        "confirmed_aperiodic_duration_ms": None,
    }
    if prefix:
        rows = [
            r
            for r in spectrum
            if r["time_ms"] - 12.5 >= prefix["start_ms"] and r["time_ms"] + 12.5 <= prefix["end_ms"]
        ]
        available = len(rows) >= 3 and spectral_summary(rows)["centroid_hz"] is not None
        onset.update(
            status="generic_prefix_available" if available else "insufficient_support",
            frames=len(rows),
            spectrum=spectral_summary(rows) if available else None,
            duration_ms=prefix["end_ms"],
            saved_raw_voiced_frames=sum(
                p["f0_hz"] is not None
                for p in pitch["frames"]
                if p["timestamp_seconds"] * 1000 < prefix["end_ms"]
            ),
        )
    flags = ["timing_valid", "enough_audio_duration", "boundary_not_independently_validated"]
    flags.append(
        "spectral_measurement_available"
        if any(r["centroid_hz"] is not None for r in spectrum)
        else "spectrum_missing"
    )
    if pitch["usable_frame_count"] == 0:
        flags.append("F0_missing")
    elif pitch["usable_frame_count"] < 5:
        flags.append("insufficient_saved_pitch")
    else:
        flags.append("saved_pitch_available")
    if pitch["raw_missing_fraction"] is not None and pitch["raw_missing_fraction"] > 0.5:
        flags.append("heavy_raw_F0_missingness")
    if pitch["tracker_instability_frames"]:
        flags.append("tracker_instability")
    flags.append("nucleus_candidate_available" if windows else "insufficient_saved_voicing")
    flags.append(
        "formant_measurement_available" if formants["summary_hz"] else "formants_unavailable"
    )
    if formants["status"] == "quality_abstention":
        flags.append("formant_summary_abstained")
    flags.append(
        "prefix_spectrum_available"
        if onset["status"] == "generic_prefix_available"
        else "onset_window_unresolved"
    )
    clipping = float(np.mean(abs(crop) >= 0.98))
    if clipping > 0.02:
        flags.append("clipping")
    result.update(
        status="measured",
        quality_flags=flags,
        pitch=pitch,
        analysis_windows=windows,
        formants=formants,
        onset=onset,
        energy={
            "rms": float(np.sqrt(np.mean(crop**2))),
            "peak": float(np.max(abs(crop))),
            "near_full_scale_fraction": clipping,
        },
        spectrum=spectral_summary(spectrum),
        spectral_frames=spectrum,
        sample_count=len(crop),
        sample_rate_hz=RATE,
    )
    return result


def load_manifest(path):
    manifest = json.loads(Path(path).read_text())
    if set(manifest) != {"version", "regions"} or manifest["version"] != 1:
        raise ValueError("Unknown manifest fields/version")
    seen = set()
    for r in manifest["regions"]:
        if set(r) != {"id", "audio_path", "audio_sha256", "span", "saved_frames"}:
            raise ValueError("Manifest only accepts acoustic input fields")
        if not r["id"].startswith("R") or not r["id"][1:].isdigit() or r["id"] in seen:
            raise ValueError("Invalid or duplicate blind ID")
        seen.add(r["id"])
        Span(**r["span"])
        tuple(SavedFrame(**p) for p in r["saved_frames"])
    return manifest


def verify_seal(packet):
    packet = Path(packet)
    seal = json.loads((packet / "seal.json").read_text())
    for relative, digest in seal.items():
        if sha(packet / relative) != digest:
            raise ValueError("Blind packet changed after seal")
    return hashlib.sha256((packet / "seal.json").read_bytes()).hexdigest()
