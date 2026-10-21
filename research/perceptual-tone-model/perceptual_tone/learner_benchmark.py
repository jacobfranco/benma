"""Evaluation-only learner archive and alignment construction; no model runtime imports.

Selection consumes only source identity, transcript availability and provenance roles.
Historical system outputs are attached *after* selection and never enter the review UI.
"""

import csv
import hashlib
import html
import json
import re
import shutil
import subprocess
import wave
from collections import Counter
from pathlib import Path

from .aishell3 import alignment_token, parse_dictionary
from .aishell3_alignment import reconstruct, textgrid
from .aishell3_boundaries import derive
from .common import PACKAGE, ROOT, digest, file_hash, read_json, read_rows, write_json, write_rows
from .manifest import verify_baseline

CONFIG = PACKAGE / "configs/learner-benchmark.json"
DEFAULT = PACKAGE / "data/generated/learner-alignment-v1"
VAR = ROOT / "services/api/var"
WHOLE = ["PASS", "START ISSUE", "END ISSUE", "BOTH", "WRONG UNIT"]
TONE = ["PASS", "CLIPPED", "CONTAMINATED", "WRONG UNIT", "TOO LITTLE MATERIAL"]


def ref(path):
    path = Path(path).absolute()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def hanzi(text):
    return "".join(re.findall(r"[\u3400-\u9fff]", text or ""))


def asset(path):
    path = Path(path)
    return {"path": ref(path), "sha256": file_hash(path), "bytes": path.stat().st_size}


def decode(path):
    """Research fingerprint only, never rewrites an archived source."""
    p = Path(path)
    try:
        with wave.open(str(p)) as w:
            if w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2:
                return w.readframes(w.getnframes())
    except (wave.Error, EOFError):
        pass
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        capture_output=True,
        check=True,
    ).stdout


def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)


def role_for(names, config):
    """Strictly provenance-only. No audio features, family predictions or grades."""
    for role in ["excluded", "natural", "diagnostic", "human_intent_unconfirmed"]:
        for prefix, reason in config[role].items():
            if any(n.startswith(prefix) for n in names):
                return (
                    "unsuitable_unknown"
                    if role in ("excluded", "human_intent_unconfirmed")
                    else role
                ), reason
    return "unsuitable_unknown", "capture identity and natural/diagnostic intent not established"


def selection(record, config):
    if not record["audio_exists"] or not record["alignment_transcript"]:
        return "excluded"
    if record["role"] in ("natural", "diagnostic"):
        return "proposed_benchmark"
    if not record["known_control"] and any(
        n.startswith(p) for n in record["names"] for p in config["supplemental_alignment_prefixes"]
    ):
        return "supplemental_provenance_quarantine"
    return "excluded"


def source_files():
    """Explicit archive scope; never opens learned prediction files or model caches."""
    paths = set()
    for base in [
        VAR,
        ROOT / "apps/mobile/src/__tests__/fixtures",
        ROOT / "services/api/tests/fixtures",
        ROOT / "docs/research/pronunciation-v2",
    ]:
        for p in base.rglob("*.json"):
            if any(s in p.parts for s in ["deps", "silero-vad", "audio"]):
                continue
            if base.name == "pronunciation-v2" and not any(
                s.startswith(
                    (
                        "2026-10-02",
                        "2026-10-03",
                        "2026-10-04",
                        "2026-10-05",
                        "2026-10-06",
                        "2026-10-07",
                        "2026-10-08",
                        "2026-10-09",
                        "2026-10-12",
                        "2026-10-13",
                    )
                )
                for s in p.parts
            ):
                continue
            paths.add(p)
    return sorted(paths)


