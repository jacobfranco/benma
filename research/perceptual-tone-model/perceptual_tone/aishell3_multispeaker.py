"""New-speaker release gates; no model search or alteration of pilot evidence."""

from collections import Counter

from .aishell3 import speaker_split, verify_split
from .common import digest

CLASSES = ("T1", "T2", "T3", "T4")


def split_summary(rows, assignments, pilot_speakers):
    """Report coverage and fail closed on concentration or supervised speaker leakage."""
    if set(assignments) & set(pilot_speakers):
        raise ValueError("pilot_speaker_in_new_experiment")
    if any(
        r["speaker_id"] not in assignments or r["partition"] != assignments[r["speaker_id"]]
        for r in rows
    ):
        raise ValueError("row_split_mismatch")
    verify_split(rows)
    partitions = {}
    per_speaker = {}
    for speaker in sorted(assignments):
        subset = [r for r in rows if r["speaker_id"] == speaker]
        counts = Counter(r["label"] for r in subset)
        per_speaker[speaker] = {
            "partition": assignments[speaker],
            "counts": dict(counts),
            "primary": sum(counts[t] for t in CLASSES),
            "neutral": counts["T5"],
        }
    for part in ("train", "validation", "test"):
        subset = [r for r in rows if r["partition"] == part]
        counts = Counter(r["label"] for r in subset)
        if any(not counts[t] for t in CLASSES):
            raise ValueError("missing_partition_class:" + part)
        partitions[part] = {
            "speakers": sorted(s for s, p in assignments.items() if p == part),
            "class_counts": dict(counts),
            "primary": sum(counts[t] for t in CLASSES),
            "neutral": counts["T5"],
        }
    test = [r for r in rows if r["partition"] == "test" and r["label"] in CLASSES]
    n_by_speaker = Counter(r["speaker_id"] for r in test)
    t3_by_speaker = Counter(r["speaker_id"] for r in test if r["label"] == "T3")
    n3 = sum(t3_by_speaker.values())
    concentration = {
        "test_units": len(test),
        "test_speakers": len(n_by_speaker),
        "test_t3": n3,
        "test_speakers_with_t3": len(t3_by_speaker),
        "largest_test_speaker_share": max(n_by_speaker.values(), default=0) / max(1, len(test)),
        "largest_test_t3_speaker_share": max(t3_by_speaker.values(), default=0) / max(1, n3),
        "effective_test_speakers": len(test) ** 2
        / max(1, sum(n * n for n in n_by_speaker.values())),
        "test_sample_counts": dict(sorted(n_by_speaker.items())),
        "test_t3_counts": dict(sorted(t3_by_speaker.items())),
    }
    if (
        len(n_by_speaker) < 8
        or len(test) < 400
        or n3 < 80
        or len(t3_by_speaker) < 5
        or concentration["largest_test_speaker_share"] > 0.25
        or concentration["largest_test_t3_speaker_share"] > 0.30
    ):
        raise ValueError("multispeaker_coverage_or_concentration_gate_failed")
    return {
        "partitions": partitions,
        "per_speaker": per_speaker,
        "concentration": concentration,
        "pilot_speakers_disjoint": True,
    }


def make_split(rows, pilot_speakers, seed):
    assignments = speaker_split({r["speaker_id"] for r in rows}, seed)
    assigned = [{**r, "partition": assignments[r["speaker_id"]]} for r in rows]
    return assigned, {
        "seed": seed,
        "assignments": assignments,
        "policy": "speaker hash ordering, 60/20/20; no model features or outputs",
        **split_summary(assigned, assignments, pilot_speakers),
    }


def verify_packet(packet, folder, file_hash):
    if packet["packet_sha256"] != digest({k: v for k, v in packet.items() if k != "packet_sha256"}):
        raise ValueError("qa_packet_hash_changed")
    seen = set()
    for item in packet["items"]:
        key = item["row"]["example_id"]
        if key in seen or item["item_sha256"] != digest(item["row"]):
            raise ValueError("qa_item_changed_or_duplicated")
        seen.add(key)
        if item["row"]["playback"] != item["playback"]:
            raise ValueError("qa_playback_changed")
        for media in item["playback"].values():
            path = (folder / media["reference"]).resolve()
            if not path.is_relative_to(folder.resolve()) or file_hash(path) != media["sha256"]:
                raise ValueError("qa_media_changed")


def validate_adjudication(adjudication, reviews, candidate_ids):
    payload = {k: v for k, v in adjudication.items() if k != "adjudication_sha256"}
    if digest(payload) != adjudication.get("adjudication_sha256"):
        raise ValueError("adjudication_hash_changed")
    if adjudication.get("systematic_bug_found") or adjudication.get("model_predictions_inspected"):
        raise ValueError("systematic_issue_or_model_output_invalidates_gate")
    raw = {r["example_id"]: r for r in reviews}
    issues = {k for k, r in raw.items() if r["decision"] != "PASS" or r["final_decision"] != "PASS"}
    items = {i["example_id"]: i for i in adjudication["items"]}
    if set(items) != issues or len(items) != len(adjudication["items"]):
        raise ValueError("every_human_issue_requires_exactly_one_adjudication")
    quarantines = set()
    for key, item in items.items():
        if key not in candidate_ids or item["original_human_review"] != raw[key]:
            raise ValueError("adjudication_changed_human_evidence")
        if item["outcome"] not in {"PASS_AS_IS", "QUARANTINE_UNIT"}:
            raise ValueError("systematic_or_unresolved_adjudication")
        if item["outcome"] == "QUARANTINE_UNIT":
            quarantines.add(key)
        elif item.get("neighbor_phones_in_pool") != 0 or not item.get("exported_samples_exact"):
            raise ValueError("pass_requires_owned_exact_samples")
    if quarantines != set(adjudication["quarantined_example_ids"]):
        raise ValueError("adjudication_quarantine_inventory_mismatch")
    return quarantines
