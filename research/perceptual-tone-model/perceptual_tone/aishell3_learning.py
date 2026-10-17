"""Four-tone learning contracts. Text and labels never enter primary feature inputs."""

import copy
import re
from collections import Counter

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import GEOMETRY, QUALITY

CLASSES = ("T1", "T2", "T3", "T4")
SEED = 20261017


def audio_contract(row):
    """This exact whitelist, not the research manifest, reaches the encoder."""
    o, s = row["original"], row["spans"]
    return {
        "audio_reference": o["audio"]["reference"],
        "audio_sha256": o["audio"]["sha256"],
        "read_unit": [o["start"], o["end"]],
        "pooling": [s["tone_bearing_pooling_span"][k] for k in ("start_seconds", "end_seconds")],
        "context": [s["context"][k] for k in ("start_seconds", "end_seconds")],
    }


def validate_audio_contract(value):
    if set(value) != {"audio_reference", "audio_sha256", "read_unit", "pooling", "context"}:
        raise ValueError("forbidden_encoder_input")
    a, b = value["read_unit"]
    p, q = value["pooling"]
    c, d = value["context"]
    if not 0 <= c <= a <= p < q <= b <= d:
        raise ValueError("invalid_three_span_contract")


def phonetic_base(pinyin):
    if not re.fullmatch(r"[a-zv]+[1-5]", pinyin):
        raise ValueError("require_numbered_corpus_pinyin")
    return pinyin[:-1]


def acoustic_vector(row):
    features = row["shape"].get("features", {})
    values = [row["duration"]]
    names = ["duration"]
    for key in GEOMETRY:
        names.append("shape." + key)
        values.append(features.get(key))
    for key in ("family_noise_st", "family_clarity", "family_scale_st"):
        names.append(key)
        values.append(row["observed"].get("features", {}).get(key))
    for key in QUALITY:
        names.append("quality." + key)
        values.append(row["eligibility"]["metrics"].get(key))
    for i in range(1, 5):
        names.append(f"family_support.T{i}")
        values.append(row["observed"]["fits"].get(f"TONE_{i}"))
    points = np.asarray([p["normalized_semitones"] for s in row["segments"] for p in s])
    for name, value in zip(
        ("min", "q25", "median", "q75", "max"),
        np.quantile(points, [0, 0.25, 0.5, 0.75, 1]) if len(points) else [None] * 5,
        strict=True,
    ):
        names.append("contour." + name)
        values.append(value)
    values = np.asarray([np.nan if v is None else v for v in values], dtype=float)
    if np.isinf(values).any():
        raise ValueError("infinite_feature")
    return names + ["missing." + k for k in names], np.r_[values, np.isnan(values).astype(float)]


def metric(truth, pred, probabilities=None):
    if (
        len(truth) != len(pred)
        or any(x not in CLASSES for x in truth)
        or any(x is not None and x not in CLASSES for x in pred)
    ):
        raise ValueError("invalid_metric_inputs")
    truth = np.asarray(truth)
    pred = np.asarray(pred, dtype=object)
    covered = pred != None  # noqa: E711
    y, p = truth[covered], pred[covered].astype(str)
    cm = confusion_matrix(y, p, labels=CLASSES)
    precision, recall, f1, support = precision_recall_fscore_support(
        y, p, labels=CLASSES, zero_division=0
    )
    n = len(truth)
    n3 = int((truth == "T3").sum())
    counts = Counter(truth.tolist())
    out = {
        "n": n,
        "covered": int(covered.sum()),
        "coverage": float(covered.mean()) if n else None,
        "accuracy": float((y == p).mean()) if len(y) else None,
        "balanced_accuracy": float(recall[support > 0].mean()) if len(y) else None,
        "macro_f1": float(f1.mean()) if len(y) else None,
        "correct_fraction_all": float((truth == pred).mean()) if n else None,
        "classes": list(CLASSES),
        "confusion": cm.tolist(),
        "class_counts": dict(counts),
        "per_tone": {
            c: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "covered_n": int(support[i]),
                "n": counts[c],
                "recall_all": float(((truth == c) & (pred == c)).sum() / counts[c])
                if counts[c]
                else None,
                "abstentions": int(((truth == c) & ~covered).sum()),
            }
            for i, c in enumerate(CLASSES)
        },
    }
    for target in ("T2", "T4"):
        count = int(((truth == "T3") & (pred == target)).sum())
        out["T3_to_" + target] = {"count": count, "rate_all_T3": count / n3 if n3 else None}
    if probabilities is not None:
        probs = np.asarray(probabilities)
        if (
            probs.shape != (n, 4)
            or not np.isfinite(probs).all()
            or (probs < 0).any()
            or not np.allclose(probs.sum(1), 1)
        ):
            raise ValueError("invalid_probabilities")
        if not np.array_equal(np.asarray(CLASSES)[probs.argmax(1)], pred):
            raise ValueError("prediction_probability_mismatch")
        confidence = probs.max(1)
        correct = truth == pred
        out["confidence_bins"] = []
        for lo, hi in zip(
            (0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
            (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0000001),
            strict=True,
        ):
            mask = (confidence >= lo) & (confidence < hi)
            out["confidence_bins"].append(
                {
                    "lower": lo,
                    "upper": min(hi, 1),
                    "n": int(mask.sum()),
                    "accuracy": float(correct[mask].mean()) if mask.any() else None,
                }
            )
        out["high_confidence_errors"] = int(((confidence >= 0.8) & ~correct).sum())
    return out


def pipeline(kind, C=1.0):
    model = (
        LogisticRegression(C=C, class_weight="balanced", max_iter=2000, tol=1e-6, random_state=SEED)
        if kind == "logistic"
        else MLPClassifier(
            hidden_layer_sizes=(64,), alpha=0.01, solver="lbfgs", max_iter=400, random_state=SEED
        )
    )
    return make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), model
    )


def label_mutation_check(row):
    original = audio_contract(row)
    changed = copy.deepcopy(row)
    for k in (
        "label",
        "corpus_pinyin",
        "hanzi",
        "transcript",
        "lexical_tone",
        "surface_tone",
        "expected_tone",
    ):
        changed["original"][k] = "MUTATED_FOR_LEAKAGE_TEST"
    for p in changed["original"]["aligned_phones"]:
        p["phone"] = "MUTATED_TONE_PHONE"
    if original != audio_contract(changed):
        raise ValueError("metadata_leaks_to_encoder")
    validate_audio_contract(original)
    return True
