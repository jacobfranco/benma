"""Stable serialization and write-once artifacts."""

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[1]
LABELS = ("acceptable", "borderline", "incorrect")
ALL_LABELS = (*LABELS, "ungradable")
PARTITIONS = ("train", "validation", "test")


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        for row in rows:
            stream.write(canonical(row) + b"\n")


def resolve(reference):
    path = Path(reference)
    return path if path.is_absolute() else ROOT / path


def runtime():
    versions = {}
    for name in (
        "numpy",
        "scipy",
        "scikit-learn",
        "torch",
        "transformers",
        "huggingface-hub",
        "safetensors",
        "tokenizers",
        "joblib",
        "threadpoolctl",
    ):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": versions,
    }
