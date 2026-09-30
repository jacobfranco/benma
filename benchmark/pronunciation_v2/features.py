"""Frozen waveform-only features; one clip per forward avoids group-norm padding effects."""

import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

import numpy as np
import torch
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model

LAYERS = (4, 6, 8)
MODEL_ID = "facebook/wav2vec2-base"
PREPROCESSING = {
    "sample_rate": 16000,
    "channels": 1,
    "decode": "ffmpeg float32 PCM",
    "trim": False,
    "augmentation": False,
    "waveform_normalization": "checkpoint feature extractor",
    "batch_size": 1,
    "attention_mask_to_encoder": False,
    "pooling": "mean of valid hidden frames only; no padded waveform in encoder",
    "dtype": "float32",
    "attention_implementation": "eager",
}


def load_waveform(path):
    raw = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-",
        ],
        timeout=30,
    )
    values = np.frombuffer(raw, dtype="<f4").copy()
    if len(values) < 400 or not np.isfinite(values).all():
        raise ValueError("Invalid or too short waveform")
    return values


def masked_mean(hidden, mask):
    if hidden.ndim != 3 or mask.shape != hidden.shape[:2] or not torch.all(mask.sum(1) > 0):
        raise ValueError("Invalid hidden/mask shapes or empty pooling region")
    weights = mask.to(hidden.dtype).unsqueeze(-1)
    return (hidden.masked_fill(~mask.bool().unsqueeze(-1), 0) * weights).sum(1) / weights.sum(1)


def select_layers(states, layers=LAYERS):
    # Transformers index 0 is pre-transformer encoder input. k is AFTER block k.
    if any(k < 1 or k >= len(states) for k in layers):
        raise ValueError("Layer must identify a transformer block output")
    return {k: states[k] for k in layers}


def state_digest(model):
    digest = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def freeze(model):
    model.requires_grad_(False)
    model.eval()
    return model


def encode_waveforms(model, processor, waves, layers=LAYERS):
    if model.training or any(p.requires_grad for p in model.parameters()):
        raise ValueError("Encoder must be frozen in eval mode")
    device = next(model.parameters()).device
    features = {k: [] for k in layers}
    with torch.inference_mode():
        for wave in waves:
            values = processor(wave, sampling_rate=16000, return_tensors="pt").input_values.to(
                device
            )
            # Checkpoint uses group-norm convolution and expects no encoder attention mask.
            states = model(values, output_hidden_states=True).hidden_states
            for k, hidden in select_layers(states, layers).items():
                valid = torch.ones(hidden.shape[:2], dtype=torch.bool, device=device)
                features[k].append(masked_mean(hidden, valid)[0].cpu().numpy())
    if any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Encoder received gradients")
    return {k: np.stack(v) for k, v in features.items()}


def extract(rows, snapshot, destination, layers=LAYERS):
    if destination.exists():
        raise FileExistsError("Refusing to silently replace feature cache")
    torch.set_num_threads(4)
    torch.manual_seed(20260929)
    torch.use_deterministic_algorithms(True)
    started = time.perf_counter()
    model, loading = Wav2Vec2Model.from_pretrained(
        snapshot,
        local_files_only=True,
        attn_implementation="eager",
        output_loading_info=True,
    )
    # An acoustic base can have unused pretraining heads, but no missing acoustic parameters.
    if loading["missing_keys"] or loading["mismatched_keys"] or loading["error_msgs"]:
        raise RuntimeError(f"Incomplete encoder checkpoint: {loading}")
    model = freeze(model)
    processor = Wav2Vec2FeatureExtractor.from_pretrained(snapshot, local_files_only=True)
    before = state_digest(model)
    collected = {k: [] for k in layers}
    for i, row in enumerate(rows, 1):
        path = Path(row["local_path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["audio_sha256"]:
            raise ValueError("Audio changed after split lock")
        wave = load_waveform(path)
        result = encode_waveforms(model, processor, [wave], layers)
        if i == 1:
            repeated = encode_waveforms(model, processor, [wave], layers)
            if not all(np.array_equal(result[k], repeated[k]) for k in layers):
                raise RuntimeError("Nondeterministic extraction")
        for k in layers:
            collected[k].append(result[k][0])
        if i % 50 == 0:
            print(f"Extracted {i}/{len(rows)}", flush=True)
    after = state_digest(model)
    if before != after or any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Frozen encoder mutated")
    values = {f"layer_{k}": np.stack(v) for k, v in collected.items()}
    np.savez_compressed(destination, asset_ids=[r["source_asset_id"] for r in rows], **values)
    report = {
        "n": len(rows),
        "layers": list(layers),
        "seconds": time.perf_counter() - started,
        "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        "device": "cpu",
        "torch_threads": 4,
        "hidden_size": model.config.hidden_size,
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "state_hash_before": before,
        "state_hash_after": after,
        "no_gradients": True,
        "first_clip_repeat_bitwise_equal": True,
        "loading_info": loading,
        "model_config": model.config.to_dict(),
        "processor_config": processor.to_dict(),
    }
    destination.with_suffix(".json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
