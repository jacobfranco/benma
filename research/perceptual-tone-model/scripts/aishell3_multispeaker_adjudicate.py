"""Preserve human decisions; adjudicate three ownership findings before any ML output."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json, stable_rows
from aishell3_multispeaker_acquire import ROOT
from aishell3_round2 import ingest_round2
from perceptual_tone.aishell3_alignment import textgrid
from perceptual_tone.aishell3_boundaries import TONES, derive
from perceptual_tone.aishell3_qa import decode
from perceptual_tone.common import digest, file_hash, read_json, read_rows

QUARANTINE = {"aishell3:SSB03420076:12", "aishell3:SSB03230044:5"}
WHOLE_ONLY = "aishell3:SSB05650015:10"


def adjudicate(root=ROOT):
    folder = root / "adjudication"
    raw = folder / "raw-developer-export.json"
    ingested = ingest_round2(
        root / "spot-check", raw, root / "spot-check/developer-decisions.jsonl"
    )
    if ingested["final_decisions"] != {"PASS": 22, "CLIPPED": 2} or ingested["whole_unit_review"][
        "decisions"
    ] != {"PASS": 23, "BOTH": 1}:
        raise ValueError("unexpected_human_review_inventory")
    reviews = {r["example_id"]: r for r in read_json(raw)["reviews"]}
    packet = read_json(root / "spot-check/packet.json")
    items = {i["row"]["example_id"]: i for i in packet["items"]}
    records = read_rows(root / "candidates.jsonl")
    by_id = {r["example_id"]: r for r in records}
    output = []
    for key in sorted(QUARANTINE | {WHOLE_ONLY}):
        r, item = by_id[key], items[key]
        o, s = r["original"], r["spans"]
        pcm, rate, _ = decode(o["audio"]["reference"])
        if derive(o, rate, len(pcm)) != s:
            raise ValueError("derivation_changed")
        tiers = textgrid(
            (
                root / "expansion/aligned" / o["speaker_id"] / (o["utterance_id"] + ".TextGrid")
            ).read_text()
        )
        final = s["tone_bearing_pooling_span"]
        phones = [o["aligned_phones"][i] for i in s["owned_phone_indices"]]
        ownership = []
        for p in phones:
            owners = [w for w in tiers["words"] if w[0] <= p["start"] and p["end"] <= w[1] and w[2]]
            if len(owners) != 1 or owners[0][:2] != (o["start"], o["end"]):
                raise ValueError("systematic_phone_ownership_defect")
            ownership.append({"phone": p, "owner": owners[0]})
        for view, bounds in (
            ("target", s["playback_read_unit"]),
            ("final", final),
            ("context", s["context"]),
        ):
            media = item["playback"][view]
            actual, actual_rate, _ = decode(root / "spot-check" / media["reference"])
            expected = pcm[bounds["start_sample"] : bounds["end_sample"]]
            if actual_rate != rate or not np.array_equal(actual, expected):
                raise ValueError("systematic_export_defect")
        if key == "aishell3:SSB03420076:12":
            diagnosis = (
                "E: uncertain acoustic start ownership. Consecutive /y/ vowels yu2->yu3 are "
                "continuous in the spectrogram; MFA assigns 30 ms to preceding yu2 and 490 ms "
                "to target yu3. This does not independently establish their acoustic boundary. "
                "The human note suggests excess initial material, not missing target material. "
                "No onset, medial or neighboring MFA phone enters the pool. Coarticulation "
                "and an early MFA boundary cannot be distinguished confidently; quarantine."
            )
        elif key == "aishell3:SSB03230044:5":
            diagnosis = (
                "E: uncertain acoustic start ownership, with possible A (preceding-vowel tail). "
                "The beginning of the 480 ms /i/ interval shows continuing periodic energy "
                "from the /ow/ transition, followed by lower energy and a later stronger /i/ "
                "region. This is compatible with the developer's excess-start observation, "
                "but a spectrogram cannot independently certify read-unit identity. "
                "No target onset/medial is represented; no neighbor MFA phone or export "
                "offset is included. Relevant target clipping is not established; quarantine."
            )
        else:
            diagnosis = (
                "PASS_AS_IS for tone-bearing use. Whole target is 90 ms /p-w/ onset plus "
                "30 ms /u/ nucleus. Pooling excludes the onset and contains exactly the "
                "target-owned /u/, with no neighboring phone. Human explicitly passed this "
                "final. The whole-target BOTH finding remains a real playback objection; "
                "no reconstruction or export defect is found. Poor/fuzzy whole-unit acoustic "
                "boundaries do not override the intact structurally owned, human-passed final."
            )
        output.append(
            {
                "example_id": key,
                "speaker_id": o["speaker_id"],
                "utterance_id": o["utterance_id"],
                "partition": o["partition"],
                "hanzi": o["hanzi"],
                "pinyin": o["corpus_pinyin"],
                "actual_reading_tone": o["label"],
                "previous": o["preceding"],
                "next": o["following"],
                "whole_seconds": [o["start"], o["end"]],
                "pooling_seconds": [final["start_seconds"], final["end_seconds"]],
                "pooling_duration_seconds": (final["end_sample"] - final["start_sample"]) / rate,
                "pooling_sample_bounds": [final["start_sample"], final["end_sample"]],
                "context_seconds": [s["context"]["start_seconds"], s["context"]["end_seconds"]],
                "mfa_phones": o["aligned_phones"],
                "tone_bearing_phones": phones,
                "phone_ownership_trace": ownership,
                "first_pool_phone_role": "nucleus",
                "neighbor_phones_in_pool": 0,
                "exported_samples_exact": True,
                "whole_and_final_wav_byte_identical": item["playback"]["target"]["sha256"]
                == item["playback"]["final"]["sha256"],
                "original_human_review": reviews[key],
                "classification": "UNCERTAIN_ACOUSTIC_START_OWNERSHIP"
                if key in QUARANTINE
                else "TARGET_OWNED_FINAL_HUMAN_PASS",
                "outcome": "QUARANTINE_UNIT" if key in QUARANTINE else "PASS_AS_IS",
                "diagnosis": diagnosis,
                "visual_evidence": {
                    "path": f"plots/{item['item']}.png",
                    "sha256": file_hash(folder / f"plots/{item['item']}.png"),
                },
                "evidence_limit": (
                    "Phone ownership is structural; developer supplied auditory judgment. "
                    "No claimed independent assistant listening or manual timestamp change."
                ),
            }
        )
    # Document descriptive scope after the three-item trace. No new filtering rule.
    primary = [r for r in records if r["primary_eligible"]]
    single = [r for r in primary if len(r["original"]["aligned_phones"]) == 1]
    long_single = [
        r for r in single if r["original"]["end"] - r["original"]["start"] >= 0.48 - 1e-9
    ]
    identical_neighbor = []
    for r in single:
        o = r["original"]
        previous = by_id.get(f"aishell3:{o['utterance_id']}:{o['index'] - 1}")
        if previous and previous["original"]["aligned_phones"][-1]["phone"].translate(TONES) == o[
            "aligned_phones"
        ][0]["phone"].translate(TONES):
            identical_neighbor.append(r["example_id"])
    impact = {
        "primary_units_scoped": len(primary),
        "proven_derivation_or_export_defects": 0,
        "same_single_phone_whole_equals_final_pattern": len(single),
        "single_phone_at_least_480ms": [r["example_id"] for r in long_single],
        "same_segment_preceding_phone_pattern": identical_neighbor,
        "interpretation": (
            "Descriptive structural similarities, not established acoustic failures. "
            "No global exclusion or retuning from these patterns."
        ),
        "structural_preflight_sha256": file_hash(root / "preflight/validation.json"),
    }
    payload = {
        "schema": "aishell3-multispeaker-human-adjudication-v1",
        "raw_export_sha256": file_hash(raw),
        "packet_sha256": packet["packet_sha256"],
        "candidate_freeze_sha256": file_hash(root / "candidate-freeze.json"),
        "items": output,
        "full_corpus_impact": impact,
        "quarantined_example_ids": sorted(QUARANTINE),
        "systematic_bug_found": False,
        "gate": "SATISFIED_WITH_EXPLICIT_QUARANTINES",
        "gate_basis": (
            "22 direct final PASS including the whole-target outlier, plus two quarantines; "
            "raw decisions unchanged."
        ),
        "model_predictions_inspected": False,
        "timing_edits": 0,
    }
    payload["adjudication_sha256"] = digest(payload)
    stable_json(folder / "adjudication.json", payload)
    stable_rows(
        folder / "quarantined.jsonl",
        [
            {
                "record": by_id[key],
                "reason": "human_final_nonpass_unresolved_start_acoustic_ownership",
                "adjudication_sha256": payload["adjudication_sha256"],
            }
            for key in sorted(QUARANTINE)
        ],
    )
    return payload


if __name__ == "__main__":
    print(json.dumps(adjudicate(), ensure_ascii=False, indent=2))
