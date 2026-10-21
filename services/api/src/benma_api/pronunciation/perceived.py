"""Transcript-conditioned visualization. No target, semantic context, or grading input.

Dictionary readings and lexical shapes explain the perceived text, not learner intent.
Missing alignment never prevents visualizing independently measured pitch.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC
from importlib.metadata import version
from typing import Any

from pypinyin.contrib.tone_convert import to_tone, to_tone3
from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.audio.presence import require_speech
from benma_api.config import Settings
from benma_api.db.models import (
    AudioAsset,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    PronunciationTarget,
    Utterance,
)
from benma_api.errors import AnalysisUnsupportedError, AuthorizationError
from benma_api.pronunciation.acoustics import (
    AcousticAnalysisPort,
    AcousticAnalysisService,
    build_acoustic_analyzer,
)
from benma_api.pronunciation.alignment import (
    AlignmentPort,
    AlignmentRequest,
    build_aligner,
    validate_alignment,
)
from benma_api.pronunciation.azure_alignment import azure_word_timing_groups
from benma_api.pronunciation.chunks import CHUNK_POLICY_VERSION, pronunciation_chunk_candidates
from benma_api.pronunciation.contours import (
    CLASSIFIER_VERSION,
    DISPLAY_VERSION,
    classify_contour,
    simplify_display,
    syllable_contour,
)
from benma_api.pronunciation.pitch_evidence import (
    display_from_track,
    gate_observation,
    interpretation_eligibility,
    load_pitch_track,
    project_pitch,
)
from benma_api.pronunciation.pitch_types import ELIGIBILITY_VERSION, TRACK_VERSION
from benma_api.pronunciation.readings import READING_VERSION, resolve_run
from benma_api.pronunciation.surface import (
    LEARNER_SURFACE_VERSION,
    SURFACE_VERSION,
    SurfaceExpectation,
    learner_surface_expectations,
    surface_expectations,
)
from benma_api.pronunciation.targets import parse_corrected_pinyin
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence
from benma_api.schemas import (
    ExpectedTonePoint,
    MeasuredPitchPoint,
    PerceivedAnalysisData,
    PerceivedReadingResponse,
    PerceivedSpeechAnalysisResponse,
    PerceivedSyllable,
)
from benma_api.storage.audio_store import AudioObjectStore

LOGGER = logging.getLogger(__name__)
VERSION = "perceived-speech-v6-utterance-evidence"
# Chao 55/35/214/51, rescaled from 1..5 to 0..1; never measured Hz.
# https://linguistics.berkeley.edu/acip/appendix/languages/chinese/chinese_tone.html
# Neutral tone has no context-free fixed shape.
LEXICAL_SHAPES = {1: [1.0, 1.0], 2: [0.5, 1.0], 3: [0.25, 0.0, 0.75], 4: [1.0, 0.0]}
HAN_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


def perceived_syllables(
    text: str,
    evidence: dict[str, Any],
    timings: dict[str, float] | None = None,
) -> list[PerceivedSyllable]:
    """Reuse the existing dictionary; skip non-Han runs without losing character offsets.

    Only normalized pronunciation tokens with exact character offsets may override a
    dictionary reading. Ordinary ASR text/logprob tokens do not establish pronunciation.
    Phrase/grammar context is limited to this exact transcript; inference is never consulted.
    """
    started = time.perf_counter()
    grounded: dict[int, str] = {}
    for token in evidence.get("tokens") or []:
        if not isinstance(token, dict):
            continue
        start, end = token.get("character_start"), token.get("character_end")
        if (
            type(start) is int
            and type(end) is int
            and 0 <= start < end <= len(text)
            and end == start + 1
            and token.get("text") == text[start:end]
            and isinstance(token.get("pinyin"), str)
        ):
            try:
                parsed = parse_corrected_pinyin(text[start:end], token["pinyin"])
                grounded[start] = parsed.pinyin_syllables[0]
            except ValueError:
                continue
    syllables: list[PerceivedSyllable] = []
    for match in HAN_RUN.finditer(text):
        for offset, (reading, source, options) in enumerate(resolve_run(match.group())):
            start = match.start() + offset
            selected = grounded.get(start) or reading
            tone = (
                (0 if selected[-1:] == "5" else int(selected[-1]))
                if (selected and selected[-1:] in "12345")
                else None
            )
            if tone is None:
                selected = None
            heights = LEXICAL_SHAPES.get(tone, []) if tone is not None else []
            syllables.append(
                PerceivedSyllable(
                    index=len(syllables),
                    character_start=start,
                    character_end=start + 1,
                    characters=text[start : start + 1],
                    pinyin=to_tone(selected.replace("5", "")) if selected else None,
                    lexical_tone=tone,
                    reading_source="perception_token"
                    if start in grounded
                    else (source if selected else "unresolved"),
                    resolution_confidence="high" if selected else "unresolved",
                    alternatives=list(options),
                    expected_tone=[
                        ExpectedTonePoint(position=i / (len(heights) - 1), height=h)
                        for i, h in enumerate(heights)
                    ],
                )
            )
    if timings is not None:
        timings["reading_resolution"] = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    surface = surface_expectations(
        text, [s.character_start for s in syllables], [s.lexical_tone for s in syllables]
    )
    for syllable, expectation in zip(syllables, surface, strict=True):
        syllable.expected_surface_tone = expectation.tone  # type: ignore[assignment]
        syllable.surface_rule = expectation.rule
        syllable.surface_rule_version = SURFACE_VERSION
        heights = LEXICAL_SHAPES.get(expectation.tone, []) if expectation.tone is not None else []
        syllable.expected_surface_shape = [
            ExpectedTonePoint(position=i / (len(heights) - 1), height=h)
            for i, h in enumerate(heights)
        ]
    if timings is not None:
        timings["surface_resolution"] = (time.perf_counter() - started) * 1000
    return syllables


def unresolved_spans(text: str) -> list[dict[str, Any]]:
    return [
        {"text": match.group(), "character_start": match.start(), "character_end": match.end()}
        for match in re.finditer(r"[^\u3400-\u4dbf\u4e00-\u9fff\W_]+", text)
    ]


def reading_response(perception: PerceptionRun) -> PerceivedReadingResponse:
    if perception.status != "succeeded" or not perception.transcript:
        raise AnalysisUnsupportedError("successful speech perception is required")
    return PerceivedReadingResponse(
        perception_run_id=perception.id,
        alignment_reference_text=perception.transcript,
        reading_version=READING_VERSION,
        surface_version=SURFACE_VERSION,
        syllables=perceived_syllables(perception.transcript, perception.normalized_result or {}),
        unresolved_spans=unresolved_spans(perception.transcript),
    )


def analysis_response(run: PerceivedSpeechAnalysis) -> PerceivedSpeechAnalysisResponse:
    data = PerceivedAnalysisData.model_validate(run.result)
    for syllable in data.syllables:
        # Old analyses lack completeness evidence: preserve saved history but
        # never serialize an old confident category as newly eligible feedback.
        syllable.observed_contour = gate_observation(
            syllable.observed_contour, syllable.pitch_eligibility
        )
    # Also enrich old persisted analyses using their saved timing payload. Pure
    # presentation: no provider call, reclassification or mutation of stored truth.
    if (
        "timing_groups" not in run.result
        and data.alignment_status != "synthetic"
        and data.evidence_status != "synthetic_replay"
    ):
        timing = run.result.get("timing_evidence", {})
        if timing.get("provider") == "azure_speech_alignment_only" and timing.get("id"):
            data.timing_groups = azure_word_timing_groups(
                timing.get("provider_timing") or {},
                run.alignment_reference_text,
                data.syllables,
                duration_seconds=data.duration_seconds,
                timing_evidence_id=timing["id"],
            )
    # Presentation metadata is derived from this attempt's saved perceived text
    # and readings, including history. Never persist it as fresh acoustic evidence.
    data.pronunciation_chunk_policy = CHUNK_POLICY_VERSION
    data.pronunciation_chunk_candidates = pronunciation_chunk_candidates(
        run.alignment_reference_text, data.syllables
    )
    return PerceivedSpeechAnalysisResponse(
        id=run.id,
        perception_run_id=run.perception_run_id,
        utterance_id=run.utterance_id,
        alignment_reference_text=run.alignment_reference_text,
        analyzer_version=run.analyzer_version,
        status=run.status,
        error_code=run.error_code,
        latency_ms=run.latency_ms,
        created_at=run.created_at if run.created_at.tzinfo else run.created_at.replace(tzinfo=UTC),
        data=data,
    )


class PerceivedSpeechAnalysisService:
    def __init__(
        self,
        db: Session,
        store: AudioObjectStore,
        settings: Settings,
        *,
        analyzer: AcousticAnalysisPort | None = None,
        aligner: AlignmentPort | None = None,
    ) -> None:
        self.db, self.store, self.settings = db, store, settings
        self.analyzer = analyzer or build_acoustic_analyzer(settings)
        self.aligner = aligner or build_aligner(settings)

    def run(
        self,
        *,
        account_id: uuid.UUID,
        perception_run_id: uuid.UUID,
        dev_learned_target_id: uuid.UUID | None = None,
    ) -> PerceivedSpeechAnalysis:
        target = None
        if dev_learned_target_id is not None:
            if (
                not self.settings.enable_dev_learned_tone
                or self.settings.environment == "production"
            ):
                raise AnalysisUnsupportedError("learned dev target comparison is disabled")
            target = self.db.get(PronunciationTarget, dev_learned_target_id)
            if target is None or target.account_id != account_id:
                raise AuthorizationError("pronunciation target was not found")
        # Serialize duplicate requests. NO KEY UPDATE allows interpretation's FK insertion.
        perception = self.db.scalar(
            select(PerceptionRun)
            .where(
                PerceptionRun.id == perception_run_id,
                PerceptionRun.account_id == account_id,
            )
            .with_for_update(key_share=True)
        )
        if perception is None:
            raise AuthorizationError("perception run was not found")
        if (
            perception.status != "succeeded"
            or not perception.transcript
            or not perception.transcript.strip()
        ):
            raise AnalysisUnsupportedError("successful speech perception is required")
        utterance = self.db.scalar(
            select(Utterance).where(
                Utterance.id == perception.utterance_id,
                Utterance.account_id == account_id,
            )
        )
        if utterance is None:
            raise AuthorizationError("utterance was not found")
        asset = self.db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if asset is None or asset.account_id != account_id or asset.duration_seconds is None:
            raise AuthorizationError("canonical audio was not found")
        duration_seconds = asset.duration_seconds
        require_speech(self.store.read(asset.storage_key), transcript=perception.transcript)
        config = {
            "normalization": "exact-persisted-transcript-v1",
            "reading_engine": f"pypinyin-{version('pypinyin')}",
            "reading_policy": READING_VERSION,
            "expected_tone": "conservative-surface-shapes-v1",
            "surface_rules": SURFACE_VERSION,
            "display_filter": DISPLAY_VERSION,
            "observed_classifier": CLASSIFIER_VERSION,
            "pitch_track": TRACK_VERSION,
            "pitch_eligibility": ELIGIBILITY_VERSION,
            "analyzer_version": VERSION,
            "acoustic_algorithm": self.analyzer.algorithm_name,
            "acoustic_version": self.analyzer.algorithm_version,
            "acoustic_parameters": self.analyzer.parameters,
            "aligner": self.aligner.algorithm_name,
            "aligner_version": self.aligner.algorithm_version,
            "alignment_dictionary": self.settings.mfa_dictionary,
            "alignment_model": self.settings.mfa_acoustic_model,
            "alignment_timeout_seconds": self.settings.alignment_timeout_seconds,
            "timing_strategy": "exact-asr-then-configured-aligner-v1",
            "aligner_configuration": (
                getattr(self.aligner, "configuration", {})
                if isinstance(getattr(self.aligner, "configuration", {}), dict)
                else {}
            ),
        }
        if self.settings.enable_dev_learned_tone and self.settings.environment != "production":
            config["dev_learned_tone"] = "dev-fast-learned-tone-v1"
            config["dev_learner_surface"] = LEARNER_SURFACE_VERSION
            config["dev_learned_target_id"] = str(target.id) if target else None
        config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        existing = self.db.scalar(
            select(PerceivedSpeechAnalysis).where(
                PerceivedSpeechAnalysis.perception_run_id == perception.id,
                PerceivedSpeechAnalysis.configuration_sha256 == config_hash,
            )
        )
        if existing is not None:
            self.db.commit()
            return existing
        started = time.perf_counter()
        # This snapshot is already the provider's persisted normalized perception text.
        # No trim, punctuation replacement, correction, or inferred wording is written over it.
        text = perception.transcript
        timings: dict[str, float] = {}
        syllables = perceived_syllables(text, perception.normalized_result or {}, timings)

        acoustic_compute = AcousticAnalysisService(self.db, self.store, self.analyzer).prepare(
            account_id=account_id, utterance_id=utterance.id
        )
        request = AlignmentRequest(
            audio_path=self.store.path_for_processing(asset.storage_key),
            reference_text=text,
            reference_kind="perceived_text",
            pinyin_syllables=[s.pinyin or "" for s in syllables],
            duration_seconds=asset.duration_seconds,
            timeout_seconds=(
                self.settings.mfa_timeout_seconds
                if self.settings.alignment_provider == "mfa"
                else self.settings.alignment_timeout_seconds
            ),
        )

        timing_evidence_id = str(uuid.uuid4())
        timing_evidence: dict[str, Any] = {
            "id": timing_evidence_id,
            "utterance_id": str(utterance.id),
            "perception_run_id": str(perception.id),
            "reference_text": text,
            "configuration": config["aligner_configuration"],
            "reference_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "provider": self.aligner.algorithm_name,
            "provider_version": self.aligner.algorithm_version,
        }

        def validated(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
            selected: list[dict[str, Any]] = []
            for order, original in enumerate(units):
                index = original.get("syllable_index", order)
                if type(index) is not int or not 0 <= index < len(syllables):
                    return []
                syllable = syllables[index]
                label = str(original.get("label", "")).strip()
                numeric = to_tone3(syllable.pinyin or "", neutral_tone_with_five=True)
                if label != syllable.characters and (
                    not numeric or to_tone3(label, neutral_tone_with_five=True) != numeric
                ):
                    return []
                selected.append({**original, "syllable_index": index})
            selected.sort(key=lambda u: u["syllable_index"])
            if len({u["syllable_index"] for u in selected}) != len(selected):
                return []
            try:
                # Silence is not a missing syllable. Coverage is of transcript units,
                # not of the full recording duration (which may include long pauses).
                quality = validate_alignment(
                    selected,
                    target_count=len(selected),
                    duration_seconds=duration_seconds,
                    check_audio_coverage=False,
                )
            except (KeyError, TypeError, ValueError, OverflowError):
                return []
            return selected if quality["usable_for_syllable_visualization"] else []

        token_units: list[dict[str, Any]] = []
        for token in (perception.normalized_result or {}).get("tokens") or []:
            if not isinstance(token, dict) or not isinstance(token.get("timing"), dict):
                continue
            matching = next(
                (
                    s
                    for s in syllables
                    if type(token.get("character_start")) is int
                    and type(token.get("character_end")) is int
                    and token["character_start"] == s.character_start
                    and token["character_end"] == s.character_end
                    and token.get("text") == s.characters
                ),
                None,
            )
            if matching:
                token_units.append(
                    {
                        **token["timing"],
                        "label": matching.characters,
                        "syllable_index": matching.index,
                        "source": "perception_token",
                        "source_evidence_id": str(perception.id),
                    }
                )
        token_units = validated(token_units)
        synthetic_perception = (perception.normalized_result or {}).get(
            "evidence_status"
        ) == "synthetic_replay"

        def align() -> tuple[list[dict[str, Any]], str, str | None, int]:
            alignment_started = time.perf_counter()
            units = token_units
            synthetic = synthetic_perception
            failure_code = "alignment_unavailable"
            if not syllables:
                return [], "unavailable", "no_mandarin_characters", 0
            if len(token_units) != len(syllables):
                try:
                    if self.aligner.algorithm_name == "disabled":
                        failure_code = "alignment_disabled"
                    response = self.aligner.align(request)
                    timing_evidence["evidence_status"] = response.evidence_status
                    provider_units = validated(response.units)
                    synthetic = synthetic or response.evidence_status == "synthetic_replay"
                    # Never allow replay partitions to displace real token timing.
                    if response.evidence_status == "synthetic_replay" and token_units:
                        provider_units, synthetic = [], synthetic_perception
                    if provider_units:
                        combined = {
                            u["syllable_index"]: {
                                **u,
                                "source": u.get("source", self.aligner.algorithm_name),
                                "source_evidence_id": timing_evidence_id,
                            }
                            for u in provider_units
                        }
                        combined.update({u["syllable_index"]: u for u in token_units})
                        units = validated(list(combined.values())) or token_units
                    if self.aligner.algorithm_name == "azure_speech_alignment_only":
                        timing_evidence["provider_timing"] = response.raw_result
                except Exception as exc:
                    # Provider details never escape this optional branch.
                    failure_code = str(getattr(exc, "code", "alignment_unavailable"))
            timing_evidence["units"] = units
            sources = sorted({u.get("source", self.aligner.algorithm_name) for u in units})
            timing_evidence["sources"] = sources
            state = (
                "synthetic"
                if units and synthetic
                else "aligned"
                if len(units) == len(syllables)
                else "partial"
                if units
                else "unavailable"
            )
            timing_evidence.update(
                status=state,
                error_code=None if state == "aligned" else failure_code,
                latency_ms=round((time.perf_counter() - alignment_started) * 1000),
            )
            return (
                units,
                state,
                None if state == "aligned" else failure_code,
                round((time.perf_counter() - alignment_started) * 1000),
            )

        # Prepared closures have no SQL access; persist only on this request's owning session.
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="perceived-analysis") as pool:
            acoustic_future = pool.submit(acoustic_compute)
            alignment_future = pool.submit(align)
            acoustic = acoustic_future.result()
            units, alignment_status, alignment_error, alignment_ms = alignment_future.result()
        processing_started = time.perf_counter()
        raw_pitch = (acoustic.normalized_result or {}).get("f0", [])
        track = load_pitch_track(
            acoustic.normalized_result or {},
            audio_sha256=asset.sha256,
            tracker_source=acoustic.algorithm,
            tracker_version=acoustic.algorithm_version,
            parameters=acoustic.parameters,
        )
        display = display_from_track(track)
        timings["display_contour"] = (time.perf_counter() - processing_started) * 1000
        timings["pitch_projection"] = 0
        timings["pitch_eligibility"] = 0
        timings["contour_slicing"] = 0
        timings["quality_gate_and_classification"] = 0
        for unit in units:
            syllable = syllables[unit["syllable_index"]]
            syllable.start_seconds = unit["start_seconds"]
            syllable.end_seconds = unit["end_seconds"]
            syllable.timing_source = unit.get("source", self.aligner.algorithm_name)
            syllable.timing_evidence_id = unit.get("source_evidence_id", timing_evidence_id)
            if alignment_status in {"aligned", "partial"} and acoustic.status == "succeeded":
                slice_started = time.perf_counter()
                syllable.display_contour = syllable_contour(
                    display, unit["start_seconds"], unit["end_seconds"]
                )
                timings["contour_slicing"] += (time.perf_counter() - slice_started) * 1000
                projection_started = time.perf_counter()
                syllable.pitch_projection = project_pitch(
                    track,
                    unit["start_seconds"],
                    unit["end_seconds"],
                    timing_source=syllable.timing_source,
                    timing_evidence_id=syllable.timing_evidence_id,
                )
                timings["pitch_projection"] += (time.perf_counter() - projection_started) * 1000
                eligibility_started = time.perf_counter()
                syllable.pitch_eligibility = interpretation_eligibility(
                    track, syllable.pitch_projection
                )
                timings["pitch_eligibility"] += (time.perf_counter() - eligibility_started) * 1000
                classify_started = time.perf_counter()
                syllable.observed_contour = classify_contour(
                    syllable.display_contour,
                    unit["start_seconds"],
                    unit["end_seconds"],
                    raw=raw_pitch,
                    timings=timings,
                    pitch_track=track,
                )
                syllable.observed_contour = gate_observation(
                    syllable.observed_contour, syllable.pitch_eligibility
                )
                timings["quality_gate_and_classification"] += (
                    time.perf_counter() - classify_started
                ) * 1000
                syllable.display_contour = simplify_display(
                    syllable.display_contour,
                    preserve_seconds=syllable.observed_contour.features.get(
                        "first_reliable_core_seconds"
                    ),
                )
        group_started = time.perf_counter()
        timing_groups = (
            azure_word_timing_groups(
                timing_evidence.get("provider_timing") or {},
                text,
                syllables,
                duration_seconds=duration_seconds,
                timing_evidence_id=timing_evidence_id,
            )
            if alignment_status != "synthetic"
            and not synthetic_perception
            and timing_evidence.get("evidence_status") != "synthetic_replay"
            else []
        )
        timings["grouped_timing"] = (time.perf_counter() - group_started) * 1000
        for group in timing_groups if acoustic.status == "succeeded" else []:
            group.pitch_projection = project_pitch(
                track,
                group.start_seconds,
                group.end_seconds,
                timing_source=group.source,
                timing_evidence_id=group.timing_evidence_id,
            )
            group.pitch_eligibility = interpretation_eligibility(track, group.pitch_projection)
        tone_graph = sentence_pitch_evidence(
            raw_pitch,
            display,
            syllables,
            timing_groups,
            track=track if acoustic.status == "succeeded" else None,
        )
        learned = None
        if self.settings.enable_dev_learned_tone and self.settings.environment != "production":
            from benma_api.pronunciation.learned import analyze_learned

            deterministic_projection_ms = (time.perf_counter() - processing_started) * 1000
            target_matches = True
            expected = [s.model_copy(deep=True) for s in syllables]
            if target:
                target_syllables = perceived_syllables(target.text, {})
                target_matches = [s.characters for s in target_syllables] == [
                    s.characters for s in syllables
                ] and len(target.pinyin_syllables) == len(syllables)
                if target_matches:
                    expectations = surface_expectations(
                        target.text,
                        [s.character_start for s in target_syllables],
                        target.lexical_tones,
                    )
                    for s, reading, lexical, surface in zip(
                        expected,
                        target.pinyin_syllables,
                        target.lexical_tones,
                        expectations,
                        strict=True,
                    ):
                        s.pinyin = to_tone(reading.replace("5", ""))
                        s.lexical_tone = lexical  # type: ignore[assignment]
                        s.expected_surface_tone = surface.tone  # type: ignore[assignment]
                        s.surface_rule = surface.rule
                else:
                    for s in expected:
                        s.expected_surface_tone = None
                        s.surface_rule = "target_transcript_mapping_unresolved"
            surfaces = (
                learner_surface_expectations(
                    target.text if target else text,
                    [s.character_start for s in (target_syllables if target else syllables)],
                    [s.lexical_tone for s in expected],
                )
                if target_matches
                else [
                    SurfaceExpectation(None, "target_transcript_mapping_unresolved")
                    for s in expected
                ]
            )
            learned = analyze_learned(
                audio=request.audio_path,
                sha256=asset.sha256,
                duration=duration_seconds,
                syllables=syllables,
                graph=tone_graph,
                raw=acoustic.normalized_result or {},
                recorded=alignment_status in {"aligned", "partial"}
                and not synthetic_perception
                and acoustic.status == "succeeded",
                expected=expected,
                target_text=target.text if target else text,
                intended=target is not None,
                surfaces=surfaces,
            )
            learned.timings_ms.update(
                azure_timing=alignment_ms,
                deterministic_f0=acoustic.latency_ms or 0,
                deterministic_projection=deterministic_projection_ms,
                backend_analysis_total=(time.perf_counter() - started) * 1000,
            )
            learned.target_mapping_resolved = target_matches
        display = simplify_display(display)
        timings["contour_processing_classification"] = (
            time.perf_counter() - processing_started
        ) * 1000
        result = acoustic.normalized_result or {}
        pitch = [MeasuredPitchPoint.model_validate(point) for point in result.get("mobile_f0", [])]
        pitch_available = any(point.f0_hz is not None for point in pitch)
        issues = result.get("recording_quality", {}).get("issues", [])
        observations = [
            "Pitch is measured from your recording; gaps have no reliable voiced pitch.",
            "Expected shapes use conservative surface-tone rules; dictionary tones stay separate.",
        ]
        if alignment_status == "unavailable":
            observations.append(
                "Syllable timing is unavailable; the tone strip follows text order."
            )
        if any(s.reading_source == "unresolved" for s in syllables):
            observations.append(
                "Some characters have multiple readings; their tone pattern is unresolved."
            )
        if issues:
            observations.append("Recording quality limits the pitch evidence.")
        data = PerceivedAnalysisData(
            dev_learned_tone=learned,
            pitch_track_evidence_id=track.evidence_id if acoustic.status == "succeeded" else None,
            tone_graph=tone_graph,
            timing_groups=timing_groups,
            display_contour=display,
            expected_tone_basis="conservative_surface_tones",
            timing_source="+".join(timing_evidence.get("sources", [])) or None,
            timing_evidence_id=timing_evidence_id,
            timing_coverage=len(units) / len(syllables)
            if syllables and alignment_status != "synthetic"
            else 0,
            unresolved_spans=unresolved_spans(text),
            timings_ms=timings,
            syllables=syllables,
            measured_pitch=pitch,
            duration_seconds=asset.duration_seconds,
            voiced_fraction=result.get("contour_features", {}).get("voiced_fraction"),
            pitch_status="available" if pitch_available else "unavailable",
            alignment_status=alignment_status,
            alignment_error_code=alignment_error,
            quality_issues=issues,
            observations=observations,
            pitch_latency_ms=acoustic.latency_ms,
            alignment_latency_ms=alignment_ms,
            evidence_status="synthetic_replay"
            if alignment_status == "synthetic"
            or (perception.normalized_result or {}).get("evidence_status") == "synthetic_replay"
            else "recorded_audio",
        )
        persistence_started = time.perf_counter()
        self.db.add(acoustic)
        self.db.flush()
        timings["persistence_flush"] = (time.perf_counter() - persistence_started) * 1000
        data.timings_ms = {key: round(value, 3) for key, value in timings.items()}
        run = PerceivedSpeechAnalysis(
            account_id=account_id,
            utterance_id=utterance.id,
            perception_run_id=perception.id,
            audio_asset_id=asset.id,
            audio_sha256=asset.sha256,
            acoustic_run_id=acoustic.id,
            alignment_reference_text=text,
            analyzer_version=VERSION,
            configuration_sha256=config_hash,
            configuration=config,
            result={**data.model_dump(mode="json"), "timing_evidence": timing_evidence},
            latency_ms=round((time.perf_counter() - started) * 1000),
            status="failed"
            if acoustic.status == "failed"
            else ("succeeded" if pitch_available and alignment_status == "aligned" else "partial"),
            error_code="pitch_unavailable" if acoustic.status == "failed" else None,
        )
        self.db.add(run)
        commit_started = time.perf_counter()
        self.db.commit()
        LOGGER.info(
            "perceived_speech_analysis_timing",
            extra={
                "reading_ms": timings["reading_resolution"],
                "pitch_ms": acoustic.latency_ms,
                "alignment_ms": alignment_ms,
                "contour_ms": timings["contour_processing_classification"],
                "persistence_commit_ms": round((time.perf_counter() - commit_started) * 1000, 3),
                "total_ms": round((time.perf_counter() - started) * 1000, 3),
            },
        )
        return run
