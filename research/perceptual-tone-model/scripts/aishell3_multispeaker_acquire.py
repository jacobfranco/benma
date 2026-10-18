"""Bounded, pinned, speaker-first acquisition; the historical pilot is read-only."""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import wave
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json, stable_rows
from perceptual_tone.aishell3 import (
    alignment_token,
    checked_wav,
    g2p_spelling,
    parse_content,
    parse_speakers,
    resolve_speaker,
)
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows
from perceptual_tone.manifest import verify_baseline

ROOT = PACKAGE / "data/generated/aishell3-multispeaker-v2"
OLD = PACKAGE / "data/generated/aishell3"
CONFIG = PACKAGE / "configs/aishell3-multispeaker.json"
PILOT_MANIFEST = "8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f"


def preserve(root):
    """Hash all historical corpus, models, predictions, QA and reports before work."""
    snapshot = root / "historical-preservation.json"
    if snapshot.exists():
        evidence = read_json(snapshot)
        for name, expected_hash in evidence.items():
            if file_hash(PACKAGE / name) != expected_hash:
                raise ValueError("historical_evidence_changed:" + name)
        verify_baseline()
        return {
            "historical_files": len(evidence),
            "pilot_manifest_sha256": PILOT_MANIFEST,
        }
    paths = [OLD, PACKAGE / "models/generated/aishell3-first-four-tone-v1"]
    paths += list((PACKAGE / "reports").glob("aishell3*"))
    paths += list(PACKAGE.glob("aishell3*.md"))
    files = sorted(
        {
            p
            for base in paths
            for p in ([base] if base.is_file() else base.rglob("*"))
            if p.is_file()
        }
    )
    evidence = {str(p.relative_to(PACKAGE)): file_hash(p) for p in files}
    stable_json(root / "historical-preservation.json", evidence)
    expected = "8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f"
    old_release = OLD / "releases/aishell3-nucleus-coda-context-v1-20261017/manifest.jsonl"
    if file_hash(old_release) != expected:
        raise ValueError("historical_pilot_manifest_changed")
    verify_baseline()
    return {"historical_files": len(evidence), "pilot_manifest_sha256": expected}