def discover(destination, config, study_dir=Path("/home/jacob/benma-study")):
    destination.mkdir(parents=True, exist_ok=False)
    source_pcm, records, path_owner, byte_owner = {}, {}, {}, {}

    def add_source(p):
        data = decode(p)
        pcm_hash = hashlib.sha256(data).hexdigest()
        key = pcm_hash[:24]
        if key not in records:
            source_pcm[key] = data
            records[key] = {
                "recording_id": key,
                "names": [],
                "audio": asset(p),
                "sources": [],
                "provenance": [],
                "transcripts": [],
                "intended_phrases": [],
                "historical_segmentation": [],
                "audio_exists": True,
                "pcm16k_sha256": pcm_hash,
                "duration_seconds": len(data) / 32000,
            }
        r = records[key]
        if p.stem not in r["names"]:
            r["names"].append(p.stem)
        if ref(p) not in {x["path"] for x in r["sources"]}:
            r["sources"].append(asset(p))
        path_owner[str(p.resolve())] = key
        byte_owner[file_hash(p)] = key
        return key

    # Canonical captures first: preferred evaluation copy, original upload preserved below.
    for p in sorted((VAR / "audio").glob("*/canonical/*")):
        add_source(p)
    for p in sorted(study_dir.glob("*.wav")):
        add_source(p)
    evidence = []
    # Parse metadata before the unknown original uploads, to recover explicit asset lineage.
    documents = []
    for p in source_files():
        try:
            d = read_json(p)
        except (ValueError, UnicodeError):
            continue
        documents.append((p, d))
        for item in walk(d):
            canonical = item.get("canonical")
            original = item.get("original")
            if isinstance(canonical, dict) and isinstance(original, dict):
                key = byte_owner.get(canonical.get("sha256"))
                if key and original.get("storage_key"):
                    op = VAR / "audio" / original["storage_key"]
                    if op.exists():
                        path_owner[str(op.resolve())] = key
                        byte_owner[file_hash(op)] = key
                        if ref(op) not in {a["path"] for a in records[key]["sources"]}:
                            records[key]["sources"].append(asset(op))
    all_audio = set((VAR / "audio").glob("*/*/*"))
    all_audio.update(VAR.rglob("*.wav"))
    all_audio = {p for p in all_audio if p.is_file() and "deps" not in p.parts}
    all_audio.update(study_dir.glob("*.wav"))
    # Saved research audio derivatives: native corpus/model artifacts are outside discovery scope.
    for name in ["audio", "stage0-pass1", "stage0-pass2", "stage0-validated", "stage0-reproduced"]:
        all_audio.update((PACKAGE / "data/generated" / name).rglob("*.wav"))
    # Originals may have no canonical counterpart; preserve as separate unknowns, not dropped.
    for p in sorted((VAR / "audio").glob("*/original/*")):
        if str(p.resolve()) not in path_owner:
            try:
                add_source(p)
            except (subprocess.CalledProcessError, wave.Error, EOFError) as e:
                evidence.append({**asset(p), "relationship": "broken_original", "error": str(e)})
    for p in sorted(all_audio):
        if p.suffix.lower() not in (".wav", ".m4a", ".mp3", ".webm", ".ogg"):
            continue
        key = path_owner.get(str(p.resolve())) or byte_owner.get(file_hash(p))
        relationship = "source_or_identical_copy"
        start = None
        if not key:
            try:
                pcm = decode(p)
                matches = [
                    (k, data.find(pcm))
                    for k, data in source_pcm.items()
                    if len(pcm) >= 3200 and len(pcm) <= len(data)
                ]
                matches = [(k, at) for k, at in matches if at >= 0 and at % 2 == 0]
                if len(matches) == 1:
                    key, at = matches[0]
                    start = at // 2
                    relationship = (
                        "exact_pcm_derivative"
                        if len(pcm) < len(source_pcm[key])
                        else "pcm_duplicate"
                    )
            except (subprocess.CalledProcessError, wave.Error, EOFError):
                relationship = "undecodable"
        if not key:
            relationship = (
                "generated_reference_or_assistant"
                if p.parent.name in ("reference", "assistant")
                else "unlinked_research_artifact"
            )
        evidence.append(
            {
                **asset(p),
                "recording_id": key,
                "relationship": relationship,
                "source_start_sample_16k": start,
            }
        )
        if key:
            path_owner[str(p.resolve())] = key
            byte_owner[file_hash(p)] = key
    stem_owner = {n: k for k, r in records.items() for n in r["names"]}
    source_audit = []
    missing_references = []
    for p, d in documents:
        for item in walk(d):
            key = item.get("storage_key")
            if isinstance(key, str) and "/canonical/" in key and not (VAR / "audio" / key).exists():
                missing_references.append(
                    {
                        "metadata_path": ref(p),
                        "storage_key": key,
                        "audio_exists": False,
                        "reason": "referenced_canonical_audio_missing",
                    }
                )

    def identify(item):
        for field in ["audio_sha256", "canonical_sha256", "sha256"]:
            if item.get(field) in byte_owner:
                return byte_owner[item[field]]
        for field in ["storage_key", "audio_path", "path", "recording", "id"]:
            v = item.get(field)
            if isinstance(v, str):
                if Path(v).stem in stem_owner:
                    return stem_owner[Path(v).stem]
                if str(Path(v).resolve()) in path_owner:
                    return path_owner[str(Path(v).resolve())]
        for field in ["canonical", "audio", "provenance"]:
            if isinstance(item.get(field), dict):
                found = identify(item[field])
                if found:
                    return found
        return None

    analysis_ids = {}
    for p, d in documents:
        used = False
        for item in walk(d):
            key = identify(item)
            if not key:
                continue
            used = True
            r = records[key]
            origin = {"path": ref(p), "sha256": file_hash(p)}
            if origin not in r["provenance"]:
                r["provenance"].append(origin)
            if isinstance(item.get("id"), str):
                analysis_ids[item["id"]] = key
            per = item.get("perception", {})
            texts = [
                item.get("alignment_reference_text"),
                item.get("transcript"),
                item.get("lookup_text_only"),
                per.get("transcript") if isinstance(per, dict) else None,
                per.get("raw_transcript") if isinstance(per, dict) else None,
            ]
            for value in texts:
                if isinstance(value, str) and hanzi(value) and value not in r["transcripts"]:
                    r["transcripts"].append(value)
            intended = item.get("intended_text")
            if isinstance(intended, str) and intended not in r["intended_phrases"]:
                r["intended_phrases"].append(intended)
            for attempt in item.get("attempts", []) or []:
                target = attempt.get("target", {}) or {}
                if target.get("text") and target["text"] not in r["intended_phrases"]:
                    r["intended_phrases"].append(target["text"])
            analyses = item.get("analyses", []) or []
            if isinstance(item.get("analysis"), dict):
                analyses = [*analyses, item["analysis"]]
            if "alignment_reference_text" in item:
                analyses = [*analyses, item]
            for a in analyses:
                if a.get("id"):
                    analysis_ids[a["id"]] = key
                t = a.get("alignment_reference_text")
                if t and t not in r["transcripts"]:
                    r["transcripts"].append(t)
                result = a.get("result", a)
                syllables = result.get("syllables", [])
                if syllables:
                    historical = {
                        "source": origin,
                        "analysis_id": a.get("id"),
                        "alignment_reference_text": t,
                        "alignment_status": result.get("alignment_status"),
                        "syllables": [
                            {
                                k: s.get(k)
                                for k in [
                                    "index",
                                    "characters",
                                    "pinyin",
                                    "lexical_tone",
                                    "expected_surface_tone",
                                    "surface_rule",
                                    "start_seconds",
                                    "end_seconds",
                                    "timing",
                                    "timing_source",
                                    "timing_evidence_id",
                                ]
                            }
                            for s in syllables
                        ],
                    }
                    if digest(historical) not in {digest(h) for h in r["historical_segmentation"]}:
                        r["historical_segmentation"].append(historical)
        if used:
            source_audit.append(asset(p))
    # Fixtures whose identity is recorded in separate provenance files.
    for _p, d in documents:
        for item in walk(d):
            if item.get("id") in analysis_ids and item.get("alignment_reference_text"):
                r = records[analysis_ids[item["id"]]]
                if item["alignment_reference_text"] not in r["transcripts"]:
                    r["transcripts"].append(item["alignment_reference_text"])
    for r in records.values():
        r["role"], r["role_reason"] = role_for(r["names"], config)
        r["known_control"] = any(n.startswith(k) for n in r["names"] for k in config["excluded"])
        study = next((n for n in r["names"] if n in config["study_alignment_transcripts"]), None)
        r["alignment_transcript"] = (
            config["study_alignment_transcripts"][study]
            if study
            else hanzi(r["transcripts"][0])
            if r["transcripts"]
            else None
        )
        r["intended_phrase"] = r["intended_phrases"][0] if r["intended_phrases"] else None
        # A saved perceived text does not establish an intended phrase.
        r["phrase_basis"] = (
            "documented_study_prompt" if study else "historical_ASR_alignment_hypothesis"
        )
        r["actual_reading_hypothesis"] = (
            "我要去贵州 (documented instruction, realization unverified)"
            if study == "S13"
            else None
        )
        r["transcript_conflict"] = bool(
            study and any(hanzi(t) != r["alignment_transcript"] for t in r["transcripts"])
        )
        r["selection"] = selection(r, config)
        r["exclusion_reason"] = (
            None
            if r["selection"] == "proposed_benchmark"
            else r["role_reason"]
            if r["alignment_transcript"]
            else "no_recoverable_transcript_or_intent"
        )
        r["transcript_exists"] = bool(r["transcripts"])
        r["phrase_reconstructable"] = bool(r["alignment_transcript"])
        r["alignment_failed"] = None
        r["tone_bearing_derivable"] = None
    rows = sorted(records.values(), key=lambda r: r["recording_id"])
    write_rows(destination / "inventory.jsonl", rows)
    write_rows(destination / "audio-artifacts.jsonl", evidence)
    write_json(destination / "discovery-sources.json", source_audit)
    write_rows(destination / "missing-audio-references.jsonl", missing_references)
    write_json(
        destination / "inventory-summary.json",
        {
            "source_recordings": len(rows),
            "archive_audio_artifacts": len(evidence),
            "roles": dict(Counter(r["role"] for r in rows)),
            "selection": dict(Counter(r["selection"] for r in rows)),
            "phrases": dict(
                sorted(
                    Counter(
                        r["alignment_transcript"] for r in rows if r["alignment_transcript"]
                    ).items()
                )
            ),
            "relationships": dict(Counter(e["relationship"] for e in evidence)),
            "scope": (
                "All local upload originals/canonical captures, benma-study, saved physical "
                "archives and research derivatives. No live database/network. "
                "Unproven sources retained as unknown."
            ),
        },
    )
    return rows


