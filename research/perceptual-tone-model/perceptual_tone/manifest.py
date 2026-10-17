"""Canonical v2 manifest and a read-only bridge to the frozen v1 evaluator."""

import copy
import subprocess
import tempfile

from .common import PACKAGE, ROOT, canonical, file_hash, read_json, read_rows, write_rows


def verify_baseline():
    lock = read_json(PACKAGE / "configs/baseline.json")
    manifest_path = PACKAGE / "baseline-manifest.json"
    if file_hash(manifest_path) != lock["manifest_sha256"]:
        raise ValueError("Frozen manifest hash changed")
    committed = subprocess.check_output(
        ["git", "show", f"{lock['commit']}:research/perceptual-tone-model/baseline-manifest.json"],
        cwd=ROOT,
    )
    if committed != manifest_path.read_bytes():
        raise ValueError("Manifest differs from committed baseline")
    frozen = read_json(manifest_path)
    for name, expected in frozen["files"].items():
        if file_hash(ROOT / name) != expected:
            raise ValueError(f"Frozen baseline changed: {name}")
    return {**lock, "verified_files": len(frozen["files"])}


def upgrade(rows, dataset_version, speakers=None, fixture=False):
    """Speaker registry is an explicit recording -> verified pseudonym mapping."""
    result = []
    speakers = speakers or {}
    for original in rows:
        row = copy.deepcopy(original)
        if row["schema_version"] != "1.0.0":
            raise ValueError("Upgrade requires frozen v1 records")
        if row["annotations"]:
            raise ValueError("Legacy annotations need explicit timestamp/provenance migration")
        row.pop("disagreement")
        row["schema_version"] = "2.0.0"
        row["dataset_version"] = dataset_version
        row["target"]["pinyin"] = None  # Unknown is not synthesized from a label.
        row["expected"].update(previous_syllable=None, next_syllable=None)
        neighbors = {
            r["target"]["syllable_index"]: r["target"]["syllable"]
            for r in rows
            if r["recording_id"] == row["recording_id"] and r["target"]["unit_kind"] == "syllable"
        }
        index = row["target"]["syllable_index"]
        row["expected"]["previous_syllable"] = neighbors.get(index - 1)
        row["expected"]["next_syllable"] = neighbors.get(index + 1)
        row["speaker_id"] = speakers.get(row["recording_id"])
        row["partition"] = "stage0" if fixture else "unassigned"
        row["provenance"] = {
            "stage": "stage0" if fixture else "pilot",
            "speaker_identity": ("temporary_fixture" if fixture else "verified")
            if row["speaker_id"]
            else "unknown",
            "annotation_kind": "none",
            "notes": "Non-scientific fixture identities; no speaker independence claim."
            if fixture
            else None,
        }
        row["aggregate"] = None
        row["windows"] = {}
        result.append(row)
    validate(result)
    return result


def validate(rows):
    if not rows:
        raise ValueError("Empty manifest")
    process = subprocess.run(
        ["node", str(PACKAGE / "data/validate.cjs")], input=canonical(rows), capture_output=True
    )
    if process.returncode:
        raise ValueError(process.stderr.decode())
    seen = set()
    judgment_ids = set()
    versions = set()
    for row in rows:
        if row["example_id"] in seen:
            raise ValueError("Duplicate example_id")
        seen.add(row["example_id"])
        versions.add(row["dataset_version"])
        t, c = row["target"], row["context_window"]
        if not (
            0 <= c["start_seconds"] <= t["start_seconds"] < t["end_seconds"] <= c["end_seconds"]
        ):
            raise ValueError("Invalid timing/context bounds")
        if t["unit_kind"] == "syllable" and t["syllable_indices"] != [t["syllable_index"]]:
            raise ValueError("Syllable must have one owned index")
        if row["partition"] in ("train", "validation", "test") and (
            not row["speaker_id"] or t["unit_kind"] != "syllable"
        ):
            raise ValueError("Partition requires a known speaker and a single syllable")
        if row["provenance"]["speaker_identity"] == "verified" and not row["speaker_id"]:
            raise ValueError("Verified speaker cannot be null")
        for w in row["windows"].values():
            if not (
                0 <= w["start_sample"] < w["end_sample"]
                and w["sample_rate_hz"] == row["audio"]["sample_rate_hz"]
            ):
                raise ValueError("Invalid audio window")
        from .annotations import active_judgments

        active_judgments(row["annotations"])
        for judgment in row["annotations"]:
            if judgment["judgment_id"] in judgment_ids:
                raise ValueError("Judgment IDs must be globally unique across examples")
            judgment_ids.add(judgment["judgment_id"])
        origins = {a["origin"] for a in row["annotations"]}
        expected = row["provenance"]["annotation_kind"]
        if origins and origins != {expected}:
            raise ValueError("Mixed or inconsistent annotation provenance")
        if not origins and expected != "none":
            raise ValueError("Annotation provenance without judgments")
    if len(versions) != 1:
        raise ValueError("Mixed dataset versions")
    return rows


def replay(rows):
    baseline = verify_baseline()
    validate(rows)
    old = []
    old_keys = set(read_json(PACKAGE / "dataset.schema.json")["properties"])
    for row in rows:
        record = {k: copy.deepcopy(v) for k, v in row.items() if k in old_keys}
        record["schema_version"] = "1.0.0"
        record["partition"] = "stage0"
        record["target"].pop("pinyin")
        record["expected"].pop("previous_syllable")
        record["expected"].pop("next_syllable")
        record["annotations"] = []  # Annotation data never enters the evaluator.
        record["disagreement"] = {
            "status": "unlabeled",
            "counts": {k: 0 for k in ("acceptable", "borderline", "incorrect", "ungradable")},
            "adjudicated_label": None,
            "adjudicator_id": None,
            "notes": None,
        }
        old.append(record)
    with tempfile.TemporaryDirectory(prefix="benma-replay-") as directory:
        from pathlib import Path

        source, output = Path(directory) / "input.jsonl", Path(directory) / "output.jsonl"
        write_rows(source, old)
        subprocess.run(
            ["node", str(PACKAGE / "evaluate.cjs"), str(source), str(output)],
            check=True,
            capture_output=True,
            cwd=ROOT,
        )
        evaluated = read_rows(output)
    result = copy.deepcopy(rows)
    for row, evaluated_row in zip(result, evaluated, strict=True):
        row["deterministic"] = evaluated_row["deterministic"]
    return result, baseline
