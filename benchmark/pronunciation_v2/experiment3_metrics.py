"""Pure paired reporting; no audio, model access, selection, or fitting."""

from fractions import Fraction

import numpy as np

VERSION = "experiment3-evaluation-v1"
TONES = (1, 2, 3, 4)
POOLED = ("accuracy", "balanced_accuracy", "macro_f1")
BOOT_METRICS = (*POOLED, "equal_speaker_mean_balanced_accuracy")
BOOTSTRAP = {
    "draws": 10000,
    "seed": 20261002,
    "rng": "numpy.random.default_rng",
    "unit": "speaker; all clips; with replacement; paired A/B",
    "speaker_order": "sorted speaker_id",
    "percentiles": [2.5, 97.5],
    "method": "linear",
    "difference": "B - A",
    "metrics": list(BOOT_METRICS),
}
UNCERTAINTY = (
    "Speaker-bootstrap descriptive uncertainty from only 18 speakers, not population "
    "guarantees. Intervals including zero are suggestive, not demonstrated superiority. "
    "Bootstrap results do not alter the preregistered decision."
)
IDENTITY = {
    "source_asset_id": "source_asset_id",
    "speaker_id": "speaker_id",
    "source_declared_speaker_status": "speaker_native_status",
    "character": "text",
    "pinyin": "pinyin",
    "true_lexical_tone": "tone",
}
COLUMNS = (
    list(IDENTITY)
    + [
        key
        for arm in ("A", "B")
        for key in [f"{arm}_prediction", *(f"{arm}_T{t}_probability" for t in TONES)]
    ]
    + ["A_correct", "B_correct"]
)
METRIC_DEFINITIONS = {
    "confusion_matrix": "4x4 integer counts; true rows, predicted columns; T1,T2,T3,T4",
    "correct_count": "trace(confusion_matrix)",
    "accuracy": "correct_count / support",
    "precision": "TP / predicted-tone count; zero when denominator is zero",
    "recall": "TP / true-tone support; null when support is zero",
    "f1": "2*TP / (true-tone support + predicted-tone count); zero if denominator zero",
    "balanced_accuracy": "unweighted mean of all four recalls; null if any tone absent",
    "macro_f1": "unweighted mean of all four tone F1 scores, including zeros",
    "equal_speaker_mean_balanced_accuracy": "unweighted mean of individual speaker BA",
    "directed_confusions": "T2->T3,T3->T2,T3->T4,T4->T3; count / true-tone support",
    "difference": "B minus A; no rounding before differences or decisions",
    "decision_arithmetic": "exact rational counts, no floating-point tolerance",
}
DECISION = {
    "primary": "all 18 speakers and all 720 sealed rows; no exclusions",
    "pooled_non_regression": list(POOLED),
    "strict_improvement": "at least one of accuracy, balanced_accuracy, macro_f1",
    "equal_speaker_mean_ba_non_regression": True,
    "maximum_tone_drop": "1/20 (0.05 absolute), inclusive, for precision/recall/F1",
    "maximum_speaker_ba_drop": "1/10 (0.10 absolute), inclusive",
    "subgroups": "SECONDARY_DESCRIPTIVE only; source-declared NATIVE and LEARNER",
    "bootstrap_affects_decision": False,
}


def confusion(truth, prediction):
    truth, prediction = np.asarray(truth), np.asarray(prediction)
    if (
        truth.ndim != 1
        or prediction.shape != truth.shape
        or not len(truth)
        or truth.dtype.kind not in "iu"
        or prediction.dtype.kind not in "iu"
        or not np.isin(truth, TONES).all()
        or not np.isin(prediction, TONES).all()
    ):
        raise ValueError("Aligned nonempty integer T1-T4 labels required")
    return np.bincount((truth - 1) * 4 + prediction - 1, minlength=16).reshape(4, 4)


def exact_metrics(matrix):
    cm = np.asarray(matrix)
    if cm.shape != (4, 4) or cm.dtype.kind not in "iu" or (cm < 0).any() or not cm.sum():
        raise ValueError("Nonempty 4x4 nonnegative integer confusion matrix required")
    support = [int(x) for x in cm.sum(1)]
    predicted = [int(x) for x in cm.sum(0)]
    correct = int(np.trace(cm))
    tone = {}
    for i in range(4):
        tp = int(cm[i, i])
        tone[str(i + 1)] = {
            "precision": Fraction(tp, predicted[i]) if predicted[i] else Fraction(0),
            "recall": Fraction(tp, support[i]) if support[i] else None,
            "f1": Fraction(2 * tp, support[i] + predicted[i])
            if support[i] + predicted[i]
            else Fraction(0),
            "support": support[i],
        }
    directed = {}
    for a, b in ((2, 3), (3, 2), (3, 4), (4, 3)):
        count, denominator = int(cm[a - 1, b - 1]), support[a - 1]
        directed[f"T{a}->T{b}"] = {
            "count": count,
            "denominator": denominator,
            "rate": Fraction(count, denominator) if denominator else None,
        }
    return {
        "correct_count": correct,
        "support": sum(support),
        "accuracy": Fraction(correct, sum(support)),
        "balanced_accuracy": sum(t["recall"] for t in tone.values()) / 4 if all(support) else None,
        "macro_f1": sum(t["f1"] for t in tone.values()) / 4,
        "per_tone": tone,
        "confusion_matrix": cm.tolist(),
        "directed_confusions": directed,
    }


