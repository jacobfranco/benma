"""Offline replay of saved connected-speech records; never reads audio or calls providers.

Usage: python -m benchmark.pronunciation_v2.connected_replay \
    --record S01=/private/S01/record.json --output /private/replay
Full replay records stay local. Summary files and Markdown reports may be reviewed
separately for inclusion in research docs; the CLI never copies source audio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

from benchmark.pronunciation_v2.connected_schema import Record
from benchmark.pronunciation_v2.connected_speech_probe import build_record, markdown


def replay_record(original: Record, source_sha256: str | None = None) -> Record:
    """Recompute derivations only, retaining original evidence and capture identity."""
    if original.perception.evidence.get("transcript") != original.perception.raw_transcript:
        raise ValueError("saved perception evidence differs from immutable transcript")
    before = original.configuration.get("context_before_ms", 150)
    after = original.configuration.get("context_after_ms", 150)
    if before != after:
        raise ValueError("asymmetric context is not supported by this replay version")
    result = build_record(
        recording_id=original.recording_id,
        audio=original.audio.model_copy(deep=True),
        provider=original.provider,
        evidence=original.perception.evidence,
        raw_response=original.perception.raw_response,
        request_configuration=original.perception.request_configuration,
        azure_raw=original.alignment.raw_response,
        alignment_status=original.alignment.evidence_status,
        acoustics=original.acoustics,
        target=original.intended_text,
        mode=original.mode,
        context_ms=before,
    )
    # Keep capture provenance exact, including status when optional evidence failed.
    result = result.model_copy(
        update={
            "perception": original.perception.model_copy(deep=True),
            "alignment": result.alignment.model_copy(
                update={
                    "evidence_status": original.alignment.evidence_status,
                }
            ),
            "study_annotations": list(original.study_annotations),
            "replay": {
                "source_record_sha256": source_sha256,
                "source_schema_version": original.schema_version,
                "source_analysis_version": original.analysis_version,
                "source_configuration": original.configuration,
                "source_alignment_issues": original.alignment.issues,
                "source_replay": original.replay,
                "pypinyin_version": version("pypinyin"),
                "acoustics": "unchanged_saved_whole_recording_trace",
                "provider_calls": 0,
            },
        }
    )
    return Record.model_validate(result.model_dump())


def coverage(record):
    raw = record.alignment.raw_response
    try:
        raw_words = raw["NBest"][0]["Words"]
    except (TypeError, KeyError, IndexError):
        raw_words = []
    # Availability counts raw explicit entries, independently of acceptance.
    from benma_api.pronunciation.azure_alignment import HAN, _span

    available = sum(
        isinstance(g, dict)
        and isinstance(g.get("Grapheme"), str)
        and bool(HAN.fullmatch(g["Grapheme"]))
        and _span(g) is not None
        for w in raw_words
        if isinstance(w, dict)
        for g in (w.get("Syllables") or [])
    )
    return {
        "han_units": len(record.units),
        "provider_grapheme_timing_available": available,
        "timing_accepted": sum(u.timing is not None for u in record.units),
        "timing_unresolved": sum(u.timing is None for u in record.units),
        "reading_resolved": sum(u.reading.pinyin is not None for u in record.units),
        "reading_ambiguous": sum(u.reading.ambiguous for u in record.units),
        "at_least_five_usable_f0": sum(
            u.pitch is not None and u.pitch.usable_frame_count >= 5 for u in record.units
        ),
        "heavy_missingness": sum("heavy_f0_missingness" in u.quality_flags for u in record.units),
        "zero_usable_f0": sum(
            u.pitch is not None and u.pitch.usable_frame_count == 0 for u in record.units
        ),
        "tracker_instability_units": sum(
            "tracker_instability" in u.quality_flags for u in record.units
        ),
        "tracker_instability_frames": sum(
            not p.get("quality_usable", True)
            for u in record.units
            if u.pitch
            for p in u.pitch.frames
        ),
        "mapping_issue_count": len(record.alignment.issues),
    }


def comparison(label, original, replayed, sha):
    old = {u.unit_id: u for u in original.units}
    recovered = [u for u in replayed.units if u.timing and old[u.unit_id].timing is None]
    return {
        "study_id": label,
        "recording_id": original.recording_id,
        "source_record_sha256": sha,
        "audio_sha256": original.audio.sha256,
        "canonical_audio_sha256": original.audio.canonical_sha256,
        "perceived_text": original.perception.raw_transcript,
        "intended_text": original.intended_text,
        "before": coverage(original),
        "after": coverage(replayed),
        "mapping_issues": replayed.alignment.issues,
        "unresolved_readings": [
            {
                "unit_id": u.unit_id,
                "character": u.perceived_text,
                "alternatives": u.reading.alternatives,
                "context": u.reading.context_text,
            }
            for u in replayed.units
            if u.reading.ambiguous
        ],
        "recovered_regions": [
            {
                "unit_id": u.unit_id,
                "character": u.perceived_text,
                "timing": u.timing.model_dump(),
                "usable_f0_frames": u.pitch.usable_frame_count if u.pitch else None,
                "total_f0_frames": u.pitch.frame_count if u.pitch else None,
                "quality_flags": u.quality_flags,
            }
            for u in recovered
        ],
    }


def summary_markdown(rows):
    lines = [
        "# Coverage before / after",
        "",
        "Saved real-study evidence; before counts come from the original stored units. "
        "No ASR, Azure, audio decoding or Praat extraction is performed.",
        "",
        "| Study | Han | Raw grapheme spans | Timing before | Timing after | Untimed after | "
        "Readings before | Readings after | Ambiguous after | Mapping issues |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        a, b = row["before"], row["after"]
        lines.append(
            f"| {row['study_id']} | {b['han_units']} | "
            f"{b['provider_grapheme_timing_available']} | {a['timing_accepted']} | "
            f"{b['timing_accepted']} | {b['timing_unresolved']} | "
            f"{a['reading_resolved']} | {b['reading_resolved']} | "
            f"{b['reading_ambiguous']} | {b['mapping_issue_count']} |"
        )
    lines += [
        "",
        "## Saved F0 evidence",
        "",
        "Counts are units except the explicitly labeled frame column. "
        "`>=5` means selected F0 is present and quality_usable is true. "
        "Heavy missingness uses the existing >0.5 raw gated F0 missing proportion. "
        "Zero usable F0 excludes untimed units. Instability means any existing "
        "quality_usable=false frame. These overlapping flags are not tone diagnoses.",
        "",
        "| Study | Timed before→after | ≥5 usable before→after | "
        "Heavy missing before→after | "
        "Zero usable before→after | Instability units before→after | "
        "Instability frames before→after |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        values = [
            f"{row['before'][key]}→{row['after'][key]}"
            for key in (
                "timing_accepted",
                "at_least_five_usable_f0",
                "heavy_missingness",
                "zero_usable_f0",
                "tracker_instability_units",
                "tracker_instability_frames",
            )
        ]
        lines.append("| " + " | ".join([row["study_id"], *values]) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="append", required=True, metavar="LABEL=PATH")
    parser.add_argument("--output", required=True, type=Path, help="New local output directory")
    parser.add_argument(
        "--annotations", type=Path, help="JSON label-to-notes map; not acoustic gold"
    )
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output already exists; preserve original evidence and choose a new path")
    annotations = json.loads(args.annotations.read_text()) if args.annotations else {}
    if not isinstance(annotations, dict) or any(
        not isinstance(notes, list) or any(not isinstance(note, str) for note in notes)
        for notes in annotations.values()
    ):
        parser.error("annotations must map labels to lists of notes")
    inputs = []
    for item in args.record:
        label, sep, filename = item.partition("=")
        if (
            not sep
            or not label
            or any(
                c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                for c in label
            )
        ):
            parser.error("record must be a safe LABEL=PATH")
        if label == "TOTAL" or label in [r[0] for r in inputs]:
            parser.error("duplicate or reserved label")
        data = Path(filename).read_bytes()
        original = Record.model_validate_json(data)
        inputs.append((label, original, hashlib.sha256(data).hexdigest()))
    # Validate and derive every record before writing any output.
    outputs = [
        (label, original, replay_record(original, sha), sha) for label, original, sha in inputs
    ]
    if set(annotations) - {label for label, *_ in outputs}:
        parser.error("annotations contain unknown study labels")
    outputs = [
        (
            label,
            original,
            result.model_copy(
                update={
                    "study_annotations": [*result.study_annotations, *annotations.get(label, [])],
                }
            ),
            sha,
        )
        for label, original, result, sha in outputs
    ]
    rows = [
        comparison(label, original, replayed, sha) for label, original, replayed, sha in outputs
    ]
    total = {
        "study_id": "TOTAL",
        **{
            side: {key: sum(r[side][key] for r in rows) for key in rows[0][side]}
            for side in ("before", "after")
        },
    }
    args.output.mkdir(parents=True, exist_ok=False)
    for label, _, result, _ in outputs:
        dest = args.output / label
        dest.mkdir()
        (dest / "record.json").write_text(result.model_dump_json(indent=2) + "\n")
        (dest / "report.md").write_text(markdown(result))
    (args.output / "coverage.json").write_text(
        json.dumps([*rows, total], ensure_ascii=False, indent=2) + "\n"
    )
    (args.output / "coverage-before-after.md").write_text(summary_markdown([*rows, total]))
    print(args.output / "coverage-before-after.md")


if __name__ == "__main__":
    main()
