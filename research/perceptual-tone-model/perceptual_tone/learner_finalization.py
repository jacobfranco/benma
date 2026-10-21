"""Finalize existing learner artifacts only: no discovery, alignment, training or scoring."""

import html
import os
import shutil
import wave
from collections import Counter, defaultdict
from datetime import datetime

from .common import PACKAGE, ROOT, digest, file_hash, read_json, read_rows, write_json, write_rows
from .learner_benchmark import DEFAULT as CONSTRUCTION
from .learner_benchmark import TONE, WHOLE, verify_inputs, walk

DEFAULT = PACKAGE / "data/generated/learner-alignment-review-v2"
NATURAL = "PRIMARY_NATURAL_CANDIDATE"
DIAGNOSTIC = "DOCUMENTED_DIAGNOSTIC"
UNKNOWN = "UNKNOWN_PROVENANCE"
CONTROL = "CONTROL"
UNUSABLE = "UNUSABLE"
SEED = "learner-alignment-review-v2-20261019"
REVIEW_FLAGS = {
    "experimental_final_under_60ms",
    "implausible_read_unit_duration",
    "extreme_phone_duration",
    "historical_ASR_disagrees_with_documented_reading",
    "collapsed_phone_durations",
}
CONFIG = PACKAGE / "configs/learner-benchmark.json"


def stable(path, value, rows=False):
    if path.exists():
        prior = read_rows(path) if rows else read_json(path)
        if prior != value:
            raise ValueError("existing_artifact_differs_use_new_version:" + str(path))
    else:
        (write_rows if rows else write_json)(path, value)


def category(source):
    if source["known_control"]:
        return CONTROL
    return {"natural": NATURAL, "diagnostic": DIAGNOSTIC}.get(source["role"], UNKNOWN)


def structural_issues(unit):
    """Duration/ASR flags do not decide alignment correctness."""
    problems = [f for f in unit["flags"] if f not in REVIEW_FLAGS]
    spans = unit.get("spans")
    if not spans or not spans.get("available"):
        return sorted(set([*problems, "no_owned_tone_bearing_span"]))
    whole, tone, context = (
        spans[k] for k in ["playback_read_unit", "tone_bearing_pooling_span", "context"]
    )
    if not (
        0
        <= context["start_sample"]
        <= whole["start_sample"]
        <= tone["start_sample"]
        < tone["end_sample"]
        == whole["end_sample"]
        <= context["end_sample"]
    ):
        problems.append("invalid_nested_sample_ownership")
    phones = unit["aligned_phones"]
    if not phones or phones[0]["start"] != unit["start"] or phones[-1]["end"] != unit["end"]:
        problems.append("incomplete_phone_ownership")
    for i, p in enumerate(phones):
        if p["start"] >= p["end"] or (i and phones[i - 1]["end"] != p["start"]):
            problems.append("phone_gap_or_overlap")
    return sorted(set(problems))


def extract_dates(source, documents):
    hashes = {s["sha256"] for s in source["sources"]}
    dates = []
    for ref in source["provenance"]:
        p = ROOT / ref["path"]
        if file_hash(p) != ref["sha256"]:
            raise ValueError("historical_provenance_changed")
        if str(p) not in documents:
            documents[str(p)] = read_json(p)
        for node in walk(documents[str(p)]):
            if node.get("sha256") in hashes and node.get("created_at"):
                candidate = {
                    "value": node["created_at"],
                    "event": "audio_asset_created_at",
                    "asset_kind": node.get("kind"),
                    "source": ref,
                    "limitation": "stored upload/canonicalization time, not exact microphone start",
                }
                if candidate not in dates:
                    dates.append(candidate)
    return sorted(
        dates, key=lambda d: (d["asset_kind"] != "original", d["value"], d["source"]["path"])
    )


