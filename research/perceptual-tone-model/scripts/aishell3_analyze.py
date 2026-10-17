"""Reconstruct the alignment pilot and issue a hash-bound, unanswered audio QA packet."""

import argparse
import csv
import html
import json
import math
import sys
import wave
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.aishell3 import TONE_CLASSES, checked_wav, quality_gate, t3_contexts
from perceptual_tone.aishell3_alignment import reconstruct, textgrid
from perceptual_tone.common import (
    PACKAGE,
    digest,
    file_hash,
    read_json,
    read_rows,
    write_json,
    write_rows,
)


def reconstruct_stage(root, stage="pilot"):
    """Read saved alignments; never invoke MFA or change their boundaries."""
    pilot = root / stage
    config = read_json(PACKAGE / "configs/aishell3.json")
    utterances = read_rows(pilot / "utterances.jsonl")
    lexicon = read_json(pilot / "lexicon-audit.json")
    registry = {r["speaker_id"]: r for r in read_rows(root / "speaker-registry.jsonl")}
    analysis_path = pilot / "aligned/alignment_analysis.csv"
    diagnostics = {}
    with analysis_path.open() as stream:
        for r in csv.DictReader(stream):
            if r["file"] in diagnostics:
                raise ValueError("duplicate_mfa_diagnostics")
            diagnostics[r["file"]] = {
                "speaker_id": r["speaker"],
                "alignment_log_likelihood": float(r["overall_log_likelihood"])
                if r["overall_log_likelihood"]
                else None,
                "speech_log_likelihood": float(r["speech_log_likelihood"])
                if r["speech_log_likelihood"]
                else None,
                "phone_duration_deviation": float(r["phone_duration_deviation"])
                if r["phone_duration_deviation"]
                else None,
                "snr": float(r["snr"]) if r["snr"] else None,
                "source_sha256": file_hash(analysis_path),
            }
    rows, failures = [], []
    for u in utterances:
        if file_hash(u["audio"]["reference"]) != u["audio"]["sha256"]:
            raise ValueError("Source audio changed after preparation")
        if (
            checked_wav(Path(u["alignment_audio"]["reference"]).read_bytes())["pcm_sha256"]
            != u["pcm_sha256"]
        ):
            raise ValueError("Alignment audio PCM differs from corpus source")
        path = pilot / "aligned" / u["speaker_id"] / (u["utterance_id"] + ".TextGrid")
        try:
            tiers = textgrid(path.read_text())
            diag = diagnostics.get(u["utterance_id"], {})
            if diag.get("speaker_id") != u["speaker_id"]:
                raise ValueError("diagnostic_speaker_mismatch")
            diag = {
                **diag,
                "textgrid_sha256": file_hash(path),
                "mfa_version": config["mfa_version"],
                "acoustic_model": config["acoustic_model"],
                "acoustic_version": config["acoustic_version"],
                "lexicon_sha256": file_hash(pilot / "read-units.dict"),
            }
            rows.extend(reconstruct(u, tiers, lexicon["pronunciations"], diag, config))
        except (ValueError, OSError) as error:
            failures.append(
                {
                    "utterance_id": u["utterance_id"],
                    "read_units": len(u["units"]),
                    "reason": str(error),
                }
            )
    return rows, failures, utterances, lexicon, registry, config


