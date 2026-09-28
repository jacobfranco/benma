from __future__ import annotations

import io
import math
import struct
import uuid
import wave
from pathlib import Path

from conftest import ApiClient

from benma_api.config import Settings
from benma_api.db.models import AcousticRun, AssessmentRun, PronunciationTarget
from benma_api.pronunciation.acoustics import AutocorrelationAcousticAnalyzer
from benma_api.pronunciation.alignment import validate_alignment
from benma_api.pronunciation.interpretation import diff_observations, interpret_evidence
from benma_api.pronunciation.targets import (
    parse_corrected_pinyin,
    parse_mandarin_target,
    surface_tone_expectation,
)


def test_target_parser_preserves_lexical_and_surface_tones() -> None:
    nihao = parse_mandarin_target("你好")
    assert nihao.lexical_tones == [3, 3]
    assert nihao.surface_tone_expectation["expected_surface_tones"] == [2, 3]
    assert nihao.surface_tone_expectation["rules"][0]["type"] == "THIRD_TONE_SANDHI"
    assert surface_tone_expectation("不是", [4, 4])["expected_surface_tones"] == [2, 4]
    assert surface_tone_expectation("一个", [1, 4])["expected_surface_tones"] == [2, 4]
    assert surface_tone_expectation("一天", [1, 1])["expected_surface_tones"] == [4, 1]


def test_neutral_tone_and_ambiguous_long_third_tone_sequence() -> None:
    neutral = parse_corrected_pinyin("妈妈", "ma1 ma5")
    assert neutral.lexical_tones == [1, 0]
    assert neutral.surface_tone_expectation["rules"][0]["type"] == "NEUTRAL_TONE_TARGET"
    ambiguous = surface_tone_expectation("我很好", [3, 3, 3])
    assert ambiguous["status"] == "context_dependent"
    assert ambiguous["expected_surface_tones"] is None


def test_user_pinyin_correction_is_a_new_target_revision(
    client: ApiClient, auth_header: dict[str, str]
) -> None:
    original = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "行"}
    ).json()
    corrected_response = client.post(
        f"/v1/pronunciation-targets/{original['id']}/pinyin-corrections",
        headers=auth_header,
        json={"pinyin": "hang2"},
    )
    assert corrected_response.status_code == 201
    corrected = corrected_response.json()
    assert corrected["id"] != original["id"]
    assert corrected["parent_target_id"] == original["id"]
    assert corrected["pinyin_source"] == "user-corrected"
    assert corrected["display_pinyin"] == "háng"
    unchanged = client.get(
        f"/v1/pronunciation-targets/{original['id']}", headers=auth_header
    ).json()
    assert unchanged["pinyin_syllables"] == original["pinyin_syllables"]


def _chirp(path: Path, *, start_hz: float, end_hz: float, seconds: float = 0.5) -> None:
    rate = 16000
    count = round(rate * seconds)
    phase = 0.0
    samples: list[int] = []
    for index in range(count):
        hz = start_hz + (end_hz - start_hz) * index / max(1, count - 1)
        phase += 2 * math.pi * hz / rate
        samples.append(round(math.sin(phase) * 9000))
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def test_acoustics_preserve_raw_confidence_and_relative_pitch(tmp_path: Path) -> None:
    rising = tmp_path / "rising.wav"
    falling = tmp_path / "falling.wav"
    _chirp(rising, start_hz=150, end_hz=260)
    _chirp(falling, start_hz=280, end_hz=140)
    analyzer = AutocorrelationAcousticAnalyzer()
    up = analyzer.analyze(rising)
    down = analyzer.analyze(falling)
    assert up["contour_features"]["change_semitones"] > 0
    assert down["contour_features"]["change_semitones"] < 0
    assert up["normalization"]["scope"] == "utterance_local"
    assert all("voicing_probability" in point for point in up["f0"])
    assert len(up["mobile_f0"]) <= 240