def numeric(value):
    if isinstance(value, Fraction):
        return float(value)
    if isinstance(value, dict):
        return {k: numeric(v) for k, v in value.items()}
    if isinstance(value, list):
        return [numeric(v) for v in value]
    return value


def difference(a, b):
    result = {k: b[k] - a[k] if a[k] is not None and b[k] is not None else None for k in POOLED}
    result["per_tone"] = {
        t: {
            k: b["per_tone"][t][k] - a["per_tone"][t][k]
            if a["per_tone"][t][k] is not None and b["per_tone"][t][k] is not None
            else None
            for k in ("precision", "recall", "f1")
        }
        for t in map(str, TONES)
    }
    return result


def decision(a, b, speakers):
    """Inputs are exact count-derived Fractions; equality at both limits is allowed."""
    checks = []

    def add(condition, passed, details):
        checks.append({"condition": condition, "passed": bool(passed), "details": details})

    for k in POOLED:
        add(f"pooled_{k}_non_regression", b[k] >= a[k], {"difference": b[k] - a[k]})
    add("strict_pooled_improvement", any(b[k] > a[k] for k in POOLED), {})
    k = "equal_speaker_mean_balanced_accuracy"
    add("equal_speaker_mean_ba_non_regression", b[k] >= a[k], {"difference": b[k] - a[k]})
    for k in ("precision", "recall", "f1"):
        drops = {t: a["per_tone"][t][k] - b["per_tone"][t][k] for t in map(str, TONES)}
        failed = {t: d for t, d in drops.items() if d > Fraction(1, 20)}
        add(f"tone_{k}_drop_at_most_0.05", not failed, {"violations": failed})
    drops = {
        s: v["A"]["balanced_accuracy"] - v["B"]["balanced_accuracy"] for s, v in speakers.items()
    }
    failed = {s: d for s, d in drops.items() if d > Fraction(1, 10)}
    add("speaker_ba_drop_at_most_0.10", not failed, {"violations": failed})
    return {
        "promising": all(c["passed"] for c in checks),
        "checks": checks,
        "failed_conditions": [c["condition"] for c in checks if not c["passed"]],
        "interpretation": "Apply all nine conditions to the full panel; inspect complete metric "
        "differences for mixed, unchanged or worse behavior. Failure alone does not mean worse.",
    }


def prediction_records(rows, asset_ids, probability_a, probability_b):
    expected = [r["source_asset_id"] for r in rows]
    if list(asset_ids) != expected or len(set(expected)) != len(expected) or not rows:
        raise ValueError("Prediction identity/order/coverage differs from manifest")
    probabilities = [np.asarray(p) for p in (probability_a, probability_b)]
    for p in probabilities:
        if (
            p.shape != (len(rows), 4)
            or not np.isfinite(p).all()
            or (p < 0).any()
            or (p > 1).any()
            or not np.allclose(p.sum(1), 1, atol=1e-6, rtol=0)
        ):
            raise ValueError("Invalid probabilities")
    records = []
    for i, row in enumerate(rows):
        record = {k: row[v] for k, v in IDENTITY.items()}
        record["true_lexical_tone"] = int(row["tone"])
        for arm, p in zip(("A", "B"), probabilities, strict=True):
            prediction = int(np.argmax(p[i])) + 1  # Lowest numbered tone wins exact ties.
            record[f"{arm}_prediction"] = prediction
            record.update({f"{arm}_T{t}_probability": float(p[i, t - 1]) for t in TONES})
            record[f"{arm}_correct"] = int(prediction == int(row["tone"]))
        records.append(record)
    validate_records(rows, records)
    return records


def validate_records(rows, records):
    if len(rows) != len(records) or len({r["source_asset_id"] for r in records}) != len(rows):
        raise ValueError("Prediction row coverage/uniqueness differs")
    for row, record in zip(rows, records, strict=True):
        if set(record) != set(COLUMNS) or any(
            str(record[k]) != str(row[v]) for k, v in IDENTITY.items()
        ):
            raise ValueError("Prediction row identity/order/metadata differs")
        if int(record["true_lexical_tone"]) not in TONES:
            raise ValueError("Invalid true tone")
        for arm in ("A", "B"):
            p = np.array([float(record[f"{arm}_T{t}_probability"]) for t in TONES])
            if (
                not np.isfinite(p).all()
                or (p < 0).any()
                or (p > 1).any()
                or not np.isclose(p.sum(), 1, atol=1e-6, rtol=0)
                or str(record[f"{arm}_prediction"]) != str(int(p.argmax()) + 1)
                or str(record[f"{arm}_correct"])
                != str(int(int(record[f"{arm}_prediction"]) == int(row["tone"])))
            ):
                raise ValueError("Prediction/probability/correctness inconsistency")


