"""Read-only inputs -> sealed perceptual stimuli. No model-result reader lives here."""

import base64
import hashlib
import io
import json
import math
import random
import re
import wave
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.signal import correlate, resample_poly

from .aishell3 import parse_content
from .aishell3_boundaries import derive
from .common import PACKAGE, ROOT, canonical, digest, file_hash, read_json, read_rows, write_json
from .manifest import verify_baseline

VERSION = "benma-realized-tone-blind-v1-20261019"
SEED = 20261019
OUTPUT = PACKAGE / "data/generated/realized-tone-blind-v1-20261019"
LEARNER = PACKAGE / "data/generated/releases/benma-learner-natural-v1-20261019"
LEARNER_SHA = "8024a51df91e60b9e336189cd9b04dfbf2d5d8c530fd0656778c731e1306f4ae"
NATIVE = (
    PACKAGE
    / "data/generated/aishell3-multispeaker-v2/releases"
    / "aishell3-multispeaker-context-v2-20261017"
)
COUNTS = {"T1": 6, "T2": 6, "T3": 6, "T4": 6, "NEUTRAL": 4}
CHOICES = {
    "T1": "T1 — high / level",
    "T2": "T2 — rising",
    "T3": "T3 — low / dipping / low-rising",
    "T4": "T4 — falling",
    "NEUTRAL": "NEUTRAL / WEAK",
    "UNCLEAR": "UNCLEAR / CANNOT TELL",
}
VIEWS = {"tone": "tone_bearing_pooling_span", "whole": "playback_read_unit"}
MIN_REPEAT_DISTANCE = 15


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_inputs():
    require(file_hash(LEARNER / "release-manifest.json") == LEARNER_SHA, "learner_release_changed")
    for root, filename in ((LEARNER, "release-manifest.json"), (NATIVE, "release.json")):
        for name, sha in read_json(root / filename)["files"].items():
            require(file_hash(root / name) == sha, "release_file_changed:" + name)
    require(
        read_json(NATIVE / "release.json")["qa_gate"] == "SATISFIED_WITH_EXPLICIT_QUARANTINES",
        "native_qa_gate_not_satisfied",
    )
    return verify_baseline()


@lru_cache(maxsize=128)
def source_audio(path, sha):
    require(file_hash(path) == sha, "source_audio_changed")
    with wave.open(path) as stream:
        require(stream.getnchannels() == 1 and stream.getsampwidth() == 2, "source_format")
        rate = stream.getframerate()
        raw = stream.readframes(stream.getnframes())
        require(len(raw) == stream.getnframes() * 2, "incomplete_audio")
    return np.frombuffer(raw, dtype="<i2"), rate, {"pcm_sha256": hashlib.sha256(raw).hexdigest()}


@lru_cache(maxsize=4)
def source_transcript(path, sha):
    require(file_hash(path) == sha, "corpus_transcript_changed")
    return Path(path).read_text().splitlines()


def periodic_frames(pcm, rate):
    """Fixed, label-free periodicity presence check; no contour or tone estimate."""
    x = resample_poly(pcm.astype(float) / 32768, 8000, rate)
    window, hop = 320, 80  # 40 ms, 10 ms at 8 kHz
    count = 0
    for start in range(0, len(x) - window + 1, hop):
        frame = x[start : start + window]
        frame = frame - frame.mean()
        energy = np.dot(frame, frame)
        if energy / window < 1e-6:
            continue
        corr = correlate(frame, frame, mode="full", method="fft")[window - 1 :]
        lags = np.arange(16, 134)  # 60-500 Hz, used only for periodicity existence
        scores = corr[lags] / (energy * (1 - lags / window))
        count += int(float(scores.max()) >= 0.35)
    return count


