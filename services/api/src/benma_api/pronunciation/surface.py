"""Conservative tone categories for exact text; no audio, intent, or meaning input.

These are ordinary connected-speech expectations, not guaranteed prosody or F0.
Long third-tone chains, ambiguous 一 uses, and reduplication stay unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass

SURFACE_VERSION = "exact-text-surface-v1.1"
THIRD_TONE_WORDS = frozenset({"你好", "很好", "可以", "水果", "所有", "了解", "管理", "理想"})
YI_QUANTITY_FOLLOWERS = frozenset(
    "个只本张条件杯瓶碗次遍天年小时种点些位辆块颗把支双头匹座间台份笔封"
)
DIGITS = frozenset("零〇一二三四五六七八九十百千万亿两")


@dataclass(frozen=True, slots=True)
class SurfaceExpectation:
    tone: int | None
    rule: str


def surface_expectations(
    text: str, offsets: list[int], lexical: list[int | None]
) -> list[SurfaceExpectation]:
    if len(offsets) != len(lexical):
        raise ValueError("surface expectations require exact character offsets")
    result = [SurfaceExpectation(t, "lexical_neutral" if t == 0 else "unchanged") for t in lexical]

    def adjacent(a: int, b: int) -> bool:
        return 0 <= a < len(offsets) and 0 <= b < len(offsets) and offsets[b] == offsets[a] + 1

    i = 0
    while i < len(lexical):
        if lexical[i] != 3:
            i += 1
            continue
        end = i + 1
        while end < len(lexical) and adjacent(end - 1, end) and lexical[end] == 3:
            end += 1
        if end - i >= 2:
            word = text[offsets[i] : offsets[end - 1] + 1]
            clause_start = offsets[i] == 0 or not text[offsets[i] - 1].isalnum()
            clause_end = (
                offsets[end - 1] + 1 == len(text) or not text[offsets[end - 1] + 1].isalnum()
            )
            if end - i == 2 and (word in THIRD_TONE_WORDS or (clause_start and clause_end)):
                result[i] = SurfaceExpectation(2, "third_tone_pair")
                result[i + 1] = SurfaceExpectation(3, "third_tone_pair_final")
            else:
                for index in range(i, end):
                    result[index] = SurfaceExpectation(None, "prosodic_grouping_unresolved")
        i = end
    for i, offset in enumerate(offsets):
        character = text[offset]
        before = text[offset - 1] if offset else ""
        after = text[offset + 1] if offset + 1 < len(text) else ""
        following = lexical[i + 1] if adjacent(i, i + 1) else None
        if lexical[i] is None:
            result[i] = SurfaceExpectation(None, "reading_unresolved")
        elif character == "不" and lexical[i] == 4:
            if before and before == after:
                result[i] = SurfaceExpectation(None, "reduplication_prosody_unresolved")
            elif following == 4:
                result[i] = SurfaceExpectation(2, "bu_before_fourth")
        elif character == "一" and lexical[i] == 1:
            if before == "第" or (before in DIGITS and before) or (after in DIGITS and after):
                result[i] = SurfaceExpectation(1, "yi_ordinal_or_number")
            elif before and before == after:
                result[i] = SurfaceExpectation(None, "reduplication_prosody_unresolved")
            elif following in {1, 2, 3, 4} and after in YI_QUANTITY_FOLLOWERS:
                result[i] = SurfaceExpectation(2 if following == 4 else 4, "yi_quantity")
            elif following is None and (not after or not after.isalnum()):
                result[i] = SurfaceExpectation(1, "yi_isolated_or_final")
            else:
                result[i] = SurfaceExpectation(None, "yi_grammatical_context_unresolved")
        elif (
            character == "个"
            and lexical[i] == 4
            and adjacent(i - 1, i)
            and before == "一"
            and after != "个"
            and result[i - 1].rule == "yi_quantity"
        ):
            # Quantity-classifier 个 can be reduced/neutral or stressed. Exact
            # text does not choose that realization, so require no fixed T4
            # contour. Keep lexical gè and 一's preceding sandhi unchanged.
            result[i] = SurfaceExpectation(None, "quantity_ge_reduction_optional")
    return result
