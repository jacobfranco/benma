"""Canonical PCM audio preflight, bounded crops, and blinded static packets."""

import copy
import hashlib
import math
import random
import shutil
import wave
from pathlib import Path

from .annotations import item_id
from .common import PACKAGE, digest, file_hash, resolve, write_json, write_rows


def read_audio(reference, expected_hash=None):
    path = resolve(reference)
    if expected_hash and file_hash(path) != expected_hash:
        raise ValueError(f"Audio checksum mismatch: {path}")
    with wave.open(str(path), "rb") as stream:
        if (
            stream.getnchannels() != 1
            or stream.getsampwidth() != 2
            or stream.getcomptype() != "NONE"
        ):
            raise ValueError("Use canonical mono PCM16 WAV input; no implicit audio conversion")
        sample_rate, count = stream.getframerate(), stream.getnframes()
        pcm = stream.readframes(count)
    if len(pcm) != count * 2:
        raise ValueError("Truncated WAV")
    return pcm, sample_rate, count


def bounds(start, end, count, rate, before, after):
    if not all(math.isfinite(v) for v in (start, end, before, after)):
        raise ValueError("Non-finite audio bounds")
    if not (0 <= start < end <= count / rate and before >= 0 and after >= 0):
        raise ValueError("Target outside recording or invalid context size")
    return max(0, math.floor((start - before) * rate)), min(count, math.ceil((end + after) * rate))


def _crop(pcm, rate, start, end, directory):
    cropped = pcm[start * 2 : end * 2]
    pcm_hash = hashlib.sha256(cropped).hexdigest()
    key = digest({"pcm_sha256": pcm_hash, "sample_rate_hz": rate, "format": "mono-pcm16-v1"})
    path = directory / f"{key}.wav"
    if not path.exists():
        with path.open("xb") as output, wave.open(output, "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(cropped)
    check, check_rate, _ = read_audio(str(path))
    if check != cropped or check_rate != rate:
        raise ValueError("Corrupt audio cache entry")
    return {
        "reference": str(path.resolve()),
        "sha256": file_hash(path),
        "pcm_sha256": pcm_hash,
        "sample_rate_hz": rate,
        "start_sample": start,
        "end_sample": end,
        "start_seconds": start / rate,
        "end_seconds": end / rate,
    }


def prepare_windows(rows, config, cache_dir):
    if set(config) != {"local", "wide"}:
        raise ValueError("Window config requires local and wide views")
    for value in config.values():
        if set(value) != {"before_seconds", "after_seconds"}:
            raise ValueError("Unknown window size setting")
    if any(config["wide"][k] < config["local"][k] for k in config["local"]):
        raise ValueError("Wide context must include local context")
    directory = Path(cache_dir)
    directory.mkdir(parents=True, exist_ok=True)
    result, sources = copy.deepcopy(rows), {}
    for row in result:
        reference, sha = row["audio"]["reference"], row["audio"]["sha256"]
        key = (reference, sha)
        if key not in sources:
            sources[key] = read_audio(reference, sha)
        pcm, rate, count = sources[key]
        if rate != row["audio"]["sample_rate_hz"]:
            raise ValueError("Manifest sample rate differs from audio")
        if row["context_window"]["end_seconds"] > count / rate:
            raise ValueError("Original context window exceeds audio bounds")
        t = row["target"]
        views = {"target": {"before_seconds": 0, "after_seconds": 0}, **config}
        row["windows"] = {}
        for name, size in views.items():
            start, end = bounds(
                t["start_seconds"],
                t["end_seconds"],
                count,
                rate,
                size["before_seconds"],
                size["after_seconds"],
            )
            row["windows"][name] = _crop(pcm, rate, start, end, directory)
    return result


def verify_window_config(rows, config):
    sources = {}
    for row in rows:
        key = (row["audio"]["reference"], row["audio"]["sha256"])
        if key not in sources:
            sources[key] = read_audio(*key)
        _, rate, count = sources[key]
        for view, size in {"target": {"before_seconds": 0, "after_seconds": 0}, **config}.items():
            expected = bounds(
                row["target"]["start_seconds"],
                row["target"]["end_seconds"],
                count,
                rate,
                size["before_seconds"],
                size["after_seconds"],
            )
            window = row["windows"][view]
            if expected != (window["start_sample"], window["end_sample"]):
                raise ValueError("Manifest windows differ from experiment window config")


def packet(rows, destination, seed=20261015):
    """Only public/ is distributed; private-map.json never leaves the researcher."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    public = destination / "public"
    public.mkdir()
    (public / "audio").mkdir()
    items, mapping = [], {}
    for row in rows:
        if row["target"]["unit_kind"] != "syllable":
            continue
        identifier = item_id(row)
        if identifier in mapping:
            raise ValueError("Duplicate annotation item")
        mapping[identifier] = row["example_id"]
        audio = {}
        for view in ("target", "local", "wide"):
            window = row["windows"][view]
            source = resolve(window["reference"])
            if file_hash(source) != window["sha256"]:
                raise ValueError("Window changed before packet creation")
            name = f"audio/{identifier}-{view}.wav"
            shutil.copyfile(source, public / name)
            audio[view] = {
                "reference": name,
                "target_start_seconds": row["target"]["start_seconds"] - window["start_seconds"],
                "target_end_seconds": row["target"]["end_seconds"] - window["start_seconds"],
            }
        # Full utterance remains available if the configured wide crop lacks context.
        source = resolve(row["audio"]["reference"])
        if file_hash(source) != row["audio"]["sha256"]:
            raise ValueError("Recording changed before packet creation")
        full = f"audio/{identifier}-utterance.wav"
        shutil.copyfile(source, public / full)
        items.append(
            {
                "item_id": identifier,
                "utterance": row["utterance"],
                "target_hanzi": row["target"]["syllable"],
                "syllable_index": row["target"]["syllable_index"],
                "audio": audio,
                "full_utterance_audio": full,
            }
        )
    random.Random(seed).shuffle(items)
    write_json(destination / "private-map.json", {"version": 1, "items": mapping})
    write_rows(public / "items.jsonl", items)
    write_rows(
        public / "responses.template.jsonl",
        [
            {
                "item_id": i["item_id"],
                "judgment_id": "REPLACE_WITH_UNIQUE_JUDGMENT_ID",
                "annotator_id": "REPLACE_WITH_LISTENER_PSEUDONYM",
                "acceptability": None,
                "perceived_tone": None,
                "confidence": None,
                "notes": None,
                "timestamp": "REPLACE_WITH_ISO8601_TIMESTAMP",
                "rubric_version": "1.0",
                "version": 1,
                "supersedes": None,
                "origin": "human",
            }
            for i in items
        ],
    )
    shutil.copyfile(PACKAGE / "annotations/LISTENER_GUIDE.md", public / "LISTENER_GUIDE.md")
    return {"items": len(items), "public_directory": str(public), "seed": seed}
