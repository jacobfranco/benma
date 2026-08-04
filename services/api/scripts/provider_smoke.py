"""Credential-aware live known-target smoke test; never falls back to replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
import wave
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from benma_api.config import Settings
from benma_api.speech.contracts import KnownTargetAssessmentInput
from benma_api.speech.providers.factory import build_assessment_provider
from benma_api.speech.raw_evidence import encode_raw_payload


def _sanitize(value: object) -> object:
    forbidden = {"signature", "authorization", "secret", "secretid", "secretkey", "apikey"}
    if isinstance(value, dict):
        return {
            str(key): _sanitize(item)
            for key, item in value.items()
            if str(key).lower().replace("_", "") not in forbidden
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _wav_metadata(path: Path) -> dict[str, Any]:
    try:
        with wave.open(str(path), "rb") as stream:
            metadata = {
                "sample_rate_hz": stream.getframerate(),
                "channels": stream.getnchannels(),
                "sample_width_bits": stream.getsampwidth() * 8,
                "duration_seconds": stream.getnframes() / stream.getframerate(),
            }
    except (wave.Error, EOFError) as exc:
        raise SystemExit(f"sample must be a readable PCM WAV: {exc}") from exc
    expected = (16000, 1, 16)
    actual = (
        metadata["sample_rate_hz"],
        metadata["channels"],
        metadata["sample_width_bits"],
    )
    if actual != expected:
        raise SystemExit(f"sample must be canonical 16kHz mono PCM16 WAV; got {actual}")
    return metadata


def _git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "undocumented"
    return completed.stdout.strip() or "undocumented"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="benma-provider-smoke")
    parser.add_argument(
        "provider",
        choices=["azure", "tencent_sentence", "tencent_pinyin", "iflytek"],
    )
    parser.add_argument("--sample", required=True, type=Path)
    parser.add_argument("--target", required=True)
    parser.add_argument("--pinyin", nargs="*", default=[])
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument(
        "--capture",
        type=Path,
        help="optional path for a sanitized LIVE_CAPTURED_SANITIZED response fixture",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.provider == "tencent_pinyin" and not args.pinyin:
        raise SystemExit("--pinyin numeric syllables are required for Tencent pinyin mode")
    metadata = _wav_metadata(args.sample)
    audio = args.sample.read_bytes()
    try:
        settings = Settings(assessment_provider=args.provider)
    except ValidationError as exc:
        print(f"BLOCKED_EXTERNAL: {args.provider} credentials/configuration unavailable")
        print(str(exc).splitlines()[0])
        return 2
    provider = build_assessment_provider(settings)
    request = KnownTargetAssessmentInput(
        attempt_id=uuid.uuid4(),
        canonical_audio=audio,
        mime_type="audio/wav",
        target_snapshot={
            "text": args.target,
            "pinyin_syllables": args.pinyin,
            "surface_tone_expectation": {},
        },
        timeout_seconds=args.timeout,
    )
    response = provider.assess(request)
    raw = _sanitize(response.raw_payload)
    raw_hash = encode_raw_payload(raw).sha256
    output = {
        "capture_type": "LIVE_REQUEST_SUCCEEDED",
        "lifecycle": "LIVE_VALIDATED",
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit_sha": _git_commit(),
        "provider": provider.provider_name,
        "product": provider.product_name,
        "provider_version": response.provider_version or "undocumented",
        "adapter_version": provider.adapter_version,
        "target": args.target,
        "audio_sha256": hashlib.sha256(audio).hexdigest(),
        **metadata,
        "request_configuration": response.request_configuration or {},
        "transport_timings_ms": response.transport_timings_ms or {},
        "raw_response_sha256": raw_hash,
        "estimated_billable_units": 1 if args.provider.startswith("tencent_") else None,
        "estimated_cost_usd": 0.000699 if args.provider.startswith("tencent_") else None,
        "pricing_provenance": (
            {
                "pricing_date": "2026-08-03",
                "source": "https://cloud.tencent.com/document/product/1774/107342",
                "conversion": "0.005 CNY/call at provisional 7.15 CNY/USD",
            }
            if args.provider.startswith("tencent_")
            else {"status": "unknown_until_account_quote_or_observed_bill"}
        ),
        "normalized_evidence": response.evidence.normalized(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.capture:
        args.capture.parent.mkdir(parents=True, exist_ok=True)
        captured = {
            **output,
            "capture_type": "LIVE_CAPTURED_SANITIZED",
            "raw_response": raw,
        }
        args.capture.write_text(
            json.dumps(captured, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote sanitized live capture to {args.capture}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