def mechanical(row, spans, *, control):
    pcm, rate, info = source_audio(row["audio"]["reference"], row["audio"]["sha256"])
    require(info["pcm_sha256"] == row["pcm_sha256"], "source_pcm_changed")
    reconstructed = derive(row, rate, len(pcm))
    for key in (*VIEWS.values(), "owned_phone_indices", "original_mfa_phones", "policy"):
        require(reconstructed[key] == spans[key], "span_ownership_mismatch:" + key)
    require(spans["available"] and spans["owned_phone_indices"], "missing_owned_nucleus")
    pieces = {}
    for name, key in VIEWS.items():
        s = spans[key]
        require(0 <= s["start_sample"] < s["end_sample"] <= len(pcm), "invalid_span")
        pieces[name] = pcm[s["start_sample"] : s["end_sample"]]
        require(bool(np.any(pieces[name])), "zero_audio")
    tone = pieces["tone"]
    peak = int(np.max(np.abs(pieces["whole"].astype(np.int32))))
    voiced = periodic_frames(tone, rate)
    if control:
        require(peak < 32760, "digital_clipping")
        require(voiced > 0, "no_periodic_material")
    return {
        "source_sha256": row["audio"]["sha256"],
        "source_pcm_sha256": info["pcm_sha256"],
        "exact_owned_source_samples": True,
        "tone_pcm_sha256": hashlib.sha256(tone.tobytes()).hexdigest(),
        "tone_seconds": len(tone) / rate,
        "whole_seconds": len(pieces["whole"]) / rate,
        "whole_peak_pcm16": peak,
        "periodic_frames": voiced,
        "owned_nucleus_and_coda": True,
    }


def unit_record(row, spans, role, check, review=None):
    # Explicit projection: unneeded labels, historical results and predictions never
    # reach learner/control selection, repeat selection, or presentation ordering.
    tone = row["corpus_tone"] if role == "control" else None
    return {
        "unit_id": row["example_id"],
        "source_id": row.get("source_id", row["utterance_id"]),
        "speaker_id": row["speaker_id"],
        "role": role,
        "gold": ("NEUTRAL" if tone == 5 else "T" + str(tone)) if tone else None,
        "phonetic_base": row.get("phonetic_base") if role == "control" else None,
        "position": "utterance_edge"
        if not row["preceding"] or not row["following"]
        else "utterance_medial",
        "source_audio": row["audio"],
        "spans": {k: spans[k] for k in VIEWS.values()},
        "mechanical": check,
        "qa_basis": "individual_tone_PASS"
        if role == "learner" or review
        else "frozen_release_corpus_QA_acceptance",
        "individual_native_review": review,
    }


def load_eligible():
    learners = read_rows(LEARNER / "primary.jsonl")
    excluded = {r["example_id"] for r in read_rows(LEARNER / "primary-quarantine.jsonl")}
    require(len(learners) == 16 and len(excluded) == 16, "learner_count_changed")
    units = []
    for r in learners:
        require(
            r["example_id"] not in excluded
            and not r["quarantined"]
            and not r["alignment_quarantined"]
            and not r["structural_violations"]
            and r["provenance_category"] == "PRIMARY_NATURAL_CANDIDATE"
            and r["qa"]["tone"] == "PASS"
            and r["eligible_for_evaluation"],
            "ineligible_learner",
        )
        units.append(
            unit_record(r, r["spans"], "learner", mechanical(r, r["spans"], control=False))
        )
    learner_speakers = {u["speaker_id"] for u in units}
    split = read_json(NATIVE / "split.json")["assignments"]
    registry = {r["speaker_id"]: r for r in read_rows(NATIVE / "speaker-registry.jsonl")}
    quarantine = {r["record"]["example_id"] for r in read_rows(NATIVE / "quarantined.jsonl")}
    reviewed = {r["example_id"]: r for r in read_rows(NATIVE / "qa-decisions.jsonl")}
    pool, failures = [], []
    for candidate in read_rows(NATIVE / "manifest.jsonl"):
        r, spans = candidate["original"], candidate["spans"]
        if r["partition"] != "test":
            continue
        try:
            require(r["example_id"] not in quarantine and not r["exclusion_reasons"], "quarantine")
            require(split[r["speaker_id"]] == "test", "split_mismatch")
            require(r["speaker_id"] not in learner_speakers, "learner_speaker_overlap")
            require(r["speaker_id"] in registry, "unverified_speaker")
            require(
                registry[r["speaker_id"]]["metadata_provenance"]["official_metadata_exact_match"],
                "speaker_metadata_unverified",
            )
            require(r["utterance_id"].startswith(r["speaker_id"]), "source_speaker_mismatch")
            source = Path(r["audio"]["reference"])
            require(
                source.parent.name == r["speaker_id"] and source.stem == r["utterance_id"],
                "source_ownership_mismatch",
            )
            provenance = r["transcript_provenance"]
            lines = source_transcript(
                str(source.parents[3] / provenance["member"]), provenance["sha256"]
            )
            parsed = parse_content(lines[provenance["line"] - 1])
            require(parsed["utterance_id"] == r["utterance_id"], "transcript_source_mismatch")
            require(
                all(r[k] == v for k, v in parsed["units"][r["index"]].items()),
                "corpus_read_label_mismatch",
            )
            require(
                not spans["flags"] and not r["erhua"] and not r["unusual_multi_hanzi"],
                "frozen_quality_flag",
            )
            review = reviewed.get(r["example_id"])
            if review:
                require(review["decision"] == review["final_decision"] == "PASS", "review_failure")
            check = mechanical(r, spans, control=True)
            pool.append(unit_record(r, spans, "control", check, review))
        except ValueError as error:
            failures.append({"unit_id": r["example_id"], "reason": str(error)})
    return (
        sorted(units, key=lambda x: x["unit_id"]),
        sorted(pool, key=lambda x: x["unit_id"]),
        failures,
    )


