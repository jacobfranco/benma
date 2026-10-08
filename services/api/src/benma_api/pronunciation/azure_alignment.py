"""Azure Mandarin offsets as alignment-only evidence, never free-speech assessment.

Perceived speech uses exact provider Grapheme spans, independent of readings.
The legacy target-relative path retains SAPI reading matching. Provider reference
phone labels and tone digits never establish measured learner pronunciation.
"""

from __future__ import annotations

import math
import re
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from pypinyin.contrib.tone_convert import to_tone3

from benma_api.errors import AnalysisUnsupportedError, ProviderMalformedResponseError
from benma_api.schemas import PerceivedSyllable, PerceivedTimingGroup
from benma_api.speech.providers.azure import request_azure_speech

if TYPE_CHECKING:
    from benma_api.pronunciation.alignment import AlignmentRequest, AlignmentResponse

AZURE_ALIGNMENT_VERSION = "zh-CN-exact-grapheme-v2-target-sapi-v1"
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


def _exact_word_spans(
    raw: dict[str, Any], reference: str, duration_seconds: float | None
) -> list[tuple[int, dict[str, Any], list[tuple[int, str]], dict[str, float]]]:
    """Shared exact-reference/order/bounds checks for character and word evidence."""
    best = raw.get("NBest")
    if not isinstance(best, list) or not best or not isinstance(best[0], dict):
        return []
    words = best[0].get("Words", [])
    if not isinstance(words, list) or any(
        not isinstance(w, dict) or not isinstance(w.get("Word"), str) for w in words
    ):
        return []
    lexical = [(i, c) for i, c in enumerate(reference) if c.isalnum()]
    if [c for w in words for c in w["Word"] if c.isalnum()] != [c for _, c in lexical]:
        return []
    accepted: list[tuple[int, dict[str, Any], list[tuple[int, str]], dict[str, float]]] = []
    cursor, previous_word_end = 0, 0.0
    for wi, word in enumerate(words):
        letters = [c for c in word["Word"] if c.isalnum()]
        positions = lexical[cursor : cursor + len(letters)]
        cursor += len(letters)
        assessment = word.get("PronunciationAssessment")
        error = (assessment if isinstance(assessment, dict) else {}).get(
            "ErrorType", word.get("ErrorType")
        )
        span = _span(word)
        if span and (
            span["start_seconds"] < previous_word_end
            or not math.isfinite(span["end_seconds"])
            or (duration_seconds is not None and span["end_seconds"] > duration_seconds)
        ):
            return []
        if span:
            previous_word_end = span["end_seconds"]
        if not span or error in {"Omission", "Insertion"} or not letters:
            continue
        accepted.append((wi, word, positions, span))
    return accepted


def azure_grapheme_units(
    raw: dict[str, Any], reference: str, *, duration_seconds: float | None = None
) -> list[dict[str, Any]]:
    """Exact provider character spans, independent of reading and reference phones.

    Port of the audited connected-speech mapper. A missing character span stays
    missing; a conflicting tier rejects its word. Whole-reference mismatch and
    overlapping word spans fail closed. Audio bounds are checked by the caller.
    """
    lexical = [(i, c) for i, c in enumerate(reference) if HAN.fullmatch(c)]
    indices = {offset: i for i, (offset, _) in enumerate(lexical)}
    units: list[dict[str, Any]] = []
    for wi, word, positions, span in _exact_word_spans(raw, reference, duration_seconds):
        letters = [c for _, c in positions]
        tier = word.get("Syllables")
        source = "azure_provider_grapheme"
        if tier is None or tier == []:
            if len(letters) != 1 or not HAN.fullmatch(letters[0]):
                continue
            tier = [{**word, "Grapheme": letters[0]}]
            source = "azure_character_word"
        if (
            not isinstance(tier, list)
            or any(not isinstance(g, dict) for g in tier)
            or [g.get("Grapheme") for g in tier] != letters
            or any(not HAN.fullmatch(c) for c in letters)
        ):
            continue
        pending: list[dict[str, Any]] = []
        invalid = False
        for gi, (g, (offset, character)) in enumerate(zip(tier, positions, strict=True)):
            timing = _span(g)
            if timing is None:
                continue
            if (
                not math.isfinite(timing["end_seconds"])
                or timing["end_seconds"] - timing["start_seconds"] > 3
                or timing["start_seconds"] < span["start_seconds"] - 0.001
                or timing["end_seconds"] > span["end_seconds"] + 0.001
                or (pending and timing["start_seconds"] < pending[-1]["end_seconds"])
            ):
                invalid = True
            pending.append(
                {
                    "label": character,
                    "syllable_index": indices[offset],
                    "character_start": offset,
                    "character_end": offset + 1,
                    **timing,
                    "source": source,
                    "provider_word_index": wi,
                    "provider_grapheme_index": gi if source == "azure_provider_grapheme" else None,
                }
            )
        if not invalid:
            units.extend(pending)
    if any(b["start_seconds"] < a["end_seconds"] for a, b in pairwise(units)):
        return []
    return units


def azure_word_timing_groups(
    raw: dict[str, Any],
    reference: str,
    syllables: list[PerceivedSyllable],
    *,
    duration_seconds: float,
    timing_evidence_id: str,
) -> list[PerceivedTimingGroup]:
    """Preserve whole words only when none of their characters owns timing.

    Anonymous syllables and reference phones never enter this transformation.
    Partially character-timed words retain their trustworthy character evidence;
    this initial group representation does not overlap it.
    """
    groups = []
    for _, _word, positions, span in _exact_word_spans(raw, reference, duration_seconds):
        if len(positions) < 2 or any(not HAN.fullmatch(c) for _, c in positions):
            continue
        start, end = positions[0][0], positions[-1][0] + 1
        if end - start != len(positions):
            continue
        members = [s for s in syllables if start <= s.character_start < end]
        if len(members) != len(positions) or any(
            s.start_seconds is not None or s.end_seconds is not None for s in members
        ):
            continue
        # A token span from another source cannot overlap this word either.
        if any(
            s.start_seconds is not None
            and s.end_seconds is not None
            and s.start_seconds < span["end_seconds"]
            and s.end_seconds > span["start_seconds"]
            for s in syllables
        ):
            continue
        groups.append(
            PerceivedTimingGroup(
                character_start=start,
                character_end=end,
                text=reference[start:end],
                **span,
                timing_evidence_id=timing_evidence_id,
            )
        )
    return groups


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
        if request.reference_kind == "perceived_text":
            return AlignmentResponse(
                units=azure_grapheme_units(
                    raw, request.reference_text, duration_seconds=request.duration_seconds
                ),
                raw_result=raw,
                evidence_status="live_provider",
            )
        payload = timing_payload(raw)
        return AlignmentResponse(
            units=azure_syllable_units(payload, request.reference_text, request.pinyin_syllables),
            raw_result=payload,
            evidence_status="live_provider",
        )
