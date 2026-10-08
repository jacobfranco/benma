"""Saved production-frame replay only: no audio extraction, providers, or trackers."""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from pathlib import Path

from benma_api.pronunciation.contours import classify_contour
from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    display_from_track,
    gate_observation,
    interpretation_eligibility,
    project_pitch,
)

ROOT = Path(__file__).resolve().parents[2]
SAVED = ROOT / "services/api/var/f0-foundation"
OUTPUT = ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence"


def main() -> None:
    manifest = json.loads((SAVED / "manifest-local.json").read_text())
    previous = json.loads((ROOT / "services/api/var/capture-robustness/replay.json").read_text())
    lookup = {r["sha256"]: r for r in previous if "sha256" in r}
    rows, timing, tracks = [], [], {}
    for entry in manifest:
        # These saved frames are the pre-existing PRODUCTION selection, not six-tracker runs.
        if entry["kind"] not in {"capture", "negative"}:
            continue
        saved = json.loads((SAVED / "production" / (entry["id"] + ".json")).read_text())
        result = saved["result"]
        t = time.perf_counter()
        track = build_pitch_track(
            result,
            audio_sha256=entry["sha256"],
            tracker_source="praat_autocorrelation",
            tracker_version="saved-production",
            parameters={"provenance": "frozen production JSON"},
        )
        build_ms = (time.perf_counter() - t) * 1000
        assert [f.timestamp_seconds for f in track.frames if f.selected_f0_hz] == saved[
            "retained_times"
        ]
        tracks[entry["id"]] = track
        before = lookup.get(entry["sha256"], {})
        windows = [
            dict(label=w["character"], start=w["start"], end=w["end"], observed=w["observed"])
            for w in before.get("methods", {}).get("baseline", {}).get("rows", [])
            if isinstance(w.get("start"), (int, float)) and isinstance(w.get("end"), (int, float))
        ]
        if not windows:
            windows = entry.get("diagnostic_windows", [])
        if entry["kind"] == "negative" or not windows:
            windows = [
                *windows,
                dict(
                    label="whole waveform (diagnostic only)",
                    start=0,
                    end=result["duration_seconds"],
                ),
            ]
        for w in windows:
            t = time.perf_counter()
            p = project_pitch(track, w["start"], w["end"], timing_source="saved_research_interval")
            projected = (time.perf_counter() - t) * 1000
            t = time.perf_counter()
            eligible = interpretation_eligibility(track, p)
            eligibility_ms = (time.perf_counter() - t) * 1000
            t = time.perf_counter()
            observed = classify_contour(
                display_from_track(track), w["start"], w["end"], raw=result["f0"], pitch_track=track
            )
            after = gate_observation(observed, eligible)
            gesture_ms = (time.perf_counter() - t) * 1000
            timing.append(
                dict(
                    recording=entry["id"],
                    build_ms=build_ms,
                    projection_ms=projected,
                    eligibility_ms=eligibility_ms,
                    gesture_ms=gesture_ms,
                )
            )
            rows.append(
                dict(
                    recording=entry["id"],
                    audio_sha256=entry["sha256"],
                    projection=p.model_dump(mode="json"),
                    learner_comparison="uncertain",
                    negative=entry["kind"] == "negative",
                    region=w["label"],
                    start=w["start"],
                    end=w["end"],
                    before=w.get("observed", observed.model_dump()),
                    after=after.model_dump(),
                    acoustic_candidate=observed.model_dump(),
                    eligibility=eligible.model_dump(mode="json"),
                )
            )
    # Scan every possible 120/200/400-ms negative window: whole-recording rejection
    # must not hide a coherent spurious island a future alignment could attribute.
    negative_windows = []
    for entry in manifest:
        if entry["kind"] != "negative":
            continue
        track = tracks[entry["id"]]
        counts = Counter()
        sufficient = []
        for width in (0.12, 0.2, 0.4):
            for f in track.frames:
                if f.timestamp_seconds + width > track.duration_seconds:
                    continue
                p = project_pitch(
                    track,
                    f.timestamp_seconds,
                    f.timestamp_seconds + width,
                    timing_source="negative_window_stress",
                )
                e = interpretation_eligibility(track, p)
                counts[e.state] += 1
                if e.state == "sufficient":
                    sufficient.append([f.timestamp_seconds, f.timestamp_seconds + width])
        negative_windows.append(
            dict(recording=entry["id"], states=dict(counts), sufficient_intervals=sufficient)
        )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "replay.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    (OUTPUT / "negative-window-stress.json").write_text(
        json.dumps(negative_windows, indent=2) + "\n"
    )
    (OUTPUT / "processing-timings.json").write_text(
        json.dumps(
            dict(
                samples=timing,
                summary={
                    key: dict(
                        median=statistics.median(r[key] for r in timing),
                        maximum=max(r[key] for r in timing),
                    )
                    for key in ("build_ms", "projection_ms", "eligibility_ms", "gesture_ms")
                },
            ),
            indent=2,
        )
        + "\n"
    )
    print("Saved-only regions:", len(rows), Counter(r["eligibility"]["state"] for r in rows))
    for r in rows:
        if r["recording"] in {
            "take_1",
            "take_2",
            "take_3",
            "human_control",
            "f5dc0cc1",
            "silence_accidental",
        }:
            print(
                r["recording"],
                r["region"],
                r["before"]["classification"],
                r["after"]["classification"],
                r["eligibility"]["state"],
                r["eligibility"]["reasons"],
            )
    print(
        "Negative interval stress:",
        [{k: v for k, v in r.items() if k != "sufficient_intervals"} for r in negative_windows],
    )


if __name__ == "__main__":
    main()
