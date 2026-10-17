"""Run from repository root: python research/perceptual-tone-model/scripts/pilot.py."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from .annotations import import_annotations, item_id
from .audio import packet, prepare_windows
from .common import ALL_LABELS, PACKAGE, digest, read_json, read_rows, write_json, write_rows
from .embeddings import FrozenEncoder
from .experiment import run, validate_config
from .features import matrix
from .manifest import replay, upgrade, validate, verify_baseline
from .splits import split_speakers


def stage0(output, config):
    if config["scientific"]:
        raise ValueError("Stage 0 requires an explicitly non-scientific configuration")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    groups = defaultdict(list)
    for row in read_rows(PACKAGE / "stage0.dataset.jsonl"):
        if row["target"]["unit_kind"] == "syllable":
            groups[row["recording_id"]].append(row)
    recordings = sorted(k for k, rows in groups.items() if len(rows) >= 4)[:6]
    if len(recordings) != 6:
        raise ValueError("Expected six available multi-syllable Stage-0 recordings")
    source = [row for recording in recordings for row in groups[recording][:4]]
    speakers = {
        recording: f"NONSCIENTIFIC-fixture-speaker-{i}" for i, recording in enumerate(recordings)
    }
    rows = upgrade(source, "stage0-smoke-v1", speakers, fixture=True)
    rows, baseline = replay(rows)
    rows = prepare_windows(rows, config["windows"], PACKAGE / "data/generated/audio")
    validate(rows)
    write_rows(output / "manifest.jsonl", rows)
    packet_result = packet(rows, output / "annotation-packet", config["seed"])
    submissions = []
    # Labels deliberately cycle independent of every deterministic output.
    for i, row in enumerate(rows):
        label = ALL_LABELS[i % 4]
        for listener in range(3):
            submissions.append(
                {
                    "item_id": item_id(row),
                    "judgment_id": f"mock-{i}-{listener}",
                    "annotator_id": f"MOCK-listener-{listener}",
                    "acceptability": label,
                    "perceived_tone": None,
                    "confidence": None,
                    "notes": "MOCK TEST ONLY",
                    "timestamp": "2026-10-15T00:00:00Z",
                    "rubric_version": "1.0",
                    "version": 1,
                    "supersedes": None,
                    "origin": "mock_test",
                }
            )
    write_rows(output / "mock-judgments.jsonl", submissions)
    rows = import_annotations(
        rows,
        submissions,
        output / "annotation-packet/private-map.json",
        config["aggregation"],
        allow_mock=True,
    )
    write_rows(output / "annotated.jsonl", rows)
    rows, split = split_speakers(rows, config["split"])
    write_rows(output / "split.dataset.jsonl", rows)
    write_json(output / "split.json", split)
    report = run(rows, split, config, output / "experiment")
    registry = read_json(PACKAGE / "configs/encoders.json")
    primary = FrozenEncoder(registry[config["encoder"]], config["embedding"])
    again, _ = primary.extract_all(rows)
    index = read_json(output / "experiment/embedding-index.json")
    for row in rows:
        expected = np.load(
            PACKAGE / "embeddings/generated" / f"{index[row['example_id']]['cache_key']}.npy",
            allow_pickle=False,
        )
        if not np.array_equal(again[row["example_id"]], expected):
            raise ValueError("Cached embedding differs from first extraction")
    if primary.hits != len(rows):
        raise ValueError("Cache rerun unexpectedly recomputed embeddings")
    secondary_settings = {**config["embedding"], "view": "wide", "pooling": "context_mean"}
    secondary = FrozenEncoder(registry["wavlm_base_plus"], secondary_settings)
    _, metadata = secondary.extract_all(rows[:2])
    write_json(output / "wavlm-smoke.json", metadata)
    summary = {
        "status": "passed",
        "scientific": False,
        "conclusion": (
            "Engineering smoke test only; mock labels and temporary speaker IDs "
            "cannot establish model quality."
        ),
        "baseline": baseline,
        "manifest_examples": len(rows),
        "fixture_speakers": len(speakers),
        "raw_mock_judgments": len(submissions),
        "ungradable_preserved": sum(r["aggregate"]["label"] == "ungradable" for r in rows),
        "partition_counts": report["partition_counts"],
        "packet": packet_result,
        "models_exercised": list(report["models"]),
        "encoders": registry,
        "primary_embeddings": len(rows),
        "secondary_embeddings": len(metadata),
        "cached_rerun_hits": primary.hits,
        "identity": report["identity"],
        "fit_warnings": {k: v.get("fit_warnings", []) for k, v in report["models"].items()},
        "runtime": report["runtime"],
        "full_report": str(output / "experiment/report.json"),
    }
    write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Offline Benma perceptual acceptability pilot")
    parser.add_argument("--config", type=Path, default=PACKAGE / "configs/pilot.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-baseline")
    p = sub.add_parser("init")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--speakers", type=Path, required=True)
    p.add_argument("--dataset-version", required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("preflight")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--packet", type=Path, required=True)
    p = sub.add_parser("import-annotations")
    for flag in ("input", "judgments", "mapping", "output"):
        p.add_argument(f"--{flag}", type=Path, required=True)
    p = sub.add_parser("split")
    for flag in ("input", "output", "split-output"):
        p.add_argument(f"--{flag}", type=Path, required=True)
    p = sub.add_parser("run")
    for flag in ("input", "split", "output"):
        p.add_argument(f"--{flag}", type=Path, required=True)
    p = sub.add_parser("export-features")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("embed")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("stage0")
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = verify_baseline()
    config = validate_config(read_json(args.config))
    if args.command == "verify-baseline":
        result = baseline
    elif args.command == "init":
        rows = upgrade(read_rows(args.input), args.dataset_version, read_json(args.speakers))
        rows, _ = replay(rows)
        write_rows(args.output, rows)
        result = {"examples": len(rows), "output": str(args.output)}
    elif args.command == "preflight":
        rows = validate(read_rows(args.input))
        rows, _ = replay(rows)
        rows = prepare_windows(rows, config["windows"], PACKAGE / "data/generated/audio")
        validate(rows)
        result = packet(rows, args.packet, config["seed"])
        write_rows(args.output, rows)
    elif args.command == "import-annotations":
        rows = import_annotations(
            validate(read_rows(args.input)),
            read_rows(args.judgments),
            args.mapping,
            config["aggregation"],
        )
        write_rows(args.output, rows)
        result = {"examples": len(rows), "raw_judgments": sum(len(r["annotations"]) for r in rows)}
    elif args.command == "split":
        rows, split = split_speakers(validate(read_rows(args.input)), config["split"])
        write_rows(args.output, rows)
        write_json(args.split_output, split)
        result = split
    elif args.command == "run":
        result = run(read_rows(args.input), read_json(args.split), config, args.output)
        result = {"status": result["status"], "report": str(args.output / "report.json")}
    elif args.command == "export-features":
        rows, _ = replay(validate(read_rows(args.input)))
        values, names = matrix(rows, ["benma", "context"])
        args.output.mkdir(parents=True, exist_ok=False)
        np.savez_compressed(
            args.output / "features.npz",
            values=values,
            example_ids=np.array([r["example_id"] for r in rows]),
        )
        write_json(args.output / "schema.json", {"columns": names, "dataset_hash": digest(rows)})
        result = {"rows": len(rows), "columns": len(names)}
    elif args.command == "embed":
        rows = validate(read_rows(args.input))
        registry = read_json(PACKAGE / "configs/encoders.json")
        encoder = FrozenEncoder(registry[config["encoder"]], config["embedding"])
        _, metadata = encoder.extract_all(rows)
        write_json(args.output, metadata)
        result = {
            "embeddings": len(metadata),
            "cache_hits": encoder.hits,
            "cache_misses": encoder.misses,
        }
    else:
        result = stage0(args.output, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
