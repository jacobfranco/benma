"""Descriptive analysis of immutable confirmatory predictions; no fitting or selection."""

import csv
import itertools
import json
from collections import Counter

import numpy as np

from .aishell3_learning import metric
from .common import file_hash, read_json, write_json
from .pooling_confirmatory import ARMS, OUT, REFERENCE, STATES, verify_manifest

HEADS = ("expanded", "pilot")
TONES = ("T1", "T2", "T3", "T4")


def describe(values):
    v = np.asarray([v for v in values if v is not None], float)
    if not len(v):
        return {"n": 0}
    return {
        "n": len(v),
        "mean": float(v.mean()),
        "median": float(np.median(v)),
        "min": float(v.min()),
        "max": float(v.max()),
        "p05": float(np.quantile(v, 0.05)),
        "p95": float(np.quantile(v, 0.95)),
    }


def csv_file(name, rows):
    with (OUT / name).open("x") as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader()
        w.writerows(
            {
                k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                for k, v in r.items()
            }
            for r in rows
        )


def compare(a, b, va, vb):
    return {
        "tv": float(np.abs(np.array(a["probabilities"]) - b["probabilities"]).sum() / 2),
        "argmax_agreement": a["prediction"] == b["prediction"],
        "embedding_cosine": float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb))),
        "embedding_l2": float(np.linalg.norm(va - vb)),
        "probability_margin_change": b["probability_margin"] - a["probability_margin"],
        "logit_margin_change": b["logit_margin"] - a["logit_margin"],
    }


def stability_summary(rows):
    return {
        "n": len(rows),
        "flips": sum(not r["argmax_agreement"] for r in rows),
        "agreement": float(np.mean([r["argmax_agreement"] for r in rows])) if rows else None,
        **{
            k: describe([r[k] for r in rows])
            for k in (
                "tv",
                "embedding_cosine",
                "embedding_l2",
                "probability_margin_change",
                "logit_margin_change",
            )
        },
    }


def paired_uncertainty(ids, a, b, meta):
    """B minus A, resampling whole held-out speakers; no inferential cutoff."""
    diff = np.array(
        [int(b[i] == meta[i]["native_label"]) - int(a[i] == meta[i]["native_label"]) for i in ids]
    )
    speakers = sorted({meta[i]["speaker"] for i in ids})
    groups = [diff[[j for j, i in enumerate(ids) if meta[i]["speaker"] == s]] for s in speakers]
    counts = np.array([len(g) for g in groups])
    sums = np.array([g.sum() for g in groups])
    rng = np.random.default_rng(20261022)
    draws = rng.integers(0, len(groups), size=(10000, len(groups)))
    bootstrap = sums[draws].sum(1) / counts[draws].sum(1)
    return {
        "n": len(ids),
        "speakers": len(speakers),
        "b_only_correct": int((diff == 1).sum()),
        "a_only_correct": int((diff == -1).sum()),
        "accuracy_delta": float(diff.mean()),
        "speaker_cluster_bootstrap_95": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
        "caution": "Descriptive percentile interval; few speakers, not an equivalence test.",
    }


