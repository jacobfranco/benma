"""Verify candidate packet, crops, lineage, pinned models, and research-only changes."""

import json
import subprocess
import sys
import wave
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import (
    PACKAGE,
    ROOT,
    digest,
    file_hash,
    read_json,
    read_rows,
    write_json,
    write_rows,
)
from perceptual_tone.learner_benchmark import DEFAULT, verify_inputs
from perceptual_tone.manifest import verify_baseline


def stable_audit(path, value, rows=False):
    if path.exists():
        prior = read_rows(path) if rows else read_json(path)
        if prior != value:
            raise ValueError("audit_changed_use_new_output_version")
    else:
        (write_rows if rows else write_json)(path, value)


def verify(root=DEFAULT):
    verify_inputs(root)
    packet = read_json(root / "qa/packet.json")
    assert (
        digest({k: v for k, v in packet.items() if k != "packet_sha256"}) == packet["packet_sha256"]
    )
    assert file_hash(root / "candidate-manifest.jsonl") == packet["candidate_manifest_sha256"]
    rows = read_rows(root / "candidate-manifest.jsonl")
    indexed = {r["example_id"]: r for r in rows}
    assert len(indexed) == len(rows)
    count = 0
    for item in packet["items"]:
        r = indexed[item["example_id"]]
        assert r["model_prediction"] is None and r["human_perceptual_judgment"] is None
        assert (
            r["alignment_qa"] is None
            and not r["eligible_for_training"]
            and not r["eligible_for_evaluation"]
        )
        grid = root / "aligned/jacob" / (r["utterance_id"] + ".TextGrid")
        assert file_hash(grid) == r["alignment_diagnostics"]["textgrid_sha256"]
        with wave.open(r["audio"]["reference"]) as source:
            rate, channels, width = (
                source.getframerate(),
                source.getnchannels(),
                source.getsampwidth(),
            )
            original = source.readframes(source.getnframes())
        for clip in item["clips"].values():
            path = ROOT / clip["path"]
            assert file_hash(path) == clip["sha256"]
            first, last = clip["start_sample"], clip["end_sample"]
            with wave.open(str(path)) as stream:
                assert stream.getframerate() == rate
                assert stream.getnframes() == last - first
                assert (
                    stream.readframes(stream.getnframes())
                    == original[first * channels * width : last * channels * width]
                )
            count += 1
        whole, tone, context = (item["clips"][v] for v in ["whole", "tone", "context"])
        assert context["start_sample"] <= whole["start_sample"] <= tone["start_sample"]
        assert tone["end_sample"] == whole["end_sample"] <= context["end_sample"]
    # Verify identity against the pre-existing fitted-model seals, without unpickling.
    primary = PACKAGE / "models/generated/aishell3-multispeaker-fixed-v2"
    secondary = PACKAGE / "models/generated/aishell3-first-four-tone-v1"
    assert (
        file_hash(primary / "experiment_B.joblib")
        == read_json(primary / "models-frozen.json")["models"]["experiment_B"]["sha256"]
    )
    assert (
        file_hash(secondary / "model2_hubert.joblib")
        == read_json(secondary / "selected.json")["models"]["model2_hubert"]["sha256"]
    )
    changes = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    ).splitlines()
    assert all(line[3:].startswith("research/perceptual-tone-model/") for line in changes), changes
    assert not (root / "releases").exists(), "This pass must stop before release"
    inventory = read_rows(root / "inventory.jsonl")
    failures = []
    for source in inventory:
        units = [r for r in rows if r["source_recording_id"] == source["recording_id"]]
        flags = sorted({f for r in units for f in r["flags"]})
        reasons = flags + ([source["exclusion_reason"]] if source["exclusion_reason"] else [])
        if not reasons:
            continue
        failures.append(
            {
                "recording_id": source["recording_id"],
                "names": source["names"],
                "phrase": source["alignment_transcript"],
                "selection": source["selection"],
                "audio_exists": source["audio_exists"],
                "transcript_exists": source["transcript_exists"],
                "phrase_reconstructable": source["phrase_reconstructable"],
                "alignment_attempted": bool(units),
                "alignment_failed": False if units else None,
                "tone_bearing_spans_derived": sum(
                    bool(r["spans"] and r["spans"]["available"]) for r in units
                ),
                "reasons": reasons,
            }
        )
    stable_audit(root / "exclusion-and-suspicion-report.jsonl", failures, rows=True)
    result = {
        "baseline": verify_baseline(),
        "review_items": len(packet["items"]),
        "exact_pcm_crops_verified": count,
        "original_sources_verified": sum(len(r["sources"]) for r in inventory),
        "native_artifacts_unchanged": len(
            read_json(root / "frozen-models.json")["native_preservation"]
        ),
        "preexisting_model_seals_verified": True,
        "candidate_manifest_sha256": file_hash(root / "candidate-manifest.jsonl"),
        "packet_sha256": packet["packet_sha256"],
        "research_only_changes": True,
        "model_predictions_generated": False,
        "human_QA_pending": True,
        "release_created": False,
        "source_role_counts": dict(Counter(r["role"] for r in inventory)),
        "alignment_flag_counts": dict(Counter(f for r in rows for f in r["flags"])),
    }
    stable_audit(root / "verification.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
