import hashlib
import json
import shutil
import uuid
from pathlib import Path

from benma_api.config import Settings
from benma_api.db.models import AcousticRun, AudioAsset, PronunciationAttempt, Utterance
from benma_api.db.session import get_session_factory
from benma_api.pronunciation.diagnostic import _NoAudioStore, diagnostic
from benma_api.pronunciation.laboratory import PronunciationLaboratoryService
from sqlalchemy import select, text

settings = Settings()
assert settings.environment != "production"
out = Path("/home/jacob/benma/docs/calibration/2026-09-25-f0-tracking")
snapshot = Path("/tmp/benma-f0-corpus")
snapshot.mkdir(exist_ok=True)
rows = []
fresh = []
inventory = []
with get_session_factory()() as db:
    db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
    for u in db.scalars(select(Utterance).order_by(Utterance.created_at)):
        diag = diagnostic(db, u.id)
        aid = diag.get("acoustic_run_id")
        if not aid:
            continue
        acoustic = db.get(AcousticRun, uuid.UUID(aid))
        if not acoustic.normalized_result:
            continue
        asset = db.get(AudioAsset, u.canonical_audio_asset_id)
        path = snapshot / (str(u.id) + ".wav")
        shutil.copyfile(settings.audio_storage_dir / asset.storage_key, path)
        row = {
            "id": str(u.id),
            "created_at": u.created_at.isoformat(),
            "acoustic": acoustic.normalized_result,
            "spans": diag["syllables"],
            "diagnostic": diag,
            "audio_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        attempt = db.scalar(
            select(PronunciationAttempt)
            .where(PronunciationAttempt.utterance_id == u.id)
            .order_by(PronunciationAttempt.created_at.desc())
        )
        row["attempt_id"] = str(attempt.id) if attempt else None
        if attempt and attempt.created_at.isoformat() >= "2026-09-25T20:00:00":
            result = (
                PronunciationLaboratoryService(db, _NoAudioStore(), settings)
                .result(account_id=attempt.account_id, attempt_id=attempt.id)
                .model_dump(mode="json")
            )
            fresh.append(
                {
                    "attempt_id": str(attempt.id),
                    "utterance_id": str(u.id),
                    "target_id": str(attempt.target_id),
                    "created_at": attempt.created_at.isoformat(),
                    "target": result["target"]["text"],
                    "diagnostic": diag,
                    "result": result,
                }
            )
        rows.append(row)
        inventory.append({k: v for k, v in row.items() if k not in {"acoustic", "diagnostic"}})
    db.rollback()
(snapshot / "corpus.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
(out / "fresh-diagnostics.json").write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n")
(out / "corpus-inventory.json").write_text(
    json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
)
print("recordings", len(rows), "all spans", sum(len(r["spans"]) for r in rows))
for r in fresh:
    print(r["target"], r["created_at"], r["diagnostic"]["perceived_text"])
    print(
        [
            (
                s.get("start_seconds"),
                s.get("end_seconds"),
                s.get("locally_recomputed_contour", {}).get("classification"),
                s.get("locally_recomputed_contour", {}).get("reason"),
            )
            for s in r["diagnostic"]["syllables"]
        ]
    )