def master_inventory(inventory, candidates, config):
    selected = {u["source_recording_id"] for u in candidates}
    documents = {}
    result = []
    for source in inventory:
        cat = category(source)
        documented_human = cat in (NATURAL, DIAGNOSTIC) or any(
            n.startswith(prefix)
            for n in source["names"]
            for prefix in config["human_intent_unconfirmed"]
        )
        control_type = None
        if cat == CONTROL:
            reason = source["role_reason"].lower()
            control_type = (
                "no_speech"
                if "no-speech" in reason
                else "tts_noise_playback"
                if "noise" in reason
                else "tts_playback"
            )
        dates = extract_dates(source, documents)
        units = [u for u in candidates if u["source_recording_id"] == source["recording_id"]]
        structural = sorted({f for u in units for f in structural_issues(u)})
        material = cat
        unusable_reasons = []
        if not source["audio_exists"]:
            unusable_reasons.append("missing_source_audio")
        if not source["phrase_reconstructable"]:
            unusable_reasons.append("missing_recoverable_transcript")
        if structural:
            unusable_reasons.extend(structural)
        if unusable_reasons and cat != CONTROL:
            material = UNUSABLE
        result.append(
            {
                **source,
                "source_id": source["recording_id"],
                "provenance_category": cat,
                "material_category": material,
                "speaker": "jacob" if documented_human else None,
                "human_control_status": "human" if documented_human else control_type or "unknown",
                "capture_date": dates[0] if dates else None,
                "capture_date_evidence": dates,
                "capture_intent": source["role_reason"]
                if cat in (NATURAL, DIAGNOSTIC, CONTROL)
                else None,
                "intent_status": cat,
                "independent_source": True,
                "is_derivative": False,
                "parent_source_id": None,
                "alignment_eligibility": "ALIGNED_PENDING_QA"
                if units
                else "NOT_SELECTED_CONTROL"
                if cat == CONTROL
                else "INELIGIBLE_MISSING_MATERIAL"
                if unusable_reasons
                else "NOT_SELECTED_UNKNOWN_PROVENANCE",
                "primary_benchmark_candidate": cat == NATURAL and not unusable_reasons,
                "benchmark_eligibility": "PENDING_ALIGNMENT_QA"
                if cat == NATURAL
                else "SUPPLEMENTAL_DIAGNOSTIC_ONLY"
                if cat == DIAGNOSTIC
                else "CONTROL_EXCLUDED"
                if cat == CONTROL
                else "PROVENANCE_HOLD",
                "hold_reasons": unusable_reasons
                + (
                    ["UNKNOWN — no historical evidence establishes natural vs diagnostic intent"]
                    if cat == UNKNOWN
                    else ["documented control; not learner speech"]
                    if cat == CONTROL
                    else []
                ),
                "selected_for_QA": source["recording_id"] in selected,
                "selected_unit_count": len(units),
                "structural_violations": structural,
            }
        )
    return sorted(result, key=lambda r: r["source_id"])


