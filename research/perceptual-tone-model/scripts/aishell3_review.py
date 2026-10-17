"""Finish the existing 26-item packet without changing any targets or audio."""

import argparse
import html
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json
from perceptual_tone.aishell3_qa import DECISIONS, decode
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows


def build(root):
    folder = root / "pilot/audit/review"
    items = read_rows(folder / "items.jsonl")
    candidates = {r["example_id"]: r for r in read_rows(root / "pilot/audit/candidates.jsonl")}
    overrides = read_json(root / "pilot/lexicon-audit.json")["stock_dictionary_supported_overrides"]
    enriched, references = [], []
    for item in items:
        row = item["row"]
        if candidates[row["example_id"]] != row:
            raise ValueError("packet_candidate_mismatch")
        pcm, rate, info = decode(row["audio"]["reference"])
        if not 0 <= row["start"] < row["end"] <= len(pcm) / rate:
            raise ValueError("bad_packet_boundary")
        for view, clip in item["playback"].items():
            path = folder / clip["reference"]
            if path.parent != folder / "audio" or file_hash(path) != clip["sha256"]:
                raise ValueError("packet_audio_path_or_hash_mismatch")
            samples, clip_rate, _ = decode(path)
            first = round(clip["start_seconds"] * rate)
            last = round(clip["end_seconds"] * rate)
            margin = {"target": 0, "context": 0.25, "utterance": None}[view]
            expected_first = (
                0 if margin is None else max(0, math.floor((row["start"] - margin) * rate))
            )
            expected_last = (
                len(pcm)
                if margin is None
                else min(len(pcm), math.ceil((row["end"] + margin) * rate))
            )
            if (
                (first, last) != (expected_first, expected_last)
                or rate != clip_rate
                or not np.array_equal(samples, pcm[first:last])
            ):
                raise ValueError("packet_crop_pcm_or_boundary_mismatch")
            if not np.any(samples):
                raise ValueError("empty_or_all_zero_review_audio")
            references.append(clip["reference"])
        plot = folder / "plots" / (item["item"] + ".png")
        if not plot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("invalid_boundary_plot")
        enriched.append(
            {
                **item,
                "item_sha256": digest(row),
                "container_note": info.get("container_warning")
                or "Original RIFF container valid; PCM unchanged.",
                "pronunciation_note": overrides.get(
                    row["corpus_pinyin"], "Pinned pinyin G2P; no custom override."
                ),
                "plot": {"reference": str(plot.relative_to(folder)), "sha256": file_hash(plot)},
            }
        )
    payload = {
        "schema": "aishell3-playback-integrity-v1",
        "decisions": list(DECISIONS),
        "items": enriched,
    }
    packet = {**payload, "packet_sha256": digest(payload)}
    stable_json(folder / "packet.json", packet)
    esc = html.escape
    content = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>AISHELL-3 · 26 playback checks</title>",
        "<style>body{font:16px system-ui;line-height:1.5;max-width:1100px;margin:auto;"
        "padding:20px;background:#f7f8fa;color:#17202a}"
        "header{background:#fff;border:1px solid #ccd;padding:20px}"
        "section{background:#fff;border:1px solid #ccd;margin:24px 0;padding:20px}"
        "button,select,input,textarea{font:inherit;padding:8px;margin:4px}button{cursor:pointer}"
        "button:focus-visible,select:focus-visible{outline:3px solid #175cd3}img{width:100%}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere}textarea{display:block;width:95%}"
        "audio{max-width:100%}label{display:block}code{overflow-wrap:anywhere}"
        ".players{display:flex;gap:15px;flex-wrap:wrap}.player{display:flex;flex-direction:column}"
        "#message{color:#9a3412}details{margin:12px 0}</style>",
        "<header><h1>AISHELL-3 alignment playback QA</h1>",
        "<p><strong>26 targets · 78 audio clips · human review pending.</strong> "
        "Check that the target span contains the intended corpus read unit. Listen to context "
        "and target; use the full utterance whenever ownership is unclear. Tone labels come "
        "from the corpus: no tone relabeling or native-listener tone judgment is required.</p>",
        "<p><strong>PASS:</strong> intended unit, plausible boundaries, "
        "no obvious transcript/audio mismatch. Mark any clipped onset, stolen neighbor, "
        "wrong unit, or uncertain case with "
        "the appropriate non-PASS and notes. Any non-PASS blocks training until investigated; "
        "decisions never edit labels or timings.</p>",
        '<label>Your name <input id="reviewer" autocomplete="name"></label>',
        '<p id="progress" role="status"></p><button id="export">EXPORT COMPLETE DECISIONS</button>'
        '<button id="draft">EXPORT DRAFT</button>',
        '<label>Import saved JSON <input id="import" type="file" '
        'accept="application/json,.json"></label>',
        '<p id="message" role="status" aria-live="polite"></p>',
        "<p>Progress stays in this browser when local storage is available. "
        "Export a draft as a backup. No data is sent to a server.</p></header>",
    ]
    for item in enriched:
        row = item["row"]

        def neighbor(u, default):
            return esc(f"{u['hanzi']} {u['corpus_pinyin']} ({u['label']})") if u else default

        content += [
            f'<section data-id="{esc(row["example_id"])}"><h2>{item["item"]}: '
            f"{esc(row['hanzi'])} · {row['corpus_pinyin']} · {row['label']}</h2>",
            f"<p><code>{row['example_id']}</code><br>Speaker {row['speaker_id']} · "
            f"utterance {row['utterance_id']}<br>"
            f"Target {row['start']:.3f}&ndash;{row['end']:.3f} s "
            f"({1000 * (row['end'] - row['start']):.0f} ms)<br>{esc(row['transcript'])}</p>",
            f"<p>{neighbor(row['preceding'], 'START')} → <strong>{esc(row['hanzi'])} "
            f"{row['corpus_pinyin']}</strong> → {neighbor(row['following'], 'END')}</p>",
            '<div class="players">',
        ]
        for view in ("context", "target", "utterance"):
            ref = item["playback"][view]["reference"]
            content.append(
                f'<div class="player"><button data-view="{view}">PLAY {view.upper()}</button>'
                f'<audio data-view="{view}" aria-label="{item["item"]} {view}" '
                f'controls preload="none" src="{esc(ref)}"></audio></div>'
            )
        content += [
            "</div>",
            '<label>Decision <select aria-label="QA decision">'
            '<option value="">Choose a decision</option>'
            + "".join(f"<option>{esc(d)}</option>" for d in DECISIONS)
            + "</select></label>",
            '<label><input type="checkbox">I listened to the context and target '
            "and checked read-unit ownership.</label>",
            '<label>Notes (required for non-PASS)<textarea rows="2"></textarea></label>',
            f'<img loading="lazy" src="{item["plot"]["reference"]}" '
            f'alt="{item["item"]} waveform, spectrogram and phone boundaries">',
            "<details><summary>Phones, diagnostics and source notes</summary><pre>"
            + esc(
                json.dumps(
                    {
                        "aligned_phones": row["aligned_phones"],
                        "diagnostics": row["alignment_diagnostics"],
                        "RIFF_note": item["container_note"],
                        "custom_pronunciation_note": item["pronunciation_note"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            + "</pre></details></section>",
        ]
    content += [
        '<script id="packet" type="application/json">'
        + json.dumps(packet, ensure_ascii=False).replace("<", "\\u003c")
        + "</script>",
        "<script>" + (PACKAGE / "scripts/aishell3_review.js").read_text() + "</script></html>",
    ]
    # Only presentation changes. Original items, clips, plots and row hashes stay fixed.
    (folder / "index.html").write_text("\n".join(content) + "\n")
    result = {
        "targets": len(items),
        "audio_clips": len(references),
        "plots": len(items),
        "all_media_hashes_and_decoded_pcm_verified": True,
        "human_playback_qa": "pending",
        "packet_sha256": packet["packet_sha256"],
        "html": str((folder / "index.html").resolve()),
    }
    stable_json(root / "continuation/review-media-qa.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE / "data/generated/aishell3")
    build(parser.parse_args().root)
