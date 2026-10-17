"""Frozen HuBERT/WavLM embeddings with content-addressed, verified caches."""

import hashlib
import re
from pathlib import Path

import numpy as np

from .audio import read_audio
from .common import PACKAGE, digest, file_hash, read_json, runtime, write_json

VERSION = "frozen-speech-v1"


def cache_key(audio_pcm_sha256, encoder, settings, target_samples, environment, weights):
    return digest(
        {
            "implementation": VERSION,
            "audio_pcm_sha256": audio_pcm_sha256,
            "encoder": encoder,
            "settings": settings,
            "target_samples": target_samples,
            "runtime": environment,
            "model_files": weights,
        }
    )


def frame_centers(config, frame_count):
    receptive, stride = 1, 1
    for kernel, step in zip(config.conv_kernel, config.conv_stride, strict=True):
        receptive += (kernel - 1) * stride
        stride *= step
    return (receptive - 1) / 2 + np.arange(frame_count) * stride


def pool(hidden, centers, target_samples, method):
    if method == "context_mean":
        return hidden.mean(axis=0)
    target = (centers >= target_samples[0]) & (centers < target_samples[1])
    if not target.any():
        raise ValueError("No encoder frame centers within target; review segmentation")
    target_mean = hidden[target].mean(axis=0)
    if method == "target_mean":
        return target_mean
    if method == "target_context_concat":
        return np.concatenate([target_mean, hidden.mean(axis=0)])
    raise ValueError("Unsupported pooling method")


class FrozenEncoder:
    def __init__(self, encoder, settings, cache_dir=None, model_cache=None):
        import torch
        from huggingface_hub import snapshot_download

        if set(settings) != {"view", "pooling", "device", "threads"}:
            raise ValueError("Unknown/missing embedding settings")
        if settings["view"] not in ("local", "wide") or settings["pooling"] not in (
            "target_mean",
            "context_mean",
            "target_context_concat",
        ):
            raise ValueError("Unsupported embedding view/pooling")
        if not re.fullmatch(r"[a-f0-9]{40}", encoder["revision"]):
            raise ValueError("Encoder revision must be an immutable commit SHA")
        if settings["threads"] < 1 or settings["device"] not in ("cpu", "cuda"):
            raise ValueError("Invalid runtime settings")
        self.encoder, self.settings = encoder, settings
        self.directory = Path(cache_dir or PACKAGE / "embeddings/generated")
        self.directory.mkdir(parents=True, exist_ok=True)
        self.snapshot = Path(
            snapshot_download(
                encoder["model_id"],
                revision=encoder["revision"],
                cache_dir=model_cache or PACKAGE / ".cache/huggingface",
                local_files_only=True,
            )
        )
        self.weights = {
            name: file_hash(self.snapshot / name)
            for name in ("config.json", "preprocessor_config.json", "pytorch_model.bin")
        }
        self.environment = runtime()
        self.environment["embedding_code_sha256"] = file_hash(Path(__file__))
        self.environment["device"] = settings["device"]
        self.environment["device_name"] = (
            torch.cuda.get_device_name(0) if settings["device"] == "cuda" else "CPU"
        )
        self.model = self.processor = None
        self.hits = self.misses = 0

    def _load(self):
        import torch
        from transformers import HubertModel, Wav2Vec2FeatureExtractor, WavLMModel

        torch.set_num_threads(self.settings["threads"])
        torch.use_deterministic_algorithms(True)
        cls = {"hubert": HubertModel, "wavlm": WavLMModel}[self.encoder["architecture"]]
        self.model = cls.from_pretrained(str(self.snapshot), local_files_only=True)
        self.model.eval().requires_grad_(False).to(self.settings["device"])
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(
            str(self.snapshot), local_files_only=True
        )
        if (
            self.processor.sampling_rate != self.encoder["sample_rate_hz"]
            or self.processor.do_normalize != self.encoder["normalize"]
            or self.model.config.hidden_size != self.encoder["hidden_size"]
            or not 1 <= self.encoder["hidden_layer"] <= self.model.config.num_hidden_layers
        ):
            raise ValueError("Pinned encoder metadata does not match model configuration")

    def extract(self, row):
        import torch

        window = row["windows"][self.settings["view"]]
        pcm, rate, count = read_audio(window["reference"], window["sha256"])
        pcm_hash = hashlib.sha256(pcm).hexdigest()
        if rate != self.encoder["sample_rate_hz"] or pcm_hash != window["pcm_sha256"]:
            raise ValueError("Encoder requires verified canonical audio at its pinned sample rate")
        target = [
            row["target"][key] * rate - window["start_sample"]
            for key in ("start_seconds", "end_seconds")
        ]
        if not 0 <= target[0] < target[1] <= count:
            raise ValueError("Target outside embedding window")
        key = cache_key(
            pcm_hash, self.encoder, self.settings, target, self.environment, self.weights
        )
        array_path, metadata_path = self.directory / f"{key}.npy", self.directory / f"{key}.json"
        dimension = self.encoder["hidden_size"] * (
            2 if self.settings["pooling"] == "target_context_concat" else 1
        )
        if array_path.exists() and metadata_path.exists():
            metadata = read_json(metadata_path)
            if metadata["cache_key"] != key or file_hash(array_path) != metadata["vector_sha256"]:
                raise ValueError("Embedding cache checksum mismatch")
            vector = np.load(array_path, allow_pickle=False)
            self.hits += 1
        else:
            if array_path.exists() or metadata_path.exists():
                raise ValueError("Incomplete embedding cache entry; remove that entry and retry")
            if self.model is None:
                self._load()
            audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
            inputs = self.processor(audio, sampling_rate=rate, return_tensors="pt")
            inputs = {k: v.to(self.settings["device"]) for k, v in inputs.items()}
            with torch.inference_mode():
                hidden = (
                    self.model(**inputs, output_hidden_states=True)
                    .hidden_states[self.encoder["hidden_layer"]][0]
                    .cpu()
                    .numpy()
                )
            vector = pool(
                hidden,
                frame_centers(self.model.config, len(hidden)),
                target,
                self.settings["pooling"],
            ).astype(np.float32)
            with array_path.open("xb") as stream:
                np.save(stream, vector, allow_pickle=False)
            metadata = {
                "cache_key": key,
                "encoder": self.encoder,
                "settings": self.settings,
                "embedding_dimension": dimension,
                "runtime": self.environment,
                "model_files": self.weights,
                "window_pcm_sha256": pcm_hash,
                "target_relative_samples": target,
                "frame_alignment": "convolution_receptive_field_centers",
                "implementation": VERSION,
                "vector_sha256": file_hash(array_path),
            }
            write_json(metadata_path, metadata)
            self.misses += 1
        if vector.shape != (dimension,) or not np.isfinite(vector).all():
            raise ValueError("Invalid cached embedding dimension/values")
        return vector, metadata

    def extract_all(self, rows):
        vectors, metadata = {}, {}
        for row in rows:
            vectors[row["example_id"]], metadata[row["example_id"]] = self.extract(row)
        return vectors, metadata
