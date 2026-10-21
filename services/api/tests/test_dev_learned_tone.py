from __future__ import annotations

import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest
from conftest import wav_bytes
from test_perceived_speech import analyze, perception_for

from benma_api.config import Settings
from benma_api.pronunciation import learned, learned_runtime
from benma_api.pronunciation.alignment import AlignmentResponse, MontrealForcedAligner
from benma_api.pronunciation.learned import comparison, refine_span, supported_explanation
from benma_api.pronunciation.learned_contracts import LearnedRealization
from benma_api.pronunciation.perceived import perceived_syllables
from benma_api.schemas import DisplayContour, SentencePitchEvidence

ROOT = Path(__file__).resolve().parents[3]


def dev_settings(**changes):
    return Settings(
        _env_file=None,
        environment="test",
        enable_dev_learned_tone=True,
        alignment_provider="azure",
        azure_speech_key="fixture",
        azure_speech_region="fixture",
        **changes,
    )


def test_gate_defaults_and_production_rejection():
    assert not Settings(_env_file=None, environment="production").enable_dev_learned_tone
    with pytest.raises(ValueError, match="development-only"):
        Settings(_env_file=None, environment="production", enable_dev_learned_tone=True)
    for provider in ("mfa", "disabled", "replay"):
        with pytest.raises(ValueError, match="requires Azure"):
            Settings(_env_file=None, enable_dev_learned_tone=True, alignment_provider=provider)


def raw():
    return {
        "energy_gate": {"threshold_rms": 0.1},
        "f0": [{"timestamp_seconds": i / 100, "energy_rms": 0.2} for i in range(31)],
    }


def test_frozen_envelope_guard_and_missing_metadata():
    retained = [0.04, 0.05, 0.06, 0.07, 0.08, 0.12, 0.13, 0.14]
    result = refine_span([0.042, 0.14], retained, raw(), 0.3)
    assert result.pooling_span == [0.045000000000000005, 0.135]
    assert result.reason is None  # Pitch dropout alone is not an interruption.
    evidence = raw()
    evidence["f0"][10]["energy_rms"] = 0.01
    blocked = refine_span([0.042, 0.14], retained, evidence, 0.3)
    assert blocked.reason == "ambiguous_interrupted_voiced_envelope"
    assert blocked.continuity["passed"] is False
    assert (
        refine_span([0.04, 0.14], retained, {}, 0.3).reason == "missing_acoustic_validity_metadata"
    )
    assert refine_span(None, retained, evidence, 0.3).reason == "invalid_or_missing_azure_timing"
    assert (
        refine_span([0.04, 0.14], [], evidence, 0.3).reason
        == "no_voiced_support_in_tone_bearing_span"
    )
    assert refine_span([0.04, 0.07], retained, raw(), 0.3).reason == "too_little_material"


def test_refinement_matches_frozen_saved_spans_without_inference():
    folder = ROOT / "research/perceptual-tone-model/data/generated"
    saved = json.loads((folder / "fast-timing-ownership-v1/final-results.json").read_text())
    for row in saved["rows"]:
        data = json.loads(
            (folder / "azure-timing-replay-v1" / row["take_id"] / "acoustics.json").read_text()
        )
        retained = [
            p["timestamp_seconds"] for seg in data["graph"]["filtered"]["segments"] for p in seg
        ]
        final = row["representations"]["final"]
        result = refine_span(row["azure_whole"], retained, data["raw"], 100)
        if result.pooling_span:
            assert result.pooling_span == final["contract"]["pooling"]
        assert bool(result.continuity.get("interruptions")) == bool(final["interruptions"])


def contract(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(wav_bytes(0.3))
    return {
        "audio_reference": str(audio),
        "audio_sha256": hashlib.sha256(audio.read_bytes()).hexdigest(),
        "read_unit": [0.03, 0.2],
        "pooling": [0.04, 0.18],
        "context": [0, 0.3],
    }


@pytest.mark.parametrize(
    "field", ["expected_tone", "lexical_tone", "hanzi", "pinyin", "grade", "speaker"]
)
def test_inference_rejects_target_leakage(tmp_path, field):
    with pytest.raises(ValueError, match="audio_contract_fields"):
        learned_runtime.validate_contract({**contract(tmp_path), field: "forbidden"})


def test_resident_reuse_serializes_concurrent_requests(tmp_path, monkeypatch):
    class Runtime:
        calls = 0
        load_count = 1
        lock_sha256 = "fixture"

        def infer(self, value):
            self.calls += 1
            return {"status": "ok"}

    factory = Mock(side_effect=Runtime)
    monkeypatch.setattr(learned_runtime, "_runtime", None)
    monkeypatch.setattr(learned_runtime, "FrozenRuntime", factory)
    value = contract(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: learned_runtime.infer_batch([value]), range(2)))
    assert factory.call_count == 1
    assert sum(info["cold_start"] for _, info in results) == 1
    assert sorted(info["inference_calls"] for _, info in results) == [1, 2]


