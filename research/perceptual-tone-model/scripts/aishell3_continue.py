"""Audit saved AISHELL-3 boundaries, scale existing audio and ingest human QA.

The continue command releases a verified dataset; it never starts training.
"""

import argparse
import json
import sys
import wave
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_analyze import reconstruct_stage
from perceptual_tone.aishell3 import (
    alignment_token,
    g2p_spelling,
    parse_speakers,
    size_balanced_speaker_split,
)
from perceptual_tone.aishell3_qa import audit_rows, dataset_gate, validate_reviews
from perceptual_tone.common import (
    PACKAGE,
    digest,
    file_hash,
    read_json,
    read_rows,
    write_json,
    write_rows,
)
from perceptual_tone.manifest import verify_baseline


def stable_json(path, value):
    if path.exists():
        if read_json(path) != value:
            raise ValueError(f"Existing artifact differs: {path}")
    else:
        write_json(path, value)


def stable_rows(path, rows):
    if path.exists():
        if read_rows(path) != rows:
            raise ValueError(f"Existing artifact differs: {path}")
    else:
        write_rows(path, rows)


def audit(root, *, scaled=False):
    rows, failures, utterances, lexicon, registry, _ = reconstruct_stage(root)
    acquisition = read_json(root / "acquisition.json")
    for chunk in acquisition["chunks"]:
        if file_hash(root / "source" / chunk["name"]) != chunk["sha256"]:
            raise ValueError("source_prefix_chunk_changed")
    for member in acquisition["members"]:
        if (
            not member["member"].endswith(".wav")
            and file_hash(root / "extracted" / member["member"]) != member["sha256"]
        ):
            raise ValueError("source_metadata_changed")
    raw_registry = parse_speakers((root / "extracted/spk-info.txt").read_text(), {})
    for speaker, data in registry.items():
        if any(
            data[k] != raw_registry[speaker][k]
            for k in ("speaker_id", "age_group", "gender", "accent", "metadata_line")
        ):
            raise ValueError("speaker_registry_changed")
    for name, spec in lexicon["models"].items():
        if file_hash(PACKAGE / ".cache/mfa-work/pretrained_models" / name) != spec["sha256"]:
            raise ValueError("pinned_mfa_asset_changed")
    if rows != read_rows(root / "pilot/audit/candidates.jsonl"):
        raise ValueError("Pilot reconstruction changed")
    _, pilot_rejected, pilot = audit_rows(rows, utterances, registry, failures)
    if pilot_rejected:
        raise ValueError("Pilot has new audio-integrity rejections")
    if digest(rows) != digest(reconstruct_stage(root)[0]):
        raise ValueError("Nondeterministic reconstruction")
    pilot["reconstruction_deterministic"] = True
    stable_json(root / "continuation/pilot-automatic-qa.json", pilot)
    if not scaled:
        return pilot
    if pilot["automatic_qa"] != "passed":
        raise ValueError("Pilot automatic QA prevents scaling")
    extra, extra_failures, extra_utterances, _, _, _ = reconstruct_stage(root, "expansion")
    if digest(extra) != digest(reconstruct_stage(root, "expansion")[0]):
        raise ValueError("Nondeterministic expansion reconstruction")
    if {u["utterance_id"] for u in utterances} & {u["utterance_id"] for u in extra_utterances}:
        raise ValueError("Pilot must not be realigned")
    all_rows = rows + extra
    unit_counts = Counter()
    for utterance in utterances + extra_utterances:
        unit_counts[utterance["speaker_id"]] += len(utterance["units"])
    partitions = size_balanced_speaker_split(unit_counts)
    all_rows = [{**r, "partition": partitions[r["speaker_id"]]} for r in all_rows]
    accepted, rejected, summary = audit_rows(
        all_rows, utterances + extra_utterances, registry, failures + extra_failures
    )
    summary["reconstruction_deterministic"] = True
    summary["existing_pilot_utterances_reused"] = len(utterances)
    summary["new_utterances_aligned"] = len(extra_utterances) - len(extra_failures)
    summary["new_units_attempted"] = sum(len(u["units"]) for u in extra_utterances)
    summary["split_policy"] = (
        "fixed_10_3_3_speakers_minimum_squared_unit_count_error_to_60_20_20_seed_20261015_no_labels_or_metrics"
    )
    summary["coverage_gate"] = dataset_gate(accepted)
    # Neutral remains in the audited data but is held out of the first four-class run.
    core = [r for r in accepted if r["label"] != "T5"]
    summary["first_experiment_classes"] = ["T1", "T2", "T3", "T4"]
    summary["core_units"] = len(core)
    summary["core_coverage_gate"] = dataset_gate(core)
    summary["neutral_policy"] = (
        "Retained in audit; excluded from first model for sparse held-out coverage."
    )
    stable_rows(root / "continuation/scaled-candidates.jsonl", accepted)
    stable_rows(root / "continuation/scaled-rejected.jsonl", rejected)
    stable_rows(root / "continuation/scaled-utterance-failures.jsonl", failures + extra_failures)
    stable_json(root / "continuation/scaled-automatic-qa.json", summary)
    return summary


