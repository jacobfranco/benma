"""Descriptive analysis of sealed predictions; never constructs candidate vectors."""

import csv
import itertools
import json
from collections import Counter

import numpy as np

from .aishell3_learning import metric
from .common import PACKAGE, file_hash, read_json, write_json
from .pooling_experiment import OUT, verify_manifest
from .pooling_representation import ARMS

REFERENCE = "CURRENT_REFERENCE"
ALL = (REFERENCE, *ARMS)
HEADS = ("expanded", "pilot")
CASE_GROUPS = {
    "take-1-3": {"pre_vowel_earliest": [13, 14, 15], "all_added_early": list(range(13, 20))},
    "take-2-3": {"below_gate_earliest": [13, 14], "all_added_early": list(range(13, 19))},
    "take-3-1": {"strong_frication": list(range(13, 17)), "all_added_early": list(range(13, 18))},
    "take-3-2": {"quiet_added_tail": list(range(29, 36))},
    "google-2": {},
    "take-3-0": {},
}


def csv_file(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("x") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                for k, v in r.items()
            }
            for r in rows
        )


def describe(values):
    values = np.asarray([v for v in values if v is not None], float)
    if not len(values):
        return {"n": 0}
    return {
        "n": len(values),
        "mean": float(values.mean()),
        "min": float(values.min()),
        "median": float(np.median(values)),
        "max": float(values.max()),
        "p90": float(np.quantile(values, 0.9)),
    }


def compare(left, right):
    return {
        "tv": float(np.abs(np.array(left["probabilities"]) - right["probabilities"]).sum() / 2),
        "argmax_agreement": left["prediction"] == right["prediction"],
        "left_margin": left["probability_margin"],
        "right_margin": right["probability_margin"],
    }


