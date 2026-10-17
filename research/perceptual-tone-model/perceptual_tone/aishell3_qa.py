"""Automatic data integrity and hash-bound human playback decisions.

Neither plots nor successful decoding constitute a human playback review.
"""

import hashlib
import io
import math
import wave
from collections import Counter, defaultdict
from datetime import datetime
from itertools import pairwise
from pathlib import Path

import numpy as np

from .aishell3 import checked_wav, parse_content, resolve_speaker, t3_contexts, verify_split
from .common import digest, file_hash

DECISIONS = (
    "PASS",
    "BOUNDARY EARLY",
    "BOUNDARY LATE",
    "WRONG UNIT",
    "AUDIO/TRANSCRIPT MISMATCH",
    "OTHER",
)


def decode(path):
    raw = Path(path).read_bytes()
    info = checked_wav(raw)
    with wave.open(io.BytesIO(raw)) as stream:
        pcm = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
        rate = stream.getframerate()
    if len(pcm) != info["frames"] or not len(pcm):
        raise ValueError("incomplete_or_empty_decoded_audio")
    return pcm, rate, info


def distribution(values):
    if not values:
        return {}
    return dict(
        zip(
            ("min", "p1", "p5", "p25", "median", "p75", "p95", "p99", "max"),
            (float(x) for x in np.percentile(values, (0, 1, 5, 25, 50, 75, 95, 99, 100))),
            strict=True,
        )
    )


