"""Experiment 3: verify, exclusively lock, then (only in a future pass) evaluate.

Verification imports no encoder/head implementation and performs no inference.
Evaluation requires the externally recorded runner-lock SHA-256 on the command line.
"""

import argparse
import ast
import contextlib
import csv
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import zlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import experiment3_metrics as metrics
import numpy as np
import public_panel as panel

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
FROZEN = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-preflight"
DATA = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-data"
OUT = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-evaluation"
SCHEMA = CODE / "experiment3-output-schema.json"
MANIFEST_SHA = "141a9349da2786b822d6bbb109ff726f97b466bdb0f4548c5a7f1a2874b60490"
SEAL_SHA = "4de7c7d8c5d16409439f449496fe67b1980b798a645bbfcd37963b4527eb6be0"
ARRAYS_SHA = "d3961629af0f7f91005c60911ea408a3fe1d149db2cc986df231765f35170659"
FROZEN_HASHES = {
    "head-linear.npz": "d3f1cbe4a6ac7ea7c76b4538805d57cf99a36dd7d14909432725d4bc5cf696c2",
    "head-nonlinear.npz": "eb2c29fb7473faac715b93cdb1671134d7c408dc87065166b77e50d630efd28d",
    "protocol.lock.json": "f795f15d970043d65592ac9ef7cd3ee4af9b36bf2310de23a840bcf12db08721",
    "heads.lock.json": "bd6e5b5c3d2a52e2f88c7a3b1b87caa8eb0880136de90b9deeb26f251eb18743",
}
REVISION = "0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8"
SPEAKERS = sorted(f"sait-ema:{s}" for s in panel.EXPECTED_SPEAKERS)


def now():
    return datetime.now(UTC).isoformat()


def encoded(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def require_hash(path, expected):
    if digest(path) != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")


def exclusive(path, data):
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def read_json(path):
    return json.loads(path.read_text())


def environment(protocol):
    expected = protocol["environment"]
    packages = {name: importlib.metadata.version(name) for name in expected["packages"]}
    observed = {
        **expected,
        "packages": packages,
        "versions": {name: packages[name] for name in expected["versions"]},
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ffmpeg": subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
    }
    if observed != expected:
        raise ValueError("Frozen protocol environment/package versions changed")
    return {
        "protocol_environment": observed,
        "installed_distributions": sorted(
            (d.metadata["Name"], d.version) for d in importlib.metadata.distributions()
        ),
        "executables_sha256": {
            name: digest(path)
            for name, path in {
                "python": sys.executable,
                "ffmpeg": shutil.which("ffmpeg"),
                "ffprobe": shutil.which("ffprobe"),
            }.items()
        },
        "head_torch_threads": 1,
        "encoder_torch_threads": 4,
        "blas_threads": 1,
        "device": "cpu",
        "dtype": "float32",
    }


def verify_composition(rows):
    panel.validate_composition(rows)
    if sorted({r["speaker_id"] for r in rows}) != SPEAKERS:
        raise ValueError("Exact speaker IDs changed")
    if len({r["source_asset_id"] for r in rows}) != 720:
        raise ValueError("Duplicate/missing source asset")
    if Counter(r["tone"] for r in rows) != dict.fromkeys("1234", 180):
        raise ValueError("Aggregate tone counts changed")
    if any(r["speaker_id"] != "sait-ema:" + r["speaker_name"] for r in rows):
        raise ValueError("Speaker name/ID mismatch")


def verify_audio(row):
    """Recompute source and both PCM hashes; no features or amplitude diagnostics."""
    path = ROOT / row["local_path"]
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if (
        sha != row["audio_sha256"]
        or sha != row["source_sha256"]
        or hashlib.sha1(raw).hexdigest() != row["source_sha1"]
        or zlib.crc32(raw) != int(row["archive_crc32"])
        or len(raw) != int(row["source_bytes"])
    ):
        raise ValueError(f"Source/file hash mismatch: {row['source_asset_id']}")
    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)], timeout=30
        )
    )
    streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if len(streams) != 1:
        raise ValueError("Expected one audio stream")
    rate, channels = int(streams[0]["sample_rate"]), int(streams[0]["channels"])
    if rate != int(row["sample_rate_hz"]) or channels != int(row["channels"]):
        raise ValueError("Source decode format changed")
    pcm = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-",
        ],
        timeout=30,
    )
    source_hash = hashlib.sha256(f"{rate}:{channels}:f32le:".encode() + pcm).hexdigest()
    if source_hash != row["decoded_pcm_sha256"]:
        raise ValueError("Source PCM hash changed")
    if len(pcm) / 4 / rate / channels != float(row["duration_seconds"]):
        raise ValueError("Decoded duration changed")
    evaluation_pcm = panel.mono16_pcm(path)
    if hashlib.sha256(evaluation_pcm).hexdigest() != row["evaluation_pcm_sha256"]:
        raise ValueError("Mono 16 kHz preprocessing PCM changed")
    if not np.isfinite(np.frombuffer(evaluation_pcm, dtype="<f4")).all():
        raise ValueError("Nonfinite evaluation PCM")


