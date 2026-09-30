"""Offline frozen V1 adapter: raw waveform -> Praat -> target-independent category."""

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/api/src"))

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.contours import classify_contour
from benma_api.schemas import DisplayContour
from preflight import write_csv, write_json


def run(output, cache):
    sources = [
        "services/api/src/benma_api/pronunciation/" + name
        for name in ("acoustics.py", "contours.py", "evidence_region.py")
    ]
    hashes = {}
    for source in sources:
        historic = subprocess.check_output(["git", "show", "68057aa:" + source])
        current = Path(source).read_bytes()
        if historic != current:
            raise ValueError("V1 source differs from frozen reference")
        hashes[source] = hashlib.sha256(current).hexdigest()
    if not (output / "primary-metrics.json").exists():
        raise ValueError("Primary test must be recorded before comparison")
    rows = [
        r
        for r in csv.DictReader((output / "split-manifest.csv").open())
        if r["partition"] == "test"
    ]
    analyzer = PraatAcousticAnalyzer()
    results, raw_results = [], []
    with tempfile.TemporaryDirectory(prefix="v1-", dir=cache) as tmp:
        for row in rows:
            wav = Path(tmp) / "clip.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    row["local_path"],
                    "-map",
                    "0:a:0",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(wav),
                ],
                check=True,
            )
            with wave.open(str(wav), "rb") as audio:
                duration = audio.getnframes() / audio.getframerate()
            evidence = analyzer.analyze(wav)
            observed = classify_contour(
                DisplayContour(), 0, duration, raw=evidence["f0"], timing_reliable=True
            )
            classification = observed.classification
            category = (
                classification[0]
                if classification in ("1-like", "2-like", "3-like", "4-like")
                else ""
            )
            results.append(
                {
                    "source_asset_id": row["source_asset_id"],
                    "v1_category": category,
                    "v1_observed": classification,
                    "v1_abstain": not bool(category),
                    "v1_ordinal_confidence": observed.confidence,
                    "v1_reason": observed.reason,
                    "v1_voiced_coverage": observed.voiced_coverage,
                    "v1_quality": json.dumps(evidence["recording_quality"], sort_keys=True),
                }
            )
            raw_results.append(
                {
                    "source_asset_id": row["source_asset_id"],
                    "observed": observed.model_dump(),
                    "acoustics": evidence,
                }
            )
    write_csv(output / "v1-results.csv", results)
    write_json(cache / "v1-evidence.json", raw_results)
    write_json(
        output / "v1-config.json",
        {
            "reference": "68057aa",
            "source_sha256": hashes,
            "algorithm": analyzer.algorithm_name,
            "version": analyzer.algorithm_version,
            "parameters": analyzer.parameters,
            "span": "whole isolated clip; no text or tone input",
            "preprocessing": "production-equivalent ffmpeg mono 16kHz PCM16; no trimming",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.cache)