def run():
    manifest = verify_manifest()
    rows = read_json(OUT / "predictions.json")["rows"]
    meta = read_json(OUT / "evaluation-metadata.json")
    reps = {(r["id"], r["arm"], r["perturbation"]): r for r in manifest["records"]}
    lookup = {(r["id"], r["arm"], r["perturbation"], r["head"]): r for r in rows}
    vectors = {
        k: np.array(r["pooled_vector"]) for k, r in reps.items() if r["pooled_vector"] is not None
    }
    plan = read_json(OUT / "preregistration.json")
    datasets = {
        d: [i["id"] for i in plan["items"] if i["dataset"] == d]
        for d in sorted({i["dataset"] for i in plan["items"]})
    }
    native_ids = datasets["native"]
    conditions = [(a, s) for a in ARMS for s in STATES] + [(REFERENCE, "BASE")]
    coverage = []
    for dataset, ids in datasets.items():
        for a, s in conditions:
            rr = [reps[i, a, s] for i in ids if (i, a, s) in reps]
            coverage.append(
                {
                    "dataset": dataset,
                    "arm": a,
                    "perturbation": s,
                    "intended": len(ids),
                    "rows": len(rr),
                    "usable": sum(r["pooled_vector"] is not None for r in rr),
                    "head_usable": sum((i, a, s, HEADS[0]) in lookup for i in ids),
                    "reasons": dict(
                        Counter(r["abstention_reason"] for r in rr if r["abstention_reason"])
                    ),
                }
            )
    native_metrics, paired_metrics, per_tone = [], [], []
    for h in HEADS:
        for a, s in conditions:
            m = metric(
                [meta[i]["native_label"] for i in native_ids],
                [lookup.get((i, a, s, h), {}).get("prediction") for i in native_ids],
            )
            native_metrics.append({"head": h, "arm": a, "perturbation": s, **m})
            per_tone.extend(
                {"head": h, "arm": a, "perturbation": s, "tone": t, **m["per_tone"][t]}
                for t in TONES
            )
        for (a, sa), (b, sb) in itertools.combinations(conditions, 2):
            ids = [i for i in native_ids if (i, a, sa, h) in lookup and (i, b, sb, h) in lookup]
            pa = {i: lookup[i, a, sa, h]["prediction"] for i in ids}
            pb = {i: lookup[i, b, sb, h]["prediction"] for i in ids}
            ma = metric([meta[i]["native_label"] for i in ids], list(pa.values()))
            mb = metric([meta[i]["native_label"] for i in ids], list(pb.values()))
            paired_metrics.append(
                {
                    "head": h,
                    "a": a,
                    "a_state": sa,
                    "b": b,
                    "b_state": sb,
                    "a_metrics": ma,
                    "b_metrics": mb,
                    "common_ids": ids,
                    "deltas_b_minus_a": {
                        k: mb[k] - ma[k] for k in ("accuracy", "balanced_accuracy", "macro_f1")
                    },
                    "recall_deltas": {
                        t: mb["per_tone"][t]["recall"] - ma["per_tone"][t]["recall"] for t in TONES
                    },
                    **paired_uncertainty(ids, pa, pb, meta),
                }
            )
    perturbations, arm_comparisons, agreements = [], [], []
    for dataset, ids in datasets.items():
        for i in ids:
            for h in HEADS:
                for a in ARMS:
                    for s in STATES[1:]:
                        base, contraction = lookup.get((i, a, "BASE", h)), lookup.get((i, a, s, h))
                        if base and contraction:
                            rr = reps[i, a, "BASE"]
                            edge = 0 if s == "CONTRACT_LEFT" else -1
                            perturbations.append(
                                {
                                    "id": i,
                                    "dataset": dataset,
                                    "tone": meta[i]["native_label"],
                                    "head": h,
                                    "arm": a,
                                    "perturbation": s,
                                    "base_correct": base["prediction"] == meta[i]["native_label"]
                                    if dataset == "native"
                                    else None,
                                    "contract_correct": contraction["prediction"]
                                    == meta[i]["native_label"]
                                    if dataset == "native"
                                    else None,
                                    "removed_weight": rr["normalized_weights"][edge],
                                    "removed_rms": rr["acoustic_audit"]["rms_20ms"][edge],
                                    "removed_high_band_fraction": rr["acoustic_audit"][
                                        "high_band_fraction"
                                    ][edge],
                                    **compare(
                                        base, contraction, vectors[i, a, "BASE"], vectors[i, a, s]
                                    ),
                                }
                            )
                for s in STATES:
                    a, b = (lookup.get((i, arm, s, h)) for arm in ARMS)
                    if a and b:
                        arm_comparisons.append(
                            {
                                "id": i,
                                "dataset": dataset,
                                "head": h,
                                "perturbation": s,
                                **compare(a, b, vectors[i, ARMS[0], s], vectors[i, ARMS[1], s]),
                            }
                        )
            for a, s in conditions:
                p, q = (lookup.get((i, a, s, h)) for h in HEADS)
                if p and q:
                    agreements.append(
                        {
                            "id": i,
                            "dataset": dataset,
                            "arm": a,
                            "perturbation": s,
                            "agree": p["prediction"] == q["prediction"],
                            "tv": float(
                                np.abs(np.array(p["probabilities"]) - q["probabilities"]).sum() / 2
                            ),
                        }
                    )
    stability, tone_stability, arm_stability_delta, head_summary, distribution, effective = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for dataset in datasets:
        for h in HEADS:
            for a in ARMS:
                for s in STATES[1:]:
                    subset = [
                        r
                        for r in perturbations
                        if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                        == (dataset, h, a, s)
                    ]
                    stability.append(
                        {
                            "dataset": dataset,
                            "head": h,
                            "arm": a,
                            "perturbation": s,
                            **stability_summary(subset),
                        }
                    )
                    if dataset == "native":
                        for t in TONES:
                            sub = [r for r in subset if r["tone"] == t]
                            tone_stability.append(
                                {
                                    "head": h,
                                    "arm": a,
                                    "perturbation": s,
                                    "tone": t,
                                    **stability_summary(sub),
                                    "recall_change": float(
                                        np.mean(
                                            [
                                                int(r["contract_correct"]) - int(r["base_correct"])
                                                for r in sub
                                            ]
                                        )
                                    )
                                    if sub
                                    else None,
                                }
                            )
            for s in STATES[1:]:
                uu = {
                    r["id"]: r
                    for r in perturbations
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                    == (dataset, h, ARMS[0], s)
                }
                aa = {
                    r["id"]: r
                    for r in perturbations
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                    == (dataset, h, ARMS[1], s)
                }
                ids = sorted(uu.keys() & aa.keys())
                arm_stability_delta.append(
                    {
                        "dataset": dataset,
                        "head": h,
                        "perturbation": s,
                        "n": len(ids),
                        "tv_acoustic_minus_uniform": describe(
                            [aa[i]["tv"] - uu[i]["tv"] for i in ids]
                        ),
                        "acoustic_lower_tv_count": sum(aa[i]["tv"] < uu[i]["tv"] for i in ids),
                        "uniform_flips": sum(not uu[i]["argmax_agreement"] for i in ids),
                        "acoustic_flips": sum(not aa[i]["argmax_agreement"] for i in ids),
                    }
                )
            for a, s in conditions:
                subset = [
                    r
                    for r in rows
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"]) == (dataset, h, a, s)
                ]
                distribution.append(
                    {
                        "dataset": dataset,
                        "head": h,
                        "arm": a,
                        "perturbation": s,
                        **{
                            k: describe([r[k] for r in subset])
                            for k in (
                                "standardized_norm",
                                "distance_to_training_mean",
                                "cosine_to_reference",
                                "l2_to_reference",
                                "standardized_distance_to_reference",
                            )
                        },
                    }
                )
        for a, s in conditions:
            subset = [
                r
                for r in agreements
                if (r["dataset"], r["arm"], r["perturbation"]) == (dataset, a, s)
            ]
            head_summary.append(
                {
                    "dataset": dataset,
                    "arm": a,
                    "perturbation": s,
                    "n": len(subset),
                    "agreement": float(np.mean([r["agree"] for r in subset])) if subset else None,
                    "disagreements": sum(not r["agree"] for r in subset),
                    "tv": describe([r["tv"] for r in subset]),
                }
            )
        for s in STATES:
            subset = [
                r
                for r in reps.values()
                if r["dataset"] == dataset
                and r["arm"] == ARMS[1]
                and r["perturbation"] == s
                and r["pooled_vector"] is not None
            ]
            effective.append(
                {
                    "dataset": dataset,
                    "perturbation": s,
                    **describe([r["effective_n"] for r in subset]),
                    "lowest_five": [
                        {k: r[k] for k in ("id", "effective_n", "frame_count", "support_ms")}
                        for r in sorted(subset, key=lambda r: r["effective_n"])[:5]
                    ],
                }
            )
    cases = []
    for i in ("take-1-3", "take-2-3", "take-3-1", "take-3-2", "google-2", "take-3-0"):
        cases.append(
            {
                "id": i,
                "display": meta[i]["display"],
                "predictions": [r for r in rows if r["id"] == i],
                "perturbations": [r for r in perturbations if r["id"] == i],
                "coverage": [
                    {
                        k: r.get(k)
                        for k in (
                            "arm",
                            "perturbation",
                            "frame_count",
                            "support_ms",
                            "effective_n",
                            "abstention_reason",
                        )
                    }
                    for r in reps.values()
                    if r["id"] == i
                ],
            }
        )
    # Compare the two edges on the same items; raw acoustics are descriptive, never gating.
    edge_comparison = []
    for dataset in datasets:
        for h in HEADS:
            for a in ARMS:
                left = {
                    r["id"]: r
                    for r in perturbations
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                    == (dataset, h, a, STATES[1])
                }
                right = {
                    r["id"]: r
                    for r in perturbations
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                    == (dataset, h, a, STATES[2])
                }
                ids = sorted(left.keys() & right.keys())
                edge_comparison.append(
                    {
                        "dataset": dataset,
                        "head": h,
                        "arm": a,
                        "n": len(ids),
                        "left_minus_right_tv": describe(
                            [left[i]["tv"] - right[i]["tv"] for i in ids]
                        ),
                        "left_more_influential_count": sum(
                            left[i]["tv"] > right[i]["tv"] for i in ids
                        ),
                        "left_removed_weight": describe([left[i]["removed_weight"] for i in ids]),
                        "right_removed_weight": describe([right[i]["removed_weight"] for i in ids]),
                    }
                )
    summary = {
        "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
        "coverage": coverage,
        "native_metrics": native_metrics,
        "paired_native_metrics": paired_metrics,
        "per_tone_metrics": per_tone,
        "stability": stability,
        "per_tone_stability": tone_stability,
        "arm_stability_delta": arm_stability_delta,
        "head_agreement": head_summary,
        "distribution": distribution,
        "effective_n": effective,
        "left_vs_right": edge_comparison,
    }
    write_json(OUT / "analysis-summary.json", summary)
    for name, data in [
        ("native-metrics", native_metrics),
        ("paired-native-metrics", paired_metrics),
        ("per-tone-metrics", per_tone),
        ("perturbation-stability", stability),
        ("per-tone-stability", tone_stability),
        ("arm-stability-delta", arm_stability_delta),
        ("expanded-pilot-comparison", head_summary),
        ("embedding-distribution", distribution),
        ("effective-n", effective),
        ("left-vs-right", edge_comparison),
        ("coverage", coverage),
    ]:
        write_json(OUT / f"{name}.json", data)
        csv_file(f"{name}.csv", data)
    write_json(OUT / "six-diagnostic-cases.json", cases)
    csv_file("perturbation-item-pairs.csv", perturbations)
    csv_file("uniform-acoustic-item-pairs.csv", arm_comparisons)
    csv_file("expanded-pilot-item-pairs.csv", agreements)
    csv_file("all-predictions.csv", rows)
    print("ANALYSIS COMPLETE", flush=True)


if __name__ == "__main__":
    run()
