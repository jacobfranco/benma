"""Verify packet integrity and research-only preservation, without annotation analysis."""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.blind_packet import OUTPUT, leakage_audit, require, verify_preservation
from perceptual_tone.common import PACKAGE, ROOT, digest, file_hash, read_json, write_json


def verify():
    preservation = verify_preservation()
    private = OUTPUT / "private"
    selection = read_json(private / "selection.json")
    seal = read_json(private / "selection-seal.json")
    require(file_hash(private / "selection.json") == seal["selection_sha256"], "selection_changed")
    require(
        file_hash(private / "packet-manifest.json") == seal["manifest_file_sha256"],
        "manifest_file_changed",
    )
    require(
        digest(read_json(private / "packet-manifest.json")) == seal["packet_sha256"],
        "manifest_payload_changed",
    )
    audit = leakage_audit((OUTPUT / "qa/index.html").read_text(), selection)
    require(audit == read_json(private / "leakage-audit.json"), "leakage_audit_changed")
    key = read_json(private / "answer-key.json")
    require(
        key["packet_sha256"] == seal["packet_sha256"] and len(key["items"]) == 52,
        "key_packet_mismatch",
    )
    require(
        [r["annotation_id"] for r in key["items"]]
        == [r["annotation_id"] for r in selection["presentation_order"]],
        "key_order_mismatch",
    )
    browser = read_json(private / "browser-tests.log")
    require(browser["status"] == "PASS" and browser["audio_decodes"] == 104, "browser_tests_failed")
    log = (private / "python-tests.log").read_text()
    require(
        bool(re.search(r"Ran 12 tests", log)) and log.rstrip().endswith("OK"), "python_tests_failed"
    )
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    ).splitlines()
    require(
        all(line[3:].startswith("research/perceptual-tone-model/") for line in status),
        "change_outside_research",
    )
    starting = read_json(private / "starting-state.json")
    changed = [line[3:] for line in status if line[3:] not in starting["files"]]
    for name in changed:
        result = subprocess.run(
            ["git", "diff", "--no-index", "--check", "/dev/null", name],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        require(
            result.returncode in (0, 1) and not result.stdout and not result.stderr,
            "untracked_whitespace:" + name,
        )
    python_files = [name for name in changed if name.endswith(".py")]
    subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", *python_files], cwd=ROOT, check=True)
    subprocess.run(
        [str(ROOT / ".venv/bin/ruff"), "format", "--check", *python_files], cwd=ROOT, check=True
    )
    for filename in ("blind_review.js", "blind_review_smoke.cjs"):
        subprocess.run(["node", "--check", str(PACKAGE / "scripts" / filename)], check=True)
    artifacts = [
        p
        for p in OUTPUT.rglob("*")
        if p.is_file() and p.name not in ("validation.json", "packet-artifact-seal.json")
    ]
    artifacts.extend(ROOT / name for name in changed)
    artifact_seal = {
        "schema": "benma-realized-tone-artifact-seal-v1",
        "packet_sha256": seal["packet_sha256"],
        "files": {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(artifacts)},
    }
    result = {
        "status": "PASS",
        **preservation,
        "packet_sha256": seal["packet_sha256"],
        "summary": selection["summary"],
        "leakage_audit": audit,
        "python_tests": 12,
        "browser_tests": browser,
        "ruff_and_javascript_syntax": "PASS",
        "git_diff_check": "PASS",
        "untracked_whitespace_check": "PASS",
        "new_research_files": changed,
        "no_production_inference_grading_ui_api_or_deployment_changes": True,
        "no_training_calibration_annotation_scoring_commit_push_or_deploy": True,
        "human_review_files_created": 0,
    }
    for name, value in (("packet-artifact-seal.json", artifact_seal), ("validation.json", result)):
        target = private / name
        if target.exists():
            require(read_json(target) == value, "verification_record_changed:" + name)
        else:
            write_json(target, value)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
