"""Experiment 2 metadata-only selection, bounded acquisition and immutable sealing.

No model imports, feature extraction, predictions, listening or fitting. Run with
services/api/.venv/bin/python; existing pypinyin 0.55.0 and ffmpeg are required.
"""

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import re
import subprocess
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from pilot import diagnostics, field, normalize, parse_pinyin, wikitext

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/pronunciation-v2/2026-09-30-experiment-2-preflight"
CACHE = ROOT / "benchmark/corpus/recordings/original/experiment-2-preflight"
OLD = Path.home() / ".cache/benma/benma-pronunciation-v2-pilot"
PREVIOUS = ROOT / "docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec"
REVISION = "c3aaa9e892e4b1c2a25b637401f52f6e35b53e74"
OMPAL = f"https://raw.githubusercontent.com/phantomhsieh/OMPAL-corpus/{REVISION}/"
BLOCKED_IDS = {
    "shtooka:wei-gao",
    "lingualibre:Q1431140",
    "lingualibre:Q1573006",
    "lingualibre:Q301531",
    "commons:wyverald",
    "lingualibre:Q1832",
    "lingualibre:Q1845",
    "shtooka:yue-tan",
}
BLOCKED_NAMES = {
    "weigao",
    "canonni",
    "levihighway",
    "luilui6666",
    "xudongyang",
    "wyverald",
    "wangcheng",
    "junda",
    "yuetan",
}
FIELDS = (
    "source",
    "source_asset_id",
    "speaker_id",
    "speaker_name",
    "speaker_native_status",
    "native_status_evidence",
    "speaker_identity_confidence",
    "source_url",
    "audio_url",
    "revision_id",
    "text",
    "pinyin",
    "tone",
    "label_source",
    "license",
    "license_url",
    "license_evidence_url",
    "attribution",
    "source_bytes",
    "source_sha1",
    "local_path",
    "audio_sha256",
    "decoded_pcm_sha256",
    "duration_seconds",
    "sample_rate_hz",
    "channels",
    "metadata_status",
    "selection_status",
    "exclusions",
)
ACQUIRED_FIELDS = (
    "local_path",
    "audio_sha256",
    "decoded_pcm_sha256",
    "duration_seconds",
    "sample_rate_hz",
    "channels",
)


def temporal_bin_boundaries(valid_frames: int) -> tuple[int, int, int, int]:
    """Executable protocol reference only; never loads audio or encoder features."""
    if type(valid_frames) is not int or valid_frames < 3:
        raise ValueError("At least three valid frames are required for both arms")
    return 0, valid_frames // 3, (2 * valid_frames) // 3, valid_frames


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def csv_bytes(rows, fields=FIELDS):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in sorted(rows, key=lambda r: (str(r["speaker_id"]), r["source_asset_id"])):
        writer.writerow({key: row.get(key, "") for key in fields})
    return stream.getvalue().encode("utf-8")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def name_key(value):
    return re.sub(r"[\W_]", "", value.casefold())


def blocked(row):
    return row["speaker_id"] in BLOCKED_IDS or name_key(row["speaker_name"]) in BLOCKED_NAMES


def commons_row(page, allow_sharealike):
    record, reasons = normalize(page)
    wiki = wikitext(page)
    meta = page["imageinfo"][0]["extmetadata"]
    # A deliberately separate evaluation policy; never relax the training policy.
    if (
        allow_sharealike
        and "sharealike_deferred" in reasons
        and record["api_license"] == "CC BY-SA 4.0"
        and meta.get("LicenseUrl", {}).get("value", "").rstrip("/")
        == "https://creativecommons.org/licenses/by-sa/4.0"
        and re.search(r"\{\{cc-by-sa-4\.0\s*\}\}", wiki, re.I)
    ):
        reasons.remove("sharealike_deferred")
        record["license"] = "CC BY-SA 4.0"
        record["license_url"] = "https://creativecommons.org/licenses/by-sa/4.0/"
        record["attribution"] = (
            f"{record['title']}; {record['author']}; {record['source_url']}; "
            f"{record['license_url']}; original audio unchanged"
        )
    row = {key: record.get(key) or "" for key in FIELDS}
    if blocked(row):
        reasons.append("previous_experiment_speaker_or_audited_singleton")
    if record["source_collection"] == "Lingua Libre":
        # Cross-check template identity/text against the independent filename fields.
        expected = f"-{row['speaker_name']}-{row['text']}."
        if expected not in page["title"]:
            reasons.append("filename_template_conflict")
        if field(wiki, "languageId") not in ("Q9192", "Q727694"):
            reasons.append("mandarin_not_explicit")
    elif not blocked(row):
        reasons.append("non_lingualibre_identity_requires_individual_audit")
    row["metadata_status"] = "eligible" if not reasons else "excluded"
    row["exclusions"] = "|".join(sorted(set(reasons)))
    return row


