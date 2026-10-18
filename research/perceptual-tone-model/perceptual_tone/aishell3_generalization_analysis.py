"""Descriptive analysis of sealed predictions, never a model-selection input."""

from collections import Counter

import numpy as np

from .aishell3_boundaries import features
from .aishell3_learning import CLASSES, metric


def analyze(rows, predicted, probabilities=None, prosody=None, bootstrap_replicates=2000):
    truth = np.asarray([r["original"]["label"] for r in rows])
    predicted = np.asarray(predicted, dtype=object)
    probabilities = None if probabilities is None else np.asarray(probabilities)
    speakers = np.asarray([r["original"]["speaker_id"] for r in rows])
    per_speaker = {}
    for speaker in sorted(set(speakers)):
        indices = np.flatnonzero(speakers == speaker)
        m = metric(truth[indices], predicted[indices])
        confusions = Counter(
            f"{truth[i]}->{predicted[i] or 'abstain'}" for i in indices if truth[i] != predicted[i]
        )
        per_speaker[speaker] = {
            **m,
            "speaker_id": speaker,
            "macro_f1_meaningful_all_four_present": all(t in truth[indices] for t in CLASSES),
            "t3_correct": int(((truth[indices] == "T3") & (predicted[indices] == "T3")).sum()),
            "t3_total": int((truth[indices] == "T3").sum()),
            "major_confusions": dict(confusions.most_common()),
        }
    accuracies = [s["accuracy"] for s in per_speaker.values() if s["accuracy"] is not None]
    overall = metric(truth, predicted, probabilities)
    overall["abstentions"] = len(rows) - overall["covered"]
    result = {
        "overall": overall,
        "per_speaker": per_speaker,
        "speaker_accuracy": {
            "mean": float(np.mean(accuracies)) if accuracies else None,
            "median": float(np.median(accuracies)) if accuracies else None,
            "min": min(accuracies) if accuracies else None,
            "max": max(accuracies) if accuracies else None,
        },
        "speaker_accuracy_denominator": (
            "covered examples for abstaining baseline; all examples for learned models"
        ),
    }
    contexts = {f"before_T{i}": [] for i in range(1, 6)}
    contexts.update(
        phrase_final=[], phrase_medial=[], phrase_position_unknown=[], utterance_final=[]
    )
    for i, row in enumerate(rows):
        o = row["original"]
        if o["label"] != "T3":
            continue
        if o["following"]:
            contexts["before_" + o["following"]["label"]].append(i)
        else:
            contexts["utterance_final"].append(i)
        marks = (prosody or {}).get(o["utterance_id"])
        position = (
            "phrase_final"
            if not o["following"] or (marks and marks[o["index"]] in ("%", "$"))
            else "phrase_medial"
            if marks
            else "phrase_position_unknown"
        )
        contexts[position].append(i)
    result["t3_context"] = {
        key: {
            "n": len(indices),
            "correct": sum(predicted[i] == "T3" for i in indices),
            "recall_all": sum(predicted[i] == "T3" for i in indices) / len(indices)
            if indices
            else None,
            "predictions": dict(Counter(predicted[i] or "abstain" for i in indices)),
        }
        for key, indices in contexts.items()
    }
    if probabilities is not None:
        confidence = probabilities.max(1)
        result["confidence_by_true_tone"] = {
            tone: {
                "n": int((truth == tone).sum()),
                "quantiles_0_25_50_75_100": np.quantile(
                    confidence[truth == tone], [0, 0.25, 0.5, 0.75, 1]
                ).tolist(),
            }
            for tone in CLASSES
            if (truth == tone).any()
        }
        errors = []
        for i, row in enumerate(rows):
            if truth[i] == predicted[i]:
                continue
            o = row["original"]
            span = row["spans"]["tone_bearing_pooling_span"]
            duration = span["end_seconds"] - span["start_seconds"]
            f = features(o)
            errors.append(
                {
                    "example_id": row["example_id"],
                    "speaker_id": o["speaker_id"],
                    "truth": truth[i],
                    "prediction": predicted[i],
                    "confusion": f"{truth[i]}->{predicted[i]}",
                    "corpus_pinyin": o["corpus_pinyin"],
                    "nucleus": f["nucleus"],
                    "final_class": f["final_class"],
                    "pooling_seconds": duration,
                    "short_under_60ms": duration < 0.06,
                    "confidence": float(confidence[i]),
                    "low_confidence_below_0_5": bool(confidence[i] < 0.5),
                    "high_confidence_at_least_0_8": bool(confidence[i] >= 0.8),
                }
            )
        result["errors"] = errors
        result["error_groups"] = {
            field: dict(Counter(str(e[field]) for e in errors))
            for field in (
                "confusion",
                "speaker_id",
                "corpus_pinyin",
                "nucleus",
                "final_class",
                "short_under_60ms",
                "low_confidence_below_0_5",
                "high_confidence_at_least_0_8",
            )
        }
        if bootstrap_replicates:
            # Draw speakers uniformly and retain every example of each drawn speaker.
            # Twelve held-out speakers remain the actual independent sample size.
            rng = np.random.default_rng(20261017)
            names = sorted(per_speaker)
            matrices = np.asarray([per_speaker[s]["confusion"] for s in names], dtype=float)
            draws = rng.integers(0, len(names), size=(bootstrap_replicates, len(names)))
            samples = matrices[draws].sum(axis=1)
            diagonal = np.diagonal(samples, axis1=1, axis2=2)
            actual, predicted_count = samples.sum(2), samples.sum(1)
            with np.errstate(divide="ignore", invalid="ignore"):
                f1 = np.divide(
                    2 * diagonal,
                    actual + predicted_count,
                    out=np.zeros_like(diagonal),
                    where=(actual + predicted_count) != 0,
                )
                values = {
                    "accuracy": diagonal.sum(1) / samples.sum((1, 2)),
                    "macro_f1": f1.mean(1),
                    "t3_recall": diagonal[:, 2] / actual[:, 2],
                }
            result["speaker_bootstrap"] = {
                "replicates": bootstrap_replicates,
                "seed": 20261017,
                "independent_speakers": len(names),
                "method": "speaker cluster percentile bootstrap, 95% interval",
                "intervals": {
                    k: np.quantile(v, [0.025, 0.975]).tolist() for k, v in values.items()
                },
            }
    return result