def duration_bin(unit):
    d = unit["mechanical"]["tone_seconds"]
    return "short" if d <= 0.10 else "medium" if d <= 0.16 else "long"


def select_controls(pool, seed=SEED):
    """Balance frozen corpus classes, speakers, durations and position proxies."""
    rng = random.Random(seed)
    requests = [(tone, i) for tone, count in COUNTS.items() for i in range(count)]
    rng.shuffle(requests)
    chosen, speakers, bases = [], Counter(), Counter()
    used_sources, used_pcm = set(), set()
    for tone, index in requests:
        candidates = [
            u
            for u in pool
            if u["gold"] == tone
            and u["source_id"] not in used_sources
            and u["mechanical"]["source_pcm_sha256"] not in used_pcm
            and speakers[u["speaker_id"]] < 3
        ]
        require(candidates, "control_balance_unavailable")
        target_bin = ("short", "medium", "long")[index % 3]
        target_position = "utterance_edge" if index == 0 else "utterance_medial"
        tie = {u["unit_id"]: rng.random() for u in candidates}
        picked = min(
            candidates,
            key=lambda u: (
                speakers[u["speaker_id"]],
                duration_bin(u) != target_bin,
                u["position"] != target_position,
                bases[u["phonetic_base"]],
                tie[u["unit_id"]],
            ),
        )
        chosen.append(picked)
        speakers[picked["speaker_id"]] += 1
        bases[picked["phonetic_base"]] += 1
        used_sources.add(picked["source_id"])
        used_pcm.add(picked["mechanical"]["source_pcm_sha256"])
    require(Counter(u["gold"] for u in chosen) == COUNTS, "wrong_control_tone_balance")
    require(len(speakers) == 12 and min(speakers.values()) >= 2, "speaker_balance_failed")
    require(
        len({u["mechanical"]["tone_pcm_sha256"] for u in chosen}) == 28, "duplicate_control_pcm"
    )
    return chosen


