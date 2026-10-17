"""Diagnose original evidence and build an unanswered Round-2 comparison packet.

No aligner, model, acquisition or release command is invoked. All generated
artifacts are write-once; running build again verifies byte-identical output.
"""

import argparse
import hashlib
import html
import io
import json
import math
import sys
import wave
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import audit, stable_json, stable_rows, verified_packet
from perceptual_tone.aishell3_alignment import textgrid
from perceptual_tone.aishell3_boundaries import POLICY, control_matches, derive, features, span
from perceptual_tone.aishell3_qa import decode, distribution, validate_reviews
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows
from perceptual_tone.manifest import verify_baseline

SCHEMA = "aishell3-playback-round2-comparison-v1"
WHOLE_DECISIONS = ("PASS", "START ISSUE", "END ISSUE", "BOTH", "WRONG UNIT")
FINAL_DECISIONS = ("PASS", "CLIPPED", "CONTAMINATED", "WRONG UNIT", "TOO LITTLE MATERIAL")


def stable_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Existing artifact differs: {path}")
    else:
        path.write_bytes(data)


def export_clip(folder, name, pcm, rate, bounds):
    first, last = bounds["start_sample"], bounds["end_sample"]
    if rate != bounds["sample_rate_hz"] or not 0 <= first < last <= len(pcm):
        raise ValueError("invalid_clip_bounds")
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm[first:last].astype("<i2").tobytes())
    path = folder / name
    stable_bytes(path, stream.getvalue())
    actual, actual_rate, _ = decode(path)
    if actual_rate != rate or not np.array_equal(actual, pcm[first:last]):
        raise ValueError("export_pcm_mismatch")
    if not np.any(actual):
        raise ValueError("all_zero_clip")
    return {
        "reference": name,
        "sha256": file_hash(path),
        **bounds,
        "pcm_sha256": hashlib.sha256(actual.tobytes()).hexdigest(),
    }


def verify_original_media(root, packet):
    result = []
    folder = root / "pilot/audit/review"
    document = (folder / "index.html").read_text()
    for item in packet["items"]:
        row = item["row"]
        pcm, rate, _ = decode(row["audio"]["reference"])
        views = {}
        for view, media in item["playback"].items():
            actual, clip_rate, _ = decode(folder / media["reference"])
            first, last = round(media["start_seconds"] * rate), round(media["end_seconds"] * rate)
            margin = {"target": 0, "context": 0.25, "utterance": None}[view]
            expected = (
                (0, len(pcm))
                if margin is None
                else (
                    max(0, math.floor((row["start"] - margin) * rate)),
                    min(len(pcm), math.ceil((row["end"] + margin) * rate)),
                )
            )
            if (
                (first, last) != expected
                or rate != clip_rate
                or not np.array_equal(actual, pcm[first:last])
                or f'src="{media["reference"]}"' not in document
            ):
                raise ValueError("original_playback_layer_mismatch")
            views[view] = {
                "first_sample": first,
                "end_sample_exclusive": last,
                "pcm_exact": True,
                "html_references_this_wav": True,
                "sha256": media["sha256"],
            }
        result.append({"example_id": row["example_id"], "views": views})
    return result


