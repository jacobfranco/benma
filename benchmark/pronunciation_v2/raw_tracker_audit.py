"""Read-only saved tracker diagnostic; optional local audio replay, never provider I/O.

python -m benchmark.pronunciation_v2.raw_tracker_audit snapshot.json [snapshot2.json]
  --retrack --audio-root services/api/var/audio --frames --start 1.2 --end 1.47

Supports current measurement snapshots and existing gesture-readability snapshots.
Candidate strengths describe autocorrelation, not calibrated voice probabilities.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


def distribution(values: list[float]) -> dict[str, float] | None:
    return (
        {"min": min(values), "median": statistics.median(values), "max": max(values)}
        if values
        else None
    )


def frame_diagnostic(point: dict, retained: dict, ceiling: float = 550) -> dict:
    candidates = [c for c in point.get("pitch_candidates", []) if 0 < c["frequency_hz"] <= ceiling]
    raw = point.get("tracker_f0_hz")
    selected = retained.get("selected_f0_hz")
    # selection_reason='praat_selected' can coexist with raw=None in saved data.
    # Classify the actual stage, not that legacy fallback string.
    if raw is not None:
        state = "retained" if selected is not None else "benma_rejected_voiced_output"
    elif "pitch_candidates" not in point:
        state = "candidate_history_unavailable"
    else:
        state = (
            "estimator_unvoiced_with_candidates"
            if candidates
            else "estimator_no_in_range_candidates"
        )
    best = max(candidates, key=lambda c: c["strength"], default=None)
    return {
        "timestamp_seconds": point["timestamp_seconds"],
        "raw_f0_hz": raw,
        "selected_strength": point.get("voicing_probability"),
        "candidate_count": len(candidates),
        "best_candidate": best,
        "candidates": candidates,
        "energy_rms": point.get("energy_rms"),
        "energy_gated": point.get("energy_gated"),
        "comparison_f0_hz": point.get("comparison_f0_hz"),
        "filter_disagreement_st": point.get("filter_disagreement_st"),
        "state": state,
        "retained_f0_hz": selected,
        "exclusion_reasons": retained.get("exclusion_reasons", []),
        "saved_selection_reason": point.get("selection_reason"),
    }


def summarize_frames(frames: list[dict], start: float, end: float, hop: float = 0.01) -> dict:
    def continuity(key: str) -> dict:
        voiced = [f for f in frames if f[key] is not None]
        runs = 0
        last = None
        missing_run = longest_missing = 0
        jumps = []
        for f in frames:
            if f[key] is None:
                missing_run += 1
                longest_missing = max(longest_missing, missing_run)
                continue
            missing_run = 0
            if last is None or f["timestamp_seconds"] - last["timestamp_seconds"] > hop * 1.5:
                runs += 1
            if last and f["timestamp_seconds"] - last["timestamp_seconds"] <= 0.12:
                jumps.append(abs(12 * math.log2(f[key] / last[key])))
            last = f
        return {
            "voiced_frames": len(voiced),
            "voiced_ratio": len(voiced) / len(frames) if frames else 0,
            "f0_hz": distribution([f[key] for f in voiced]),
            "fragment_count": runs,
            "longest_unvoiced_run_seconds": round(longest_missing * hop, 8),
            "largest_jump_st_within_120ms": max(jumps, default=0),
            "jumps_over_6st": sum(j > 6 for j in jumps),
        }

    return {
        "interval": [start, end],
        "total_frames": len(frames),
        "states": dict(Counter(f["state"] for f in frames)),
        "raw": continuity("raw_f0_hz"),
        "retained": continuity("retained_f0_hz"),
        "raw_voiced_strength": distribution(
            [f["selected_strength"] for f in frames if f["raw_f0_hz"]]
        ),
        "best_candidate_strength": distribution(
            [f["best_candidate"]["strength"] for f in frames if f["best_candidate"]]
        ),
        "frame_energy_rms": distribution(
            [f["energy_rms"] for f in frames if f["energy_rms"] is not None]
        ),
    }


def audit_snapshot(
    saved: dict,
    *,
    audio_root: Path | None = None,
    include_frames: bool = False,
    start: float = 0,
    end: float | None = None,
) -> dict:
    acoustic = saved["acoustic"]
    result = acoustic.get("result", acoustic.get("normalized_result"))
    data = saved.get("data", saved.get("analysis", {}).get("result", {}))
    parameters = acoustic["parameters"]
    raw = result["f0"]
    track = result.get("utterance_pitch_track", {})
    selected = {f["timestamp_seconds"]: f for f in track.get("frames", [])}
    if not selected:
        selected = {f["timestamp_seconds"]: f for f in data.get("tone_graph", {}).get("raw", [])}
    frames = [
        frame_diagnostic(p, selected.get(p["timestamp_seconds"], {}), parameters["pitch_ceiling"])
        for p in raw
    ]
    stop = end if end is not None else result["duration_seconds"]
    window = [f for f in frames if start <= f["timestamp_seconds"] < stop]
    output: dict[str, Any] = {
        "id": saved.get("id", saved.get("analysis", {}).get("id")),
        "created_at": saved.get("created_at", saved.get("analysis", {}).get("created_at")),
        "audio_sha256": saved["audio"]["sha256"],
        "sample_rate_hz": result["sample_rate_hz"],
        "duration_seconds": result["duration_seconds"],
        "algorithm": acoustic["algorithm"],
        "algorithm_version": acoustic.get("version", acoustic.get("algorithm_version")),
        "parameters": parameters,
        "recording_quality": result["recording_quality"],
        "energy_gate": result.get("energy_gate"),
        "provider_snr_db": data.get("timing_evidence", {}).get("provider_timing", {}).get("SNR"),
        "summary": summarize_frames(window, start, stop, parameters["time_step"]),
        "syllables": [
            {
                "text": s["characters"],
                **summarize_frames(
                    [
                        f
                        for f in frames
                        if s["start_seconds"] <= f["timestamp_seconds"] < s["end_seconds"]
                    ],
                    s["start_seconds"],
                    s["end_seconds"],
                    parameters["time_step"],
                ),
            }
            for s in data.get("syllables", [])
            if s.get("start_seconds") is not None
        ],
    }
    if audio_root is not None:
        import parselmouth
        from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer

        path = audio_root / saved["audio"]["storage_key"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == saved["audio"]["sha256"]
        analyzer = PraatAcousticAnalyzer()
        tracker_parameters = {
            k: v for k, v in parameters.items() if k not in {"energy_gate", "quality_gate"}
        }
        assert {
            k: v for k, v in analyzer.parameters.items() if k not in {"energy_gate", "quality_gate"}
        } == tracker_parameters, "Configuration differs; do not claim identical replay"
        replay = analyzer.analyze(path)
        pitch = parselmouth.Sound(str(path)).to_pitch_ac(
            **{k: v for k, v in parameters.items() if k not in {"energy_gate", "quality_gate"}}
        )
        output["replay"] = {
            "all_f0_fields_equal": replay["f0"] == raw,
            "raw_tracker_equal": all(
                a.get("tracker_f0_hz") == b.get("tracker_f0_hz")
                for a, b in zip(raw, replay["f0"], strict=True)
            ),
            "raw_candidates_equal": all(
                a.get("pitch_candidates") == b.get("pitch_candidates")
                for a, b in zip(raw, replay["f0"], strict=True)
            ),
            "background_periodicity": replay.get("background_periodicity"),
            "selection": replay.get("selection"),
            "frame_count": len(replay["f0"]),
            "audio_sha256_verified": True,
        }
        for f, original in zip(frames, pitch, strict=True):
            intensity = float(original.intensity)
            silence, voicing = parameters["silence_threshold"], parameters["voicing_threshold"]
            unvoiced_score = (
                voicing + max(0, 2 - intensity / (silence / (1 + voicing)))
                if silence > 0
                else voicing
            )
            scores = [
                float(c.strength)
                - parameters["octave_cost"]
                * math.log2(parameters["pitch_ceiling"] / float(c.frequency))
                for c in original.candidates
                if 0 < c.frequency <= parameters["pitch_ceiling"]
            ]
            f.update(
                praat_intensity=intensity,
                unvoiced_local_score=unvoiced_score,
                best_voiced_local_score=max(scores, default=None),
            )
        # This explains local vs path decisions, not a proposed alternate tracker.
        output["replay"]["unvoiced_with_locally_preferred_candidate"] = [
            f["timestamp_seconds"]
            for f in window
            if f["raw_f0_hz"] is None
            and f["best_voiced_local_score"] is not None
            and f["best_voiced_local_score"] > f["unvoiced_local_score"]
        ]
    if include_frames:
        output["frames"] = window
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots", type=Path, nargs="+")
    parser.add_argument("--retrack", action="store_true")
    parser.add_argument("--audio-root", type=Path, default=Path("services/api/var/audio"))
    parser.add_argument("--frames", action="store_true")
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--end", type=float)
    args = parser.parse_args()
    print(
        json.dumps(
            [
                audit_snapshot(
                    json.loads(p.read_text()),
                    audio_root=args.audio_root if args.retrack else None,
                    include_frames=args.frames,
                    start=args.start,
                    end=args.end,
                )
                for p in args.snapshots
            ],
            ensure_ascii=False,
            indent=2,
        )
    )