def source_hashes():
    # Includes transitive local imports, every research test and both schemas/config locks.
    paths = [
        *CODE.glob("*.py"),
        SCHEMA,
        CODE / "requirements-lock.txt",
        ROOT / "pyproject.toml",
        OUT / "runner-spec.md",
        OUT / "validation.json",
    ]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def frozen_state():
    require_hash(DATA / "sealed-test-manifest.csv", MANIFEST_SHA)
    require_hash(DATA / "seal.json", SEAL_SHA)
    for name, expected in FROZEN_HASHES.items():
        require_hash(FROZEN / name, expected)
    protocol = read_json(FROZEN / "protocol.lock.json")
    for name, expected in protocol["files_sha256"].items():
        require_hash(ROOT / name, expected)
    encoder = protocol["encoder"]
    if (
        encoder["revision"] != REVISION
        or encoder["model_id"] != "facebook/wav2vec2-base"
        or Path(encoder["snapshot"]).name != REVISION
        or protocol["layer"] != 8
    ):
        raise ValueError("Frozen representation changed")
    for name, expected in encoder["files_sha256"].items():
        require_hash(Path(encoder["snapshot"]) / name, expected)
    # Transformers must not prefer a newly added, unpinned alternative weight/config file.
    if {p.name for p in Path(encoder["snapshot"]).iterdir()} != set(encoder["files_sha256"]):
        raise ValueError("Encoder snapshot file set changed")
    tree = ast.parse((CODE / "features.py").read_text())
    preprocessing = next(
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "PREPROCESSING" for t in n.targets)
    )
    if preprocessing != protocol["preprocessing"]:
        raise ValueError("Frozen preprocessing config changed")
    env = environment(protocol)
    seal = read_json(DATA / "seal.json")
    if seal["heads_lock_sha256"] != FROZEN_HASHES["heads.lock.json"]:
        raise ValueError("Seal/head binding changed")
    heads = read_json(FROZEN / "heads.lock.json")
    if heads["nonlinear_arrays_sha256"] != ARRAYS_SHA:
        raise ValueError("Nonlinear array commitment changed")
    # Read-only array integrity, no classifier construction or prediction.
    with np.load(FROZEN / "head-nonlinear.npz", allow_pickle=False) as arrays:
        hashed = hashlib.sha256()
        for key in sorted(arrays.files):
            value = np.ascontiguousarray(arrays[key])
            hashed.update(json.dumps([key, value.dtype.str, list(value.shape)]).encode())
            hashed.update(value.tobytes())
        if hashed.hexdigest() != ARRAYS_SHA:
            raise ValueError("Nonlinear array bytes changed")
    return {
        "manifest_sha256": MANIFEST_SHA,
        "seal_sha256": SEAL_SHA,
        "frozen_sha256": FROZEN_HASHES,
        "nonlinear_arrays_sha256": ARRAYS_SHA,
        "encoder": encoder,
        "representation": {
            "layer": 8,
            "dimensions": 768,
            "pooling": "whole-valid-frame mean",
            "eval": True,
            "gradients": False,
        },
        "preprocessing": preprocessing,
        "preprocessing_sha256": hashlib.sha256(encoded(preprocessing)).hexdigest(),
        "source_sha256": source_hashes(),
        "environment": env,
        "metric_definitions": metrics.METRIC_DEFINITIONS,
        "bootstrap": metrics.BOOTSTRAP,
        "promising_rule": metrics.DECISION,
        "output_schema_version": metrics.VERSION,
        "output_schema_sha256": digest(SCHEMA),
        "expected_speaker_ids": SPEAKERS,
        "expected_rows": 720,
    }


