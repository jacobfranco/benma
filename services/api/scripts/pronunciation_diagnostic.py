"""Generate a self-contained manual waveform/F0/alignment inspection artifact."""

from __future__ import annotations

import argparse
import html
import json
import struct
import uuid
import wave
from pathlib import Path

from sqlalchemy import select

from benma_api.config import get_settings
from benma_api.db.models import (
    AcousticRun,
    AlignmentRun,
    AudioAsset,
    PronunciationAttempt,
    Utterance,
)
from benma_api.db.session import get_session_factory
from benma_api.storage.audio_store import LocalFilesystemAudioStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt_id", type=uuid.UUID)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = get_settings()
    store = LocalFilesystemAudioStore(settings.audio_storage_dir)
    with get_session_factory()() as db:
        attempt = db.get(PronunciationAttempt, args.attempt_id)
        if attempt is None:
            raise SystemExit("attempt not found")
        utterance = db.get(Utterance, attempt.utterance_id)
        if utterance is None:
            raise SystemExit("utterance not found")
        asset = db.get(AudioAsset, utterance.canonical_audio_asset_id)
        acoustic = db.scalar(
            select(AcousticRun)
            .where(AcousticRun.utterance_id == utterance.id)
            .order_by(AcousticRun.created_at.desc())
        )
        alignment = db.scalar(
            select(AlignmentRun)
            .where(AlignmentRun.pronunciation_attempt_id == attempt.id)
            .order_by(AlignmentRun.created_at.desc())
        )
        if asset is None or acoustic is None or acoustic.normalized_result is None:
            raise SystemExit("attempt requires canonical audio and acoustic evidence")
        audio = store.read(asset.storage_key)
        args.output.mkdir(parents=True, exist_ok=True)
        audio_name = "canonical.wav"
        (args.output / audio_name).write_bytes(audio)
        with wave.open(str(store.path_for_processing(asset.storage_key)), "rb") as stream:
            raw = stream.readframes(stream.getnframes())
            rate = stream.getframerate()
        samples = struct.unpack(f"<{len(raw) // 2}h", raw)
        width, height = 1100, 420
        duration = len(samples) / rate
        bucket = max(1, len(samples) // width)
        waveform = []
        for index in range(0, len(samples), bucket):
            value = max(abs(item) for item in samples[index : index + bucket]) / 32768
            x = index / len(samples) * width
            waveform.append(f"{x:.1f},{160 - value * 125:.1f} {x:.1f},{160 + value * 125:.1f}")
        points = acoustic.normalized_result.get("mobile_f0", [])
        f0 = [
            f"{float(item['timestamp_seconds']) / duration * width:.1f},"
            f"{350 - (float(item['normalized_semitones']) + 12) / 24 * 130:.1f}"
            for item in points
            if item.get("normalized_semitones") is not None
        ]
        units = (
            alignment.normalized_result.get("units", [])
            if alignment and alignment.normalized_result
            else []
        )
        boundaries = []
        for unit in units:
            x = float(unit["start_seconds"]) / duration * width
            boundaries.append(
                f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="410" stroke="#a35f2d"/>'
                f'<text x="{x + 4:.1f}" y="18" font-size="12">'
                f'{html.escape(str(unit["label"]))}</text>'
            )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            '<rect width="100%" height="100%" fill="#fff"/>'
            f"{''.join(boundaries)}"
            f'<path d="M {" M ".join(waveform)}" stroke="#586563" fill="none"/>'
            f'<polyline points="{" ".join(f0)}" stroke="#12645c" fill="none" stroke-width="2"/>'
            '<text x="10" y="405" font-size="12">'
            "Waveform (top) · normalized F0 (bottom) · raw boundaries</text>"
            "</svg>"
        )
        (args.output / "diagnostic.svg").write_text(svg, encoding="utf-8")
        metadata = {
            "attempt_id": str(attempt.id),
            "acoustic_run_id": str(acoustic.id),
            "alignment_run_id": str(alignment.id) if alignment else None,
            "alignment_quality": alignment.quality if alignment else "unavailable",
        }
        (args.output / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><h1>Pronunciation diagnostic</h1>"
            f"<audio controls src='{audio_name}'></audio><br><img src='diagnostic.svg'>"
            f"<pre>{html.escape(json.dumps(metadata, indent=2))}</pre>",
            encoding="utf-8",
        )
        print(f"wrote manual diagnostic to {args.output / 'index.html'}")


if __name__ == "__main__":
    main()
