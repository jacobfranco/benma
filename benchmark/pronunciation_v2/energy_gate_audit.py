"""Read-only waveform/energy diagnostics using already saved tracker estimates.

No F0 extraction, alternate tracker, gate relaxation, or acoustic mutation.
"""

from __future__ import annotations

import hashlib
import json
import math
import wave
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from benchmark.pronunciation_v2.gesture_readability_audit import OUT, ROOT


def path_metrics(frames: list[dict[str, Any]], key: str) -> dict[str, Any]:
    voiced = [f for f in frames if f.get(key)]
    jumps = [
        abs(12 * math.log2(b[key] / a[key]))
        for a, b in pairwise(voiced)
        if b["timestamp_seconds"] - a["timestamp_seconds"] <= 0.12
    ]
    gaps = [b["timestamp_seconds"] - a["timestamp_seconds"] - 0.01 for a, b in pairwise(voiced)]
    return {
        "count": len(voiced),
        "support_seconds": len(voiced) * 0.01,
        "maximum_jump_st": max(jumps, default=0),
        "jumps_over_6_st": sum(j > 6 for j in jumps),
        "largest_gap_seconds": max(0, max(gaps, default=0)),
        "hz_range": [min(f[key] for f in voiced), max(f[key] for f in voiced)] if voiced else None,
    }


def summarize_unit(
    name: str, result: dict[str, Any], retained: set[float], start: float, end: float
) -> dict[str, Any]:
    frames = [f for f in result["f0"] if start <= f["timestamp_seconds"] < end]
    # selected here means the saved display's retained measurements, not the
    # analyzer's earlier selected_f0_hz diagnostic field.
    selected = [f for f in frames if f["timestamp_seconds"] in retained]
    gated = [f for f in frames if f.get("energy_gated")]
    return {
        "id": name,
        "start": start,
        "end": end,
        "threshold_rms": result["energy_gate"]["threshold_rms"],
        "noise_floor_rms": result["energy_gate"]["noise_floor_rms"],
        "raw": path_metrics(frames, "tracker_f0_hz"),
        "selected": path_metrics(selected, "f0_hz"),
        "energy_rejected": len(gated),
        "energy_rejected_path": path_metrics(gated, "tracker_f0_hz"),
        "above_gate_but_tracker_unvoiced": sum(
            not f.get("tracker_f0_hz") and f["energy_rms"] >= result["energy_gate"]["threshold_rms"]
            for f in frames
        ),
        "audible_voiced_duration": None,
    }


def waveform(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path)) as reader:
        assert reader.getnchannels() == 1 and reader.getsampwidth() == 2
        rate = reader.getframerate()
        values = (
            np.frombuffer(reader.readframes(reader.getnframes()), dtype="<i2").astype(float) / 32768
        )
    return rate, values