def prepare_expansion(root):
    pilot = audit(root)
    if pilot["automatic_qa"] != "passed":
        raise ValueError("Pilot automatic QA prevents scaling")
    previous = {u["utterance_id"] for u in read_rows(root / "pilot/utterances.jsonl")}
    utterances = [
        u for u in read_rows(root / "utterances.jsonl") if u["utterance_id"] not in previous
    ]
    stage = root / "expansion"
    stage.mkdir(exist_ok=False)
    for u in utterances:
        folder = stage / "corpus-expansion" / u["speaker_id"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / u["filename"]
        with wave.open(u["audio"]["reference"], "rb") as source:
            params, pcm = source.getparams(), source.readframes(source.getnframes())
        with wave.open(str(path), "wb") as dest:
            dest.setparams(params)
            dest.writeframes(pcm)
        u["alignment_audio"] = {
            "reference": str(path.resolve()),
            "sha256": file_hash(path),
            "pcm_sha256": u["pcm_sha256"],
            "conversion": "container_rewrite_only_original_pcm44100",
        }
        (folder / (u["utterance_id"] + ".lab")).write_text(
            " ".join(alignment_token(unit) for unit in u["units"]) + "\n"
        )
    spellings = {
        p: g2p_spelling(p)
        for p in sorted({u["corpus_pinyin"] for r in utterances for u in r["units"]})
    }
    (stage / "pinyin.txt").write_text("\n".join(sorted(set(spellings.values()))) + "\n")
    write_json(stage / "g2p-spelling.json", spellings)
    write_rows(stage / "utterances.jsonl", utterances)
    return {
        "new_utterances": len(utterances),
        "new_units": sum(len(u["units"]) for u in utterances),
        "pinyin_tokens": len(spellings),
        "pilot_untouched": True,
    }


def verified_packet(root):
    packet = read_json(root / "pilot/audit/review/packet.json")
    if packet["packet_sha256"] != digest({k: v for k, v in packet.items() if k != "packet_sha256"}):
        raise ValueError("packet_content_hash_mismatch")
    candidates = {r["example_id"]: r for r in read_rows(root / "pilot/audit/candidates.jsonl")}
    folder = root / "pilot/audit/review"
    original_items = read_rows(folder / "items.jsonl")
    if [
        {k: item[k] for k in ("item", "row", "playback")} for item in packet["items"]
    ] != original_items:
        raise ValueError("representative_review_sample_changed")
    for item in packet["items"]:
        if item["row"] != candidates.get(item["row"]["example_id"]) or item[
            "item_sha256"
        ] != digest(item["row"]):
            raise ValueError("packet_candidate_changed")
        for media in [*item["playback"].values(), item["plot"]]:
            path = (folder / media["reference"]).resolve()
            if not path.is_relative_to(folder.resolve()) or file_hash(path) != media["sha256"]:
                raise ValueError("packet_media_changed")
    return packet


def ingest(root, source, destination):
    packet = verified_packet(root)
    raw = read_json(source)
    if raw.get("schema") != packet["schema"] or raw.get("packet_sha256") != packet["packet_sha256"]:
        raise ValueError("review_packet_hash_mismatch")
    normalized, status = validate_reviews(packet["items"], raw.get("reviews", []), complete=True)
    normalized = [{**r, "packet_sha256": packet["packet_sha256"]} for r in normalized]
    stable_rows(destination, normalized)
    return status


def release(root, reviews, output):
    # Recompute from original media/TextGrids, not an editable summary's passed flag.
    summary = audit(root, scaled=True)
    packet = verified_packet(root)
    decisions = read_rows(reviews)
    if any(r.get("packet_sha256") != packet["packet_sha256"] for r in decisions):
        raise ValueError("reviews_bound_to_different_packet")
    _, human = validate_reviews(packet["items"], decisions, complete=True)
    if human["status"] != "passed":
        raise ValueError(
            "Human playback reported an issue; investigate and quarantine before release"
        )
    if summary["automatic_qa"] != "passed" or not summary["core_coverage_gate"]["passed"]:
        raise ValueError("Automatic or coverage gate failed")
    verify_baseline()
    rows = [
        r for r in read_rows(root / "continuation/scaled-candidates.jsonl") if r["label"] != "T5"
    ]
    stable_rows(output / "dataset.jsonl", rows)
    result = {
        "status": "READY_FOR_TRAINING",
        "training_run": False,
        "units": len(rows),
        "dataset_sha256": file_hash(output / "dataset.jsonl"),
        "human_playback": human,
        "reviews_sha256": file_hash(reviews),
        "packet_sha256": packet["packet_sha256"],
        "automatic_qa": summary,
    }
    stable_json(output / "gate.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["audit-pilot", "prepare-expansion", "audit-scaled", "ingest", "continue"]
    )
    parser.add_argument("--root", type=Path, default=PACKAGE / "data/generated/aishell3")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "audit-pilot":
        result = audit(args.root)
    elif args.action == "prepare-expansion":
        result = prepare_expansion(args.root)
    elif args.action == "audit-scaled":
        result = audit(args.root, scaled=True)
    elif args.action == "ingest":
        if not args.input or not args.output:
            parser.error("ingest requires --input (browser JSON) and --output (normalized JSONL)")
        result = ingest(args.root, args.input, args.output)
    else:
        if not args.reviews or not args.output:
            parser.error(
                "continue requires --reviews (normalized JSONL) and --output (release directory)"
            )
        result = release(args.root, args.reviews, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
