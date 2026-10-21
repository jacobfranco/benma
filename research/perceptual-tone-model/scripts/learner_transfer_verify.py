"""Verify release, predictions, raw QA, original artifacts and production freeze."""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import ROOT, file_hash, read_json, read_rows, write_json
from perceptual_tone.learner_finalization import CONSTRUCTION, verify
from perceptual_tone.learner_release import DRAFT, RELEASE, RUN, verify_release
from perceptual_tone.learner_transfer import check_phase
from perceptual_tone.manifest import verify_baseline


def validate():
    baseline = verify_baseline()
    construction = verify()
    starting = read_json(RUN / "starting-state.json")
    for name, sha in starting["preserved_files"].items():
        if file_hash(ROOT / name) != sha:
            raise ValueError("preexisting_research_artifact_changed:" + name)
    release = verify_release()
    if file_hash(DRAFT) != file_hash(RELEASE / "raw-draft.json"):
        raise ValueError("raw_draft_changed")
    rows = read_rows(RELEASE / "all-units.jsonl")
    answers = {r["unit_id"]: r for r in read_json(RELEASE / "raw-draft.json")["reviews"]}
    if any(u["qa"] != answers[u["example_id"]] for u in rows):
        raise ValueError("human_notes_or_telemetry_changed")
    phases = {}
    primary_seal_path = RUN / "primary/results-seal.json"
    for phase in ("primary", "diagnostic", "unknown"):
        seal = check_phase(phase)
        protocol = read_json(RUN / phase / "protocol.json")
        if protocol["config"] != read_json(RELEASE / "inference-config.json"):
            raise ValueError("inference_config_changed_after_release")
        if phase != "primary" and protocol["primary_result_seal_sha256"] != file_hash(
            primary_seal_path
        ):
            raise ValueError("primary_not_frozen_before_supplemental")
        if protocol["learner_training_calls"] != 0 or protocol["model_reselection"]:
            raise ValueError("learner_training_or_selection")
        predictions = read_rows(RUN / phase / "predictions.jsonl")
        accepted = read_rows(RELEASE / (phase + ".jsonl"))
        if {r["example_id"] for r in predictions} != {r["example_id"] for r in accepted}:
            raise ValueError("wrong_inference_population")
        reproduction = read_json(RUN / (phase + "-reproduction.json"))
        if (
            any(reproduction["probability_max_deltas"].values())
            or any(reproduction["fresh_encoder_max_deltas_one_per_take"].values())
            or not reproduction["deterministic_full_reproduction_exact"]
        ):
            raise ValueError("reproduction_failure")
        phases[phase] = {
            "rows": len(predictions),
            "seal_sha256": file_hash(RUN / phase / "results-seal.json"),
            "frozen_at": seal["frozen_at"],
            "reproduction": reproduction,
        }
    comparison = read_json(RUN / "representation-comparison/seal.json")
    for name, sha in comparison["files"].items():
        if file_hash(RUN / "representation-comparison" / name) != sha:
            raise ValueError("comparison_artifact_changed")
    changes = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    ).splitlines()
    if any(not line[3:].startswith("research/perceptual-tone-model/") for line in changes):
        raise ValueError("change_outside_research")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    # git diff does not cover untracked files. Check those without staging them.
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    for name in untracked:
        result = subprocess.run(
            ["git", "diff", "--no-index", "--check", "/dev/null", name],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 1) or result.stdout.strip() or result.stderr.strip():
            raise ValueError(
                "untracked_whitespace_error:" + name + ":" + result.stdout + result.stderr
            )
    log = (RUN / "python-tests.log").read_text()
    test_count = re.search(r"Ran (\d+) tests", log)
    if not test_count or not log.rstrip().endswith("OK"):
        raise ValueError("focused_tests_not_passed")
    browser = read_json(RUN / "browser-tests.log")
    if not browser["playback_telemetry_optional"] or not browser["exact_missing_field_errors"]:
        raise ValueError("browser_completion_contract_failed")
    result = {
        "status": "PASS",
        "release": release,
        "baseline_verified_files": baseline["verified_files"],
        "source_file_references": sum(
            len(s["sources"]) for s in read_rows(CONSTRUCTION / "inventory.jsonl")
        ),
        "native_artifacts_unchanged": len(
            read_json(CONSTRUCTION / "frozen-models.json")["native_preservation"]
        ),
        "construction_artifacts_unchanged": construction["construction_artifacts_unchanged"],
        "preexisting_construction_and_review_files_unchanged": len(starting["preserved_files"]),
        "raw_draft_and_all_notes_telemetry_unchanged": True,
        "primary_then_supplemental": True,
        "phases": phases,
        "comparison_reproduction": read_json(RUN / "comparison-reproduction.json"),
        "focused_python_tests_passed": int(test_count[1]),
        "browser": browser,
        "git_diff_check": "PASS",
        "untracked_whitespace_check": "PASS",
        "research_only_changes": [line[3:] for line in changes],
        "no_production_changes": True,
        "no_training_adaptation_or_model_reselection": True,
    }
    target = RUN / "validation.json"
    if target.exists():
        if read_json(target) != result:
            raise ValueError("verification_record_changed")
    else:
        write_json(target, result)
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
