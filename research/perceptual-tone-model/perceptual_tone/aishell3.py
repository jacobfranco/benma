"""AISHELL-3 v1.0 read units, source identity, and fail-closed research contracts.

The corpus pronunciation supplies the label. No Hanzi-to-pinyin conversion or
Benma tone rule is used here. MFA supplies timing only.
"""

import hashlib
import io
import re
import tarfile
import wave
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path, PurePosixPath

from .common import digest, file_hash

VERSION = "aishell3-read-units-v1"
UTTERANCE = re.compile(r"SSB\d{8}")
PINYIN = re.compile(r"([a-zv]+)([1-5])")
HAN = re.compile(r"[\u3400-\u9fff]+")
SILENCE = {"", "sil", "sp"}
TONE_CLASSES = ("T1", "T2", "T3", "T4", "T5")


def pinyin_token(token):
    match = PINYIN.fullmatch(token)
    if not match:
        raise ValueError("invalid_corpus_pinyin")
    base, tone = match.groups()
    return {
        "corpus_pinyin": token,
        "phonetic_base": base,
        "corpus_tone": int(tone),
        "label": "T" + tone,
        "erhua": base.endswith("r") and base != "er",
    }


def strip_tone(token):
    return pinyin_token(token)["phonetic_base"]


def parse_content(line):
    fields = line.split()
    if len(fields) < 3 or (len(fields) - 1) % 2:
        raise ValueError("invalid_read_unit_pairs")
    filename = fields[0]
    uid = filename.removesuffix(".wav")
    if filename != uid + ".wav" or not UTTERANCE.fullmatch(uid):
        raise ValueError("invalid_utterance_id")
    units = []
    for i, (hanzi, pinyin) in enumerate(zip(fields[1::2], fields[2::2], strict=True)):
        unit = pinyin_token(pinyin)
        # Preserve ALL corpus pairs, including atypical multi-Hanzi annotations.
        # Flag them for QA instead of changing the corpus read-unit sequence.
        if not HAN.fullmatch(hanzi):
            raise ValueError("unsupported_hanzi_read_unit")
        units.append(
            {
                **unit,
                "index": i,
                "hanzi": hanzi,
                "lexical_tone": None,
                "unusual_multi_hanzi": len(hanzi) > 1
                and not (len(hanzi) == 2 and hanzi.endswith("儿") and unit["erhua"]),
                "lexical_tone_provenance": "not_derived",
                "prosody_after": None,
            }
        )
    return {
        "utterance_id": uid,
        "speaker_id": uid[:7],
        "filename": filename,
        "transcript": "".join(u["hanzi"] for u in units),
        "units": units,
    }


def parse_speakers(text, provenance):
    registry = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 4:
            raise ValueError("invalid_speaker_metadata")
        speaker, age, gender, accent = fields
        if (
            not re.fullmatch(r"SSB\d{4}", speaker)
            or speaker in registry
            or age not in {"A", "B", "C", "D"}
            or gender not in {"male", "female"}
            or accent not in {"north", "south", "others"}
        ):
            raise ValueError("invalid_or_duplicate_speaker")
        registry[speaker] = {
            "speaker_id": speaker,
            "age_group": age,
            "gender": gender,
            "accent": accent,
            "metadata_line": line_number,
            "metadata_provenance": provenance,
            "partition": "unassigned",
        }
    return registry


def resolve_speaker(utterance, audio_member, registry):
    path = PurePosixPath(audio_member)
    parts = path.parts
    if (
        len(parts) != 4
        or parts[0] not in {"train", "test"}
        or parts[1] != "wav"
        or parts[2] != utterance["speaker_id"]
        or parts[3] != utterance["filename"]
        or utterance["speaker_id"] not in registry
    ):
        raise ValueError("unverified_speaker_or_audio_id")
    return registry[utterance["speaker_id"]]


