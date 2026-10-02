"""Research-only grapheme timing: identity and spans never depend on pinyin.

Production Azure mapping is deliberately unchanged. A phone tier is not a fallback
syllable segmentation. The raw Azure response remains authoritative provenance.
"""

from __future__ import annotations

import copy
import math
import re

from benma_api.pronunciation.azure_alignment import HAN, _span
from benma_api.pronunciation.perceived import perceived_syllables
from pypinyin.contrib.tone_convert import to_tone3

MAPPING_VERSION = "azure-exact-grapheme-v2"
READING_VERSION = "perceived-word-context-v1"
# Existing production azure_syllable_units containment allowance, not a new tolerance.
WORD_TOLERANCE_SECONDS = 0.001


def lexical_chars(text):
    return [(i, c) for i, c in enumerate(text) if c.isalnum()]


def grapheme_candidates(raw, text):
    """Return normalized words, timing candidates and explicit mapping issues.

    Whole-reference identity fails closed. A malformed grapheme tier rejects its
    whole word; a missing span leaves only that character untimed. Cross-word
    ordering/audio/duration checks are additionally enforced by alignment_evidence.
    """
    try:
        raw_words = raw["NBest"][0]["Words"]
        if not isinstance(raw_words, list) or any(
            not isinstance(w, dict) or not isinstance(w.get("Word"), str) for w in raw_words
        ):
            raise ValueError("invalid words")
    except (KeyError, IndexError, TypeError, ValueError):
        return [], [], ["malformed_alignment:invalid_words"]
    positions = lexical_chars(text)
    if [c for w in raw_words for _, c in lexical_chars(w["Word"])] != [c for _, c in positions]:
        return [], [], ["asr_timing_text_conflict"]
    han_indices = {
        offset: i for i, (offset, _) in enumerate(p for p in positions if HAN.fullmatch(p[1]))
    }
    words, candidates, issues = [], [], []
    cursor = 0
    for wi, raw_word in enumerate(raw_words):
        letters = [c for _, c in lexical_chars(raw_word["Word"])]
        matched = positions[cursor : cursor + len(letters)]
        cursor += len(letters)
        assessment = raw_word.get("PronunciationAssessment")
        assessment = assessment if isinstance(assessment, dict) else {}
        error = assessment.get("ErrorType", raw_word.get("ErrorType"))
        word_span = _span(raw_word)
        word = {
            "text": raw_word["Word"],
            "timing": word_span,
            "omitted_or_inserted": error in {"Omission", "Insertion"},
            "raw_provider_word": copy.deepcopy(raw_word),
        }
        words.append(word)
        prefix = f"word[{wi}]"
        if not matched:
            issues.append(f"{prefix}:empty_lexical_word")
            continue
        if word["omitted_or_inserted"]:
            issues.append(f"{prefix}:provider_omission_or_insertion")
            continue
        if word_span is None:
            issues.append(f"{prefix}:missing_or_invalid_word_timing")
            continue
        tier = raw_word.get("Syllables")
        source = "azure_provider_grapheme"
        if tier is None or tier == []:
            # A single Han word is already a character span. Never subdivide a word.
            if len(letters) != 1 or not HAN.fullmatch(letters[0]):
                issues.append(f"{prefix}:grapheme_timing_unavailable")
                continue
            tier = [{"Grapheme": letters[0], **raw_word}]
            source = "azure_character_word"
        if (
            not isinstance(tier, list)
            or any(not isinstance(g, dict) for g in tier)
            or [g.get("Grapheme") for g in tier] != letters
            or any(not HAN.fullmatch(c) for c in letters)
        ):
            issues.append(f"{prefix}:grapheme_sequence_conflict")
            continue
        pending, previous_end, invalid = [], word_span["start_seconds"], False
        for gi, (g, (offset, character)) in enumerate(zip(tier, matched, strict=True)):
            span = _span(g)
            if span is None:
                issues.append(f"{prefix}:grapheme[{gi}]:missing_or_invalid_timing")
                # Missing timing is not estimated from neighbors or phones.
                continue
            if (
                span["start_seconds"] < word_span["start_seconds"] - WORD_TOLERANCE_SECONDS
                or span["end_seconds"] > word_span["end_seconds"] + WORD_TOLERANCE_SECONDS
                or (pending and span["start_seconds"] < previous_end)
            ):
                invalid = True
                issues.append(f"{prefix}:invalid_or_nonmonotonic_grapheme_span")
            previous_end = span["end_seconds"]
            pending.append(
                {
                    "label": character,
                    "syllable_index": han_indices[offset],
                    "character_start": offset,
                    "character_end": offset + 1,
                    **span,
                    "source": source,
                    "provider_timing": {
                        "word_index": wi,
                        "grapheme_index": gi if source == "azure_provider_grapheme" else None,
                        "provider_word": raw_word["Word"],
                        "grapheme": character,
                        "raw_source": f"/NBest/0/Words/{wi}"
                        + (f"/Syllables/{gi}" if source == "azure_provider_grapheme" else ""),
                        "raw_entry": copy.deepcopy(
                            g if source == "azure_provider_grapheme" else raw_word
                        ),
                        "validity": "accepted_exact_provider_span",
                    },
                }
            )
        if not invalid:
            candidates.extend(pending)
    return words, candidates, issues