def tokens(record):
    from pypinyin import Style, lazy_pinyin

    phrase = record["alignment_transcript"]
    values = lazy_pinyin(phrase, style=Style.TONE3, neutral_tone_with_five=True, errors="strict")
    if len(values) != len(phrase) or any(not re.fullmatch(r"[a-zvü]+[1-5]", v) for v in values):
        raise ValueError("unrecoverable_read_units")
    # Phrase dictionaries can return contextual ge5; retain lexical ge4 separately.
    values = ["ge4" if ch == "个" else p for ch, p in zip(phrase, values, strict=True)]
    lexical = [int(v[-1]) for v in values]
    intended = hanzi(record.get("intended_phrase"))
    intended_values = (
        lazy_pinyin(intended, style=Style.TONE3, neutral_tone_with_five=True)
        if len(intended) == len(phrase)
        else []
    )
    intended_values = [
        "ge4" if ch == "个" else p for ch, p in zip(intended, intended_values, strict=False)
    ]
    expected_phrase = intended if intended_values else phrase
    expected_lexical = [int(p[-1]) for p in intended_values] if intended_values else lexical
    units = []
    for i, (ch, p) in enumerate(zip(phrase, values, strict=True)):
        expected_ch = expected_phrase[i]
        surface = expected_lexical[i]
        alternatives = []
        basis = "lexical_default_contextual_expectation_not_realized_label"
        if (
            expected_ch in "们吧了个"
            or (expected_ch in "友上" and i and expected_phrase[i - 1 : i + 1] in ("朋友", "晚上"))
            or (i and expected_ch == expected_phrase[i - 1] == "走")
        ):
            surface, basis = 5, "contextual_neutral_expected"
        elif expected_ch == "一" and i + 1 < len(values):
            surface, basis = (2 if expected_lexical[i + 1] == 4 else 4), "yi_context_rule"
        elif expected_ch == "不" and i + 1 < len(values) and expected_lexical[i + 1] == 4:
            surface, basis = 2, "bu_before_T4"
        elif expected_lexical[i] == 3 and i + 1 < len(values) and expected_lexical[i + 1] == 3:
            surface, alternatives, basis = None, [2, 3], "T3_chain_prosodic_grouping_unreviewed"
        # MFA transcript uses lexical pronunciation, as in AISHELL, not a predicted tone.
        units.append(
            {
                "index": i,
                "hanzi": ch,
                "corpus_pinyin": p,
                "corpus_tone": lexical[i],
                "intended_pinyin": intended_values[i] if intended_values else None,
                "alignment_pinyin": p,
                "intended_lexical_tone": int(intended_values[i][-1]) if intended_values else None,
                "alignment_lexical_tone": lexical[i],
                "expected_surface_tone": surface,
                "surface_alternatives": alternatives,
                "surface_basis": basis,
                "expected_tone_text_basis": "intended_phrase"
                if intended_values
                else "alignment_reading_hypothesis",
                "actual_reading_hypothesis": record["actual_reading_hypothesis"],
                "model_prediction": None,
                "human_perceptual_judgment": None,
            }
        )
    return units


