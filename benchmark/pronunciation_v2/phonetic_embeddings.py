"""Optional frozen, local-only representations of blind crops; never imports a trained head."""

import argparse
import json
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import torch
from features import encode_waveforms, freeze, state_digest
from phonetic_evidence import decode, dump, load_manifest, sha, verify_seal
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model


def extract_embeddings(manifest_path, packet, snapshot, destination):
    seal = verify_seal(packet)
    manifest = load_manifest(manifest_path)
    if not snapshot.is_dir() or not (snapshot / "pytorch_model.bin").is_file():
        raise FileNotFoundError("Local model cache unavailable; skip, never download")
    if destination.exists():
        raise FileExistsError("Refusing embedding overwrite")
    lock = json.loads(
        Path("docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec/checkpoint.json").read_text()
    )
    if snapshot.name != lock["revision"] or any(
        sha(snapshot / name) != lock["files_sha256"][name]
        for name in ("pytorch_model.bin", "config.json", "preprocessor_config.json")
    ):
        raise ValueError("Cached encoder differs from the prior checkpoint receipt")
    torch.set_num_threads(4)
    torch.manual_seed(20260929)
    torch.use_deterministic_algorithms(True)
    model, loading = Wav2Vec2Model.from_pretrained(
        snapshot,
        local_files_only=True,
        attn_implementation="eager",
        output_loading_info=True,
    )
    if loading["missing_keys"] or loading["mismatched_keys"] or loading["error_msgs"]:
        raise RuntimeError("Incomplete acoustic encoder")
    model = freeze(model)
    processor = Wav2Vec2FeatureExtractor.from_pretrained(snapshot, local_files_only=True)
    before = state_digest(model)
    results, ids, lengths = [], [], []
    decoded = {}
    for r in manifest["regions"]:
        if sha(r["audio_path"]) != r["audio_sha256"]:
            raise ValueError("Audio changed")
        if r["audio_path"] not in decoded:
            decoded[r["audio_path"]] = decode(r["audio_path"])
        start, end = (round(r["span"][k] * 16) for k in ("start_ms", "end_ms"))
        crop = decoded[r["audio_path"]][start:end]
        evidence = json.loads((packet / r["id"] / "evidence.json").read_text())
        if evidence["status"] != "measured" or len(crop) < 400:
            continue
        feature = encode_waveforms(model, processor, [crop], layers=(6,))[6][0]
        repeat = encode_waveforms(model, processor, [crop], layers=(6,))[6][0]
        if not np.array_equal(feature, repeat):
            raise RuntimeError("Nondeterministic frozen features")
        results.append(feature)
        ids.append(r["id"])
        lengths.append(int(model._get_feat_extract_output_lengths(len(crop))))
    after = state_digest(model)
    if before != after or any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Encoder changed or received gradients")
    destination.mkdir(parents=True)
    np.savez_compressed(destination / "embeddings.npz", ids=ids, block6_mean=np.stack(results))
    dump(
        destination / "receipt.json",
        {
            "model": "facebook/wav2vec2-base",
            "revision": snapshot.name,
            "checkpoint_sha256": sha(snapshot / "pytorch_model.bin"),
            "ids": ids,
            "hidden_frames": lengths,
            "dimensions": model.config.hidden_size,
            "block": 6,
            "pooling": "mean_all_valid_hidden_frames_one_unpadded_crop",
            "device": "cpu",
            "dtype": "float32",
            "normalization": processor.to_dict(),
            "every_crop_repeat_bitwise_equal": True,
            "no_gradients": True,
            "state_sha256_before": before,
            "state_sha256_after": after,
            "packet_seal_sha256": seal,
            "loading_info": loading,
            "semantics": "future_model_input_not_interpretable_phone_evidence",
        },
    )
    print(f"Frozen block-6 embeddings: {len(ids)} x {model.config.hidden_size}; repeat equal")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    extract_embeddings(args.manifest, args.packet, args.snapshot, args.output)


if __name__ == "__main__":
    main()