def test_silence_is_invalid_and_pitch_is_not_interpolated(tmp_path: Path) -> None:
    path = tmp_path / "silence.wav"
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 8000)
    path.write_bytes(output.getvalue())
    result = AutocorrelationAcousticAnalyzer().analyze(path)
    assert result["recording_quality"]["status"] == "invalid_for_interpretation"
    assert {"too_quiet", "low_voiced_fraction"}.issubset(result["recording_quality"]["issues"])
    assert all(point["f0_hz"] is None for point in result["f0"])


def test_alignment_sanity_checks_suppress_bad_boundaries() -> None:
    valid = [
        {"label": "sheng1", "start_seconds": 0.0, "end_seconds": 0.4},
        {"label": "huo2", "start_seconds": 0.4, "end_seconds": 0.8},
    ]
    assert validate_alignment(valid, target_count=2, duration_seconds=0.8)[
        "usable_for_syllable_visualization"
    ]
    invalid = [
        {"label": "sheng1", "start_seconds": 0.0, "end_seconds": 0.7},
        {"label": "huo2", "start_seconds": 0.5, "end_seconds": 1.2},
    ]
    quality = validate_alignment(invalid, target_count=3, duration_seconds=1.0)
    assert quality["quality"] == "invalid"
    assert {"target_unit_count_mismatch", "boundary_overlap", "alignment_beyond_audio"}.issubset(
        quality["issues"]
    )


def _interpret(
    provider_tone: int | None,
    pitch: list[float],
    *,
    expected_tone: int = 2,
    synthetic: bool = False,
) -> dict[str, object]:
    target = PronunciationTarget(
        text="麻",
        display_pinyin="má" if expected_tone == 2 else "mǎ",
        pinyin_syllables=[f"ma{expected_tone}"],
        lexical_tones=[expected_tone],
        target_source="manual",
        pinyin_source="fixture",
        pinyin_alternatives=[["ma2"]],
        syllable_units=[{"characters": "麻"}],
        surface_tone_expectation={
            "expected_surface_tones": [expected_tone],
            "rules": [],
        },
    )
    assessment = AssessmentRun(
        provider="fixture",
        product="fixture",
        adapter_version="1",
        target_snapshot={},
        normalized_result={
            "syllables": ([{"detected_tone": provider_tone}] if provider_tone else []),
            "evidence_status": "synthetic_replay" if synthetic else "live_provider",
        },
        status="succeeded",
    )
    acoustic = AcousticRun(
        algorithm="fixture",
        algorithm_version="1",
        parameters={},
        normalized_result={
            "recording_quality": {"status": "usable", "issues": []},
            "f0": [
                {"timestamp_seconds": index * 0.1, "normalized_semitones": value}
                for index, value in enumerate(pitch)
            ],
        },
        status="succeeded",
    )
    observations, _ = interpret_evidence(
        target=target,
        assessment=assessment,
        acoustic=acoustic,
        alignment=None,
        settings=Settings(environment="test"),
    )
    return observations[0]


def test_fixture_tone_cannot_issue_a_provider_judgment():
    real = _interpret(4, [-2.0, 2.0])
    synthetic = _interpret(4, [-2.0, 2.0], synthetic=True)
    assert real["kind"] == "conflict"
    assert synthetic["kind"] == "acoustic_observation"
    assert synthetic["observed_provider_tone"] is None
    assert synthetic["f0_direction"] == real["f0_direction"] == "rising"


def test_interpreter_distinguishes_agreement_conflict_and_acoustic_only() -> None:
    agreement = _interpret(4, [2.0, -2.0])
    assert agreement["kind"] == "tone_evidence_mismatch"
    assert agreement["agreement"] == "agreement"
    conflict = _interpret(4, [-2.0, 2.0])
    assert conflict["kind"] == "conflict"
    acoustic_only = _interpret(None, [-2.0, 2.0])
    assert acoustic_only["kind"] == "acoustic_observation"
    assert acoustic_only["capability_state"] == "raw_evidence"
    third_tone = _interpret(4, [-2.0, 2.0], expected_tone=3)
    assert third_tone["agreement"] == "inconclusive"


