"""Deliberately export one production attempt for later benchmark import.

This personal-development command is not a substitute for public-user consent.
"""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from benma_api.config import get_settings
from benma_api.db.session import get_session_factory
from benma_api.pronunciation.research_export import export_pronunciation_attempt
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
    settings = get_settings()
    store = LocalFilesystemAudioStore(settings.audio_storage_dir)
    try:
        with get_session_factory()() as db:
            destination = export_pronunciation_attempt(
                db,
                store,
                attempt_id=args.attempt_id,
                output=args.output,
                requested_production=args.requested_production,
                confirmed=args.confirm_research_export,
                notes=args.notes,
            )
    except (FileExistsError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"exported {args.attempt_id} to {destination}; benchmark import remains separate")


if __name__ == "__main__":
    main()