def randomize(learners, controls, seed=SEED):
    rng = random.Random(seed + 1)
    repeats = [
        rng.choice([u for u in learners if u["source_id"] == source])
        for source in sorted({u["source_id"] for u in learners})
    ]
    require(len(repeats) == 3, "learner_take_count_changed")
    repeats += [rng.choice([u for u in controls if u["gold"] == tone]) for tone in COUNTS]
    presentations = [
        {"unit_id": u["unit_id"], "base_role": u["role"], "role": u["role"]}
        for u in learners + controls
    ]
    presentations += [
        {"unit_id": u["unit_id"], "base_role": u["role"], "role": "repeat"} for u in repeats
    ]
    by_id = {u["unit_id"]: u for u in learners + controls}
    for _attempt in range(200000):
        rng.shuffle(presentations)
        positions = {}
        valid = True
        for i, p in enumerate(presentations):
            u = by_id[p["unit_id"]]
            if p["unit_id"] in positions and i - positions[p["unit_id"]] < MIN_REPEAT_DISTANCE:
                valid = False
                break
            positions[p["unit_id"]] = i
            if i and u["source_id"] == by_id[presentations[i - 1]["unit_id"]]["source_id"]:
                valid = False
                break
            if i > 1 and all(
                by_id[presentations[j]["unit_id"]]["speaker_id"] == u["speaker_id"]
                for j in (i - 2, i - 1)
            ):
                valid = False
                break
        if valid:
            break
    else:
        raise ValueError("cannot_randomize")
    for p in presentations:
        p["annotation_id"] = "A" + f"{rng.getrandbits(80):020x}"
    require(len({p["annotation_id"] for p in presentations}) == 52, "id_collision")
    # Earliest exposure is canonical, even if the shuffled copy arrived first.
    first = {}
    for i, p in enumerate(presentations):
        p["order"] = i + 1
        p["duplicate_of"] = first.get(p["unit_id"])
        p["role"] = "repeat" if p["duplicate_of"] else p["base_role"]
        first.setdefault(p["unit_id"], p["annotation_id"])
    return presentations


