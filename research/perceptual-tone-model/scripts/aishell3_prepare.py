"""Prepare the bounded AISHELL-3 pilot. No classifier training or automatic QA pass."""

import argparse
import json
import sys
import wave
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.aishell3 import (
    VERSION,
    alignment_token,
    attach_prosody,
    custom_lexicon,
    extract_prefix,
    g2p_spelling,
    parse_content,
    parse_dictionary,
    parse_prosody,
    parse_speakers,
    resolve_speaker,
)
from perceptual_tone.common import (
    PACKAGE,
    digest,
    file_hash,
    read_json,
    read_rows,
    write_json,
    write_rows,
)
from perceptual_tone.manifest import verify_baseline


def prepare(root, config):
    source = root / "source"
    extracted = root / "extracted"
    inventory = extract_prefix(
        [source / "official-prefix-4MiB.tgz", source / "official-bytes-4-16MiB.bin"], extracted
    )
    if inventory["prefix_bytes"] != config["source_prefix_bytes"]:
        raise ValueError("Unexpected source prefix size")
    inventory.update(
        source_url=config["official_archive_url"],
        corpus=config["corpus"],
        license="Apache-2.0",
        upstream_full_checksum_verified=False,
    )
    write_json(root / "acquisition.json", inventory)
    metadata = extracted / "spk-info.txt"
    registry = parse_speakers(
        metadata.read_text(),
        {
            "source_url": config["official_archive_url"],
            "member": "spk-info.txt",
            "sha256": file_hash(metadata),
            "prefix_sha256": inventory["prefix_sha256"],
        },
    )
    transcript_path = extracted / "test/content.txt"
    transcript_hash = file_hash(transcript_path)
    transcripts, parse_errors = {}, []
    for line_number, line in enumerate(transcript_path.read_text().splitlines(), 1):
        try:
            u = parse_content(line)
        except ValueError as error:
            parse_errors.append({"line": line_number, "reason": str(error)})
            continue
        if u["utterance_id"] in transcripts:
            raise ValueError("duplicate_utterance_transcript")
        u["transcript_provenance"] = {
            "member": "test/content.txt",
            "line": line_number,
            "sha256": transcript_hash,
        }
        transcripts[u["utterance_id"]] = u
    prosody, prosody_errors = {}, []
    for line_number, line in enumerate(
        (source / "hf-label_train-set.txt").read_text().splitlines(), 1
    ):
        if not line.strip() or line.startswith("#"):
            continue
        try:
            p = parse_prosody(line)
            if p["utterance_id"] in prosody:
                raise ValueError("duplicate_prosody_id")
            prosody[p["utterance_id"]] = p
        except ValueError as error:
            prosody_errors.append({"line": line_number, "reason": str(error)})
    utterances, exclusions = [], []
    for member in inventory["members"]:
        if not member["member"].endswith(".wav"):
            continue
        uid = Path(member["member"]).stem
        if uid not in transcripts:
            exclusions.append({"utterance_id": uid, "reason": "missing_transcript"})
            continue
        u = transcripts[uid]
        try:
            resolve_speaker(u, member["member"], registry)
        except ValueError as error:
            exclusions.append({"utterance_id": uid, "reason": str(error)})
            continue
        # Prosody is auxiliary: conflicts are recorded, never used to relabel.
        prosody_status = "not_in_train_prosody_file"
        if uid in prosody:
            try:
                u = attach_prosody(u, prosody[uid])
                prosody_status = "exact_content_match"
            except ValueError:
                prosody_status = "content_mismatch_not_attached"
        utterances.append(
            {
                **u,
                "corpus": config["corpus"],
                "archive_member": member["member"],
                "source_partition": "test",
                "partition": "pilot_qa",
                "prosody_status": prosody_status,
                "audio": {
                    "reference": str((extracted / member["member"]).resolve()),
                    "sha256": member["sha256"],
                    "sample_rate_hz": 44100,
                },
                "pcm_sha256": member["pcm_sha256"],
                "duration": member["duration"],
            }
        )
    # Cover every acquired speaker, then round-robin. Longer connected utterances
    # come first; hash breaks ties. No tone or model performance is used to select.
    groups = defaultdict(list)
    for u in utterances:
        groups[u["speaker_id"]].append(u)
    for values in groups.values():
        values.sort(key=lambda u: (-len(u["units"]), digest([config["seed"], u["utterance_id"]])))
    ordered_speakers = sorted(groups, key=lambda s: digest([config["seed"], s]))
    selected, depth = [], 0
    while len(selected) < config["pilot_utterances"]:
        added = 0
        for speaker in ordered_speakers:
            if depth < len(groups[speaker]) and len(selected) < config["pilot_utterances"]:
                selected.append(groups[speaker][depth])
                added += 1
        if not added:
            raise ValueError("not_enough_pilot_utterances")
        depth += 1
    pilot = root / "pilot"
    pilot.mkdir(exist_ok=False)
    if len({u["speaker_id"] for u in selected}) < 4:
        raise ValueError("Pilot requires four verified speakers")
    for u in selected:
        folder = pilot / "corpus" / u["speaker_id"]
        folder.mkdir(parents=True, exist_ok=True)
        with wave.open(u["audio"]["reference"], "rb") as original:
            params, pcm = original.getparams(), original.readframes(original.getnframes())
        with wave.open(str(folder / u["filename"]), "wb") as canonical:
            canonical.setparams(params)
            canonical.writeframes(pcm)
        u["alignment_audio"] = {
            "reference": str((folder / u["filename"]).resolve()),
            "sha256": file_hash(folder / u["filename"]),
            "pcm_sha256": u["pcm_sha256"],
            "conversion": "container_rewrite_only_original_pcm44100",
        }
        (folder / (u["utterance_id"] + ".lab")).write_text(
            " ".join(alignment_token(unit) for unit in u["units"]) + "\n"
        )
    pinyin = sorted({u["corpus_pinyin"] for r in selected for u in r["units"]})
    spellings = {p: g2p_spelling(p) for p in pinyin}
    (pilot / "pinyin.txt").write_text("\n".join(sorted(set(spellings.values()))) + "\n")
    write_json(pilot / "g2p-spelling.json", spellings)
    selected_ids = {u["speaker_id"] for u in selected}
    for speaker in registry.values():
        speaker.update(
            acquired_utterances=len(groups[speaker["speaker_id"]]),
            corpus_source_partitions=["test"] if groups[speaker["speaker_id"]] else [],
            partition="pilot_qa" if speaker["speaker_id"] in selected_ids else "unassigned",
        )
    write_rows(root / "speaker-registry.jsonl", [registry[s] for s in sorted(registry)])
    write_rows(root / "utterances.jsonl", utterances)
    write_rows(root / "source-exclusions.jsonl", exclusions)
    write_rows(pilot / "utterances.jsonl", selected)
    write_json(
        root / "format-audit.json",
        {
            "parser": VERSION,
            "transcript_rows": len(transcripts),
            "parse_errors": parse_errors,
            "prosody_rows": len(prosody),
            "prosody_parse_errors": prosody_errors,
            "prosody_status_acquired": dict(Counter(u["prosody_status"] for u in utterances)),
            "acquired_speakers": sorted(groups.keys() & {u["speaker_id"] for u in utterances}),
            "acquired_utterances": len(utterances),
            "acquired_read_units": sum(len(u["units"]) for u in utterances),
            "pilot_utterances": len(selected),
            "pilot_speakers": sorted(selected_ids),
            "pilot_read_units": sum(len(u["units"]) for u in selected),
            "baseline": verify_baseline(),
        },
    )
    print(
        json.dumps(
            {
                "utterances": len(selected),
                "speakers": len(selected_ids),
                "read_units": sum(len(u["units"]) for u in selected),
            }
        )
    )


