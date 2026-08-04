"""Explicit, one-attempt production-to-benchmark research export boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from sqlalchemy.orm import Session

from benma_api.db.models import (
    AudioAsset,
    PronunciationAttempt,
    PronunciationTarget,
    ResearchExport,
    Utterance,
)
from benma_api.storage.audio_store import AudioObjectStore

RequestedProduction = Literal[
    "correct", "wrong_tone", "wrong_initial", "wrong_final", "negative_control"
]


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "undocumented"
    return result.stdout.strip() or "undocumented"


def export_pronunciation_attempt(
    db: Session,
    store: AudioObjectStore,
    *,
    attempt_id: uuid.UUID,
    output: Path,
    requested_production: RequestedProduction,
    confirmed: bool,
    notes: str | None = None,
) -> Path:
    if not confirmed:
        raise ValueError("refusing export without explicit research-export confirmation")
    attempt = db.get(PronunciationAttempt, attempt_id)
    if attempt is None:
        raise ValueError("attempt not found")
    utterance = db.get(Utterance, attempt.utterance_id)
    target = db.get(PronunciationTarget, attempt.target_id)
    if utterance is None or target is None:
        raise ValueError("attempt has missing target or utterance")
    original = db.get(AudioAsset, utterance.original_audio_asset_id)
    canonical = db.get(AudioAsset, utterance.canonical_audio_asset_id)
    if original is None or canonical is None:
        raise ValueError("attempt has missing audio evidence")
    original_bytes = store.read(original.storage_key)
    canonical_bytes = store.read(canonical.storage_key)
    if hashlib.sha256(original_bytes).hexdigest() != original.sha256:
        raise ValueError("original audio bytes do not match stored hash")
    if hashlib.sha256(canonical_bytes).hexdigest() != canonical.sha256:
        raise ValueError("canonical audio bytes do not match stored hash")
    destination = output.resolve() / str(attempt.id)
    if destination.exists():
        raise FileExistsError(f"export destination already exists: {destination}")
    destination.mkdir(parents=True)
    original_suffix = Path(original.storage_key).suffix or ".audio"
    original_name = f"original{original_suffix}"
    canonical_name = "canonical.wav"
    (destination / original_name).write_bytes(original_bytes)
    (destination / canonical_name).write_bytes(canonical_bytes)
    metadata = {
        "schema_version": "1.1.0",
        "source": "explicit_production_export",
        "exported_at": datetime.now(UTC).isoformat(),
        "export_tool_version": "production-attempt-export-v2",
        "git_commit_sha": _git_commit(),
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
        "requested_production": requested_production,
        "requested_production_is_ground_truth": False,
        "notes": notes,
        "audio": {
            "original": original_name,
            "canonical": canonical_name,
            "original_sha256": original.sha256,
            "canonical_sha256": canonical.sha256,
        },
        "consent_scope": "personal_development_only",
        "automatic_benchmark_import": False,
        "deletion_semantics": (
            "This is an independent explicit research copy. Production deletion does not "
            "silently mutate it; delete the export separately when required."
        ),
    }
    (destination / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    db.add(
        ResearchExport(
            account_id=attempt.account_id,
            pronunciation_attempt_id=attempt.id,
            export_metadata={
                "destination": str(destination),
                "requested_production": requested_production,
                "requested_production_is_ground_truth": False,
                "canonical_sha256": canonical.sha256,
                "export_tool_version": "production-attempt-export-v2",
            },
        )
    )
    db.commit()
    return destination
