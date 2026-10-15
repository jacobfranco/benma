"""Explicitly approved, bounded unhinted language experiment; no production imports.

A manifest pins exact private WAVs by SHA-256. Never retries or substitutes audio.
Run with the API environment from services/api, supplying absolute manifest/output.
The output contains provider text/metadata, never audio or credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import httpx
from benma_api.config import Settings


def run(manifest: Path, output: Path) -> None:
    entries = json.loads(manifest.read_text())
    if len(entries) != 9 or len({e["id"] for e in entries}) != 9:
        raise ValueError("This approved experiment requires exactly nine distinct frozen items")
    if output.exists():
        raise ValueError("Refusing to repeat an existing experiment")
    for entry in entries:
        if hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Frozen waveform hash mismatch")
    settings = Settings()
    if settings.openai_api_key is None:
        raise ValueError("Configured OpenAI credential unavailable")
    results = []
    for entry in entries:
        started = time.monotonic()
        record = {k: v for k, v in entry.items() if k != "path"}
        record.update(
            model="gpt-transcribe",
            request_fields={"model": "gpt-transcribe", "response_format": "json"},
            prompt_supplied=False,
            language_hint_supplied=False,
        )
        try:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": "Bearer " + settings.openai_api_key.get_secret_value()},
                data=record["request_fields"],
                files={"file": ("canonical.wav", Path(entry["path"]).read_bytes(), "audio/wav")},
                timeout=30,
            )
            record["http_status"] = response.status_code
            record["response"] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            record["request_error"] = type(exc).__name__
        record["latency_seconds"] = time.monotonic() - started
        results.append(record)
        output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(record, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.output)
