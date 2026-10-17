"""Strict MFA long-TextGrid ingestion and phone-owned read-unit reconstruction."""

import math
import re
from itertools import pairwise

from .aishell3 import SILENCE, alignment_token

NUMBER = r"[-+\d.eE]+"
INTERVAL = re.compile(
    rf'intervals \[\d+\]:\s*xmin = ({NUMBER})\s*xmax = ({NUMBER})\s*text = "((?:[^"]|"")*)"',
    re.S,
)


def textgrid(text):
    if 'Object class = "TextGrid"' not in text:
        raise ValueError("not_long_textgrid")
    blocks = re.split(r"\bitem \[\d+\]:", text)
    tiers = {}
    for block in blocks[1:]:
        name = re.search(r'name\s*=\s*"([^"]+)"', block)
        size = re.search(r"intervals: size\s*=\s*(\d+)", block)
        if not name or not size or 'class = "IntervalTier"' not in block:
            raise ValueError("invalid_textgrid_tier")
        if name[1] in tiers:
            raise ValueError("duplicate_textgrid_tier")
        values = [
            (float(a), float(b), label.replace('""', '"'))
            for a, b, label in INTERVAL.findall(block)
        ]
        if len(values) != int(size[1]):
            raise ValueError("textgrid_interval_count_mismatch")
        if any(
            not math.isfinite(a) or not math.isfinite(b) or a < 0 or b <= a for a, b, _ in values
        ):
            raise ValueError("invalid_textgrid_interval")
        if any(b > c + 1e-6 for (_, b, _), (c, _, _) in pairwise(values)):
            raise ValueError("overlapping_textgrid_intervals")
        tiers[name[1]] = values
    if set(tiers) != {"words", "phones"}:
        raise ValueError("require_exact_word_and_phone_tiers")
    return tiers


def reconstruct(utterance, tiers, lexicon, diagnostics, config):
    units = utterance["units"]
    words = [(a, b, t) for a, b, t in tiers["words"] if t not in SILENCE]
    phones = tiers["phones"]
    tolerance = config["timing_tolerance_seconds"]
    global_reasons = []
    if [t for _, _, t in words] != [alignment_token(u) for u in units]:
        global_reasons.append("alignment_token_sequence_mismatch")
    if any(
        a < 0 or b > utterance["duration"] + tolerance
        for tier in tiers.values()
        for a, b, _ in tier
    ):
        global_reasons.append("alignment_outside_audio")
    likelihood = diagnostics.get("alignment_log_likelihood")
    if likelihood is None or not math.isfinite(likelihood):
        global_reasons.append("missing_alignment_diagnostics")
    elif likelihood < config["minimum_alignment_log_likelihood"]:
        global_reasons.append("extreme_alignment_log_likelihood")
    # Every speech phone must belong to exactly one word. No proportional split.
    for a, b, phone in phones:
        if phone in SILENCE:
            continue
        owners = [w for w in words if a >= w[0] - tolerance and b <= w[1] + tolerance]
        if len(owners) != 1:
            global_reasons.append("orphan_or_crossing_phone")
            break
    results = []
    for i, unit in enumerate(units):
        row = {
            "example_id": f"aishell3:{utterance['utterance_id']}:{i}",
            "corpus": utterance["corpus"],
            "utterance_id": utterance["utterance_id"],
            "speaker_id": utterance["speaker_id"],
            "partition": utterance["partition"],
            "source_partition": utterance["source_partition"],
            "audio": utterance["audio"],
            "pcm_sha256": utterance["pcm_sha256"],
            "duration": utterance["duration"],
            "transcript": utterance["transcript"],
            "transcript_provenance": utterance["transcript_provenance"],
            **unit,
            "preceding": units[i - 1] if i else None,
            "following": units[i + 1] if i + 1 < len(units) else None,
            "prosody_available": utterance["prosody_status"] == "exact_content_match",
            "aligned_phones": [],
            "start": None,
            "end": None,
            "alignment_diagnostics": diagnostics,
            "confidence": None,
            "exclusion_reasons": list(global_reasons),
        }
        if unit.get("unusual_multi_hanzi"):
            row["exclusion_reasons"].append("atypical_multi_hanzi_requires_audio_review")
        if not global_reasons:
            a, b, token = words[i]
            contained = [
                (x, y, phone) for x, y, phone in phones if x >= a - tolerance and y <= b + tolerance
            ]
            speech = [(x, y, phone) for x, y, phone in contained if phone not in SILENCE]
            row.update(
                start=a,
                end=b,
                aligned_phones=[{"start": x, "end": y, "phone": phone} for x, y, phone in speech],
            )
            expected = lexicon.get(token, [])
            actual = tuple(phone for _, _, phone in speech)
            if not expected:
                row["exclusion_reasons"].append("oov_read_unit")
            if not actual:
                row["exclusion_reasons"].append("required_phones_missing")
            elif actual not in {tuple(v) for v in expected}:
                row["exclusion_reasons"].append("phone_pronunciation_mismatch")
            if any(phone in SILENCE for _, _, phone in contained):
                row["exclusion_reasons"].append("silence_inside_read_unit")
            if speech and (
                abs(speech[0][0] - a) > tolerance
                or abs(speech[-1][1] - b) > tolerance
                or any(abs(y - x) > tolerance for (_, y, _), (x, _, _) in pairwise(speech))
            ):
                row["exclusion_reasons"].append("incomplete_phone_ownership")
            if not config["duration_min_seconds"] <= b - a <= config["duration_max_seconds"]:
                row["exclusion_reasons"].append("implausible_read_unit_duration")
            if any(y - x > config["max_phone_duration_seconds"] for x, y, _ in speech):
                row["exclusion_reasons"].append("extreme_phone_duration")
            floor = sum(y - x <= config["phone_floor_seconds"] for x, y, _ in speech)
            if speech and floor / len(speech) > config["max_floor_phone_fraction"]:
                row["exclusion_reasons"].append("collapsed_phone_durations")
        row["reconstruction_status"] = "rejected" if row["exclusion_reasons"] else "candidate"
        results.append(row)
    return results
