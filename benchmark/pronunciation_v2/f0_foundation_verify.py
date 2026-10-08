"""Fresh-process CPU timing and actual-recording metadata-invariance verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.f0_foundation import extract_utterance_pitch, track_record


def verify(root: Path, tracker: str):
    started = time.perf_counter()
    if tracker == "crepe_full":
        import torch
        import torchcrepe

        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.use_deterministic_algorithms(True)
        checkpoint = Path(torchcrepe.__file__).parent / "assets/full.pth"
        assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == (
            "133225604dedd2e4005f8bbd1bd0a2ec073ba8b7a6cd31ff6d5edbbfa3539986"
        )
        torchcrepe.load.model("cpu", "full")
    initialization = time.perf_counter() - started
    rows = json.loads((root / "manifest.json").read_text())
    cases = {r["id"]: r for r in rows}
    results = {
        "tracker": tracker,
        "explicit_initialization_seconds": initialization,
        "warm_runs": [],
        "invariance": {},
    }
    # Warm import/JIT/kernel state, then measure serially with no output serialization.
    started = time.perf_counter()
    extract_utterance_pitch(Path(cases["native_24k"]["audio_path"]), tracker)
    results["first_inference_seconds"] = time.perf_counter() - started
    for case in ("native_24k", "human_control"):
        for iteration in range(3):
            started = time.perf_counter()
            cpu = time.process_time()
            track = extract_utterance_pitch(Path(cases[case]["audio_path"]), tracker)
            seconds = time.perf_counter() - started
            results["warm_runs"].append(
                {
                    "recording": case,
                    "iteration": iteration,
                    "duration_seconds": cases[case]["duration_seconds"],
                    "wall_seconds": seconds,
                    "cpu_seconds": time.process_time() - cpu,
                    "real_time_factor": seconds / cases[case]["duration_seconds"],
                    "evidence_sha256": hashlib.sha256(track.canonical_bytes()).hexdigest(),
                }
            )
    # Actual historical suspicious-branch audio, not only an easy synthetic.
    case = cases["f5dc0cc1"]
    contexts = [
        {"transcript": "贵州", "target": "广州", "pinyin": "gui4 zhou1", "tone": [4, 1]},
        {"transcript": "鬼粥", "target": "fake", "pinyin": "nonsense", "tone": [1, 4]},
        {"transcript": "", "target": None, "character": None, "expected_contour": "fake"},
    ]
    outputs = [
        track_record({"audio_path": case["audio_path"], **c}, tracker).canonical_bytes()
        for c in contexts
    ]
    assert outputs[0] == outputs[1] == outputs[2]
    for name in ("native_24k", "human_control"):
        hashes = [r["evidence_sha256"] for r in results["warm_runs"] if r["recording"] == name]
        assert len(set(hashes)) == 1
    results["invariance"] = {
        "recording": case["id"],
        "audio_sha256": case["sha256"],
        "contexts": contexts,
        "byte_identical": True,
        "evidence_sha256": hashlib.sha256(outputs[0]).hexdigest(),
    }
    results["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    results["median_warm_rtf"] = float(
        np.median([r["real_time_factor"] for r in results["warm_runs"]])
    )
    (root / f"verification-{tracker}.json").write_text(json.dumps(results, indent=2))
    print(tracker, results["median_warm_rtf"], "metadata invariant", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tracker")
    parser.add_argument("--output", type=Path, default=Path("/tmp/benma-f0-bakeoff"))
    args = parser.parse_args()
    verify(args.output, args.tracker)
