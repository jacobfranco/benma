"""Replay frozen Oct 6 evidence and accepted timing; never call a provider/tracker."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from itertools import pairwise
from pathlib import Path

from benchmark.pronunciation_v2.relative_pitch_gesture import (
    Sample,
    Unit,
    pairwise_error,
    project_relative,
)

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / "services/api/var/relative-pitch-gesture"
REPORT = ROOT / "docs/research/pronunciation-v2/2026-10-07-relative-pitch-gesture"
SAVED = ROOT / "services/api/var/f0-foundation"


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def accepted_units(data):
    """Use persisted accepted projections, not raw provider words or equal splits."""
    if data["alignment_status"] in {"synthetic", "unavailable"}:
        return []
    result = []
    for s in [*data["syllables"], *data["timing_groups"]]:
        projection = s.get("pitch_projection") or {}
        start, end = s.get("start_seconds"), s.get("end_seconds")
        if start is None or end is None:
            continue
        assert projection["start_seconds"] == start and projection["end_seconds"] == end
        assert projection["track_evidence_id"] == data["pitch_track_evidence_id"]
        grouped = "text" in s
        if grouped:
            members = [
                m
                for m in data["syllables"]
                if s["character_start"] <= m["character_start"]
                and m["character_end"] <= s["character_end"]
            ]
            assert len(members) > 1 and all(m["start_seconds"] is None for m in members)
            assert "".join(m["characters"] for m in members) == s["text"]
        result.append(
            (
                Unit(str(s["character_start"]), start, end, projection["timing_source"]),
                s.get("characters", s.get("text")),
                grouped,
                s,
            )
        )
    return sorted(result, key=lambda u: u[0].start)


def control_replay():
    protected = {r["recording"]: set(r["times"]) for r in read(SAVED / "low-f0-proxy-samples.json")}
    controls = []
    low_view = None
    for id_ in [*protected, "syn_steady_70", "native_24k", "take_1", "take_2", "take_3"]:
        saved = read(SAVED / "production" / (id_ + ".json"))
        raw = saved["result"]["f0"]
        retained = set(saved["retained_times"])
        samples = [
            Sample(
                i,
                p["timestamp_seconds"],
                p["f0_hz"] if p["timestamp_seconds"] in retained else None,
            )
            for i, p in enumerate(raw)
        ]
        # Whole-recording stress unit is explicitly a control fixture, not inferred timing.
        duration = saved["result"]["duration_seconds"]
        projected = project_relative(
            samples, [Unit("control", 0, duration, "frozen_control_fixture")]
        )
        points = [p for s in projected["segments"] for p in s]
        assert {p["timestamp_seconds"] for p in points} == retained
        kept = protected.get(id_, set()) & {p["timestamp_seconds"] for p in points}
        assert kept == protected.get(id_, set())
        for multiplier in [0.5, 2, 8]:
            shifted = project_relative(
                [
                    Sample(
                        s.source_index,
                        s.timestamp_seconds,
                        s.selected_hz * multiplier if s.selected_hz else None,
                    )
                    for s in samples
                ],
                [Unit("control", 0, duration, "frozen_control_fixture")],
            )
            shifted_points = [p for seg in shifted["segments"] for p in seg]
            assert (
                max(
                    (
                        abs(a["normalized_semitones"] - b["normalized_semitones"])
                        for a, b in zip(points, shifted_points, strict=True)
                    ),
                    default=0,
                )
                < 1e-10
            )
        controls.append(
            dict(
                id=id_,
                selected=len(retained),
                protected=len(kept),
                pairwise_error=pairwise_error(projected),
                selected_min_hz=min(s.selected_hz for s in samples if s.selected_hz),
            )
        )
        if id_ == "7787300e":
            explicit = next(s for s in samples if s.timestamp_seconds == 2.5124)
            assert explicit.selected_hz == 54.61
            low_view = dict(
                id=id_,
                duration=duration,
                samples=[vars(s) for s in samples],
                relative=projected,
                explicit=vars(explicit),
            )
    under70 = read(
        ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json"
    )
    for row in under70:
        assert row["timestamp"] in protected[row["recording"]]
    assert sum(r["protected"] for r in controls) == 617
    return dict(
        controls=controls,
        protected_preserved=617,
        under70_preserved=len(under70),
        under70=under70,
        max_pairwise_error=max(r["pairwise_error"] for r in controls),
    ), low_view


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    rows, adapters = [], []
    sources = {}
    saved_path = LOCAL / "saved-analyses.json"
    sources[str(saved_path.relative_to(ROOT))] = hashlib.sha256(saved_path.read_bytes()).hexdigest()
    for saved in read(saved_path):
        id_ = saved["id"]
        data = saved["analyses"][-1]["result"]
        before = json.dumps(data, sort_keys=True)
        path = ROOT / "services/api/var/octave-ambiguity/before" / (id_ + ".json")
        capture = read(path)
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        track = capture["track"]
        assert track["evidence_id"] == data["pitch_track_evidence_id"]
        assert saved["sha256"] == capture["sha256"]
        frames = track["frames"]
        for f, r in zip(frames, data["tone_graph"]["raw"], strict=True):
            assert f["timestamp_seconds"] == r["timestamp_seconds"]
            assert f["selected_f0_hz"] == r["selected_f0_hz"]
            assert f["raw_f0_hz"] == r["tracker_f0_hz"]
        samples = [
            Sample(i, f["timestamp_seconds"], f["selected_f0_hz"]) for i, f in enumerate(frames)
        ]
        accepted = accepted_units(data)
        for u, _, _, original in accepted:
            assert original["pitch_projection"]["frame_indices"] == [
                i for i, f in enumerate(frames) if u.start <= f["timestamp_seconds"] < u.end
            ]
        relative = project_relative(samples, [u for u, _, _, _ in accepted])
        for unit, (_, label, grouped, original) in zip(relative["units"], accepted, strict=True):
            unit.update(
                label=label,
                grouped=grouped,
                eligibility=original.get("pitch_eligibility"),
                center_st_re_recording=(
                    unit["center_semitones_re_1hz"] - 12 * math.log2(track["baseline_hz"])
                )
                if unit["selected_count"]
                else None,
            )
            points = [p for seg in unit["segments"] for p in seg]
            # Inventory existing >6 st discontinuities, not a new rejection rule.
            unit["large_selected_steps"] = [
                dict(
                    start=a["timestamp_seconds"],
                    end=b["timestamp_seconds"],
                    gap_seconds=b["timestamp_seconds"] - a["timestamp_seconds"],
                    delta_st=b["absolute_semitones"] - a["absolute_semitones"],
                    missing_between=b["source_frame_index"] - a["source_frame_index"] > 1,
                )
                for a, b in pairwise(points)
                if abs(b["absolute_semitones"] - a["absolute_semitones"]) > 6
            ]
            unit["selected_indices"] = [p["source_frame_index"] for p in points]
        projected = [p for seg in relative["segments"] for p in seg]
        relative_indices = {p["source_frame_index"] for p in projected}
        expected = {
            s.source_index
            for s in samples
            if s.selected_hz is not None
            and any(u.start <= s.timestamp_seconds < u.end for u, _, _, _ in accepted)
        }
        assert relative_indices == expected
        assert len(relative_indices) == len(projected)
        assert json.dumps(data, sort_keys=True) == before
        rows.append(
            dict(
                id=id_,
                audio_sha256=saved["sha256"],
                analysis_id=saved["analyses"][-1]["id"],
                analysis_created_at=saved["analyses"][-1]["created_at"],
                transcript="".join(s["characters"] for s in data["syllables"]),
                alignment_status=data["alignment_status"],
                timing_units=len(accepted),
                individual_units=sum(not g for _, _, g, _ in accepted),
                grouped_units=sum(g for _, _, g, _ in accepted),
                empty_pitch_units=sum(not u["selected_count"] for u in relative["units"]),
                selected_count=sum(s.selected_hz is not None for s in samples),
                projected_count=len(projected),
                unassigned_selected_indices=[
                    s.source_index
                    for s in samples
                    if s.selected_hz is not None and s.source_index not in relative_indices
                ],
                pairwise_error=pairwise_error(relative),
                duration=data["duration_seconds"],
                baseline_hz=track["baseline_hz"],
                relative=relative,
                filtered=data["tone_graph"]["filtered"],
                absolute_mine=data["tone_graph"]["mine"],
                raw=data["tone_graph"]["raw"],
            )
        )
        adapters.append(dict(data=data, relative=relative))
    geometry = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "benchmark/pronunciation_v2/relative_pitch_geometry.cjs")],
            input=json.dumps(adapters),
            text=True,
        )
    )
    for row, layout in zip(rows, geometry, strict=True):
        row["layout"] = layout
        # Actual mobile mapping must not drop, duplicate, or invent prototype points.
        assert sorted(
            p["source_frame_index"] for seg in layout["proposed"]["segments"] for p in seg
        ) == sorted(p["source_frame_index"] for seg in row["relative"]["segments"] for p in seg)
        row["target_independence"] = layout["target_independence"]
        row["input_unchanged"] = layout["input_unchanged"]
        # Sensitivity: translate the current smoothed/simplified vertices too.
        # This is diagnostic only; it cannot satisfy the exact measured-pair invariant.
        translated = [
            p["normalized_semitones"] - u["center_st_re_recording"]
            for seg in layout["current"]["segments"]
            for p in seg
            for u in row["relative"]["units"]
            if u["start_seconds"] <= p["timestamp_seconds"] < u["end_seconds"]
        ]
        row["translated_existing_mine_domain"] = [
            min(-3, min(translated, default=0) - 1),
            max(3, max(translated, default=0) + 1),
        ]
        row["domain_span_ratio"] = (
            (layout["relative_domain"][1] - layout["relative_domain"][0])
            / (layout["current_domain"][1] - layout["current_domain"][0])
            if row["projected_count"]
            else None
        )
    controls, low_view = control_replay()
    summary = dict(
        recordings=[
            {
                k: v
                for k, v in row.items()
                if k not in {"raw", "filtered", "absolute_mine", "layout"}
            }
            | dict(
                current_domain=row["layout"]["current_domain"],
                relative_domain=row["layout"]["relative_domain"],
            )
            for row in rows
        ],
        controls=controls,
        input_sha256=sources,
        production_integration=False,
        outcome="B",
        projection_scope="Full-resolution selected measurements; no smoothing or simplification",
    )
    dump(REPORT / "replay.json", summary)
    dump(LOCAL / "viewer-data.json", dict(recordings=rows, low_control=low_view))
    template = (ROOT / "benchmark/pronunciation_v2/relative_pitch_viewer.html").read_text()
    (LOCAL / "viewer.html").write_text(
        template.replace(
            "__EVIDENCE_JSON__",
            json.dumps(dict(recordings=rows, low_control=low_view), ensure_ascii=False).replace(
                "</", "<\\/"
            ),
        )
    )
    for row in rows:
        print(
            row["id"][:8],
            row["timing_units"],
            row["projected_count"],
            row["layout"]["current_domain"],
            row["layout"]["relative_domain"],
            "large-step units:",
            [
                (u["label"], len(u["large_selected_steps"]))
                for u in row["relative"]["units"]
                if u["large_selected_steps"]
            ],
        )
    print(
        "Controls",
        controls["protected_preserved"],
        controls["under70_preserved"],
        "pairwise error",
        max([r["pairwise_error"] for r in rows] + [controls["max_pairwise_error"]]),
    )


if __name__ == "__main__":
    main()