def audit_rows(rows, utterances, registry, failures):
    """Recheck provenance, PCM and every crop after strict TextGrid reconstruction."""
    by_utterance = {u["utterance_id"]: u for u in utterances}
    if len(by_utterance) != len(utterances):
        raise ValueError("duplicate_utterance")
    if len({r["example_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate_example")
    audio, transcript_files = {}, {}
    for u in utterances:
        resolve_speaker(u, u["archive_member"], registry)
        path = Path(u["audio"]["reference"])
        if file_hash(path) != u["audio"]["sha256"]:
            raise ValueError("source_audio_hash_mismatch")
        pcm, rate, info = decode(path)
        if info["pcm_sha256"] != u["pcm_sha256"]:
            raise ValueError("source_pcm_hash_mismatch")
        if u["alignment_audio"]["pcm_sha256"] != info["pcm_sha256"]:
            raise ValueError("canonical_pcm_provenance_mismatch")
        canonical_path = Path(u["alignment_audio"]["reference"])
        if file_hash(canonical_path) != u["alignment_audio"]["sha256"]:
            raise ValueError("canonical_audio_hash_mismatch")
        if decode(canonical_path)[2]["pcm_sha256"] != info["pcm_sha256"]:
            raise ValueError("canonical_pcm_changed")
        source = path.parents[3] / u["transcript_provenance"]["member"]
        if source not in transcript_files:
            if file_hash(source) != u["transcript_provenance"]["sha256"]:
                raise ValueError("source_transcript_hash_mismatch")
            transcript_files[source] = source.read_text().splitlines()
        parsed = parse_content(transcript_files[source][u["transcript_provenance"]["line"] - 1])
        if parsed["utterance_id"] != u["utterance_id"] or parsed["units"] != u["units"]:
            raise ValueError("source_read_unit_sequence_changed")
        audio[u["utterance_id"]] = (pcm, rate)
    checked, groups, clip_hash_partitions = [], defaultdict(list), defaultdict(set)
    for original in rows:
        row = {**original, "exclusion_reasons": list(original["exclusion_reasons"])}
        u = by_utterance[row["utterance_id"]]
        unit = u["units"][row["index"]]
        if any(row.get(key) != value for key, value in unit.items()):
            raise ValueError("row_labels_do_not_match_corpus")
        pcm, rate = audio[row["utterance_id"]]
        if row["start"] is not None:
            first, last = math.floor(row["start"] * rate), math.ceil(row["end"] * rate)
            if first < 0 or last > len(pcm) or last <= first:
                row["exclusion_reasons"].append("invalid_decoded_target_bounds")
            elif not np.any(pcm[first:last]):
                row["exclusion_reasons"].append("all_zero_target_pcm")
            for margin in (0, 0.25):
                a, b = (
                    max(0, math.floor((row["start"] - margin) * rate)),
                    min(len(pcm), math.ceil((row["end"] + margin) * rate)),
                )
                clip_hash_partitions[hashlib.sha256(pcm[a:b].tobytes()).hexdigest()].add(
                    row["partition"]
                )
            groups[row["utterance_id"]].append(row)
        row["reconstruction_status"] = "rejected" if row["exclusion_reasons"] else "candidate"
        checked.append(row)
    for group in groups.values():
        ordered = sorted(group, key=lambda r: r["index"])
        if any(a["end"] > b["start"] + 1e-4 for a, b in pairwise(ordered)):
            raise ValueError("overlapping_or_inverted_units")
    if any(len(parts) > 1 for parts in clip_hash_partitions.values()):
        raise ValueError("duplicate_derivative_pcm_across_partitions")
    accepted = [r for r in checked if r["reconstruction_status"] == "candidate"]
    rejected = [r for r in checked if r["reconstruction_status"] == "rejected"]
    attempted = sum(len(u["units"]) for u in utterances)
    counts = Counter(reason for r in rejected for reason in r["exclusion_reasons"])
    structural = {
        "alignment_token_sequence_mismatch",
        "orphan_or_crossing_phone",
        "alignment_outside_audio",
        "oov_read_unit",
        "required_phones_missing",
        "phone_pronunciation_mismatch",
        "incomplete_phone_ownership",
        "silence_inside_read_unit",
    }
    blockers = []
    if failures or set(counts) & structural:
        blockers.append("structural_alignment_failure")
    if len(accepted) / max(1, attempted) < 0.9:
        blockers.append("reconstruction_yield_below_90_percent")
    durations = [r["end"] - r["start"] for r in checked if r["start"] is not None]
    stats = distribution(durations)
    summary = {
        "automatic_qa": "passed" if not blockers else "failed",
        "blockers": blockers,
        "utterances_attempted": len(utterances),
        "utterances_aligned": len(utterances) - len(failures),
        "units_attempted": attempted,
        "units_accepted": len(accepted),
        "units_rejected": len(rejected),
        "failed_utterance_units": sum(f["read_units"] for f in failures),
        "rejection_reasons": dict(counts),
        "verified_speakers": sorted({r["speaker_id"] for r in accepted}),
        "per_tone": dict(Counter(r["label"] for r in accepted)),
        "per_speaker": dict(sorted(Counter(r["speaker_id"] for r in accepted).items())),
        "t3_contexts": t3_contexts(accepted),
        "duration_seconds": stats,
        "accepted_duration_seconds": distribution([r["end"] - r["start"] for r in accepted]),
        "phone_duration_seconds": distribution(
            [p["end"] - p["start"] for r in checked for p in r["aligned_phones"]]
        ),
        "duration_outliers": [
            {
                "example_id": r["example_id"],
                "seconds": r["end"] - r["start"],
                "reasons": r["exclusion_reasons"],
            }
            for r in rejected
            if r["start"] is not None
        ],
        "clips_decoded": sum(r["start"] is not None for r in checked),
        "derivative_pcm_overlap": False,
        "reconstruction_sha256": digest(rows),
        "human_playback_qa": "pending",
        "training_run": False,
    }
    return accepted, rejected, summary


def validate_reviews(items, reviews, *, complete=False):
    """Accept only explicit, identified playback decisions for immutable packet rows."""
    if not items:
        raise ValueError("empty_review_packet")
    expected = {i["row"]["example_id"]: i for i in items}
    if len(expected) != len(items):
        raise ValueError("duplicate_packet_item")
    seen, normalized = set(), []
    for review in reviews:
        key = review.get("example_id")
        if key not in expected or key in seen:
            raise ValueError("unknown_or_duplicate_review")
        seen.add(key)
        if review.get("item_sha256") != digest(expected[key]["row"]):
            raise ValueError("review_not_bound_to_current_item")
        decision = review.get("decision")
        if decision not in DECISIONS:
            raise ValueError("missing_or_invalid_decision")
        if not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip():
            raise ValueError("reviewer_required")
        try:
            timestamp = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise ValueError("valid_review_timestamp_required") from error
        if timestamp.tzinfo is None:
            raise ValueError("timezone_required")
        if review.get("heard_context_and_target") is not True:
            raise ValueError("explicit_playback_confirmation_required")
        if not isinstance(review.get("notes", ""), str):
            raise ValueError("notes_must_be_text")
        if decision != "PASS" and not review.get("notes", "").strip():
            raise ValueError("nonpass_requires_notes")
        normalized.append(
            {
                k: review[k]
                for k in (
                    "example_id",
                    "item_sha256",
                    "decision",
                    "reviewer",
                    "reviewed_at",
                    "heard_context_and_target",
                )
            }
            | {"notes": review.get("notes", "")}
        )
    missing = sorted(expected.keys() - seen)
    if complete and missing:
        raise ValueError("incomplete_packet_review")
    issues = [r for r in normalized if r["decision"] != "PASS"]
    return normalized, {
        "status": "failed" if issues else "pending" if missing else "passed",
        "reviewed": len(seen),
        "expected": len(items),
        "missing": missing,
        "issues": issues,
        "audited_by_tone": dict(
            Counter(
                (
                    expected[r["example_id"]]["row"]["label"]
                    if "label" in expected[r["example_id"]]["row"]
                    else expected[r["example_id"]]["row"]["original"]["label"]
                )
                for r in normalized
                if r["decision"] == "PASS"
            )
        ),
    }


def dataset_gate(rows):
    verify_split(rows)
    counts = {
        part: dict(Counter(r["label"] for r in rows if r["partition"] == part))
        for part in ("train", "validation", "test")
    }
    blockers = []
    if len(rows) < 500:
        blockers.append("fewer_than_500_units")
    if len({r["speaker_id"] for r in rows}) < 8:
        blockers.append("fewer_than_eight_speakers")
    for part, values in counts.items():
        if any(values.get(t, 0) < (20 if part == "test" else 10) for t in ("T1", "T2", "T3", "T4")):
            blockers.append("core_class_coverage_" + part)
    return {
        "passed": not blockers,
        "blockers": blockers,
        "per_split_tone_counts": counts,
        "speaker_split": {
            part: sorted({r["speaker_id"] for r in rows if r["partition"] == part})
            for part in counts
        },
    }