def choose(rows):
    """Only audited metadata fields are accessed; extra/prediction fields ignored.

    Speakers with >=8 eligible targets in EACH tone; up to 10 per tone ranked by
    SHA256(source_asset_id UTF-8), then ID. Scarce cells are retained in full.
    """
    cells = defaultdict(list)
    for row in rows:
        if row["metadata_status"] == "eligible" and not blocked(row):
            if str(row["tone"]) not in {"1", "2", "3", "4"}:
                raise ValueError("Only tones 1-4")
            cells[row["speaker_id"], int(row["tone"])].append(row)
    speakers = {
        speaker
        for speaker, _ in cells
        if all(len(cells.get((speaker, tone), [])) >= 8 for tone in range(1, 5))
    }
    selected = set()
    for (speaker, _), items in list(cells.items()):
        if speaker in speakers:
            items = sorted(
                items,
                key=lambda r: (
                    hashlib.sha256(r["source_asset_id"].encode()).hexdigest(),
                    r["source_asset_id"],
                ),
            )
            selected.update(r["source_asset_id"] for r in items[:10])
    return selected


def ompal_rows():
    folder = CACHE / "ompal"
    tree = json.loads((folder / "tree.json").read_text())
    if tree["truncated"] or tree["sha"] != REVISION:
        raise ValueError("OMPAL tree is incomplete or not pinned")
    assets = {p["path"]: p for p in tree["tree"]}
    for name in ("README.md", "LICENSE", "native_scores.json"):
        data = (folder / name).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != assets[name]["sha"]:
            raise ValueError(f"OMPAL Git blob mismatch: {name}")
    scores = json.loads((folder / "native_scores.json").read_text())
    rows = []
    for asset, annotation in sorted(scores.items()):
        speaker = "SPEAKER" + asset[1:6]
        path = f"wav/{speaker}/{asset}.wav"
        text = annotation["text"]
        # Deliberately never read annotation tone/accuracy/fluency/prosody scores.
        words = "".join("".join(word["text"]) for word in annotation["words"])
        reasons = ["connected_speech_without_syllable_boundaries"]
        if words != text:
            reasons.append("word_text_transcript_mismatch")
        rows.append(
            {
                **dict.fromkeys(FIELDS, ""),
                "source": "OMPAL",
                "source_asset_id": f"ompal:{asset}",
                "speaker_id": f"ompal:{speaker}",
                "speaker_name": speaker,
                "speaker_native_status": "NATIVE",
                "native_status_evidence": OMPAL + "README.md",
                "speaker_identity_confidence": "corpus_speaker_id_cross_source_alias_unknown",
                "source_url": f"https://github.com/phantomhsieh/OMPAL-corpus/blob/{REVISION}/{path}",
                "audio_url": OMPAL + path,
                "revision_id": REVISION,
                "text": text,
                "label_source": (
                    "No single lexical tone assigned; transcript only; no pinyin/timestamps"
                ),
                "license": "CC BY 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "license_evidence_url": OMPAL + "LICENSE",
                "attribution": f"OMPAL; Hsieh et al., Interspeech 2025; {OMPAL + path}; CC BY 4.0",
                "source_bytes": assets[path]["size"],
                "source_sha1": assets[path]["sha"],
                "metadata_status": "excluded",
                "selection_status": "native_sentence_reserve",
                "exclusions": "|".join(reasons),
            }
        )
    return rows


