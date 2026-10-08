"""Replay frozen evidence only; compare current, centered, and composed Mine."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess

from benchmark.pronunciation_v2.composed_relative_overflow import compose
from benchmark.pronunciation_v2.relative_pitch_report import (
    LOCAL,
    REPORT,
    ROOT,
    accepted_units,
    dump,
    read,
)
from benchmark.pronunciation_v2.robust_domain_overflow_report import measured_segments

OUT = LOCAL / "composed"


def build():
    previous_path = LOCAL / "overflow/viewer-data.json"
    previous = read(previous_path)
    for name, expected in previous["input_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    before = copy.deepcopy(previous)
    saved = read(LOCAL / "saved-analyses.json")
    rows, adapters = [], []
    for old, capture in zip(previous["recordings"], saved, strict=True):
        assert old["id"] == capture["id"]
        data = capture["analyses"][-1]["result"]
        accepted = accepted_units(data)
        assert [u.key for u, *_ in accepted] == [u["key"] for u in old["units"]]
        rebuilt = measured_segments(
            data["tone_graph"]["raw"], old["units"], old["baseline_hz"], old["cadence"]
        )
        assert rebuilt == [
            [{k: v for k, v in p.items() if k != "position"} for p in s] for s in old["segments"]
        ]
        assert old["filtered"] == data["tone_graph"]["filtered"]
        assert old["raw"] == data["tone_graph"]["raw"]
        r = {**old, **compose(old["segments"], old["units"], old["cadence"])}
        for row, (unit, *_rest) in zip(r["units"], accepted, strict=True):
            row["timing_source"] = unit.timing_source
        adapters.append(
            dict(
                data=data,
                relative=dict(
                    segments=r["segments"],
                    minimum_semitones=r["centered_domain"][0],
                    maximum_semitones=r["centered_domain"][1],
                ),
            )
        )
        r["absolute_segments"] = old["segments"]
        r["absolute_robust_burden"] = {
            k: v for k, v in old["policies"]["mad3"].items() if k not in {"paths", "units"}
        }
        rows.append(r)
    layouts = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "benchmark/pronunciation_v2/relative_pitch_geometry.cjs")],
            input=json.dumps(adapters),
            text=True,
        )
    )
    for row, layout in zip(rows, layouts, strict=True):
        assert layout["target_independence"] and layout["input_unchanged"]
        assert layout["proposed"]["segments"] == row["segments"]
        assert layout["current"] == row["layout"]["current"]
        row["layout"] = layout
    controls, synthetic = [], []
    for source, target in [(previous["controls"], controls), (previous["synthetic"], synthetic)]:
        for old in source:
            target.append({**old, **compose(old["segments"], old["units"], 0.01)})
    # The same 24-st sweep with ordinary units dominating the shared window.
    # Explicit synthetic fixture spans; no inferred production timing.
    sweep = copy.deepcopy(previous["synthetic"][2])
    ordinary = copy.deepcopy(previous["synthetic"][0])
    segments, units = copy.deepcopy(sweep["segments"]), copy.deepcopy(sweep["units"])
    for i in range(1, 61):
        unit = {**ordinary["units"][0], "key": str(i), "start_seconds": i, "end_seconds": i + 0.05}
        units.append(unit)
        segments.append(
            [
                {
                    **p,
                    "unit_key": str(i),
                    "timestamp_seconds": p["timestamp_seconds"] + i,
                    "source_frame_index": 100 * i + p["source_frame_index"],
                    "position": p["position"] + i,
                }
                for p in ordinary["segments"][0]
            ]
        )
    mixed = dict(id="24st_sweep_with_ordinary_units", **compose(segments, units, 0.01))
    assert previous == before
    return dict(
        recordings=rows,
        controls=controls,
        synthetic=synthetic,
        mixed_sweep=mixed,
        protected_preserved=previous["protected_preserved"],
        sub70_preserved=previous["sub70_preserved"],
        selected_control_preserved=previous["selected_control_preserved"],
        input_sha256={
            **previous["input_sha256"],
            str(previous_path.relative_to(ROOT)): hashlib.sha256(
                previous_path.read_bytes()
            ).hexdigest(),
        },
        production_integration=False,
        outcome="B",
        reviewed_policy="mad3.5",
        acceptance_reason=(
            "Primary gestures and high-register unit improve, but a5acd04c has overflow "
            "in four of six units, including 27.8% of coherent 苹 support and two "
            "overflow runs at the ordinary 果 crest. Stop line-graph heuristic iteration."
        ),
    )


def main():
    evidence = build()
    dump(OUT / "viewer-data.json", evidence)
    dump(
        REPORT / "composed-replay.json",
        {
            **evidence,
            "recordings": [
                {
                    k: v
                    for k, v in r.items()
                    if k not in {"layout", "raw", "filtered", "absolute_segments"}
                }
                for r in evidence["recordings"]
            ],
        },
    )
    template = (
        ROOT / "benchmark/pronunciation_v2/composed_relative_overflow_viewer.html"
    ).read_text()
    (OUT / "viewer.html").write_text(
        template.replace(
            "__COMPOSED_JSON__", json.dumps(evidence, ensure_ascii=False).replace("</", "<\\/")
        )
    )
    for r in evidence["recordings"]:
        print(r["id"][:8], "current", r["current_domain"], "centered", r["centered_domain"])
        for policy, p in r["policies"].items():
            print(
                policy,
                [round(v, 3) for v in p["domain"]],
                "outside",
                p["overflow_points"],
                "events",
                len(p["events"]),
                "ms",
                round(1000 * p["overflow_duration_seconds"], 3),
                "support%",
                round(100 * p["overflow_support_fraction"], 3),
                "units",
                p["affected_units"],
                "entirely",
                p["entirely_outside_units"],
            )


if __name__ == "__main__":
    main()
