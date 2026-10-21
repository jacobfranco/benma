"""Opt-in research inference. The model boundary has no text or grading fields."""

import math
import os
import resource
import time
import wave
from pathlib import Path

import numpy as np

from .aishell3_boundaries import derive
from .aishell3_embeddings import LAYERS, Encoder
from .aishell3_learning import validate_audio_contract
from .common import PACKAGE, ROOT, file_hash, read_json
from .learner_release import RELEASE, verify_release
from .learner_transfer import CLASSES, load_models, probabilities
from .manifest import verify_baseline

VERSION = "dev-learned-tone-v1"
LOCK = PACKAGE / "configs/dev-learned-lock.json"


def require_dev(enabled):
    if not enabled or os.environ.get("BENMA_ENVIRONMENT", "development") not in (
        "development",
        "test",
    ):
        raise ValueError("explicit_development_opt_in_required")


def verify_frozen():
    lock = read_json(LOCK)
    for name, expected in lock["files"].items():
        if file_hash(ROOT / name) != expected:
            raise ValueError("frozen_hash_mismatch:" + name)
    baseline = verify_baseline()
    learner = verify_release()
    native = ROOT / lock["native_release"]
    for name, expected in read_json(native / "release.json")["files"].items():
        if file_hash(native / name) != expected:
            raise ValueError("native_release_changed:" + name)
    return {"baseline": baseline, "learner": learner, "lock_sha256": file_hash(LOCK)}


def project_spans(audio, alignment):
    """Strict ownership from unmodified MFA phones; never infer missing boundaries."""
    if not alignment or alignment.get("start") is None:
        raise ValueError("missing_alignment")
    if alignment.get("exclusion_reasons"):
        raise ValueError("alignment_rejected:" + ",".join(alignment["exclusion_reasons"]))
    with wave.open(str(audio)) as stream:
        rate, frames = stream.getframerate(), stream.getnframes()
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
            raise ValueError("require_mono_pcm16")
    # Copy only timing/phones: expected labels cannot influence projection.
    row = {k: alignment[k] for k in ("start", "end", "aligned_phones")}
    row["example_id"] = "live-unit"
    return derive(row, rate, frames)


def span_contract(audio, alignment):
    spans = project_spans(audio, alignment)
    if not spans["available"]:
        raise ValueError("invalid_tone_bearing_span:" + spans["reason"])
    if spans["flags"]:
        # Existing research 60ms review flag, not a learner-tuned confidence rule.
        raise ValueError("too_little_material:" + ",".join(spans["flags"]))
    contract = {
        "audio_reference": str(Path(audio).resolve()),
        "audio_sha256": file_hash(audio),
        "read_unit": [alignment["start"], alignment["end"]],
        "pooling": [
            spans["tone_bearing_pooling_span"][k] for k in ("start_seconds", "end_seconds")
        ],
        "context": [spans["context"][k] for k in ("start_seconds", "end_seconds")],
    }
    validate_audio_contract(contract)
    return contract, spans


def validate_runtime_contract(contract):
    validate_audio_contract(contract)  # exact allowlist, including rejection of extra keys
    for field in ("read_unit", "pooling", "context"):
        if len(contract[field]) != 2 or not all(
            isinstance(t, (int, float)) and math.isfinite(t) for t in contract[field]
        ):
            raise ValueError("nonfinite_or_invalid_span")
    if file_hash(contract["audio_reference"]) != contract["audio_sha256"]:
        raise ValueError("audio_source_hash_changed")
    with wave.open(contract["audio_reference"]) as stream:
        if contract["context"][1] > stream.getnframes() / stream.getframerate():
            raise ValueError("span_outside_audio")
    if contract["pooling"][1] - contract["pooling"][0] < 0.06 - 1e-9:
        raise ValueError("too_little_material")


def abstention(reason):
    return {
        "status": "abstained",
        "reason": reason,
        "prediction": None,
        "confidence": None,
        "probabilities": None,
        "version": VERSION,
    }


