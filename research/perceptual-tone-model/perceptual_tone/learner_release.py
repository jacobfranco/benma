"""Attested learner QA ingestion and write-once, evaluation-only releases.

This module cannot load learned models. All adjudication precedes inference.
"""

import shutil
import wave
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .aishell3_boundaries import derive
from .common import PACKAGE, ROOT, digest, file_hash, read_json, read_rows, write_json, write_rows
from .learner_benchmark import import_alignment
from .learner_finalization import (
    CONSTRUCTION,
    DEFAULT,
    DIAGNOSTIC,
    NATURAL,
    UNKNOWN,
    render,
    validate_reviews,
    verify,
)

VERSION = "benma-learner-natural-v1-20261019"
RELEASE = PACKAGE / "data/generated/releases" / VERSION
RUN = PACKAGE / "data/generated/learner-transfer-v1-20261019"
REQUEST = Path(
    "/home/jacob/.codex/attachments/28269420-0346-4696-b77f-5ccdd41340b6/pasted-text.txt"
)
DRAFT = Path("/home/jacob/Downloads/benma-learner-alignment-draft.json")


def now():
    return datetime.now(UTC).isoformat()


def alignment_audit(units):
    """Reconstruct from existing TextGrids; never rerun the forced aligner."""
    indexed = {u["example_id"]: u for u in units}
    lexicon = read_json(CONSTRUCTION / "lexicon.json")
    failures, count = [], 0
    for utterance in read_rows(CONSTRUCTION / "utterances.jsonl"):
        ident = utterance["utterance_id"]
        first = indexed[f"learner:{ident}:0"]
        grid = CONSTRUCTION / "aligned/jacob" / (ident + ".TextGrid")
        if file_hash(grid) != first["alignment_diagnostics"]["textgrid_sha256"]:
            raise ValueError("textgrid_hash_changed")
        rebuilt = import_alignment(
            utterance, grid.read_text(), lexicon, first["alignment_diagnostics"]
        )
        for r in rebuilt:
            saved = indexed[r["example_id"]]
            for key in ("hanzi", "index", "start", "end", "aligned_phones", "audio"):
                if r[key] != saved[key]:
                    failures.append([r["example_id"], key])
            with wave.open(saved["audio"]["reference"]) as stream:
                projection = derive(r, stream.getframerate(), stream.getnframes())
            for key in (
                "playback_read_unit",
                "tone_bearing_pooling_span",
                "context",
                "owned_phone_indices",
                "original_mfa_phones",
                "policy",
            ):
                if projection[key] != saved["spans"][key]:
                    failures.append([r["example_id"], key])
            if saved["structural_violations"]:
                failures.append([r["example_id"], "structural_violations"])
            count += 1
    return {
        "reconstructed_units": count,
        "mismatches": failures,
        "systematic_bug_found": bool(failures),
        "repaired_count": 0,
        "assessment": (
            "Saved word/phone ownership, source samples and nucleus/coda reconstruction "
            "reproduce exactly. No general reconstruction defect demonstrated. Human crop "
            "objections remain authoritative; reproduction does not prove acoustic correctness. "
            "Frequent short finals and wrong-unit judgments may reflect forced-alignment "
            "limitations or learner production; this evidence cannot distinguish their cause. "
            "No general correction is established, so quarantine tone non-PASS without repair."
        ),
    }


def adjudicate(unit, review, item):
    if unit["structural_violations"]:
        raise ValueError("systematic_alignment_investigation_required")
    accepted = review["tone"] == "PASS"
    objection = review["whole"] != "PASS" or not accepted
    decision = "PASS_AS_IS" if accepted else "QUARANTINE_UNIT"
    reason = (
        "Human tone-bearing PASS; preserve the whole-target objection."
        if accepted and objection
        else "Both human crop judgments PASS."
        if accepted
        else "Human tone-bearing " + review["tone"] + "; no justified general repair."
    )
    return {
        **unit,
        "qa_item_id": item["item_id"],
        "qa_item_sha256": item["item_sha256"],
        "qa": review,
        "qa_status": "ACCEPTED_BY_DEVELOPER_ATTESTATION",
        "alignment_qa": review,
        "adjudication_required": objection,
        "adjudication": decision,
        "adjudication_reason": reason,
        "quarantined": not accepted,
        "quarantine_reasons": [] if accepted else ["human_tone_" + review["tone"]],
        "status": "frozen_evaluation_only" if accepted else "quarantined",
        "partition": "evaluation_only",
        "eligible_for_evaluation": accepted,
        "eligible_for_training": False,
        "actual_realized_acoustic_tone": "UNKNOWN",
        "whole_duration_seconds": unit["end"] - unit["start"],
        "tone_duration_seconds": (
            item["clips"]["tone"]["end_sample"] - item["clips"]["tone"]["start_sample"]
        )
        / item["clips"]["tone"]["sample_rate_hz"],
    }