def render(packet):
    esc = html.escape
    out = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>AISHELL-3 playback QA · Round 2</title>",
        "<style>body{font:16px system-ui;line-height:1.5;max-width:1050px;margin:auto;"
        "padding:24px;background:#f4f6f8;color:#17202a}header,section{background:white;"
        "padding:24px;margin-bottom:24px;border:1px solid #ccd}button,input,select,textarea{"
        "font:inherit;margin:6px;padding:8px}label{display:block}textarea{width:92%}"
        ".players{display:flex;flex-wrap:wrap;gap:16px}.player{display:flex;flex-direction:column}"
        "audio{max-width:100%;width:280px}pre{white-space:pre-wrap}#message{color:#963800}"
        "button{cursor:pointer}code{overflow-wrap:anywhere}</style>",
        "<header><h1>AISHELL-3 playback QA · Round 2</h1>",
        f"<p>{len(packet['items'])} items. Check speech ownership and timing. "
        "Tone labels remain the corpus labels.</p>",
        "<p>Listen to <strong>PLAY CONTEXT</strong>, then "
        "<strong>PLAY ORIGINAL TARGET</strong> (the whole read unit). "
        "Give a boundary decision. Then listen to <strong>PLAY TONE-BEARING TARGET</strong>, "
        "an experimental vowel and ending crop. It intentionally omits the initial consonant "
        "and any medial glide. Give a separate final-ownership decision. "
        "Use the full utterance whenever needed.</p>",
        "<p><strong>Whole-unit PASS:</strong> intended unit, plausible start and end, "
        "no obvious neighboring speech or clipping. <strong>Final PASS:</strong> "
        "the vowel and ending belong to this target, remain complete enough to inspect, "
        "and contain no obvious neighbor. If too short to assess, select TOO LITTLE MATERIAL. "
        "A final PASS does not erase a whole-unit failure. "
        "Describe which edge and sound is affected in the notes.</p>",
        "<p>These are candidate representations. "
        "Review does not release data or start training.</p>",
        '<label>Your name <input id="reviewer" autocomplete="name"></label>'
        '<p id="progress" role="status"></p>',
        '<button id="export">EXPORT COMPLETE DECISIONS</button>'
        '<button id="draft">EXPORT DRAFT</button>',
        '<label>Import saved JSON <input id="import" type="file" '
        'accept="application/json,.json"></label>',
        '<p id="message" role="status" aria-live="polite"></p></header>',
    ]
    for item in packet["items"]:
        row, s = item["row"]["original"], item["row"]["spans"]

        def neighbor(n):
            return esc(n["hanzi"] + " " + n["corpus_pinyin"]) if n else "—"

        final = s["tone_bearing_pooling_span"]
        out += [
            f'<section data-id="{esc(row["example_id"])}"><h2>{item["item"]} · '
            f"{esc(row['hanzi'])} {row['corpus_pinyin']} ({row['label']})</h2>",
            f"<p><code>{row['example_id']}</code><br>Speaker {row['speaker_id']} · "
            f"utterance {row['utterance_id']}<br>{esc(row['transcript'])}</p>",
            f"<p>{neighbor(row['preceding'])} → <strong>{esc(row['hanzi'])}</strong> → "
            f"{neighbor(row['following'])}</p>",
            f"<p>Whole unit {row['start']:.3f}&ndash;{row['end']:.3f} s; experimental final "
            f"{final['start_seconds']:.3f}&ndash;{final['end_seconds']:.3f} s.</p>"
            '<div class="players">',
        ]
        names = {
            "context": "CONTEXT",
            "target": "ORIGINAL TARGET",
            "final": "TONE-BEARING TARGET",
            "utterance": "UTTERANCE",
        }
        for view in ("context", "target", "final", "utterance"):
            out.append(
                f'<div class="player"><button data-view="{view}">PLAY {names[view]}</button>'
                f'<audio data-view="{view}" controls preload="none" '
                f'aria-label="{item["item"]} {view}" '
                f'src="{item["playback"][view]["reference"]}"></audio></div>'
            )
        out.append("</div>")
        for key, label, choices in (
            ("decision", "Whole-unit boundary decision", WHOLE_DECISIONS),
            ("final_decision", "Experimental final ownership", FINAL_DECISIONS),
        ):
            out.append(
                f'<label>{label} <select data-field="{key}">'
                '<option value="">Choose a decision</option>'
                + "".join(f"<option>{d}</option>" for d in choices)
                + "</select></label>"
            )
        out += [
            '<label><input type="checkbox">I listened to context, target and final '
            "and checked their ownership.</label>",
            "<label>Notes (required if either decision is non-PASS)"
            '<textarea rows="3"></textarea></label>',
            "<details><summary>Aligned phone evidence</summary><pre>"
            + esc(json.dumps(row["aligned_phones"], ensure_ascii=False, indent=2))
            + "</pre></details></section>",
        ]
    out += [
        '<script id="packet" type="application/json">'
        + json.dumps(packet, ensure_ascii=False).replace("<", "\\u003c")
        + "</script>",
        "<script>"
        + (PACKAGE / "scripts/aishell3_round2_review.js").read_text()
        + "</script></html>",
    ]
    return ("\n".join(out) + "\n").encode()


