"""Append-only listener judgments. Consensus is derived, never a replacement."""

import copy
import math
from datetime import datetime

from .common import ALL_LABELS, digest, read_json


def active_judgments(judgments):
    ids, active = {}, {}
    for judgment in judgments:
        jid, annotator = judgment["judgment_id"], judgment["annotator_id"]
        if jid in ids:
            raise ValueError("Duplicate judgment_id")
        if judgment["acceptability"] not in ALL_LABELS:
            raise ValueError("Invalid acceptability label; Benma grades are not human labels")
        stamp = datetime.fromisoformat(judgment["timestamp"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("Judgment timestamp needs a timezone")
        previous = active.get(annotator)
        if previous:
            if (
                judgment["supersedes"] != previous["judgment_id"]
                or judgment["version"] != previous["version"] + 1
            ):
                raise ValueError("Revisions must explicitly supersede the current judgment")
            if stamp < datetime.fromisoformat(previous["timestamp"].replace("Z", "+00:00")):
                raise ValueError("Revision predates original judgment")
        elif judgment["supersedes"] is not None or judgment["version"] != 1:
            raise ValueError("Initial judgment must have version 1 and no supersedes")
        ids[jid] = judgment
        active[annotator] = judgment
    return list(active.values())


def aggregate(judgments, config):
    if set(config) != {
        "method",
        "min_judgments",
        "min_fraction",
        "max_entropy",
        "exclude_mixed_ungradable",
    }:
        raise ValueError("Unknown/missing aggregation config")
    if config["method"] not in ("majority", "unanimous") or config["min_judgments"] < 1:
        raise ValueError("Invalid aggregation method/minimum")
    if not 0.5 < config["min_fraction"] <= 1 or not 0 <= config["max_entropy"] <= 1:
        raise ValueError("Invalid aggregation thresholds")
    active = active_judgments(judgments)
    counts = {label: sum(a["acceptability"] == label for a in active) for label in ALL_LABELS}
    n = len(active)
    maximum = max(counts.values())
    entropy = -sum((c / n) * math.log2(c / n) for c in counts.values() if c) / 2 if n else 0
    winners = [label for label, count in counts.items() if count == maximum]
    label, reason = None, "unlabeled"
    if n:
        reason = "high_disagreement"
        fraction = maximum / n
        required = 1 if config["method"] == "unanimous" else config["min_fraction"]
        if n < config["min_judgments"]:
            reason = "insufficient_judgments"
        elif config["exclude_mixed_ungradable"] and 0 < counts["ungradable"] < n:
            reason = "mixed_ungradable"
        elif len(winners) == 1 and fraction >= required and entropy <= config["max_entropy"]:
            label, reason = winners[0], "consensus"
    return {
        "label": label,
        "reason": reason,
        "counts": counts,
        "n_judgments": n,
        "raw_judgment_count": len(judgments),
        "disagreement_count": n - maximum,
        "entropy_normalized": entropy,
        "unanimous": n > 0 and maximum == n,
        "config_hash": digest(config),
    }


def item_id(row):
    return (
        "item-"
        + digest(
            {
                "recording_audio": row["audio"]["sha256"],
                "target": {
                    k: row["target"][k]
                    for k in ("syllable", "syllable_index", "start_seconds", "end_seconds")
                },
                "utterance": row["utterance"],
            }
        )[:24]
    )


def import_annotations(rows, submissions, mapping_path, config, allow_mock=False):
    mapping = read_json(mapping_path)
    by_id = {row["example_id"]: row for row in rows}
    mapped = mapping["items"]
    result = copy.deepcopy(rows)
    targets = {row["example_id"]: row for row in result}
    # Validate the entire batch before the caller writes anything.
    for submission in submissions:
        submitted = copy.deepcopy(submission)
        packet_id = submitted.pop("item_id")
        if packet_id not in mapped:
            raise ValueError("Unknown packet item_id")
        example_id = mapped[packet_id]
        if example_id not in by_id or item_id(by_id[example_id]) != packet_id:
            raise ValueError("Packet does not match this manifest")
        if submitted.get("origin") != "human" and not (
            allow_mock and submitted.get("origin") == "mock_test"
        ):
            raise ValueError("Only independent human judgments are accepted outside Stage 0")
        if (
            submitted.get("origin") == "mock_test"
            and targets[example_id]["provenance"]["stage"] != "stage0"
        ):
            raise ValueError("Mock labels cannot enter a pilot dataset")
        existing = targets[example_id]["annotations"]
        duplicate = next(
            (j for j in existing if j["judgment_id"] == submitted["judgment_id"]), None
        )
        if duplicate:
            if duplicate != submitted:
                raise ValueError("Attempt to overwrite a raw judgment")
            continue  # Exact re-import is idempotent.
        existing.append(submitted)
        targets[example_id]["provenance"]["annotation_kind"] = submitted["origin"]
    for row in result:
        row["aggregate"] = aggregate(row["annotations"], config)
    from .manifest import validate

    validate(result)
    return result