def freeze(draft=DRAFT, destination=RELEASE):
    if destination.exists():
        raise ValueError("release_exists_immutable_use_verify")
    preservation = verify()
    packet = read_json(DEFAULT / "qa/packet.json")
    if digest({k: v for k, v in packet.items() if k != "packet_sha256"}) != packet["packet_sha256"]:
        raise ValueError("packet_content_hash_mismatch")
    answers = read_json(draft)
    validation = validate_reviews(packet, answers)
    units = read_rows(DEFAULT / "candidate-manifest.jsonl")
    if len(units) != 123 or len(packet["items"]) != 123:
        raise ValueError("expected_123_units")
    audit = alignment_audit(units)
    if audit["systematic_bug_found"]:
        raise ValueError("systematic_alignment_bug_stop_before_release_or_scoring")
    reviews = {r["unit_id"]: r for r in answers["reviews"]}
    items = {r["unit_id"]: r for r in packet["items"]}
    released = [adjudicate(u, reviews[u["example_id"]], items[u["example_id"]]) for u in units]
    false_counts = {
        k: sum(r["heard"][k] is False for r in reviews.values())
        for k in ("context", "whole", "tone")
    }
    false_counts["heard_all"] = sum(r["heard_all"] is False for r in reviews.values())
    acceptance = {
        "accepted_by_developer_attestation": True,
        "playback_telemetry_complete": not any(false_counts.values()),
        "reviewer": answers["reviewer"],
        "substantive_reviews": validation,
        "false_playback_counts": false_counts,
        "raw_draft_sha256": file_hash(draft),
        "request_sha256": file_hash(REQUEST),
        "acceptance_basis": "Explicit developer attestation in the supplied request (request.txt).",
        "policy": "Human decisions authoritative; playback telemetry auxiliary provenance only.",
        "reason": (
            "Developer reviewed every item and entered every intended judgment; context was "
            "used only when needed and some whole/tone playback events did not register "
            "reliably. Draft accepted without changing flags or inventing listening events."
        ),
        "missing_substantive_decisions": 0,
        "whole_decisions": dict(Counter(r["whole"] for r in reviews.values())),
        "tone_decisions": dict(Counter(r["tone"] for r in reviews.values())),
    }
    destination.mkdir(parents=True)
    shutil.copyfile(draft, destination / "raw-draft.json")
    shutil.copyfile(REQUEST, destination / "request.txt")
    for name in (
        "qa/packet.json",
        "candidate-manifest.jsonl",
        "selected-take-provenance.jsonl",
        "source-lineage.json",
    ):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEFAULT / name, target)
    write_json(destination / "review-acceptance.json", acceptance)
    write_json(destination / "alignment-audit.json", audit)
    write_rows(
        destination / "adjudication.jsonl", [u for u in released if u["adjudication_required"]]
    )
    write_rows(destination / "all-units.jsonl", released)
    counts = {}
    for name, category in (("primary", NATURAL), ("diagnostic", DIAGNOSTIC), ("unknown", UNKNOWN)):
        selected = [u for u in released if u["provenance_category"] == category]
        write_rows(destination / (name + ".jsonl"), [u for u in selected if not u["quarantined"]])
        write_rows(
            destination / (name + "-quarantine.jsonl"), [u for u in selected if u["quarantined"]]
        )
        counts[name] = {
            "candidate": len(selected),
            "accepted": sum(not u["quarantined"] for u in selected),
            "quarantined": sum(u["quarantined"] for u in selected),
        }
    master = read_rows(DEFAULT / "selected-take-provenance.jsonl")
    historical_ids = {
        r["source_id"]
        for r in master
        if r["alignment_transcript"] == "我想买这个"
        or any(n.startswith(("8faf1a90", "a5acd04c")) for n in r["names"])
    }
    write_rows(
        destination / "historical-special-cases.jsonl",
        [u for u in released if u["source_id"] in historical_ids],
    )
    # Freeze model identities before any learner probabilities are available.
    models = {
        "expanded": PACKAGE / "models/generated/aishell3-multispeaker-fixed-v2/experiment_B.joblib",
        "pilot": PACKAGE / "models/generated/aishell3-first-four-tone-v1/model2_hubert.joblib",
    }
    write_json(
        destination / "inference-config.json",
        {
            "models": {k: {"path": str(v), "sha256": file_hash(v)} for k, v in models.items()},
            "encoder": read_json(PACKAGE / "configs/encoders.json")["chinese_hubert_base"],
            "view": "context",
            "layer": 9,
            "pooling": "nucleus_coda_frame_center_mean",
            "classifier": "balanced_logistic_regression",
            "C": 0.1,
            "training_allowed": False,
            "adaptation_allowed": False,
            "threshold_fitting_allowed": False,
            "classes": ["T1", "T2", "T3", "T4"],
            "metrics": "DESCRIPTIVE expected/intended-tone agreement; no realized-tone gold",
            "neutral_policy": (
                "T5 outside four-class model; report separately, "
                "exclude from numbered agreement denominator"
            ),
            "deterministic": (
                "Unchanged Praat analyzer and frozen Benma acoustic-family adapter "
                "on accepted whole spans; no text inputs."
            ),
            "comparison": (
                "After primary result seal, compare pilot to prior archived "
                "whole-syllable probe and same-context whole pooling; no selection."
            ),
        },
    )
    write_json(destination / "preservation.json", preservation)
    manifest = {
        "schema": "benma-learner-evaluation-release-v1",
        "version": VERSION,
        "frozen_at": now(),
        "evaluation_only": True,
        "training_allowed": False,
        "realized_tone_gold_available": False,
        "counts": counts,
        "adjudication_units": sum(u["adjudication_required"] for u in released),
        "primary_implicated_units": sum(
            u["adjudication_required"] and u["provenance_category"] == NATURAL for u in released
        ),
        "historical_view_overlaps_supplemental_not_additive": True,
        "files": {
            str(p.relative_to(destination)): file_hash(p)
            for p in sorted(destination.rglob("*"))
            if p.is_file()
        },
    }
    write_json(destination / "release-manifest.json", manifest)
    seal = {"manifest_sha256": file_hash(destination / "release-manifest.json"), "version": VERSION}
    write_json(destination / "release-seal.json", seal)
    for path in destination.rglob("*"):
        if path.is_file():
            path.chmod(0o444)
    verify_release(destination)
    return {**seal, "counts": counts, "acceptance": acceptance, "audit": audit}


