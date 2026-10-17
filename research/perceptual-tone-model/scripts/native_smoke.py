"""Real native-audio encoder plumbing only. Never fits a head or evaluates test."""

import copy
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows, runtime, write_json
from perceptual_tone.embeddings import FrozenEncoder
from perceptual_tone.manifest import verify_baseline
from perceptual_tone.native_protocol import model_input


def run(manifest, output):
    baseline = verify_baseline()
    config = read_json(PACKAGE / "configs/native-tone.json")
    encoders = read_json(PACKAGE / "configs/encoders.json")
    selected = {}
    for row in read_rows(manifest):
        if row["partition"] == "train":
            selected.setdefault(row["utterance_id"], row)
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise ValueError("Need two training utterances")
    results = []
    started = time.monotonic()
    for name in config["encoders"]:
        # One model load per encoder; no parameter ever requires gradients.
        e = FrozenEncoder(
            encoders[name],
            {"view": "local", "pooling": "target_mean", "device": "cpu", "threads": 2},
        )
        for layer in config["layers"]:
            e.encoder = {**encoders[name], "hidden_layer": layer}
            for view in ("local", "wide"):
                for pooling in config["pooling"]:
                    e.settings = {"view": view, "pooling": pooling, "device": "cpu", "threads": 2}
                    for row in selected.values():
                        vector, metadata = e.extract(row)
                        model_input({"embedding": vector})
                        changed = copy.deepcopy(row)
                        changed.update(
                            label="WRONG",
                            pinyin="leak4",
                            lexical_tone=99,
                            surface_tone=99,
                            transcript="labels must not enter encoder",
                        )
                        again, repeated = e.extract(changed)
                        if not np.array_equal(vector, again) or metadata != repeated:
                            raise AssertionError("Label mutation changed embedding/cache")
                        results.append(
                            {
                                "encoder": name,
                                "revision": e.encoder["revision"],
                                "layer": layer,
                                "view": view,
                                "pooling": pooling,
                                "example_id": row["example_id"],
                                "dimension": len(vector),
                                "cache_key": metadata["cache_key"],
                                "label_mutation_invariant": True,
                            }
                        )
        if e.model is not None:
            assert not any(p.requires_grad for p in e.model.parameters())
        del e
    write_json(
        output,
        {
            "status": "ENGINEERING_SMOKE_ONLY_NO_TRAINING",
            "baseline": baseline,
            "manifest_sha256": file_hash(manifest),
            "runtime": runtime(),
            "elapsed_seconds": time.monotonic() - started,
            "utterances": 2,
            "embeddings": len(results),
            "results": results,
            "trained_models": 0,
            "test_examples_evaluated": 0,
        },
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.output)