def require_runner_lock(expected_sha, state):
    if not expected_sha or len(expected_sha) != 64:
        raise ValueError("An externally recorded --lock-sha256 is required")
    require_hash(OUT / "runner.lock.json", expected_sha)
    locked = read_json(OUT / "runner.lock.json")
    # JSON round trip normalizes tuples from package metadata before exact comparison.
    if locked["frozen_state"] != json.loads(encoded(state)):
        raise ValueError("Runner source/schema/input/environment differs from lock")
    if locked["test_predictions_opened"] is not False:
        raise ValueError("Runner was not locked before test opening")
    return locked


def verify(expected_lock=None, *, require_lock=False):
    if (OUT / "opened").exists():
        raise FileExistsError("Test opening already claimed; no retries or silent overwrite")
    state = frozen_state()
    if require_lock or (OUT / "runner.lock.json").exists():
        require_runner_lock(expected_lock, state)
    with contextlib.redirect_stdout(io.StringIO()):
        panel.verify_seal()
    rows = panel.csv_rows(DATA / "sealed-test-manifest.csv")
    verify_composition(rows)
    # Independent read-only decodes; ordered map propagates every failure before inference.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(verify_audio, rows), 1):
            if i % 120 == 0:
                print(f"Verified source and PCM hashes: {i}/720", file=sys.stderr, flush=True)
    panel.check_no_staged_audio()
    return state, rows


def lock():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "runner.lock.json").exists() or (OUT / "runner.lock.sha256").exists():
        raise FileExistsError("Runner lock is immutable; refusing replacement")
    validation = read_json(OUT / "validation.json")
    if validation["required_checks_passed"] is not True:
        raise ValueError("Passing focused validation is required before locking")
    for path, expected in validation["tested_files_sha256"].items():
        require_hash(ROOT / path, expected)
    state, _ = verify()
    receipt = {
        "locked_at": now(),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "git_branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip(),
        "test_predictions_opened": False,
        "embeddings_computed": False,
        "frozen_state": state,
    }
    exclusive(OUT / "runner.lock.json", encoded(receipt))
    sha = digest(OUT / "runner.lock.json")
    exclusive(OUT / "runner.lock.sha256", (sha + "  runner.lock.json\n").encode())
    print(
        json.dumps(
            {
                "status": "VERIFIED_SEALED_UNOPENED",
                "runner_lock_sha256": sha,
                "locked_at": receipt["locked_at"],
            }
        )
    )