def verify_release(destination=RELEASE):
    seal = read_json(destination / "release-seal.json")
    if file_hash(destination / "release-manifest.json") != seal["manifest_sha256"]:
        raise ValueError("release_manifest_changed")
    manifest = read_json(destination / "release-manifest.json")
    expected = set(manifest["files"]) | {"release-manifest.json", "release-seal.json"}
    if {str(p.relative_to(destination)) for p in destination.rglob("*") if p.is_file()} != expected:
        raise ValueError("release_inventory_changed")
    for name, sha in manifest["files"].items():
        if file_hash(destination / name) != sha:
            raise ValueError("immutable_release_file_changed:" + name)
    for model in read_json(destination / "inference-config.json")["models"].values():
        if file_hash(model["path"]) != model["sha256"]:
            raise ValueError("frozen_model_changed")
    for u in read_rows(destination / "all-units.jsonl"):
        if file_hash(u["audio"]["reference"]) != u["audio"]["sha256"]:
            raise ValueError("release_audio_changed")
        for original in u["original_sources"]:
            if file_hash(ROOT / original["path"]) != original["sha256"]:
                raise ValueError("original_audio_changed")
    return seal


def future_review_page():
    """New research page; retain the exact original reviewed packet and UI artifacts."""
    root = RUN / "review-with-optional-telemetry"
    render(root, read_json(DEFAULT / "qa/packet.json"))
    return root / "qa/index.html"
