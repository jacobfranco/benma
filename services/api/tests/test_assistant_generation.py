from __future__ import annotations

import json
import uuid
from copy import deepcopy
from typing import Any

import pytest
from conftest import ApiClient, wav_bytes
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.api.routes import (
    get_assistant_response_generator,
    get_assistant_speech_provider,
    get_contextual_interpreter,
)
from benma_api.assistant_generation.contracts import (
    AssistantGenerationProviderResponse,
    AssistantResponseGenerationEvidence,
    AssistantResponseGenerationInput,
)
from benma_api.contextual_interpretation.contracts import (
    ContextualInterpretationEvidence,
    ContextualInterpretationInput,
)
from benma_api.db.models import (
    AssessmentRun,
    AssistantGenerationRun,
    AssistantSpeechRun,
    AudioAsset,
    ConversationTurn,
    PerceptionRun,
    PronunciationAttempt,
    PronunciationTarget,
    UserCorrection,
    Utterance,
)
from benma_api.errors import ProviderTimeoutError
from benma_api.speech.synthesis import SpeechSynthesisRequest, SpeechSynthesisResponse


class SequencedInterpreter:
    interpreter_name = "assistant-generation-test-interpreter"
    interpreter_version = "1"

    def __init__(self, decisions: list[str]) -> None:
        self.interpreter_configuration = {"policy": "test"}
        self.decisions = iter(decisions)
        self.requests: list[ContextualInterpretationInput] = []

    def interpret(
        self, request: ContextualInterpretationInput
    ) -> ContextualInterpretationEvidence:
        self.requests.append(deepcopy(request))
        decision = next(self.decisions)
        return ContextualInterpretationEvidence(
            decision=decision,  # type: ignore[arg-type]
            inferred_text=(
                "我想买水果。"
                if decision == "infer"
                else request.perceived_transcript
                if decision == "preserve"
                else None
            ),
            uncertainty={
                "level": "high" if decision == "clarify" else "low",
                "rationale": "fixture",
                "alternatives": ["早梅", "糟糕"] if decision == "clarify" else [],
            },
            clarification_needed=decision == "clarify",
        )


class SequencedGenerator:
    provider_name = "assistant-generation-test-provider"
    product_name = "fixture-generation"
    adapter_version = "1"
    generator_version = "fixture-policy-v1"

    def __init__(
        self,
        outputs: list[str],
        *,
        error: Exception | None = None,
    ) -> None:
        self.generator_configuration = {
            "model": "fixture-mandarin-model",
            "reasoning_effort": "low",
        }
        self.outputs = iter(outputs)
        self.error = error
        self.requests: list[AssistantResponseGenerationInput] = []

    def generate(
        self, request: AssistantResponseGenerationInput
    ) -> AssistantGenerationProviderResponse:
        self.requests.append(deepcopy(request))
        if self.error is not None:
            raise self.error
        text = next(self.outputs)
        return AssistantGenerationProviderResponse(
            evidence=AssistantResponseGenerationEvidence(
                generation_type=request.generation_type,
                generated_text=text,
                clarification_alternatives_used=tuple(
                    candidate
                    for candidate in request.clarification_alternatives
                    if candidate in text
                ),
            ),
            raw_payload={"provider_output": text, "request_id": "fixture-provider-id"},
            provider_version="fixture-provider-v2",
        )


class RecordingSpeechProvider:
    provider_name = "assistant-speech-test-provider"
    product_name = "fixture-synthesis"
    adapter_version = "fixture-adapter-v1"

    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.requests: list[SpeechSynthesisRequest] = []

    def synthesize(self, request: SpeechSynthesisRequest) -> SpeechSynthesisResponse:
        self.requests.append(deepcopy(request))
        if self.error is not None:
            raise self.error
        return SpeechSynthesisResponse(
            audio=wav_bytes(),
            mime_type="audio/wav",
            provider_version="fixture-speech-model-v2",
            evidence_status="fixture_replay",
        )


def use_speech_provider(
    client: ApiClient, provider: RecordingSpeechProvider
) -> RecordingSpeechProvider:
    async def override() -> RecordingSpeechProvider:
        return provider

    client.app.dependency_overrides[get_assistant_speech_provider] = override
    return provider


def configure_free_talk(
    client: ApiClient,
    *,
    decisions: list[str],
    outputs: list[str],
    error: Exception | None = None,
) -> tuple[SequencedInterpreter, SequencedGenerator]:
    interpreter = SequencedInterpreter(decisions)
    generator = SequencedGenerator(outputs, error=error)

    async def override_interpreter() -> SequencedInterpreter:
        return interpreter

    async def override_generator() -> SequencedGenerator:
        return generator

    client.app.dependency_overrides[get_contextual_interpreter] = override_interpreter
    client.app.dependency_overrides[get_assistant_response_generator] = override_generator
    return interpreter, generator