def wav_bytes(unit, view):
    pcm, rate, _ = source_audio(unit["source_audio"]["reference"], unit["source_audio"]["sha256"])
    s = unit["spans"][VIEWS[view]]
    raw = pcm[s["start_sample"] : s["end_sample"]]
    if rate != 16000:
        divisor = math.gcd(rate, 16000)
        raw = np.clip(
            np.rint(resample_poly(raw.astype(float), 16000 // divisor, rate // divisor)),
            -32768,
            32767,
        ).astype("<i2")
    stream = io.BytesIO()
    with wave.open(stream, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(raw.astype("<i2").tobytes())
    return stream.getvalue()


def public_manifest(units, order):
    encoded = {
        u["unit_id"]: {
            view: "data:audio/wav;base64," + base64.b64encode(wav_bytes(u, view)).decode("ascii")
            for view in VIEWS
        }
        for u in units
    }
    return {
        "packet_version": VERSION,
        "items": [
            {"annotation_id": p["annotation_id"], "audio": encoded[p["unit_id"]]} for p in order
        ],
    }


def durations(units):
    return {
        view: {
            **dict(
                zip(
                    ("min", "q1", "median", "q3", "max"),
                    np.quantile(
                        [u["mechanical"][view + "_seconds"] for u in units], [0, 0.25, 0.5, 0.75, 1]
                    )
                    .round(6)
                    .tolist(),
                    strict=True,
                )
            ),
            "mean": round(float(np.mean([u["mechanical"][view + "_seconds"] for u in units])), 6),
        }
        for view in VIEWS
    }


def build(destination=OUTPUT):
    verify_inputs()
    require(not (destination / "private/selection.json").exists(), "packet_exists_immutable")
    learners, pool, failures = load_eligible()
    controls = select_controls(pool)
    order = randomize(learners, controls)
    units = learners + controls
    manifest = public_manifest(units, order)
    packet_hash = digest(manifest)
    payload = {**manifest, "packet_sha256": packet_hash}
    selection = {
        "schema": "benma-blind-selection-v1",
        "seed": SEED,
        "packet_sha256": packet_hash,
        "learner_release_sha256": LEARNER_SHA,
        "native_release_sha256": file_hash(NATIVE / "release.json"),
        "units": units,
        "presentation_order": order,
        "eligible_control_count": len(pool),
        "excluded_control_checks": failures,
        "model_results_read_for_selection": False,
        "native_QA_authorization": "User approved frozen release corpus-wide QA acceptance; "
        "individual listening PASS is recorded separately, never inferred.",
        "audio_policy": "Exact frozen source spans; delivery mono PCM16 16000 Hz; "
        "fixed scipy resample_poly where needed; no normalization, denoising or time stretching.",
        "position_limit": "Utterance edge/medial proxy only; "
        "internal phrase boundaries unavailable.",
        "minimum_repeat_distance": MIN_REPEAT_DISTANCE,
        "duration_bins_seconds": {"short": "<=0.10", "medium": "(0.10,0.16]", "long": ">0.16"},
        "mechanical_policy": "Frozen accepted test split; no span flags, erhua or multi-Hanzi; "
        "exact corpus read label, speaker and PCM ownership; no digital saturation (peak<32760); "
        ">0 periodic 40ms frames (60–500Hz autocorrelation>=0.35, energy>=1e-6). "  # noqa: RUF001
        "No new auditory QA; structural checks cannot certify acoustic crop integrity.",
        "summary": {
            "learners": 16,
            "excluded_natural_quarantine": 16,
            "excluded_diagnostic": 12,
            "excluded_unknown_provenance": 79,
            "controls": 28,
            "control_tones": dict(Counter(u["gold"] for u in controls)),
            "control_speakers": dict(sorted(Counter(u["speaker_id"] for u in controls).items())),
            "control_phonetic_bases": len({u["phonetic_base"] for u in controls}),
            "individual_native_PASS": sum(
                u["individual_native_review"] is not None for u in controls
            ),
            "repeats": 8,
            "repeat_learner": 3,
            "repeat_control": 5,
            "presentations": 52,
            "durations_seconds": {"learner": durations(learners), "control": durations(controls)},
            "control_duration_bins": dict(Counter(duration_bin(u) for u in controls)),
            "control_positions": dict(Counter(u["position"] for u in controls)),
        },
    }
    write_json(destination / "private/selection.json", selection)
    # A manifest hash commits to the ordered opaque IDs AND the delivered audio bytes.
    (destination / "private/packet-manifest.json").write_bytes(canonical(manifest) + b"\n")
    write_json(
        destination / "private/selection-seal.json",
        {
            "selection_sha256": file_hash(destination / "private/selection.json"),
            "packet_sha256": packet_hash,
            "manifest_file_sha256": file_hash(destination / "private/packet-manifest.json"),
            "model_outputs_accessed": False,
        },
    )
    template = (PACKAGE / "scripts/blind_review.html").read_text()
    js = (PACKAGE / "scripts/blind_review.js").read_text()
    html = template.replace("__PACKET__", json.dumps(payload, separators=(",", ":"))).replace(
        "__SCRIPT__", js
    )
    qa = destination / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    (qa / "index.html").write_text(html)
    audit = leakage_audit(html, selection)
    write_json(destination / "private/leakage-audit.json", audit)
    return selection["summary"] | {"packet_sha256": packet_hash}


def leakage_audit(html, selection):
    match = re.search(r'<script id="packet" type="application/json">(.*?)</script>', html, re.S)
    require(match is not None, "missing_public_payload")
    packet = json.loads(match[1])
    require(set(packet) == {"packet_version", "packet_sha256", "items"}, "public_top_fields")
    manifest = {k: v for k, v in packet.items() if k != "packet_sha256"}
    require(digest(manifest) == packet["packet_sha256"], "packet_hash_mismatch")
    for item in packet["items"]:
        require(set(item) == {"annotation_id", "audio"}, "public_item_fields")
        require(re.fullmatch(r"A[0-9a-f]{20}", item["annotation_id"]), "nonopaque_id")
        require(set(item["audio"]) == set(VIEWS), "unexpected_audio_view")
        for data in item["audio"].values():
            raw = base64.b64decode(data.removeprefix("data:audio/wav;base64,"), validate=True)
            with wave.open(io.BytesIO(raw)) as stream:
                require(
                    stream.getframerate() == 16000
                    and stream.getnchannels() == 1
                    and stream.getsampwidth() == 2
                    and stream.getnframes() > 0,
                    "bad_public_audio",
                )
            require(raw[12:16] == b"fmt " and raw[36:40] == b"data", "wav_metadata_leak")
    visible_code = html[: match.start(1)] + html[match.end(1) :]
    forbidden = (
        "learner",
        "native",
        "control item",
        "duplicate",
        "source_id",
        "source_audio",
        "expected_surface",
        "pinyin",
        "hanzi",
        "hubert",
        "expanded",
        "pilot",
        "deterministic result",
        "selection.json",
        "answer-key",
        "manifest.json",
        "SSB",
        "/home/",
        "../",
        "http://",
        "https://",
    )
    for word in forbidden:
        require(word.lower() not in visible_code.lower(), "visible_leak:" + word)
    require(not re.search(r"[\u3400-\u9fff]", visible_code), "visible_hanzi")
    for u in selection["units"]:
        require(u["unit_id"] not in html and u["source_id"] not in html, "source_identifier_leak")
    require(not re.search(r'(?:src|href)=["\'](?!data:|#)', visible_code), "external_navigation")
    return {
        "status": "PASS",
        "presentations": len(packet["items"]),
        "audio_views": 104,
        "public_fields_allowlisted": True,
        "embedded_pcm_metadata_stripped": True,
        "external_requests_or_links": 0,
        "identifiers_labels_predictions_roles_and_paths_absent": True,
        "html_sha256": hashlib.sha256(html.encode()).hexdigest(),
        "limits": "Audio can reveal voice or syllable identity; first-pass metadata blindness "
        "does not prevent independent filesystem access or recognition of repeated audio.",
    }


def validate_review(packet, review, *, complete=True):
    """Schema/integrity checks only. No hidden key, accuracy, agreement or model scoring."""
    require(
        set(review) == {"schema", "packet_version", "packet_sha256", "reviewer", "reviews"},
        "export_fields",
    )
    require(review["schema"] == "benma-realized-tone-review-v1", "review_schema")
    for key in ("packet_version", "packet_sha256"):
        require(review[key] == packet[key], key)
    require(isinstance(review["reviewer"], str) and bool(review["reviewer"].strip()), "reviewer")
    ids = [p["annotation_id"] for p in packet["items"]]
    require([r["annotation_id"] for r in review["reviews"]] == ids, "review_id_order")
    for r in review["reviews"]:
        require(
            set(r)
            == {
                "annotation_id",
                "perceived_tone",
                "confidence",
                "usability",
                "tone_bearing_heard",
                "whole_target_heard",
                "timestamp",
            },
            "review_fields",
        )
        require(
            r["perceived_tone"] in CHOICES or (not complete and r["perceived_tone"] is None),
            "perceived_tone",
        )
        require(
            (type(r["confidence"]) is int and 1 <= r["confidence"] <= 5)
            or (not complete and r["confidence"] is None),
            "confidence",
        )
        require(r["usability"] in (None, "CLEAR", "BORDERLINE", "UNUSABLE"), "usability")
        require(
            type(r["tone_bearing_heard"]) is bool and type(r["whole_target_heard"]) is bool,
            "heard_type",
        )
        require(not complete or r["tone_bearing_heard"], "tone_bearing_not_heard")
        require(not r["whole_target_heard"] or r["tone_bearing_heard"], "listening_order")
        timestamp = r["timestamp"]
        if timestamp is None and not complete:
            continue
        require(isinstance(timestamp, str), "timestamp")
        require(
            datetime.fromisoformat(timestamp.replace("Z", "+00:00")).tzinfo is not None,
            "timestamp_timezone",
        )
    return {"status": "VALID_SCHEMA_ONLY", "presentations": len(ids), "scoring_performed": False}


def verify_preservation(destination=OUTPUT):
    starting = read_json(destination / "private/starting-state.json")
    for name, sha in starting["files"].items():
        require(file_hash(ROOT / name) == sha, "preexisting_file_changed:" + name)
    baseline = verify_inputs()
    return {
        "baseline_hashes_unchanged": baseline["verified_files"],
        "preexisting_files_unchanged": len(starting["files"]),
    }
