"""Build a quarantined Phase-A packet from a bounded official THCHS archive prefix.

No training permission is inferred from successful parsing. The downloaded
alignment's `transcription` tier is synthetic timing and is never consumed.
"""

import argparse
import hashlib
import html
import io
import math
import re
import sys
import tarfile
import wave
import zipfile
from collections import Counter
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.audio import prepare_windows
from perceptual_tone.common import digest, file_hash, read_json, write_json, write_rows
from perceptual_tone.manifest import verify_baseline
from perceptual_tone.native_labels import CLASSES, HAN, labels, t3_groups
from perceptual_tone.native_protocol import speaker_partition, validate_split

VERSION = "thchs-single-han-word-audit-v2"
INTERVAL = re.compile(
    r'intervals \[\d+\]:\s*xmin = ([\d.eE+-]+)\s*xmax = ([\d.eE+-]+)\s*text = "(.*?)"', re.S
)


def word_intervals(text):
    tiers = re.split(r"item \[\d+\]:", text)[1:]
    words = [t for t in tiers if re.search(r'name\s*=\s*"words"', t)]
    if len(words) != 1:
        raise ValueError("Require one actual words tier")
    result = [(float(a), float(b), s) for a, b, s in INTERVAL.findall(words[0])]
    if not result or any(
        not math.isfinite(a) or not math.isfinite(b) or a < 0 or b <= a for a, b, _ in result
    ):
        raise ValueError("Invalid word intervals")
    if any(b > c + 1e-6 for (_, b, _), (c, _, _) in pairwise(result)):
        raise ValueError("Overlapping words")
    return result


def extract_prefix(prefix, output):
    """Save only complete regular WAV members; do not extract paths or links."""
    rows = []
    (output / "audio").mkdir()
    complete_archive = True
    try:
        with tarfile.open(prefix, mode="r|gz") as archive:
            for member in archive:
                if not member.isfile() or not re.fullmatch(
                    r"data_thchs30/(train|dev|test)/[A-D]\d+_\d+\.wav", member.name
                ):
                    continue
                content = archive.extractfile(member).read()
                if len(content) != member.size:
                    break
                with wave.open(io.BytesIO(content)) as wav:
                    if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (
                        1,
                        2,
                        16000,
                    ):
                        raise ValueError("Unexpected source format")
                    count = wav.getnframes()
                    pcm = wav.readframes(count)
                if len(pcm) != count * 2:
                    raise ValueError("Incomplete PCM")
                path = output / "audio" / Path(member.name).name
                with path.open("xb") as stream:
                    stream.write(content)
                uid = path.stem
                # Conservative alias grouping: A/B/C/D are text groups. Keep
                # every matching numeric speaker suffix together, even if this
                # merges different people. Never inflate speaker counts with it.
                speaker_group = str(int(uid.split("_")[0][1:]))
                rows.append(
                    {
                        "utterance_id": uid,
                        "speaker_id": "thchs-group-" + speaker_group,
                        "released_speaker_id": uid.split("_")[0],
                        "prompt_id": uid.split("_")[1],
                        "duration": count / 16000,
                        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
                        "audio": {
                            "reference": str(path.resolve()),
                            "sha256": file_hash(path),
                            "sample_rate_hz": 16000,
                        },
                        "archive_member": member.name,
                    }
                )
    except (EOFError, tarfile.ReadError):
        complete_archive = False
    return rows, complete_archive


