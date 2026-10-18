"""Build new-speaker evidence and a small human QA packet; release only after PASS."""

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_analyze import reconstruct_stage
from aishell3_continue import stable_json, stable_rows
from aishell3_multispeaker_acquire import CONFIG, OLD, ROOT, preserve
from aishell3_round2 import (
    FINAL_DECISIONS,
    SCHEMA,
    WHOLE_DECISIONS,
    export_clip,
    ingest_round2,
    render,
    stable_bytes,
)
from perceptual_tone.aishell3 import attach_prosody, parse_prosody
from perceptual_tone.aishell3_boundaries import POLICY, derive, features, span
from perceptual_tone.aishell3_learning import label_mutation_check
from perceptual_tone.aishell3_multispeaker import (
    make_split,
    split_summary,
    validate_adjudication,
    verify_packet,
)
from perceptual_tone.aishell3_qa import audit_rows, decode
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows


def audit(root):
    preserve(root)
    rows, failures, utterances, lexicon, registry, _config = reconstruct_stage(root, "expansion")
    for name, asset in lexicon["models"].items():
        if file_hash(PACKAGE / ".cache/mfa-work/pretrained_models" / name) != asset["sha256"]:
            raise ValueError("mfa_asset_changed")
    accepted, rejected, summary = audit_rows(rows, utterances, registry, failures)
    if digest(rows) != digest(reconstruct_stage(root, "expansion")[0]):
        raise ValueError("nondeterministic_reconstruction")
    summary["reconstruction_deterministic"] = True
    stable_rows(root / "audit/rejected.jsonl", rejected)
    stable_rows(root / "audit/utterance-failures.jsonl", failures)
    stable_json(root / "audit/automatic-qa.json", summary)
    if summary["automatic_qa"] != "passed":
        raise ValueError("automatic_qa_failed:" + ",".join(summary["blockers"]))
    # Bind prosody separately: the original read-unit annotations remain byte-equivalent.
    wanted = {u["utterance_id"]: u for u in utterances}
    auxiliary, mismatch = {}, []
    source = OLD / "source/hf-label_train-set.txt"
    for line in source.read_text().splitlines():
        if not line.strip() or line.startswith("#") or line.split("|", 1)[0] not in wanted:
            continue
        p = parse_prosody(line)
        try:
            attached = attach_prosody(wanted[p["utterance_id"]], p)
            auxiliary[p["utterance_id"]] = [u["prosody_after"] for u in attached["units"]]
        except ValueError as error:
            mismatch.append({"utterance_id": p["utterance_id"], "reason": str(error)})
    stable_json(
        root / "audit/prosody.json",
        {
            "source_sha256": file_hash(source),
            "exact_matches": auxiliary,
            "not_attached": mismatch,
            "policy": "Auxiliary reporting only; no label or alignment change.",
        },
    )
    cfg = read_json(CONFIG)
    pilot_speakers = {r["speaker_id"] for r in read_rows(OLD / "utterances.jsonl")}
    accepted, split = make_split(accepted, pilot_speakers, cfg["seed"])
    if {part: len(d["speakers"]) for part, d in split["partitions"].items()} != cfg[
        "speaker_partitions"
    ]:
        raise ValueError("speaker_partition_count_changed")
    records, audio, unavailable = [], {}, []
    for row in accepted:
        uid = row["utterance_id"]
        if uid not in audio:
            audio[uid] = decode(row["audio"]["reference"])
        pcm, rate, _ = audio[uid]
        spans = derive(row, rate, len(pcm))
        if not spans["available"]:
            unavailable.append({"example_id": row["example_id"], "reason": spans["reason"]})
            continue
        records.append(
            {
                "dataset_version": cfg["version"],
                "example_id": row["example_id"],
                "original": row,
                "spans": spans,
                "primary_eligible": row["label"] != "T5",
            }
        )
    stable_rows(root / "audit/span-unavailable.jsonl", unavailable)
    if unavailable:
        # Concrete new structures require investigation; never relax the existing projection.
        raise ValueError("new_tone_bearing_structure_unavailable")
    for row in records:
        label_mutation_check(row)
    # Frozen immediately, before QA and every model operation. Never reselect from outcomes.
    stable_json(root / "split.json", split)
    stable_rows(root / "candidates.jsonl", records)
    stable_json(
        root / "candidate-freeze.json",
        {
            "dataset_version": cfg["version"],
            "config_sha256": file_hash(CONFIG),
            "split_sha256": file_hash(root / "split.json"),
            "candidates_sha256": file_hash(root / "candidates.jsonl"),
            "source_acquisition_sha256": file_hash(root / "acquisition.json"),
            "automatic_qa_sha256": file_hash(root / "audit/automatic-qa.json"),
            "primary": sum(r["primary_eligible"] for r in records),
            "neutral": sum(not r["primary_eligible"] for r in records),
            "label_mutation_checks": len(records),
            "status": "FROZEN_CANDIDATES_PENDING_HUMAN_QA",
            "model_evaluation_started": False,
        },
    )
    return {
        "automatic_qa": summary,
        "split": split,
        "freeze": read_json(root / "candidate-freeze.json"),
    }


