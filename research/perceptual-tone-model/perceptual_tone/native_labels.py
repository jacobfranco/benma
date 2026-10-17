"""Weak surface-tone supervision. Text stays on the label side of the boundary."""

import re
import sys

from pypinyin.contrib.tone_convert import to_tone3

from .common import ROOT

sys.path.insert(0, str(ROOT / "services/api/src"))
from benma_api.pronunciation.readings import READING_VERSION, resolve_run
from benma_api.pronunciation.surface import (
    DIGITS,
    SURFACE_VERSION,
    surface_expectations,
)

VERSION = "native-weak-surface-v2"
CLASSES = ("T1", "T2", "T3", "T4", "NEUTRAL")
HAN = re.compile(r"[\u3400-\u9fff]")


def tone_number(reading):
    value = to_tone3(reading.lower(), neutral_tone_with_five=True)
    if not re.fullmatch(r"[a-züv:]+[1-5]", value):
        raise ValueError("Not one pinyin syllable")
    return int(value[-1]) % 5


def strip_tone(reading):
    tone_number(reading)
    value = to_tone3(reading.lower(), neutral_tone_with_five=True)
    return value[:-1].replace("u:", "v").replace("ü", "v")


def labels(text):
    """Preserve punctuation; whitespace is segmentation, never a prosodic pause.

    Reuse frozen exact-text linguistic logic, with an additional exclusion for
    T3 next to an unresolved reading. Never infer neutral from short duration.
    """
    text = re.sub(r"\s+", "", text)
    entries = []
    for match in re.finditer(r"[\u3400-\u9fff]+", text):
        for j, (reading, source, alternatives) in enumerate(resolve_run(match.group())):
            entries.append(
                {
                    "offset": match.start() + j,
                    "hanzi": match.group()[j],
                    "pinyin": reading,
                    "reading_source": source,
                    "reading_alternatives": list(alternatives),
                    "lexical_tone": tone_number(reading) if reading else None,
                }
            )
    offsets = [r["offset"] for r in entries]
    lexical = [r["lexical_tone"] for r in entries]
    resolved = surface_expectations(text, offsets, lexical)
    for i, (row, surface) in enumerate(zip(entries, resolved, strict=True)):
        following = entries[i + 1] if i + 1 < len(entries) else None
        adjacent = following is not None and following["offset"] == row["offset"] + 1
        reason = None
        if row["hanzi"] == "儿" or (adjacent and following["hanzi"] == "儿"):
            reason = "erhua_or_er_ownership_unresolved"
        if row["lexical_tone"] == 3 and adjacent and following["lexical_tone"] is None:
            reason = "t3_following_reading_unresolved"
        if surface.tone is None:
            reason = surface.rule
        before = text[row["offset"] - 1] if row["offset"] else ""
        after = text[row["offset"] + 1] if row["offset"] + 1 < len(text) else ""
        # Benma expectations allow lexical fallback; supervised labels cannot.
        # Cardinal-number 一 can undergo sandhi; keep only explicit ordinal 一.
        if row["hanzi"] == "一" and before != "第" and (before in DIGITS or after in DIGITS):
            reason = "cardinal_yi_surface_uncertain"
        # AB/AA neutralization is grammatical, not reliably resolved by citation
        # dictionary tones. Retain explicit lexical neutral entries, e.g. 妈妈.
        if row["hanzi"] == before and row["lexical_tone"] not in (None, 0):
            reason = "reduplication_reduction_optional"
        row.update(
            index=i,
            surface_tone=None if reason else surface.tone,
            label=None if reason else ("NEUTRAL" if surface.tone == 0 else f"T{surface.tone}"),
            exclusion=reason,
            rule=surface.rule,
            phonetic_base=strip_tone(row["pinyin"]) if row["pinyin"] else None,
            next_lexical_tone=following["lexical_tone"] if adjacent else None,
            phrase_position="medial" if adjacent else "final",
            label_provenance={
                "version": VERSION,
                "reading": READING_VERSION,
                "surface": SURFACE_VERSION,
                "kind": "derived_not_perceptual",
            },
        )
    return text, entries


def t3_groups(row):
    if row["lexical_tone"] != 3:
        return []
    result = ["lexical_T3", "phrase_" + row["phrase_position"]]
    following = row["next_lexical_tone"]
    if following is not None:
        result.append("before_" + ("NEUTRAL" if following == 0 else f"T{following}"))
    if row["label"] == "T3":
        result.append("non_sandhi_T3")
    elif row["label"] == "T2":
        result.append("sandhi_T3_to_T2")
    else:
        result.append("excluded_T3")
    return result