def prepare(destination=DEFAULT):
    config = read_json(CONFIG)
    baseline = verify_baseline()
    discover(destination, config)
    # Inventory is written in full before any selection or alignment outputs.
    write_json(
        destination / "protocol.json",
        {
            "config": config,
            "config_sha256": file_hash(CONFIG),
            "baseline": baseline,
            "status": "candidate_only_human_QA_pending",
            "no_training": True,
            "no_predictions": True,
            "evaluation_only": True,
        },
    )
    models = []
    for role, folder, name in [
        ("primary", "aishell3-multispeaker-fixed-v2", "experiment_B.joblib"),
        ("secondary", "aishell3-first-four-tone-v1", "model2_hubert.joblib"),
    ]:
        p = PACKAGE / "models/generated" / folder / name
        models.append({"role": role, **asset(p)})
    native_files = []
    for base in [
        PACKAGE / "models/generated",
        PACKAGE / "data/generated/aishell3/releases",
        PACKAGE / "data/generated/aishell3-multispeaker-v2/releases",
    ]:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in (".json", ".jsonl", ".joblib"):
                native_files.append(asset(p))  # hash only, never read probabilities
    write_json(
        destination / "frozen-models.json",
        {
            "models": models,
            "method": read_json(PACKAGE / "configs/aishell3-multispeaker.json")["primary"],
            "native_preservation": native_files,
        },
    )
    return prepare_alignment(destination)


