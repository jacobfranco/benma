"""Speaker partitions and fail-closed identity/audio leakage checks."""

import copy
import hashlib
import math

from .audio import read_audio
from .common import PARTITIONS, digest
from .manifest import validate


def split_speakers(rows, config):
    if set(config) != {"seed", "fractions", "version"}:
        raise ValueError("Unknown/missing split config")
    fractions = config["fractions"]
    if (
        len(fractions) != 3
        or not all(0 < f < 1 for f in fractions)
        or not math.isclose(sum(fractions), 1)
    ):
        raise ValueError("Split fractions must be three positive fractions summing to one")
    if any(not r["speaker_id"] for r in rows):
        raise ValueError("Resolve every speaker identity before splitting")
    speakers = sorted({r["speaker_id"] for r in rows}, key=lambda s: digest([config["seed"], s]))
    if len(speakers) < 3:
        raise ValueError("At least three speakers are required")
    sizes = [int(len(speakers) * f) for f in fractions]
    for i in sorted(range(3), key=lambda i: (-(len(speakers) * fractions[i] % 1), i))[
        : len(speakers) - sum(sizes)
    ]:
        sizes[i] += 1
    for i in range(3):
        if sizes[i] == 0:
            donor = max(range(3), key=lambda j: sizes[j])
            sizes[donor] -= 1
            sizes[i] += 1
    assignments, offset = {}, 0
    for partition, size in zip(PARTITIONS, sizes, strict=True):
        for speaker in speakers[offset : offset + size]:
            assignments[speaker] = partition
        offset += size
    split = {"config": config, "speakers": assignments}
    split["sha256"] = digest(split)
    return apply_split(rows, split), split


def apply_split(rows, split):
    if split["sha256"] != digest({k: v for k, v in split.items() if k != "sha256"}):
        raise ValueError("Split hash mismatch")
    speakers = {r["speaker_id"] for r in rows}
    if speakers != set(split["speakers"]):
        raise ValueError("Split speaker registry does not match dataset")
    if set(split["speakers"].values()) != set(PARTITIONS):
        raise ValueError("Split must populate train/validation/test")
    result = copy.deepcopy(rows)
    for row in result:
        row["partition"] = split["speakers"][row["speaker_id"]]
    validate(result)
    leakage_checks(result)
    return result


def leakage_checks(rows, scientific=False):
    validate(rows)
    owners, partitions, seen_audio = {}, {}, {}
    checked_windows = 0

    def register(kind, key, row):
        identity = (kind, key)
        partition = row["partition"]
        previous = partitions.setdefault(identity, partition)
        if previous != partition:
            raise ValueError(f"{kind} leakage across partitions: {previous} / {partition}")
        if kind in ("recording", "recording_sha", "recording_pcm"):
            speaker = owners.setdefault(identity, row["speaker_id"])
            if speaker != row["speaker_id"]:
                raise ValueError("Recording has inconsistent speaker identity")

    for row in rows:
        if row["partition"] not in PARTITIONS:
            raise ValueError("Assign every training/evaluation example to a speaker partition")
        if scientific and (
            row["provenance"]["stage"] != "pilot"
            or row["provenance"]["speaker_identity"] != "verified"
            or row["provenance"]["annotation_kind"] not in ("human", "none")
        ):
            raise ValueError(
                "Stage-0/mock/unknown identity data cannot enter a scientific pilot run"
            )
        register("speaker", row["speaker_id"], row)
        register("recording", row["recording_id"], row)
        register("recording_sha", row["audio"]["sha256"], row)
        # Do not trust a manifest's checksum or an alias path without checking bytes.
        audio_key = (row["audio"]["reference"], row["audio"]["sha256"])
        if audio_key not in seen_audio:
            pcm, rate, count = read_audio(*audio_key)
            seen_audio[audio_key] = (pcm, rate, count)
        pcm, rate, count = seen_audio[audio_key]
        register("recording_pcm", digest([rate, hashlib.sha256(pcm).hexdigest()]), row)
        if set(row["windows"]) != {"target", "local", "wide"}:
            raise ValueError("Run audio preflight before leakage checks")
        for window in row["windows"].values():
            crop, crop_rate, crop_count = read_audio(window["reference"], window["sha256"])
            start, end = window["start_sample"], window["end_sample"]
            if not (
                0 <= start < end <= count
                and crop_rate == rate
                and crop_count == end - start
                and crop == pcm[start * 2 : end * 2]
                and window["start_seconds"] == start / rate
                and window["end_seconds"] == end / rate
                and hashlib.sha256(crop).hexdigest() == window["pcm_sha256"]
            ):
                raise ValueError("Window provenance does not match source audio")
            target = row["target"]
            if not (start / rate <= target["start_seconds"] < target["end_seconds"] <= end / rate):
                raise ValueError("Window does not contain target")
            register("audio_window_pcm", digest([rate, window["pcm_sha256"]]), row)
            checked_windows += 1
    return {
        "passed": True,
        "speakers": len({r["speaker_id"] for r in rows}),
        "recordings": len({r["recording_id"] for r in rows}),
        "checked_windows": checked_windows,
        "checks": [
            "speaker",
            "recording_id",
            "source_sha256",
            "decoded_recording_pcm",
            "decoded_window_pcm",
            "source_window_provenance",
            "annotation_provenance",
            "allowlisted_numeric_features_only",
            "raw_annotations_only_for_targets",
        ],
        "scientific_identity_required": scientific,
    }