def pair_summary(records):
    truth = [int(r["true_lexical_tone"]) for r in records]
    arms = {
        arm: exact_metrics(confusion(truth, [int(r[f"{arm}_prediction"]) for r in records]))
        for arm in ("A", "B")
    }
    categories = dict.fromkeys(
        ("both_correct", "A_only_correct", "B_only_correct", "both_wrong"), 0
    )
    for r in records:
        a = int(r["A_prediction"]) == int(r["true_lexical_tone"])
        b = int(r["B_prediction"]) == int(r["true_lexical_tone"])
        categories[
            ("both_wrong", "B_only_correct", "A_only_correct", "both_correct")[2 * a + b]
        ] += 1
    return {
        **arms,
        "paired_correctness": categories,
        "difference_B_minus_A": difference(arms["A"], arms["B"]),
    }


def report(rows, records):
    validate_records(rows, records)
    speakers = {}
    for s in sorted({r["speaker_id"] for r in records}):
        group = [r for r in records if r["speaker_id"] == s]
        statuses = {r["source_declared_speaker_status"] for r in group}
        if len(statuses) != 1:
            raise ValueError("Inconsistent source-declared speaker status")
        speakers[s] = {"source_declared_speaker_status": statuses.pop(), **pair_summary(group)}
    primary = pair_summary(records)
    for arm in ("A", "B"):
        bas = [s[arm]["balanced_accuracy"] for s in speakers.values()]
        if None in bas:
            raise ValueError("Primary speakers must have all four true tones")
        primary[arm]["equal_speaker_mean_balanced_accuracy"] = sum(bas) / len(bas)
    primary["difference_B_minus_A"]["equal_speaker_mean_balanced_accuracy"] = (
        primary["B"]["equal_speaker_mean_balanced_accuracy"]
        - primary["A"]["equal_speaker_mean_balanced_accuracy"]
    )
    subgroups = {}
    for status in sorted({r["source_declared_speaker_status"] for r in records}):
        group = [r for r in records if r["source_declared_speaker_status"] == status]
        subgroups[status] = {
            "role": "SECONDARY_DESCRIPTIVE",
            "speaker_count": len({r["speaker_id"] for r in group}),
            **pair_summary(group),
        }
    return numeric(
        {
            "schema_version": VERSION,
            "panel": {
                "role": "PRIMARY_ALL_SEALED_ROWS",
                "rows": len(records),
                "speakers": len(speakers),
            },
            "primary": primary,
            "per_speaker": speakers,
            "source_declared_status_subgroups": subgroups,
            "decision": decision(primary["A"], primary["B"], speakers),
        }
    )


def bootstrap(rows, records, *, draws=10000, seed=20261002):
    """Sum sampled speaker confusion matrices: exactly equivalent to copying every clip."""
    validate_records(rows, records)
    speakers = sorted({r["speaker_id"] for r in records})
    matrices = []
    for s in speakers:
        group = [r for r in records if r["speaker_id"] == s]
        matrices.append(
            [
                confusion(
                    [int(r["true_lexical_tone"]) for r in group],
                    [int(r[f"{arm}_prediction"]) for r in group],
                )
                for arm in ("A", "B")
            ]
        )
    matrices = np.asarray(matrices)
    if not (matrices.sum(-1) > 0).all():
        raise ValueError("Speaker bootstrap requires all four tones per speaker")
    sampled = np.random.default_rng(seed).integers(0, len(speakers), size=(draws, len(speakers)))
    cm = matrices[sampled].sum(1)
    tp = np.diagonal(cm, axis1=-2, axis2=-1)
    support, predicted = cm.sum(-1), cm.sum(-2)
    f1 = np.divide(
        2 * tp,
        support + predicted,
        out=np.zeros_like(tp, dtype=float),
        where=(support + predicted) > 0,
    )
    individual_ba = (np.diagonal(matrices, axis1=-2, axis2=-1) / matrices.sum(-1)).mean(-1)
    values = {
        "accuracy": tp.sum(-1) / cm.sum((-1, -2)),
        "balanced_accuracy": (tp / support).mean(-1),
        "macro_f1": f1.mean(-1),
        "equal_speaker_mean_balanced_accuracy": individual_ba[sampled].mean(1),
    }
    differences = {k: v[:, 1] - v[:, 0] for k, v in values.items()}
    return {
        "schema_version": VERSION,
        "configuration": {**BOOTSTRAP, "draws": draws, "seed": seed},
        "speaker_order": speakers,
        "sampled_speaker_indices": sampled.tolist(),
        "differences": {k: v.tolist() for k, v in differences.items()},
        "intervals_95_percent": {
            k: np.percentile(v, [2.5, 97.5], method="linear").tolist()
            for k, v in differences.items()
        },
        "interpretation": UNCERTAINTY,
    }
