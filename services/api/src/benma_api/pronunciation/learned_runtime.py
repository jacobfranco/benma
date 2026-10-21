"""Lazy, process-resident frozen runtime. Only audio and numeric spans enter infer.

The lock covers initialization and inference: API requests run in worker threads.
Each process owns one encoder/head. Request caches are temporary, so warm behavior
does not depend on duplicate recordings and no research evidence is written.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Any

from benma_api.pronunciation.learned_contracts import LearnedRealization

ROOT = Path(__file__).resolve().parents[5]
RESEARCH = ROOT / "research/perceptual-tone-model"
FROZEN_LOCK_SHA256 = "cdae4b423e77dc3698cf75beee761f987b29ffd896fdd1c64c584b427233ca61"
RUNTIME_FILES = (
    "configs/encoders.json",
    "perceptual_tone/aishell3_boundaries.py",
    "perceptual_tone/aishell3_embeddings.py",
    "perceptual_tone/aishell3_learning.py",
    "perceptual_tone/embeddings.py",
    "perceptual_tone/learner_transfer.py",
    "models/generated/aishell3-multispeaker-fixed-v2/experiment_B.joblib",
)
_LOCK = threading.Lock()
_runtime: FrozenRuntime | None = None


def validate_contract(contract: dict[str, Any]) -> None:
    if set(contract) != {"audio_reference", "audio_sha256", "read_unit", "pooling", "context"}:
        raise ValueError("audio_contract_fields")
    for field in ("read_unit", "pooling", "context"):
        span = contract[field]
        if len(span) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in span):
            raise ValueError("invalid_span")
    a, b = contract["read_unit"]
    p, q = contract["pooling"]
    c, d = contract["context"]
    if not 0 <= c <= a <= p < q <= b <= d or q - p < 0.06 - 1e-9:
        raise ValueError("invalid_or_short_span")
    path = Path(contract["audio_reference"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != contract["audio_sha256"]:
        raise ValueError("audio_hash_changed")
    with wave.open(str(path)) as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
            raise ValueError("canonical_audio_required")
        if d > audio.getnframes() / 16000:
            raise ValueError("span_outside_audio")


class FrozenRuntime:
    def __init__(self) -> None:
        # Verify only runtime dependencies, not historical snapshots of the UI/API
        # being integrated. The full historical evidence freeze is checked separately.
        lock_bytes = (RESEARCH / "configs/dev-learned-lock.json").read_bytes()
        if hashlib.sha256(lock_bytes).hexdigest() != FROZEN_LOCK_SHA256:
            raise ValueError("frozen_lock_hash_mismatch")
        lock = json.loads(lock_bytes)
        for name in RUNTIME_FILES:
            expected = lock["files"]["research/perceptual-tone-model/" + name]
            if hashlib.sha256((RESEARCH / name).read_bytes()).hexdigest() != expected:
                raise ValueError("frozen_dependency_hash_mismatch")
        if str(RESEARCH) not in sys.path:
            sys.path.insert(0, str(RESEARCH))
        embeddings = importlib.import_module("perceptual_tone.aishell3_embeddings")
        transfer = importlib.import_module("perceptual_tone.learner_transfer")
        self.probabilities = transfer.probabilities
        self.calls = 0
        self.load_count = 1
        self.lock_sha256 = FROZEN_LOCK_SHA256
        with tempfile.TemporaryDirectory(prefix="benma-learned-load-") as folder:
            self.encoder = embeddings.Encoder(
                "chinese_hubert_base", Path(folder) / "embeddings", Path(folder) / "canonical"
            )
            if self.encoder.base.weights != lock["encoder_weights"]:
                raise ValueError("encoder_hash_mismatch")
            self.encoder.base._load()
        self.models = transfer.load_models(
            {"models": {"expanded": lock["model_method"]["models"]["expanded"]}}
        )

    def infer(self, contract: dict[str, Any]) -> dict[str, Any]:
        import numpy as np

        validate_contract(contract)
        with tempfile.TemporaryDirectory(prefix="benma-learned-attempt-") as folder:
            self.encoder.cache = Path(folder) / "embeddings"
            self.encoder.cache.mkdir()
            self.encoder.canonical = Path(folder) / "canonical"
            vectors, record = self.encoder.extract(contract, "context")
            p = self.probabilities(self.models, np.stack([vectors[1]]))["expanded"][0]
        self.calls += 1
        classes = ("T1", "T2", "T3", "T4")
        return {
            "status": "ok",
            "reason": None,
            "prediction": classes[int(p.argmax())],
            "confidence": float(p.max()),
            "probabilities": dict(zip(classes, p.tolist(), strict=True)),
            "owned_encoder_frames": record["owned_frames"],
        }


def infer_batch(contracts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Caller checks the dev gate; this boundary rejects all non-acoustic fields."""
    global _runtime
    for contract in contracts:
        validate_contract(contract)
    started = time.perf_counter()
    with _LOCK:
        queue_ms = (time.perf_counter() - started) * 1000
        cold = _runtime is None
        load_ms = 0.0
        try:
            if contracts and _runtime is None:
                load = time.perf_counter()
                _runtime = FrozenRuntime()
                load_ms = (time.perf_counter() - load) * 1000
            infer = time.perf_counter()
            outputs = [_runtime.infer(c) for c in contracts] if _runtime else []
            info = {
                "cold_start": bool(contracts) and cold,
                "model_load_ms": load_ms,
                "hubert_inference_ms": (time.perf_counter() - infer) * 1000,
                "runtime_queue_ms": queue_ms,
                "load_count": _runtime.load_count if _runtime else 0,
                "inference_calls": _runtime.calls if _runtime else 0,
                "embedding_cache_hits": 0,
                "lock_sha256": _runtime.lock_sha256 if _runtime else None,
            }
            return outputs, info
        except Exception as error:
            # No fallback to deterministic correctness; keep the acoustic chart.
            reason = "learned_runtime_unavailable:" + type(error).__name__
            return [LearnedRealization(reason=reason).model_dump() for _ in contracts], {
                "error": reason,
                "cold_start": cold,
                "runtime_queue_ms": queue_ms,
                "failed_runtime_ms": (time.perf_counter() - started) * 1000,
            }
