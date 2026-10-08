"""One frozen Silero ONNX model, offline research only; never imported by the API.

Setup is documented in the report. This program never downloads anything. Run
`default` and inspect its saved results BEFORE explicitly running `thresholds`.
The audio adapter accepts PCM bytes only, with no transcript/target argument.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
import platform
import time
import wave
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PRIOR = ROOT / "docs/research/pronunciation-v2/2026-10-06-speech-presence"
REPORT = ROOT / "docs/research/pronunciation-v2/2026-10-06-silero-vad"
LOCAL = ROOT / "services/api/var/silero-vad"
UPSTREAM = LOCAL / "upstream"
MODEL = UPSTREAM / "silero_vad/data/silero_vad.onnx"
MODEL_SHA = "1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3"
UTILS_SHA = "15d0f6b3ef9590e22ca2f146e1436f6901da356cb552d3183df4100862b333cb"
RATE, WINDOW = 16000, 512
THRESHOLDS = (0.30, 0.40, 0.50, 0.60, 0.70)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def upstream():
    """Import the hash-pinned official helpers without modifying upstream code."""
    path = UPSTREAM / "silero_vad/utils_vad.py"
    if sha(path.read_bytes()) != UTILS_SHA or sha(MODEL.read_bytes()) != MODEL_SHA:
        raise ValueError("Silero source/model hash mismatch")
    spec = importlib.util.spec_from_file_location("benma_research_silero_upstream", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.torch.set_num_threads(1)
    return module


def read_frozen_audio(entry: dict, entries: dict[str, dict]) -> bytes:
    if "parent_id" in entry:
        parent = read_frozen_audio(entries[entry["parent_id"]], entries)
        if sha(parent) != entry["parent_sha256"]:
            raise ValueError(f"Parent hash mismatch: {entry['id']}")
        start, end = entry["interval_seconds"]
        with wave.open(io.BytesIO(parent)) as stream:
            rate = stream.getframerate()
            stream.setpos(round(start * rate))
            frames = stream.readframes(round((end - start) * rate))
        output = io.BytesIO()
        with wave.open(output, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(frames)
        data = output.getvalue()
    else:
        data = (ROOT / entry["path"]).read_bytes()
    if sha(data) != entry["sha256"]:
        raise ValueError(f"Audio hash mismatch: {entry['id']}")
    return data


def corpus():
    """Verify EVERY input before constructing a model or starting inference."""
    data = (PRIOR / "corpus.json").read_bytes()
    manifest = json.loads(data)
    entries = {e["id"]: e for e in manifest["entries"]}
    if len(entries) != 48 or len(entries) != len(manifest["entries"]):
        raise ValueError("Frozen corpus coverage/identity changed")
    if Counter(e["label"] for e in entries.values()) != {
        "positive": 37,
        "negative": 10,
        "unresolved": 1,
    }:
        raise ValueError("Frozen corpus labels changed")
    audio = {key: read_frozen_audio(entry, entries) for key, entry in entries.items()}
    return data, entries, audio


def normalize_audio(pcm: bytes) -> tuple[np.ndarray, dict]:
    """PCM16 / 32768, mono, no gain adjustment; polyphase resample to 16 kHz.

    Forty-six frozen cases use 16 kHz; two cached variants require 24-to-16 kHz
    resampling. Alternate-rate unit fixtures do not expand the frozen corpus.
    """
    with wave.open(io.BytesIO(pcm)) as stream:
        rate = stream.getframerate()
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
            raise ValueError("Expected mono PCM16 WAV")
        values = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
    if not len(values) or rate <= 0:
        raise ValueError("Empty or invalid audio")
    samples = values.astype(np.float32) / np.float32(32768)
    if rate != RATE:
        from scipy.signal import resample_poly

        factor = math.gcd(rate, RATE)
        samples = resample_poly(samples, RATE // factor, rate // factor).astype(np.float32)
    return samples, {
        "input_sample_rate": rate,
        "normalized_sample_rate": RATE,
        "input_samples": len(values),
        "normalized_samples": len(samples),
        "input_duration_seconds": len(values) / rate,
        "normalized_duration_seconds": len(samples) / RATE,
        "preprocessing": "mono PCM16 / 32768; float32; no gain/DC/filter change; "
        "scipy resample_poly only when input is not 16 kHz",
        "window_samples": WINDOW,
        "window_seconds": WINDOW / RATE,
        "context_samples": 64,
        "last_chunk_zero_padding_samples": (-len(samples)) % WINDOW,
    }


class AudioOnlySilero:
    """Official ONNX wrapper, reset between utterances; only audio enters infer."""

    def __init__(self):
        self.helpers = upstream()
        self.model = self.helpers.OnnxWrapper(str(MODEL), force_onnx_cpu=True)

    def infer(self, pcm: bytes) -> dict:
        samples, metadata = normalize_audio(pcm)
        self.model.reset_states()
        frames = []
        for start in range(0, len(samples), WINDOW):
            valid = min(WINDOW, len(samples) - start)
            chunk = np.zeros(WINDOW, dtype=np.float32)
            chunk[:valid] = samples[start : start + valid]
            probability = self.model(self.helpers.torch.from_numpy(chunk), RATE).item()
            frames.append(
                {
                    "start_sample": start,
                    "end_sample": start + valid,
                    "start_seconds": start / RATE,
                    "end_seconds": (start + valid) / RATE,
                    "window_end_seconds": (start + WINDOW) / RATE,
                    "probability": probability,
                }
            )
        return {**metadata, "model_sha256": MODEL_SHA, "frames": frames}


class NumpySilero:
    """Same ONNX model/state/context as upstream, without Torch at runtime.

    Deployment feasibility probe, NOT a second model. Corpus tests require
    bit-exact agreement with the official wrapper before using its timings.
    Recurrent state and context are local to each infer call.
    """

    def __init__(self):
        import onnxruntime as ort

        if sha(MODEL.read_bytes()) != MODEL_SHA:
            raise ValueError("Silero model hash mismatch")
        options = ort.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(MODEL), providers=["CPUExecutionProvider"], sess_options=options
        )

    def infer(self, pcm: bytes) -> dict:
        samples, metadata = normalize_audio(pcm)
        state = np.zeros((2, 1, 128), dtype=np.float32)
        context = np.zeros((1, 64), dtype=np.float32)
        frames = []
        for start in range(0, len(samples), WINDOW):
            valid = min(WINDOW, len(samples) - start)
            chunk = np.zeros((1, WINDOW), dtype=np.float32)
            chunk[0, :valid] = samples[start : start + valid]
            inputs = np.concatenate((context, chunk), axis=1)
            output, state = self.session.run(
                None, {"input": inputs, "state": state, "sr": np.array(RATE, dtype=np.int64)}
            )
            context = inputs[:, -64:]
            frames.append(
                {
                    "start_sample": start,
                    "end_sample": start + valid,
                    "start_seconds": start / RATE,
                    "end_seconds": (start + valid) / RATE,
                    "window_end_seconds": (start + WINDOW) / RATE,
                    "probability": float(output.item()),
                }
            )
        return {**metadata, "model_sha256": MODEL_SHA, "frames": frames}


def segment(timeline: dict, helpers, threshold=0.5, min_speech_duration_ms=250) -> dict:
    """Official helper on PRESERVED probabilities, no boolean shortcut."""
    probabilities = [f["probability"] for f in timeline["frames"]]
    regions = helpers.get_speech_timestamps_from_probs(
        probabilities,
        sampling_rate=RATE,
        threshold=threshold,
        min_speech_duration_ms=min_speech_duration_ms,
        audio_length_samples=timeline["normalized_samples"],
    )
    durations = [(r["end"] - r["start"]) / RATE for r in regions]
    return {
        "threshold": threshold,
        "negative_threshold": max(threshold - 0.15, 0.01),
        "min_speech_duration_ms": min_speech_duration_ms,
        "min_silence_duration_ms": 100,
        "speech_pad_ms": 30,
        "max_speech_duration_s": "infinity",
        "accepted": bool(regions),
        "max_probability": max(probabilities),
        "median_probability": float(np.median(probabilities)),
        "probability_quantiles_0_10_25_50_75_90_95_100": np.quantile(
            probabilities, [0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1]
        ).tolist(),
        "total_speech_seconds": sum(durations),
        "longest_region_seconds": max(durations, default=0),
        "number_regions": len(regions),
        "first_speech_seconds": regions[0]["start"] / RATE if regions else None,
        "last_speech_seconds": regions[-1]["end"] / RATE if regions else None,
        "regions_samples": regions,
        "regions_seconds": [{k: v / RATE for k, v in r.items()} for r in regions],
    }


def summary(rows):
    return {
        "negative_rejected": sum(
            not r["silero"]["accepted"] for r in rows if r["label"] == "negative"
        ),
        "positive_retained": sum(r["silero"]["accepted"] for r in rows if r["label"] == "positive"),
        "false_accepts": [
            r["id"] for r in rows if r["label"] == "negative" and r["silero"]["accepted"]
        ],
        "false_rejects": [
            r["id"] for r in rows if r["label"] == "positive" and not r["silero"]["accepted"]
        ],
        "categories": {
            tag: {
                "total": sum(tag in r["tags"] for r in rows if r["label"] == "positive"),
                "retained": sum(
                    tag in r["tags"] and r["silero"]["accepted"]
                    for r in rows
                    if r["label"] == "positive"
                ),
            }
            for tag in sorted({t for r in rows if r["label"] == "positive" for t in r["tags"]})
        },
    }


def run_default():
    manifest, entries, audio = corpus()
    REPORT.mkdir(exist_ok=True)
    if (REPORT / "default-results.json").exists():
        raise FileExistsError("Default already recorded; do not overwrite the first result")
    (REPORT / "corpus.json").write_bytes(manifest)
    write_json(
        REPORT / "hash-verification.json",
        {
            "manifest_sha256": sha(manifest),
            "verified_before_inference": True,
            "counts": dict(Counter(e["label"] for e in entries.values())),
            "waveforms": {key: sha(data) for key, data in audio.items()},
        },
    )
    # The unchanged production baseline is read from the prior frozen replay.
    baseline = {r["id"]: r for r in json.loads((PRIOR / "measurements.json").read_text())}
    start = time.perf_counter()
    adapter = AudioOnlySilero()
    load_ms = (time.perf_counter() - start) * 1000
    import onnxruntime
    import torch

    provenance = {
        "package": "silero-vad",
        "version": "6.2.3",
        "upstream_repository": "https://github.com/snakers4/silero-vad",
        "download": json.loads((LOCAL / "download.json").read_text()),
        "model": "silero_vad/data/silero_vad.onnx",
        "model_sha256": MODEL_SHA,
        "model_size_bytes": MODEL.stat().st_size,
        "utils_sha256": UTILS_SHA,
        "license": "MIT",
        "backend": "onnxruntime",
        "onnxruntime": onnxruntime.__version__,
        "providers": adapter.model.session.get_providers(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "python": platform.python_version(),
        "intra_op_threads": 1,
        "inter_op_threads": 1,
        "batch_size": 1,
        "initial_import_and_model_load_ms": load_ms,
        "manifest_sha256": sha(manifest),
        "upstream_opset": 16,
    }
    write_json(REPORT / "model-provenance.json", provenance)
    rows = []
    for key, entry in entries.items():
        if baseline[key]["sha256"] != entry["sha256"]:
            raise ValueError("Baseline identity mismatch")
        timeline = adapter.infer(audio[key])
        timeline.update({"id": key, "audio_sha256": entry["sha256"], "provenance": provenance})
        # Persist raw frames BEFORE invoking any speech-segmentation helper.
        write_json(REPORT / "probabilities" / f"{key}.json", timeline)
        rows.append(
            {
                "id": key,
                "label": entry["label"],
                "tags": entry["tags"],
                "audio_sha256": entry["sha256"],
                "duration_seconds": timeline["input_duration_seconds"],
                "current_accepted": baseline[key]["current_accepted"],
                "silero": segment(timeline, adapter.helpers),
            }
        )
    result = {
        "configuration": "unmodified upstream defaults",
        "summary": summary(rows),
        "rows": rows,
    }
    write_json(REPORT / "default-results.json", result)
    print(json.dumps(result["summary"], indent=2))
    print(json.dumps(next(r for r in rows if r["id"] == "silence_accidental"), indent=2))


def run_thresholds():
    corpus()  # All hashes still mandatory even when reusing saved probabilities.
    default = json.loads((REPORT / "default-results.json").read_text())
    helpers = upstream()
    runs = []
    for threshold in THRESHOLDS:
        rows = []
        for row in default["rows"]:
            timeline = json.loads((REPORT / "probabilities" / f"{row['id']}.json").read_text())
            rows.append({**row, "silero": segment(timeline, helpers, threshold)})
        run = {
            "threshold": threshold,
            "min_speech_duration_ms": 250,
            "summary": summary(rows),
            "rows": rows,
        }
        runs.append(run)
        print(threshold, json.dumps(run["summary"]))
    write_json(
        REPORT / "threshold-results.json",
        {
            "default_results_sha256": sha((REPORT / "default-results.json").read_bytes()),
            "threshold_only": True,
            "runs": runs,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("default", "thresholds"))
    args = parser.parse_args()
    {"default": run_default, "thresholds": run_thresholds}[args.stage]()
