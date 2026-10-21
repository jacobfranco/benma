"""Inference-only timing and sealed numerical reproduction, using archived audio."""

import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import read_rows
from perceptual_tone.dev_inference import LearnedRecognizer
from perceptual_tone.learner_release import RUN


def benchmark():
    rows = [
        r
        for r in read_rows(RUN / "primary/predictions.jsonl")
        if r["audio_contract"]["pooling"][1] - r["audio_contract"]["pooling"][0] >= 0.06
    ][:4]
    with tempfile.TemporaryDirectory(prefix="benma-dev-inference-") as folder:
        recognizer = LearnedRecognizer(Path(folder), enabled=True)
        costs, deltas = [], []
        for row in rows:
            started = time.perf_counter()
            result = recognizer.infer(row["audio_contract"])
            costs.append(time.perf_counter() - started)
            for name in ("expanded", "pilot"):
                actual = list(result[name]["probabilities"].values())
                expected = row[name]["probabilities"]
                np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)
                deltas.append(float(np.max(np.abs(np.array(actual) - expected))))
        started = time.perf_counter()
        for row in rows:
            recognizer.infer(row["audio_contract"])
        return {
            "source": "archived accepted learner units; not fresh physical testing",
            "units": len(rows),
            "fresh_unit_seconds": costs,
            "cached_four_units_seconds": time.perf_counter() - started,
            "maximum_probability_delta": max(deltas),
            **recognizer.performance(),
        }


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