def plan(root, config):
    preservation = preserve(root)
    source = root / "source"
    registry_file = source / "spk-info.txt"
    if file_hash(registry_file) != file_hash(OLD / "extracted/spk-info.txt"):
        raise ValueError("publisher_speaker_registry_differs_from_official")
    overlap = source / "overlap-SSB00050353.wav"
    if file_hash(overlap) != file_hash(OLD / "extracted/test/wav/SSB0005/SSB00050353.wav"):
        raise ValueError("publisher_overlap_audio_differs_from_official")
    registry = parse_speakers(
        registry_file.read_text(),
        {
            "source_repository": config["source_repository"],
            "revision": config["source_revision"],
            "member": "spk-info.txt",
            "sha256": file_hash(registry_file),
            "official_metadata_exact_match": True,
        },
    )
    metadata = read_json(OLD / "source/hf-metadata.json")
    if metadata["sha"] != config["source_revision"]:
        raise ValueError("source_revision_mismatch")
    available = {s["rfilename"] for s in metadata["siblings"]}
    pilot_speakers = {r["speaker_id"] for r in read_rows(OLD / "utterances.jsonl")}
    grouped, seen = defaultdict(list), set()
    transcript = source / "train-content.txt"
    transcript_hash = file_hash(transcript)
    for line, text in enumerate(transcript.read_text().splitlines(), 1):
        u = parse_content(text)  # Unexpected syntax fails closed, no silent row skipping.
        if u["utterance_id"] in seen:
            raise ValueError("duplicate_transcript")
        seen.add(u["utterance_id"])
        member = f"train/wav/{u['speaker_id']}/{u['filename']}"
        if member not in available or u["speaker_id"] in pilot_speakers:
            continue
        resolve_speaker(u, member, registry)
        if any(x["unusual_multi_hanzi"] for x in u["units"]):
            continue  # Same manual-review exclusion as the existing parser/reconstructor.
        u.update(
            archive_member=member,
            transcript_provenance={
                "member": "train/content.txt",
                "line": line,
                "sha256": transcript_hash,
                "source_repository": config["source_repository"],
                "revision": config["source_revision"],
            },
        )
        grouped[u["speaker_id"]].append(u)
    grouped = {
        s: [u for u in values if 4 <= len(u["units"]) <= 24] for s, values in grouped.items()
    }
    available_counts = {
        s: Counter(x["label"] for u in values for x in u["units"]) for s, values in grouped.items()
    }
    eligible = [
        s
        for s, c in available_counts.items()
        if sum(c[t] for t in ("T1", "T2", "T3", "T4"))
        >= config["numbered_units_per_speaker_target"]
        and c["T3"] >= config["minimum_t3_per_speaker_before_alignment"]
        and all(c[t] >= 6 for t in ("T1", "T2", "T4"))
    ]
    speakers = sorted(eligible, key=lambda s: digest([config["seed"], "new-speakers", s]))[
        : config["speakers"]
    ]
    if len(speakers) != config["speakers"]:
        raise ValueError("insufficient_new_verified_speakers")
    selected = []
    for speaker in speakers:
        remaining = list(grouped[speaker])
        counts = Counter()
        while (
            sum(counts[t] for t in ("T1", "T2", "T3", "T4"))
            < config["numbered_units_per_speaker_target"]
            or counts["T3"] < config["minimum_t3_per_speaker_before_alignment"]
            or any(counts[t] < 6 for t in ("T1", "T2", "T4"))
        ):
            if not remaining:
                raise ValueError("speaker_coverage_unavailable:" + speaker)
            deficits = {
                t: max(
                    0,
                    (config["minimum_t3_per_speaker_before_alignment"] if t == "T3" else 6)
                    - counts[t],
                )
                for t in ("T1", "T2", "T3", "T4")
            }

            def rank(u, deficits=deficits):
                tones = Counter(x["label"] for x in u["units"])
                # Choose useful connected utterances, bounded at 24 read units.
                return (
                    -sum(min(tones[t], deficits[t]) for t in deficits),
                    -min(20, sum(tones[t] for t in deficits)),
                    digest([config["seed"], u["utterance_id"]]),
                )

            choices = [u for u in remaining if 4 <= len(u["units"]) <= 24]
            u = min(choices, key=rank)
            selected.append(u)
            counts.update(x["label"] for x in u["units"])
            remaining.remove(u)
    stable_rows(root / "selection.jsonl", selected)
    stable_rows(root / "speaker-registry.jsonl", [registry[s] for s in sorted(speakers)])
    summary = {
        "config_sha256": file_hash(CONFIG),
        "preservation": preservation,
        "source_repository": config["source_repository"],
        "revision": config["source_revision"],
        "source_listing_sha256": file_hash(OLD / "source/hf-metadata.json"),
        "metadata": {
            p.name: {"bytes": p.stat().st_size, "sha256": file_hash(p)}
            for p in (transcript, registry_file, overlap)
        },
        "parsed_transcripts": len(seen),
        "parse_errors": 0,
        "insufficient_available_speaker_coverage": sorted(set(grouped) - set(eligible)),
        "speakers": sorted(speakers),
        "excluded_all_pilot_speakers": sorted(pilot_speakers),
        "utterances": len(selected),
        "units": sum(len(u["units"]) for u in selected),
        "tones": dict(Counter(x["label"] for u in selected for x in u["units"])),
        "selection_sha256": file_hash(root / "selection.jsonl"),
        "selection_before_split_freeze": True,
        "maximum_source_bytes": config["maximum_source_bytes"],
    }
    stable_json(root / "acquisition-plan.json", summary)
    return summary