def lineage(inventory, artifacts):
    """Complete graph from saved discovery records; no new audio/archive search."""
    byte_groups = defaultdict(list)
    for a in artifacts:
        byte_groups[a["sha256"]].append(a["path"])
    clips = {a["sha256"]: a for a in artifacts if a["relationship"] == "exact_pcm_derivative"}
    source_paths = {a["path"]: r["source_id"] for r in inventory for a in r["sources"]}
    nodes = [
        {
            "id": "source:" + r["source_id"],
            "kind": "independent_source",
            "provenance_category": r["provenance_category"],
        }
        for r in inventory
    ]
    edges = []
    for a in sorted(artifacts, key=lambda a: a["path"]):
        node = {
            "id": "audio:" + a["path"],
            "path": a["path"],
            "sha256": a["sha256"],
            "kind": "audio_artifact",
            "source_id": a["recording_id"],
        }
        nodes.append(node)
        if a["sha256"] in clips:
            parent = clips[a["sha256"]]
            edges.append(
                {
                    "from": "source:" + parent["recording_id"],
                    "to": node["id"],
                    "relation": "exact_pcm_clip_or_copy_of_clip",
                    "start_sample_16k": parent["source_start_sample_16k"],
                }
            )
        elif a["recording_id"]:
            edges.append(
                {
                    "from": "source:" + a["recording_id"],
                    "to": node["id"],
                    "relation": "original_or_canonical_representation"
                    if a["path"] in source_paths
                    else "source_equivalent_or_exact_copy",
                    "discovery_relation": a["relationship"],
                }
            )
    for sha, paths in sorted(byte_groups.items()):
        if len(paths) > 1:
            first, *rest = sorted(paths)
            edges.extend(
                {
                    "from": "audio:" + first,
                    "to": "audio:" + p,
                    "relation": "byte_identical",
                    "sha256": sha,
                }
                for p in rest
            )
    metadata = {}
    for r in inventory:
        for p in r["provenance"]:
            ident = "metadata:" + p["path"]
            metadata[ident] = {"id": ident, "kind": "analysis_or_historical_metadata", **p}
            edges.append(
                {
                    "from": "source:" + r["source_id"],
                    "to": ident,
                    "relation": "historical_metadata_reference",
                }
            )
    nodes.extend(metadata.values())
    return {
        "schema": "learner-source-lineage-v2",
        "nodes": sorted(nodes, key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["from"], e["to"], e["relation"])),
        "counts": {
            "independent_source_roots": len(inventory),
            "audio_artifacts": len(artifacts),
            "exact_duplicate_groups": sum(len(v) > 1 for v in byte_groups.values()),
            "exact_duplicate_copies_beyond_first": sum(len(v) - 1 for v in byte_groups.values()),
            "whole_source_byte_different_representations_beyond_first": sum(
                len({a["sha256"] for a in r["sources"]}) - 1 for r in inventory
            ),
            "exact_pcm_clip_contents": len(clips),
            "clip_or_clip_copy_artifacts": sum(a["sha256"] in clips for a in artifacts),
            "additional_pcm_duplicate": sum(
                a["relationship"] == "pcm_duplicate" for a in artifacts
            ),
            "unlinked_control_reference_assistant_artifacts": sum(
                a["relationship"] == "generated_reference_or_assistant" for a in artifacts
            ),
            "unlinked_research_artifacts": sum(
                a["relationship"] == "unlinked_research_artifact" for a in artifacts
            ),
        },
    }


def distribution(units, field):
    counts = Counter(u[field] for u in units)
    return {
        **{f"T{i}": counts[i] for i in range(1, 5)},
        "neutral": counts[5],
        "unresolved_or_unknown": counts[None],
    }


def compile_candidates(old_units, master):
    indexed = {r["source_id"]: r for r in master}
    result = []
    for old in old_units:
        r = indexed[old["source_recording_id"]]
        structural = structural_issues(old)
        result.append(
            {
                **old,
                "source_id": r["source_id"],
                "provenance_category": r["provenance_category"],
                "material_category": r["material_category"],
                "human_control_status": r["human_control_status"],
                "speaker_id": r["speaker"],
                "provenance_status": r["provenance_category"],
                "primary_natural_candidate": r["provenance_category"] == NATURAL,
                "selection": "primary_natural_candidate"
                if r["provenance_category"] == NATURAL
                else "supplemental",
                "alignment_status": "STRUCTURAL_VIOLATION"
                if structural
                else "STRUCTURALLY_VALID_QA_PENDING",
                "structural_violations": structural,
                "reconstruction_status": "structurally_invalid"
                if structural
                else "structurally_valid_qa_pending",
                "exclusion_reasons": structural,
                "historical_reconstruction_flags": old["exclusion_reasons"],
                "alignment_flags": old["flags"],
                "alignment_quarantined": bool(structural),
                "provenance_hold": r["provenance_category"] == UNKNOWN,
                "qa_status": "PENDING",
                "alignment_qa": None,
                "status": "PENDING",
                "eligible_for_training": False,
                "eligible_for_evaluation": False,
                "source_lineage_node": "source:" + r["source_id"],
                "historical_role": r["capture_intent"],
                "historical_benma_reference": str(
                    (CONSTRUCTION / "historical-benma.jsonl").relative_to(ROOT)
                ),
                "realized_tone_ground_truth": None,
                "model_prediction": None,
                "human_perceptual_judgment": None,
            }
        )
    return sorted(result, key=lambda r: r["example_id"])