def prepare_alignment(destination):
    rows = read_rows(destination / "inventory.jsonl")
    selected = [r for r in rows if r["selection"] != "excluded"]
    audits = [
        PACKAGE / "data/generated/aishell3-multispeaker-v2/expansion/lexicon-audit.json",
        PACKAGE / "data/generated/aishell3-multispeaker-v2/pilot/lexicon-audit.json",
    ]
    pronunciations = {}
    for p in audits:
        d = read_json(p)
        for token, pinyin in d["mapping"].items():
            pronunciations[pinyin] = d["pronunciations"][token]
    # Reuse exact numbered pinyin pronunciations; fill missing entries only from
    # the pinned stock dictionary's single-Hanzi, matching-tone pronunciation.
    stock = parse_dictionary(
        (
            PACKAGE / ".cache/mfa-work/pretrained_models/dictionary/mandarin_china_mfa.dict"
        ).read_text()
    )
    utterances, lexicon, supplements = [], {}, {}
    for r in selected:
        units = tokens(r)
        key = r["recording_id"]
        corpus = destination / "corpus/jacob"
        corpus.mkdir(parents=True, exist_ok=True)
        pcm = decode(ROOT / r["audio"]["path"])
        wav = corpus / f"{key}.wav"
        with wave.open(str(wav), "wb") as w:
            w.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            w.writeframes(pcm)
        for u in units:
            if u["corpus_pinyin"] not in pronunciations:
                spec = read_json(CONFIG)["dictionary_supplements"].get(u["corpus_pinyin"])
                if not spec or tuple(spec["phones"]) not in stock.get(spec["hanzi"], []):
                    raise ValueError("missing_pinned_pronunciation:" + u["corpus_pinyin"])
                pronunciations[u["corpus_pinyin"]] = [spec["phones"]]
                supplements[u["corpus_pinyin"]] = spec
            lexicon[alignment_token(u)] = pronunciations[u["corpus_pinyin"]]
        (corpus / f"{key}.lab").write_text(" ".join(alignment_token(u) for u in units) + "\n")
        utterances.append(
            {
                "utterance_id": key,
                "corpus": "Benma-learner-evaluation-only",
                "speaker_id": "jacob",
                "partition": "evaluation_candidate",
                "source_partition": r["role"],
                "audio": {"reference": str(wav.resolve()), "sha256": file_hash(wav)},
                "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
                "duration": len(pcm) / 32000,
                "transcript": r["alignment_transcript"],
                "transcript_provenance": r["provenance"],
                "prosody_status": "unknown",
                "units": units,
                "source_recording": r,
            }
        )
    write_rows(destination / "selected-recordings.jsonl", selected)
    write_rows(destination / "utterances.jsonl", utterances)
    write_json(destination / "lexicon.json", lexicon)
    write_json(destination / "lexicon-supplements.json", supplements)
    (destination / "read-units.dict").write_text(
        "".join(
            token + "\t" + " ".join(p) + "\n" for token in sorted(lexicon) for p in lexicon[token]
        )
    )
    write_json(
        destination / "selection-seal.json",
        {
            "files": {
                n: file_hash(destination / n)
                for n in [
                    "inventory.jsonl",
                    "selected-recordings.jsonl",
                    "utterances.jsonl",
                    "protocol.json",
                    "lexicon.json",
                    "read-units.dict",
                ]
            },
            "selected_recordings": len(selected),
            "units": sum(len(u["units"]) for u in utterances),
            "model_outputs_available_to_selection": False,
        },
    )
    return read_json(destination / "inventory-summary.json")


def verify_inputs(destination):
    verify_baseline()
    for name, sha in read_json(destination / "selection-seal.json")["files"].items():
        if file_hash(destination / name) != sha:
            raise ValueError("selection_changed:" + name)
    for f in read_json(destination / "frozen-models.json")["native_preservation"]:
        if file_hash(ROOT / f["path"]) != f["sha256"]:
            raise ValueError("native_artifact_changed:" + f["path"])
    for u in read_rows(destination / "utterances.jsonl"):
        if file_hash(u["audio"]["reference"]) != u["audio"]["sha256"]:
            raise ValueError("alignment_input_audio_changed")
    for r in read_rows(destination / "inventory.jsonl"):
        for a in r["sources"]:
            if file_hash(ROOT / a["path"]) != a["sha256"]:
                raise ValueError("original_audio_changed")


def import_alignment(utterance, grid, lexicon, diagnostics):
    config = read_json(PACKAGE / "configs/aishell3.json")
    # Keep native diagnostic thresholds; long learner units flagged, never truncated.
    rows = reconstruct(utterance, textgrid(grid), lexicon, diagnostics, config)
    for r in rows:
        r["example_id"] = f"learner:{utterance['utterance_id']}:{r['index']}"
    return rows


def crop(source, interval, target):
    with wave.open(str(source), "rb") as w:
        if w.getframerate() != interval["sample_rate_hz"]:
            raise ValueError("crop_sample_rate_mismatch")
        w.setpos(interval["start_sample"])
        count = interval["end_sample"] - interval["start_sample"]
        pcm = w.readframes(count)
        params = w.getparams()
    if len(pcm) != count * params.nchannels * params.sampwidth:
        raise ValueError("short_crop")
    target.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as w:
        w.setparams(params)
        w.writeframes(pcm)
    return {
        **asset(target),
        "frames": count,
        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        **interval,
    }


