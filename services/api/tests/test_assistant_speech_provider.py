from __future__ import annotations

import httpx
import pytest
from conftest import wav_bytes
from pydantic import ValidationError

from benma_api.assistant_speech.factory import build_assistant_speech_provider
from benma_api.config import Settings
from benma_api.db.models import PronunciationTarget
from benma_api.errors import ProviderMalformedResponseError, ProviderTimeoutError
from benma_api.pronunciation.reference import build_reference_provider
from benma_api.speech.synthesis import (
    AzureSpeechSynthesisProvider,
    SpeechSynthesisRequest,
)


def request(text: str = "好呀，你想买什么水果？") -> SpeechSynthesisRequest:
    return SpeechSynthesisRequest(
        text=text,
        locale="zh-CN",
        voice="zh-CN-Xiaochen:DragonHDLatestNeural",
        model_version="DragonHDLatestNeural",
        rate="0%",
        timeout_seconds=2.0,
    )


def test_azure_synthesis_uses_exact_escaped_text_and_pcm_wav_contract() -> None:
    captured: dict[str, object] = {}

    def exchange(outbound: httpx.Request) -> httpx.Response:
        captured["url"] = str(outbound.url)
        captured["authorization"] = outbound.headers["Ocp-Apim-Subscription-Key"]
        captured["format"] = outbound.headers["X-Microsoft-OutputFormat"]
        captured["body"] = outbound.content.decode()
        return httpx.Response(200, content=wav_bytes(), request=outbound)

    provider = AzureSpeechSynthesisProvider(
        "speech-test-key",
        "eastus",
        transport=httpx.MockTransport(exchange),
    )
    result = provider.synthesize(request("好呀，<水果&朋友>？"))

    assert captured["url"] == ("https://eastus.tts.speech.microsoft.com/cognitiveservices/v1")
    assert captured["authorization"] == "speech-test-key"
    assert captured["format"] == "riff-24khz-16bit-mono-pcm"
    assert "好呀，&lt;水果&amp;朋友&gt;？" in str(captured["body"])
    assert "zh-CN-Xiaochen:DragonHDLatestNeural" in str(captured["body"])
    assert result.audio.startswith(b"RIFF")
    assert result.mime_type == "audio/wav"
    assert result.provider_version == "DragonHDLatestNeural"


def test_azure_synthesis_maps_timeout_and_malformed_audio() -> None:
    def timeout(outbound: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("speech-test-key stayed private", request=outbound)

    timed_out = AzureSpeechSynthesisProvider(
        "speech-test-key",
        "eastus",
        transport=httpx.MockTransport(timeout),
    )
    with pytest.raises(ProviderTimeoutError) as timeout_error:
        timed_out.synthesize(request())
    assert "speech-test-key" not in timeout_error.value.message

    malformed = AzureSpeechSynthesisProvider(
        "speech-test-key",
        "eastus",
        transport=httpx.MockTransport(
            lambda outbound: httpx.Response(200, content=b"not audio", request=outbound)
        ),
    )
    with pytest.raises(ProviderMalformedResponseError):
        malformed.synthesize(request())


def test_reference_and_assistant_domains_share_only_azure_transport_adapter() -> None:
    settings = Settings(
        environment="test",
        assistant_speech_provider="azure",
        reference_speech_provider="azure",
        azure_speech_key="factory-speech-key",
        azure_speech_region="eastus",
    )
    target = PronunciationTarget(
        text="生活",
        display_pinyin="shēng huó",
        pinyin_syllables=["sheng1", "huo2"],
        lexical_tones=[1, 2],
        target_source="manual",
        pinyin_source="fixture",
    )

    assistant = build_assistant_speech_provider(settings)
    reference = build_reference_provider(settings, target)

    assert isinstance(assistant, AzureSpeechSynthesisProvider)
    assert isinstance(reference, AzureSpeechSynthesisProvider)
    assert assistant.product_name == reference.product_name == "speech_synthesis"


def test_assistant_speech_configuration_is_fail_fast() -> None:
    with pytest.raises(ValidationError, match="Azure speech key and region"):
        Settings(
            azure_alignment_enabled=False,
            alignment_provider="disabled",
            environment="test",
            assistant_speech_provider="azure",
            azure_speech_key=None,
            azure_speech_region=None,
        )
    with pytest.raises(ValidationError, match="assistant speech timeout"):
        Settings(
            azure_alignment_enabled=False,
            alignment_provider="disabled",
            environment="test",
            assistant_speech_timeout_seconds=0,
        )


def test_conversation_flash_default_does_not_change_pronunciation_reference() -> None:
    settings = Settings(_env_file=None, environment="test")
    assert settings.assistant_speech_voice == "zh-CN-Xiaochen:DragonHDFlashLatestNeural"
    assert settings.assistant_speech_model_version == "DragonHDFlashLatestNeural"
    assert settings.reference_speech_voice == "zh-CN-Xiaochen:DragonHDLatestNeural"
    assert settings.reference_speech_model_version == "DragonHDLatestNeural"
    overridden = Settings(
        _env_file=None,
        assistant_speech_voice="custom-voice",
        assistant_speech_model_version="custom-model",
    )
    assert overridden.assistant_speech_voice == "custom-voice"
    assert overridden.assistant_speech_model_version == "custom-model"
