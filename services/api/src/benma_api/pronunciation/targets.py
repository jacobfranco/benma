"""Mandarin target parsing with explicit automatic provenance and alternatives."""

from __future__ import annotations

from dataclasses import dataclass

from pypinyin import Style, pinyin


@dataclass(frozen=True, slots=True)
class ParsedTarget:
    display_pinyin: str
    pinyin_syllables: list[str]
    lexical_tones: list[int | None]
    alternatives: list[list[str]]
    provenance: str = "pypinyin-automatic"


def parse_mandarin_target(text: str) -> ParsedTarget:
    tone3_groups = pinyin(
        text,
        style=Style.TONE3,
        heteronym=True,
        neutral_tone_with_five=True,
    )
    display_groups = pinyin(text, style=Style.TONE, heteronym=False)
    selected = [group[0] for group in tone3_groups]
    tones: list[int | None] = []
    for syllable in selected:
        tones.append(int(syllable[-1]) if syllable and syllable[-1] in "12345" else None)
    return ParsedTarget(
        display_pinyin=" ".join(group[0] for group in display_groups),
        pinyin_syllables=selected,
        lexical_tones=tones,
        alternatives=[list(group) for group in tone3_groups],
    )