def contextual_readings(text, evidence, words):
    """Use exact perceived word context with the existing conservative phrase engine.

    No provider phone, score, target or first-heteronym default is a reading input.
    Full perceived-clause resolution has priority. Word context may only fill a
    previously unresolved reading with a phrase resolution, never a
    single-character dictionary guess. Dictionary gaps stay unresolved.
    """
    readings = perceived_syllables(text, evidence)
    by_offset = {s.character_start: s for s in readings}
    for word in words:
        start, end = word.character_start, word.character_end
        # Contiguous exact substring only; never concatenate across punctuation.
        context = text[start:end]
        for local in perceived_syllables(context, {}):
            current = by_offset.get(start + local.character_start)
            if (
                current is not None
                and current.reading_source == "unresolved"
                and local.reading_source == "phrase"
                and local.pinyin is not None
            ):
                # Surface expectations remain those of the full clause. A word is
                # not an independent prosodic clause and cannot supply grammar rules.
                current.pinyin = local.pinyin
                current.lexical_tone = local.lexical_tone
                current.reading_source = "phrase"
                current.resolution_confidence = "high"
                current.alternatives = local.alternatives
    return readings


def reference_phones(raw_word, candidate, reading):
    """Attach a SAPI reference label only with exact timing AND resolved base match.

    Equal counts alone are insufficient. An unresolved reading can have valid
    timing while this conservative attachment abstains; raw phones remain saved.
    """
    if reading.pinyin is None:
        return []
    base = re.sub(r"[1-5]$", "", to_tone3(reading.pinyin, neutral_tone_with_five=True))
    base = base.replace("v", "ü").replace("u:", "ü")
    phones = raw_word.get("Phonemes", [])
    if not isinstance(phones, list):
        return []
    matches = []
    for phone in phones:
        if not isinstance(phone, dict):
            continue
        label = phone.get("Phoneme")
        match = (
            re.fullmatch(r"([a-züv:]+)\s*([0-5])", label.lower())
            if isinstance(label, str)
            else None
        )
        span = _span(phone)
        if (
            not match
            or match[1].replace("v", "ü").replace("u:", "ü") != base
            or span != {k: candidate[k] for k in ("start_seconds", "end_seconds")}
        ):
            continue
        assessment = phone.get("PronunciationAssessment")
        assessment = assessment if isinstance(assessment, dict) else {}
        score = assessment.get("AccuracyScore", phone.get("AccuracyScore"))
        if type(score) not in (float, int) or not math.isfinite(score):
            score = None
        matches.append({"label": label, "score": score, "raw_entry": copy.deepcopy(phone)})
    return matches if len(matches) == 1 else []