def create_conversation(client: ApiClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.post("/v1/conversations", headers=headers, json={})
    assert response.status_code == 201
    return response.json()


def append_perception(
    session_factory: sessionmaker[Session],
    *,
    utterance_id: object,
    transcript: str,
    raw_payload: object | None = None,
) -> uuid.UUID:
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(str(utterance_id)))
        assert utterance is not None
        run = PerceptionRun(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            provider="assistant-generation-fixture",
            product="transcription",
            adapter_version="1",
            transcript=transcript,
            normalized_result={"transcript": transcript},
            raw_payload_json=raw_payload,
            status="succeeded",
        )
        db.add(run)
        db.commit()
        return run.id


def add_user_turn(
    client: ApiClient,
    headers: dict[str, str],
    *,
    conversation_id: object,
    utterance_id: object,
    perception_run_id: object,
) -> dict[str, Any]:
    response = client.post(
        f"/v1/conversations/{conversation_id}/user-turns",
        headers=headers,
        json={
            "utterance_id": str(utterance_id),
            "perception_run_id": str(perception_run_id),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize(
    ("decision", "transcript", "assistant_text", "generation_type", "resolved"),
    [
        (
            "preserve",
            "我们可以睡觉一起。",
            "好啊，我们什么时候休息？",
            "reply",
            "我们可以睡觉一起。",
        ),
        ("infer", "我想卖水果。", "好呀，你想买什么水果？", "reply", "我想买水果。"),
        ("clarify", "糟妹。", "你是想说“早梅”还是别的？", "clarification", None),
    ],
)
def test_free_talk_generates_reply_or_clarification_from_contextual_decision(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
    decision: str,
    transcript: str,
    assistant_text: str,
    generation_type: str,
    resolved: str | None,
) -> None:
    _, generator = configure_free_talk(
        client,
        decisions=[decision],
        outputs=[assistant_text],
    )
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript=transcript,
    )

    user_turn = add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=perception_id,
    )
    listed = client.get(
        f"/v1/conversations/{conversation['id']}/turns", headers=auth_header
    )
    assert listed.status_code == 200
    turns = listed.json()
    assert [turn["role"] for turn in turns] == ["user", "assistant"]
    assert turns[0]["id"] == user_turn["id"]
    assert turns[0]["resolved_text"] == resolved
    assert turns[1]["assistant_text"] == assistant_text
    assert turns[1]["resolved_text"] == assistant_text
    assert turns[1]["assistant_generation_run_id"] is not None

    request = generator.requests[0]
    assert request.generation_type == generation_type
    assert request.resolved_semantic_text == resolved
    if decision == "clarify":
        assert request.contextual_decision == "clarify"
        assert request.resolved_semantic_text is None

    generation_response = client.get(
        f"/v1/assistant-generations/{turns[1]['assistant_generation_run_id']}",
        headers=auth_header,
    )
    assert generation_response.status_code == 200
    generation = generation_response.json()
    assert generation["triggering_user_turn_id"] == user_turn["id"]
    assert generation["generation_type"] == generation_type
    assert generation["generated_text"] == assistant_text
    assert generation["model"] == "fixture-mandarin-model"
    assert generation["status"] == "succeeded"
    current = generation["input_snapshot"]["current_user_turn"]
    assert current["resolved_semantic_text"] == resolved

    with session_factory() as db:
        perception = db.get(PerceptionRun, perception_id)
        assert perception is not None and perception.transcript == transcript


def test_generated_assistant_is_next_context_but_not_its_own_input(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    first_output = "FIRST_GENERATED_ASSISTANT_OUTPUT"
    second_output = "SECOND_GENERATED_ASSISTANT_OUTPUT"
    interpreter, generator = configure_free_talk(
        client,
        decisions=["preserve", "preserve"],
        outputs=[first_output, second_output],
    )
    conversation = create_conversation(client, auth_header)
    first_perception = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="第一句。",
    )
    second_perception = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="第二句。",
    )

    add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=first_perception,
    )
    add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=second_perception,
    )

    assert interpreter.requests[1].context_snapshot["turns"] == [
        {"role": "user", "text": "第一句。"},
        {"role": "assistant", "text": first_output},
    ]
    first_input = json.dumps(generator.requests[0].snapshot(), ensure_ascii=False)
    second_input = json.dumps(generator.requests[1].snapshot(), ensure_ascii=False)
    assert first_output not in first_input
    assert second_output not in second_input
    assert first_output in second_input