def run():
    manifest = verify_manifest()
    rows = read_json(OUT / "predictions.json")["rows"]
    lookup = {(r["id"], r["arm"], r["head"]): r for r in rows}
    representations = {(r["id"], r["arm"]): r for r in manifest["records"]}
    meta = read_json(OUT / "evaluation-metadata.json")
    native_ids = read_json(OUT / "native-control-ids.json")["ids"]
    physical_ids = [i for i in meta if meta[i]["native_label"] is None]
    prior = read_json(PACKAGE / "data/generated/ownership-selector-v1/results.json")["rows"]
    physical_metadata = {
        f"{r['recording']}-{r['index']}": r for r in prior if r["candidate"] == "GAP_AWARE_AZURE"
    }
    vectors = {
        (r["id"], r["arm"]): np.load(r["vector_path"], allow_pickle=False)
        for r in manifest["records"]
        if r["vector_path"] is not None
    }
    coverage = []
    for dataset in ("physical", "native"):
        for arm in ARMS:
            rep = [r for r in manifest["records"] if r["arm"] == arm and r["dataset"] == dataset]
            usable = [r for r in rep if r["abstention_reason"] is None]
            coverage.append(
                {
                    "dataset": dataset,
                    "arm": arm,
                    "total": len(rep),
                    "usable": len(usable),
                    "abstained": len(rep) - len(usable),
                    "reasons": dict(
                        Counter(r["abstention_reason"] for r in rep if r["abstention_reason"])
                    ),
                    "head_usable": sum((r["id"], arm, HEADS[0]) in lookup for r in rep),
                    "effective_support_failures": 0,
                    "effective_support_policy": "descriptive_only_no_new_gate",
                    "usable_effective_n_below_3": sum(r["effective_n"] < 3 for r in usable),
                    "effective_n": describe([r["effective_n"] for r in usable]),
                    "support_ms": describe([r["support_ms"] for r in usable]),
                }
            )
    native = {}
    common = [i for i in native_ids if all((i, a, HEADS[0]) in lookup for a in ALL)]
    for head in HEADS:
        native[head] = {}
        for arm in ALL:
            predictions = [lookup.get((i, arm, head), {}).get("prediction") for i in native_ids]
            all_metric = metric([meta[i]["native_label"] for i in native_ids], predictions)
            common_metric = metric(
                [meta[i]["native_label"] for i in common],
                [lookup[i, arm, head]["prediction"] for i in common],
            )
            own_ids = [i for i in native_ids if (i, arm, head) in lookup]
            paired_ref = metric(
                [meta[i]["native_label"] for i in own_ids],
                [lookup[i, REFERENCE, head]["prediction"] for i in own_ids],
            )
            deltas = {}
            for key in ("accuracy", "balanced_accuracy", "macro_f1"):
                delta = all_metric[key] - paired_ref[key]
                deltas[key] = {"absolute": delta, "relative": delta / paired_ref[key]}
            native[head][arm] = {
                "all_selected": all_metric,
                "common_covered": common_metric,
                "reference_on_arm_covered": paired_ref,
                "paired_deltas_from_reference": deltas,
            }
    comparisons, agreements, physical = [], [], []
    for identifier in physical_ids:
        for arm in ARMS:
            rep = representations[identifier, arm]
            row = {
                "id": identifier,
                "case": meta[identifier]["display"],
                "arm": arm,
                "ownership": rep["ownership"],
                "representation_reason": rep["abstention_reason"],
                "head_compatible": meta[identifier]["head_compatible"],
                "frame_count": len(rep["frame_ids"]),
                "effective_n": rep["effective_n"],
                "support_ms": rep["support_ms"],
                "pitch_evidence_status_metadata_only": physical_metadata[identifier][
                    "pitch_evidence"
                ]["status"],
            }
            for head in HEADS:
                prediction = lookup.get((identifier, arm, head))
                row[head] = prediction
            row["heads_agree"] = (
                row["expanded"]["prediction"] == row["pilot"]["prediction"]
                if row["expanded"] and row["pilot"]
                else None
            )
            physical.append(row)
    for dataset, identifiers in (("physical", physical_ids), ("native", native_ids)):
        for identifier in identifiers:
            for left, right in itertools.combinations(ALL, 2):
                for head in HEADS:
                    a, b = (
                        lookup.get((identifier, left, head)),
                        lookup.get((identifier, right, head)),
                    )
                    if a and b:
                        va, vb = vectors[identifier, left], vectors[identifier, right]
                        comparisons.append(
                            {
                                "dataset": dataset,
                                "id": identifier,
                                "head": head,
                                "left": left,
                                "right": right,
                                "embedding_cosine": float(
                                    np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb))
                                ),
                                "embedding_l2": float(np.linalg.norm(va - vb)),
                                **compare(a, b),
                            }
                        )
            for arm in ALL:
                a, b = (
                    lookup.get((identifier, arm, HEADS[0])),
                    lookup.get((identifier, arm, HEADS[1])),
                )
                if a and b:
                    agreements.append(
                        {"dataset": dataset, "id": identifier, "arm": arm, **compare(a, b)}
                    )
    stability = []
    for dataset in ("physical", "native"):
        for head in HEADS:
            for left, right in itertools.combinations(ALL, 2):
                subset = [
                    r
                    for r in comparisons
                    if (r["dataset"], r["head"], r["left"], r["right"])
                    == (dataset, head, left, right)
                ]
                stability.append(
                    {
                        "dataset": dataset,
                        "head": head,
                        "left": left,
                        "right": right,
                        "n": len(subset),
                        "tv": describe([r["tv"] for r in subset]),
                        "argmax_agree": sum(r["argmax_agreement"] for r in subset),
                        "embedding_cosine": describe([r["embedding_cosine"] for r in subset]),
                        "embedding_l2": describe([r["embedding_l2"] for r in subset]),
                    }
                )
    head_summary = []
    for dataset in ("physical", "native"):
        for arm in ALL:
            subset = [r for r in agreements if r["dataset"] == dataset and r["arm"] == arm]
            head_summary.append(
                {
                    "dataset": dataset,
                    "arm": arm,
                    "n": len(subset),
                    "disagreements": sum(not r["argmax_agreement"] for r in subset),
                    "tv": describe([r["tv"] for r in subset]),
                }
            )
    distribution = []
    for dataset in ("physical", "native"):
        for head in HEADS:
            for arm in ALL:
                subset = [
                    r for r in rows if (r["dataset"], r["head"], r["arm"]) == (dataset, head, arm)
                ]
                entry = {"dataset": dataset, "head": head, "arm": arm}
                for field in (
                    "standardized_norm",
                    "distance_to_training_mean",
                    "cosine_to_reference",
                    "standardized_distance_to_reference",
                    "probability_margin",
                    "logit_margin",
                ):
                    entry[field] = describe([r[field] for r in subset])
                paired = [
                    r["standardized_norm"] - lookup[r["id"], REFERENCE, head]["standardized_norm"]
                    for r in subset
                    if (r["id"], REFERENCE, head) in lookup
                ]
                entry["paired_standardized_norm_delta"] = describe(paired)
                distribution.append(entry)
    cases = []
    for identifier, groups in CASE_GROUPS.items():
        case = {"id": identifier, "display": meta[identifier]["display"], "arms": {}}
        for arm in ALL:
            rep = representations.get((identifier, arm))
            data = {
                "representation": rep,
                "outputs": {h: lookup.get((identifier, arm, h)) for h in HEADS},
            }
            if rep and arm in ARMS:
                weights = dict(zip(rep["frame_ids"], rep["normalized_weights"], strict=True))
                data["known_region_weight_mass"] = {
                    g: sum(weights.get(i, 0) for i in ids) for g, ids in groups.items()
                }
            case["arms"][arm] = data
        cases.append(case)
    # Verify historical native vector comparability without changing any candidate.
    cache = PACKAGE / "models/generated/aishell3-multispeaker-fixed-v2"
    index = read_json(cache / "test-chinese_hubert_base-context.json")
    archive_path = cache / "test-chinese_hubert_base-context.npz"
    assert file_hash(archive_path) == index["sha256"]
    archived = np.load(archive_path, allow_pickle=False)["values"][:, 1]
    archived_map = dict(zip(index["ids"], archived, strict=True))
    errors = [
        float(
            np.max(
                np.abs(
                    np.load(representations[i, REFERENCE]["vector_path"], allow_pickle=False)
                    - archived_map[i]
                )
            )
        )
        for i in native_ids
    ]
    reference_verification = {
        "items": len(errors),
        "max_embedding_absolute_error": max(errors),
        "archive_sha256": file_hash(archive_path),
        "arithmetic": "new float64 mean versus frozen float32 Torch mean",
    }
    assert max(errors) < 1e-6
    # Physical baseline must reproduce the previous ownership experiment too.
    errors = []
    for r in prior:
        if r["candidate"] != "GAP_AWARE_AZURE":
            continue
        identifier = f"{r['recording']}-{r['index']}"
        for head in HEADS:
            current = lookup.get((identifier, ARMS[0], head))
            if current:
                old = [r["outputs"][head]["probabilities"][f"T{i}"] for i in range(1, 5)]
                errors.append(float(np.max(np.abs(np.array(current["probabilities"]) - old))))
    reference_verification["physical_uniform_probability_max_error"] = max(errors)
    assert max(errors) < 1e-6
    summary = {
        "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
        "native_common_covered_n": len(common),
        "coverage": coverage,
        "native_metrics": native,
        "stability": stability,
        "head_agreement": head_summary,
        "distribution": distribution,
        "reference_verification": reference_verification,
    }
    write_json(OUT / "analysis-summary.json", summary)
    write_json(OUT / "native-metrics.json", native)
    write_json(OUT / "six-diagnostic-cases.json", cases)
    write_json(OUT / "embedding-distribution.json", distribution)
    write_json(
        OUT / "effective-support.json",
        {
            "summaries": [r for r in coverage if r["arm"] == "ACOUSTIC_WEIGHTED"],
            "most_concentrated_ten_per_dataset_descriptive_only": {
                dataset: sorted(
                    [
                        r
                        for r in manifest["records"]
                        if r["dataset"] == dataset
                        and r["arm"] == "ACOUSTIC_WEIGHTED"
                        and r["abstention_reason"] is None
                    ],
                    key=lambda r: r["effective_n"],
                )[:10]
                for dataset in ("physical", "native")
            },
        },
    )
    csv_file(
        "case-frame-weights.csv",
        [
            {
                "id": c["id"],
                "frame_id": frame_id,
                "center": center,
                "rms_20ms": acoustic["rms_20ms"],
                "high_band_fraction": acoustic["high_band_fraction"],
                "raw_weight": raw,
                "normalized_weight": weight,
                "central_selected": frame_id
                in c["arms"]["CENTRAL_HALF"]["representation"]["frame_ids"],
            }
            for c in cases
            for frame_id, center, acoustic, raw, weight in zip(
                *[
                    c["arms"]["ACOUSTIC_WEIGHTED"]["representation"][key]
                    for key in (
                        "frame_ids",
                        "frame_centers",
                        "mapped_acoustics",
                        "raw_acoustic_weights",
                        "normalized_weights",
                    )
                ],
                strict=True,
            )
        ],
    )
    csv_file("coverage.csv", coverage)
    csv_file("physical-20-unit-comparison.csv", physical)
    csv_file("pairwise-stability.csv", comparisons)
    csv_file("expanded-pilot-comparison.csv", agreements)
    csv_file("all-predictions.csv", rows)
    csv_file(
        "native-metrics.csv",
        [{"head": h, "arm": a, **native[h][a]["all_selected"]} for h in HEADS for a in ALL],
    )
    print(
        json.dumps(
            {
                "native": {
                    h: {
                        a: {
                            k: native[h][a]["all_selected"][k]
                            for k in ("covered", "accuracy", "balanced_accuracy", "macro_f1")
                        }
                        for a in ALL
                    }
                    for h in HEADS
                },
                "coverage": coverage,
                "head_agreement": head_summary,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
