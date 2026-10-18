"""Verify new-speaker source, alignment, split, audio, QA and frozen-model contracts."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json
from aishell3_multispeaker import verify_candidates
from aishell3_multispeaker_acquire import OLD, ROOT, preserve
from perceptual_tone.aishell3 import parse_speakers
from perceptual_tone.aishell3_embeddings import PAD, input_audio
from perceptual_tone.aishell3_learning import audio_contract, label_mutation_check
from perceptual_tone.aishell3_multispeaker import verify_packet
from perceptual_tone.aishell3_qa import decode
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows
from perceptual_tone.embeddings import frame_centers


def verify(root=ROOT):
    freeze = verify_candidates(root)
    history = preserve(root)
    rows = read_rows(root / "candidates.jsonl")
    original_speakers = parse_speakers((root / "source/spk-info.txt").read_text(), {})
    registry = read_rows(root / "speaker-registry.jsonl")
    for r in registry:
        original = original_speakers[r["speaker_id"]]
        if any(
            r[k] != original[k]
            for k in ("speaker_id", "gender", "accent", "age_group", "metadata_line")
        ):
            raise ValueError("new_speaker_provenance_changed")
        if r["metadata_provenance"]["sha256"] != file_hash(root / "source/spk-info.txt"):
            raise ValueError("speaker_metadata_hash_changed")
    old_units = read_rows(OLD / "utterances.jsonl")
    old_pcm = {u["pcm_sha256"] for u in old_units}
    old_ids = {u["utterance_id"] for u in old_units}
    for row in rows:
        if row["original"]["pcm_sha256"] in old_pcm or row["original"]["utterance_id"] in old_ids:
            raise ValueError("pilot_source_reused")
    by_id = {r["example_id"]: r for r in rows}
    packet = read_json(root / "spot-check/packet.json")
    verify_packet(packet, root / "spot-check", file_hash)
    for item in packet["items"]:
        candidate = by_id[item["row"]["example_id"]]
        if any(item["row"][k] != candidate[k] for k in ("original", "spans")):
            raise ValueError("qa_not_bound_to_frozen_candidate")
    spec = read_json(PACKAGE / "configs/encoders.json")["chinese_hubert_base"]
    encoder_config = (
        PACKAGE
        / ".cache/huggingface"
        / ("models--" + spec["model_id"].replace("/", "--"))
        / "snapshots"
        / spec["revision"]
        / "config.json"
    )
    geometry = SimpleNamespace(**read_json(encoder_config))
    audio, derivative_parts, resampled_parts, frame_counts = {}, {}, {}, []
    for row in rows:
        o, spans = row["original"], row["spans"]
        if o["utterance_id"] not in audio:
            audio[o["utterance_id"]] = decode(o["audio"]["reference"])
            grid = root / "expansion/aligned" / o["speaker_id"] / (o["utterance_id"] + ".TextGrid")
            if file_hash(grid) != o["alignment_diagnostics"]["textgrid_sha256"]:
                raise ValueError("original_mfa_alignment_changed")
        pcm, rate, _ = audio[o["utterance_id"]]
        if digest(o) != spans["original_row_sha256"]:
            raise ValueError("original_span_evidence_changed")
        if spans["original_mfa_phones"] != o["aligned_phones"]:
            raise ValueError("original_phone_evidence_changed")
        for key in ("playback_read_unit", "context", "tone_bearing_pooling_span"):
            s = spans[key]
            if s["sample_rate_hz"] != rate or not 0 <= s["start_sample"] < s["end_sample"] <= len(
                pcm
            ):
                raise ValueError("invalid_source_sample_bounds")
            clip = pcm[s["start_sample"] : s["end_sample"]]
            if not np.any(clip):
                raise ValueError("silent_derivative")
            h = hashlib.sha256(clip.tobytes()).hexdigest()
            if derivative_parts.setdefault(h, o["partition"]) != o["partition"]:
                raise ValueError("precise_derivative_audio_leakage")
        label_mutation_check(row)
        values, target, _ = input_audio(
            audio_contract(row), "context", root / "preflight/canonical"
        )
        h = hashlib.sha256(values.tobytes()).hexdigest()
        if resampled_parts.setdefault(h, o["partition"]) != o["partition"]:
            raise ValueError("resampled_context_leakage")
        pool = values[target[0] : target[1]]
        h = hashlib.sha256(pool.tobytes()).hexdigest()
        if resampled_parts.setdefault(h, o["partition"]) != o["partition"]:
            raise ValueError("resampled_pool_leakage")
        count = len(values)
        for kernel, stride in zip(geometry.conv_kernel, geometry.conv_stride, strict=True):
            count = (count - kernel) // stride + 1
        centers = frame_centers(geometry, count)
        owned = int(((centers >= target[0]) & (centers < target[1])).sum())
        if owned == 0:
            raise ValueError("no_encoder_frame_center_in_frozen_pool")
        frame_counts.append(owned)
    result = {
        "status": "PASS_PRE_EVALUATION_INTEGRITY",
        "history": history,
        "frozen_candidate_manifest_sha256": freeze["candidates_sha256"],
        "speaker_provenance_records_verified": len(registry),
        "utterance_audio_and_alignments": len(audio),
        "source_derivatives_verified": len(rows) * 3,
        "resampled_context_and_pool_checks": len(rows) * 2,
        "label_mutation_checks": len(rows),
        "qa_items_bound_to_candidates": len(packet["items"]),
        "encoder_frame_geometry": {
            "config_sha256": file_hash(encoder_config),
            "edge_padding": PAD,
            "minimum_owned_frames": min(frame_counts),
            "maximum_owned_frames": max(frame_counts),
        },
        "model_inference": False,
        "training": False,
        "human_qa_inferred": False,
    }
    stable_json(root / "preflight/validation.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
