"""Native-tone contracts, speaker/source isolation, and abstention-aware metrics."""

import re
from collections import defaultdict

import numpy as np
from sklearn.metrics import confusion_matrix, f1_score

from .common import digest
from .native_labels import CLASSES


def speaker_partition(speakers, seed):
    ordered = sorted(set(speakers), key=lambda s: digest([seed, s]))
    if len(ordered) < 6:
        raise ValueError("Need at least six speaker groups for three partitions")
    held = max(1, round(len(ordered) * 0.2))
    return {
        s: "test" if i < held else "validation" if i < 2 * held else "train"
        for i, s in enumerate(ordered)
    }


def validate_split(rows):
    owners = {k: {} for k in ("speaker_id", "utterance_id", "pcm_sha256", "prompt_id")}
    examples = set()
    transcripts = {}
    for row in rows:
        if row["partition"] not in ("train", "validation", "test"):
            raise ValueError("Unassigned partition")
        if row["example_id"] in examples:
            raise ValueError("Duplicate example")
        examples.add(row["example_id"])
        for field, seen in owners.items():
            value = row[field]
            if not value:
                raise ValueError("Missing source/speaker identity")
            if value in seen and seen[value] != row["partition"]:
                raise ValueError(f"Cross-partition leakage: {field}")
            seen[value] = row["partition"]
        if row.get("transcript"):
            text_key = digest(re.sub(r"\W", "", row["transcript"]))
            if text_key in transcripts and transcripts[text_key] != row["partition"]:
                raise ValueError("Cross-partition leakage: duplicate transcript")
            transcripts[text_key] = row["partition"]
    # All windows of one decoded source share one partition. Crops cannot cross it.
    return {p: sum(r["partition"] == p for r in rows) for p in ("train", "validation", "test")}


def model_input(value):
    """Reject extra keys: callers cannot accidentally concatenate manifest fields.

    The optional phonetic base is admitted only after a train-only ambiguity
    filter; corpus context, lexical labels, and IDs are never numeric features.
    """
    if set(value) not in ({"embedding"}, {"embedding", "phonetic_base"}):
        raise ValueError("Forbidden model-input field")
    x = np.asarray(value["embedding"], dtype=np.float32)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all():
        raise ValueError("Invalid speech vector")
    if "phonetic_base" in value and not re.fullmatch(r"[a-zv]+", value["phonetic_base"]):
        raise ValueError("Phonetic input must be tone-free ASCII pinyin")
    return x


def ambiguous_bases(train_rows, minimum_per_tone=5):
    counts = defaultdict(lambda: defaultdict(int))
    for row in train_rows:
        if row["partition"] != "train":
            raise ValueError("Identity vocabulary may use training data only")
        if row["label"] in CLASSES:
            counts[row["phonetic_base"]][row["label"]] += 1
    return sorted(
        base
        for base, tones in counts.items()
        if sum(n >= minimum_per_tone for n in tones.values()) >= 2
    )


