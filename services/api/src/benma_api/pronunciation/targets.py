"""Mandarin target parsing and conservative surface-tone expectations.

Lexical tones are immutable facts about the selected dictionary reading. Surface
tones are a separate, explicitly reasoned expectation and are never written back
over lexical tones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from pypinyin import Style, pinyin
from pypinyin.contrib.tone_convert import to_tone, to_tone3

Tone = Literal[0, 1, 2, 3, 4]


@dataclass(frozen=True, slots=True)
class ParsedTarget:
    display_pinyin: str
    pinyin_syllables: list[str]
    lexical_tones: list[int | None]
    alternatives: list[list[str]]
    syllable_units: list[dict[str, Any]]
    surface_tone_expectation: dict[str, Any]
    provenance: str = "pypinyin-automatic"


def _numeric_syllable(value: str) -> tuple[str, int | None]:
    normalized = to_tone3(value.strip().lower(), neutral_tone_with_five=True)
    match = re.fullmatch(r"([a-züv:]+)([1-5])", normalized)
    if match is None:
        return normalized, None
    tone = int(match.group(2))
    return f"{match.group(1)}{tone}", 0 if tone == 5 else tone


def _surface_tones(text: str, lexical: list[int | None]) -> dict[str, Any]:
    surface = list(lexical)
    rules: list[dict[str, Any]] = []
    status = "resolved"
    notes: list[str] = []

    # Only the canonical two-syllable case is deterministic without a prosodic parser.
    if len(surface) == 2 and surface == [3, 3]:
        surface[0] = 2
        rules.append(
            {
                "type": "THIRD_TONE_SANDHI",
                "syllable_index": 0,
                "lexical_tone": 3,
                "expected_surface_tone": 2,
                "confidence": "high",
            }
        )
    elif len(surface) > 2 and any(
        surface[index : index + 2] == [3, 3] for index in range(len(surface) - 1)
    ):
        status = "context_dependent"
        notes.append("Longer third-tone sequences require prosodic grouping.")

    characters = list(text)
    if len(characters) == len(surface):
        for index, character in enumerate(characters):
            following = surface[index + 1] if index + 1 < len(surface) else None
            if character == "不" and lexical[index] == 4 and following == 4:
                surface[index] = 2
                rules.append(
                    {
                        "type": "BU_BEFORE_TONE_FOUR",
                        "syllable_index": index,
                        "lexical_tone": 4,
                        "expected_surface_tone": 2,
                        "confidence": "high",
                    }
                )
            if character == "一" and lexical[index] == 1 and following in {1, 2, 3, 4}:
                expected = 2 if following == 4 else 4
                surface[index] = expected
                rules.append(
                    {
                        "type": "YI_CONTEXTUAL_ALTERNATION",
                        "syllable_index": index,
                        "lexical_tone": 1,
                        "expected_surface_tone": expected,
                        "confidence": "high",
                    }
                )
    elif "一" in text or "不" in text:
        status = "context_dependent"
        notes.append("Character-to-syllable mapping is not one-to-one for a contextual rule.")

    for index, tone in enumerate(lexical):
        if tone == 0:
            rules.append(
                {
                    "type": "NEUTRAL_TONE_TARGET",
                    "syllable_index": index,
                    "lexical_tone": 0,
                    "expected_surface_tone": 0,
                    "confidence": "high",
                    "shape_grading": "unavailable",
                }
            )

    return {
        "lexical_tones": lexical,
        "expected_surface_tones": surface if status == "resolved" else None,
        "status": status,
        "rules": rules,
        "notes": notes,
        "engine": "benma-surface-tone-v1",
        "capability_state": "experimental",
    }


def surface_tone_expectation(text: str, lexical: list[int | None]) -> dict[str, Any]:
    """Public pure function for table-driven rule tests and future import tools."""

    return _surface_tones(text, lexical)


def parse_mandarin_target(text: str) -> ParsedTarget:
    tone3_groups = pinyin(
        text,
        style=Style.TONE3,
        heteronym=True,
        neutral_tone_with_five=True,
    )
    selected: list[str] = []
    tones: list[int | None] = []
    alternatives: list[list[str]] = []
    syllable_units: list[dict[str, Any]] = []
    display: list[str] = []
    for index, group in enumerate(tone3_groups):
        numeric, tone = _numeric_syllable(group[0])
        selected.append(numeric)
        tones.append(tone)
        alternatives.append([_numeric_syllable(item)[0] for item in group])
        marked = to_tone(numeric.replace("5", "")) if tone is not None else numeric
        display.append(marked)
        syllable_units.append(
            {
                "character_span": {"start": index, "end": index + 1},
                "characters": text[index : index + 1],
                "pinyin": numeric,
                "pinyin_base": re.sub(r"[1-5]$", "", numeric),
                "lexical_tone": tone,
            }
        )
    return ParsedTarget(
        display_pinyin=" ".join(display),
        pinyin_syllables=selected,
        lexical_tones=tones,
        alternatives=alternatives,
        syllable_units=syllable_units,
        surface_tone_expectation=_surface_tones(text, tones),
    )


def parse_corrected_pinyin(text: str, corrected_pinyin: str) -> ParsedTarget:
    values = corrected_pinyin.strip().split()
    if not values:
        raise ValueError("corrected pinyin must include at least one syllable")
    if any(
        not re.search(r"[1-5]$", value.strip())
        and not re.search(r"[1-4]$", to_tone3(value.strip(), neutral_tone_with_five=False))
        for value in values
    ):
        raise ValueError("each corrected pinyin syllable must explicitly include a tone")
    numeric_and_tones = [_numeric_syllable(value) for value in values]
    if any(tone is None for _, tone in numeric_and_tones):
        raise ValueError("each corrected pinyin syllable must include a tone 1-4 or neutral tone 5")
    if len(values) != len(text):
        raise ValueError(
            "corrected pinyin must currently map one syllable to each target character"
        )
    numeric = [item[0] for item in numeric_and_tones]
    tones = [item[1] for item in numeric_and_tones]
    units = [
        {
            "character_span": {"start": index, "end": index + 1},
            "characters": text[index : index + 1],
            "pinyin": syllable,
            "pinyin_base": re.sub(r"[1-5]$", "", syllable),
            "lexical_tone": tones[index],
        }
        for index, syllable in enumerate(numeric)
    ]
    return ParsedTarget(
        display_pinyin=" ".join(to_tone(item.replace("5", "")) for item in numeric),
        pinyin_syllables=numeric,
        lexical_tones=tones,
        alternatives=[[item] for item in numeric],
        syllable_units=units,
        surface_tone_expectation=_surface_tones(text, tones),
        provenance="user-corrected",
    )
