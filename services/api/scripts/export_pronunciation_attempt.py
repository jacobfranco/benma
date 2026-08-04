"""Deliberately export one production attempt for later benchmark import.

This personal-development command is not a substitute for public-user consent.
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from benma_api.config import get_settings
from benma_api.db.models import (
    AudioAsset,
    PronunciationAttempt,
    PronunciationTarget,
    ResearchExport,
    Utterance,
)
from benma_api.db.session import get_session_factory
from benma_api.storage.audio_store import LocalFilesystemAudioStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt_id", type=uuid.UUID)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--requested-production",
        required=True,
        choices=("correct", "wrong_tone", "wrong_initial", "wrong_final", "negative_control"),
    )
    parser.add_argument("--notes")
    parser.add_argument("--confirm-research-export", action="store_true")
    args = parser.parse_args()
    if not args.confirm_research_export:
        raise SystemExit("refusing export without --confirm-research-export")
    settings = get_settings()
    store = LocalFilesystemAudioStore(settings.audio_storage_dir)
    with get_session_factory()() as db:
        attempt = db.get(PronunciationAttempt, args.attempt_id)
        if attempt is None:
            raise SystemExit("attempt not found")
        utterance = db.get(Utterance, attempt.utterance_id)
        target = db.get(PronunciationTarget, attempt.target_id)
        if utterance is None or target is None:
            raise SystemExit("attempt has missing target or utterance")
        original = db.get(AudioAsset, utterance.original_audio_asset_id)
        canonical = db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if original is None or canonical is None:
            raise SystemExit("attempt has missing audio evidence")
        destination = args.output.resolve() / str(attempt.id)
        if destination.exists():
            raise SystemExit(f"export destination already exists: {destination}")
        destination.mkdir(parents=True)
        original_suffix = Path(original.storage_key).suffix or ".audio"
        original_name = f"original{original_suffix}"
        canonical_name = "canonical.wav"
        (destination / original_name).write_bytes(store.read(original.storage_key))
        (destination / canonical_name).write_bytes(store.read(canonical.storage_key))
        metadata = {
            "schema_version": "1.0.0",
            "source": "explicit_production_export",
            "production_attempt_id": str(attempt.id),
            "production_utterance_id": str(utterance.id),
            "target": {
                "text": target.text,
                "display_pinyin": target.display_pinyin,
                "pinyin_syllables": target.pinyin_syllables,
                "lexical_tones": target.lexical_tones,
                "surface_tone_expectation": target.surface_tone_expectation,
                "pinyin_source": target.pinyin_source,
            },
            "requested_production": args.requested_production,
            "notes": args.notes,
            "audio": {
                "original": original_name,
                "canonical": canonical_name,
                "original_sha256": original.sha256,
                "canonical_sha256": canonical.sha256,
            },
            "consent_scope": "personal_development_only",
            "automatic_benchmark_import": False,
        }
        (destination / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        export = ResearchExport(
            account_id=attempt.account_id,
            pronunciation_attempt_id=attempt.id,
            export_metadata={
                "destination": str(destination),
                "requested_production": args.requested_production,
                "canonical_sha256": canonical.sha256,
            },
        )
        db.add(export)
        db.commit()
        print(f"exported {attempt.id} to {destination}; benchmark import remains separate")


if __name__ == "__main__":
    main()
