"""Azure Mandarin offsets as alignment-only evidence, never free-speech assessment.

The zh-CN SAPI response uses full pinyin syllables in its Phonemes tier. We accept
one such entry per exact character only when the base reading matches. Tone digits
are provider reference labels (sometimes sandhi), never measured learner tones.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any

from pypinyin.contrib.tone_convert import to_tone3

from benma_api.errors import AnalysisUnsupportedError, ProviderMalformedResponseError
from benma_api.speech.providers.azure import request_azure_speech

if TYPE_CHECKING:
    from benma_api.pronunciation.alignment import AlignmentRequest, AlignmentResponse

AZURE_ALIGNMENT_VERSION = "zh-CN-sapi-syllable-offsets-v1"
AZURE_TIMING_CONFIG = {
    "GradingSystem": "HundredMark",
    "Granularity": "Phoneme",
    "Dimension": "Comprehensive",
    "EnableMiscue": True,
    "PhonemeAlphabet": "SAPI",
}
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def _span(item: dict[str, Any]) -> dict[str, float] | None:
    start, duration = item.get("Offset"), item.get("Duration")
    if (
        not isinstance(start, (int, float))
        or isinstance(start, bool)
        or not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not math.isfinite(start)
        or not math.isfinite(duration)
        or start < 0
        or duration <= 0
    ):
        return None
    return {"start_seconds": start / 10_000_000, "end_seconds": (start + duration) / 10_000_000}


def timing_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Whitelist timing fields. Scores, recognized prose, and IDs are not alignment truth."""
    try:
        best = raw["NBest"][0]
        words = best["Words"]
        if not isinstance(words, list):
            raise TypeError
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderMalformedResponseError("Azure response has no word timing") from exc
    output = []
    for word in words:
        if not isinstance(word, dict):
            continue
        assessment = word.get("PronunciationAssessment")
        error = (
            assessment.get("ErrorType") if isinstance(assessment, dict) else word.get("ErrorType")
        )
        output.append(
            {
                "text": word.get("Word"),
                "timing": _span(word),
                "omitted_or_inserted": error in {"Omission", "Insertion"},
                "phones": [
                    {"phone": p.get("Phoneme"), "timing": _span(p)}
                    for p in word.get("Phonemes", [])
                    if isinstance(p, dict)
                ],
            }
        )
    return {"words": output}


def azure_syllable_units(
    payload: dict[str, Any], reference: str, readings: list[str]
) -> list[dict[str, Any]]:
    """No equal splits and no fuzzy text matching; uncertain words remain untimed."""
    lexical = [(i, c) for i, c in enumerate(reference) if c.isalnum()]
    han_offsets = [i for i, c in enumerate(reference) if HAN.fullmatch(c)]
    by_offset = {offset: index for index, offset in enumerate(han_offsets)}
    if len(readings) != len(han_offsets):
        return []
    units: list[dict[str, Any]] = []
    cursor = 0
    for word in payload.get("words", []):
        if not isinstance(word, dict) or not isinstance(word.get("text"), str):
            return []
        letters = [c for c in word["text"] if c.isalnum()]
        if word.get("omitted_or_inserted") and not word.get("timing"):
            # An omitted exact reference word still consumes its reference characters.
            if letters != [c for _, c in lexical[cursor : cursor + len(letters)]]:
                return []
            cursor += len(letters)
            continue
        positions = lexical[cursor : cursor + len(letters)]
        if not letters or letters != [c for _, c in positions]:
            # A repeated word cannot be located safely by searching forward in text.
            return []
        cursor += len(letters)
        if word.get("omitted_or_inserted"):
            continue
        phones = word.get("phones", [])
        for j, (offset, character) in enumerate(positions):
            index = by_offset.get(offset)
            if index is None:
                continue
            source = "azure_character_word"
            phone_label = None
            span = word.get("timing") if len(letters) == 1 else None
            if len(phones) == len(letters):
                phone = phones[j]
                label = str(phone.get("phone", ""))
                # A single initial/final is not a syllable, even when counts coincide.
                match = re.fullmatch(r"([a-züv:]+)\s*([0-5])", label.lower())
                reading = to_tone3(readings[index], neutral_tone_with_five=True)
                base = re.sub(r"[1-5]$", "", reading).replace("v", "ü").replace("u:", "ü")
                if match and match[1].replace("v", "ü").replace("u:", "ü") == base:
                    span = phone.get("timing")
                    source, phone_label = "azure_sapi_syllable", label
            if not isinstance(span, dict):
                continue
            word_span = word.get("timing")
            if isinstance(word_span, dict) and (
                span["start_seconds"] < word_span["start_seconds"] - 0.001
                or span["end_seconds"] > word_span["end_seconds"] + 0.001
            ):
                continue
            units.append(
                {
                    "label": character,
                    "syllable_index": index,
                    "character_start": offset,
                    "character_end": offset + 1,
                    **span,
                    "source": source,
                    "reference_phone_label": phone_label,
                }
            )
    return units


class AzureSpeechAligner:
    algorithm_name = "azure_speech_alignment_only"
    algorithm_version = AZURE_ALIGNMENT_VERSION

    def __init__(self, key: str, region: str, timeout_seconds: float = 12) -> None:
        self.key, self.region, self.timeout_seconds = key, region, timeout_seconds
        self.configuration = {
            "locale": "zh-CN",
            "region": region,
            "purpose": "alignment_only",
            "request": AZURE_TIMING_CONFIG,
            "reference_kind": "persisted_reference",
            "timeout_seconds": timeout_seconds,
            "maximum_duration_seconds": 30,
            "mapping": AZURE_ALIGNMENT_VERSION,
        }

    def align(self, request: AlignmentRequest) -> AlignmentResponse:
        # Local import avoids an alignment factory/module cycle.
        from benma_api.pronunciation.alignment import AlignmentResponse

        if request.duration_seconds > 30:
            raise AnalysisUnsupportedError("Azure short-audio timing supports at most 30 seconds")
        raw = request_azure_speech(
            audio=request.audio_path.read_bytes(),
            key=self.key,
            region=self.region,
            config={**AZURE_TIMING_CONFIG, "ReferenceText": request.reference_text},
            timeout_seconds=min(request.timeout_seconds, self.timeout_seconds),
        )
        payload = timing_payload(raw)
        return AlignmentResponse(
            units=azure_syllable_units(payload, request.reference_text, request.pinyin_syllables),
            raw_result=payload,
            evidence_status="live_provider",
        )