def make_packet(units, old_packet, candidate_hash):
    old_items = {i["example_id"]: i for i in old_packet["items"]}
    ordered = sorted(units, key=lambda u: digest([SEED, u["example_id"]]))
    items = []
    for n, u in enumerate(ordered, 1):
        prior = old_items[u["example_id"]]
        item = {
            "item_id": f"Q{n:03d}",
            "unit_id": u["example_id"],
            "source_id": u["source_id"],
            "original_qa_item_id": prior["item_id"],
            "phrase": prior["phrase"],
            "hanzi": prior["hanzi"],
            "pinyin": prior["pinyin"],
            "index": prior["index"],
            "clips": prior["clips"],
            "provenance_category": u["provenance_category"],
            "alignment_flags": u["alignment_flags"],
            "structurally_valid": not u["structural_violations"],
            "source_audio_sha256": prior["source_audio_sha256"],
        }
        item["item_sha256"] = digest(item)
        items.append(item)
    packet = {
        "schema": "learner-alignment-qa-v2",
        "version": SEED,
        "items": items,
        "whole_choices": WHOLE,
        "tone_choices": TONE,
        "candidate_manifest_sha256": candidate_hash,
        "order_policy": "deterministic hash order independent of provenance, flags and predictions",
        "order_seed": SEED,
        "purpose": "alignment_integrity_only",
        "export_filename": "benma-learner-alignment-qa.json",
    }
    packet["packet_sha256"] = digest(packet)
    return packet


def render(root, packet):
    cards = []
    for item in packet["items"]:
        clips = []
        for view, label in [
            ("context", "CONTEXT"),
            ("whole", "WHOLE TARGET"),
            ("tone", "TONE-BEARING TARGET"),
        ]:
            url = os.path.relpath(ROOT / item["clips"][view]["path"], root / "qa")
            clips.append(
                f'<button data-play="{view}">PLAY {label}</button>'
                f'<audio preload="none" data-view="{view}" src="{html.escape(url)}"></audio>'
            )
        choices = "".join(
            f'<label>{label}<select data-decision="{key}"><option value="">Choose…</option>'
            + "".join(f"<option>{choice}</option>" for choice in options)
            + "</select></label>"
            for label, key, options in [
                ("WHOLE TARGET", "whole", WHOLE),
                ("TONE-BEARING TARGET", "tone", TONE),
            ]
        )
        cards.append(
            f'<section data-id="{item["item_id"]}"><h2>{item["item_id"]} · '
            f"{html.escape(item['phrase'])} · target {item['index'] + 1}: "
            f"<b>{html.escape(item['hanzi'])}</b> ({html.escape(item['pinyin'])})</h2>"
            f'<p class="identity">Take {item["source_id"]} · {item["provenance_category"]}</p>'
            + "".join(clips)
            + choices
            + '<label><input type="checkbox" data-heard> '
            "All three playback events recorded (optional provenance)</label>"
            "<label>Boundary/ownership notes"
            "<textarea></textarea></label></section>"
        )
    # Retain the page layout; preserve flags in metadata without visible badness labels.
    old_html = (CONSTRUCTION / "qa/index.html").read_text()
    header = old_html[: old_html.index("<section data-id=")]
    header = header.replace(
        "Some historical takes remain outside the benchmark pending provenance.",
        "Small coarticulatory onset differences alone are not failures. "
        "Check the vowel/final for clipping or wrong-unit material. "
        "TOO LITTLE MATERIAL means insufficient trustworthy target nucleus/coda evidence.",
    )
    header = header.replace('<div id="status"', '<p id="progress"></p><div id="status"')
    header = header.replace(
        "Listen to context, whole target, and tone-bearing target.",
        "Judge the whole target and tone-bearing target. Context playback is optional. "
        "Playback telemetry is provenance only and does not determine completion.",
    )
    header = header.replace("h2{overflow-wrap:anywhere}", "h2,.identity{overflow-wrap:anywhere}")
    encoded = __import__("json").dumps(packet, ensure_ascii=False).replace("<", "\\u003c")
    content = (
        header + "".join(cards) + f'<script id="packet" type="application/json">{encoded}</script>'
        '<script src="review.js"></script></html>'
    )
    target = root / "qa/index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_text() != content:
        raise ValueError("existing_review_page_differs_use_new_version")
    if not target.exists():
        target.write_text(content)
    script = PACKAGE / "scripts/learner_review_v2.js"
    if (root / "qa/review.js").exists() and file_hash(root / "qa/review.js") != file_hash(script):
        raise ValueError("existing_review_script_differs_use_new_version")
    if not (root / "qa/review.js").exists():
        shutil.copyfile(script, root / "qa/review.js")