def infer(rows, protocol):
    """Future-only model boundary. No labels, status, text or speakers enter either head."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from features import encode_waveforms, freeze, load_waveform, state_digest
    from model_probe import predict_head
    from threadpoolctl import threadpool_limits
    from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model

    torch.set_num_threads(4)
    torch.manual_seed(20260929)
    torch.use_deterministic_algorithms(True)
    snapshot = protocol["encoder"]["snapshot"]
    model, loading = Wav2Vec2Model.from_pretrained(
        snapshot,
        local_files_only=True,
        attn_implementation="eager",
        output_loading_info=True,
        use_safetensors=False,
        torch_dtype=torch.float32,
    )
    if loading["missing_keys"] or loading["mismatched_keys"] or loading["error_msgs"]:
        raise ValueError("Incomplete frozen encoder")
    model = freeze(model.to(device="cpu", dtype=torch.float32))
    processor = Wav2Vec2FeatureExtractor.from_pretrained(snapshot, local_files_only=True)
    before = state_digest(model)
    features = []
    ids = []
    for row in rows:
        path = ROOT / row["local_path"]
        require_hash(path, row["audio_sha256"])
        wave = load_waveform(path)
        if (
            hashlib.sha256(wave.astype("<f4", copy=False).tobytes()).hexdigest()
            != row["evaluation_pcm_sha256"]
        ):
            raise ValueError("Inference waveform differs from verified PCM")
        features.append(encode_waveforms(model, processor, [wave], layers=(8,))[8][0])
        ids.append(row["source_asset_id"])
    if state_digest(model) != before or any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Encoder mutated or received gradients")
    x = np.stack(features)
    if x.shape != (len(rows), 768) or x.dtype != np.float32 or not np.isfinite(x).all():
        raise ValueError("Invalid frozen representation")
    with threadpool_limits(limits=1):
        probability_a = predict_head(FROZEN / "head-linear.npz", x)
        probability_b = nonlinear_probabilities(x)
    return metrics.prediction_records(rows, ids, probability_a, probability_b)


def nonlinear_probabilities(x):
    import torch

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    with np.load(FROZEN / "head-nonlinear.npz", allow_pickle=False) as arrays:
        head = torch.nn.Sequential(torch.nn.Linear(768, 8), torch.nn.Tanh(), torch.nn.Linear(8, 4))
        head.load_state_dict(
            {
                k: torch.from_numpy(arrays[k].copy())
                for k in ("0.weight", "0.bias", "2.weight", "2.bias")
            },
            strict=True,
        )
        head.to(device="cpu", dtype=torch.float32).eval().requires_grad_(False)
        # StandardScaler.transform preserves float32 input with two in-place operations.
        values = np.asarray(x, dtype=np.float32).copy()
        values -= arrays["mean"]
        values /= arrays["scale"]
        with torch.inference_mode():
            return torch.softmax(head(torch.from_numpy(values)), dim=1).numpy()


def validate_schema(value, schema, definitions):
    """Strict validator for the deliberately small JSON Schema subset used by this runner."""
    if "$ref" in schema:
        return validate_schema(value, definitions[schema["$ref"].split("/")[-1]], definitions)
    if "anyOf" in schema:
        for choice in schema["anyOf"]:
            try:
                validate_schema(value, choice, definitions)
                return
            except ValueError:
                pass
        raise ValueError("Schema anyOf failed")
    kind = schema.get("type")
    types = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    if kind and (
        not isinstance(value, types[kind])
        or (kind in {"integer", "number"} and isinstance(value, bool))
    ):
        raise ValueError(f"Schema type mismatch: {kind}")
    if "const" in schema and value != schema["const"]:
        raise ValueError("Schema constant mismatch")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("Schema enum mismatch")
    if kind == "object":
        props = schema.get("properties", {})
        if not set(schema.get("required", [])) <= set(value):
            raise ValueError("Missing required schema fields")
        for key, item in value.items():
            child = props.get(key, schema.get("additionalProperties", False))
            if child is False:
                raise ValueError(f"Unexpected schema field: {key}")
            if child is not True:
                validate_schema(item, child, definitions)
    if kind == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get(
            "maxItems", float("inf")
        ):
            raise ValueError("Schema array length mismatch")
        for item in value:
            validate_schema(item, schema["items"], definitions)
    if kind in {"number", "integer"} and (
        not np.isfinite(value)
        or value < schema.get("minimum", -float("inf"))
        or value > schema.get("maximum", float("inf"))
    ):
        raise ValueError("Schema numeric bounds mismatch")


def validate_output(name, value):
    spec = read_json(SCHEMA)
    validate_schema(value, spec["outputs"][name], spec["$defs"])


def review(results, boot):
    lines = [
        "# Experiment 3 evaluation",
        "",
        "Primary evidence: ALL 18 source-declared speakers / ALL 720 sealed clips. No exclusions.",
        "Raw probabilities are uncalibrated; no abstention or confidence threshold.",
        "",
        f"Preregistered promising rule: {results['decision']['promising']}.",
        "Failed conditions: "
        + (", ".join(results["decision"]["failed_conditions"]) or "none")
        + ".",
        results["decision"]["interpretation"],
        "",
        metrics.UNCERTAINTY,
        "",
        "Source-declared NATIVE controls and LEARNER groups are secondary descriptive results; "
        "they do not replace the primary panel or infer status beyond source documentation.",
        "",
        "Complete metrics, per-tone/support/confusions, paired categories, speaker differences, "
        "subgroups and decision checks follow (B minus A):",
        "",
        "```json",
        json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False),
        "```",
        "",
        "Paired speaker-bootstrap percentile 95% intervals:",
        "",
        "```json",
        json.dumps(boot["intervals_95_percent"], indent=2, allow_nan=False),
        "```",
        "",
    ]
    return "\n".join(lines)


def evaluate(expected_lock):
    state, rows = verify(expected_lock, require_lock=True)  # All checks precede model access.
    destination = OUT / "opened"
    destination.mkdir()  # Exclusive claim survives failure; automatic retries are prohibited.
    exclusive(
        destination / "opening-receipt.json",
        encoded(
            {
                "opened_at": now(),
                "runner_lock_sha256": expected_lock,
                "manifest_sha256": MANIFEST_SHA,
                "test_access_authorized": True,
            }
        ),
    )
    records = infer(rows, read_json(FROZEN / "protocol.lock.json"))
    metrics.validate_records(rows, records)
    results = metrics.report(rows, records)
    boot = metrics.bootstrap(rows, records)
    validate_output("predictions.csv", records)
    validate_output("results.json", results)
    validate_output("bootstrap.json", boot)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=metrics.COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    metrics.validate_records(rows, list(csv.DictReader(io.StringIO(stream.getvalue()))))
    exclusive(destination / "predictions.csv", stream.getvalue().encode())
    exclusive(destination / "results.json", encoded(results))
    exclusive(destination / "bootstrap.json", encoded(boot))
    exclusive(destination / "review.md", review(results, boot).encode())
    # Check pinned inputs/code again without invoking an unopened-panel claim.
    if frozen_state() != state:
        raise ValueError("Frozen state changed during evaluation; outputs are incomplete")
    receipt = {
        "schema_version": metrics.VERSION,
        "completed_at": now(),
        "status": "COMPLETE",
        "runner_lock_sha256": expected_lock,
        "manifest_sha256": MANIFEST_SHA,
        "rows": len(records),
        "speakers": len(SPEAKERS),
        "test_predictions_opened": True,
        "artifacts_sha256": {p.name: digest(p) for p in sorted(destination.iterdir())},
    }
    validate_output("evaluation-receipt.json", receipt)
    exclusive(destination / "evaluation-receipt.json", encoded(receipt))
    print(json.dumps({"status": "COMPLETE", "output": str(destination)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("verify", "lock", "evaluate"))
    parser.add_argument("--lock-sha256", help="Externally recorded immutable runner-lock digest")
    args = parser.parse_args()
    if args.stage == "evaluate":
        if not args.lock_sha256:
            parser.error("evaluate requires --lock-sha256")
        evaluate(args.lock_sha256)
    elif args.stage == "lock":
        lock()
    else:
        state, rows = verify(args.lock_sha256)
        print(
            json.dumps(
                {
                    "status": "VERIFIED_SEALED_UNOPENED",
                    "rows": len(rows),
                    "manifest_sha256": state["manifest_sha256"],
                }
            )
        )


if __name__ == "__main__":
    main()
