"""Read-only reuse of Benma service functions in its existing Python environment."""

# ruff: noqa: E402
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services/api/src"))

from benma_api.audio.presence import require_speech
from benma_api.audio.service import canonicalize, inspect_audio
from benma_api.config import Settings
from benma_api.pronunciation.chunks import pronunciation_chunk_candidates
from benma_api.pronunciation.perceived import perceived_syllables
from benma_api.speech.contracts import UnknownTargetPerceptionInput
from benma_api.speech.providers.factory import build_perception_provider
from pypinyin.contrib.tone_convert import to_tone, to_tone3


def expectations(text):
    syllables = perceived_syllables(text, {})
    return {
        "syllables": [
            s.model_dump(mode="json")
            | {
                "pinyin_numeric": to_tone3(s.pinyin, neutral_tone_with_five=True)
                if s.pinyin
                else None,
            }
            for s in syllables
        ],
        "chunks": [
            c.model_dump(mode="json") for c in pronunciation_chunk_candidates(text, syllables)
        ],
    }


def run(request):
    if request["action"] == "expectations":
        return expectations(request["text"])
    if request["action"] == "render":
        return [to_tone(p) if p else "[unavailable]" for p in request["pinyin"]]
    if request["action"] != "prepare":
        raise ValueError("unsupported_bridge_action")
    settings = Settings(_env_file=ROOT / "services/api/.env")
    if settings.environment not in ("development", "test"):
        raise ValueError("development_environment_required")
    source, destination = Path(request["source"]), Path(request["destination"])
    inspect_audio(source, settings)
    data = canonicalize(source, settings)
    require_speech(data)
    with destination.open("xb") as stream:
        stream.write(data)
    result = expectations(request["text"])
    result["asr"] = {
        "status": "unavailable",
        "transcript": None,
        "reason": "live_provider_not_configured_or_not_requested",
    }
    if request.get("asr") and settings.perception_provider not in ("disabled", "replay"):
        try:
            provider = build_perception_provider(settings)
            response = provider.perceive(
                UnknownTargetPerceptionInput(
                    utterance_id=uuid.uuid4(),
                    canonical_audio=data,
                    mime_type="audio/wav",
                    language_hint="zh",
                    timeout_seconds=45,
                )
            )
            result["asr"] = {
                "status": "available",
                "provider": provider.provider_name,
                **response.evidence.normalized(),
            }
        except Exception as error:
            result["asr"] = {"status": "failed", "transcript": None, "reason": type(error).__name__}
    return result


if __name__ == "__main__":
    print(json.dumps(run(json.loads(sys.stdin.read())), ensure_ascii=False, allow_nan=False))