def test_generation_input_excludes_raw_payload_pronunciation_and_correction_truth(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    _, generator = configure_free_talk(
        client,
        decisions=["clarify"],
        outputs=["你刚才说什么？"],
    )
    speech = use_speech_provider(client, RecordingSpeechProvider())
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="我想卖水果。",
        raw_payload={"marker": "RAW_PROVIDER_SECRET_MARKER"},
    )
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(str(uploaded_utterance["id"])))
        assert utterance is not None
        correction = UserCorrection(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            perception_run_id=perception_id,
            intended_text="HIDDEN_CORRECTION_TRUTH",
        )
        target = PronunciationTarget(
            account_id=utterance.account_id,
            text="HIDDEN_PRONUNCIATION_TARGET",
            display_pinyin="hidden",
            pinyin_syllables=["hidden"],
            lexical_tones=[None],
            target_source="manual",
            pinyin_source="fixture",
        )
        db.add_all([correction, target])
        db.flush()
        attempt = PronunciationAttempt(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            target_id=target.id,
        )
        db.add(attempt)
        db.flush()
        db.add(
            AssessmentRun(
                account_id=utterance.account_id,
                pronunciation_attempt_id=attempt.id,
                provider="fixture",
                product="fixture",
                adapter_version="1",
                target_snapshot={"marker": "HIDDEN_TARGET_SNAPSHOT"},
                normalized_result={"marker": "HIDDEN_PRONUNCIATION_EVIDENCE"},
                status="succeeded",
            )
        )
        db.commit()

    add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=perception_id,
    )

    serialized = json.dumps(generator.requests[0].snapshot(), ensure_ascii=False)
    assert "我想卖水果。" in serialized
    assert generator.requests[0].clarification_alternatives == ("早梅", "糟糕")
    assert "RAW_PROVIDER_SECRET_MARKER" not in serialized
    assert "HIDDEN_CORRECTION_TRUTH" not in serialized
    assert "HIDDEN_PRONUNCIATION" not in serialized
    assert "HIDDEN_TARGET_SNAPSHOT" not in serialized
    assert len(speech.requests) == 1
    speech_input = repr(speech.requests[0])
    assert speech.requests[0].text == "你刚才说什么？"
    assert "RAW_PROVIDER_SECRET_MARKER" not in speech_input
    assert "HIDDEN_CORRECTION_TRUTH" not in speech_input
    assert "HIDDEN_PRONUNCIATION" not in speech_input
    assert "HIDDEN_TARGET_SNAPSHOT" not in speech_input


def test_failed_generation_is_persisted_without_an_assistant_turn(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    configure_free_talk(
        client,
        decisions=["preserve"],
        outputs=[],
        error=ProviderTimeoutError("safe generation timeout", retryable=True),
    )
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="你好。",
    )

    response = client.post(
        f"/v1/conversations/{conversation['id']}/user-turns",
        headers=auth_header,
        json={
            "utterance_id": str(uploaded_utterance["id"]),
            "perception_run_id": str(perception_id),
        },
    )
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "provider_timeout"
    with session_factory() as db:
        turns = list(
            db.scalars(
                select(ConversationTurn).where(
                    ConversationTurn.conversation_id
                    == uuid.UUID(str(conversation["id"]))
                )
            )
        )
        run = db.scalar(
            select(AssistantGenerationRun).where(
                AssistantGenerationRun.conversation_id
                == uuid.UUID(str(conversation["id"]))
            )
        )
        assert len(turns) == 1 and turns[0].role == "user"
        assert run is not None
        assert run.status == "failed"
        assert run.generated_text is None
        assert run.error_code == "provider_timeout"