def diagnostic_rows(units):
    return [
        {
            "unit_id": u["example_id"],
            "take_id": u["source_id"],
            "target": u["hanzi"],
            "intended_pinyin": u["intended_pinyin"],
            "alignment_pinyin": u["alignment_pinyin"],
            "flags": u["alignment_flags"],
            "whole_duration_seconds": u["end"] - u["start"],
            "tone_bearing_duration_seconds": (
                u["spans"]["tone_bearing_pooling_span"]["end_sample"]
                - u["spans"]["tone_bearing_pooling_span"]["start_sample"]
            )
            / 16000,
            "prompt_ASR_disagreement": "historical_ASR_disagrees_with_documented_reading"
            in u["alignment_flags"],
            "structurally_valid": not u["structural_violations"],
            "human_review_required": True,
            "alignment_quarantined": u["alignment_quarantined"],
        }
        for u in units
        if u["alignment_flags"]
    ]


def build(root=DEFAULT):
    verify_inputs(CONSTRUCTION)
    inventory = read_rows(CONSTRUCTION / "inventory.jsonl")
    old_units = read_rows(CONSTRUCTION / "candidate-manifest.jsonl")
    old_packet = read_json(CONSTRUCTION / "qa/packet.json")
    assert len(inventory) == 174 and len(old_units) == 123 and len(old_packet["items"]) == 123
    root.mkdir(parents=True, exist_ok=True)
    prior_files = {
        str(p.relative_to(CONSTRUCTION)): file_hash(p)
        for p in sorted(CONSTRUCTION.rglob("*"))
        if p.is_file()
    }
    stable(
        root / "construction-preservation.json", {"root": str(CONSTRUCTION), "files": prior_files}
    )
    master = master_inventory(inventory, old_units, read_json(CONFIG))
    graph = lineage(master, read_rows(CONSTRUCTION / "audio-artifacts.jsonl"))
    units = compile_candidates(old_units, master)
    stable(root / "master-inventory.jsonl", master, rows=True)
    stable(root / "source-lineage.json", graph)
    stable(root / "candidate-manifest.jsonl", units, rows=True)
    stable(root / "alignment-diagnostics.jsonl", diagnostic_rows(units), rows=True)
    selected = [r for r in master if r["selected_for_QA"]]
    stable(root / "selected-take-provenance.jsonl", selected, rows=True)
    special = [r for r in master if r["alignment_transcript"] == "我想买这个"]
    stable(root / "wo-xiang-mai-zhe-ge-inventory.jsonl", special, rows=True)
    packet = make_packet(units, old_packet, file_hash(root / "candidate-manifest.jsonl"))
    stable(root / "qa/packet.json", packet)
    render(root, packet)
    counts = {}
    for cat in [NATURAL, DIAGNOSTIC, UNKNOWN, CONTROL]:
        subset = [u for u in units if u["provenance_category"] == cat]
        counts[cat] = {
            "archive_takes": sum(r["provenance_category"] == cat for r in master),
            "selected_takes": len({u["source_id"] for u in subset}),
            "units": len(subset),
            "intended_lexical": distribution(subset, "intended_lexical_tone"),
            "alignment_reading_lexical": distribution(subset, "alignment_lexical_tone"),
            "expected_surface": distribution(subset, "expected_surface_tone"),
        }
    summary = {
        "version": SEED,
        "categories": counts,
        "lineage": graph["counts"],
        "documented_human_sources": sum(r["human_control_status"] == "human" for r in master),
        "unknown_human_identity_sources": sum(
            r["human_control_status"] == "unknown" for r in master
        ),
        "material_category_counts": dict(Counter(r["material_category"] for r in master)),
        "capture_dates_recovered": sum(r["capture_date"] is not None for r in master),
        "selected_recordings": len(selected),
        "qa_units": len(units),
        "playback_clips": len(units) * 3,
        "alignment_successes": len(selected),
        "tone_bearing_spans": len(units),
        "alignment_flagged_units": sum(bool(u["alignment_flags"]) for u in units),
        "structural_violations": sum(bool(u["structural_violations"]) for u in units),
        "provenance_held_units": sum(u["provenance_hold"] for u in units),
        "flagged_and_provenance_held": sum(
            bool(u["alignment_flags"]) and u["provenance_hold"] for u in units
        ),
        "candidate_manifest_sha256": file_hash(root / "candidate-manifest.jsonl"),
        "packet_sha256": packet["packet_sha256"],
        "lineage_sha256": file_hash(root / "source-lineage.json"),
        "human_QA_status": "PENDING",
        "benchmark_release_created": False,
        "inference_run": False,
    }
    stable(root / "summary.json", summary)
    reports(root, master, units, summary)
    return summary