def packet(root):
    verify_candidates(root)
    records = read_rows(root / "candidates.jsonl")
    cfg = read_json(CONFIG)
    selected, used_speakers = [], set()
    used_initials, used_finals = set(), set()
    # Six per tone, including shortest and longest spans; prefer 24 distinct speakers.
    for tone in ("T3", "T1", "T2", "T4"):
        choices = [r for r in records if r["original"]["label"] == tone]
        for mode in ("short", "long", "variety", "variety", "variety", "variety"):

            def rank(r, mode=mode):
                o, s = r["original"], r["spans"]["tone_bearing_pooling_span"]
                f = features(o)
                duration = s["end_sample"] - s["start_sample"]
                order = (
                    duration
                    if mode == "short"
                    else -duration
                    if mode == "long"
                    else -(
                        (f["initial_class"] not in used_initials)
                        + (f["final_class"] not in used_finals)
                    )
                )
                return (
                    o["speaker_id"] in used_speakers,
                    order,
                    digest([cfg["seed"], r["example_id"]]),
                )

            row = min(choices, key=rank)
            selected.append(row)
            choices.remove(row)
            used_speakers.add(row["original"]["speaker_id"])
            f = features(row["original"])
            used_initials.add(f["initial_class"])
            used_finals.add(f["final_class"])
    if len(selected) != cfg["qa_items"]:
        raise ValueError("qa_size_changed")
    folder = root / "spot-check"
    items = []
    for i, record in enumerate(selected, 1):
        row, spans = record["original"], record["spans"]
        pcm, rate, _ = decode(row["audio"]["reference"])
        bounds = {
            "target": spans["playback_read_unit"],
            "context": spans["context"],
            "final": spans["tone_bearing_pooling_span"],
            "utterance": span(0, len(pcm) / rate, rate, len(pcm)),
        }
        playback = {
            view: export_clip(folder, f"audio/item-{i:02d}-{view}.wav", pcm, rate, value)
            for view, value in bounds.items()
        }
        bound = {
            "example_id": record["example_id"],
            "original": row,
            "spans": spans,
            "playback": playback,
        }
        items.append(
            {
                "item": f"item-{i:02d}",
                "row": bound,
                "item_sha256": digest(bound),
                "playback": playback,
            }
        )
    payload = {
        "schema": SCHEMA,
        "policy": POLICY,
        "decisions": list(WHOLE_DECISIONS),
        "final_decisions": list(FINAL_DECISIONS),
        "items": items,
        "purpose": "New-speaker ownership spot check; not tone correctness.",
        "candidate_freeze_sha256": file_hash(root / "candidate-freeze.json"),
    }
    document = {**payload, "packet_sha256": digest(payload)}
    stable_json(folder / "packet.json", document)
    html = render(document).replace("playback QA · Round 2".encode(), b"new-speaker spot check")
    stable_bytes(folder / "index.html", html)
    verify_packet(document, folder, file_hash)
    summary = {
        "items": len(items),
        "speakers": sorted(used_speakers),
        "tone_counts": dict(Counter(r["original"]["label"] for r in selected)),
        "initial_classes": sorted(used_initials),
        "final_classes": sorted(used_finals),
        "packet_sha256": document["packet_sha256"],
        "human_result": "PENDING",
        "human_decisions_inferred": False,
        "training_run": False,
    }
    stable_json(folder / "summary.json", summary)
    return summary


def verify_candidates(root):
    freeze = read_json(root / "candidate-freeze.json")
    for filename, key in (
        ("split.json", "split_sha256"),
        ("candidates.jsonl", "candidates_sha256"),
        ("acquisition.json", "source_acquisition_sha256"),
        ("audit/automatic-qa.json", "automatic_qa_sha256"),
    ):
        if file_hash(root / filename) != freeze[key]:
            raise ValueError("candidate_freeze_changed:" + filename)
    if file_hash(CONFIG) != freeze["config_sha256"]:
        raise ValueError("frozen_method_config_changed")
    rows = read_rows(root / "candidates.jsonl")
    old_speakers = {u["speaker_id"] for u in read_rows(OLD / "utterances.jsonl")}
    split_summary(
        [r["original"] for r in rows], read_json(root / "split.json")["assignments"], old_speakers
    )
    for r in rows:
        if file_hash(r["original"]["audio"]["reference"]) != r["original"]["audio"]["sha256"]:
            raise ValueError("source_audio_changed")
        label_mutation_check(r)
    return freeze