def test_interpreter_diff_is_stable_and_non_mutating() -> None:
    baseline = [{"category": "TONE", "syllable_index": 0, "kind": "tone_unavailable"}]
    same = diff_observations(baseline, list(baseline))
    assert same == {"changed": False, "added": [], "removed": [], "modified": []}
    changed = diff_observations(
        baseline,
        [{"category": "TONE", "syllable_index": 0, "kind": "acoustic_observation"}],
    )
    assert changed["changed"] is True
    assert changed["added"] and changed["removed"]
    assert baseline[0]["kind"] == "tone_unavailable"


def test_reference_is_cached_and_owned(client: ApiClient, auth_header: dict[str, str]) -> None:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    ).json()
    path = f"/v1/pronunciation-targets/{target['id']}/reference-speech"
    first = client.post(path, headers=auth_header, json={}).json()
    second = client.post(path, headers=auth_header, json={}).json()
    assert first["id"] == second["id"]
    assert first["status"] == "succeeded"
    assert first["generation_config"]["evidence_status"] == "synthetic_replay"
    assert first["acoustic_result"]["capability_state"] == "raw_evidence"
    audio = client.get(first["audio_url"], headers=auth_header)
    assert audio.status_code == 200 and audio.content.startswith(b"RIFF")
    other = client.post("/v1/dev/auth", json={"phone_number": "+12025550129"}).json()
    denied = client.get(first["audio_url"], headers={"Authorization": f"Bearer {other['token']}"})
    assert denied.status_code == 404
    forced = client.post(path, headers=auth_header, json={"force": True}).json()
    assert forced["id"] != first["id"]


def test_reference_provider_failure_is_persisted_and_retryable(
    client: ApiClient, auth_header: dict[str, str], settings: Settings
) -> None:
    settings.reference_speech_provider = "disabled"
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    ).json()
    response = client.post(
        f"/v1/pronunciation-targets/{target['id']}/reference-speech",
        headers=auth_header,
        json={},
    )
    assert response.status_code == 200
    failed = response.json()
    assert failed["status"] == "failed"
    assert failed["error_code"] == "analysis_unsupported"
    assert failed["audio_url"] is None


def test_analysis_orchestrates_separate_evidence_and_is_idempotent(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    ).json()
    client.post(
        f"/v1/pronunciation-targets/{target['id']}/reference-speech",
        headers=auth_header,
        json={},
    )
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    path = f"/v1/pronunciation-attempts/{attempt['id']}/analyze"
    first_response = client.post(path, headers=auth_header, json={})
    assert first_response.status_code == 200, first_response.text
    first = first_response.json()
    second = client.post(path, headers=auth_header, json={}).json()
    assert first["assessment"]["id"] == second["assessment"]["id"]
    assert first["acoustic"]["id"] == second["acoustic"]["id"]
    assert first["alignment"]["id"] == second["alignment"]["id"]
    assert first["interpretation"]["id"] == second["interpretation"]["id"]
    assert first["interpretation"]["interpreter_configuration"] == {
        "enable_experimental_tone_interpretation": True,
        "enable_categorical_tone_judgment": False,
    }
    rerun = client.post(
        path,
        headers=auth_header,
        json={
            "rerun_provider": True,
            "rerun_acoustics": True,
            "rerun_alignment": True,
        },
    ).json()
    assert rerun["assessment"]["id"] != first["assessment"]["id"]
    assert rerun["acoustic"]["id"] != first["acoustic"]["id"]
    assert rerun["alignment"]["id"] != first["alignment"]["id"]
    assert rerun["interpretation"]["id"] != first["interpretation"]["id"]
    assert first["capability_policy"]["categorical_tone_judgment"] == "unavailable"
    assert first["capability_policy"]["wording_policy"]["raw_evidence"] == (
        "factual_provider_or_acoustic_observation_only"
    )
    assert first["overall_evidence"]["recording_quality"]["status"] == (
        "invalid_for_interpretation"
    )
    assert first["syllables"][0]["interpretation"] is None or (
        first["syllables"][0]["interpretation"]["kind"] == "invalid_audio"
    )
    history = client.get(f"/v1/pronunciation-targets/{target['id']}/attempts", headers=auth_header)
    assert history.status_code == 200 and len(history.json()) == 1


