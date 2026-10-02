"""Offline sentence diagnostic. No target enters perception, alignment, or pitch."""
# ruff: noqa: E402 -- script bootstraps the production source tree

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services/api/src"))

from benma_api.audio.service import canonicalize, inspect_audio
from benma_api.config import Settings
from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.azure_alignment import (
    AZURE_TIMING_CONFIG,
    timing_payload,
)
from benma_api.pronunciation.contours import display_contour
from benma_api.pronunciation.perceived import perceived_syllables
from benma_api.pronunciation.readings import READING_VERSION
from benma_api.pronunciation.surface import SURFACE_VERSION
from benma_api.speech.contracts import UnknownTargetPerceptionInput
from benma_api.speech.providers.azure import request_azure_speech
from benma_api.speech.providers.factory import build_perception_provider

from benchmark.pronunciation_v2.connected_mapping import (
    MAPPING_VERSION,
    contextual_readings,
    grapheme_candidates,
    reference_phones,
)
from benchmark.pronunciation_v2.connected_mapping import (
    READING_VERSION as CONTEXT_READING_VERSION,
)
from benchmark.pronunciation_v2.connected_schema import (
    Alignment,
    Audio,
    Context,
    Expectation,
    Perception,
    Phone,
    Pitch,
    Reading,
    Record,
    Span,
    TextEdit,
    Unit,
    Word,
)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reading_of(syllable) -> Reading:
    return Reading(
        pinyin=syllable.pinyin,
        lexical_tone=syllable.lexical_tone,
        status=syllable.reading_source,
        alternatives=syllable.alternatives,
        ambiguous=syllable.reading_source == "unresolved",
    )


def lexical_chars(text: str) -> list[tuple[int, str]]:
    # Ignore punctuation/space ONLY in comparison/mapping; retain original offsets.
    return [(i, c) for i, c in enumerate(text) if c.isalnum()]