def build(destination=DEFAULT):
    verify_inputs(destination)
    utterances = read_rows(destination / "utterances.jsonl")
    lexicon = read_json(destination / "lexicon.json")
    analysis = destination / "aligned/alignment_analysis.csv"
    diagnostics = {}
    with analysis.open() as stream:
        for r in csv.DictReader(stream):
            diagnostics[r["file"]] = {
                **r,
                "alignment_log_likelihood": float(r["overall_log_likelihood"])
                if r["overall_log_likelihood"]
                else None,
                "source_sha256": file_hash(analysis),
            }
    rows, failures, qa = [], [], []
    for u in utterances:
        grid = destination / "aligned/jacob" / (u["utterance_id"] + ".TextGrid")
        try:
            ds = {**diagnostics.get(u["utterance_id"], {}), "textgrid_sha256": file_hash(grid)}
            aligned = import_alignment(u, grid.read_text(), lexicon, ds)
        except (ValueError, FileNotFoundError) as e:
            failures.append(
                {
                    "recording_id": u["utterance_id"],
                    "reason": str(e),
                    "audio_exists": True,
                    "transcript_exists": True,
                    "phrase_reconstructable": True,
                    "alignment_failed": True,
                    "tone_bearing_derivable": False,
                }
            )
            continue
        for row in aligned:
            r = u["source_recording"]
            flags = list(row["exclusion_reasons"])
            if r["transcript_conflict"]:
                flags.append("historical_ASR_disagrees_with_documented_reading")
            projection = None
            if row["start"] is not None:
                try:
                    projection = derive(row, 16000, round(u["duration"] * 16000))
                    flags.extend(projection["flags"])
                except ValueError as e:
                    flags.append(str(e))
            row.update(
                source_recording_id=r["recording_id"],
                alignment_speaker_group="jacob",
                speaker_id="jacob" if r["role"] in ("natural", "diagnostic") else None,
                realized_tone_ground_truth=None,
                provenance=r["provenance"],
                original_sources=r["sources"],
                intended_phrase=r["intended_phrase"],
                role=r["role"],
                selection=r["selection"],
                historical_segmentation=r["historical_segmentation"],
                actual_reading_hypothesis=r["actual_reading_hypothesis"],
                model_prediction=None,
                human_perceptual_judgment=None,
                alignment_qa=None,
                spans=projection,
                flags=sorted(set(flags)),
                eligible_for_training=False,
                eligible_for_evaluation=False,
                status="pending_human_alignment_QA",
            )
            rows.append(row)
            if not projection or not projection["available"]:
                failures.append(
                    {
                        "example_id": row["example_id"],
                        "recording_id": r["recording_id"],
                        "reason": flags or ["no_tone_bearing_span"],
                        "audio_exists": True,
                        "transcript_exists": True,
                        "phrase_reconstructable": True,
                        "alignment_failed": row["start"] is None,
                        "tone_bearing_derivable": False,
                    }
                )
                continue
            item_id = f"Q{len(qa) + 1:03d}"
            clips = {}
            for view, key in [
                ("context", "context"),
                ("whole", "playback_read_unit"),
                ("tone", "tone_bearing_pooling_span"),
            ]:
                clips[view] = crop(
                    u["audio"]["reference"],
                    projection[key],
                    destination / "qa/audio" / f"{item_id}-{view}.wav",
                )
            qa.append(
                {
                    "item_id": item_id,
                    "example_id": row["example_id"],
                    "phrase": row["transcript"],
                    "hanzi": row["hanzi"],
                    "pinyin": row["alignment_pinyin"],
                    "index": row["index"],
                    "flags": row["flags"],
                    "selection": row["selection"],
                    "clips": clips,
                    "source_audio_sha256": u["audio"]["sha256"],
                }
            )
    write_rows(destination / "candidate-manifest.jsonl", rows)
    write_rows(destination / "alignment-failures.jsonl", failures)
    write_rows(
        destination / "suspicious-units.jsonl",
        [r for r in rows if r["flags"] or r["selection"] != "proposed_benchmark"],
    )
    # Retain existing frozen deterministic outputs only after selection, by exact take ID.
    historical = []
    for r in read_rows(PACKAGE / "stage0.baseline.jsonl"):
        matches = [u for u in utterances if r["recording_id"] in u["source_recording"]["names"]]
        if matches:
            historical.append(
                {
                    "recording_id": matches[0]["utterance_id"],
                    "source_recording_name": r["recording_id"],
                    "source": ref(PACKAGE / "stage0.baseline.jsonl"),
                    "source_sha256": file_hash(PACKAGE / "stage0.baseline.jsonl"),
                    "target": r["target"],
                    "deterministic": r["deterministic"],
                    "historical_notes": r.get("notes"),
                }
            )
    write_rows(destination / "historical-benma.jsonl", historical)
    packet = {
        "version": read_json(CONFIG)["version"],
        "candidate_manifest_sha256": file_hash(destination / "candidate-manifest.jsonl"),
        "items": qa,
        "whole_choices": WHOLE,
        "tone_choices": TONE,
        "purpose": "alignment_integrity_only",
    }
    packet["packet_sha256"] = digest(packet)
    write_json(destination / "qa/packet.json", packet)
    render_page(destination, packet)
    proposed = [r for r in rows if r["selection"] == "proposed_benchmark"]

    def counts(field, values):
        c = Counter(r[field] for r in values)
        return {
            **{f"T{i}" if i != 5 else "neutral": c[i] for i in range(1, 6)},
            "unresolved": c[None],
        }

    summary = {
        "aligned_recordings": len(utterances)
        - len({f["recording_id"] for f in failures if "example_id" not in f}),
        "recording_alignment_failures": [f for f in failures if "example_id" not in f],
        "unit_alignment_failures": len(failures),
        "tone_bearing_spans": len(qa),
        "qa_items": len(qa),
        "proposed_recordings": len({r["source_recording_id"] for r in proposed}),
        "proposed_units": len(proposed),
        "proposed_phrases": sorted(
            {r["intended_phrase"] for r in proposed if r["intended_phrase"]}
        ),
        "proposed_lexical": counts("intended_lexical_tone", proposed),
        "proposed_alignment_lexical": counts("alignment_lexical_tone", proposed),
        "proposed_surface": counts("expected_surface_tone", proposed),
        "all_QA_alignment_lexical": counts("alignment_lexical_tone", rows),
        "all_QA_surface": counts("expected_surface_tone", rows),
        "unique_syllables": len({r["alignment_pinyin"].rstrip("12345") for r in proposed}),
        "repeated_takes_beyond_first_per_phrase": len({r["source_recording_id"] for r in proposed})
        - len({r["transcript"] for r in proposed}),
        "suspicious_alignment_units": sum(bool(r["flags"]) for r in rows),
        "provenance_quarantined_units": sum(r["selection"] != "proposed_benchmark" for r in rows),
        "pending_QA": True,
        "benchmark_frozen": False,
        "prediction_run": False,
    }
    write_json(destination / "alignment-summary.json", summary)
    return summary


