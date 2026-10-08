"""Bounded fragment replay over the preceding pass's frozen evidence, offline."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
import subprocess
from itertools import pairwise

from benchmark.pronunciation_v2.relative_pitch_fragments import (
    fragment_pairwise_error,
    relative_pitch_fragments,
)
from benchmark.pronunciation_v2.relative_pitch_gesture import Sample, Unit
from benchmark.pronunciation_v2.relative_pitch_report import (
    LOCAL,
    REPORT,
    ROOT,
    SAVED,
    accepted_units,
    dump,
    read,
)

OUT = LOCAL / "fragments"


def flatten(projection):
    return [p for seg in projection["segments"] for p in seg]


def invariant_check(samples, units, hop, projected):
    points = flatten(projected)
    selected = {
        s.source_index: s
        for s in samples
        if s.selected_hz is not None and any(u.start <= s.timestamp_seconds < u.end for u in units)
    }
    assert set(selected) == {p["source_frame_index"] for p in points}
    assert len(points) == len(selected)
    assert fragment_pairwise_error(projected) < 1e-12
    for p in points:
        source = selected[p["source_frame_index"]]
        assert source.timestamp_seconds == p["timestamp_seconds"]
        assert p["absolute_semitones"] == 12 * math.log2(source.selected_hz)
    # Changing register, including independently across existing fragments,
    # cannot change membership, geometry or domain. No acoustic selection rerun.
    factors = {
        p["source_frame_index"]: (2 if i % 2 else 0.5)
        for i, seg in enumerate(projected["segments"])
        for p in seg
    }
    shifted = relative_pitch_fragments(
        [
            Sample(
                s.source_index,
                s.timestamp_seconds,
                s.selected_hz * factors.get(s.source_index, 1) if s.selected_hz else None,
            )
            for s in samples
        ],
        units,
        cadence_seconds=hop,
    )
    assert [[p["source_frame_index"] for p in seg] for seg in shifted["segments"]] == [
        [p["source_frame_index"] for p in seg] for seg in projected["segments"]
    ]
    assert (
        max(
            (
                abs(a["normalized_semitones"] - b["normalized_semitones"])
                for a, b in zip(points, flatten(shifted), strict=True)
            ),
            default=0,
        )
        < 1e-10
    )


def controls():
    protected = {r["recording"]: set(r["times"]) for r in read(SAVED / "low-f0-proxy-samples.json")}
    results, low = [], None
    for id_ in [*protected, "syn_steady_70", "native_24k", "take_1", "take_2", "take_3"]:
        saved = read(SAVED / "production" / (id_ + ".json"))
        raw = saved["result"]["f0"]
        selected = set(saved["retained_times"])
        samples = [
            Sample(
                i,
                p["timestamp_seconds"],
                p["f0_hz"] if p["timestamp_seconds"] in selected else None,
            )
            for i, p in enumerate(raw)
        ]
        hop = statistics.median(
            b.timestamp_seconds - a.timestamp_seconds for a, b in pairwise(samples)
        )
        units = [Unit("fixture", 0, saved["result"]["duration_seconds"], "frozen_control_fixture")]
        projected = relative_pitch_fragments(samples, units, cadence_seconds=hop)
        invariant_check(samples, units, hop, projected)
        retained = {p["timestamp_seconds"] for p in flatten(projected)}
        assert retained == selected
        assert protected.get(id_, set()) <= retained
        results.append(
            dict(
                id=id_,
                selected=len(retained),
                protected=len(protected.get(id_, set())),
                fragments=len(projected["segments"]),
                pairwise_error=fragment_pairwise_error(projected),
            )
        )
        if id_ == "7787300e":
            low = dict(
                id=id_,
                duration=saved["result"]["duration_seconds"],
                samples=[vars(s) for s in samples],
                projection=projected,
                explicit=vars(next(s for s in samples if s.timestamp_seconds == 2.5124)),
            )
            assert low["explicit"]["selected_hz"] == 54.61
    counter_samples = [Sample(i, 0.01 * i, hz) for i, hz in enumerate([100, 105, 210, 220])]
    counter = relative_pitch_fragments(
        counter_samples, [Unit("continuous", 0, 0.04, "fixture")], cadence_seconds=0.01
    )
    assert len(counter["segments"]) == 1
    high_samples = [Sample(i, 0.01 * i, hz) for i, hz in enumerate([350, 380, 410, 440])]
    high = relative_pitch_fragments(
        high_samples, [Unit("high", 0, 0.04, "fixture")], cadence_seconds=0.01
    )
    invariant_check(high_samples, [Unit("high", 0, 0.04, "fixture")], 0.01, high)
    under70 = read(
        ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json"
    )
    assert all(p["timestamp"] in protected[p["recording"]] for p in under70)
    summary = dict(
        recordings=results,
        protected_preserved=sum(r["protected"] for r in results),
        sub70_preserved=len(under70),
        selected_preserved=sum(r["selected"] for r in results),
        continuous_counterexample=counter,
        high_control=high,
    )
    assert summary["protected_preserved"] == 617 and summary["sub70_preserved"] == 11
    return summary, low


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original_view = read(LOCAL / "viewer-data.json")
    saved_analyses = read(LOCAL / "saved-analyses.json")
    rows, adapters, source_hashes = [], [], {}
    for path in [LOCAL / "viewer-data.json", LOCAL / "saved-analyses.json", REPORT / "replay.json"]:
        source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for source, saved in zip(original_view["recordings"], saved_analyses, strict=True):
        data = saved["analyses"][-1]["result"]
        assert source["id"] == saved["id"]
        original = copy.deepcopy(data)
        assert source["raw"] == data["tone_graph"]["raw"]
        assert source["filtered"] == data["tone_graph"]["filtered"]
        path = ROOT / "services/api/var/octave-ambiguity/before" / (source["id"] + ".json")
        source_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        capture = read(path)
        track = capture["track"]
        assert track["evidence_id"] == data["pitch_track_evidence_id"]
        frames = track["frames"]
        samples = [
            Sample(i, p["timestamp_seconds"], p["selected_f0_hz"]) for i, p in enumerate(frames)
        ]
        accepted = accepted_units(data)
        units = [u for u, _, _, _ in accepted]
        hop = track["frame_cadence_seconds"]
        projected = relative_pitch_fragments(samples, units, cadence_seconds=hop)
        invariant_check(samples, units, hop, projected)
        for i, (f, raw) in enumerate(zip(frames, data["tone_graph"]["raw"], strict=True)):
            assert (
                raw["source_frame_index"] == i
                and raw["timestamp_seconds"] == f["timestamp_seconds"]
            )
            assert (
                raw["selected_f0_hz"] == f["selected_f0_hz"]
                and raw["tracker_f0_hz"] == f["raw_f0_hz"]
            )
        baseline = 12 * math.log2(track["baseline_hz"])
        for unit, (timing, label, grouped, raw_unit) in zip(
            projected["units"], accepted, strict=True
        ):
            assert raw_unit["pitch_projection"]["frame_indices"] == [
                i
                for i, f in enumerate(frames)
                if timing.start <= f["timestamp_seconds"] < timing.end
            ]
            unit.update(
                label=label,
                grouped=grouped,
                eligibility=raw_unit.get("pitch_eligibility"),
                absolute_st_re_recording=[v - baseline for v in unit["absolute_semitone_range"]],
                changes_vs_whole_unit=unit["fragment_count"] > 1,
            )
            for frag in unit["fragments"]:
                frag["center_st_re_recording"] = frag["center_semitones_re_1hz"] - baseline
                frag["absolute_st_re_recording"] = [
                    v - baseline for v in frag["absolute_semitone_range"]
                ]
                frag["adjacent_steps"] = [
                    dict(
                        start=a["timestamp_seconds"],
                        end=b["timestamp_seconds"],
                        source_indices=[a["source_frame_index"], b["source_frame_index"]],
                        delta_st=b["absolute_semitones"] - a["absolute_semitones"],
                    )
                    for a, b in pairwise(frag["segments"][0])
                ]
                frag["maximum_adjacent_step_st"] = max(
                    (abs(s["delta_st"]) for s in frag["adjacent_steps"]), default=0
                )
            unit["maximum_continuous_step_st"] = max(
                (f["maximum_adjacent_step_st"] for f in unit["fragments"]), default=0
            )
        assert data == original
        cadence_deltas = [b.timestamp_seconds - a.timestamp_seconds for a, b in pairwise(samples)]
        row = dict(
            id=source["id"],
            transcript=source["transcript"],
            duration=source["duration"],
            baseline_hz=source["baseline_hz"],
            audio_sha256=source["audio_sha256"],
            track_evidence_id=track["evidence_id"],
            cadence=dict(
                expected=hop,
                minimum=min(cadence_deltas),
                maximum=max(cadence_deltas),
                median=statistics.median(cadence_deltas),
                maximum_contiguous_step=1.5 * hop,
            ),
            accepted_units=len(units),
            grouped_units=sum(g for _, _, g, _ in accepted),
            projected_count=len(flatten(projected)),
            selected_count=sum(s.selected_hz is not None for s in samples),
            fragment_count=len(projected["segments"]),
            projection=projected,
            current_domain=source["layout"]["current_domain"],
            whole_unit_domain=source["layout"]["relative_domain"],
            fragment_domain=[projected["minimum_semitones"], projected["maximum_semitones"]],
            pairwise_error=fragment_pairwise_error(projected),
            raw=source["raw"],
            filtered=source["filtered"],
        )
        rows.append(row)
        adapters.append(dict(data=data, relative=projected))
    layouts = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "benchmark/pronunciation_v2/relative_pitch_geometry.cjs")],
            input=json.dumps(adapters),
            text=True,
        )
    )
    for row, layout in zip(rows, layouts, strict=True):
        row["layout"] = layout
        row["target_independence"] = layout["target_independence"]
        row["input_unchanged"] = layout["input_unchanged"]
        assert len(flatten(row["projection"])) == sum(
            len(s) for s in layout["proposed"]["segments"]
        )
        # New centers must not change even one existing selected point's X coordinate.
        prior = next(r for r in original_view["recordings"] if r["id"] == row["id"])
        old_positions = {
            p["source_frame_index"]: p["position"]
            for seg in prior["layout"]["proposed"]["segments"]
            for p in seg
        }
        new_positions = {
            p["source_frame_index"]: p["position"]
            for seg in layout["proposed"]["segments"]
            for p in seg
        }
        assert old_positions == new_positions
        row["horizontal_positions_unchanged"] = True
        row["domain_span_change_fraction"] = (
            (row["fragment_domain"][1] - row["fragment_domain"][0])
            / (row["current_domain"][1] - row["current_domain"][0])
            - 1
            if row["projected_count"]
            else None
        )
    control_summary, low = controls()
    summary = dict(
        recordings=[
            {k: v for k, v in row.items() if k not in {"layout", "raw", "filtered"}} for row in rows
        ],
        controls=control_summary,
        input_sha256=source_hashes,
        production_integration=False,
        outcome="B",
    )
    dump(REPORT / "fragment-replay.json", summary)
    viewer = dict(
        recordings=rows,
        low_control=low,
        counterexample=control_summary["continuous_counterexample"],
    )
    dump(OUT / "viewer-data.json", viewer)
    template = (
        ROOT / "benchmark/pronunciation_v2/relative_pitch_fragments_viewer.html"
    ).read_text()
    (OUT / "viewer.html").write_text(
        template.replace(
            "__FRAGMENT_JSON__", json.dumps(viewer, ensure_ascii=False).replace("</", "<\\/")
        )
    )
    for r in rows:
        print(
            r["id"][:8],
            r["accepted_units"],
            "units",
            r["fragment_count"],
            "fragments",
            r["projected_count"],
            "points",
            r["fragment_domain"],
        )
    print(
        "Controls:",
        control_summary["protected_preserved"],
        "protected;",
        control_summary["sub70_preserved"],
        "sub70;",
        control_summary["selected_preserved"],
        "total selected",
    )


if __name__ == "__main__":
    main()
