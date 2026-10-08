"""Lexical readings of exact text, never semantic correction or acoustic grading.

pypinyin's heteronym mode exposes rare dictionary readings for characters outside
its phrase lexicon. Use longest phrase matches, a small reviewed lexicon supplement,
then grammatical rules; never resolve a remaining polyphone by list order.
"""

from functools import lru_cache
from typing import Literal

from pypinyin import Style, pinyin
from pypinyin.contrib.tone_convert import to_tone3
from pypinyin.phrases_dict import phrases_dict

from benma_api.pronunciation.surface import DIGITS, YI_QUANTITY_FOLLOWERS

READING_VERSION = "exact-text-lexical-context-v3.2"
ReadingSource = Literal["phrase", "grammar", "dictionary", "unresolved"]
# Reviewed contemporary Mandarin defaults; the dictionary also lists historical
# variants. This is deliberately NOT a generic first-dictionary-reading fallback.
DOMINANT = {"聊": "liao2", "末": "mo4", "去": "qu4", "一": "yi1", "不": "bu4"}
# Citation readings, including lexical neutral tones. No sandhi substitutions.
LEXICAL_NEUTRAL_READINGS = {"妈妈": ("ma1", "ma5")}
SUPPLEMENT = {
    **LEXICAL_NEUTRAL_READINGS,
    "很好": ("hen3", "hao3"),
    "聊聊": ("liao2", "liao2"),
    "聊天": ("liao2", "tian1"),
    "周末": ("zhou1", "mo4"),
    "今天": ("jin1", "tian1"),
    "酒吧": ("jiu3", "ba1"),
    "网吧": ("wang3", "ba1"),
    "吧台": ("ba1", "tai2"),
}


def citation_reading(character: str, reading: str) -> str:
    # The phrase dictionary sometimes already spells sandhi (不是 bú shì, 一个 yí gè).
    # Keep citation tone distinct from surface realization in our lexical field.
    if character == "一" and reading in {"yi1", "yi2", "yi4", "yi5"}:
        return "yi1"
    if character == "不" and reading in {"bu2", "bu4", "bu5"}:
        return "bu4"
    return reading


@lru_cache(maxsize=1)
def _phrase_lengths() -> tuple[int, ...]:
    return tuple(sorted({len(word) for word in phrases_dict} | {2}, reverse=True))


@lru_cache(maxsize=4096)
def character_options(character: str) -> tuple[str, ...]:
    return tuple(
        pinyin(character, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)[0]
    )


def _quantity_follows(text: str, start: int) -> bool:
    end = start
    while end < len(text) and text[end] in DIGITS:
        end += 1
    return end > start and end < len(text) and text[end] in YI_QUANTITY_FOLLOWERS


@lru_cache(maxsize=2048)
def resolve_run(text: str) -> tuple[tuple[str | None, ReadingSource, tuple[str, ...]], ...]:
    """One entry per Han character; cache immutable values only, not user evidence."""
    result: list[tuple[str | None, ReadingSource, tuple[str, ...]]] = []
    index = 0
    while index < len(text):
        phrase: list[list[str]] | None = None
        for size in _phrase_lengths():
            if size < 2 or size > len(text) - index:
                continue
            word = text[index : index + size]
            if word in SUPPLEMENT:
                phrase = [[value] for value in SUPPLEMENT[word]]
            elif word in phrases_dict:
                phrase = phrases_dict[word]
            if phrase is not None and len(phrase) == size:
                break
            phrase = None
        if phrase is not None:
            for phrase_offset, group in enumerate(phrase):
                options = tuple(
                    dict.fromkeys(
                        citation_reading(
                            text[index + phrase_offset],
                            to_tone3(value, neutral_tone_with_five=True),
                        )
                        for value in group
                    )
                )
                result.append(
                    (
                        options[0] if len(options) == 1 else None,
                        "phrase" if len(options) == 1 else "unresolved",
                        options,
                    )
                )
            index += len(phrase)
            continue
        character = text[index]
        options = character_options(character)
        selected: str | None
        source: ReadingSource
        # End of a Han clause, with preceding lexical material. Lexical 吧 in 酒吧
        # has already been consumed by longest-match lookup. Bare 吧 stays ambiguous.
        if character == "吧" and index == len(text) - 1 and index > 0:
            selected, source = "ba5", "grammar"
        elif character == "们" and index > 0 and text[index - 1] in "我你他她它咱您人友学师孩":
            selected, source = "men5", "grammar"
        elif character == "要" and _quantity_follows(text, index + 1):
            # Want/need a quantity: yào. Longest phrase lookup above still owns
            # 要求/要挟; bare 要 and other unresolved uses keep their alternatives.
            selected, source = "yao4", "grammar"
        else:
            selected = DOMINANT.get(character) or (options[0] if len(options) == 1 else None)
            source = "dictionary" if selected else "unresolved"
        result.append((selected, source, options))
        index += 1
    return tuple(result)