def test_model_failure_abstains_without_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(learned_runtime, "_runtime", None)
    monkeypatch.setattr(learned_runtime, "FrozenRuntime", Mock(side_effect=OSError))
    outputs, info = learned_runtime.infer_batch([contract(tmp_path)])
    assert outputs[0]["status"] == "abstained"
    assert outputs[0]["prediction"] is None
    assert info["error"] == "learned_runtime_unavailable:OSError"


def test_grading_neutral_unresolved_abstention_and_no_probability_threshold():
    for confidence in (0.26, 0.99):
        result = LearnedRealization(status="ok", prediction="T4", confidence=confidence)
        assert comparison(3, result).state == "experimental_mismatch"
        assert comparison(4, result).state == "experimental_match"
        assert comparison(None, result).state == "unresolved"
        assert comparison(0, result).state == "neutral"
        assert not comparison(3, result).correction
    assert comparison(3, LearnedRealization(reason="timing")).state == "insufficient"
    syllables = perceived_syllables("我想买这个", {})
    assert [s.expected_surface_tone for s in syllables] == [None, None, None, 4, 0]


def test_explanation_requires_eligible_measured_movement():
    s = perceived_syllables("买", {})[0]
    r = LearnedRealization(status="ok", prediction="T4")
    s.observed_contour.classification = "4-like"
    s.observed_contour.confidence = "moderate"
    s.observed_contour.features = {"change_st": -4}
    assert supported_explanation(s, r) is None
    s.pitch_eligibility = s.pitch_eligibility.model_copy(update={"state": "sufficient"})
    assert supported_explanation(s, r) == "Measured pitch fell by 4.00 semitones."
    s.observed_contour.features = {}
    assert supported_explanation(s, r) is None


@pytest.mark.parametrize(
    "transcript,target_text",
    [
        ("我", None),
        ("我", "我"),
        ("我", "买"),
        ("我想买这个", None),
        ("我想买这个", "我想买这个"),
        ("我想买这个", "我，想买这个"),  # noqa: RUF001
        ("我，想买这个", None),  # noqa: RUF001
    ],
)
def test_normal_api_azure_reuse_and_no_mfa(
    client,
    settings,
    auth_header,
    uploaded_utterance,
    session_factory,
    monkeypatch,
    target_text,
    transcript,
):
    settings.enable_dev_learned_tone = True
    settings.alignment_provider = "azure"
    settings.acoustic_provider = "praat"
    settings.azure_speech_key = dev_settings().azure_speech_key
    settings.azure_speech_region = "fixture"
    provider = Mock(
        algorithm_name="azure_speech_alignment_only", algorithm_version="fixture", configuration={}
    )
    provider.align.return_value = AlignmentResponse(
        units=[
            {
                "label": "我",
                "syllable_index": 0,
                "start_seconds": 0.02,
                "end_seconds": 0.14,
                "source": "azure_provider_grapheme",
            }
        ],
        raw_result={},
        evidence_status="live_provider",
    )
    monkeypatch.setattr("benma_api.pronunciation.perceived.build_aligner", lambda _: provider)
    mfa = Mock(side_effect=AssertionError("MFA must not run"))
    monkeypatch.setattr(MontrealForcedAligner, "align", mfa)
    infer = Mock(return_value=([], {}))
    monkeypatch.setattr(learned, "infer_batch", infer)
    # This short fixture may abstain before inference; return one result per usable span.
    infer.side_effect = lambda contracts: (
        [{"status": "abstained", "reason": "fixture"} for _ in contracts],
        {},
    )
    p = perception_for(session_factory, uploaded_utterance, transcript)
    body = {}
    if target_text:
        target = client.post(
            "/v1/pronunciation-targets", headers=auth_header, json={"text": target_text}
        )
        assert target.status_code == 201
        body = {"dev_learned_target_id": target.json()["id"]}

    def request():
        response = client.post(
            f"/v1/perceptions/{p.id}/speech-analysis", headers=auth_header, json=body
        )
        assert response.status_code == 200, response.text
        return response.json()

    first = request()
    second = request()
    assert first == second
    assert provider.align.call_count == 1
    assert mfa.call_count == 0
    assert "dev_learned_tone" in first["data"]
    assert "azure_timing" in first["data"]["dev_learned_tone"]["timings_ms"]
    result = first["data"]["dev_learned_tone"]
    assert result["expectation_basis"] == ("intended_target" if target_text else "perceived_text")
    mapping = target_text is None or target_text == transcript
    assert result["target_mapping_resolved"] == mapping
    if not mapping:
        assert result["units"][0]["expected_surface_tone"] is None
        assert result["units"][0]["comparison"]["correction"] is False
        assert result["units"][0]["expectation_resolution"] == "unresolved"
    if len(transcript) > 1 and mapping:
        first = [3] if "，" in transcript else [2, 3]  # noqa: RUF001
        assert [u["acceptable_surface_tones"] for u in result["units"]] == [
            first,
            [2],
            [3],
            [4],
            [],
        ]
        assert result["units"][-1]["expected_neutral"] is True
        assert [u["contextual_rule"] for u in result["units"]] == [
            None if "，" in transcript else "third_tone_sandhi",  # noqa: RUF001
            "third_tone_sandhi", None, None, None,
        ]
        assert result["units"][1]["target_pinyin"] == "xiǎng"
        assert result["units"][1]["lexical_tone"] == 3
        # Missing acoustic support never becomes a numbered recognition.
        assert result["units"][-1]["realization"]["prediction"] is None