def lexicon(root, stage="pilot"):
    pilot = root / stage
    models = PACKAGE / ".cache/mfa-work/pretrained_models"
    acoustic = models / "acoustic/mandarin_mfa.zip"
    with zipfile.ZipFile(acoustic) as archive:
        meta = json.loads(archive.read("mandarin_mfa/meta.json"))
    generated = parse_dictionary((pilot / "pinyin.dict").read_text())
    spellings = read_json(pilot / "g2p-spelling.json")
    pronunciations = {p: generated[s] for p, s in spellings.items() if s in generated}
    reused = []
    if stage == "expansion":
        validated = read_json(root / "pilot/lexicon-audit.json")
        for token, pinyin in validated["mapping"].items():
            if pinyin in spellings:
                pronunciations[pinyin] = validated["pronunciations"][token]
                reused.append(pinyin)
    stock_path = models / "dictionary/mandarin_china_mfa.dict"
    stock = parse_dictionary(stock_path.read_text())
    overrides = read_json(PACKAGE / "configs/aishell3-pronunciations.json")["entries"]
    applied = {}
    for pinyin, spec in overrides.items():
        if pinyin not in spellings:
            continue
        if tuple(spec["source_phones"]) not in stock.get(spec["source_word"], []):
            raise ValueError("Pronunciation source does not match pinned dictionary")
        applied[pinyin] = {
            **spec,
            "rejected_g2p_phones": generated.get(spellings[pinyin]),
            "source_dictionary_sha256": file_hash(stock_path),
        }
        pronunciations[pinyin] = [tuple(spec["phones"])]
    utterances = read_rows(pilot / "utterances.jsonl")
    entries, mapping, oovs = custom_lexicon(utterances, pronunciations, meta["phones"])
    write_json(
        pilot / "lexicon-audit.json",
        {
            "oovs": oovs,
            "mapping": mapping,
            "pronunciations": entries,
            "generated_pinyin_dictionary_sha256": file_hash(pilot / "pinyin.dict"),
            "reused_validated_pilot_pronunciations": sorted(reused),
            "stock_dictionary_supported_overrides": applied,
            "acoustic_metadata": meta,
            "models": {
                str(p.relative_to(models)): {"sha256": file_hash(p), "bytes": p.stat().st_size}
                for p in models.rglob("*")
                if p.is_file() and p.suffix in {".zip", ".dict"}
            },
        },
    )
    if oovs:
        raise ValueError("Unresolved OOVs: " + ", ".join(oovs))
    with (pilot / "read-units.dict").open("x") as out:
        for word in sorted(entries):
            for phones in entries[word]:
                out.write(word + "\t" + " ".join(phones) + "\n")
    print(json.dumps({"alignment_tokens": len(entries), "oovs": len(oovs)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "lexicon"])
    parser.add_argument("--root", type=Path, default=PACKAGE / "data/generated/aishell3")
    parser.add_argument("--stage", default="pilot", choices=["pilot", "expansion"])
    args = parser.parse_args()
    config = read_json(PACKAGE / "configs/aishell3.json")
    if args.action == "prepare":
        prepare(args.root, config)
    else:
        lexicon(args.root, args.stage)