def test_generation_provenance_is_append_only_and_non_disclosing(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    configure_free_talk(
        client,
        decisions=["preserve"],
        outputs=["你好呀！"],
    )
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="你好。",
    )
    add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=perception_id,
    )
    with session_factory() as db:
        run = db.scalar(select(AssistantGenerationRun))
        assert run is not None
        run_id = run.id
        run.generated_text = "rewritten"
        with pytest.raises(ValueError, match="append-only"):
            db.commit()

    other_auth = client.post(
        "/v1/dev/auth", json={"phone_number": "+12025550187"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}
    hidden = client.get(
        f"/v1/assistant-generations/{run_id}", headers=other_headers
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "authorization_error"


@pytest.mark.parametrize(
    ("decision", "resolved", "generation_type"),
    [
        ("clarify", "fabricated meaning", "clarification"),
        ("clarify", None, "reply"),
        ("preserve", None, "reply"),
        ("preserve", "different meaning", "reply"),
        ("infer", "perceived", "reply"),
        ("infer", "inferred", "clarification"),
    ],
)
def test_generation_input_rejects_contradictory_semantics(
    decision: str,
    resolved: str | None,
    generation_type: str,
) -> None:
    with pytest.raises(ValueError):
        AssistantResponseGenerationInput(
            conversation_context_snapshot={"format": "test", "version": 1, "turns": []},
            perceived_transcript="perceived",
            contextual_decision=decision,  # type: ignore[arg-type]
            resolved_semantic_text=resolved,
            clarification_alternatives=(),
            generation_type=generation_type,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("decision", "transcript", "assistant_text"),
    [
        ("infer", "我想卖水果。", "好呀，你想买什么水果？"),
        ("clarify", "不清楚。", "你是想说什么？"),
        ("preserve", "我们明天聊。", "可以啊，早点休息吧。"),
    ],
)
def test_free_talk_persists_playable_speech_for_exact_generated_text(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
    decision: str,
    transcript: str,
    assistant_text: str,
) -> None:
    configure_free_talk(client, decisions=[decision], outputs=[assistant_text])
    provider = use_speech_provider(client, RecordingSpeechProvider())
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript=transcript,
    )

    response = add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=perception_id,
    )

    assistant = response["assistant_turn"]
    speech = assistant["assistant_speech"]
    assert assistant["assistant_text"] == assistant_text
    assert speech["status"] == "succeeded"
    assert speech["text_snapshot"] == assistant_text
    assert speech["assistant_generation_run_id"] == assistant[
        "assistant_generation_run_id"
    ]
    assert speech["assistant_turn_id"] == assistant["id"]
    assert speech["provider"] == provider.provider_name
    assert speech["product"] == provider.product_name
    assert speech["provider_version"] == "fixture-speech-model-v2"
    assert speech["voice"] == "zh-CN-Xiaochen:DragonHDLatestNeural"
    assert speech["locale"] == "zh-CN"
    assert speech["audio_asset"]["kind"] == "assistant_speech"
    assert provider.requests == [
        SpeechSynthesisRequest(
            text=assistant_text,
            locale="zh-CN",
            voice="zh-CN-Xiaochen:DragonHDLatestNeural",
            model_version="DragonHDLatestNeural",
            rate="0%",
            timeout_seconds=30.0,
        )
    ]

    audio = client.get(speech["audio_url"], headers=auth_header)
    assert audio.status_code == 200
    assert audio.headers["content-type"] == "audio/wav"
    assert audio.content.startswith(b"RIFF")
    with session_factory() as db:
        generation = db.get(
            AssistantGenerationRun,
            uuid.UUID(str(assistant["assistant_generation_run_id"])),
        )
        persisted_speech = db.get(AssistantSpeechRun, uuid.UUID(str(speech["id"])))
        assert generation is not None and generation.generated_text == assistant_text
        assert persisted_speech is not None
        assert persisted_speech.text_snapshot == generation.generated_text
        audio_asset = db.get(AudioAsset, persisted_speech.audio_asset_id)
        assert audio_asset is not None
        assert audio_asset.storage_key.startswith(
            f"{conversation['account_id']}/assistant/"
        )