def build(root, output):
    baseline = verify_baseline()
    original_auto = audit(root, scaled=True)
    packet = verified_packet(root)
    reviews = read_rows(root / "continuation/playback-decisions.jsonl")
    if any(r["packet_sha256"] != packet["packet_sha256"] for r in reviews):
        raise ValueError("round1_wrong_packet")
    _, human = validate_reviews(packet["items"], reviews, complete=True)
    if Counter(r["decision"] for r in reviews) != {"PASS": 18, "BOUNDARY EARLY": 7, "OTHER": 1}:
        raise ValueError("unexpected_round1_decisions")
    stable_json(output / "round1-status.json", human)
    media_evidence = verify_original_media(root, packet)
    stable_json(output / "original-media-audit.json", media_evidence)
    rows = read_rows(root / "continuation/scaled-candidates.jsonl")
    originals = {r["example_id"]: r for r in rows}
    old_items = {i["row"]["example_id"]: i for i in packet["items"]}
    notes = read_json(PACKAGE / "annotations/aishell3-round1-diagnostics.json")["items"]
    failures = [originals[r["example_id"]] for r in reviews if r["decision"] != "PASS"]
    passes = [originals[r["example_id"]] for r in reviews if r["decision"] == "PASS"]
    if set(notes) != {r["example_id"] for r in failures}:
        raise ValueError("diagnostic_inventory_incomplete")
    audio, records, changed_samples = {}, [], []
    for row in rows:
        utterance = row["utterance_id"]
        if utterance not in audio:
            audio[utterance] = decode(row["audio"]["reference"])
        pcm, rate, _ = audio[utterance]
        s = derive(row, rate, len(pcm))
        if s != derive(row, rate, len(pcm)):
            raise ValueError("nondeterministic_span_derivation")
        # Preserve the exact context heard in round 1 for all 26 comparisons.
        # Contexts intentionally overlap; the shared-boundary fix concerns targets.
        if row["example_id"] in old_items:
            old_context = old_items[row["example_id"]]["playback"]["context"]
            s["context"] = {
                "start_sample": round(old_context["start_seconds"] * rate),
                "end_sample": round(old_context["end_seconds"] * rate),
                "sample_rate_hz": rate,
                "start_seconds": old_context["start_seconds"],
                "end_seconds": old_context["end_seconds"],
                "endpoint_convention": "half_open",
            }
            s["context_reason"] = "exact_round1_context_retained_for_comparison"
        name = f"{utterance}-{row['index']:03d}"
        media = {
            view: export_clip(output, f"audio/{name}-{view}.wav", pcm, rate, s[key])
            for view, key in (
                ("target", "playback_read_unit"),
                ("final", "tone_bearing_pooling_span"),
                ("context", "context"),
            )
            if s[key] is not None
        }
        if (
            row["example_id"] in old_items
            and media["context"]["sha256"]
            != old_items[row["example_id"]]["playback"]["context"]["sha256"]
        ):
            raise ValueError("round1_context_changed")
        old = (math.floor(row["start"] * rate), math.ceil(row["end"] * rate))
        new = (s["playback_read_unit"]["start_sample"], s["playback_read_unit"]["end_sample"])
        delta = (new[0] - old[0], new[1] - old[1])
        if old != new:
            changed_samples.append(
                {
                    "example_id": row["example_id"],
                    "start_delta_samples": delta[0],
                    "end_delta_samples": delta[1],
                }
            )
        records.append(
            {
                "example_id": row["example_id"],
                "original": row,
                "spans": s,
                "media": media,
                "sample_delta": list(delta),
                "eligible_for_training": False,
            }
        )
    by_id = {r["example_id"]: r for r in records}
    # Include rejected neighbors when checking the complete utterance ordering.
    all_units = rows + read_rows(root / "continuation/scaled-rejected.jsonl")
    by_position = {(r["utterance_id"], r["index"]): r for r in all_units}
    overlaps = 0
    for row in rows:
        prev = by_position.get((row["utterance_id"], row["index"] - 1))
        if prev:
            pcm, rate, _ = audio[row["utterance_id"]]
            left = span(prev["start"], prev["end"], rate, len(pcm))
            right = by_id[row["example_id"]]["spans"]["playback_read_unit"]
            if left["end_sample"] > right["start_sample"]:
                raise ValueError("derived_unit_overlap")
            overlaps += math.ceil(prev["end"] * rate) > math.floor(row["start"] * rate)
    comparisons = {r["example_id"]: control_matches(r, passes) for r in failures}
    inventory = []
    for row in failures:
        key = row["example_id"]
        review = next(r for r in reviews if r["example_id"] == key)
        path = root / "pilot/aligned" / row["speaker_id"] / (row["utterance_id"] + ".TextGrid")
        tiers = textgrid(path.read_text())
        word = next(w for w in tiers["words"] if w[:2] == (row["start"], row["end"]))
        own = [
            {"start": a, "end": b, "phone": p}
            for a, b, p in tiers["phones"]
            if a >= row["start"] and b <= row["end"]
        ]
        if own != row["aligned_phones"]:
            raise ValueError("raw_phone_ownership_changed")
        prev = by_position.get((row["utterance_id"], row["index"] - 1))
        nxt = by_position.get((row["utterance_id"], row["index"] + 1))
        inventory.append(
            {
                "example_id": key,
                "speaker": row["speaker_id"],
                "utterance": row["utterance_id"],
                "target_read_unit": row["hanzi"],
                "previous_read_unit": row["preceding"],
                "next_read_unit": row["following"],
                "target_pinyin": row["corpus_pinyin"],
                "corpus_tone": row["label"],
                "human_review": review,
                **notes[key],
                "features": features(row),
                "controls": comparisons[key][:3],
                "stages": {
                    "A_mfa": {
                        "path": str(path),
                        "sha256": file_hash(path),
                        "word_interval": list(word),
                        "phones": own,
                        "previous_phone": prev["aligned_phones"][-1] if prev else None,
                        "next_phone": nxt["aligned_phones"][0] if nxt else None,
                        "previous_phones": prev["aligned_phones"] if prev else [],
                        "next_phones": nxt["aligned_phones"] if nxt else [],
                    },
                    "B_reconstruction": {
                        "start": row["start"],
                        "end": row["end"],
                        "phones_exact": True,
                    },
                    "C_stored_round1": {
                        k: old_items[key]["row"][k] for k in ("start", "end", "aligned_phones")
                    },
                    "D_original_export": next(m for m in media_evidence if m["example_id"] == key),
                    "E_browser": "Standalone WAV at currentTime=0, no utterance seek or dynamic "
                    "endpoint; see browser audit for decoding checks.",
                },
                "derived": by_id[key]["spans"],
                "sample_delta": by_id[key]["sample_delta"],
                "remaining_status": "Unresolved human non-PASS; no automatic reversal.",
                "candidate_limit": "Nucleus+coda removes onset/medial only; the original end "
                "is unchanged. It cannot restore clipped finals or certify acoustic ownership.",
            }
        )
    # Keep short PASS outliers; maximize phonetic coverage, then matching quality.
    # Only 18 choose 8 subsets: exact deterministic selection is cheap here.
    control_features = {r["example_id"]: features(r) for r in passes}
    mandatory = {r["example_id"] for r in passes if by_id[r["example_id"]]["spans"]["flags"]}
    scores = [{m["example_id"]: m["score"] for m in matches} for matches in comparisons.values()]

    def control_score(group):
        coverage = sum(
            len({control_features[k][field] for k in group})
            for field in ("initial_class", "final_class")
        )
        return coverage, sum(max(score[k] for k in group) for score in scores)

    control_ids = list(
        max(
            (
                group
                for group in combinations(sorted(control_features), 8)
                if mandatory.issubset(group)
            ),
            key=control_score,
        )
    )
    selected = {r["example_id"] for r in failures} | set(control_ids)
    outliers = sorted(
        [
            r
            for r in records
            if r["spans"]["available"] and r["spans"]["flags"] and r["example_id"] not in selected
        ],
        key=lambda r: (
            r["spans"]["tone_bearing_pooling_span"]["end_sample"]
            - r["spans"]["tone_bearing_pooling_span"]["start_sample"],
            r["example_id"],
        ),
    )[:2]
    selected |= {r["example_id"] for r in outliers}
    selected_ids = sorted(selected, key=lambda key: digest(["round2-blind-order-v1", key]))
    items = []
    for number, key in enumerate(selected_ids, 1):
        record = by_id[key]
        pcm, rate, _ = audio[record["original"]["utterance_id"]]
        utterance = export_clip(
            output,
            f"audio/{record['original']['utterance_id']}-utterance.wav",
            pcm,
            rate,
            span(0, len(pcm) / rate, rate, len(pcm)),
        )
        playback = {**record["media"], "utterance": utterance}
        # Bind both representations and media hashes, not just the original row.
        bound_row = {
            "example_id": key,
            "original": record["original"],
            "spans": record["spans"],
            "playback": playback,
        }
        items.append(
            {
                "item": f"item-{number:02d}",
                "row": bound_row,
                "item_sha256": digest(bound_row),
                "playback": playback,
            }
        )
    payload = {
        "schema": SCHEMA,
        "policy": POLICY,
        "decisions": list(WHOLE_DECISIONS),
        "final_decisions": list(FINAL_DECISIONS),
        "items": items,
    }
    round2 = {**payload, "packet_sha256": digest(payload)}
    group_stats = {}
    for group, subset in (
        ("failed", failures),
        ("pass_controls", passes),
        ("all_candidates", rows),
    ):
        keys = {r["example_id"] for r in subset}
        recs = [r for r in records if r["example_id"] in keys]
        group_stats[group] = {
            "count": len(subset),
            "initial_classes": dict(Counter(features(r)["initial_class"] for r in subset)),
            "final_classes": dict(Counter(features(r)["final_class"] for r in subset)),
            "sample_only_changes": sum(r["sample_delta"] != [0, 0] for r in recs),
            "final_start_changes": sum(
                r["spans"]["tone_bearing_pooling_span"]["start_sample"]
                != r["spans"]["playback_read_unit"]["start_sample"]
                for r in recs
                if r["spans"]["available"]
            ),
            "final_end_changes": 0,
            "short_final_flags": sum(
                "experimental_final_under_60ms" in r["spans"]["flags"] for r in recs
            ),
        }
    summary = {
        "policy": POLICY,
        "status": "BLOCKED_PENDING_ROUND2_HUMAN_REVIEW",
        "training_run": False,
        "released": False,
        "ml_target_changed": False,
        "round1": {"total": 26, "pass": 18, "boundary_early": 7, "other": 1, "gate": "failed"},
        "original_automatic_qa": original_auto["automatic_qa"],
        "full_candidates": len(rows),
        "original_quarantines_unchanged": len(all_units) - len(rows),
        "all_labels_and_original_spans_preserved": True,
        "clips_decoded_and_pcm_verified": sum(len(r["media"]) for r in records),
        "tone_bearing_derivable": sum(r["spans"]["available"] for r in records),
        "tone_bearing_unavailable": sum(not r["spans"]["available"] for r in records),
        "derivable_by_tone": dict(
            Counter(r["original"]["label"] for r in records if r["spans"]["available"])
        ),
        "root_cause_counts": dict(Counter(n["root_cause_classification"] for n in notes.values())),
        "original_clips_verified": sum(len(m["views"]) for m in media_evidence),
        "old_adjacent_sample_overlaps": overlaps,
        "new_adjacent_sample_overlaps": 0,
        "sample_changed_units": len(changed_samples),
        "maximum_edge_change_samples": max(abs(d) for r in records for d in r["sample_delta"]),
        "groups": group_stats,
        "duration_seconds": {},
        "short_final_outliers": [r["example_id"] for r in records if r["spans"]["flags"]],
        "round2_items": len(items),
        "round2_controls": len(control_ids),
        "round2_new_outliers": len(outliers),
        "round2_html": str((output / "index.html").resolve()),
        "packet_sha256": round2["packet_sha256"],
        "baseline": baseline,
        "rule_deterministic": True,
    }
    for field in ("playback_read_unit", "tone_bearing_pooling_span", "context"):
        summary["duration_seconds"][field] = distribution(
            [
                (r["spans"][field]["end_sample"] - r["spans"][field]["start_sample"])
                / r["spans"][field]["sample_rate_hz"]
                for r in records
                if r["spans"][field] is not None
            ]
        )
    stable_rows(output / "derived-candidates.jsonl", records)
    stable_rows(output / "failure-inventory.jsonl", inventory)
    stable_json(output / "control-comparisons.json", comparisons)
    stable_json(output / "sample-corrections.json", changed_samples)
    stable_rows(
        output / "reviewed26-candidate-effects.jsonl",
        [{"human_review": r, "candidate": by_id[r["example_id"]]} for r in reviews],
    )
    stable_json(
        output / "private-selection.json",
        {
            "failures": [r["example_id"] for r in failures],
            "controls": control_ids,
            "outliers": [r["example_id"] for r in outliers],
            "order": selected_ids,
        },
    )
    stable_json(output / "packet.json", round2)
    stable_bytes(output / "index.html", render(round2))
    stable_json(output / "summary.json", summary)
    return summary