def acquire(root, config):
    selected = read_rows(root / "selection.jsonl")
    if (
        file_hash(root / "selection.jsonl")
        != read_json(root / "acquisition-plan.json")["selection_sha256"]
    ):
        raise ValueError("acquisition_plan_changed")
    # Hard request bound: at most 1 MB per selected file, maximum 300 MB in total.
    limit = min(1000000, config["maximum_source_bytes"] // len(selected))

    def fetch(u):
        member = u["archive_member"]
        url = f"https://huggingface.co/datasets/{config['source_repository']}/resolve/{config['source_revision']}/{member}"
        path = root / "extracted" / member
        receipt = path.with_suffix(".receipt.json")
        if path.exists():
            record = read_json(receipt)
            if record["sha256"] != file_hash(path):
                raise ValueError("source_audio_changed")
            return record
        with urllib.request.urlopen(url, timeout=90) as response:
            raw = response.read(limit + 1)
            headers = {
                k: response.headers.get(k) for k in ("ETag", "Content-Length", "Last-Modified")
            }
        if len(raw) > limit:
            raise ValueError("bounded_download_limit:" + member)
        info = checked_wav(raw)
        record = {
            "member": member,
            "url": url,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "headers": headers,
            **info,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        stable_json(receipt, record)
        return record

    with ThreadPoolExecutor(max_workers=6) as pool:
        members = list(pool.map(fetch, selected))
    summary = {
        "members": members,
        "audio_bytes": sum(r["bytes"] for r in members),
        "utterances": len(members),
        "speakers": sorted({u["speaker_id"] for u in selected}),
        "source_repository": config["source_repository"],
        "revision": config["source_revision"],
        "license": "Apache-2.0",
        "official_full_archive_checksum_verified": False,
        "provenance": (
            "Publisher mirror at pinned revision; registry and overlap audio match retained "
            "official bytes."
        ),
    }
    stable_json(root / "acquisition.json", summary)
    return {k: v for k, v in summary.items() if k != "members"}


def prepare(root):
    selected = read_rows(root / "selection.jsonl")
    acquisition = read_json(root / "acquisition.json")
    members = {m["member"]: m for m in acquisition["members"]}
    transcript = root / "extracted/train/content.txt"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    if not transcript.exists():
        shutil.copyfile(root / "source/train-content.txt", transcript)
    stage = root / "expansion"
    utterances = []
    for u in selected:
        path = root / "extracted" / u["archive_member"]
        m = members[u["archive_member"]]
        if file_hash(path) != m["sha256"]:
            raise ValueError("acquired_source_changed")
        canonical = stage / "corpus-expansion" / u["speaker_id"] / u["filename"]
        canonical.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path)) as w:
            params, pcm = w.getparams(), w.readframes(w.getnframes())
        if not canonical.exists():
            with wave.open(str(canonical), "wb") as w:
                w.setparams(params)
                w.writeframes(pcm)
        if checked_wav(canonical.read_bytes())["pcm_sha256"] != m["pcm_sha256"]:
            raise ValueError("canonical_pcm_mismatch")
        lab = canonical.with_suffix(".lab")
        text = " ".join(alignment_token(x) for x in u["units"]) + "\n"
        if lab.exists() and lab.read_text() != text:
            raise ValueError("alignment_transcript_changed")
        if not lab.exists():
            lab.write_text(text)
        utterances.append(
            {
                **u,
                "corpus": "AISHELL-3/OpenSLR93/v1.0",
                "source_partition": "train",
                "partition": "unassigned",
                "prosody_status": "preserved_separately_for_reporting",
                "audio": {"reference": str(path), "sha256": m["sha256"], "sample_rate_hz": 44100},
                "pcm_sha256": m["pcm_sha256"],
                "duration": m["duration"],
                "alignment_audio": {
                    "reference": str(canonical),
                    "sha256": file_hash(canonical),
                    "pcm_sha256": m["pcm_sha256"],
                    "conversion": "container_rewrite_only_original_pcm44100",
                },
            }
        )
    stable_rows(stage / "utterances.jsonl", utterances)
    spellings = {
        p: g2p_spelling(p)
        for p in sorted({x["corpus_pinyin"] for u in selected for x in u["units"]})
    }
    stable_json(stage / "g2p-spelling.json", spellings)
    path = stage / "pinyin.txt"
    text = "\n".join(sorted(set(spellings.values()))) + "\n"
    if path.exists() and path.read_text() != text:
        raise ValueError("pinyin_input_changed")
    if not path.exists():
        path.write_text(text)
    # Reuse the existing lexicon builder's validated-pronunciation lookup verbatim.
    pilot = root / "pilot"
    pilot.mkdir(exist_ok=True)
    target = pilot / "lexicon-audit.json"
    if not target.exists():
        shutil.copyfile(OLD / "pilot/lexicon-audit.json", target)
    return {"utterances": len(utterances), "pinyin_tokens": len(spellings)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "acquire", "prepare", "verify-history"])
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    config = read_json(CONFIG)
    result = {
        "plan": lambda: plan(args.root, config),
        "acquire": lambda: acquire(args.root, config),
        "prepare": lambda: prepare(args.root),
        "verify-history": lambda: preserve(args.root),
    }[args.action]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
