"""Small, reviewed learner spans from saved perceived readings, not timing or intent.

These four expressions are deliberately not a general tokenizer/classifier list.
Reading phrase matches include grammar, names and idioms: they are not word edges.
The client separately partitions whole timing units and may veto these candidates.
"""

from __future__ import annotations

from itertools import pairwise

from pypinyin.contrib.tone_convert import to_tone3

from benma_api.schemas import PerceivedSyllable, PronunciationChunkCandidate

CHUNK_POLICY_VERSION = "perceived-pronunciation-chunks-v1"
# Citation readings only. Preserve saved overrides and contextual expectations.
REVIEWED_READINGS = {
    "雨伞": ({"yu3"}, {"san3"}),
    "这个": ({"zhe4"}, {"ge4", "ge5"}),
    "那个": ({"na4"}, {"ge4", "ge5"}),
    "一个": ({"yi1"}, {"ge4"}),
}


def pronunciation_chunk_candidates(
    text: str, syllables: list[PerceivedSyllable]
) -> list[PronunciationChunkCandidate]:
    """Read-only, deterministic, and usable for old saved analyses without reanalysis."""
    candidates: list[PronunciationChunkCandidate] = []
    for left, right in pairwise(syllables):
        start, end = left.character_start, right.character_end
        word = left.characters + right.characters
        readings = REVIEWED_READINGS.get(word)
        if (
            readings is None
            or start < 0
            or end > len(text)
            or left.character_end != start + 1
            or right.character_start != left.character_end
            or end != start + 2
            or right.index != left.index + 1
            or text[start:end] != word
        ):
            continue
        if any(
            s.reading_source == "unresolved"
            or not s.pinyin
            or to_tone3(s.pinyin, neutral_tone_with_five=True) not in allowed
            for s, allowed in zip((left, right), readings, strict=True)
        ):
            continue
        if word.endswith("个") and end < len(text) and text[end] == "个":
            continue
        if word == "一个" and left.surface_rule != "yi_quantity":
            # Ordinals, number strings, reduplication and unknown older context
            # are not licensed by the reviewed quantity-use rule.
            continue
        reason = (
            "lexical_word" if word == "雨伞"
            else "numeral_classifier" if word == "一个"
            else "demonstrative_classifier"
        )
        candidates.append(PronunciationChunkCandidate(
            text=word,
            character_start=start,
            character_end=end,
            syllable_indices=[left.index, right.index],
            reason=reason,
        ))
    return candidates
