"""CPU latency for the SAME frozen Silero model; no download or new model."""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from silero_vad_audit import (
    REPORT,
    AudioOnlySilero,
    NumpySilero,
    corpus,
    segment,
    write_json,
)


def stats(values):
    return {
        "median": float(np.median(values)),
        "p95": float(np.quantile(values, 0.95)),
        "max": max(values),
    }


def cold(backend):
    # Module/NumPy startup is included in parent process wall timing; the model
    # timer below includes backend import and ONNX session/weights construction.
    _, _, audio = corpus()
    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    start = time.perf_counter()
    adapter = {"official": AudioOnlySilero, "numpy": NumpySilero}[backend]()
    load_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    adapter.infer(audio["human_control"])
    first_ms = (time.perf_counter() - start) * 1000
    print(
        json.dumps(
            {
                "backend": backend,
                "backend_import_and_model_load_ms": load_ms,
                "first_inference_ms": first_ms,
                "rss_before_kib": rss_before,
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
        )
    )


def main():
    _, entries, audio = corpus()
    cold_rows = []
    for backend in ("official", "numpy"):
        for _ in range(5):
            start = time.perf_counter()
            child = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--cold", backend],
                text=True,
                capture_output=True,
                check=True,
            )
            cold_rows.append(
                {
                    **json.loads(child.stdout),
                    "process_wall_ms": (time.perf_counter() - start) * 1000,
                }
            )
    official, numpy = AudioOnlySilero(), NumpySilero()
    adapters = {"official": official, "numpy": numpy}
    # Validate the reduced runtime path against official probabilities BEFORE
    # reporting speed. It evaluates no additional model or decision policy.
    for key, data in audio.items():
        assert official.infer(data) == numpy.infer(data), key
    timings = []
    for repeat in range(9):
        for key, data in audio.items():
            for backend in ("official", "numpy") if repeat % 2 == 0 else ("numpy", "official"):
                start = time.perf_counter()
                timeline = adapters[backend].infer(data)
                raw_ms = (time.perf_counter() - start) * 1000
                start = time.perf_counter()
                segment(timeline, official.helpers)
                segmentation_ms = (time.perf_counter() - start) * 1000
                timings.append(
                    {
                        "id": key,
                        "backend": backend,
                        "repeat": repeat,
                        "duration_seconds": timeline["input_duration_seconds"],
                        "raw_inference_ms": raw_ms,
                        "segmentation_ms": segmentation_ms,
                        "total_ms": raw_ms + segmentation_ms,
                        "real_time_factor": (raw_ms + segmentation_ms)
                        / (1000 * timeline["input_duration_seconds"]),
                    }
                )
    result = {
        "cpu": next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        "logical_cpu_count": os.cpu_count(),
        "platform": platform.platform(),
        "cpu_threads_per_session": 1,
        "cold": cold_rows,
        "cold_note": (
            "Five fresh processes per backend; OS filesystem cache not flushed."
            " Peak RSS is process high-water mark."
        ),
        "warm_note": (
            "Nine repeats per 48 cases per backend; sequential CPU, backend "
            "order alternated; WAV decode and frame metadata included; "
            "disk/JSON writes excluded."
        ),
        "numpy_note": (
            "Same weights, bit-exact full-corpus parity. Warm total includes "
            "official scalar segmentation after raw ONNX; cold NumPy measures "
            "the Torch-free raw path only."
        ),
        "representative_id": "human_control",
        "measurements": timings,
        "summary": {},
    }
    for backend in adapters:
        subset = [r for r in timings if r["backend"] == backend]
        representative = [r for r in subset if r["id"] == "human_control"]
        whole = [r for r in subset if "parent_id" not in entries[r["id"]]]
        result["summary"][backend] = {
            "corpus_total_ms": stats([r["total_ms"] for r in subset]),
            "whole_waveform_total_ms": stats([r["total_ms"] for r in whole]),
            "raw_inference_ms": stats([r["raw_inference_ms"] for r in subset]),
            "segmentation_ms": stats([r["segmentation_ms"] for r in subset]),
            "real_time_factor": stats([r["real_time_factor"] for r in subset]),
            "representative_total_ms": stats([r["total_ms"] for r in representative]),
            "representative_real_time_factor": stats(
                [r["real_time_factor"] for r in representative]
            ),
            "representative_duration_seconds": representative[0]["duration_seconds"],
            "cold": {
                key: stats([r[key] for r in cold_rows if r["backend"] == backend])
                for key in (
                    "backend_import_and_model_load_ms",
                    "first_inference_ms",
                    "process_wall_ms",
                    "peak_rss_kib",
                )
            },
        }
    write_json(REPORT / "latency.json", result)
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cold", choices=("official", "numpy"))
    args = parser.parse_args()
    if args.cold:
        cold(args.cold)
    else:
        main()