def test_cross_account_cannot_read_pronunciation_result(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "马"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    other = client.post("/v1/dev/auth", json={"phone_number": "+12025550128"}).json()
    denied = client.get(
        f"/v1/pronunciation-attempts/{attempt['id']}/result",
        headers={"Authorization": f"Bearer {other['token']}"},
    )
    assert denied.status_code == 404


def test_invalid_correction_and_unknown_reference_are_safe(
    client: ApiClient, auth_header: dict[str, str]
) -> None:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    ).json()
    invalid = client.post(
        f"/v1/pronunciation-targets/{target['id']}/pinyin-corrections",
        headers=auth_header,
        json={"pinyin": "sheng huo"},
    )
    assert invalid.status_code == 422
    missing = client.get(f"/v1/reference-speech/{uuid.uuid4()}/audio", headers=auth_header)
    assert missing.status_code == 404


def test_target_reuses_exact_provider_timing_for_shape_without_fabricating_surface_tone(
    client,
    auth_header,
    uploaded_utterance,
    monkeypatch,
):
    from test_readings_contours import raw_contour

    from benma_api.speech.contracts import AssessmentEvidence, AssessmentProviderResponse
    from benma_api.speech.providers.replay import ReplayPronunciationProvider

    # Simulated live adapter provenance for this timing-fallback test. A replay
    # adapter cannot authorize grading just by claiming live payload status.
    monkeypatch.setattr(ReplayPronunciationProvider, "provider_name", "test-live")
    raw = raw_contour([0] * 15)
    monkeypatch.setattr(
        AutocorrelationAcousticAnalyzer,
        "analyze",
        lambda *_: {
            "f0": raw,
            "mobile_f0": raw,
            "duration_seconds": 0.15,
            "recording_quality": {"status": "usable", "issues": []},
        },
    )
    monkeypatch.setattr(
        ReplayPronunciationProvider,
        "assess",
        lambda *_: AssessmentProviderResponse(
            evidence=AssessmentEvidence(
                pronunciation_score=79,
                evidence_status="live_provider",
                syllables=[{"text": "末", "timing": {"start_seconds": 0, "end_seconds": 0.15}}],
            ),
            raw_payload={"fixture": True},
        ),
    )
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "末"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    result = client.post(
        f"/v1/pronunciation-attempts/{attempt['id']}/analyze", headers=auth_header, json={}
    ).json()
    syllable = result["syllables"][0]
    assert syllable["timing"]["source"] == "assessment"
    assert syllable["observed_contour"]["classification"] == "1-like"
    assert syllable["lexical_tone"] == 4
    assert result["assessment"]["normalized_result"]["pronunciation_score"] == 79


def test_unmodeled_surface_tone_is_not_silently_lexical(client, auth_header, uploaded_utterance):
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "我很好"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    result = client.post(
        f"/v1/pronunciation-attempts/{attempt['id']}/analyze", headers=auth_header, json={}
    ).json()
    assert [s["lexical_tone"] for s in result["syllables"]] == [3, 3, 3]
    assert all(s["expected_surface_tone"] is None for s in result["syllables"])
    assert all(s["observed_contour"]["classification"] == "unclear" for s in result["syllables"])


def test_neutral_provider_shape_is_not_a_fixed_contour_mismatch() -> None:
    observation = _interpret(4, [2.0, -2.0], expected_tone=0)
    assert observation["kind"] == "neutral_context_observation"
    assert observation["observed_provider_tone"] == 4
    assert observation["f0_direction"] == "falling"
    assert "context-dependent" in str(observation["message"])
    assert "Tone 0" not in str(observation["message"])


def test_assessment_provenance_fails_closed():
    from benma_api.pronunciation.interpretation import has_live_assessment

    for provider, status, evidence, accepted in [
        ("azure", "succeeded", "live_provider", True),
        ("replay", "succeeded", "live_provider", False),
        ("azure", "succeeded", "synthetic_replay", False),
        ("azure", "succeeded", None, False),
        ("azure", "failed", "live_provider", False),
    ]:
        row = AssessmentRun(
            provider=provider,
            status=status,
            normalized_result={"evidence_status": evidence, "pronunciation_score": 79},
        )
        assert has_live_assessment(row) is accepted
