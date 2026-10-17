"""Explicit denominators, abstentions, and uncalibrated probability diagnostics."""

import numpy as np

from .common import LABELS


def ratio(numerator, denominator):
    return {
        "numerator": int(numerator),
        "denominator": int(denominator),
        "rate": float(numerator / denominator) if denominator else None,
    }


def metrics(truth, predictions, probabilities=None, confident_incorrect=0.8, bins=10):
    if not truth or len(truth) != len(predictions):
        raise ValueError("Metrics need matching nonempty truth/predictions")
    if any(t not in LABELS for t in truth) or any(
        p not in (*LABELS, "abstain") for p in predictions
    ):
        raise ValueError("Invalid metric labels")
    y, p = np.asarray(truth), np.asarray(predictions)
    confusion = [
        [int(np.sum((y == actual) & (p == predicted))) for predicted in (*LABELS, "abstain")]
        for actual in LABELS
    ]
    per_class = {}
    for label in LABELS:
        tp = np.sum((y == label) & (p == label))
        support, predicted = np.sum(y == label), np.sum(p == label)
        precision = float(tp / predicted) if predicted else 0.0
        recall = float(tp / support) if support else None
        f1 = float(2 * tp / (support + predicted)) if support + predicted else 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(support),
            "predicted": int(predicted),
        }
    accepted, incorrect = y == "acceptable", y == "incorrect"
    red, warning = p == "incorrect", np.isin(p, ("borderline", "incorrect"))
    confident = red.copy()
    calibration = None
    if probabilities is not None:
        q = np.asarray(probabilities, dtype=float)
        if (
            q.shape != (len(y), 3)
            or not np.isfinite(q).all()
            or (q < 0).any()
            or not np.allclose(q.sum(1), 1)
        ):
            raise ValueError("Invalid probability matrix")
        confident &= q[:, 2] >= confident_incorrect
        indices = np.array([LABELS.index(t) for t in truth])
        one_hot = np.eye(3)[indices]
        confidence = q.max(axis=1)
        correct = q.argmax(axis=1) == indices
        reliability, ece = [], 0.0
        for i in range(bins):
            lower, upper = i / bins, (i + 1) / bins
            mask = (confidence >= lower) & (
                confidence <= upper if i == bins - 1 else confidence < upper
            )
            n = int(mask.sum())
            acc, conf = (
                (float(correct[mask].mean()), float(confidence[mask].mean())) if n else (None, None)
            )
            if n:
                ece += n / len(y) * abs(acc - conf)
            reliability.append(
                {
                    "lower": lower,
                    "upper": upper,
                    "count": n,
                    "accuracy": acc,
                    "mean_confidence": conf,
                }
            )
        calibration = {
            "multiclass_brier": float(np.mean(np.sum((q - one_hot) ** 2, axis=1))),
            "log_loss": float(-np.log(np.clip(q[np.arange(len(y)), indices], 1e-15, 1)).mean()),
            "ece": ece,
            "reliability_bins": reliability,
            "scope": "all consensus examples, before abstention; probabilities are uncalibrated",
        }
    recalls = [v["recall"] for v in per_class.values() if v["recall"] is not None]
    return {
        "n": len(y),
        "confusion_matrix": {
            "rows": list(LABELS),
            "columns": [*LABELS, "abstain"],
            "counts": confusion,
        },
        "per_class": per_class,
        "macro_f1": float(np.mean([v["f1"] for v in per_class.values()])),
        "balanced_accuracy": float(np.mean(recalls)),
        "warning_on_acceptable": ratio(np.sum(warning & accepted), np.sum(accepted)),
        "incorrect_on_acceptable": ratio(np.sum(red & accepted), np.sum(accepted)),
        "confident_incorrect_on_acceptable": ratio(np.sum(confident & accepted), np.sum(accepted)),
        "confident_incorrect_precision": ratio(np.sum(confident & incorrect), np.sum(confident)),
        "incorrect_recall": ratio(np.sum(red & incorrect), np.sum(incorrect)),
        "abstention": ratio(np.sum(p == "abstain"), len(y)),
        "calibration": calibration,
        "confident_incorrect_threshold": confident_incorrect if probabilities is not None else None,
        "baseline_confidence_definition": "native CLEAR_DIFFERENCE decisions"
        if probabilities is None
        else None,
    }