def run() -> None:
    controls = []
    fixtures = []
    saved = ROOT / "services/api/var/gesture-readability/saved"
    projection = json.loads((OUT / "projection-replay.json").read_text())
    by_analysis = {r["analysis_id"]: r for r in projection}
    geometry = {
        r["id"]: r["manual_geometry"]
        for r in json.loads((OUT / "calibration-corpus.json").read_text())
    }
    physical = None
    for path in sorted(saved.glob("*.json")):
        p = json.loads(path.read_text())
        if path.stem not in by_analysis:
            continue
        rec = Path(p["audio"]["storage_key"]).stem[:8]
        r = p["acoustic"]["normalized_result"]
        retained = {
            f["timestamp_seconds"]
            for f in r["utterance_pitch_track"]["frames"]
            if f["selected_f0_hz"]
        }
        for u in by_analysis[path.stem]["units"]:
            item = summarize_unit(f"{rec}:{u['text']}", r, retained, u["start"], u["end"])
            item.update(
                kind="accepted_unit",
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                graph_assessment=(
                    "useful retained geometry; acoustic truth not independently certified"
                    if geometry[item["id"]] != "UNCLEAR"
                    else "ambiguous or absent selected geometry; gate correctness unadjudicated"
                ),
            )
            controls.append(item)
            if item["id"] in {"89cee47e:个", "89cee47e:我", "4b9dbd2b:个", "8faf1a90:个"}:
                fixtures.append(
                    {
                        "id": item["id"],
                        "threshold": item["threshold_rms"],
                        "duration": r["duration_seconds"],
                        "f0": [
                            f for f in r["f0"] if u["start"] <= f["timestamp_seconds"] < u["end"]
                        ],
                    }
                )
        if rec == "89cee47e":
            physical = p
    # Older saved neutral 们/吧 control: original accepted timing and original
    # saved display selection. No invented modern immutable-track provenance.
    legacy_path = saved / "a5536c4e-6679-4f61-b00b-de59d86b8ec7.json"
    legacy = json.loads(legacy_path.read_text())
    legacy_data = legacy["analysis"]["result"]
    legacy_result = legacy["acoustic"]["normalized_result"]
    legacy_retained = {
        f["timestamp_seconds"] for f in legacy_data["tone_graph"]["raw"] if f["retained"]
    }
    for unit in legacy_data["syllables"]:
        item = summarize_unit(
            f"fe8c8279:{unit['characters']}",
            legacy_result,
            legacy_retained,
            unit["start_seconds"],
            unit["end_seconds"],
        )
        item.update(
            kind="accepted_unit",
            source_sha256=hashlib.sha256(legacy_path.read_bytes()).hexdigest(),
            provenance="legacy saved analysis, no modern track/source-index audit claim",
            graph_assessment=(
                "retained measurements available; no independently labelled whole-unit gesture"
            ),
        )
        controls.append(item)
    manifest = {
        r["id"]: r
        for r in json.loads(
            (ROOT / "services/api/var/f0-foundation/manifest-local.json").read_text()
        )
    }
    for name in (
        "human_control",
        "google_old",
        "silence_accidental",
        "silence_original",
        "silence_periodic",
        "neg_digital_silence",
        "neg_stationary_noise",
        "neg_clicks",
        "syn_steady_70",
        "syn_steady_110",
        "native_gain",
    ):
        path = ROOT / f"services/api/var/f0-foundation/production/{name}.json"
        p = json.loads(path.read_text())
        r = p["result"]
        info = manifest[name]
        audio_path = Path(info["audio_path"])
        assert hashlib.sha256(audio_path.read_bytes()).hexdigest() == info["sha256"]
        item = summarize_unit(name, r, set(p["retained_times"]), 0, r["duration_seconds"])
        item.update(
            kind=info["kind"],
            source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            audio_sha256=info["sha256"],
            provenance=info.get("source_provenance"),
            scope="whole recording diagnostic, not invented unit timing",
            graph_assessment=(
                "correctly unavailable: saved unvoiced negative"
                if name.startswith("neg_") or name == "silence_original"
                else "existing false periodic pitch survives; not reliable speech evidence"
                if name in {"silence_periodic", "silence_accidental"}
                else "quality gate removes known voiced low F0; not an energy-gate failure"
                if name == "syn_steady_70"
                else "retained evidence available; detailed acoustic validity remains separate"
            ),
        )
        controls.append(item)
        if name.startswith("neg_") or name in {
            "syn_steady_70",
            "syn_steady_110",
            "silence_periodic",
            "silence_accidental",
        }:
            fixtures.append(
                {
                    "id": name,
                    "threshold": item["threshold_rms"],
                    "duration": r["duration_seconds"],
                    "f0": r["f0"],
                }
            )
    assert physical
    audio_path = ROOT / "services/api/var/audio" / physical["audio"]["storage_key"]
    rate, values = waveform(audio_path)
    width, hop = round(rate * 0.04), round(rate * 0.01)
    energies = [
        float(np.sqrt(np.mean(values[i : i + width] ** 2)))
        for i in range(0, max(1, len(values) - width + 1), hop)
    ]
    floor = float(np.quantile(energies, 0.1))
    threshold = max(0.003, min(3 * floor, max(energies) * 0.15))
    r = physical["acoustic"]["normalized_result"]
    assert math.isclose(threshold, r["energy_gate"]["threshold_rms"], abs_tol=1e-12)
    frame_table = []
    for i, f in enumerate(r["f0"]):
        if not (2.74 <= f["timestamp_seconds"] < 3.04 and f.get("tracker_f0_hz")):
            continue
        center = round(f["timestamp_seconds"] * rate)
        frame = values[center - width // 2 : center + width // 2]
        rms = float(np.sqrt(np.mean(frame**2)))
        assert abs(rms - f["energy_rms"]) < 1e-6
        frame_table.append(
            {
                "source_index": i,
                **f,
                "threshold_rms": threshold,
                "rms_over_threshold": rms / threshold,
                "previous_rms": r["f0"][i - 1]["energy_rms"],
                "next_rms": r["f0"][i + 1]["energy_rms"],
                "canonical_rms": rms,
                "canonical_peak": float(np.max(np.abs(frame))),
                "position_in_unit": (f["timestamp_seconds"] - 2.74) / 0.30,
            }
        )
    windows = []
    # Spectral energy context only, never another F0 tracker or ground-truth claim.
    for name, start, end in (
        ("pre_speech", 0.1, 0.4),
        ("ge_louder_tracker_unvoiced", 2.78, 2.89),
        ("ge_late_raw_voiced", 2.94, 3.02),
        ("post_speech", 3.08, 3.20),
    ):
        x = values[round(start * rate) : round(end * rate)]
        spectrum = np.abs(np.fft.rfft((x - x.mean()) * np.hanning(len(x)))) ** 2
        frequencies = np.fft.rfftfreq(len(x), 1 / rate)
        low = float(spectrum[(frequencies >= 40) & (frequencies <= 80)].sum())
        total = float(spectrum[(frequencies >= 40) & (frequencies <= 4000)].sum())
        windows.append(
            {
                "name": name,
                "start": start,
                "end": end,
                "rms": float(np.sqrt(np.mean(x**2))),
                "peak": float(np.max(np.abs(x))),
                "low_band_fraction": low / total,
                "spectral_resolution_hz": rate / len(x),
            }
        )
    output = {
        "threshold_rms": threshold,
        "floor_rms": floor,
        "peak_window_rms": max(energies),
        "absolute_minimum": 0.003,
        "triple_noise_floor": 3 * floor,
        "peak_cap": max(energies) * 0.15,
        "canonical_sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
        "frames": frame_table,
        "waveform_windows": windows,
        "controls": controls,
    }
    (OUT / "energy-replay.json").write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    (ROOT / "services/api/tests/fixtures/energy_gate_saved_controls.json").write_text(
        json.dumps(fixtures, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    print(
        json.dumps({k: v for k, v in output.items() if k not in {"frames", "controls"}}, indent=2)
    )
    for row in controls:
        if row["id"].endswith(":个") or row["kind"] != "accepted_unit":
            print(
                row["id"],
                row["raw"]["count"],
                row["selected"]["count"],
                row["energy_rejected"],
                row["raw"]["maximum_jump_st"],
                row["above_gate_but_tracker_unvoiced"],
            )


if __name__ == "__main__":
    run()