class LearnedRecognizer:
    def __init__(self, folder, *, enabled=False):
        require_dev(enabled)
        started = time.perf_counter()
        self.verification = verify_frozen()
        self.folder = Path(folder)
        self.config = read_json(RELEASE / "inference-config.json")
        self.models = None
        self.encoder = None
        self.setup_seconds = time.perf_counter() - started
        self.encoder_load_seconds = None
        self.classifier_load_seconds = None

    def infer(self, contract):
        """Only this five-field audio contract reaches the encoder/heads."""
        started = time.perf_counter()
        try:
            validate_runtime_contract(contract)
        except (ValueError, OSError, wave.Error) as error:
            return {"expanded": abstention(str(error)), "pilot": abstention(str(error))}
        try:
            if self.encoder is None:
                load_start = time.perf_counter()
                encoder = Encoder(
                    "chinese_hubert_base", self.folder / "embeddings", self.folder / "canonical"
                )
                lock = read_json(LOCK)
                if encoder.base.weights != lock["encoder_weights"]:
                    raise ValueError("encoder_weights_changed")
                encoder.base._load()
                self.encoder = encoder
                self.encoder_load_seconds = time.perf_counter() - load_start
            vectors, record = self.encoder.extract(contract, "context")
        except Exception as error:
            return {
                "expanded": abstention("encoder_failure:" + type(error).__name__),
                "pilot": abstention("encoder_failure:" + type(error).__name__),
            }
        try:
            if self.models is None:
                load_start = time.perf_counter()
                self.models = load_models(self.config)
                self.classifier_load_seconds = time.perf_counter() - load_start
            values = probabilities(self.models, np.stack([vectors[LAYERS.index(9)]]))
        except Exception as error:
            return {
                "expanded": abstention("classifier_failure:" + type(error).__name__),
                "pilot": abstention("classifier_failure:" + type(error).__name__),
            }
        result = {}
        for name, matrix in values.items():
            p = matrix[0]
            result[name] = {
                "status": "ok",
                "reason": None,
                "prediction": CLASSES[int(p.argmax())],
                "confidence": float(p.max()),
                "probabilities": dict(zip(CLASSES, p.tolist(), strict=True)),
                "version": VERSION,
                "model_sha256": self.config["models"][name]["sha256"],
                "encoder_revision": self.config["encoder"]["revision"],
                "layer": 9,
                "view": "context",
                "pooling": self.config["pooling"],
                "span_metadata": contract,
                "embedding": record,
                "confidence_is_calibrated_correctness": False,
            }
        result["inference_seconds"] = time.perf_counter() - started
        return result

    def performance(self):
        return {
            "verification_seconds": self.setup_seconds,
            "encoder_load_seconds": self.encoder_load_seconds,
            "classifier_load_seconds": self.classifier_load_seconds,
            "process_peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            "embedding_cache_hits": self.encoder.hits if self.encoder else 0,
            "embedding_cache_misses": self.encoder.misses if self.encoder else 0,
        }


def compare(expected, expanded, pilot, deterministic):
    """Descriptive research grading only; no new confidence cutoff or consensus truth."""
    heard = expanded.get("prediction")
    result = {
        "state": "INSUFFICIENT_EVIDENCE",
        "grade": "unavailable",
        "confidence_threshold": None,
        "confident_error": False,
        "interpretation": "",
        "explanation": None,
        "agreement_is_ground_truth": False,
    }
    if expected in (0, 5):
        result.update(
            reason="neutral_outside_four_tone_model",
            interpretation="Neutral target: no numbered-tone correction; non-veto.",
        )
        return result
    if expanded.get("status") != "ok":
        result.update(
            reason=expanded.get("reason", "model_unavailable"),
            interpretation="Learned recognition abstained.",
        )
        return result
    if expected not in (1, 2, 3, 4):
        result.update(
            reason="expected_surface_unresolved",
            interpretation=f"Expected surface unresolved; heard {heard}-like. No correction.",
        )
        return result
    secondary = [pilot.get("prediction"), deterministic.get("prediction")]
    disagreement = any(p and p != heard for p in secondary)
    match = heard == f"T{expected}"
    result.update(
        state="MODEL_DISAGREEMENT"
        if disagreement
        else "MATCH"
        if match
        else "MODEL_CONCERN_UNTHRESHOLDED",
        grade="experimental_match" if match else "experimental_mismatch",
        reason="secondary_disagreement" if disagreement else "argmax_comparison_only",
        interpretation=f"Expected T{expected} → heard {heard}-like. "
        + (
            "Argmax matches; correctness is unverified."
            if match
            else "Tone mismatch for review; raw confidence has no established cutoff."
        ),
    )
    if not match:
        observed = deterministic.get("observed", {})
        features = observed.get("features", {})
        support = (
            deterministic.get("prediction") == heard
            and observed.get("evidence") == "trustworthy"
            and observed.get("decision") == "NUMBERED"
            and observed.get("strength") == "full"
        )
        # Describe measured movement, never infer a missing T3 recovery from the model.
        key = {"T2": "rise_st", "T4": "fall_st"}.get(heard)
        amount = features.get(key) if key else None
        if support and isinstance(amount, (int, float)) and math.isfinite(amount) and amount > 0:
            verb = "rose" if heard == "T2" else "fell"
            result["explanation"] = (
                f"The retained pitch {verb} by {amount:.2f} semitones; the frozen acoustic "
                f"baseline also identified {heard}-like movement. "
                "This supports review, not certainty."
            )
        else:
            result["explanation"] = (
                f"Benma recognized this as {heard}-like, but the contour evidence is not clear "
                "enough for a specific coaching diagnosis."
            )
        result["specific_coaching_supported"] = (
            support and isinstance(amount, (int, float)) and math.isfinite(amount) and amount > 0
        )
    return result