def release(root, decisions):
    freeze = verify_candidates(root)
    preserve(root)
    folder = root / "spot-check"
    packet = read_json(folder / "packet.json")
    verify_packet(packet, folder, file_hash)
    qa = ingest_round2(folder, decisions, folder / "developer-decisions.jsonl")
    candidates = read_rows(root / "candidates.jsonl")
    adjudication = read_json(root / "adjudication/adjudication.json")
    if (
        adjudication["raw_export_sha256"] != file_hash(decisions)
        or adjudication["packet_sha256"] != packet["packet_sha256"]
        or adjudication["candidate_freeze_sha256"] != file_hash(root / "candidate-freeze.json")
    ):
        raise ValueError("adjudication_evidence_mismatch")
    quarantines = validate_adjudication(
        adjudication, read_json(decisions)["reviews"], {r["example_id"] for r in candidates}
    )
    rows = [r for r in candidates if r["example_id"] not in quarantines]
    assignments = read_json(root / "split.json")["assignments"]
    split = {
        "assignments": assignments,
        "original_split_sha256": file_hash(root / "split.json"),
        "policy": "Original speaker assignments unchanged; documented integrity quarantines only.",
        **split_summary(
            [r["original"] for r in rows],
            assignments,
            {u["speaker_id"] for u in read_rows(OLD / "utterances.jsonl")},
        ),
    }
    output = root / "releases" / read_json(CONFIG)["version"]
    if (output / "release.json").exists():
        from aishell3_release import verify_release

        return verify_release(output)
    output.mkdir(parents=True, exist_ok=False)
    stable_rows(output / "manifest.jsonl", rows)
    stable_rows(output / "primary.jsonl", [r for r in rows if r["primary_eligible"]])
    stable_rows(output / "neutral.jsonl", [r for r in rows if not r["primary_eligible"]])
    evidence = {
        "original-split.json": root / "split.json",
        "candidate-freeze.json": root / "candidate-freeze.json",
        "acquisition.json": root / "acquisition.json",
        "speaker-registry.jsonl": root / "speaker-registry.jsonl",
        "automatic-quarantines.jsonl": root / "audit/rejected.jsonl",
        "human-quarantines.jsonl": root / "adjudication/quarantined.jsonl",
        "adjudication.json": root / "adjudication/adjudication.json",
        "input-integrity.json": root / "preflight/validation.json",
        "pronunciation-corrections.json": PACKAGE
        / "configs/aishell3-multispeaker-pronunciations.json",
        "automatic-qa.json": root / "audit/automatic-qa.json",
        "prosody.json": root / "audit/prosody.json",
        "qa-packet.json": folder / "packet.json",
        "qa-decisions.jsonl": folder / "developer-decisions.jsonl",
        "qa-export.json": decisions,
        "alignment-config.json": PACKAGE / "configs/aishell3.json",
        "method-config.json": CONFIG,
        "lexicon.json": root / "expansion/lexicon-audit.json",
        "historical-preservation.json": root / "historical-preservation.json",
    }
    for name, path in evidence.items():
        shutil.copyfile(path, output / name)
    stable_json(output / "split.json", split)
    for name in ("aishell3.py", "aishell3_alignment.py", "aishell3_boundaries.py"):
        shutil.copyfile(PACKAGE / "perceptual_tone" / name, output / name)
    automatic = read_rows(root / "audit/rejected.jsonl")
    stable_rows(
        output / "quarantined.jsonl",
        [{"stage": "automatic_alignment", "record": r} for r in automatic]
        + [
            {"stage": "human_adjudication", **r}
            for r in read_rows(root / "adjudication/quarantined.jsonl")
        ],
    )
    info = {
        "dataset_version": freeze["dataset_version"],
        "status": "READY_FOR_FIXED_METHOD_EXPERIMENTS",
        "primary_numbered": sum(r["primary_eligible"] for r in rows),
        "neutral": sum(not r["primary_eligible"] for r in rows),
        "quarantined": len(automatic) + len(quarantines),
        "manifest_sha256": file_hash(output / "manifest.jsonl"),
        "pooling_version": POLICY,
        "qa": qa,
        "qa_gate": adjudication["gate"],
        "qa_policy_override": (
            "Explicit developer follow-up: 22 direct final PASS plus adjudicated "
            "PASS_AS_IS/quarantines supersedes the initial all-PASS requirement; "
            "frozen model method unchanged."
        ),
        "adjudication_sha256": adjudication["adjudication_sha256"],
        "training_started": False,
        "files": {p.name: file_hash(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    stable_json(output / "release.json", info)
    return info


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["audit", "packet", "release", "verify"])
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--decisions", type=Path)
    a = p.parse_args()
    if a.action == "release" and not a.decisions:
        p.error("release requires --decisions exported after explicit human playback")
    result = {
        "audit": lambda: audit(a.root),
        "packet": lambda: packet(a.root),
        "release": lambda: release(a.root, a.decisions),
        "verify": lambda: verify_candidates(a.root),
    }[a.action]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