def build(prefix, grids, metadata, output, config):
    baseline = verify_baseline()
    meta = read_json(metadata)
    expected = next(f for f in meta["files"] if f["key"] == "grids.zip")
    if hashlib.md5(grids.read_bytes()).hexdigest() != expected["checksum"].split(":")[1]:
        raise ValueError("Published alignment checksum mismatch")
    if meta["metadata"]["license"]["id"] != "mit-license":
        raise ValueError("Alignment license changed")
    output.mkdir(parents=True, exist_ok=False)
    utterances, complete = extract_prefix(prefix, output)
    partitions = speaker_partition([u["speaker_id"] for u in utterances], config["seed"])
    # Repeated read prompts are not permitted across partitions either. Assign
    # prompt ownership using a label-independent hash; quarantine other readings.
    prompt_partitions = {}
    for u in utterances:
        prompt_partitions.setdefault(u["prompt_id"], set()).add(partitions[u["speaker_id"]])
    prompt_owners = {
        p: sorted(v, key=lambda s: digest([config["seed"], p, s]))[0]
        for p, v in prompt_partitions.items()
    }
    rows, quarantine, texts = [], [], []
    with zipfile.ZipFile(grids) as archive:
        for u in utterances:
            raw = archive.read(f"data/{u['utterance_id']}.TextGrid")
            words = word_intervals(raw.decode())
            unsupported_text = bool(
                re.search(
                    r"[^\u3400-\u9fff\s，。！？、；：,.!?;:‘’“”\"'（）()—…-]",  # noqa: RUF001
                    "".join(s for _, _, s in words),
                )
            )
            # Zenodo adds punctuation; it is not an original prosodic annotation.
            # Derive labels without those invented internal phrase boundaries.
            transcript = "".join(HAN.findall("".join(s for _, _, s in words)))
            text, derived = labels(transcript)
            texts.append(
                {**u, "transcript": text, "alignment_sha256": hashlib.sha256(raw).hexdigest()}
            )
            i = 0
            for start, end, word in words:
                characters = HAN.findall(word)
                for _ in characters:
                    label = derived[i]
                    i += 1
                    row = {
                        **u,
                        **label,
                        "example_id": f"thchs30:{u['utterance_id']}:{i - 1}",
                        "corpus": "THCHS-30/OpenSLR18",
                        "transcript": text,
                        "partition": partitions[u["speaker_id"]],
                        "alignment": {
                            "source": "zenodo:7528596/grids.zip",
                            "version": "MFA-2.0.5/mandarin_mfa-2.0.0a",
                            "tier": "words",
                            "confidence": None,
                            "sha256": hashlib.sha256(raw).hexdigest(),
                            "word": word,
                            "word_start": start,
                            "word_end": end,
                        },
                        "transcript_provenance": (
                            "reconstructed_from_MIT_alignment_words_not_original_trn"
                        ),
                        "phrase_position_provenance": (
                            "utterance_position_only_not_verified_prosody"
                        ),
                        "t3_groups": [
                            g.replace("phrase_", "utterance_")
                            + ("_proxy" if g.startswith("phrase_") else "")
                            for g in t3_groups(label)
                        ],
                    }
                    reasons = []
                    if unsupported_text:
                        reasons.append("unsupported_transcript_content")
                    if len(characters) != 1:
                        reasons.append("multi_han_word_no_verified_syllable_boundary")
                    if label["exclusion"]:
                        reasons.append(label["exclusion"])
                    if end > u["duration"] + 1 / 16000 or not 0.06 <= end - start <= 0.8:
                        reasons.append("alignment_bounds_or_duration")
                    if prompt_owners[u["prompt_id"]] != row["partition"]:
                        reasons.append("repeated_prompt_in_other_partition")
                    if reasons:
                        quarantine.append({**row, "exclusion_reasons": reasons})
                        continue
                    row.update(
                        target={
                            "syllable_index": i - 1,
                            "syllable": label["hanzi"],
                            "start_seconds": start,
                            "end_seconds": end,
                        },
                        context_window={"start_seconds": 0, "end_seconds": u["duration"]},
                    )
                    rows.append(row)
    rows = prepare_windows(rows, config["windows"], output / "windows")
    counts = validate_split(rows)
    write_rows(output / "utterances.jsonl", texts)
    write_rows(output / "candidates.jsonl", rows)
    write_rows(output / "quarantine.jsonl", quarantine)
    write_json(output / "speaker-split.json", partitions)
    # This is a developer QA packet; no acceptability or perceptual tone labels.
    review = []
    for tone in CLASSES:
        choices = sorted(
            [r for r in rows if r["label"] == tone and r["partition"] == "train"],
            key=lambda r: digest([config["seed"], r["example_id"]]),
        )
        review.extend(choices[: config["review_per_class"]])
    template = [
        {
            "example_id": r["example_id"],
            "transcript_matches_audio": None,
            "correct_syllable_boundary": None,
            "linguistic_label_plausible": None,
            "sandhi_neutral_checked": None,
            "notes": "",
        }
        for r in review
    ]
    write_rows(output / "review.template.jsonl", template)
    parts = [
        '<!doctype html><meta charset="utf-8"><title>Native-tone pipeline QA</title>',
        "<h1>Pipeline QA — not perceptual annotation</h1>"
        "<p>Training speakers only. Every item remains unreviewed. "
        "Listen to full speech and target/context; verify transcript, "
        "ownership, and linguistic rule.</p>",
    ]
    for r in review:
        parts.append(
            f"<h2>{html.escape(r['example_id'])}: "
            f"{html.escape(r['hanzi'])} / {r['label']}</h2>"
            f"<p>{html.escape(r['transcript'])}<br>"
            f"{html.escape(r['pinyin'])}; {r['rule']}; "
            f"{r['target']['start_seconds']}&ndash;{r['target']['end_seconds']} s</p>"
        )
        for title, reference in [
            ("Utterance", r["audio"]["reference"]),
            ("Target", r["windows"]["target"]["reference"]),
            ("Context", r["windows"]["wide"]["reference"]),
        ]:
            rel = Path(reference).relative_to(output.resolve())
            parts.append(
                f'<p>{title}<audio controls preload="none" '
                f'src="{html.escape(str(rel))}"></audio></p>'
            )
    (output / "review.html").write_text("\n".join(parts))
    report = {
        "status": "QUARANTINED_NOT_TRAINING_READY",
        "implementation": VERSION,
        "baseline": baseline,
        "config": config,
        "source_prefix_sha256": file_hash(prefix),
        "source_prefix_bytes": prefix.stat().st_size,
        "whole_archive_downloaded": complete,
        "alignment_zip_sha256": file_hash(grids),
        "alignment_license": "MIT",
        "source_license": "Apache-2.0",
        "utterances": len(utterances),
        "released_speaker_ids": sorted({u["released_speaker_id"] for u in utterances}),
        "conservative_speaker_groups": len(partitions),
        "speaker_identity_audit": "unresolved_group_aliases",
        "syllables_total": len(rows) + len(quarantine),
        "candidate_syllables": len(rows),
        "quarantined_syllables": len(quarantine),
        "exclusions": dict(
            Counter(reason for r in quarantine for reason in r["exclusion_reasons"])
        ),
        "candidate_tone_counts": dict(Counter(r["label"] for r in rows)),
        "candidate_split_counts": counts,
        "candidate_t3_groups": dict(Counter(g for r in rows for g in r["t3_groups"])),
        "review_items": len(review),
        "review_completed": 0,
        "training_size": 0,
        "test_evaluated": 0,
        "manifest_sha256": file_hash(output / "candidates.jsonl"),
        "gates": {
            "original_transcript_verified": False,
            "speaker_aliases_verified": False,
            "syllable_alignment_audited": False,
            "developer_audio_qa_complete": False,
        },
    }
    write_json(output / "preflight.json", report)
    print(__import__("json").dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--grids", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "configs/native-tone.json",
    )
    args = parser.parse_args()
    build(args.prefix, args.grids, args.metadata, args.output, read_json(args.config))
