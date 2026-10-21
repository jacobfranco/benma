"""Resume frozen reliability results, finish exploratory reporting, verify inputs.

Run with the existing benchmark Python environment. Never regenerates the packet,
loads a model, or reruns inference. Existing artifacts are checked, not overwritten.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.blind_analysis import (
    FROZEN_GATE_SHA,
    PACKET_SHA,
    join_key,
    learner_analysis,
    require_gate,
    validate_export,
)
from perceptual_tone.blind_analysis_report import render
from perceptual_tone.blind_packet import (
    LEARNER,
    NATIVE,
    OUTPUT,
    leakage_audit,
    require,
    verify_preservation,
)
from perceptual_tone.common import (
    PACKAGE,
    ROOT,
    digest,
    file_hash,
    read_json,
    read_rows,
    write_json,
)

RUN = OUTPUT.parent / "realized-tone-analysis-v1-20261019"
EXPORT = Path("/home/jacob/Downloads/benma-realized-tone-blind-review.json")
REPORT = PACKAGE / "realized-tone-reliability-first-report.md"


def save_once(path, value):
    if path.exists():
        require(read_json(path) == value, "analysis_artifact_changed:" + str(path))
    else:
        write_json(path, value)


def verify_freeze():
    result = verify_preservation()
    artifact_seal = read_json(OUTPUT / "private/packet-artifact-seal.json")
    for name, sha in artifact_seal["files"].items():
        require(file_hash(ROOT / name) == sha, "packet_artifact_changed:" + name)
    selection_seal = read_json(OUTPUT / "private/selection-seal.json")
    require(digest(read_json(OUTPUT / "private/packet-manifest.json")) == PACKET_SHA, "packet_hash")
    require(
        file_hash(OUTPUT / "private/packet-manifest.json")
        == selection_seal["manifest_file_sha256"],
        "manifest_bytes",
    )
    key = read_json(OUTPUT / "private/answer-key.json")
    transfer = OUTPUT.parent / "learner-transfer-v1-20261019"
    phase_hashes = {}
    for phase in ("primary", "diagnostic", "unknown"):
        seal = read_json(transfer / phase / "results-seal.json")
        for name, sha in seal["files"].items():
            require(file_hash(transfer / phase / name) == sha, "model_result_changed:" + name)
        phase_hashes[phase] = file_hash(transfer / phase / "predictions.jsonl")
    require(key["saved_predictions_sha256"] == phase_hashes["primary"], "key_prediction_hash")
    models = read_json(LEARNER / "inference-config.json")["models"]
    for model in models.values():
        require(file_hash(model["path"]) == model["sha256"], "model_hash")
    require(
        EXPORT.read_bytes() == (RUN / "human-export.original.json").read_bytes(), "export_bytes"
    )
    require(
        file_hash(EXPORT) == read_json(RUN / "01-export-validation.json")["export_sha256"],
        "export_hash",
    )
    audit = leakage_audit(
        (OUTPUT / "qa/index.html").read_text(), read_json(OUTPUT / "private/selection.json")
    )
    require(audit == read_json(OUTPUT / "private/leakage-audit.json"), "visible_leakage_audit")
    require(key["model_results_used_for_selection"] is False, "model_selection_leakage")
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    ).splitlines()
    require(
        all(line[3:].startswith("research/perceptual-tone-model/") for line in status),
        "production_changed",
    )
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    return {
        "status": "PASS",
        **result,
        "packet_artifact_hashes_unchanged": len(artifact_seal["files"]),
        "packet_sha256": PACKET_SHA,
        "export_sha256": file_hash(EXPORT),
        "answer_key_sha256": file_hash(OUTPUT / "private/answer-key.json"),
        "learner_release_manifest_sha256": file_hash(LEARNER / "release-manifest.json"),
        "native_release_sha256": file_hash(NATIVE / "release.json"),
        "model_files": models,
        "prediction_file_hashes": phase_hashes,
        "public_page_leakage_audit": audit,
        "annotation_blinding_limit": (
            "No model output was exposed by the sealed annotation page "
            "or used to select/order stimuli. Independent reviewer memory or filesystem access "
            "cannot be audited from the export."
        ),
        "production_inference_grading_ui_apis_deployment_unchanged": True,
        "git_diff_check": "PASS",
        "no_training_tuning_adaptation_inference_commit_push_deploy": True,
    }


def main():
    review = read_json(RUN / "human-export.original.json")
    validate_export(read_json(OUTPUT / "private/packet-manifest.json"), review)
    # Reuse already completed control and repeat scoring and the frozen decision.
    stage = read_json(RUN / "02-controls-and-repeats.json")
    gate = read_json(RUN / "03-reliability-gate.json")
    require_gate(stage, gate)
    require(
        digest(gate) == FROZEN_GATE_SHA and gate["classification"] == "INSUFFICIENT", "frozen_gate"
    )
    checks = read_json(RUN / "03-registered-checks.json")
    require(checks["passed"] is False, "registered_gate_changed")
    freeze = verify_freeze()
    joined = join_key(review, read_json(OUTPUT / "private/answer-key.json"))
    result = learner_analysis(joined, read_rows(LEARNER / "primary.jsonl"), stage, gate)
    save_once(RUN / "05-final-exploratory-analysis.json", result)
    save_once(RUN / "06-freeze-verification.json", freeze)
    report = render(review, stage, gate, checks, result, freeze)
    if REPORT.exists():
        require(REPORT.read_text() == report, "report_changed")
    else:
        REPORT.write_text(report)
    print(
        json.dumps(
            {
                "status": "PASS",
                "reliability": gate["classification"],
                "report": str(REPORT),
                "artifacts": str(RUN),
                "baseline_hashes": freeze["baseline_hashes_unchanged"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
