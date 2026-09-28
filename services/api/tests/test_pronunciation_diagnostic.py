from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import event

from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.diagnostic import diagnostic


def test_fresh_persisted_pitch_regression():
    rows = json.loads((Path(__file__).parent / "fixtures/fresh_calibration_pitch.json").read_text())
    for row in rows:
        raw = row["raw"]
        result = classify_contour(display_contour(raw), row["start"], row["end"], raw=raw)
        assert result.classification == row["expected"], row["utterance_id"]
        assert result.features["alignment_start_seconds"] == row["start"]
        if result.classification in {"1-like", "4-like"}:
            assert result.confidence == "low"


def test_diagnostic_identifies_actual_attempt_and_never_writes(
    client,
    auth_header,
    uploaded_utterance,
    session_factory,
):
    uid = uuid.UUID(uploaded_utterance["id"])
    with session_factory() as db:
        free = diagnostic(db, uid)
        assert free["practice_mode"] == "free"
        assert free["target_id"] is None
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "妈"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": str(uid), "target_id": target["id"]},
    ).json()
    # Deliberately no analysis/provider call: missing evidence must remain unavailable.
    with session_factory() as db:
        statements = []
        connection = db.connection()

        def capture(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(connection, "before_cursor_execute", capture)
        result = diagnostic(db, uid)
        assert all(s.lstrip().upper().startswith("SELECT") for s in statements)
        assert result["practice_mode"] == "known_target"
        assert result["target_id"] == target["id"]
        assert result["target"]["persisted_text"] == "妈"
        assert result["target"]["attempt_target_id"] == target["id"]
        assert result["target"]["pinyin_syllables"] == ["ma1"]
        assert result["canonical_audio"]["channel_count"] == 1
        assert result["pronunciation_attempt_id"] == attempt["id"]
        assert result["syllables"][0]["pinyin"] == "ma1"
        assert result["syllables"][0]["rejected_rule"] == "timing_unavailable"
        assert "storage" not in json.dumps(result)
        assert "audio_url" not in json.dumps(result)
