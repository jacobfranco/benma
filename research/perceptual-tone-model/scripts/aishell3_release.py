"""Freeze the approved three-span representation; never modify an existing release."""

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import audit, stable_json, stable_rows
from aishell3_round2 import ingest_round2
from perceptual_tone.aishell3_qa import dataset_gate
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows
from perceptual_tone.manifest import verify_baseline

VERSION = "aishell3-nucleus-coda-context-v1-20261017"
SPEAKERS = {
    "train": [
        "SSB0009",
        "SSB0011",
        "SSB0012",
        "SSB0016",
        "SSB0018",
        "SSB0057",
        "SSB0073",
        "SSB0080",
        "SSB0122",
        "SSB0139",
    ],
    "validation": ["SSB0005", "SSB0033", "SSB0112"],
    "test": ["SSB0038", "SSB0043", "SSB0133"],
}


def verify_release(folder):
    release = read_json(folder / "release.json")
    for name, expected in release["files"].items():
        if file_hash(folder / name) != expected:
            raise ValueError("released_file_changed:" + name)
    for row in read_rows(folder / "manifest.jsonl"):
        original = row["original"]
        if file_hash(original["audio"]["reference"]) != original["audio"]["sha256"]:
            raise ValueError("released_source_audio_changed")
    return release


def release(root, source, output):
    if (output / "release.json").exists():
        return verify_release(output)
    baseline = verify_baseline()
    summary = audit(root, scaled=True)
    qa = root / "round2-final"
    result = ingest_round2(qa, source, qa / "developer-decisions.jsonl")
    if result["final_decisions"] != {"PASS": 18}:
        raise ValueError("round2_final_not_all_pass")
    accepted = read_rows(root / "continuation/scaled-candidates.jsonl")
    proposals = read_rows(qa / "derived-candidates.jsonl")
    if [p["original"] for p in proposals] != accepted:
        raise ValueError("derived_originals_changed")
    for r in accepted:
        if r["speaker_id"] not in SPEAKERS[r["partition"]]:
            raise ValueError("speaker_split_changed")
    owners = {key: {} for key in ("speaker_id", "utterance_id", "pcm_sha256")}
    derivatives = {}
    for p in proposals:
        r = p["original"]
        if not p["spans"]["available"]:
            raise ValueError("pooling_span_unavailable")
        for key, seen in owners.items():
            if seen.setdefault(r[key], r["partition"]) != r["partition"]:
                raise ValueError("split_leakage:" + key)
        for media in p["media"].values():
            if file_hash(qa / media["reference"]) != media["sha256"]:
                raise ValueError("derivative_changed")
            if derivatives.setdefault(media["pcm_sha256"], r["partition"]) != r["partition"]:
                raise ValueError("derivative_pcm_leakage")
    numbered = [p for p in proposals if p["original"]["label"] != "T5"]
    if not dataset_gate([p["original"] for p in numbered])["passed"]:
        raise ValueError("four_tone_coverage_failed")
    output.mkdir(parents=True, exist_ok=False)
    rows = [
        {
            "dataset_version": VERSION,
            "example_id": p["example_id"],
            "original": p["original"],
            "spans": p["spans"],
            "primary_eligible": p["original"]["label"] != "T5",
        }
        for p in proposals
    ]
    stable_rows(output / "manifest.jsonl", rows)
    stable_rows(output / "primary.jsonl", [r for r in rows if r["primary_eligible"]])
    stable_rows(output / "neutral.jsonl", [r for r in rows if not r["primary_eligible"]])
    stable_rows(
        output / "quarantined.jsonl", read_rows(root / "continuation/scaled-rejected.jsonl")
    )
    evidence = {
        "round1-export.json": root / "round2/round1-export.json",
        "round1-decisions.jsonl": root / "continuation/playback-decisions.jsonl",
        "round2-export.json": source,
        "round2-decisions.jsonl": qa / "developer-decisions.jsonl",
        "round2-packet.json": qa / "packet.json",
        "speaker-registry.jsonl": root / "speaker-registry.jsonl",
        "acquisition.json": root / "acquisition.json",
        "alignment-config.json": PACKAGE / "configs/aishell3.json",
        "pilot-lexicon.json": root / "pilot/lexicon-audit.json",
        "expansion-lexicon.json": root / "expansion/lexicon-audit.json",
    }
    for name, path in evidence.items():
        shutil.copyfile(path, output / name)
    for name in ("aishell3.py", "aishell3_alignment.py", "aishell3_boundaries.py"):
        shutil.copyfile(PACKAGE / "perceptual_tone" / name, output / name)
    info = {
        "dataset_version": VERSION,
        "source_corpus": "AISHELL-3/OpenSLR93/v1.0",
        "baseline": baseline,
        "accepted": len(rows),
        "primary_numbered": len(numbered),
        "neutral": len(rows) - len(numbered),
        "quarantined": summary["units_rejected"],
        "speaker_split": SPEAKERS,
        "class_counts": {
            part: dict(
                Counter(
                    p["original"]["label"] for p in proposals if p["original"]["partition"] == part
                )
            )
            for part in SPEAKERS
        },
        "sample_boundary_version": "decimal_nearest_half_up_half_open_v1",
        "pooling_version": proposals[0]["spans"]["policy"],
        "representation": "original_read_unit + nucleus_coda_pooling + short_context",
        "round2_result": result,
        "short_span_policy": (
            "Retained after explicit human PASS, including 20/30/40/50ms probes; "
            "encoder frame coverage checked separately."
        ),
        "label_metadata_for_training_inputs": False,
        "files": {p.name: file_hash(p) for p in sorted(output.iterdir()) if p.is_file()},
        "training_started": False,
    }
    info["manifest_sha256"] = file_hash(output / "manifest.jsonl")
    stable_json(output / "release.json", info)
    return verify_release(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE / "data/generated/aishell3")
    parser.add_argument(
        "--input", type=Path, default=Path("/home/jacob/Downloads/aishell3-round2-decisions.json")
    )
    parser.add_argument(
        "--output", type=Path, default=PACKAGE / "data/generated/aishell3/releases" / VERSION
    )
    parser.add_argument("--verify", action="store_true")
    a = parser.parse_args()
    print(
        __import__("json").dumps(
            verify_release(a.output) if a.verify else release(a.root, a.input, a.output), indent=2
        )
    )
