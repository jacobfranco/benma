"""Generate compact review tables from final cached results only."""

import csv
import json
import statistics
from collections import Counter

from bakeoff import OUT, quantiles, write

summary = json.loads((OUT / "summary.json").read_text())
rows = json.loads((OUT / "comparison.json").read_text())
verdicts = json.loads((OUT / "learner-verdicts.json").read_text())
changes = json.loads((OUT / "classification-changes.json").read_text())
methods = list(summary["methods"])
lines = [
    "# Final corpus metrics",
    "",
    "All quality/coverage/label counts below use the 95 timing-authorized spans. Timing-rejected spans remain unclear. Gap durations count missing 10-ms frame slots; octave events here use 10–14 st, while the frozen classifier diagnostic uses 9–15 st.",
    "",
    "| Method | Sufficient quality | Classified | Severe fragmentation | Unstable reason | Internal gaps | Missing s | Median coverage | Core p10 / p50 | >6 st jumps | Octave events | Category / tuple changes |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
flat = []
for name, m in summary["methods"].items():
    subset = [c for c in changes if c["method"] == name]
    m["confidence_changes"] = sum(
        c["old"]["observed"]["confidence"] != c["new"]["observed"]["confidence"] for c in subset
    )
    m["learner_verdicts"] = dict(
        Counter(
            s["methods"][name]["verdict"]
            for r in verdicts
            for s in r["spans"]
            if s["timing_authorized"]
        )
    )
    m["single_span_recording_extraction_ms"] = quantiles(
        [statistics.median(r["timings_ms"][name]) for r in rows if len(r["spans"]) == 1]
    )
    m["single_span_recording_count"] = sum(len(r["spans"]) == 1 for r in rows)
    lines.append(
        f"| {name} | {m['sufficient_quality']} | {m['classified']} | {m['severely_fragmented']} | {m['quality_reasons'].get('tracker_instability', 0)} | {m['internal_gaps']} | {m['internal_missing_seconds']:.2f} | {m['voiced_coverage']['p50']:.3f} | {m['core_coverage']['p10']:.3f} / {m['core_coverage']['p50']:.3f} | {m['large_jumps']} | {m['octave_like_events_10_to_14st']} | {m['category_changes']} / {m['tuple_changes']} |"
    )
    flat.append(
        {
            "method": name,
            "authorized_spans": 95,
            **{
                k: m[k]
                for k in [
                    "sufficient_quality",
                    "classified",
                    "severely_fragmented",
                    "internal_gaps",
                    "internal_missing_seconds",
                    "large_jumps",
                    "octave_like_events_10_to_14st",
                    "category_changes",
                    "tuple_changes",
                    "confidence_changes",
                ]
            },
        }
    )
lines += [
    "",
    "Sufficient quality includes ambiguous_shape (adequate F0, no supported category) and all existing certified quality exceptions. Severe fragmentation means ≥2 internal gaps or >80-ms missing run; it is an analysis statistic, not a new production gate.",
    "",
    "| Method | Recording median / p95 ms | Single-span WAV median / p95 ms | Amortized per-span median / p95 ms | Confidence changes |",
    "|---|---:|---:|---:|---:|",
]
for name, m in summary["methods"].items():
    fmt = lambda key: f"{m[key]['p50']:.2f} / {m[key]['p95']:.2f}"
    lines.append(
        f"| {name} | {fmt('recording_extraction_ms')} | {fmt('single_span_recording_extraction_ms')} | {fmt('amortized_extraction_per_numeric_span_ms')} | {m['confidence_changes']} |"
    )
lines += [
    "",
    "Whole-recording times include decoding, both primary/comparison paths and acoustic post-processing, but exclude classifier time. Three rotated repetitions per Praat method; independent estimator once. Single-span WAVs are recordings with exactly one numerical span; no audio was cropped, which could change path selection. Amortized values divide each whole-recording time by its numerical span count. Fallback values are the estimated sum of already-measured primary plus CC cost, excluding trigger overhead.",
    "",
    "| Method | Region coverage p10 / p50 / p90 | Fixed production-core coverage p10 / p50 | Gap duration p50 / p95 s | Strong-frame agreements ≤1 st / matched / baseline |",
    "|---|---:|---:|---:|---:|",
]
for name, m in summary["methods"].items():
    c = m["voiced_coverage"]
    f = m["fixed_production_core_coverage"]
    g = m["gap_duration_seconds"]
    a = m["strong_agreement"]
    lines.append(
        f"| {name} | {c['p10']:.3f} / {c['p50']:.3f} / {c['p90']:.3f} | {f['p10']:.3f} / {f['p50']:.3f} | {g['p50']:.3f} / {g['p95']:.3f} | {a['within_1st']} / {a['matched_frames']} / {a['strong_baseline_frames']} |"
    )
lines += [
    "",
    "| Method | 1-like | 2-like | 3-like | 4-like | Unclear |",
    "|---|---:|---:|---:|---:|---:|",
]
for name, m in summary["methods"].items():
    c = m["classification"]
    lines.append(
        f"| {name} | {c.get('1-like', 0)} | {c.get('2-like', 0)} | {c.get('3-like', 0)} | {c.get('4-like', 0)} | {c.get('unclear', 0)} |"
    )
lines += [
    "",
    "| Method | Contaminated spans | Raw/high-pass disagreements >6 st (frames) | Learner verdicts |",
    "|---|---:|---:|---|",
]
for name, m in summary["methods"].items():
    lines.append(
        f"| {name} | {m['contaminated_spans']} | {m['raw_filter_disagreement_frames_over6']} | {m['learner_verdicts']} |"
    )
(OUT / "metrics.md").write_text("\n".join(lines) + "\n")
with (OUT / "metrics.csv").open("w") as f:
    writer = csv.DictWriter(f, fieldnames=list(flat[0]))
    writer.writeheader()
    writer.writerows(flat)
write("summary.json", summary)
prefixes = {
    "c728c5e3": "Accepted Tone 1",
    "12df6d8f": "Accepted Tone 2",
    "fcac1921": "Accepted Tone 3",
    "49b10b69": "Accepted Tone 4",
    "70411287": "Neutral target",
    "618b19d5": "Low/subharmonic",
    "4fbf587d": "Octave instability",
    "9957925d": "Fragmented control",
    "701bdfcb": "Certified short-gap Tone 4",
    "f047a3c9": "Shallow Tone 3",
    "b1970ccc": "Accepted Tone 1 regression",
    "3d10e9d3": "Fresh 妈",
    "3e2ef0b3": "Fresh 马",
    "3f5ffcc7": "Fresh 骂",
    "d92b8685": "Fresh 天",
}
controls = []
lines = [
    "# Protected control audit",
    "",
    "Each cell is category / confidence / reason. Neutral target retains contextual learner semantics regardless of observed category. Accepted means previously accepted evidence, not independently labeled phonetic ground truth.",
    "",
    "| Control / utterance / attempt | Production | Balanced DP | Strong continuity DP | CC | Independent NAC | Bounded CC fallback |",
    "|---|---|---|---|---|---|---|",
]
for prefix, label in prefixes.items():
    row = next(r for r in rows if r["utterance_id"].startswith(prefix))
    s = row["spans"][0]
    controls.append({"control": label, **row})
    cells = [
        " / ".join(
            s["methods"][m]["observed"][k] for k in ["classification", "confidence", "reason"]
        )
        for m in methods
    ]
    lines.append(
        "| "
        + f"{label}<br>{row['utterance_id']}<br>{row['attempt_id'] or 'free speech'}"
        + " | "
        + " | ".join(cells)
        + " |"
    )
(OUT / "controls.md").write_text("\n".join(lines) + "\n")
# Smaller human-readable count of changes; no correctness assigned by intended target.
audit = {}
for name in methods:
    subset = [c for c in changes if c["method"] == name]
    audit[name] = dict(
        Counter(
            "unclear_to_category_requires_review"
            if c["old"]["observed"]["classification"] == "unclear"
            and c["new"]["observed"]["classification"] != "unclear"
            else "accepted_to_unclear_regression"
            if c["old"]["observed"]["classification"] != "unclear"
            and c["new"]["observed"]["classification"] == "unclear"
            else "category_switch_requires_review"
            if c["old"]["observed"]["classification"] != c["new"]["observed"]["classification"]
            else "confidence_or_reason_only"
            for c in subset
        )
    )
write("change-audit-summary.json", audit)
print(json.dumps(audit, indent=2))
