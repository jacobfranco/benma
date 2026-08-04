"""Create explicit development-only data without synthetic evidence rows."""

from __future__ import annotations

from sqlalchemy import select

from benma_api.auth.service import create_dev_session
from benma_api.config import get_settings
from benma_api.db.models import PronunciationTarget
from benma_api.db.session import get_session_factory
from benma_api.pronunciation.targets import parse_mandarin_target

DEV_PHONE = "+12025550123"
TARGETS = ("生活", "北京", "水饺")


def main() -> None:
    settings = get_settings()
    if settings.environment == "production" or not settings.dev_auth_enabled:
        raise SystemExit("seeding requires development mode with BENMA_DEV_AUTH_ENABLED=true")

    with get_session_factory()() as db:
        account, auth_session, token = create_dev_session(db, settings, DEV_PHONE)
        existing = set(
            db.scalars(
                select(PronunciationTarget.text).where(
                    PronunciationTarget.account_id == account.id,
                    PronunciationTarget.text.in_(TARGETS),
                )
            )
        )
        for text in TARGETS:
            if text in existing:
                continue
            parsed = parse_mandarin_target(text)
            db.add(
                PronunciationTarget(
                    account_id=account.id,
                    text=text,
                    display_pinyin=parsed.display_pinyin,
                    pinyin_syllables=parsed.pinyin_syllables,
                    lexical_tones=parsed.lexical_tones,
                    target_source="generated",
                    pinyin_source=parsed.provenance,
                    pinyin_alternatives=parsed.alternatives,
                )
            )
        db.commit()

    print(f"development account: {account.id} ({DEV_PHONE})")
    print(f"session expires: {auth_session.expires_at.isoformat()}")
    print(f"bearer token (shown once): {token}")
    print("no perception or assessment evidence was seeded")


if __name__ == "__main__":
    main()