def prepare(allow_sharealike):
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / "seal.json").exists():
        raise FileExistsError("Already sealed; use a new versioned directory")
    rows = [commons_row(p, allow_sharealike) for p in jsonl(OLD / "candidate-evidence.jsonl")]
    selected = choose(rows)
    for row in rows:
        if row["source_asset_id"] in selected:
            row["selection_status"] = "selected_before_acquisition"
        elif row["metadata_status"] == "eligible":
            row["selection_status"] = "metadata_reserve"
            row["exclusions"] = "outside_fixed_speaker_coverage_or_per_tone_cap"
        else:
            row["selection_status"] = "excluded"
    rows += ompal_rows()
    (OUT / "candidate-items.csv").write_bytes(csv_bytes(rows))
    write_json(
        OUT / "selection.json",
        {
            "allow_sharealike_evaluation_only": allow_sharealike,
            "rule": choose.__doc__,
            "selected_ids": sorted(selected),
            "candidate_items_sha256_before_acquisition": digest(OUT / "candidate-items.csv"),
            "input_evidence_sha256": digest(OLD / "candidate-evidence.jsonl"),
            "blocked_ids": sorted(BLOCKED_IDS),
            "blocked_names": sorted(BLOCKED_NAMES),
            "prediction_access": False,
            "replacement_after_download_failure": False,
        },
    )
    print(f"Prepared {len(rows)} audited items; {len(selected)} selected before acquisition")


def download(row, destination):
    if not destination.exists():
        url = row["audio_url"]
        if not (
            url.startswith("https://upload.wikimedia.org/wikipedia/commons/")
            or url.startswith(OMPAL + "wav/SPEAKER01")
        ):
            raise ValueError("Download outside bounded source allowlist")
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "BenmaPronunciationResearch/0.1 (bounded evaluation corpus audit)"
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(int(row["source_bytes"]) + 1)
        verify_source(row, data)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    data = destination.read_bytes()
    verify_source(row, data)
    return {
        "local_path": str(destination.relative_to(ROOT)),
        "audio_sha256": hashlib.sha256(data).hexdigest(),
        **diagnostics(destination),
    }


def verify_source(row, data):
    check = data
    if row["source"] == "OMPAL":
        check = b"blob " + str(len(data)).encode() + b"\0" + data
    if (
        len(data) != int(row["source_bytes"])
        or hashlib.sha1(check).hexdigest() != row["source_sha1"]
    ):
        raise ValueError("Source size/hash mismatch")


def acquire(source, resume_after_stop=False):
    if (OUT / "seal.json").exists():
        raise FileExistsError("Already sealed")
    # Stop on first network/integrity error; a rerun must not bypass a server cooldown.
    stop_path = CACHE / "acquisition-stop.json"
    stops = 0
    if stop_path.exists():
        stop = json.loads(stop_path.read_text())
        stops = stop.get("stop_count", 1)
        if not resume_after_stop or stops >= 2:
            raise RuntimeError("Prior acquisition stopped; maximum two stop events across resumes")
        # This explicit resume honors the prior Retry-After in full, plus a
        # conservative 60-second minimum. Invalid/non-numeric headers fail closed.
        delay = max(60, int(stop.get("retry_after") or 60))
        write_json(CACHE / "acquisition-stop-1.json", stop)
        print(f"Explicit conservative resume: waiting {delay}s", flush=True)
        time.sleep(delay)
    rows = list(csv.DictReader((OUT / "candidate-items.csv").open()))
    selected = [
        r
        for r in rows
        if (
            r["source"] == "OMPAL"
            if source == "ompal"
            else r["selection_status"] == "selected_before_acquisition"
        )
    ]
    if len(selected) > 202 or sum(int(r["source_bytes"]) for r in selected) > 64 * 1024**2:
        raise ValueError("Bounded acquisition budget exceeded")
    acquired = []
    for row in selected:
        destination = CACHE / source / (row["source_asset_id"].replace(":", "-") + ".wav")
        cached = destination.exists()
        try:
            info = download(row, destination)
            acquired.append({"source_asset_id": row["source_asset_id"], **info})
            print(f"Verified {source} {len(acquired)}/{len(selected)}", flush=True)
        except Exception as exc:
            write_json(
                CACHE / "acquisition-stop.json",
                {
                    "asset": row["source_asset_id"],
                    "error": str(exc),
                    "retry_after": getattr(exc, "headers", {}).get("Retry-After"),
                    "no_automatic_retry": True,
                    "stop_count": stops + 1,
                    "source": source,
                },
            )
            break
        finally:
            write_json(CACHE / f"{source}-acquired.json", acquired)
        if not cached:
            time.sleep(60 if resume_after_stop else 1)


