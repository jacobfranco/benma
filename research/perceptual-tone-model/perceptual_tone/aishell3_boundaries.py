"""Research-only span proposals. Never edit MFA evidence or training targets.

One shared, nearest-sample boundary defines adjacent half-open PCM intervals.
The experimental nucleus+coda projection uses the pinned MFA phone inventory,
not a tone digit, example ID, human verdict, energy threshold or fixed padding.
"""

import math
from decimal import ROUND_HALF_UP, Decimal

from .common import digest

TONES = str.maketrans("", "", "˥˦˧˨˩")
NUCLEI = frozenset(("a", "e", "i", "o", "u", "y", "ə", "aj", "aw", "ej", "ow", "z̩", "ʐ̩"))
CODAS = frozenset(("n", "ŋ", "ɻ"))
GLIDES = frozenset(("j", "w", "ɥ"))
STOPS = frozenset(("p", "pʰ", "pʲ", "pʷ", "t", "tʰ", "tʲ", "tʷ", "k", "kʰ", "kʷ"))
AFFRICATES = frozenset(("ts", "tsʰ", "tɕ", "tɕʰ", "tɕʷ", "ʈʂ", "ʈʂʰ"))
FRICATIVES = frozenset(("f", "s", "x", "xʷ", "ɕ", "ɕʷ", "ʂ", "ʐ"))
SONORANTS = frozenset(("m", "mʲ", "n", "ɲ", "l", "ʎ", "ɻ"))
ONSETS = STOPS | AFFRICATES | FRICATIVES | SONORANTS | {"ʔ"}  # noqa: RUF001 - IPA
POLICY = "nearest_sample_half_open_and_owned_nucleus_coda_v1"


def sample_index(seconds, rate):
    if not math.isfinite(seconds) or seconds < 0 or not isinstance(rate, int) or rate <= 0:
        raise ValueError("invalid_sample_time")
    return int((Decimal(str(seconds)) * rate).to_integral_value(rounding=ROUND_HALF_UP))


def span(start, end, rate, frames):
    if not 0 <= start < end <= frames / rate:
        raise ValueError("invalid_source_span")
    first, last = sample_index(start, rate), sample_index(end, rate)
    if not 0 <= first < last <= frames:
        raise ValueError("collapsed_or_outside_sample_span")
    return {
        "start_sample": first,
        "end_sample": last,
        "sample_rate_hz": rate,
        "start_seconds": first / rate,
        "end_seconds": last / rate,
        "endpoint_convention": "half_open",
    }


def phone_structure(row):
    phones = row["aligned_phones"]
    if not phones or phones[0]["start"] != row["start"] or phones[-1]["end"] != row["end"]:
        raise ValueError("phone_coverage_mismatch")
    for i, phone in enumerate(phones):
        if not math.isfinite(phone["start"]) or not math.isfinite(phone["end"]):
            raise ValueError("nonfinite_phone")
        if phone["end"] <= phone["start"] or (i and phones[i - 1]["end"] != phone["start"]):
            raise ValueError("phone_gap_or_overlap")
    bases = [p["phone"].translate(TONES) for p in phones]
    nuclei = [i for i, p in enumerate(bases) if p in NUCLEI]
    if len(nuclei) != 1:
        raise ValueError("require_one_unsplit_nucleus_phone")
    index = nuclei[0]
    prefix, suffix = bases[:index], bases[index + 1 :]
    # Optional consonant and optional medial; never guess an unknown role.
    if prefix and prefix[0] in ONSETS:
        prefix = prefix[1:]
    if prefix and prefix[0] in GLIDES:
        prefix = prefix[1:]
    if prefix or len(suffix) > 1 or any(p not in CODAS for p in suffix):
        raise ValueError("unsupported_phone_structure")
    return index, bases


def derive(row, rate, frames):
    full = span(row["start"], row["end"], rate, frames)
    context = span(max(0, row["start"] - 0.25), min(frames / rate, row["end"] + 0.25), rate, frames)
    common = {
        "example_id": row["example_id"],
        "original_row_sha256": digest(row),
        "policy": POLICY,
        "original_mfa_phones": row["aligned_phones"],
        "linguistic_read_unit": {"start": row["start"], "end": row["end"]},
        "playback_read_unit": full,
        "context": context,
        "ml_target_changed": False,
        "eligible_for_training": False,
    }
    try:
        index, bases = phone_structure(row)
        first = row["aligned_phones"][index]["start"]
        final = span(first, row["end"], rate, frames)
    except ValueError as error:
        return {
            **common,
            "tone_bearing_pooling_span": None,
            "available": False,
            "reason": str(error),
            "owned_phone_indices": [],
            "flags": ["unavailable"],
        }
    if (
        not full["start_sample"]
        <= final["start_sample"]
        < final["end_sample"]
        == full["end_sample"]
    ):
        raise ValueError("projection_crosses_owner")
    return {
        **common,
        "tone_bearing_pooling_span": final,
        "available": True,
        "owned_phone_indices": list(range(index, len(bases))),
        "reason": "first_vowel_or_syllabic_nucleus_through_owned_coda_no_medial_no_padding",
        "ml_target_changed": False,
        "eligible_for_training": False,
        "flags": ["experimental_final_under_60ms"]
        if final["end_sample"] - final["start_sample"] < sample_index(0.06, rate)
        else [],
    }


def features(row):
    index, bases = phone_structure(row)
    p = bases[0]
    initial = (
        "plosive"
        if p in STOPS
        else "affricate"
        if p in AFFRICATES
        else "fricative"
        if p in FRICATIVES
        else "sonorant"
        if p in SONORANTS
        else "zero_or_glide"
    )
    return {
        "initial_class": initial,
        "nucleus": bases[index],
        "final_class": "diphthong"
        if bases[index] in {"aj", "aw", "ej", "ow"}
        else "nasal"
        if bases[-1] in {"n", "ŋ"}
        else "rhotic"
        if bases[-1] == "ɻ"
        else "open",
        "previous_final": row["preceding"]["corpus_pinyin"] if row["preceding"] else None,
        "next_initial": row["following"]["corpus_pinyin"] if row["following"] else None,
        "duration": row["end"] - row["start"],
    }


def control_matches(failure, passes):
    """Rank every original PASS using structure, duration and speaker; no tone matching."""
    f = features(failure)
    matches = []
    for control in passes:
        c = features(control)
        criteria = {
            "same_initial_class": f["initial_class"] == c["initial_class"],
            "same_final_class": f["final_class"] == c["final_class"],
            "same_nucleus": f["nucleus"] == c["nucleus"],
            "same_speaker": failure["speaker_id"] == control["speaker_id"],
            "similar_duration_within_80ms": abs(f["duration"] - c["duration"]) <= 0.08,
        }
        score = sum(
            criteria[k] * weight for k, weight in zip(criteria, (4, 3, 3, 2, 1), strict=True)
        )
        matches.append(
            {
                "example_id": control["example_id"],
                "criteria": criteria,
                "score": score,
                "duration_difference_seconds": abs(f["duration"] - c["duration"]),
            }
        )
    return sorted(
        matches, key=lambda m: (-m["score"], m["duration_difference_seconds"], m["example_id"])
    )
