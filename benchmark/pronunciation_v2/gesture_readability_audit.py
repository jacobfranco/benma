"""Offline saved-evidence audit. No tracker, provider, DB write, or lexical inference.

Run with services/api/.venv/bin/python -m benchmark.pronunciation_v2.gesture_readability_audit.
Private source snapshots live in services/api/var/gesture-readability/saved.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from itertools import pairwise
from pathlib import Path

from benma_api.pronunciation.pitch_evidence import project_pitch
from benma_api.pronunciation.pitch_types import UtterancePitchTrack

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/pronunciation-v2/2026-10-08-gesture-readability"
RECORDINGS = (
    "89cee47e",
    "7e6b6fe9",
    "6b5b2135",
    "0b194cf9",
    "ee8a8b32",
    "40357072",
    "8d252264",
    "4b9dbd2b",
    "8faf1a90",
    "a5acd04c",
    "b9067bec",
    "5c70f317",
    "d47274bc",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> None:
    snapshots = []
    for path in (ROOT / "services/api/var/gesture-readability/saved").glob("*.json"):
        value = json.loads(path.read_text())
        recording = Path(value["audio"]["storage_key"]).stem
        if recording[:8] in RECORDINGS:
            snapshots.append((path, recording, value))
    snapshots.sort(key=lambda x: RECORDINGS.index(x[1][:8]))
    assert len(snapshots) == len(RECORDINGS)
    inputs = [
        {
            "data": p["analysis"]["result"],
            "audioPath": str(ROOT / "services/api/var/audio" / p["audio"]["storage_key"]),
        }
        for _, _, p in snapshots
    ]
    replay = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "benchmark/pronunciation_v2/workspace_projection.cjs")],
            input=json.dumps(inputs).encode(),
        )
    )
    corpus, audit = [], []
    for (path, recording, p), rendered in zip(snapshots, replay, strict=True):
        d = p["analysis"]["result"]
        track = UtterancePitchTrack.model_validate(
            p["acoustic"]["normalized_result"]["utterance_pitch_track"]
        )
        audio = ROOT / "services/api/var/audio" / p["audio"]["storage_key"]
        assert digest(audio) == p["audio"]["sha256"] == track.audio_sha256
        assert track.audio_sha256 == p["analysis"]["audio_sha256"]
        assert p["analysis"]["acoustic_run_id"] == p["acoustic"]["id"]
        assert p["analysis"]["utterance_id"] == p["acoustic"]["utterance_id"]
        original_track = p["acoustic"]["normalized_result"]["utterance_pitch_track"]
        content = {k: v for k, v in original_track.items() if k != "evidence_id"}
        assert (
            hashlib.sha256(
                json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            == track.evidence_id
        )
        assert (
            d["pitch_track_evidence_id"]
            == d["tone_graph"]["track_evidence_id"]
            == track.evidence_id
        )
        by_time = {f.timestamp_seconds: i for i, f in enumerate(track.frames)}
        for raw in d["tone_graph"]["raw"]:
            f = track.frames[raw["source_frame_index"]]
            assert raw["timestamp_seconds"] == f.timestamp_seconds
            assert raw["selected_f0_hz"] == f.selected_f0_hz
        units = []
        for u in rendered:
            source = (
                next(g for g in d["timing_groups"] if g["text"] == u["text"])
                if u["grouped"]
                else d["syllables"][u["members"][0]]
            )
            projection = project_pitch(
                track,
                u["start"],
                u["end"],
                timing_source=source.get("timing_source", source.get("source")),
                timing_evidence_id=source["timing_evidence_id"],
            )
            assert projection.model_dump(mode="json") == source["pitch_projection"]
            indices = [
                by_time[point["timestamp_seconds"]]
                for seg in u["contour"]["segments"]
                for point in seg
            ]
            expected = [i for i in projection.frame_indices if track.frames[i].selected_f0_hz]
            assert indices == expected
            for seg in u["contour"]["segments"]:
                for point in seg:
                    f = track.frames[by_time[point["timestamp_seconds"]]]
                    assert u["start"] <= f.timestamp_seconds < u["end"]
                    assert f.selected_f0_hz is not None and track.baseline_hz is not None
                    assert math.isclose(
                        point["normalized_semitones"],
                        12 * math.log2(f.selected_f0_hz / track.baseline_hz),
                        abs_tol=1e-10,
                    )
            assert (
                u["playback"]["samples"]
                == u["playback"]["last_sample"] - u["playback"]["first_sample"]
            )
            segments = [
                [
                    {
                        "index": by_time[q["timestamp_seconds"]],
                        "t": q["timestamp_seconds"],
                        "st": q["normalized_semitones"],
                    }
                    for q in seg
                ]
                for seg in u["contour"]["segments"]
            ]
            gaps = [
                {
                    "left": a[-1]["t"],
                    "right": b[0]["t"],
                    "missing_seconds": round(b[0]["t"] - a[-1]["t"] - 0.01, 8),
                }
                for a, b in pairwise(segments)
            ]
            item = {
                "id": f"{recording[:8]}:{u['text']}",
                "recording": recording,
                "analysis_id": p["analysis"]["id"],
                "text": u["text"],
                "start": u["start"],
                "end": u["end"],
                "grouped": u["grouped"],
                "segments": segments,
                "eligibility": source["pitch_eligibility"],
                "current_gesture": source.get("observed_gesture", "unclear"),
                "current_reason": source.get("observed_contour", {}).get("reason", "grouped"),
                "current_features": source.get("observed_contour", {}).get("features", {}),
                "manual_geometry": "UNCLEAR",
                "manual_reason": "Not yet reviewed",
            }
            raw_voiced = [i for i in projection.frame_indices if track.frames[i].raw_f0_hz]
            flagged: set[int] = set()
            for a, b in pairwise(raw_voiced):
                left, right = track.frames[a], track.frames[b]
                assert left.raw_f0_hz is not None and right.raw_f0_hz is not None
                if (
                    right.timestamp_seconds - left.timestamp_seconds <= 0.12
                    and abs(12 * math.log2(right.raw_f0_hz / left.raw_f0_hz)) > 6
                ):
                    flagged.update((a, b))
            item["flagged_indices"] = sorted(flagged)
            corpus.append(item)
            units.append(
                {
                    **u,
                    "track_evidence_id": track.evidence_id,
                    "projection_indices": list(projection.frame_indices),
                    "selected_indices": indices,
                    "selected_timestamps": [track.frames[i].timestamp_seconds for i in indices],
                    "first_selected": track.frames[indices[0]].timestamp_seconds
                    if indices
                    else None,
                    "last_selected": track.frames[indices[-1]].timestamp_seconds
                    if indices
                    else None,
                    "selected_count": len(indices),
                    "gaps": gaps,
                    "eligibility": source["pitch_eligibility"],
                    "observed_gesture": item["current_gesture"],
                    "raw_voiced": [
                        {"index": i, **track.frames[i].model_dump(mode="json")}
                        for i in projection.frame_indices
                        if track.frames[i].raw_f0_hz
                    ],
                }
            )
        audit.append(
            {
                "recording": recording,
                "created_at": p["analysis"]["created_at"],
                "analysis_id": p["analysis"]["id"],
                "utterance_id": p["analysis"]["utterance_id"],
                "perception_id": p["perception"]["id"],
                "attempts": p["attempts"],
                "transcript": p["perception"]["transcript"],
                "acoustic_run_id": p["acoustic"]["id"],
                "snapshot_sha256": digest(path),
                "audio_sha256": digest(audio),
                "track_evidence_id": track.evidence_id,
                "units": units,
            }
        )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "projection-replay.json").write_text(
        json.dumps(audit, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    # Preserve manually reviewed labels when rerunning the audit.
    corpus_path = OUT / "calibration-corpus.json"
    previous = (
        {r["id"]: r for r in json.loads(corpus_path.read_text())} if corpus_path.exists() else {}
    )
    for row in corpus:
        if row["id"] in previous:
            row.update({k: previous[row["id"]][k] for k in ("manual_geometry", "manual_reason")})
    corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, separators=(",", ":")) + "\n")
    physical = snapshots[0][2]
    fixture = {
        "provenance": {k: v for k, v in audit[0].items() if k != "units"},
        "track": physical["acoustic"]["normalized_result"]["utterance_pitch_track"],
        "data": physical["analysis"]["result"],
    }
    (ROOT / "services/api/tests/fixtures/pitch_projection_89cee47e.json").write_text(
        json.dumps(fixture, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    print(
        f"Verified {len(audit)} recordings, {len(corpus)} accepted units, "
        f"{sum(len(s) for r in corpus for s in r['segments'])} selected measurements"
    )
    for row in corpus:
        values = [q["st"] for s in row["segments"] for q in s]
        bins = (
            [
                round(
                    statistics.median(values[i * len(values) // 9 : (i + 1) * len(values) // 9]), 2
                )
                for i in range(9)
            ]
            if len(values) >= 9
            else values
        )
        print(
            row["id"],
            row["eligibility"]["state"],
            row["current_gesture"],
            "segments",
            [len(s) for s in row["segments"]],
            "nine medians",
            bins,
        )


if __name__ == "__main__":
    run()
