"""Optional read-only local DB capture; run from services/api. No provider calls."""

import json
from pathlib import Path

from benma_api.config import Settings
from benma_api.db.models import AudioAsset, PerceivedSpeechAnalysis, Utterance
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session


def main():
    ids = [
        "40357072fc994a0ab052752ca119b2e6",
        "8d2522640da64860bd83c33b0b7b7e14",
        "d47274bcdb604380abbeac49930a5dad",
        "4b9dbd2bb17b434498fcbd16a7dd4b69",
        "8faf1a90f564479cac56a41aeab22177",
        "a5acd04c21b742fbbfd53741a2aed1dd",
    ]
    rows = []
    with Session(create_engine(Settings().database_url, connect_args={"connect_timeout": 3})) as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        for id_ in ids:
            asset = db.scalar(
                select(AudioAsset).where(AudioAsset.storage_key.endswith(id_ + ".wav"))
            )
            if asset is None:
                raise ValueError("Missing asset " + id_)
            utterance = db.scalar(
                select(Utterance).where(Utterance.canonical_audio_asset_id == asset.id)
            )
            if utterance is None:
                raise ValueError("Missing saved utterance " + id_)
            analyses = list(
                db.scalars(
                    select(PerceivedSpeechAnalysis)
                    .where(PerceivedSpeechAnalysis.utterance_id == utterance.id)
                    .order_by(PerceivedSpeechAnalysis.created_at)
                )
            )
            if not analyses:
                raise ValueError("Missing saved analysis " + id_)
            row = dict(
                id=id_,
                sha256=asset.sha256,
                analyses=[
                    dict(
                        id=str(a.id),
                        created_at=str(a.created_at),
                        analyzer_version=a.analyzer_version,
                        status=a.status,
                        result=a.result,
                    )
                    for a in analyses
                ],
            )
            rows.append(row)
            print(
                id_[:8],
                len(analyses),
                [(str(a.created_at), a.status, list(a.result)) for a in analyses],
            )
    output = Path("var/relative-pitch-gesture/saved-analyses.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