def test_speech_failure_preserves_text_and_retry_appends_evidence(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    assistant_text = "文字必须保留下来。"
    configure_free_talk(
        client,
        decisions=["preserve"],
        outputs=[assistant_text],
    )
    failed_provider = use_speech_provider(
        client,
        RecordingSpeechProvider(
            error=ProviderTimeoutError("safe speech timeout", retryable=True)
        ),
    )
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="你好。",
    )

    initial = add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=perception_id,
    )
    assistant = initial["assistant_turn"]
    failed = assistant["assistant_speech"]
    assert assistant["assistant_text"] == assistant_text
    assert failed["status"] == "failed"
    assert failed["error_code"] == "provider_timeout"
    assert failed["text_snapshot"] == assistant_text
    assert failed["audio_asset"] is None
    assert failed["audio_url"] is None

    successful_provider = use_speech_provider(client, RecordingSpeechProvider())
    rejected_text = client.post(
        f"/v1/assistant-generations/{assistant['assistant_generation_run_id']}/speech",
        headers=auth_header,
        json={"text": "client rewrite attempt"},
    )
    assert rejected_text.status_code == 422
    assert successful_provider.requests == []
    retry = client.post(
        f"/v1/assistant-generations/{assistant['assistant_generation_run_id']}/speech",
        headers=auth_header,
        json={},
    )
    assert retry.status_code == 201, retry.text
    succeeded = retry.json()
    assert succeeded["id"] != failed["id"]
    assert succeeded["status"] == "succeeded"
    assert succeeded["text_snapshot"] == assistant_text
    assert successful_provider.requests[0].text == assistant_text
    assert failed_provider.requests[0].text == assistant_text

    listed = client.get(
        f"/v1/conversations/{conversation['id']}/turns", headers=auth_header
    ).json()
    assert listed[1]["assistant_text"] == assistant_text
    assert listed[1]["assistant_speech"]["id"] == succeeded["id"]
    assert listed[1]["assistant_speech"]["audio_url"] is not None
    with session_factory() as db:
        generation = db.get(
            AssistantGenerationRun,
            uuid.UUID(str(assistant["assistant_generation_run_id"])),
        )
        runs = list(
            db.scalars(
                select(AssistantSpeechRun)
                .where(
                    AssistantSpeechRun.assistant_generation_run_id
                    == uuid.UUID(str(assistant["assistant_generation_run_id"]))
                )
                .order_by(AssistantSpeechRun.created_at.asc())
            )
        )
        assert generation is not None and generation.generated_text == assistant_text
        assert [run.status for run in runs] == ["failed", "succeeded"]
        assert runs[0].id == uuid.UUID(str(failed["id"]))
        assert runs[0].error_code == "provider_timeout"


def test_failed_speech_does_not_change_text_history(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    first_text = "第一条文字回复。"
    second_text = "第二条文字回复。"
    interpreter, generator = configure_free_talk(
        client,
        decisions=["preserve", "preserve"],
        outputs=[first_text, second_text],
    )
    use_speech_provider(
        client,
        RecordingSpeechProvider(
            error=ProviderTimeoutError("speech unavailable", retryable=True)
        ),
    )
    conversation = create_conversation(client, auth_header)
    first_perception = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="第一句。",
    )
    second_perception = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="第二句。",
    )
    for perception_id in (first_perception, second_perception):
        add_user_turn(
            client,
            auth_header,
            conversation_id=conversation["id"],
            utterance_id=uploaded_utterance["id"],
            perception_run_id=perception_id,
        )

    assert interpreter.requests[1].context_snapshot["turns"] == [
        {"role": "user", "text": "第一句。"},
        {"role": "assistant", "text": first_text},
    ]
    assert generator.requests[1].conversation_context_snapshot["turns"][-1] == {
        "role": "assistant",
        "text": first_text,
    }
    turns = client.get(
        f"/v1/conversations/{conversation['id']}/turns", headers=auth_header
    ).json()
    assert [turn["role"] for turn in turns] == ["user", "assistant", "user", "assistant"]
    assert [turn["assistant_text"] for turn in turns if turn["role"] == "assistant"] == [
        first_text,
        second_text,
    ]
    assert all(
        turn["assistant_speech"]["status"] == "failed"
        for turn in turns
        if turn["role"] == "assistant"
    )


def test_speech_provenance_is_append_only_and_non_disclosing(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    configure_free_talk(client, decisions=["preserve"], outputs=["你好呀！"])
    use_speech_provider(client, RecordingSpeechProvider())
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="你好。",
    )
    result = add_user_turn(
        client,
        auth_header,
        conversation_id=conversation["id"],
        utterance_id=uploaded_utterance["id"],
        perception_run_id=perception_id,
    )
    speech = result["assistant_turn"]["assistant_speech"]
    speech_id = uuid.UUID(str(speech["id"]))
    generation_id = result["assistant_turn"]["assistant_generation_run_id"]

    with session_factory() as db:
        run = db.get(AssistantSpeechRun, speech_id)
        assert run is not None
        run.text_snapshot = "rewritten"
        with pytest.raises(ValueError, match="append-only"):
            db.commit()

    other_auth = client.post(
        "/v1/dev/auth", json={"phone_number": "+12025550186"}
    ).json()
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}
    hidden_run = client.get(f"/v1/assistant-speeches/{speech_id}", headers=other_headers)
    hidden_audio = client.get(speech["audio_url"], headers=other_headers)
    hidden_retry = client.post(
        f"/v1/assistant-generations/{generation_id}/speech",
        headers=other_headers,
        json={},
    )
    for hidden in (hidden_run, hidden_audio, hidden_retry):
        assert hidden.status_code == 404
        assert hidden.json()["error"]["code"] == "authorization_error"