def analyze(root, output, reviews=None):
    rows, failures, utterances, lexicon, registry, config = reconstruct_stage(root)
    accepted = [r for r in rows if r["reconstruction_status"] == "candidate"]
    rejected = [r for r in rows if r["reconstruction_status"] == "rejected"]
    output.mkdir(parents=True, exist_ok=False)
    write_rows(output / "candidates.jsonl", accepted)
    write_rows(output / "rejected.jsonl", rejected)
    write_rows(output / "utterance-failures.jsonl", failures)
    # Fixed class quotas, then hash order. Prefer speaker diversity within each
    # class. This pilot is QA-only; none of these speakers is held out for modeling.
    selected = []
    for tone in TONE_CLASSES:
        choices = sorted(
            [r for r in accepted if r["label"] == tone],
            key=lambda r: digest([config["seed"], r["example_id"]]),
        )
        seen_speakers, ordered = set(), []
        for row in choices:
            if row["speaker_id"] not in seen_speakers:
                ordered.append(row)
                seen_speakers.add(row["speaker_id"])
        ordered += [r for r in choices if r not in ordered]
        selected += ordered[: config["pilot_review_per_tone"]]
    # Include the actual-reading wo2 and erhua read-unit regressions if not drawn.
    for pinyin in ("wo2", "nar3"):
        choices = [r for r in accepted if r["corpus_pinyin"] == pinyin]
        if choices and choices[0] not in selected:
            selected.append(choices[0])
    review_dir = output / "review"
    review_dir.mkdir()
    (review_dir / "audio").mkdir()
    items, template = [], []
    for index, row in enumerate(selected, 1):
        pcm_path = Path(row["audio"]["reference"])
        with wave.open(str(pcm_path)) as stream:
            rate = stream.getframerate()
            pcm = stream.readframes(stream.getnframes())
        name = f"item-{index:02d}"
        links = {}
        for view, margin in (("target", 0), ("context", 0.25), ("utterance", None)):
            first = 0 if margin is None else max(0, math.floor((row["start"] - margin) * rate))
            last = (
                len(pcm) // 2
                if margin is None
                else min(len(pcm) // 2, math.ceil((row["end"] + margin) * rate))
            )
            target = review_dir / "audio" / f"{name}-{view}.wav"
            with wave.open(str(target), "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(rate)
                stream.writeframes(pcm[first * 2 : last * 2])
            links[view] = {
                "reference": f"audio/{target.name}",
                "sha256": file_hash(target),
                "start_seconds": first / rate,
                "end_seconds": last / rate,
            }
        items.append({"item": name, "row": row, "playback": links})
        template.append(
            {
                "example_id": row["example_id"],
                "item_sha256": digest(row),
                "reviewer": None,
                "reviewed_at": None,
                "heard_context_and_target": None,
                "decision": None,
                "notes": "",
            }
        )
    write_rows(review_dir / "items.jsonl", items)
    write_rows(review_dir / "review.template.jsonl", template)
    content = [
        '<!doctype html><meta charset="utf-8"><title>AISHELL-3 pilot QA</title>',
        "<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem}"
        "section{border-top:1px solid #bbb;padding:1rem 0}img{width:100%}"
        "pre{white-space:pre-wrap}audio{width:300px}</style>",
        "<h1>AISHELL-3 alignment pilot — audio QA pending</h1>",
        "<p>Listen to the utterance, target and context. Check read-unit ownership and the "
        "intended read unit. No tone relabeling or native tone judgment is required. "
        "Fill review.template.jsonl with your identity, timestamp and findings; "
        "keep item hashes unchanged.</p>",
    ]
    for item in items:
        row = item["row"]
        previous = row["preceding"]["corpus_pinyin"] if row["preceding"] else "START"
        following = row["following"]["corpus_pinyin"] if row["following"] else "END"
        content += [
            f"<section><h2>{item['item']}: {html.escape(row['hanzi'])} "
            f"— {row['corpus_pinyin']} / {row['label']}</h2>",
            f"<p>{row['utterance_id']} · {row['speaker_id']} · "
            f"{row['start']:.3f}&ndash;{row['end']:.3f} s<br>"
            f"{html.escape(row['transcript'])}<br>"
            f"{previous} → {row['corpus_pinyin']} → {following}</p>",
        ]
        for view, media in item["playback"].items():
            content.append(
                f'<p>{view}: <audio controls preload="none" src="{media["reference"]}"></audio></p>'
            )
        content.append(
            f'<img src="plots/{item["item"]}.png" alt="Waveform, spectrogram and aligned phones">'
        )
        content.append(
            "<pre>"
            + html.escape(
                json.dumps(
                    {"phones": row["aligned_phones"], "diagnostics": row["alignment_diagnostics"]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            + "</pre></section>"
        )
    (review_dir / "index.html").write_text("\n".join(content) + "\n")
    reviewed = read_rows(reviews) if reviews else []
    gate = quality_gate(accepted, registry, reviewed, stage="pilot")
    if failures:
        gate["blockers"].append("utterance_alignment_failures")
    mismatches = sum(
        "alignment_token_sequence_mismatch" in r["exclusion_reasons"] for r in rejected
    )
    if mismatches or lexicon["oovs"]:
        gate["blockers"].append("token_mismatch_or_oov")
    if len(accepted) / max(1, sum(len(u["units"]) for u in utterances)) < 0.9:
        gate["blockers"].append("pilot_reconstruction_yield_below_90_percent")
    gate["passed"] = not gate["blockers"]
    summary = {
        "status": "PILOT_QA_PASSED" if gate["passed"] else "STOPPED_PILOT_QUALITY_GATE",
        "config": config,
        "utterances_attempted": len(utterances),
        "utterances_aligned": len(utterances) - len(failures),
        "verified_speakers": sorted({u["speaker_id"] for u in utterances}),
        "corpus_read_units": sum(len(u["units"]) for u in utterances),
        "reconstructed_units": len(rows),
        "candidate_units": len(accepted),
        "rejected_units": len(rejected),
        "failed_utterance_units": sum(r["read_units"] for r in failures),
        "exclusion_reasons": dict(Counter(r for row in rejected for r in row["exclusion_reasons"])),
        "oov_count": len(lexicon["oovs"]),
        "token_sequence_mismatch_units": mismatches,
        "corpus_tone_counts": dict(Counter(u["label"] for r in utterances for u in r["units"])),
        "candidate_tone_counts": dict(Counter(r["label"] for r in accepted)),
        "candidate_t3_contexts": t3_contexts(accepted),
        "review_items": len(items),
        "review_tone_counts": dict(Counter(i["row"]["label"] for i in items)),
        "reviewed_audio_items": sum(gate["audited_by_tone"].values()),
        "pilot_gate": gate,
        "scaled_dataset_created": False,
        "training_run": False,
        "final_usable_training_units": 0,
        "speaker_split": None,
        "neutral_decision": (
            "Preserved as T5; sparse neutral may be reserved for a four-tone run "
            "after the gates pass."
        ),
        "model_metrics": None,
        "external_probe": None,
        "candidate_manifest_sha256": file_hash(output / "candidates.jsonl"),
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE / "data/generated/aishell3")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    analyze(args.root, args.output or args.root / "pilot/audit", args.reviews)
