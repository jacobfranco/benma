from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from benchmark.models import EvidenceOrigin, KnownTargetAssessmentResult
from benchmark.providers.known_target.captures import import_live_capture


def _capture(path: Path, audio_hash: str, *, target: str = "你好") -> Path:
    payload = {
        "capture_type": "LIVE_CAPTURED_SANITIZED",
        "provider": "tencent_soe_n",
        "product": "soe-n_mandarin_sentence_tone_detection",
        "provider_version": "undocumented",
        "adapter_version": "1.0.0",
        "target": target,
        "audio_sha256": audio_hash,
        "sample_rate_hz": 16000,
        "request_configuration": {"eval_mode": 1, "tone_detection": True},
        "transport_timings_ms": {"total": 124},
        "raw_response_sha256": "a" * 64,
        "normalized_evidence": {
            "overall_score": 80,
            "syllables": [
                {
                    "text": "你",
                    "reference_tone": 3,
                    "detected_tone": 2,
                    "pronunciation_score": 78,
                    "timing": {"start_seconds": 0.1, "end_seconds": 0.4},
                    "phones": [
                        {"phone": "n", "pronunciation_score": 76, "error_classifications": []}
                    ],
                }
            ],
        },
        "raw_response": {"sanitized": True},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_import_live_capture_preserves_identity_and_provenance(
    tmp_path: Path, recorded_sample  # type: ignore[no-untyped-def]
) -> None:
    audio_hash = hashlib.sha256(recorded_sample.audio.asset_path.read_bytes()).hexdigest()
    sample = recorded_sample.model_copy(
        update={"audio": recorded_sample.audio.model_copy(update={"sha256": audio_hash})}
    )
    run = import_live_capture(
        _capture(tmp_path / "capture.json", audio_hash), sample, output_dir=tmp_path / "runs"
    )
    assert run.evidence_origin == EvidenceOrigin.LIVE_CAPTURED_SANITIZED
    assert run.audio_sha256 == audio_hash
    assert run.response_latency_seconds == pytest.approx(0.124)
    assert isinstance(run.normalized_result, KnownTargetAssessmentResult)
    assert run.normalized_result.syllables[0].detected_tone == "T2"
    assert (tmp_path / "runs" / f"{run.run_id}.json").exists()


def test_import_rejects_hash_target_and_fixture_label(
    tmp_path: Path, recorded_sample  # type: ignore[no-untyped-def]
) -> None:
    audio_hash = hashlib.sha256(recorded_sample.audio.asset_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="audio hash"):
        import_live_capture(
            _capture(tmp_path / "wrong-hash.json", "f" * 64),
            recorded_sample,
            output_dir=tmp_path / "runs",
        )
    with pytest.raises(ValueError, match="target"):
        import_live_capture(
            _capture(tmp_path / "wrong-target.json", audio_hash, target="北京"),
            recorded_sample,
            output_dir=tmp_path / "runs",
        )
    fixture = _capture(tmp_path / "fixture.json", audio_hash)
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload["capture_type"] = "DOCUMENTATION_CONTRACT_EXAMPLE"
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="only LIVE_CAPTURED_SANITIZED"):
        import_live_capture(fixture, recorded_sample, output_dir=tmp_path / "runs")
