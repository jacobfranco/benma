"""Read-only frozen evidence/preservation audit; writes only new audit receipts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.f0_foundation import ORIGINAL_TRACKERS
from benchmark.pronunciation_v2.f0_foundation_rmvpe import MODEL_HASH, ROOT, SOURCE_HASHES
from benchmark.pronunciation_v2.f0_foundation_rmvpe_run import verify_corpus
from benchmark.pronunciation_v2.f0_foundation_run import load_track

REPO = Path(__file__).resolve().parents[2]
REPORT = REPO / "docs/research/pronunciation-v2/2026-10-05-f0-foundation"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path):
    rows = verify_corpus(root)
    old = Path("/tmp/benma-f0-bakeoff")
    frozen = json.loads((root / "frozen-artifact-hashes.json").read_text())
    for relative, expected in frozen.items():
        assert digest(old / relative) == expected, relative
    prior_tracks = 0
    frames = 0
    for row in rows:
        for tracker in ORIGINAL_TRACKERS:
            relative = f"tracks/{row['id']}--{tracker}.json"
            assert digest(root.parent / relative) == frozen[relative]
            prior_tracks += 1
        path = root / "tracks" / f"{row['id']}--rmvpe.json"
        track = load_track(path)
        assert track.audio_sha256 == row["sha256"]
        evidence = np.load(root / "activations" / f"{row['id']}.npz")
        ts, hz, conf = track.arrays()
        assert evidence["salience"].shape == (len(ts), 360)
        np.testing.assert_array_equal(ts, evidence["times"])
        np.testing.assert_array_equal(np.nan_to_num(hz), evidence["native_f0_hz"])
        np.testing.assert_array_equal(conf, evidence["salience"].max(axis=1))
        frames += len(ts)
    alignments = list((root.parent / "alignments").glob("*.json"))
    assert len(alignments) == 36
    for path in alignments:
        assert digest(path) == frozen[f"alignments/{path.name}"]
    assert digest(root / "vendor/rmvpe.pt") == MODEL_HASH
    for name, expected in SOURCE_HASHES.items():
        assert digest(root / "vendor/rvc" / name) == expected
    # Original capture bytes are also untouched; no database/provider is used.
    inventory = json.loads(
        (REPO / "services/api/var/capture-robustness/inventory-all.json").read_text()
    )
    for item in inventory["recordings"]:
        assert digest(Path(item["original"]["path"])) == item["original"]["sha256"]
    joins = {}
    for name, csv_name, expected_new in (
        ("metrics", "per-recording-metrics", 98),
        ("repeatability", "pairwise-repeatability", 72),
        ("windows", "diagnostic-windows", 56),
        ("perturbations", "source-perturbations", 6),
        ("low-f0-proxy", "low-f0-proxy", 36),
        ("low-f0-under70", "low-f0-under70", 6),
        ("acoustic-support", "acoustic-support", 30),
    ):
        previous = json.loads((root.parent / f"{name}.json").read_text())
        added = json.loads((root / f"{name}.json").read_text())
        assert len(added) == expected_new, (name, len(added))
        with (REPORT / f"{csv_name}.csv").open() as stream:
            exported = list(csv.DictReader(stream))
        assert len(exported) == len(previous) + len(added)
        # CSV formatting is Python str; every existing field/value survives the join.
        for actual, expected in zip(exported, previous + added, strict=True):
            assert all(actual[k] == ("" if v is None else str(v)) for k, v in expected.items()), (
                name,
                expected,
            )
        joins[name] = {"previous": len(previous), "rmvpe": len(added), "combined": len(exported)}
    baseline = json.loads((root / "baseline-files.json").read_text())
    changed = []
    unchanged = 0
    for relative, expected in baseline.items():
        path = REPO / relative
        actual = digest(path) if path.is_file() else None
        if actual == expected:
            unchanged += 1
        else:
            assert relative.startswith(
                (
                    "benchmark/pronunciation_v2/f0_foundation",
                    "docs/research/pronunciation-v2/2026-10-05-f0-foundation/",
                )
            ), relative
            changed.append(relative)
    tracked_diff = subprocess.check_output(["git", "diff", "--binary"], cwd=REPO)
    assert tracked_diff == (root / "baseline.diff").read_bytes(), (
        "Pre-existing tracked diff changed"
    )
    assert (
        subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO).decode().strip()
        == "pronunciation-v2-research"
    )
    notes = json.loads((root / "blind-review-receipt.json").read_text())
    assert digest(root / "blind-review-before-reveal.md") == notes["notes_sha256"]
    assert digest(root.parent / "blind-key-six.json") == notes["key_sha256"]
    result = {
        "corpus_files_verified": 49,
        "original_capture_hashes_verified": len(inventory["recordings"]),
        "prior_native_tracks_unchanged": prior_tracks,
        "rmvpe_native_tracks": 49,
        "rmvpe_salience_files": 49,
        "rmvpe_frames": frames,
        "salience_bins": 360,
        "failures": 0,
        "skips": 0,
        "saved_alignment_paths_unchanged": len(alignments),
        "original_frozen_artifacts_unchanged": len(frozen),
        "model_and_source_hashes_verified": True,
        "metadata_invariance": json.loads((root / "verification-rmvpe.json").read_text())[
            "invariance"
        ]["byte_identical"],
        "table_joins_and_all_prior_values_verified": joins,
        "preexisting_file_states": len(baseline),
        "unchanged_preexisting_files": unchanged,
        "changed_preexisting_research_files": changed,
        "preexisting_tracked_diff_identical": True,
        "blinded_notes_and_key_verified": True,
    }
    for path in (root / "artifact-verification.json", REPORT / "rmvpe-artifact-verification.json"):
        path.write_text(json.dumps(result, indent=2) + "\n")
    # Durable receipt includes model, raw data, notes and all derived RMVPE evidence.
    paths = [
        p
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name != "artifact-sha256.json"
    ]
    hashes = {str(p.relative_to(root)): digest(p) for p in sorted(paths)}
    (root / "artifact-sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT)
    audit(parser.parse_args().output)