def ingest_round2(folder, source, destination):
    packet = read_json(folder / "packet.json")
    if packet["schema"] != SCHEMA or packet["packet_sha256"] != digest(
        {k: v for k, v in packet.items() if k != "packet_sha256"}
    ):
        raise ValueError("invalid_round2_packet")
    for item in packet["items"]:
        if (
            item["item_sha256"] != digest(item["row"])
            or item["row"]["playback"] != item["playback"]
        ):
            raise ValueError("round2_item_changed")
        for media in item["playback"].values():
            path = (folder / media["reference"]).resolve()
            if not path.is_relative_to(folder.resolve()) or file_hash(path) != media["sha256"]:
                raise ValueError("round2_media_changed")
    raw = read_json(source)
    if raw.get("schema") != SCHEMA or raw.get("packet_sha256") != packet["packet_sha256"]:
        raise ValueError("wrong_round2_packet")
    reviews = raw.get("reviews", [])
    # Reuse identity/timestamp/hash validation without reinterpreting saved verdicts.
    if any(r.get("decision") not in WHOLE_DECISIONS for r in reviews):
        raise ValueError("invalid_whole_unit_decision")
    validation_only = [
        {**r, "decision": "PASS" if r["decision"] == "PASS" else "OTHER"} for r in reviews
    ]
    validate_reviews(packet["items"], validation_only, complete=True)
    whole = {"decisions": dict(Counter(r["decision"] for r in reviews))}
    for r in reviews:
        if r.get("final_decision") not in FINAL_DECISIONS or r.get("heard_final") is not True:
            raise ValueError("final_review_required")
        if r["final_decision"] != "PASS" and not r.get("notes", "").strip():
            raise ValueError("nonpass_final_requires_notes")
    stable_rows(destination, [{**r, "packet_sha256": packet["packet_sha256"]} for r in reviews])
    return {
        "status": "INGESTED_ONLY_NOT_RELEASED",
        "whole_unit_review": whole,
        "final_decisions": dict(Counter(r["final_decision"] for r in reviews)),
        "training_run": False,
        "released": False,
        "next_step": "Developer adjudicates prior failures, any quarantine, and control "
        "regressions. Trustworthy tone-bearing spans may pass despite fuzzy whole-unit onsets.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "ingest"))
    parser.add_argument("--root", type=Path, default=PACKAGE / "data/generated/aishell3")
    parser.add_argument("--folder", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    folder = args.folder or args.root / "round2-final"
    if args.action == "build":
        result = build(args.root, folder)
    else:
        if not args.input or not args.output:
            parser.error("ingest requires --input and --output")
        result = ingest_round2(folder, args.input, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