def test_runtime_does_not_require_mfa_or_research_releases(monkeypatch):
    from types import SimpleNamespace

    original = Path.read_bytes
    accessed = []

    def read(path):
        accessed.append(str(path))
        assert "mfa" not in str(path) and "/releases/" not in str(path)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    lock = json.loads(original(learned_runtime.RESEARCH / "configs/dev-learned-lock.json"))
    encoder = Mock()
    encoder.base.weights = lock["encoder_weights"]
    modules = {
        "perceptual_tone.aishell3_embeddings": SimpleNamespace(Encoder=Mock(return_value=encoder)),
        "perceptual_tone.learner_transfer": SimpleNamespace(
            probabilities=Mock(), load_models=Mock()
        ),
    }
    monkeypatch.setattr(learned_runtime.importlib, "import_module", modules.__getitem__)
    runtime = learned_runtime.FrozenRuntime()
    assert runtime.load_count == 1
    encoder.base._load.assert_called_once()
    assert len(accessed) == len(learned_runtime.RUNTIME_FILES) + 1


def test_disabled_response_compatibility(
    client, settings, auth_header, uploaded_utterance, session_factory, monkeypatch
):
    monkeypatch.setattr(learned, "infer_batch", Mock(side_effect=AssertionError("disabled")))
    p = perception_for(session_factory, uploaded_utterance, "我")
    result = analyze(client, auth_header, p)
    assert "dev_learned_tone" not in result["data"]
    rejected = client.post(
        f"/v1/perceptions/{p.id}/speech-analysis",
        headers=auth_header,
        json={"dev_learned_target_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert rejected.status_code != 200


def test_numbered_expectations_do_not_change_inference_and_neutral_stays_out(tmp_path, monkeypatch):
    display = DisplayContour(
        segments=[[{"timestamp_seconds": i / 100, "normalized_semitones": 0} for i in range(4, 20)]]
    )
    graph = SentencePitchEvidence(mine=display, filtered=display, raw=[])
    s = perceived_syllables("买", {})[0]
    s.start_seconds, s.end_seconds, s.timing_source = 0.03, 0.22, "azure_provider_grapheme"
    calls = []

    def infer(contracts):
        calls.append(copy.deepcopy(contracts))
        return [
            {
                "status": "ok",
                "prediction": "T4",
                "confidence": 0.4,
                "probabilities": {"T1": 0.1, "T2": 0.2, "T3": 0.3, "T4": 0.4},
            }
            for _ in contracts
        ], {}

    monkeypatch.setattr(learned, "infer_batch", infer)
    c = contract(tmp_path)
    for tone in (1, 2, 3, 4, None, 0):
        expected = s.model_copy(update={"expected_surface_tone": tone})
        result = learned.analyze_learned(
            audio=Path(c["audio_reference"]),
            sha256=c["audio_sha256"],
            duration=0.3,
            syllables=[s],
            graph=graph,
            raw=raw(),
            recorded=True,
            expected=[expected],
            target_text="买",
            intended=True,
        )
        if tone == 0:
            assert calls[-1] == []
            assert result.units[0].comparison.state == "neutral"
            assert result.units[0].realization.prediction is None
        else:
            assert calls[-1] == calls[0]
            assert result.units[0].heard_pinyin == "mài"
            output = result.units[0].realization.model_dump()
            assert set(output["probabilities"]) == {"T1", "T2", "T3", "T4"}
            assert output["confidence_is_calibrated_correctness"] is False
            assert output["model_sha256"] and output["pooling_span"]
            assert str(tmp_path) not in json.dumps(output)
