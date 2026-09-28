"""Summarize cached whole-corpus measurements; no extraction or grading writes."""

import copy
import json
import statistics
from collections import Counter

from bakeoff import CORPUS, OUT, gap_records, quantiles, write
from benma_api.pronunciation.contours import display_contour


def main():
    rows = json.loads((OUT / "comparison.json").read_text())
    # An optional whole-recording two-stage experiment. Trigger reads only acoustic
    # gaps and existing RMS gate, never target, syllable timing or classifier label.
    routed = []
    for row in rows:
        tracks = json.loads((CORPUS / (row["utterance_id"] + ".tracks.json")).read_text())
        base = tracks["production"]
        raw = base["f0"]
        valid = {p.timestamp_seconds for seg in display_contour(raw).segments for p in seg}
        gaps = gap_records(raw, 0, base["duration_seconds"], valid)
        active = [
            g
            for g in gaps
            if g["missing_seconds"] <= 0.08
            and all(
                p["energy_rms"] >= base["energy_gate"]["threshold_rms"]
                for p in raw
                if g["first_missing_center"] <= p["timestamp_seconds"] <= g["last_missing_center"]
            )
        ]
        use_cc = len(active) >= 2
        if use_cc:
            routed.append(row["utterance_id"])
        row["fallback_cc_trigger"] = {"active_internal_gap_count": len(active), "uses_cc": use_cc}
        row["timings_ms"]["fallback_cc"] = [
            statistics.median(row["timings_ms"]["production"])
            + (statistics.median(row["timings_ms"]["cc"]) if use_cc else 0.0)
        ]
        for span in row["spans"]:
            span["methods"]["fallback_cc"] = copy.deepcopy(
                span["methods"]["cc" if use_cc else "production"]
            )
            for name, result in span["methods"].items():
                reason = result["observed"]["reason"]
                # Sufficient here means all frozen quality gates passed, including
                # certified exceptions; ambiguous_shape is quality-sufficient.
                result["metrics"]["sufficient_quality"] = span["timing_authorized"] and reason in {
                    "acoustic_shape_only",
                    "ambiguous_shape",
                    "sustained_level_after_onset",
                    "short_coherent_fall",
                    "shallow_coherent_valley",
                    "coherent_short_gap",
                    "isolated_filtered_glitch",
                }
                reference = span["methods"]["production"]["region"]
                if reference:
                    source = (
                        tracks["cc" if use_cc else "production"]
                        if name == "fallback_cc"
                        else tracks[name]
                    )
                    contour = display_contour(source["f0"])
                    times = {p.timestamp_seconds for seg in contour.segments for p in seg}
                    fixed = sorted(t for t in times if reference["start"] <= t < reference["end"])
                    metrics = result["metrics"]
                    metrics["fixed_production_region_coverage"] = min(
                        1.0, len(fixed) * 0.01 / (reference["end"] - reference["start"])
                    )
                    old_contour = display_contour(raw)
                    old_times = sorted(
                        p.timestamp_seconds
                        for seg in old_contour.segments
                        for p in seg
                        if reference["start"] <= p.timestamp_seconds < reference["end"]
                    )
                    metrics["fixed_production_core_coverage"] = (
                        min(
                            1.0,
                            sum(
                                old_times[0] - 0.00005 <= t <= old_times[-1] + 0.00005
                                for t in fixed
                            )
                            * 0.01
                            / (old_times[-1] - old_times[0] + 0.01),
                        )
                        if old_times
                        else 0.0
                    )
    write("comparison.json", rows)
    summary = json.loads((OUT / "summary.json").read_text())
    summary["fallback_cc_routed_recordings"] = routed
    changes = []
    for name in rows[0]["spans"][0]["methods"]:
        units = [s["methods"][name] for r in rows for s in r["spans"] if s["timing_authorized"]]
        metrics = [s["metrics"] for s in units]
        latency = [statistics.median(r["timings_ms"][name]) for r in rows]
        amortized = [
            statistics.median(r["timings_ms"][name]) / len(r["spans"]) for r in rows if r["spans"]
        ]
        summary["methods"][name] = {
            "sufficient_quality": sum(m["sufficient_quality"] for m in metrics),
            "classified": sum(s["observed"]["classification"] != "unclear" for s in units),
            "classification": dict(Counter(s["observed"]["classification"] for s in units)),
            "confidence": dict(Counter(s["observed"]["confidence"] for s in units)),
            "quality_reasons": dict(Counter(s["observed"]["reason"] for s in units)),
            "voiced_coverage": quantiles([m["voiced_coverage"] for m in metrics]),
            "core_coverage": quantiles([m["core_coverage"] for m in metrics]),
            "fixed_production_region_coverage": quantiles(
                [m["fixed_production_region_coverage"] for m in metrics]
            ),
            "fixed_production_core_coverage": quantiles(
                [m["fixed_production_core_coverage"] for m in metrics]
            ),
            "internal_gaps": sum(len(m["gaps"]) for m in metrics),
            "internal_missing_seconds": sum(m["internal_missing_seconds"] for m in metrics),
            "gap_duration_seconds": quantiles(
                [g["missing_seconds"] for m in metrics for g in m["gaps"]]
            ),
            "severely_fragmented": sum(m["severely_fragmented"] for m in metrics),
            "large_jumps": sum(m["large_jumps"] for m in metrics),
            "octave_like_events_10_to_14st": sum(m["octave_like_events"] for m in metrics),
            "classifier_octave_events_9_to_15st": sum(
                s["observed"]["features"].get("octave_like_jump_count", 0) for s in units
            ),
            "contaminated_spans": sum(m["contaminated_frames"] > 0 for m in metrics),
            "raw_filter_disagreement_frames_over6": sum(
                m["raw_filter_disagreement_over6"] for m in metrics
            ),
            "strong_agreement": {
                k: sum(s["agreement"][k] for s in units)
                for k in [
                    "strong_baseline_frames",
                    "alternate_missing",
                    "matched_frames",
                    "within_1st",
                    "octave_disagreements",
                ]
            },
            "recording_extraction_ms": quantiles(latency),
            "amortized_extraction_per_numeric_span_ms": quantiles(amortized),
        }
    for row in rows:
        tracks = json.loads((CORPUS / (row["utterance_id"] + ".tracks.json")).read_text())
        for span in row["spans"]:
            old = span["methods"]["production"]
            for name, new in span["methods"].items():
                keys = ["classification", "confidence", "reason"]
                if tuple(old["observed"][k] for k in keys) == tuple(
                    new["observed"][k] for k in keys
                ):
                    continue
                source = "cc" if name == "fallback_cc" else name
                before = [
                    p
                    for p in tracks["production"]["f0"]
                    if span["start_seconds"] <= p["timestamp_seconds"] < span["end_seconds"]
                ]
                after = [
                    p
                    for p in tracks[source]["f0"]
                    if span["start_seconds"] <= p["timestamp_seconds"] < span["end_seconds"]
                ]
                delta = []
                for p in before:
                    q = min(
                        after, key=lambda q: abs(q["timestamp_seconds"] - p["timestamp_seconds"])
                    )
                    tracked_keys = [
                        "tracker_f0_hz",
                        "f0_hz",
                        "voicing_probability",
                        "comparison_f0_hz",
                        "quality_usable",
                        "selection_reason",
                    ]
                    if any(p.get(k) != q.get(k) for k in tracked_keys):
                        delta.append(
                            {
                                "before": {
                                    k: p.get(k) for k in ["timestamp_seconds", *tracked_keys]
                                },
                                "after": {
                                    k: q.get(k) for k in ["timestamp_seconds", *tracked_keys]
                                },
                            }
                        )
                change = {
                    "method": name,
                    "utterance_id": row["utterance_id"],
                    "attempt_id": row["attempt_id"],
                    "target": row["target"],
                    "perceived_text": row["perceived_text"],
                    "span_index": span["index"],
                    "text": span["text"],
                    "expected": span["expected"],
                    "timing_authorized": span["timing_authorized"],
                    "old": old,
                    "new": new,
                    "changed_input_frames": delta,
                    "evidence_change": f"retained {old['metrics']['retained_frames']}→{new['metrics']['retained_frames']}; internal missing {old['metrics']['internal_missing_seconds']:.3f}→{new['metrics']['internal_missing_seconds']:.3f}s; large jumps {old['metrics']['large_jumps']}→{new['metrics']['large_jumps']}; contamination {old['metrics']['contaminated_frames']}→{new['metrics']['contaminated_frames']} frames",
                }
                changes.append(change)
    write("summary.json", summary)
    write("classification-changes.json", changes)
    lines = [
        "# Every changed downstream classification, confidence or reason",
        "",
        "All comparisons use current-code re-extraction of the same WAV as baseline. Targets are identity/context columns only. Numerical rows with rejected timing are never promoted. Frequencies and per-frame causes are in [classification-changes.json](classification-changes.json).",
        "",
    ]
    for name in summary["methods"]:
        subset = [c for c in changes if c["method"] == name]
        summary["methods"][name]["category_changes"] = sum(
            c["old"]["observed"]["classification"] != c["new"]["observed"]["classification"]
            for c in subset
        )
        summary["methods"][name]["tuple_changes"] = len(subset)
        lines.extend(
            [
                f"## {name}: {len(subset)} changed tuples",
                "",
                "| Attempt / utterance | Target; perception; span | Before category / confidence / reason | After | Evidence change |",
                "|---|---|---|---|---|",
            ]
        )
        for c in subset:
            fmt = lambda side: " / ".join(
                c[side]["observed"][k] for k in ["classification", "confidence", "reason"]
            )
            lines.append(
                f"| {c['attempt_id'] or 'free speech'} / {c['utterance_id']} | {c['target'] or 'free'}; {c['perceived_text']}; {c['span_index']}:{c['text']} | {fmt('old')} | {fmt('new')} | {c['evidence_change']} |"
            )
        lines.append("")
    write("summary.json", summary)
    (OUT / "classification-changes.md").write_text("\n".join(lines) + "\n")
    print("Fallback routed", routed)
    for n, m in summary["methods"].items():
        print(
            n,
            m["sufficient_quality"],
            m["internal_gaps"],
            m["category_changes"],
            m["tuple_changes"],
        )


if __name__ == "__main__":
    main()
