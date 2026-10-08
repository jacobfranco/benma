"""Offline replay: unchanged selected F0, actual mobile timing/X ownership."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import statistics
import subprocess
from itertools import pairwise

from benchmark.pronunciation_v2.relative_pitch_report import (
    LOCAL,
    REPORT,
    ROOT,
    SAVED,
    accepted_units,
    dump,
    read,
)
from benchmark.pronunciation_v2.robust_domain_overflow import (
    POLICIES,
    derive_mine_display_domain,
    project_with_overflow,
)

OUT = LOCAL / "overflow"


def measured_segments(frames, units, baseline, hop):
    """Already accepted timing + unchanged selection; gaps alone break lines."""
    result = []
    for unit in units:
        current = []
        for frame in frames:
            t = frame["timestamp_seconds"]
            owners = [u for u in units if u["start_seconds"] <= t < u["end_seconds"]]
            owner = max(owners, key=lambda u: (u["start_seconds"], int(u["key"])), default=None)
            if owner is not unit or frame["selected_f0_hz"] is None:
                continue
            if current and (
                frame["source_frame_index"] != current[-1]["source_frame_index"] + 1
                or t - current[-1]["timestamp_seconds"] > 1.5 * hop
            ):
                result.append(current)
                current = []
            current.append(
                dict(
                    source_frame_index=frame["source_frame_index"],
                    timestamp_seconds=t,
                    normalized_semitones=12 * math.log2(frame["selected_f0_hz"] / baseline),
                    selected_f0_hz=frame["selected_f0_hz"],
                    unit_key=unit["key"],
                )
            )
        if current:
            result.append(current)
    return result


def compare(segments, units, hop):
    before = copy.deepcopy(segments)
    results = {}
    for policy in POLICIES:
        result = project_with_overflow(
            segments, derive_mine_display_domain(segments, policy), units, hop
        )
        result["units"] = []
        for u in units:
            local = project_with_overflow(
                [s for s in segments if s[0]["unit_key"] == u["key"]], result["domain"], units, hop
            )
            result["units"].append(
                dict(
                    key=u["key"],
                    label=u["label"],
                    **{k: v for k, v in local.items() if k not in {"domain", "paths", "crossings"}},
                )
            )
        results[policy] = result
    assert segments == before
    return results


def control(id_, hz, times=None, retained=None, protected=None):
    times = times or [i * 0.01 for i in range(len(hz))]
    hop = statistics.median(b - a for a, b in pairwise(times))
    retained = set(times if retained is None else retained)
    baseline = statistics.median(h for t, h in zip(times, hz, strict=True) if t in retained)
    frames = [
        dict(source_frame_index=i, timestamp_seconds=t, selected_f0_hz=h if t in retained else None)
        for i, (t, h) in enumerate(zip(times, hz, strict=True))
    ]
    units = [dict(key="0", label=id_, start_seconds=0, end_seconds=times[-1] + hop, grouped=False)]
    units[0]["display_position_per_second"] = 1 / units[0]["end_seconds"]
    segments = measured_segments(frames, units, baseline, hop)
    for s in segments:
        for p in s:
            p["position"] = p["timestamp_seconds"] / units[0]["end_seconds"]
    points = [p for s in segments for p in s]
    assert {p["timestamp_seconds"] for p in points} == retained
    assert set(protected or []) <= retained
    return dict(
        id=id_,
        baseline_hz=baseline,
        segments=segments,
        units=units,
        extent=1,
        selected_count=len(points),
        protected_count=len(protected or []),
        policies=compare(segments, units, hop),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    saved_path = LOCAL / "saved-analyses.json"
    hashes = {
        str(saved_path.relative_to(ROOT)): hashlib.sha256(saved_path.read_bytes()).hexdigest()
    }
    rows, adapters = [], []
    previous = read(LOCAL / "fragments/viewer-data.json")
    for saved in read(saved_path):
        data = saved["analyses"][-1]["result"]
        before = copy.deepcopy(data)
        source_path = ROOT / "services/api/var/octave-ambiguity/before" / (saved["id"] + ".json")
        hashes[str(source_path.relative_to(ROOT))] = hashlib.sha256(
            source_path.read_bytes()
        ).hexdigest()
        capture = read(source_path)
        track = capture["track"]
        assert saved["sha256"] == capture["sha256"]
        assert track["evidence_id"] == data["pitch_track_evidence_id"]
        raw = data["tone_graph"]["raw"]
        for i, (f, p) in enumerate(zip(track["frames"], raw, strict=True)):
            assert p["source_frame_index"] == i
            assert p["timestamp_seconds"] == f["timestamp_seconds"]
            assert p["selected_f0_hz"] == f["selected_f0_hz"]
            assert p["tracker_f0_hz"] == f["raw_f0_hz"]
        baseline = data["tone_graph"]["filtered"]["baseline_hz"]
        units = [
            dict(key=u.key, label=label, start_seconds=u.start, end_seconds=u.end, grouped=grouped)
            for u, label, grouped, _ in accepted_units(data)
        ]
        segments = measured_segments(raw, units, baseline, track["frame_cadence_seconds"])
        # Same transported baseline and exact selected ordinates as More Detail.
        detail = {
            p["timestamp_seconds"]: p["normalized_semitones"]
            for s in data["tone_graph"]["filtered"]["segments"]
            for p in s
        }
        assert all(
            p["normalized_semitones"] == detail[p["timestamp_seconds"]] for s in segments for p in s
        )
        values = [p["normalized_semitones"] for s in segments for p in s]
        display = dict(
            segments=segments,
            minimum_semitones=min(-3, min(values, default=0) - 1),
            maximum_semitones=max(3, max(values, default=0) + 1),
        )
        adapters.append(dict(data=data, relative=display))
        rows.append(
            dict(
                id=saved["id"],
                transcript=data.get("transcript", ""),
                baseline_hz=baseline,
                units=units,
                cadence=track["frame_cadence_seconds"],
                filtered=data["tone_graph"]["filtered"],
                raw=raw,
            )
        )
        assert before == data
    layouts = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "benchmark/pronunciation_v2/relative_pitch_geometry.cjs")],
            input=json.dumps(adapters),
            text=True,
        )
    )
    for r, layout in zip(rows, layouts, strict=True):
        r["layout"] = layout
        r["segments"] = layout["proposed"]["segments"]
        r["extent"] = layout["proposed"]["extent"]
        r["current_domain"] = layout["current_domain"]
        for unit in r["units"]:
            point = next((s[0] for s in r["segments"] if s[0]["unit_key"] == unit["key"]), None)
            if point:
                region = next(
                    region
                    for region in layout["proposed"]["evidenceRegions"]
                    if region["start"] <= point["position"] < region["end"]
                )
                unit["display_position_per_second"] = (region["end"] - region["start"] - 0.24) / (
                    unit["end_seconds"] - unit["start_seconds"]
                )
        r["policies"] = compare(r["segments"], r["units"], r["cadence"])
        prior = next(p for p in previous["recordings"] if p["id"] == r["id"])
        r["transcript"] = prior["transcript"]
        old_positions = {
            p["source_frame_index"]: p["position"]
            for s in prior["layout"]["proposed"]["segments"]
            for p in s
        }
        new_positions = {p["source_frame_index"]: p["position"] for s in r["segments"] for p in s}
        assert old_positions == new_positions
        r["x_preserved"] = True
        # Existing adapter changes target, characters, pinyin and reference tones
        # and asserts identical full pixel geometry; domain is values-only.
        assert layout["target_independence"] and layout["input_unchanged"]
    protected = {r["recording"]: r["times"] for r in read(SAVED / "low-f0-proxy-samples.json")}
    controls = []
    for id_ in [*protected, "syn_steady_70", "native_24k", "take_1", "take_2", "take_3"]:
        path = SAVED / "production" / (id_ + ".json")
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        saved = read(path)
        raw = saved["result"]["f0"]
        controls.append(
            control(
                id_,
                [p["f0_hz"] for p in raw],
                [p["timestamp_seconds"] for p in raw],
                saved["retained_times"],
                protected.get(id_),
            )
        )
    assert sum(c["protected_count"] for c in controls) == 617
    assert sum(c["selected_count"] for c in controls) == 2827
    under70 = read(
        ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json"
    )
    assert len(under70) == 11
    for p in under70:
        assert p["timestamp"] in protected[p["recording"]]
    control_burden = {}
    for policy in POLICIES:
        protected_outside, sub70_outside = 0, 0
        for c in controls:
            low, high = c["policies"][policy]["domain"]
            outside_times = {
                p["timestamp_seconds"]
                for s in c["segments"]
                for p in s
                if not low <= p["normalized_semitones"] <= high
            }
            protected_outside += len(outside_times & set(protected.get(c["id"], [])))
            sub70_outside += sum(
                p["recording"] == c["id"] and p["timestamp"] in outside_times for p in under70
            )
        control_burden[policy] = dict(
            protected_outside=protected_outside,
            sub70_outside=sub70_outside,
            outside_points=sum(c["policies"][policy]["overflow_points"] for c in controls),
            outside_support_seconds=sum(
                c["policies"][policy]["overflow_duration_seconds"] for c in controls
            ),
            total_support_seconds=sum(
                c["policies"][policy]["selected_support_seconds"] for c in controls
            ),
        )
    synthetic = [
        control("coherent_70_hz", [70 * 2 ** (s / 12) for s in [2, 1, 0, 1, 2]]),
        control("continuous_large_jump", [100, 105, 210, 220]),
        control("coherent_large_sweep", [55 * 2 ** (i / 30) for i in range(61)]),
    ]
    evidence = dict(
        recordings=rows,
        controls=controls,
        synthetic=synthetic,
        input_sha256=hashes,
        protected_preserved=617,
        sub70_preserved=11,
        selected_control_preserved=2827,
        control_burden=control_burden,
        production_integration=False,
        outcome="B",
    )
    dump(OUT / "viewer-data.json", evidence)
    dump(
        REPORT / "overflow-replay.json",
        {
            **evidence,
            "recordings": [
                {k: v for k, v in r.items() if k not in {"layout", "raw", "filtered"}} for r in rows
            ],
        },
    )
    template = (ROOT / "benchmark/pronunciation_v2/robust_domain_overflow_viewer.html").read_text()
    (OUT / "viewer.html").write_text(
        template.replace(
            "__OVERFLOW_JSON__", json.dumps(evidence, ensure_ascii=False).replace("</", "<\\/")
        )
    )
    for r in rows:
        print(r["id"][:8], "current", r["current_domain"])
        for policy, p in r["policies"].items():
            print(
                policy,
                "domain",
                [round(x, 3) for x in p["domain"]],
                "inside",
                p["inside_points"],
                "outside",
                p["overflow_points"],
                "events",
                len(p["events"]),
                "ms",
                round(1000 * p["overflow_duration_seconds"], 2),
                "support %",
                round(100 * p["overflow_support_fraction"], 2),
                "units",
                [(u["label"], u["overflow_points"]) for u in p["units"] if u["overflow_points"]],
            )


if __name__ == "__main__":
    main()