def compare_text(intended: str, perceived: str) -> list[TextEdit]:
    """Levenshtein: diagonal, deletion, insertion tie order; flag nonunique paths."""
    a, b = lexical_chars(intended), lexical_chars(perceived)
    costs = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    ways = [[1] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        costs[i][0] = i
    for j in range(len(b) + 1):
        costs[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            options = [
                (costs[i - 1][j - 1] + (a[i - 1][1] != b[j - 1][1]), ways[i - 1][j - 1]),
                (costs[i - 1][j] + 1, ways[i - 1][j]),
                (costs[i][j - 1] + 1, ways[i][j - 1]),
            ]
            costs[i][j] = min(c for c, _ in options)
            ways[i][j] = min(2, sum(n for c, n in options if c == costs[i][j]))
    i, j = len(a), len(b)
    unique = ways[i][j] == 1
    target_readings = {s.character_start: s for s in perceived_syllables(intended, {})}
    edits = []
    while i or j:
        if i and j and costs[i][j] == costs[i - 1][j - 1] + (a[i - 1][1] != b[j - 1][1]):
            ai, bj = a[i - 1], b[j - 1]
            op = "match" if ai[1] == bj[1] else "substitution"
            i, j = i - 1, j - 1
        elif i and costs[i][j] == costs[i - 1][j] + 1:
            ai, bj, op = a[i - 1], None, "deletion"
            i -= 1
        else:
            ai, bj, op = None, b[j - 1], "insertion"
            j -= 1
        syllable = target_readings.get(ai[0]) if ai else None
        expectation = (
            Expectation(
                reading=reading_of(syllable),
                surface_tone=syllable.expected_surface_tone,
                rule=syllable.surface_rule,
                version=SURFACE_VERSION,
            )
            if syllable and unique
            else None
        )
        edits.append(
            TextEdit(
                operation=op,
                perceived_offset=bj[0] if bj else None,
                intended_offset=ai[0] if ai else None,
                perceived=bj[1] if bj else None,
                intended=ai[1] if ai else None,
                correspondence="unique_minimum_edit" if unique else "ambiguous_minimum_edit",
                expectation=expectation,
            )
        )
    return list(reversed(edits))


def span_of(value: Any, duration_ms: float) -> Span | None:
    if not isinstance(value, dict):
        return None
    start, end = value.get("start_seconds"), value.get("end_seconds")
    if any(type(v) not in (float, int) or not math.isfinite(v) for v in (start, end)):
        return None
    start, end = start * 1000, end * 1000
    if start < 0 or end <= start or end > duration_ms:
        return None
    return Span(start_ms=start, end_ms=end, duration_ms=end - start)


def alignment_evidence(text, evidence, azure_raw, duration_ms):
    """Retain whole words; accept character timing only with exact provenance checks."""
    readings = perceived_syllables(text, evidence)
    candidates, words, issues = [], [], []
    if azure_raw is not None:
        provider_words, candidates, issues = grapheme_candidates(azure_raw, text)
        source = "azure_perceived_reference"
    else:
        source = "perception_token"
        provider_words = [
            {"text": t.get("text"), "timing": t.get("timing"), "token": t}
            for t in evidence.get("tokens", []) or []
            if isinstance(t, dict) and "timing" in t
        ]
    if azure_raw is None and not provider_words:
        source = "none"
    positions, cursor = lexical_chars(text), 0
    for word in provider_words:
        label = word.get("text")
        if not isinstance(label, str):
            issues.append("invalid_word_label")
            continue
        letters = [c for _, c in lexical_chars(label)]
        if azure_raw is not None:
            matched = positions[cursor : cursor + len(letters)]
            cursor += len(letters)
            if not matched:
                continue
            start, end = matched[0][0], matched[-1][0] + 1
        else:
            token = word["token"]
            start, end = token.get("character_start"), token.get("character_end")
            if (
                type(start) is not int
                or type(end) is not int
                or not 0 <= start < end <= len(text)
                or text[start:end] != label
            ):
                issues.append("token_character_mapping_unresolved")
                continue
            if end == start + 1:
                syllable = next((s for s in readings if s.character_start == start), None)
                if syllable and isinstance(word.get("timing"), dict):
                    candidates.append(
                        {
                            **word["timing"],
                            "syllable_index": syllable.index,
                            "source": source,
                            "confidence": token.get("timing_confidence"),
                        }
                    )
        timing = (
            None if word.get("omitted_or_inserted") else span_of(word.get("timing"), duration_ms)
        )
        if word.get("timing") and timing is None:
            issues.append("invalid_word_timing")
        words.append(
            Word(
                perceived_text=text[start:end],
                character_start=start,
                character_end=end,
                timing=timing,
                timing_source=source,
                syllable_timing_status="unresolved",
                raw_provider_word=word.get("raw_provider_word", word),
            )
        )
    accepted, previous_end, previous_index = {}, 0, -1
    for candidate in sorted(candidates, key=lambda c: c["syllable_index"]):
        index = candidate["syllable_index"]
        span = span_of(candidate, duration_ms)
        if (
            span is None
            or index <= previous_index
            or span.start_ms < previous_end
            or span.duration_ms > 3000
        ):
            issues.append("invalid_or_overlapping_syllable_timing")
            accepted = {}
            break
        accepted[index] = (span, candidate)
        previous_end, previous_index = span.end_ms, index
    # Word regions are evidence in their own right, even when subdivision fails.
    previous_end = 0
    for word in words:
        if word.timing:
            if word.timing.start_ms < previous_end:
                issues.append("overlapping_word_timing")
                accepted = {}
                break
            previous_end = word.timing.end_ms
    words = [
        w.model_copy(
            update={
                "syllable_timing_status": "mapped"
                if all(
                    s.index in accepted
                    for s in readings
                    if w.character_start <= s.character_start < w.character_end
                )
                and any(w.character_start <= s.character_start < w.character_end for s in readings)
                else "unresolved"
            }
        )
        for w in words
    ]
    readings = contextual_readings(text, evidence, words)
    return readings, accepted, words, sorted(set(issues)), source


def pitch_region(acoustics, span):
    if acoustics is None or span is None:
        return None
    frames = [
        copy.deepcopy(p)
        for p in acoustics.get("f0", [])
        if span.start_ms <= p["timestamp_seconds"] * 1000 < span.end_ms
    ]
    voiced = sum(p.get("f0_hz") is not None for p in frames)
    usable = sum(
        p.get("selected_f0_hz") is not None and p.get("quality_usable", True) for p in frames
    )
    gate = acoustics.get("energy_gate", {}).get("threshold_rms")
    active = [p for p in frames if p.get("energy_rms", 0) >= gate] if gate is not None else []
    return Pitch(
        available=usable > 0,
        frame_count=len(frames),
        voiced_frame_count=voiced,
        usable_frame_count=usable,
        frames=frames,
        voiced_proportion=voiced / len(frames) if frames else None,
        active_voiced_proportion=sum(p.get("selected_f0_hz") is not None for p in active)
        / len(active)
        if active
        else None,
        missing_proportion=1 - voiced / len(frames) if frames else None,
        filtered_contour=[
            {"timestamp_seconds": p["timestamp_seconds"], "f0_hz": p.get("selected_f0_hz")}
            for p in frames
        ],
        source="production_praat_full_utterance_then_time_slice",
    )


def build_record(
    *,
    recording_id,
    audio,
    provider,
    evidence,
    raw_response,
    azure_raw=None,
    acoustics=None,
    target=None,
    mode="free",
    context_ms=150,
    request_configuration=None,
    alignment_status="unavailable",
    issues=(),
):
    if not math.isfinite(context_ms) or context_ms < 0:
        raise ValueError("context must be finite and nonnegative")
    evidence, raw_response = copy.deepcopy(evidence), copy.deepcopy(raw_response)
    text = evidence["transcript"]
    readings, timing, words, timing_issues, source = alignment_evidence(
        text, evidence, azure_raw, audio.duration_ms
    )
    timing_issues = sorted(set([*timing_issues, *issues]))
    units = []
    for s in readings:
        span, candidate = timing.get(s.index, (None, {}))
        pitch = pitch_region(acoustics, span)
        phones = []
        provider_timing = candidate.get("provider_timing")
        if provider_timing:
            raw_word = azure_raw["NBest"][0]["Words"][provider_timing["word_index"]]
            phones = [
                Phone(
                    **phone,
                    timing=span,
                    source="azure_sapi_perceived_reference",
                )
                for phone in reference_phones(raw_word, candidate, s)
            ]
        reading = reading_of(s)
        context_word = next(
            (w for w in words if w.character_start <= s.character_start < w.character_end), None
        )
        if context_word:
            reading = reading.model_copy(update={"context_text": context_word.perceived_text})
        flags = [
            "timing_available" if span else "syllable_timing_unresolved",
            "reference_phone_available" if phones else "phone_evidence_unavailable",
            "asr_uncertainty_available"
            if evidence.get("provider_uncertainty") is not None
            else "asr_uncertainty_unavailable",
            "tone_model_not_integrated",
        ]
        reasons = ["connected_speech_diagnosis_unvalidated"]
        if span is None:
            reasons.append("no_reliable_syllable_boundary")
        if s.reading_source == "unresolved":
            flags.append("ambiguous_reading")
            reasons.append("ambiguous_reading")
        if pitch is None or pitch.usable_frame_count < 5:
            flags.append("insufficient_voiced_frames")
            reasons.append("insufficient_voiced_pitch")
        else:
            flags.append("at_least_five_usable_frames")
        if pitch and pitch.missing_proportion is not None and pitch.missing_proportion > 0.5:
            flags.append("heavy_f0_missingness")
        if pitch and any(not p.get("quality_usable", True) for p in pitch.frames):
            flags.append("tracker_instability")
            reasons.append("tracker_instability")
        if timing_issues:
            flags.append("optional_evidence_issues")
            reasons.extend(timing_issues)
        if audio.provenance == "synthetic_fixture":
            flags.append("synthetic_fixture_not_recorded_speech")
            reasons.append("synthetic_evidence")
        window = (
            Span(
                start_ms=max(0, span.start_ms - context_ms),
                end_ms=min(audio.duration_ms, span.end_ms + context_ms),
                duration_ms=min(audio.duration_ms, span.end_ms + context_ms)
                - max(0, span.start_ms - context_ms),
            )
            if span
            else None
        )
        units.append(
            Unit(
                unit_id=f"u{s.index}",
                perceived_text=s.characters,
                character_start=s.character_start,
                character_end=s.character_end,
                timing=span,
                timing_source=candidate.get("source") if span else None,
                timing_confidence=candidate.get("confidence") if span else None,
                reading=reading,
                provider_timing=provider_timing,
                pitch=pitch,
                phones=phones,
                context=Context(
                    previous_unit=f"u{s.index - 1}" if s.index else None,
                    next_unit=f"u{s.index + 1}" if s.index + 1 < len(readings) else None,
                    window=window,
                ),
                quality_flags=sorted(flags),
                abstention_reasons=sorted(set(reasons)),
            )
        )
    # Only now is intended text allowed into a derivation.
    edits = compare_text(target, text) if target is not None else None
    by_offset = {e.perceived_offset: e for e in edits or [] if e.perceived_offset is not None}
    compared = []
    for unit in units:
        edit = by_offset.get(unit.character_start)
        reasons = list(unit.abstention_reasons)
        if edit and edit.correspondence == "ambiguous_minimum_edit":
            reasons.append("target_perceived_alignment_unresolved")
        if edit and edit.expectation and edit.expectation.surface_tone is None:
            reasons.append("contextual_expectation_unresolved")
        compared.append(
            unit.model_copy(
                update={"target_comparison": edit, "abstention_reasons": sorted(set(reasons))}
            )
        )
    return Record(
        recording_id=recording_id,
        audio=audio,
        mode=mode,
        provider=provider,
        perception=Perception(
            raw_transcript=text,
            normalized_transcript=text,
            transcript_sha256=digest(text.encode()),
            evidence=evidence,
            raw_response=raw_response,
            request_configuration=request_configuration,
            evidence_status=evidence.get("evidence_status", "unknown"),
        ),
        intended_text=target,
        alignment=Alignment(
            reference_text=text,
            source=source,
            evidence_status=(
                evidence.get("evidence_status", "unknown")
                if words and source == "perception_token"
                else alignment_status
            ),
            raw_response=copy.deepcopy(azure_raw),
            words=words,
            issues=timing_issues,
        ),
        acoustics=copy.deepcopy(acoustics),
        units=compared,
        text_comparison=edits,
        configuration={
            "context_before_ms": context_ms,
            "context_after_ms": context_ms,
            "reading_version": READING_VERSION,
            "surface_version": SURFACE_VERSION,
            "azure_mapping_version": MAPPING_VERSION,
            "context_reading_version": CONTEXT_READING_VERSION,
            "quality_policy": "five_usable_frames_and_half_missing_flags_v1",
            "text_comparison": "alphanumeric_codepoints_minimum_edit_v1",
        },
        limitations=[
            "ASR text is what the recognizer heard, not a gold phonetic transcription.",
            "Reference phone labels and scores do not establish observed phones or tones.",
            "Every pronunciation judgment abstains pending connected-speech validation.",
            "No learned tone model or target-relative provider assessment is run "
            "in this research harness.",
            "Timing is conditionally mapped provider evidence, not validated gold boundaries.",
            "Non-Han text is retained but has no pronunciation units; no erhua segmentation.",
        ],
    )


def markdown(record: Record) -> str:
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [f"# Recording {record.recording_id}", "", f"Evidence: {record.audio.provenance}"]
    if record.study_annotations:
        lines += ["", "## Study notes", "", *record.study_annotations]
    if record.intended_text is not None:
        lines += ["", "## Intended", "", record.intended_text]
    lines += [
        "",
        "## What Benma heard",
        "",
        record.perception.raw_transcript,
        "",
        "## Alignment",
        "",
        "| Unit | Perceived | Timing (ms) | Source |",
        "| --- | --- | --- | --- |",
    ]
    for unit in record.units:
        timing = f"{unit.timing.start_ms:g}-{unit.timing.end_ms:g}" if unit.timing else "unresolved"
        lines.append(
            f"| {unit.unit_id} | {cell(unit.perceived_text)} | {timing} | "
            f"{unit.timing_source or 'missing'} |"
        )
    if record.alignment.words:
        lines += ["", "Provider word regions (never equally subdivided):", ""]
        for word in record.alignment.words:
            timing = (
                f"{word.timing.start_ms:g}-{word.timing.end_ms:g} ms" if word.timing else "missing"
            )
            lines.append(
                f"- {cell(word.perceived_text)}: {timing}; syllables {word.syllable_timing_status}"
            )
    if record.acoustics is not None:
        frames = record.acoustics.get("f0", [])
        voiced = sum(p.get("f0_hz") is not None for p in frames)
        selected = sum(p.get("selected_f0_hz") is not None for p in frames)
        lines += [
            "",
            "## Recording acoustics",
            "",
            f"Whole recording: {voiced}/{len(frames)} frames with raw gated F0; "
            f"{selected} selected frames. Full contours and quality details are in record.json.",
            "Untimed syllables cannot inherit these whole-recording measurements.",
        ]
    for unit in record.units:
        lines += [
            "",
            f"## Unit {unit.unit_id}: {unit.perceived_text}",
            "",
            f"- Timing: {unit.timing.start_ms:g}-{unit.timing.end_ms:g} ms; "
            f"source {unit.timing_source}."
            if unit.timing
            else "- Timing: unresolved.",
            f"- Reading: {unit.reading.pinyin or 'unresolved'}; lexical tone "
            f"{unit.reading.lexical_tone}; source {unit.reading.status}.",
        ]
        if unit.reading.context_text:
            lines.append(f"- Perceived word context: {unit.reading.context_text}.")
        if unit.reading.ambiguous:
            lines.append(f"- Reading alternatives: {', '.join(unit.reading.alternatives)}.")
        if unit.phones:
            lines.append(
                "- Reference phones (reference-conditioned, not detected sounds): "
                + ", ".join(f"{p.label} (score {p.score})" for p in unit.phones)
            )
        else:
            lines.append(
                "- Reference phones: no accepted unit attachment; raw labels, if supplied, "
                "remain in alignment evidence (reference-conditioned, not detected sounds)."
            )
        if unit.pitch:
            p = unit.pitch
            lines.append(
                f"- Observed pitch: {p.usable_frame_count}/{p.frame_count} usable frames; "
                f"raw F0 missing proportion {p.missing_proportion}."
            )
        else:
            lines.append("- Observed pitch: no timed saved acoustic slice available.")
        if unit.target_comparison:
            edit = unit.target_comparison
            lines.append(
                f"- Target relationship: {edit.operation}; intended {edit.intended}; "
                f"{edit.correspondence}. No acoustic cause inferred."
            )
            if edit.expectation:
                exp = edit.expectation
                lines.append(
                    f"- Expected pronunciation: {exp.reading.pinyin or 'unresolved'}; lexical "
                    f"{exp.reading.lexical_tone}, surface {exp.surface_tone} ({exp.rule})."
                )
        lines += [
            "- Evidence quality: " + ", ".join(unit.quality_flags),
            f"- {unit.judgment}: " + ", ".join(unit.abstention_reasons),
        ]
    deletions = [e for e in record.text_comparison or [] if e.operation == "deletion"]
    if deletions:
        lines += [
            "",
            "Target text absent from perception: " + ", ".join(e.intended for e in deletions),
        ]
    lines += ["", "## Limits", "", *[f"- {note}" for note in record.limitations]]
    if record.alignment.issues:
        lines.append("- Timing issues: " + ", ".join(record.alignment.issues))
    return "\n".join(lines) + "\n"


def run_live(audio_path, *, settings, use_azure=False):
    """No target parameter exists at this boundary; failures in optional evidence are partial."""
    if settings.perception_provider != "openai":
        raise ValueError("live probe requires BENMA_PERCEPTION_PROVIDER=openai")
    original = audio_path.read_bytes()
    meta = inspect_audio(audio_path, settings)
    if (
        len(original) > settings.max_upload_bytes
        or meta.duration_seconds > settings.max_audio_duration_seconds
    ):
        raise ValueError("audio exceeds production ingest limits")
    canonical = canonicalize(audio_path, settings)
    provider = build_perception_provider(settings)
    response = provider.perceive(
        UnknownTargetPerceptionInput(
            utterance_id=uuid.uuid4(),
            canonical_audio=canonical,
            mime_type="audio/wav",
            language_hint="zh",
            timeout_seconds=30,
        )
    )
    evidence = response.evidence.normalized()
    acoustics, azure_raw, issues = None, None, []
    with tempfile.TemporaryDirectory(prefix="benma-connected-") as tmp:
        wav = Path(tmp) / "canonical.wav"
        wav.write_bytes(canonical)
        duration_ms = inspect_audio(wav, settings).duration_seconds * 1000
        try:
            analyzer = PraatAcousticAnalyzer()
            acoustics = {
                **analyzer.analyze(wav),
                "algorithm": analyzer.algorithm_name,
                "algorithm_version": analyzer.algorithm_version,
                "parameters": analyzer.parameters,
            }
            acoustics["display_contour"] = display_contour(acoustics["f0"]).model_dump(mode="json")
        except Exception as exc:
            issues.append(f"pitch_unavailable:{type(exc).__name__}")
        native_readings, native_spans, *_ = alignment_evidence(
            evidence["transcript"], evidence, None, duration_ms
        )
        if use_azure and (not native_readings or len(native_spans) != len(native_readings)):
            if duration_ms > 30000:
                issues.append("azure_short_audio_limit_30_seconds")
            elif not settings.azure_speech_key or not settings.azure_speech_region:
                issues.append("azure_credentials_unavailable")
            else:
                try:
                    azure_raw = request_azure_speech(
                        audio=canonical,
                        key=settings.azure_speech_key.get_secret_value(),
                        region=settings.azure_speech_region,
                        config={**AZURE_TIMING_CONFIG, "ReferenceText": evidence["transcript"]},
                        timeout_seconds=settings.alignment_timeout_seconds,
                    )
                    timing_payload(azure_raw)
                except Exception as exc:
                    issues.append(f"alignment_unavailable:{type(exc).__name__}")

    return {
        "audio": Audio(
            path=str(audio_path.resolve()),
            sha256=digest(original),
            canonical_sha256=digest(canonical),
            duration_ms=duration_ms,
            provenance="recorded_audio",
        ),
        "provider": provider.product_name,
        "evidence": evidence,
        "raw_response": response.raw_payload,
        "azure_raw": azure_raw,
        "acoustics": acoustics,
        "issues": issues,
        "alignment_status": "live_provider" if azure_raw else "unavailable",
        "request_configuration": provider.request_configuration,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--audio", type=Path)
    source.add_argument(
        "--fixture", type=Path, help="Synthetic structural evidence; no network or audio required"
    )
    parser.add_argument("--target")
    parser.add_argument("--mode", choices=("free", "practice"))
    parser.add_argument("--alignment", choices=("none", "azure"), default="none")
    parser.add_argument("--context-ms", type=float, default=150)
    parser.add_argument(
        "--output", type=Path, required=True, help="New output directory; refuses overwrite"
    )
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output directory already exists; use a new path to preserve evidence")
    if not math.isfinite(args.context_ms) or args.context_ms < 0:
        parser.error("context-ms must be finite and nonnegative")
    if args.fixture:
        if args.alignment != "none":
            parser.error("fixture mode never contacts an alignment provider")
        values = json.loads(args.fixture.read_text())
        values["audio"] = Audio(
            duration_ms=values.pop("duration_ms"), provenance="synthetic_fixture"
        )
        values["evidence"]["evidence_status"] = "synthetic_fixture"
        if (
            values.pop("alignment_reference_text", values["evidence"]["transcript"])
            != values["evidence"]["transcript"]
        ):
            parser.error("fixture alignment reference must equal perceived text")
        values["alignment_status"] = "synthetic_fixture"
        recording_id = args.fixture.stem
    else:
        values = run_live(args.audio, settings=Settings(), use_azure=args.alignment == "azure")
        recording_id = str(uuid.uuid4())
    record = build_record(
        recording_id=recording_id,
        **values,
        target=args.target,
        mode=args.mode or ("practice" if args.target is not None else "free"),
        context_ms=args.context_ms,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "record.json").write_text(record.model_dump_json(indent=2) + "\n")
    (args.output / "report.md").write_text(markdown(record))
    print(args.output / "report.md")


if __name__ == "__main__":
    main()