def validate_final(rows, previous):
    required = set(FIELDS) - {"native_status_evidence", "exclusions"}
    seen = defaultdict(set)
    duplicate_keys = ("source_asset_id", "audio_sha256", "source_sha1", "decoded_pcm_sha256")
    old_values = {key: {r[key] for r in previous if r.get(key)} for key in duplicate_keys}
    old_speakers = {r["speaker_id"] for r in previous}
    for row in rows:
        if any(row.get(key) in (None, "") for key in required):
            raise ValueError("Missing required provenance")
        if blocked(row) or row["speaker_id"] in old_speakers:
            raise ValueError("Speaker overlaps prior corpus")
        if row["exclusions"] or row["metadata_status"] != "eligible":
            raise ValueError("Ambiguous/excluded item")
        if str(row["tone"]) not in {"1", "2", "3", "4"}:
            raise ValueError("Only tones 1-4")
        if parse_pinyin(row["pinyin"]) != (row["pinyin"], int(row["tone"])):
            raise ValueError("Pinyin/tone conflict")
        for key in duplicate_keys:
            if row[key] in seen[key] or row[key] in old_values[key]:
                raise ValueError(f"Duplicate {key}")
            seen[key].add(row[key])
        metadata = (row["speaker_id"], row["text"], row["pinyin"])
        if metadata in seen["metadata"]:
            raise ValueError("Duplicate speaker-target metadata")
        seen["metadata"].add(metadata)
        if digest(ROOT / row["local_path"]) != row["audio_sha256"]:
            raise ValueError("Local audio changed")


def verify_decodes(rows):
    """Offline source/hash/decode verification, independent of saved receipts."""
    for row in rows:
        path = ROOT / row["local_path"]
        verify_source(row, path.read_bytes())
        info = diagnostics(path)
        for key in ("decoded_pcm_sha256", "sample_rate_hz", "channels"):
            if str(info[key]) != str(row[key]):
                raise ValueError(f"Re-decoded {key} differs: {row['source_asset_id']}")
        if abs(info["duration_seconds"] - float(row["duration_seconds"])) > 1e-12:
            raise ValueError(f"Re-decoded duration differs: {row['source_asset_id']}")


def check_no_staged_audio():
    names = (
        subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"], cwd=ROOT
        )
        .decode()
        .split("\0")
    )
    if any(
        Path(name).suffix.lower() in {".wav", ".ogg", ".flac", ".mp3", ".opus", ".m4a"}
        for name in names
        if name
    ):
        raise ValueError("Raw audio is staged for Git")