def reports(root, master, units, summary):
    lines = [
        "# Selected take provenance — one row per take",
        "",
        "Unknown means: **UNKNOWN — no historical evidence establishes "
        "natural vs diagnostic intent**. "
        "Alignment flags are a separate review concern. No tone judgment is requested.",
        "",
        "| Take / aliases | Phrase | Category | Explicit historical evidence "
        "| Original/archive location |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in master:
        if not r["selected_for_QA"]:
            continue
        origins = "; ".join(s["path"] for s in r["sources"])
        lines.append(
            "| "
            + " | ".join(
                [
                    r["source_id"] + " / " + ", ".join(r["names"]),
                    r["alignment_transcript"],
                    r["provenance_category"],
                    r["role_reason"],
                    origins,
                ]
            )
            + " |"
        )
    text = "\n".join(lines) + "\n"
    p = root / "selected-take-provenance.md"
    if p.exists() and p.read_text() != text:
        raise ValueError("provenance_report_changed")
    if not p.exists():
        p.write_text(text)
    all_lines = [
        "# Canonical master source inventory",
        "",
        "| Source | Phrase | Human/control | Provenance | Usability "
        "| Capture date evidence | Primary eligibility | Hold |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in master:
        date = r["capture_date"]["value"] if r["capture_date"] else "unknown"
        all_lines.append(
            "| "
            + " | ".join(
                [
                    r["source_id"],
                    r["alignment_transcript"] or "unknown",
                    r["human_control_status"],
                    r["provenance_category"],
                    r["material_category"],
                    date,
                    r["benchmark_eligibility"],
                    "; ".join(r["hold_reasons"]) or "human alignment QA pending",
                ]
            )
            + " |"
        )
    text = "\n".join(all_lines) + "\n"
    p = root / "master-inventory.md"
    if p.exists() and p.read_text() != text:
        raise ValueError("master_report_changed")
    if not p.exists():
        p.write_text(text)


def validate_reviews(packet, answers):
    """Validate substantive QA; playback booleans are unmodified provenance only."""
    if not isinstance(answers, dict):
        raise ValueError("review_must_be_object")
    if answers.get("schema") != packet["schema"]:
        raise ValueError("review_schema_mismatch")
    if answers.get("packet_sha256") != packet["packet_sha256"]:
        raise ValueError("packet_hash_mismatch")
    if not isinstance(answers.get("reviewer"), str) or not answers["reviewer"].strip():
        raise ValueError("missing_reviewer")
    expected = {i["item_id"]: i for i in packet["items"]}
    rows = answers.get("reviews", [])
    if (
        not isinstance(rows, list)
        or any(not isinstance(r, dict) or not isinstance(r.get("item_id"), str) for r in rows)
        or len(rows) != len(expected)
        or {r["item_id"] for r in rows} != set(expected)
    ):
        raise ValueError("missing_or_duplicate_review")
    for r in rows:
        item = expected[r["item_id"]]
        for field in ["unit_id", "source_id", "item_sha256", "alignment_flags"]:
            if r.get(field) != item[field]:
                raise ValueError("review_identity_or_metadata_mismatch:" + field)
        if r.get("reviewer") != answers["reviewer"]:
            raise ValueError("row_reviewer_mismatch")
        for field, choices in [("whole", WHOLE), ("tone", TONE)]:
            if r.get(field) not in choices:
                raise ValueError("missing_or_invalid_" + field + ":" + r["item_id"])
        if not isinstance(r.get("notes", ""), str):
            raise ValueError("invalid_notes:" + r["item_id"])
        # Optional means no listening event is required, not that malformed
        # recorded telemetry may silently be coerced into booleans.
        if "heard" in r and (
            not isinstance(r["heard"], dict)
            or set(r["heard"]) != {"context", "whole", "tone"}
            or any(type(v) is not bool for v in r["heard"].values())
        ):
            raise ValueError("invalid_playback_telemetry:" + r["item_id"])
        if "heard_all" in r and type(r["heard_all"]) is not bool:
            raise ValueError("invalid_heard_all:" + r["item_id"])
        if (r["whole"] != "PASS" or r["tone"] != "PASS") and not r.get("notes", "").strip():
            raise ValueError("nonpass_requires_notes:" + r["item_id"])
        try:
            datetime.fromisoformat(r["reviewed_at"].replace("Z", "+00:00"))
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise ValueError("invalid_review_timestamp") from e
    return {
        "reviews": len(rows),
        "whole_nonpass": sum(r["whole"] != "PASS" for r in rows),
        "tone_nonpass": sum(r["tone"] != "PASS" for r in rows),
        "release_created": False,
    }


def verify(root=DEFAULT):
    verify_inputs(CONSTRUCTION)
    sealed = read_json(root / "construction-preservation.json")
    for p, sha in sealed["files"].items():
        if file_hash(CONSTRUCTION / p) != sha:
            raise ValueError("construction_artifact_changed:" + p)
    packet = read_json(root / "qa/packet.json")
    units = read_rows(root / "candidate-manifest.jsonl")
    master = read_rows(root / "master-inventory.jsonl")
    assert packet == make_packet(
        units,
        read_json(CONSTRUCTION / "qa/packet.json"),
        file_hash(root / "candidate-manifest.jsonl"),
    )
    assert read_json(root / "source-lineage.json") == lineage(
        master, read_rows(CONSTRUCTION / "audio-artifacts.jsonl")
    )
    assert units == compile_candidates(read_rows(CONSTRUCTION / "candidate-manifest.jsonl"), master)
    originals = {r["example_id"]: r for r in read_rows(CONSTRUCTION / "candidate-manifest.jsonl")}
    crop_count = 0
    for item in packet["items"]:
        assert digest({k: v for k, v in item.items() if k != "item_sha256"}) == item["item_sha256"]
        u = originals[item["unit_id"]]
        with wave.open(u["audio"]["reference"]) as w:
            pcm = w.readframes(w.getnframes())
            width = w.getsampwidth() * w.getnchannels()
        for clip in item["clips"].values():
            p = ROOT / clip["path"]
            assert file_hash(p) == clip["sha256"]
            with wave.open(str(p)) as w:
                assert (
                    w.readframes(w.getnframes())
                    == pcm[clip["start_sample"] * width : clip["end_sample"] * width]
                )
            crop_count += 1
    assert not (root / "releases").exists()
    assert all(
        u["model_prediction"] is None
        and u["realized_tone_ground_truth"] is None
        and u["qa_status"] == "PENDING"
        and not u["eligible_for_evaluation"]
        for u in units
    )
    result = {
        "baseline_verified_files": 413,
        "construction_artifacts_unchanged": len(sealed["files"]),
        "exact_source_matching_clips": crop_count,
        "candidate_manifest_reproducible": True,
        "QA_manifest_deterministic": True,
        "duplicate_graph_deterministic": True,
        "source_hashes_stable": True,
        "no_scoring_invocation": True,
        "no_release": True,
    }
    stable(root / "verification.json", result)
    return result