def parse_prosody(line):
    fields = line.strip().split("|")
    if len(fields) != 3 or not UTTERANCE.fullmatch(fields[0]):
        raise ValueError("invalid_prosody_line")
    units = []
    for part in fields[1].split():
        if part in {"%", "$"}:
            if not units or units[-1]["prosody_after"]:
                raise ValueError("unattached_prosody_marker")
            units[-1]["prosody_after"] = part
        else:
            units.append({**pinyin_token(part), "prosody_after": None})
    if not units:
        raise ValueError("empty_prosody")
    hanzi = fields[2].replace("%", "").replace("$", "")
    if not HAN.fullmatch(hanzi):
        raise ValueError("unsupported_prosody_text")
    offset, boundaries = 0, []
    for character in fields[2]:
        if character in {"%", "$"}:
            boundaries.append((offset, character))
        else:
            offset += 1
    return {
        "utterance_id": fields[0],
        "units": units,
        "transcript": hanzi,
        "hanzi_boundaries": boundaries,
    }


def attach_prosody(utterance, prosody):
    if (
        utterance["utterance_id"] != prosody["utterance_id"]
        or utterance["transcript"] != prosody["transcript"]
        or [u["corpus_pinyin"] for u in utterance["units"]]
        != [u["corpus_pinyin"] for u in prosody["units"]]
    ):
        raise ValueError("prosody_content_mismatch")
    offset, boundaries = 0, []
    for u, p in zip(utterance["units"], prosody["units"], strict=True):
        offset += len(u["hanzi"])
        if p["prosody_after"]:
            boundaries.append((offset, p["prosody_after"]))
    if boundaries != prosody["hanzi_boundaries"]:
        raise ValueError("prosody_boundary_read_unit_mismatch")
    return {
        **utterance,
        "units": [
            {**u, "prosody_after": p["prosody_after"]}
            for u, p in zip(utterance["units"], prosody["units"], strict=True)
        ],
    }


def checked_wav(raw):
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("invalid_wav_header")
    # Several original release WAVs have stale outer RIFF sizes. Independently
    # traverse every chunk and verify its actual payload; do not trust the decoder
    # alone, which can silently accept a short data chunk. No samples are repaired.
    offset, data_chunks = 12, 0
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError("truncated_chunk_header")
        size = int.from_bytes(raw[offset + 4 : offset + 8], "little")
        if offset + 8 + size > len(raw):
            raise ValueError("truncated_chunk_payload")
        data_chunks += raw[offset : offset + 4] == b"data"
        offset += 8 + size + size % 2
    if offset != len(raw) or data_chunks != 1:
        raise ValueError("invalid_wav_chunks")
    with wave.open(io.BytesIO(raw)) as w:
        if (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) != (
            1,
            2,
            44100,
            "NONE",
        ):
            raise ValueError("unexpected_corpus_audio_format")
        frames = w.getnframes()
        pcm = w.readframes(frames)
    if not frames or len(pcm) != frames * 2:
        raise ValueError("truncated_pcm")
    return {
        "frames": frames,
        "sample_rate_hz": 44100,
        "duration": frames / 44100,
        "container_warning": (
            "stale_riff_size_complete_chunks"
            if int.from_bytes(raw[4:8], "little") + 8 != len(raw)
            else None
        ),
        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
    }


def g2p_spelling(token):
    """Orthographic tone conversion only; never derives a reading from Hanzi."""
    from pypinyin.contrib.tone_convert import to_tone

    pinyin_token(token)
    return to_tone(token)


