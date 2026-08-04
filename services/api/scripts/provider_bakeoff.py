"""Run every implemented Mandarin evaluator against one immutable audio payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROVIDERS = ("azure", "tencent_sentence", "tencent_pinyin", "iflytek")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="benma-provider-bakeoff")
    parser.add_argument("--sample", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--pinyin", nargs="*", default=[])
    parser.add_argument("--surface-tones", nargs="*", default=[])
    parser.add_argument("--acoustic-json", type=Path)
    parser.add_argument("--alignment-json", type=Path)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _last_json(stdout: str) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _optional_evidence(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"evidence file must be a JSON object: {path}")
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "evidence": value,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.pinyin:
        raise SystemExit("--pinyin numeric syllables are required for the Tencent pinyin mode")
    audio = args.sample.read_bytes()
    audio_hash = hashlib.sha256(audio).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    smoke = Path(__file__).with_name("provider_smoke.py")
    rows: list[dict[str, Any]] = []
    for provider in PROVIDERS:
        capture = args.output / f"{provider}.live-sanitized.json"
        command = [
            sys.executable,
            str(smoke),
            provider,
            "--sample",
            str(args.sample),
            "--target",
            args.target,
            "--pinyin",
            *args.pinyin,
            "--timeout",
            str(args.timeout),
            "--capture",
            str(capture),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        parsed = _last_json(completed.stdout)
        state = (
            "LIVE_VALIDATED"
            if completed.returncode == 0 and capture.exists()
            else "BLOCKED_EXTERNAL"
        )
        row: dict[str, Any] = {
            "provider_configuration": provider,
            "state": state,
            "exit_code": completed.returncode,
            "audio_sha256": audio_hash,
            "capture": str(capture) if capture.exists() else None,
        }
        if parsed is not None:
            row["provider"] = parsed.get("provider")
            row["product"] = parsed.get("product")
            row["adapter_version"] = parsed.get("adapter_version")
            row["request_configuration"] = parsed.get("request_configuration")
            row["transport_timings_ms"] = parsed.get("transport_timings_ms")
        if state == "BLOCKED_EXTERNAL":
            row["reason"] = (completed.stdout or completed.stderr).splitlines()[:2]
        rows.append(row)
    manifest = {
        "run_type": "same_audio_known_target_bakeoff",
        "timestamp": datetime.now(UTC).isoformat(),
        "sample_id": args.sample_id,
        "target_snapshot": {
            "text": args.target,
            "pinyin": args.pinyin,
            "expected_surface_tones": args.surface_tones,
        },
        "audio_path": str(args.sample),
        "audio_sha256": audio_hash,
        "providers": rows,
        "acoustic_evidence": _optional_evidence(args.acoustic_json),
        "alignment_evidence": _optional_evidence(args.alignment_json),
        "truth_note": (
            "A requested production is not ground truth. Human annotation is required before "
            "calibration metrics may use these captures."
        ),
    }
    (args.output / "bakeoff-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Same-audio Mandarin provider bakeoff",
        "",
        f"Audio SHA-256: `{audio_hash}`",
        f"Sample ID: `{args.sample_id}`",
        f"Target: `{args.target}` / `{' '.join(args.pinyin)}`",
        f"Expected surface tones: `{' '.join(args.surface_tones) or 'not supplied'}`",
        "",
        "| Configuration | State | Product | Capture |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['provider_configuration']} | {row['state']} | "
            f"{row.get('product') or 'not reached'} | {row.get('capture') or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Independent evidence",
            "",
            f"Acoustics: `{args.acoustic_json or 'not supplied'}`",
            "",
            f"Alignment: `{args.alignment_json or 'not supplied'}`",
            "",
            manifest["truth_note"],
            "",
        ]
    )
    (args.output / "bakeoff.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if any(row["state"] == "LIVE_VALIDATED" for row in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
