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

from benma_api.pronunciation.readings import LEXICAL_NEUTRAL_READINGS
from benma_api.pronunciation.surface import SURFACE_VERSION, surface_expectations

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
    offsets = [i for i, c in enumerate(text) if re.fullmatch(r"[\u3400-\u4dbf\u4e00-\u9fff]", c)]
    if len(offsets) != len(lexical):
        return {
            "lexical_tones": lexical,
            "expected_surface_tones": None,
            "status": "context_dependent",
            "rules": [],
            "notes": ["Mapping unresolved"],
            "engine": SURFACE_VERSION,
            "capability_state": "experimental",
        }
    expectations = surface_expectations(text, offsets, lexical)
    resolved = all(e.tone is not None for e in expectations)
    names = {
        "third_tone_pair": "THIRD_TONE_SANDHI",
        "bu_before_fourth": "BU_BEFORE_TONE_FOUR",
        "yi_quantity": "YI_CONTEXTUAL_ALTERNATION",
        "lexical_neutral": "NEUTRAL_TONE_TARGET",
    }
    return {
        "lexical_tones": lexical,
        "expected_surface_tones": [e.tone for e in expectations] if resolved else None,
        "status": "resolved" if resolved else "context_dependent",
        "rules": [
            {
                "type": names.get(e.rule, e.rule),
                "syllable_index": i,
                "lexical_tone": lexical[i],
                "expected_surface_tone": e.tone,
                "confidence": "high" if e.tone is not None else "unresolved",
            }
            for i, e in enumerate(expectations)
            if e.rule != "unchanged"
        ],
        "notes": [] if resolved else ["Prosodic or grammatical grouping is unresolved."],
        "engine": SURFACE_VERSION,
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
    # Reviewed lexical words only; no general reduplication neutralization.
    for word, readings in LEXICAL_NEUTRAL_READINGS.items():
        for match in re.finditer(re.escape(word), text):
            if len(tone3_groups) == len(text):
                tone3_groups[match.start() : match.end()] = [[reading] for reading in readings]
    selected: list[str] = []
    tones: list[int | None] = []
    alternatives: list[list[str]] = []
    syllable_units: list[dict[str, Any]] = []
    display: list[str] = []
    for index, group in enumerate(tone3_groups):
        numeric, tone = _numeric_syllable(group[0])
        if text[index : index + 1] == "一" and numeric in {"yi2", "yi4", "yi5"}:
            numeric, tone = "yi1", 1
        elif text[index : index + 1] == "不" and numeric in {"bu2", "bu5"}:
            numeric, tone = "bu4", 4
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