def extract_prefix(chunks, destination):
    """Read a contiguous gzip prefix FROM BYTE ZERO; never seek inside deflate.

    Tar headers are checksum-validated by tarfile. Only complete regular members
    with a whitelisted path are written. The unavailable gzip footer is explicit.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    raw = b"".join(Path(p).read_bytes() for p in chunks)
    if raw[:2] != b"\x1f\x8b":
        raise ValueError("not_gzip_from_byte_zero")
    members, failures, tail, last = [], [], None, None
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r|gz") as archive:
            for member in archive:
                last = member.name
                if not member.isfile():
                    continue
                allowed = member.name in {
                    "ChangeLog",
                    "phone_set.txt",
                    "ReadMe.txt",
                    "spk-info.txt",
                }
                allowed |= bool(re.fullmatch(r"(?:train|test)/content\.txt", member.name))
                allowed |= bool(
                    re.fullmatch(r"(?:train|test)/wav/SSB\d{4}/SSB\d{8}\.wav", member.name)
                )
                if not allowed:
                    continue
                content = archive.extractfile(member).read()
                if len(content) != member.size:
                    raise EOFError("incomplete_member")
                info = {}
                if member.name.endswith(".wav"):
                    try:
                        info = checked_wav(content)
                    except ValueError as error:
                        failures.append({"member": member.name, "reason": str(error)})
                        continue
                path = destination / member.name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                members.append(
                    {
                        "member": member.name,
                        "bytes": len(content),
                        "sha256": file_hash(path),
                        **info,
                    }
                )
    except (EOFError, tarfile.ReadError) as error:
        tail = {"member": last, "reason": type(error).__name__}
    return {
        "format": "gzip-compressed tar",
        "prefix_bytes": len(raw),
        "prefix_sha256": hashlib.sha256(raw).hexdigest(),
        "gzip_footer_verified": False,
        "incomplete_tail": tail,
        "members": members,
        "corrupt_members": failures,
        "chunks": [
            {"name": Path(p).name, "bytes": Path(p).stat().st_size, "sha256": file_hash(p)}
            for p in chunks
        ],
    }


def alignment_token(unit):
    # ASCII letters only so tokenizer punctuation/digit handling cannot split it.
    # This is an alignment identifier, NEVER a model input feature.
    parsed = pinyin_token(unit["corpus_pinyin"])
    return "ais" + parsed["phonetic_base"] + "tone" + "abcde"[parsed["corpus_tone"] - 1]


def parse_dictionary(text):
    entries = defaultdict(set)
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        i = 1
        while i < len(fields) and re.fullmatch(r"[0-9.]+", fields[i]):
            i += 1  # MFA optional pronunciation/silence probabilities
        if i == len(fields):
            raise ValueError("empty_dictionary_pronunciation")
        entries[fields[0]].add(tuple(fields[i:]))
    return {word: sorted(phones) for word, phones in entries.items()}


def custom_lexicon(utterances, pronunciations, phone_inventory):
    entries, mapping, oovs = {}, {}, set()
    for utterance in utterances:
        for unit in utterance["units"]:
            token = alignment_token(unit)
            pinyin = unit["corpus_pinyin"]
            variants = pronunciations.get(pinyin)
            if not variants:
                oovs.add(pinyin)
                continue
            for phones in variants:
                if (
                    not phones
                    or not set(phones) <= set(phone_inventory)
                    or set(phones) & {"sil", "spn"}
                ):
                    raise ValueError("incompatible_or_missing_phones")
                contours = ["".join(re.findall("[˥˦˧˨˩]", phone)) for phone in phones]
                contours = [c for c in contours if c]
                expected = {1: "˥", 2: "˧˥", 3: "˨˩˦", 4: "˥˩", 5: None}[unit["corpus_tone"]]
                if contours != ([expected] if expected else []):
                    raise ValueError("g2p_tone_disagrees_with_corpus")
            entries[token] = variants
            mapping[token] = pinyin
    return entries, mapping, sorted(oovs)


def speaker_split(speakers, seed=20261015):
    speakers = sorted(set(speakers), key=lambda s: digest([seed, s]))
    if len(speakers) < 8:
        raise ValueError("at_least_eight_verified_speakers_required")
    held = max(1, round(len(speakers) * 0.2))
    return {
        s: "test" if i < held else "validation" if i < held * 2 else "train"
        for i, s in enumerate(speakers)
    }


def size_balanced_speaker_split(unit_counts, seed=20261015):
    """Fixed speaker quotas and nearest 60/20/20 unit totals; no labels or metrics.

    This bounded recovered subset has at most 16 speakers. Exhaustively compare
    disjoint held-out groups, then hash-break equal size errors. Freeze before ML.
    """
    speakers = sorted(unit_counts)
    if not 8 <= len(speakers) <= 16 or any(v <= 0 for v in unit_counts.values()):
        raise ValueError("size_balancer_requires_8_to_16_nonempty_speakers")
    held = max(1, round(len(speakers) * 0.2))
    groups = [(g, set(g), sum(unit_counts[s] for s in g)) for g in combinations(speakers, held)]
    total = sum(unit_counts.values())
    best, choices = None, []
    for test, test_set, n_test in groups:
        for validation, validation_set, n_validation in groups:
            if test_set & validation_set:
                continue
            error = (
                (5 * n_test - total) ** 2
                + (5 * n_validation - total) ** 2
                + (5 * (total - n_test - n_validation) - 3 * total) ** 2
            )
            if best is None or error < best:
                best, choices = error, [(test, validation)]
            elif error == best:
                choices.append((test, validation))
    test, validation = min(choices, key=lambda value: digest([seed, value]))
    return {
        s: "test" if s in test else "validation" if s in validation else "train" for s in speakers
    }


def verify_split(rows):
    owners = {key: {} for key in ("speaker_id", "utterance_id", "pcm_sha256")}
    ids = set()
    for row in rows:
        if row["partition"] not in {"train", "validation", "test"}:
            raise ValueError("unassigned_partition")
        if row["example_id"] in ids:
            raise ValueError("duplicate_example")
        ids.add(row["example_id"])
        for key, table in owners.items():
            value = row[key]
            if not value or table.get(value, row["partition"]) != row["partition"]:
                raise ValueError("split_leakage_" + key)
            table[value] = row["partition"]


def t3_contexts(rows):
    counts = Counter({f"before_T{i}": 0 for i in range(1, 6)})
    counts.update(
        {
            "utterance_final": 0,
            "utterance_medial": 0,
            "phrase_final": 0,
            "phrase_medial": 0,
            "phrase_position_unknown": 0,
        }
    )
    for row in rows:
        if row["corpus_tone"] != 3:
            continue
        following = row.get("following")
        counts["utterance_medial" if following else "utterance_final"] += 1
        if following:
            counts[f"before_T{following['corpus_tone']}"] += 1
        if row.get("prosody_available"):
            counts["phrase_final" if row["prosody_after"] in {"%", "$"} else "phrase_medial"] += 1
        elif not following:
            counts["phrase_final"] += 1  # utterance end is a phrase endpoint
        else:
            counts["phrase_position_unknown"] += 1
    return dict(counts)


def audio_only_request(row):
    """Allowlisted request used to construct features; label mutations cannot enter."""
    return {
        "audio": {k: row["audio"][k] for k in ("reference", "sha256", "sample_rate_hz")},
        "start_seconds": row["start"],
        "end_seconds": row["end"],
    }


def quality_gate(rows, registry, reviews, *, stage):
    if stage not in {"pilot", "dataset"}:
        raise ValueError("invalid_gate_stage")
    blockers = []
    ids = {r["example_id"]: r for r in rows}
    speakers = {r["speaker_id"] for r in rows}
    if len(speakers) < (4 if stage == "pilot" else 8) or not speakers <= registry.keys():
        blockers.append("speaker_provenance_or_count")
    if any(r.get("reconstruction_status") != "candidate" for r in rows):
        blockers.append("reconstruction_not_clean")
    audited = Counter()
    seen = set()
    for review in reviews:
        key = review["example_id"]
        if key not in ids or key in seen:
            raise ValueError("unknown_or_duplicate_review")
        seen.add(key)
        if review.get("item_sha256") != digest(ids[key]):
            raise ValueError("review_not_bound_to_current_item")
        if review.get("decision") not in {
            "PASS",
            "BOUNDARY EARLY",
            "BOUNDARY LATE",
            "WRONG UNIT",
            "AUDIO/TRANSCRIPT MISMATCH",
            "OTHER",
        }:
            raise ValueError("missing_or_invalid_playback_decision")
        if review["decision"] != "PASS":
            blockers.append("developer_qa_rejected_item")
        if (
            review.get("reviewer")
            and review.get("reviewed_at")
            and review.get("heard_context_and_target") is True
            and review["decision"] == "PASS"
        ):
            audited[ids[key]["label"]] += 1
    minimum = 5
    if any(audited[t] < minimum for t in TONE_CLASSES[:4]):
        blockers.append("developer_audio_qa_incomplete")
    if any(r["label"] == "T5" for r in rows) and audited["T5"] < min(
        minimum, sum(r["label"] == "T5" for r in rows)
    ):
        blockers.append("neutral_sample_qa_incomplete")
    if stage == "dataset":
        verify_split(rows)
        if len(rows) < 500:
            blockers.append("fewer_than_500_units")
        for partition in ("train", "validation", "test"):
            counts = Counter(r["label"] for r in rows if r["partition"] == partition)
            minimum_count = 20 if partition == "test" else 10
            if any(counts[t] < minimum_count for t in TONE_CLASSES[:4]):
                blockers.append("core_class_coverage_" + partition)
    blockers = sorted(set(blockers))
    return {"passed": not blockers, "blockers": blockers, "audited_by_tone": dict(audited)}