def render_page(destination, packet):
    cards = []
    for item in packet["items"]:
        buttons = "".join(
            f'<button data-play="{v}">PLAY {label}</button><audio preload="none" data-view="{v}" src="audio/{item["item_id"]}-{v}.wav"></audio>'  # noqa: E501
            for v, label in [
                ("context", "CONTEXT"),
                ("whole", "WHOLE TARGET"),
                ("tone", "TONE-BEARING TARGET"),
            ]
        )
        choices = "".join(
            f'<label>{name}<select data-decision="{key}"><option value="">Choose…</option>'
            + "".join(f"<option>{c}</option>" for c in options)
            + "</select></label>"
            for name, key, options in [
                ("WHOLE TARGET", "whole", WHOLE),
                ("TONE-BEARING TARGET", "tone", TONE),
            ]
        )
        cards.append(
            f'<section data-id="{item["item_id"]}"><h2>{item["item_id"]} · {html.escape(item["phrase"])} · target {item["index"] + 1}: <b>{html.escape(item["hanzi"])}</b> ({html.escape(item["pinyin"])})</h2>{buttons}{choices}<label><input type="checkbox" data-heard> I listened to all three clips</label><label>Boundary/ownership notes<textarea></textarea></label></section>'  # noqa: E501
        )
    encoded = json.dumps(packet, ensure_ascii=False).replace("<", "\\u003c")
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Learner alignment QA</title><style>*{box-sizing:border-box}button,select,input,textarea{max-width:calc(100% - 14px)}header input{display:block}h2{overflow-wrap:anywhere}body{font:17px system-ui;max-width:1000px;margin:auto;padding:20px;background:#f5f6f7;color:#17212b}section{background:white;border:1px solid #aab4bf;padding:20px;margin:18px 0;border-radius:8px}h2{font-size:19px}button,select,input,textarea{font:inherit;margin:7px;padding:9px}label{display:block}textarea{width:85%}button{cursor:pointer}#status{white-space:pre-wrap}header{background:#f5f6f7;padding:8px;border-bottom:1px solid #888}audio{display:none}</style><header><h1>Learner alignment QA</h1><p>Judge timing and ownership only. Pinyin is a reading hypothesis, not a realized-tone label. Listen to context, whole target, and tone-bearing target. Report clipping or neighboring material; do not classify tones. Some historical takes remain outside the benchmark pending provenance.</p><label>Reviewer <input id="reviewer" autocomplete="name"></label><button id="export">Export completed QA</button><button id="draft">Save draft</button><label>Resume saved review <input id="import" type="file" accept="application/json"></label><div id="status" role="status"></div></header>"""  # noqa: E501
    page += (
        "".join(cards)
        + f'<script id="packet" type="application/json">{encoded}</script>'
        + '<script src="review.js"></script></html>'
    )
    (destination / "qa/index.html").write_text(page)
    shutil.copyfile(PACKAGE / "scripts/learner_review.js", destination / "qa/review.js")


def validate_reviews(packet, answers):
    expected = {i["item_id"] for i in packet["items"]}
    if (
        answers.get("packet_sha256") != packet["packet_sha256"]
        or not answers.get("reviewer", "").strip()
    ):
        raise ValueError("review_packet_or_reviewer_mismatch")
    reviews = answers.get("reviews", [])
    if len(reviews) != len(expected) or {r["item_id"] for r in reviews} != expected:
        raise ValueError("incomplete_or_duplicate_reviews")
    for r in reviews:
        if set(r.get("listened_views", [])) != {"context", "whole", "tone"}:
            raise ValueError("all_three_playback_acknowledgments_required")
        if (
            r.get("whole") not in WHOLE
            or r.get("tone") not in TONE
            or not r.get("heard_all")
            or not r.get("reviewed_at")
        ):
            raise ValueError("incomplete_alignment_review")
        if (r["whole"] != "PASS" or r["tone"] != "PASS") and not r.get("notes", "").strip():
            raise ValueError("issue_requires_notes")
    return {r["item_id"]: r for r in reviews}


def release(destination, answers_path, version):
    """Explicit later-continuation action. Never evaluates models or trains."""
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", version):
        raise ValueError("invalid_release_version")
    verify_inputs(destination)
    packet = read_json(destination / "qa/packet.json")
    if digest({k: v for k, v in packet.items() if k != "packet_sha256"}) != packet["packet_sha256"]:
        raise ValueError("packet_changed")
    if file_hash(destination / "candidate-manifest.jsonl") != packet["candidate_manifest_sha256"]:
        raise ValueError("candidate_changed")
    for item in packet["items"]:
        for clip in item["clips"].values():
            if file_hash(ROOT / clip["path"]) != clip["sha256"]:
                raise ValueError("review_audio_changed")
    for row in read_rows(destination / "candidate-manifest.jsonl"):
        grid = destination / "aligned/jacob" / (row["utterance_id"] + ".TextGrid")
        if file_hash(grid) != row["alignment_diagnostics"]["textgrid_sha256"]:
            raise ValueError("reviewed_alignment_changed")
    answers = read_json(answers_path)
    checked = validate_reviews(packet, answers)
    mapped = {i["example_id"]: checked[i["item_id"]] for i in packet["items"]}
    accepted, excluded = [], []
    for row in read_rows(destination / "candidate-manifest.jsonl"):
        qa = mapped.get(row["example_id"])
        passing = qa and qa["whole"] == qa["tone"] == "PASS"
        reasons = list(row["flags"])
        if row["selection"] != "proposed_benchmark":
            reasons.append("unconfirmed_provenance")
        if not passing:
            reasons.append("alignment_QA_not_passed")
        updated = {
            **row,
            "alignment_qa": qa,
            "exclusion_reasons": reasons,
            "eligible_for_evaluation": not reasons,
            "status": "quarantined" if reasons else "frozen_evaluation_only",
        }
        (excluded if reasons else accepted).append(updated)
    if not accepted:
        raise ValueError("no_eligible_reviewed_units")
    for name in (
        "inventory.jsonl",
        "audio-artifacts.jsonl",
        "protocol.json",
        "selection-seal.json",
        "frozen-models.json",
    ):
        if not (destination / name).exists():
            raise ValueError("missing_release_provenance:" + name)
    folder = destination / "releases" / version
    folder.mkdir(parents=True, exist_ok=False)
    write_rows(folder / "manifest.jsonl", accepted)
    write_rows(folder / "exclusions.jsonl", excluded)
    write_json(folder / "human-QA.json", answers)
    # Preserve the entire discovery/selection/exclusion context with the release.
    supporting_files = {}
    for name in (
        "inventory.jsonl",
        "audio-artifacts.jsonl",
        "protocol.json",
        "selection-seal.json",
        "frozen-models.json",
    ):
        source = destination / name
        if not source.exists():
            raise ValueError("missing_release_provenance:" + name)
        shutil.copyfile(source, folder / name)
        supporting_files[name] = file_hash(folder / name)
    write_json(
        folder / "release.json",
        {
            "version": version,
            "manifest_sha256": file_hash(folder / "manifest.jsonl"),
            "exclusions_sha256": file_hash(folder / "exclusions.jsonl"),
            "human_QA_sha256": file_hash(folder / "human-QA.json"),
            "packet_sha256": packet["packet_sha256"],
            "evaluation_only": True,
            "training_prohibited": True,
            "frozen_models_sha256": file_hash(destination / "frozen-models.json"),
            "accepted_units": len(accepted),
            "supporting_files": supporting_files,
        },
    )
    return {"release": str(folder), "units": len(accepted), "excluded": len(excluded)}
