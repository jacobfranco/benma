"""Bounded, local-only presence audit. No providers, new audio, or new trackers.

Run with PYTHONPATH=.:services/api/src services/api/.venv/bin/python
benchmark/pronunciation_v2/speech_presence_audit.py. Private PCM remains ignored.
The frozen manifest is mandatory; hashes are checked before any measurement.
Candidate policies are research only and never imported by production.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import statistics
import time
import wave
from dataclasses import asdict
from pathlib import Path

import numpy as np
import parselmouth
from benma_api.audio.presence import VERSION, corroborate_transcript, speech_presence
from benma_api.errors import NoSpeechError

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/research/pronunciation-v2/2026-10-06-speech-presence"
POLICIES = ("envelope", "band_envelope", "spectral_temporal", "combined", "short_spectral")


def read_audio(entry):
    if "parent_id" in entry:
        entries = json.loads((OUTPUT / "corpus.json").read_text())["entries"]
        parent = next(e for e in entries if e["id"] == entry["parent_id"])
        source, rate, _ = read_audio(parent)
        assert hashlib.sha256(source).hexdigest() == entry["parent_sha256"]
        start, end = entry["interval_seconds"]
        with wave.open(io.BytesIO(source)) as stream:
            stream.setpos(round(start * rate))
            frames = stream.readframes(round((end - start) * rate))
        output = io.BytesIO()
        with wave.open(output, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(frames)
        data = output.getvalue()
    else:
        data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["id"]
    with wave.open(io.BytesIO(data)) as stream:
        assert stream.getnchannels() == 1 and stream.getsampwidth() == 2
        rate = stream.getframerate()
        samples = np.frombuffer(stream.readframes(stream.getnframes()), "<i2") / 32768.0
    return data, rate, samples


def longest_run(mask):
    longest = current = 0
    for value in mask:
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest * 0.01


def features(samples, rate):
    """Four families: envelope, band distribution, spectral change, entropy.

    25-ms centered Hann frames, 10-ms hop, 1024-bin FFT. Relative band
    envelopes do not depend on gain, transcript, target, or a pitch floor.
    Spectral change is total variation of seven band proportions over 50 ms.
    """
    width = round(rate * 0.025)
    frames = np.lib.stride_tricks.sliding_window_view(samples, width)[:: round(rate * 0.01)]
    frames = frames - frames.mean(axis=1, keepdims=True)
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    power = abs(np.fft.rfft(frames * np.hanning(width), n=1024)) ** 2
    hz = np.fft.rfftfreq(1024, 1 / rate)
    total = power.sum(axis=1) + 1e-30
    band = power[:, (hz >= 300) & (hz < 4000)].sum(axis=1)
    bands = np.stack(
        [
            power[:, (hz >= a) & (hz < b)].sum(axis=1)
            for a, b in (
                (0, 150),
                (150, 300),
                (300, 600),
                (600, 1200),
                (1200, 2400),
                (2400, 4000),
                (4000, 8001),
            )
        ],
        axis=1,
    )
    proportions = bands / (bands.sum(axis=1, keepdims=True) + 1e-30)
    flux = np.sum(abs(proportions[5:] - proportions[:-5]), axis=1) / 2
    probability = power / total[:, None]
    entropy = -(probability * np.log(probability + 1e-30)).sum(axis=1) / np.log(power.shape[1])
    background = float(np.quantile(rms, 0.2))
    active = rms > max(3 * background, 3 / 32768)
    return {
        "rms_quantiles_0_10_20_50_80_90_95_100": np.quantile(
            rms, [0, 0.1, 0.2, 0.5, 0.8, 0.9, 0.95, 1]
        ).tolist(),
        "active_energy_seconds": float(sum(active) * 0.01),
        "active_run_seconds": longest_run(active),
        "band_active_run_seconds": longest_run(band > 9 * np.quantile(band, 0.2)),
        "band_modulation": float(
            np.sqrt(np.quantile(band, 0.9) / max(1e-30, np.quantile(band, 0.2)))
        ),
        "band_ratio": float(band.sum() / total.sum()),
        "low_below_150_ratio": float(power[:, hz < 150].sum() / total.sum()),
        "flux_q90": float(np.quantile(flux, 0.9)) if len(flux) else 0.0,
        "entropy_median": float(np.median(entropy)),
        "band_energy_proportions": (bands.sum(axis=0) / total.sum()).tolist(),
    }


def candidate(policy, f, factor=1.0):
    envelope = f["active_run_seconds"] + 1e-9 >= 0.05 * factor
    band = (
        f["band_ratio"] >= 0.1 * factor
        and f["band_active_run_seconds"] + 1e-9 >= 0.05 * factor
        and f["band_modulation"] >= 3 * factor
    )
    spectral = f["flux_q90"] >= 0.35 * factor and f["entropy_median"] >= 0.2 * factor
    return {
        "envelope": envelope,
        "band_envelope": band,
        "spectral_temporal": spectral and envelope,
        "combined": band and spectral,
        "short_spectral": f["flux_q90"] >= 0.2 * factor and f["entropy_median"] >= 0.2 * factor,
    }[policy]


def old_decision(data, transcript):
    presence = speech_presence(data)
    try:
        corroborate_transcript(presence, transcript)
        accepted = True
    except NoSpeechError:
        accepted = False
    units = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", transcript))
    with wave.open(io.BytesIO(data)) as stream:
        rate = stream.getframerate()
        samples = np.frombuffer(stream.readframes(stream.getnframes()), "<i2") / 32768.0
    frames = np.lib.stride_tricks.sliding_window_view(samples, round(rate * 0.02))[
        :: round(rate * 0.01)
    ]
    energies = np.sqrt(np.mean((frames - frames.mean(axis=1, keepdims=True)) ** 2, axis=1))
    active = energies > max(3 * presence.background_rms, 3 / 32768)
    return {
        **asdict(presence),
        "accepted": accepted,
        "frame_energy_quantiles_0_10_20_50_80_90_95_100": np.quantile(
            energies, [0, 0.1, 0.2, 0.5, 0.8, 0.9, 0.95, 1]
        ).tolist(),
        "frame_count": len(energies),
        "active_frame_count": int(sum(active)),
        "active_total_seconds": float(sum(active) * 0.01),
        "checks": {
            "background_below_0_01": presence.background_rms < 0.01,
            "activity_below_0_05": presence.activity_seconds < 0.05,
            "no_periodic_run": presence.periodic_seconds == 0,
            "han_units": units,
            "at_least_three_han": units >= 3,
            "corroborated_total_below_bound": presence.corroborated_seconds + 1e-9
            < min(units, 10) * 0.02,
            "corroborated_run_below_0_05": presence.corroborated_run_seconds < 0.05,
        },
    }


def summarize(rows, policy, factor):
    result = {"policy": policy, "threshold_factor": factor}
    for label in ("positive", "negative", "unresolved"):
        subset = [r for r in rows if r["label"] == label]
        result[label] = {
            "total": len(subset),
            "accepted": [r["id"] for r in subset if candidate(policy, r["features"], factor)],
            "rejected": [r["id"] for r in subset if not candidate(policy, r["features"], factor)],
        }
    result["categories"] = {
        tag: {
            "total": sum(tag in r["tags"] for r in rows if r["label"] == "positive"),
            "accepted": sum(
                tag in r["tags"] and candidate(policy, r["features"], factor)
                for r in rows
                if r["label"] == "positive"
            ),
        }
        for tag in sorted({tag for r in rows if r["label"] == "positive" for tag in r["tags"]})
    }
    return result


def saved_asr(entries):
    inventory = ROOT / "services/api/var/capture-robustness/inventory-all.json"
    records = json.loads(inventory.read_text())["recordings"]
    lookup = {r["perception"]["id"]: r for r in records}
    audit = []
    for entry in entries:
        saved = lookup.get(entry.get("perception_id"))
        if not saved:
            audit.append(
                {
                    "id": entry["id"],
                    "available": False,
                    "reason": "No saved ASR for this waveform; no request made.",
                }
            )
            continue
        p = saved["perception"]
        raw = p.get("raw_payload_json") or {}
        transcript = raw.get("text", p.get("transcript")) or ""
        tokens = raw.get("logprobs", [])
        audit.append(
            {
                "id": entry["id"],
                "available": True,
                "perception_id": p["id"],
                "provider": p["provider"],
                "product": p["product"],
                "status": p["status"],
                "error_code": p["error_code"],
                "product_transcript": p["transcript"],
                "raw_transcript": transcript,
                "characters": len(transcript),
                "tokens": [{"token": t["token"], "logprob": t["logprob"]} for t in tokens],
                "mean_logprob": statistics.mean(t["logprob"] for t in tokens) if tokens else None,
                "asr_word_timing": None,
                "asr_segment_timing": None,
                "no_speech_probability": raw.get("no_speech_prob"),
                "raw_payload_sha256": p.get("raw_payload_sha256"),
            }
        )
    return audit


def main():
    manifest = json.loads((OUTPUT / "corpus.json").read_text())
    entries = manifest["entries"]
    asr = saved_asr(entries)
    asr_lookup = {r["id"]: r for r in asr}
    rows, timings = [], []
    for entry in entries:
        data, rate, samples = read_audio(entry)
        transcript = asr_lookup[entry["id"]].get("raw_transcript", entry["transcript"])
        old = old_decision(data, transcript)
        f = features(samples, rate)
        # Reuse the existing guard's exact pitch configuration, for diagnostics only.
        pitch = (
            parselmouth.Sound(samples, sampling_frequency=rate)
            .to_pitch_ac(time_step=0.01, pitch_floor=40, pitch_ceiling=550, voicing_threshold=0.45)
            .selected_array["frequency"]
        )
        voiced = pitch[pitch > 0]
        row = {
            "id": entry["id"],
            "label": entry["label"],
            "tags": entry["tags"],
            "sha256": entry["sha256"],
            "duration_seconds": len(samples) / rate,
            "rms": float(np.sqrt(np.mean(samples * samples))),
            "peak": float(max(abs(samples))),
            "old": old,
            "features": f,
            "periodic_frames": len(voiced),
            "pitch_quantiles_0_10_50_90_100": np.quantile(voiced, [0, 0.1, 0.5, 0.9, 1]).tolist()
            if len(voiced)
            else [],
            "current_accepted": old["accepted"],
        }
        rows.append(row)
        # Warm, paired local DSP timing. No network or F0 benchmark included.
        for _ in range(7):
            t = time.perf_counter()
            speech_presence(data)
            old_ms = (time.perf_counter() - t) * 1000
            t = time.perf_counter()
            features(samples, rate)
            features_ms = (time.perf_counter() - t) * 1000
            timings.append({"id": entry["id"], "old_ms": old_ms, "features_ms": features_ms})
    evaluation = [summarize(rows, p, factor) for p in POLICIES for factor in (0.8, 1.0, 1.2)]
    latency = {
        "measurements": timings,
        "summary": {
            key: {
                "median": statistics.median(r[key] for r in timings),
                "p95": float(np.quantile([r[key] for r in timings], 0.95)),
                "max": max(r[key] for r in timings),
            }
            for key in ("old_ms", "features_ms")
        },
        "production_added_ms": 0,
    }
    for name, payload in [
        ("measurements.json", rows),
        ("candidates.json", evaluation),
        ("asr-audit.json", asr),
        ("latency.json", latency),
    ]:
        (OUTPUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    (OUTPUT / "audit-version.json").write_text(
        json.dumps(
            {
                "presence_version": VERSION,
                "presence_source_sha256": hashlib.sha256(
                    (ROOT / "services/api/src/benma_api/audio/presence.py").read_bytes()
                ).hexdigest(),
                "manifest_sha256": hashlib.sha256(
                    (OUTPUT / "corpus.json").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(next(r for r in rows if r["id"] == "silence_accidental"), indent=2))
    for r in evaluation:
        print(
            r["policy"],
            r["threshold_factor"],
            "positive",
            len(r["positive"]["accepted"]),
            "/",
            r["positive"]["total"],
            "negative rejects",
            len(r["negative"]["rejected"]),
            "/",
            r["negative"]["total"],
            "misses",
            r["negative"]["accepted"],
        )
    print("Latency", latency["summary"])


if __name__ == "__main__":
    main()