def metrics(truth, predictions, probabilities=None):
    if len(truth) != len(predictions) or any(t not in CLASSES for t in truth):
        raise ValueError("Invalid truth/prediction arrays")
    if any(p is not None and p not in CLASSES for p in predictions):
        raise ValueError("Invalid predicted class; use None for abstention")
    covered = [i for i, p in enumerate(predictions) if p is not None]
    y = [truth[i] for i in covered]
    p = [predictions[i] for i in covered]
    matrix = confusion_matrix(y, p, labels=list(CLASSES)) if covered else np.zeros((5, 5), int)
    recall = {
        c: (
            sum(a == b == c for a, b in zip(truth, predictions, strict=True)) / truth.count(c)
            if truth.count(c)
            else None
        )
        for c in CLASSES
    }
    result = {
        "classes": CLASSES,
        "n": len(truth),
        "covered": len(covered),
        "coverage": len(covered) / len(truth) if truth else None,
        "accuracy_covered": float(np.mean(np.array(y) == np.array(p))) if covered else None,
        "macro_f1_covered": float(
            f1_score(y, p, labels=list(CLASSES), average="macro", zero_division=0)
        )
        if covered
        else None,
        "correct_fraction_all": sum(a == b for a, b in zip(truth, predictions, strict=True))
        / len(truth)
        if truth
        else None,
        "recall_all_with_abstentions": recall,
        "recall_covered": {
            c: (matrix[i, i] / int(matrix[i].sum()) if matrix[i].sum() else None)
            for i, c in enumerate(CLASSES)
        },
        "confusion_covered_rows_truth_columns_prediction": matrix.tolist(),
        "abstentions_by_tone": {
            c: sum(a == c and b is None for a, b in zip(truth, predictions, strict=True))
            for c in CLASSES
        },
    }
    for a, b in (("T3", "T4"), ("T3", "T2"), ("T4", "T3")):
        result[f"{a}_to_{b}_all"] = (
            sum(t == a and p == b for t, p in zip(truth, predictions, strict=True)) / truth.count(a)
            if truth.count(a)
            else None
        )
    if probabilities is not None:
        q = np.asarray(probabilities, dtype=float)
        if (
            q.shape != (len(truth), 5)
            or not np.isfinite(q).all()
            or (q < 0).any()
            or not np.allclose(q.sum(1), 1)
        ):
            raise ValueError("Invalid ordered class probabilities")
        if any(p is None for p in predictions):
            raise ValueError("Calibration requires a probability vector for every prediction")
        if any(CLASSES[i] != p for i, p in zip(q.argmax(1), predictions, strict=True)):
            raise ValueError("Probabilities and predicted classes disagree")
        bins = []
        confidence = q.max(1)
        correct = np.array(truth) == np.array(predictions)
        for k in range(10):
            selected = (confidence >= k / 10) & (
                (confidence < (k + 1) / 10) if k < 9 else (confidence <= 1)
            )
            bins.append(
                {
                    "lower": k / 10,
                    "n": int(selected.sum()),
                    "accuracy": float(correct[selected].mean()) if selected.any() else None,
                    "confidence": float(confidence[selected].mean()) if selected.any() else None,
                }
            )
        result["reliability_bins"] = bins
    return result


def baseline_prediction(deterministic):
    """Observed family only. Never expected tone, winner from grading, or color."""
    if not deterministic or deterministic.get("family_decision") != "NUMBERED":
        return None
    family = deterministic.get("observed_family")
    return {f"TONE_{i}": f"T{i}" for i in range(1, 5)}.get(family)


def training_blockers(preflight, rows, reviews):
    """Data-QA gates, never a performance pass/fail threshold.

    Returning an empty list does not establish perceptual gold labels; those
    remain weak even after a developer has checked the automatic pipeline.
    """
    validate_split(rows)
    blockers = [name for name, done in preflight["gates"].items() if done is not True]
    if len(rows) < preflight["config"]["phase_a_target_syllables"][0]:
        blockers.append("below_requested_phase_a_scale")
    for partition in ("train", "validation", "test"):
        present = {r["label"] for r in rows if r["partition"] == partition}
        if present != set(CLASSES):
            blockers.append(f"missing_classes_in_{partition}")
    by_id = {r["example_id"]: r for r in rows}
    seen = set()
    audited_classes = set()
    checks = (
        "transcript_matches_audio",
        "correct_syllable_boundary",
        "linguistic_label_plausible",
        "sandhi_neutral_checked",
    )
    for review in reviews:
        identifier = review["example_id"]
        if identifier in seen or identifier not in by_id:
            raise ValueError("Duplicate or unknown QA item")
        seen.add(identifier)
        row = by_id[identifier]
        if row["partition"] != "train":
            raise ValueError("Development QA must not inspect held-out audio")
        if all(review.get(k) is True for k in checks):
            audited_classes.add(row["label"])
    if audited_classes != set(CLASSES):
        blockers.append("developer_audio_qa_missing_classes")
    return blockers