def immutable_write(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise FileExistsError("Refusing to alter sealed artifact")
    else:
        with path.open("xb") as handle:
            handle.write(data)


def summaries(rows, final):
    groups = defaultdict(list)
    for row in rows:
        groups[row["speaker_id"] or "unresolved:" + (row["speaker_name"] or "unnamed")].append(row)
    speakers = []
    final_ids = {r["source_asset_id"] for r in final}
    for speaker, items in sorted(groups.items()):
        first = items[0]
        entry = {
            "source_asset_id": speaker,
            "speaker_id": speaker,
            "speaker_name": first["speaker_name"],
            "source": first["source"],
            "native_status": first["speaker_native_status"],
            "native_status_evidence": first["native_status_evidence"],
            "licenses_accepted_for_evaluation": "|".join(
                sorted({r["license"] for r in items if r["license"]})
            ),
            "source_url": first["source_url"],
            "audited_items": len(items),
            "local_audio_items": sum(bool(r["audio_sha256"]) for r in items),
            "selected_items": sum(
                r["selection_status"] == "selected_before_acquisition" for r in items
            ),
            "sealed_items": sum(r["source_asset_id"] in final_ids for r in items),
            "exclusions": "|".join(
                sorted({reason for r in items for reason in r["exclusions"].split("|") if reason})
            ),
        }
        for tone in range(1, 5):
            entry[f"metadata_eligible_t{tone}"] = sum(
                r["metadata_status"] == "eligible" and str(r["tone"]) == str(tone) for r in items
            )
            entry[f"local_eligible_t{tone}"] = sum(
                r["metadata_status"] == "eligible"
                and str(r["tone"]) == str(tone)
                and bool(r["audio_sha256"])
                for r in items
            )
            entry[f"sealed_t{tone}"] = sum(
                r["source_asset_id"] in final_ids and str(r["tone"]) == str(tone) for r in items
            )
        speakers.append(entry)
    tree = json.loads((CACHE / "ompal/tree.json").read_text())
    learners = Counter(
        p["path"].split("/")[1]
        for p in tree["tree"]
        if p["path"].startswith("wav/SPEAKER02") and p["path"].endswith(".wav")
    )
    for speaker, count in sorted(learners.items()):
        entry = dict.fromkeys(speakers[0], "")
        entry.update(
            source_asset_id="ompal:" + speaker,
            speaker_id="ompal:" + speaker,
            speaker_name=speaker,
            source="OMPAL",
            native_status="LEARNER",
            native_status_evidence=OMPAL + "README.md",
            licenses_accepted_for_evaluation="CC BY 4.0",
            source_url=f"https://github.com/phantomhsieh/OMPAL-corpus/tree/{REVISION}/wav/{speaker}",
            audited_items=0,
            local_audio_items=0,
            selected_items=0,
            sealed_items=0,
            exclusions=f"learner_reserve_not_acquired_or_item_audited; repository_wavs={count}",
        )
        speakers.append(entry)
    (OUT / "candidate-speakers.csv").write_bytes(csv_bytes(speakers, list(speakers[0])))
    inputs = [
        OLD / "candidate-evidence.jsonl",
        OLD / "commons-metadata.jsonl",
        CACHE / "ompal/tree.json",
        CACHE / "ompal/native_scores.json",
        CACHE / "ompal/README.md",
        CACHE / "ompal/LICENSE",
        PREVIOUS / "clean-corpus-manifest.csv",
        PREVIOUS / "split-manifest.csv",
        PREVIOUS / "experiment-config.locked.json",
        ROOT / "benchmark/pronunciation_v2/pilot.py",
        Path(__file__),
        Path(__file__).with_name("test_evaluation_preflight.py"),
    ]
    for name in (
        "ompal-acquired.json",
        "commons-acquired.json",
        "acquisition-stop-1.json",
        "acquisition-stop.json",
    ):
        if (CACHE / name).exists():
            inputs.append(CACHE / name)
    artifacts = {
        p.name: digest(p)
        for p in sorted(OUT.iterdir())
        if p.is_file() and p.name != "provenance.json"
    }
    write_json(
        OUT / "provenance.json",
        {
            "audit_date": "2026-09-30",
            "source_snapshot_date": "2026-09-28",
            "branch": "pronunciation-v2-research",
            "starting_git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "inputs_sha256": {str(p): digest(p) for p in inputs},
            "artifacts_sha256": artifacts,
            "pypinyin_version": importlib.metadata.version("pypinyin"),
            "ompal_revision": REVISION,
            "audio_cache": str(CACHE.relative_to(ROOT)),
            "acquisition_stop": json.loads((CACHE / "acquisition-stop.json").read_text())
            if (CACHE / "acquisition-stop.json").exists()
            else None,
            "acquisition_stop_is_historical_resolved": bool(final),
            "evaluation_only_sharealike_explicitly_authorized": True,
            "counts": {
                "audited_items": len(rows),
                "sealed_items": len(final),
                "downloaded_native_sentences": sum(
                    r["source"] == "OMPAL" and bool(r["audio_sha256"]) for r in rows
                ),
                "downloaded_selected_isolated": sum(
                    r["metadata_status"] == "eligible" and bool(r["audio_sha256"]) for r in rows
                ),
                "learner_speakers_inventory_only": len(learners),
                "learner_wavs_inventory_only": sum(learners.values()),
            },
            "candidate_predictions_opened": False,
            "model_loaded_or_trained": False,
            "audio_listened_or_f0_inspected": False,
            "production_api_mobile_modified": False,
            "selection_depends_on_predictions": False,
            "sealed_test_native_status": "UNKNOWN" if final else "NO_SEALED_TEST",
            "limitations": [
                "public profile identity is not a biological identity guarantee",
                "lexical targets are not observed surface-tone labels",
                "exact hashes do not detect all transformed copies",
                "CC BY-SA evaluation-only policy does not alter training-data policy",
            ],
        },
    )


def seal():
    if (OUT / "seal.json").exists():
        raise FileExistsError("Already finalized; verify existing seal, do not rebuild")
    selection = json.loads((OUT / "selection.json").read_text())
    if (
        digest(OUT / "candidate-items.csv")
        != selection["candidate_items_sha256_before_acquisition"]
    ):
        raise ValueError("Candidate metadata changed since selection")
    rows = list(csv.DictReader((OUT / "candidate-items.csv").open()))
    for source in ("ompal", "commons"):
        path = CACHE / f"{source}-acquired.json"
        acquired = (
            {r["source_asset_id"]: r for r in json.loads(path.read_text())} if path.exists() else {}
        )
        for row in rows:
            if row["source_asset_id"] in acquired:
                row.update(
                    {
                        k: v
                        for k, v in acquired[row["source_asset_id"]].items()
                        if k in ACQUIRED_FIELDS
                    }
                )
    selected = [r for r in rows if r["selection_status"] == "selected_before_acquisition"]
    if sorted(r["source_asset_id"] for r in selected) != selection["selected_ids"]:
        raise ValueError("Selection changed")
    ready = bool(selected) and all(r["audio_sha256"] for r in selected)
    blocker = "" if ready else "Selected set incomplete locally; no partial test sealed"
    if ready:
        previous = list(csv.DictReader((PREVIOUS / "clean-corpus-manifest.csv").open()))
        try:
            if importlib.metadata.version("pypinyin") != "0.55.0":
                raise ValueError("Lexical dictionary version changed")
            if digest(OLD / "candidate-evidence.jsonl") != selection["input_evidence_sha256"]:
                raise ValueError("Source metadata evidence changed")
            validate_final(selected, previous)
            verify_decodes(selected)
            check_no_staged_audio()
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            ready = False
            blocker = str(exc)
    final = selected if ready else []
    if ready:
        ids = {r["source_asset_id"] for r in final}
        pages = [
            p for p in jsonl(OLD / "candidate-evidence.jsonl") if f"commons:{p['pageid']}" in ids
        ]
        evidence = "".join(
            json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n"
            for p in sorted(pages, key=lambda p: p["pageid"])
        )
        immutable_write(OUT / "selected-source-evidence.jsonl", evidence.encode())
    write_json(
        OUT / "integrity.json",
        {
            "status": "PASS" if ready else "BLOCKED",
            "blocker": blocker,
            "selected": len(selected),
            "verified_decodes": len(final),
            "candidate_metadata_unchanged": True,
            "selection_ids_unchanged": True,
            "speaker_disjoint_from_all_previous_corpus_ids": ready,
            "duplicate_source_ids": 0 if ready else None,
            "duplicate_source_sha1": 0 if ready else None,
            "duplicate_audio_sha256": 0 if ready else None,
            "duplicate_decoded_pcm_sha256": 0 if ready else None,
            "duplicate_speaker_target_metadata": 0 if ready else None,
            "source_and_audio_hash_matches": ready,
            "only_unambiguous_lexical_t1_t4": ready,
            "required_provenance_present": ready,
            "no_raw_audio_staged": ready,
            "no_models_or_predictions_used": True,
        },
    )
    data = csv_bytes(final)
    if ready:
        immutable_write(OUT / "sealed-test-manifest.csv", data)
    record = {
        "status": "SEALED" if ready else "BLOCKED_NO_TRUSTWORTHY_COMPLETE_SET",
        "n": len(final),
        "manifest_sha256": hashlib.sha256(data).hexdigest() if ready else None,
        "selection_sha256": digest(OUT / "selection.json"),
        "protocol_sha256": digest(OUT / "protocol.md"),
        "integrity_sha256": digest(OUT / "integrity.json"),
        "sealed_at": datetime.now(UTC).isoformat() if ready else None,
        "manifest_exists": ready,
        "blocker": blocker,
        "prediction_access": False,
        "model_execution": False,
        "tone_counts": dict(sorted(Counter(str(r["tone"]) for r in final).items())),
        "speaker_counts": dict(sorted(Counter(r["speaker_id"] for r in final).items())),
        "speaker_tones": {
            s: dict(sorted(Counter(str(r["tone"]) for r in final if r["speaker_id"] == s).items()))
            for s in sorted({r["speaker_id"] for r in final})
        },
    }
    if ready:
        immutable_write(
            OUT / "seal.json", (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
        )
    write_json(OUT / "preflight-status.json", record)
    # Preserve the original pre-acquisition bytes so the selection lock is recheckable.
    (OUT / "audited-items.csv").write_bytes(csv_bytes(rows))
    excluded = [
        dict(r) for r in rows if r["source_asset_id"] not in {x["source_asset_id"] for x in final}
    ]
    exclusion_fields = (
        "source_asset_id",
        "speaker_id",
        "speaker_name",
        "source_url",
        "text",
        "pinyin",
        "tone",
        "metadata_status",
        "selection_status",
        "exclusions",
    )
    for row in excluded:
        if row["selection_status"] == "selected_before_acquisition" and not row["audio_sha256"]:
            row["exclusions"] = "audio_not_acquired_after_network_stop"
        elif row["selection_status"] == "selected_before_acquisition" and not ready:
            row["exclusions"] = "whole_selected_panel_blocked_no_partial_seal"
    (OUT / "exclusions.csv").write_bytes(csv_bytes(excluded, exclusion_fields))
    summaries(rows, final)
    print(json.dumps(record, indent=2))


def verify():
    if not (OUT / "seal.json").exists():
        raise RuntimeError("No sealed evaluation manifest; acquisition/integrity must finish first")
    record = json.loads((OUT / "seal.json").read_text())
    for name, expected in (
        ("sealed-test-manifest.csv", record["manifest_sha256"]),
        ("selection.json", record["selection_sha256"]),
        ("protocol.md", record["protocol_sha256"]),
        ("integrity.json", record["integrity_sha256"]),
    ):
        if digest(OUT / name) != expected:
            raise ValueError(f"Frozen artifact changed: {name}")
    rows = list(csv.DictReader((OUT / "sealed-test-manifest.csv").open()))
    if len(rows) != record["n"]:
        raise ValueError("Sealed row count mismatch")
    if record["status"] != "SEALED":
        if rows:
            raise ValueError("Blocked seal must be empty")
        raise RuntimeError("Verified blocked placeholder; NOT an evaluation set")
    if not rows:
        raise ValueError("Empty test cannot be sealed")
    previous = list(csv.DictReader((PREVIOUS / "clean-corpus-manifest.csv").open()))
    selection = json.loads((OUT / "selection.json").read_text())
    if (
        digest(OUT / "candidate-items.csv")
        != selection["candidate_items_sha256_before_acquisition"]
    ):
        raise ValueError("Preselection candidate metadata changed")
    if sorted(r["source_asset_id"] for r in rows) != selection["selected_ids"]:
        raise ValueError("Sealed IDs differ from preselection")
    validate_final(rows, previous)
    print(f"Verified immutable seal, local bytes and disjointness for {len(rows)} clips")


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "acquire", "seal", "verify"))
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--allow-sharealike-evaluation-only", action="store_true")
    parser.add_argument("--source", choices=("ompal", "commons"))
    parser.add_argument("--resume-after-stop", action="store_true")
    args = parser.parse_args()
    OUT = args.output.resolve()
    if args.stage == "prepare":
        prepare(args.allow_sharealike_evaluation_only)
    elif args.stage == "acquire":
        if not args.source:
            parser.error("acquire requires --source")
        acquire(args.source, args.resume_after_stop)
    elif args.stage == "seal":
        seal()
    else:
        verify()


if __name__ == "__main__":
    main()
