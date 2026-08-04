"""Versioned, truth-preserving benchmark data contracts.

The central safety property is negative: ``UnknownTargetPerceptionRequest`` has
no field for intended text, pinyin, context, or a semantic prompt. Extra fields
are rejected by Pydantic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

SCHEMA_VERSION: Literal["1.0.0"] = "1.0.0"
Score = Annotated[float, Field(ge=0.0, le=100.0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
NonNegative = Annotated[float, Field(ge=0.0)]


class StrictModel(BaseModel):
    """Immutable base contract that rejects accidental/vendor-specific fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_assignment=True)


class SpeakerCategory(StrEnum):
    NATIVE_CONTROL = "native_control"
    LEARNER = "learner"
    INTENTIONALLY_CORRUPTED = "intentionally_corrupted"
    SYNTHETIC_REFERENCE = "synthetic_reference"


class CalibrationMode(StrEnum):
    LEARNER_CORRECT = "learner_correct"
    LEARNER_INTENTIONAL_TONE_ERROR = "learner_intentional_tone_error"
    LEARNER_INTENTIONAL_INITIAL_ERROR = "learner_intentional_initial_error"
    LEARNER_INTENTIONAL_FINAL_ERROR = "learner_intentional_final_error"
    NATIVE_CONTROL = "native_control"
    NEGATIVE_CONTROL = "negative_control"
    SPONTANEOUS_NATURAL = "spontaneous_natural"


class ProviderLifecycle(StrEnum):
    DOCUMENTED = "documented"
    IMPLEMENTED = "implemented"
    FIXTURE_VALIDATED = "fixture_validated"
    LIVE_VALIDATED = "live_validated"
    PILOT_EVALUATED = "pilot_evaluated"
    CALIBRATED = "calibrated"
    DISQUALIFIED = "disqualified"


class CalibrationMaturity(StrEnum):
    RAW_EVIDENCE = "raw_evidence"
    EXPERIMENTAL = "experimental"
    CALIBRATED = "calibrated"


class CalibrationScope(StrEnum):
    NONE = "none"
    PERSONAL = "personal"
    PILOT_POPULATION = "pilot_population"
    GENERAL = "general"


class EvidenceOrigin(StrEnum):
    UNKNOWN = "unknown"
    LIVE_PROVIDER = "live_provider"
    LIVE_CAPTURED_SANITIZED = "live_captured_sanitized"
    DOCUMENTATION_CONTRACT_EXAMPLE = "documentation_contract_example"
    CONSTRUCTED_FIXTURE = "constructed_fixture"
    SYNTHETIC_REPLAY = "synthetic_replay"


class ListenerRole(StrEnum):
    ORDINARY_NATIVE_LISTENER = "ordinary_native_listener"
    LINGUISTICALLY_TRAINED_LISTENER = "linguistically_trained_listener"


class SemanticSeverity(StrEnum):
    TECHNICAL_ONLY = "technical_only"
    NOTICEABLE_BUT_UNDERSTOOD = "noticeable_but_understood"
    CONFUSING = "confusing"
    REQUIRES_REPETITION = "requires_repetition"
    WRONG_WORD_PERCEIVED = "wrong_word_perceived"


class HumanConsensusClass(StrEnum):
    STRONG_ACCEPT = "strong_accept"
    ACCEPTABLE_WITH_ERROR = "acceptable_with_error"
    AMBIGUOUS = "ambiguous"
    LIKELY_UNINTELLIGIBLE = "likely_unintelligible"
    INVALID_SAMPLE = "invalid_sample"


class ErrorType(StrEnum):
    WRONG_TONE = "wrong_tone"
    WRONG_INITIAL = "wrong_initial"
    WRONG_FINAL = "wrong_final"
    SUBSTITUTED_SYLLABLE = "substituted_syllable"
    SUBSTITUTED_WORD = "substituted_word"
    OMITTED_SYLLABLE = "omitted_syllable"
    EXTRA_SYLLABLE = "extra_syllable"
    AMERICANIZED = "americanized"
    DISTORTED_PROSODY = "distorted_prosody"
    NONE = "none"


class EnvironmentalCondition(StrEnum):
    QUIET = "quiet"
    ROOM_NOISE = "room_noise"
    BACKGROUND_CONVERSATION = "background_conversation"
    LOW_VOLUME = "low_volume"
    CLIPPED = "clipped"
    SILENCE = "silence"


class RequestMode(StrEnum):
    UNKNOWN_TARGET = "unknown_target"
    KNOWN_TARGET = "known_target"
    CONTEXT_PROBE = "context_probe"
    ACOUSTIC = "acoustic"
    ALIGNMENT = "alignment"


class RunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContextCondition(StrEnum):
    NO_CONTEXT = "A_no_context"
    CONGRUENT = "B_congruent"
    MISLEADING = "C_misleading"


class AudioAsset(StrictModel):
    asset_path: Path
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    original_asset_path: Path | None = None
    media_type: str = "audio/wav"
    sample_rate_hz: int | None = Field(default=None, gt=0)
    channels: int | None = Field(default=None, gt=0)
    sample_width_bits: int | None = Field(default=None, gt=0)
    duration_seconds: NonNegative | None = None


class RecordingQualityEvidence(StrictModel):
    clipping: bool | None = None
    silence_ratio: Probability | None = None
    voiced_fraction: Probability | None = None
    level_rms: NonNegative | None = None
    duration_seconds: NonNegative | None = None
    status: Literal["usable", "warning", "invalid", "unknown"] = "unknown"
    source: str = "production_recording_quality"


class DeviceMetadata(StrictModel):
    device_name: str | None = None
    microphone: str | None = None
    operating_system: str | None = None
    capture_software: str | None = None


class DeliberateError(StrictModel):
    error_type: ErrorType
    corrupted_syllable_index: int | None = Field(default=None, ge=0)
    expected_form: str | None = None
    produced_form: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_location_for_unit_error(self) -> DeliberateError:
        unit_errors = {
            ErrorType.WRONG_TONE,
            ErrorType.WRONG_INITIAL,
            ErrorType.WRONG_FINAL,
            ErrorType.SUBSTITUTED_SYLLABLE,
            ErrorType.OMITTED_SYLLABLE,
        }
        if self.error_type in unit_errors and self.corrupted_syllable_index is None:
            raise ValueError("unit-level deliberate errors require corrupted_syllable_index")
        return self


class BenchmarkSample(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    sample_id: str = Field(min_length=3, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    corpus_version: str = Field(min_length=1)
    audio: AudioAsset | None = None
    speaker_id: str | None = None
    speaker_category: SpeakerCategory
    device: DeviceMetadata | None = None
    intended_text: str | None = None
    intended_pinyin: tuple[str, ...] = ()
    lexical_tones: tuple[int, ...] = ()
    expected_surface_tones: tuple[str, ...] = ()
    deliberate_error: DeliberateError | None = None
    recording_notes: str | None = None
    calibration_mode: CalibrationMode | None = None
    pair_id: str | None = None
    recording_quality: RecordingQualityEvidence | None = None
    environmental_condition: EnvironmentalCondition = EnvironmentalCondition.QUIET
    tags: frozenset[str] = Field(default_factory=frozenset)
    status: Literal["planned", "recorded", "annotated"] = "planned"

    @model_validator(mode="after")
    def tone_lengths_are_coherent(self) -> BenchmarkSample:
        if (
            self.intended_pinyin
            and self.lexical_tones
            and len(self.intended_pinyin) != len(self.lexical_tones)
        ):
            raise ValueError("intended_pinyin and lexical_tones must have equal lengths")
        if (
            self.expected_surface_tones
            and self.intended_pinyin
            and len(self.expected_surface_tones) != len(self.intended_pinyin)
        ):
            raise ValueError("surface tones and intended_pinyin must have equal lengths")
        if self.status != "planned" and self.audio is None:
            raise ValueError("recorded/annotated samples require an audio asset")
        return self

    def perception_request(self) -> UnknownTargetPerceptionRequest:
        """Create the only request accepted by raw-listener provider adapters."""
        if self.audio is None:
            raise ValueError(f"sample {self.sample_id} has no audio")
        return UnknownTargetPerceptionRequest(
            sample_id=self.sample_id,
            audio=self.audio,
            language_hint="zh",
        )


class CorpusManifest(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    corpus_id: str
    corpus_version: str
    desired_sample_count: int = Field(ge=1)
    description: str
    samples: tuple[BenchmarkSample, ...]

    @model_validator(mode="after")
    def unique_sample_ids(self) -> CorpusManifest:
        ids = [sample.sample_id for sample in self.samples]
        if len(ids) != len(set(ids)):
            raise ValueError("sample_id values must be unique")
        return self


class UnknownTargetPerceptionRequest(StrictModel):
    """Audio-only production request; target/context fields are structurally impossible."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    sample_id: str
    audio: AudioAsset
    language_hint: Literal["zh", "cmn", "zh-CN"] = "zh"
    timeout_seconds: float = Field(default=60.0, gt=0, le=600)


class KnownTargetAssessmentRequest(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    sample_id: str
    audio: AudioAsset
    target_text: str = Field(min_length=1)
    target_pinyin: tuple[str, ...] = ()
    lexical_tones: tuple[int, ...] = ()
    expected_surface_tones: tuple[str, ...] = ()
    locale: str = "zh-CN"
    timeout_seconds: float = Field(default=60.0, gt=0, le=600)


class ContextInfluenceProbeRequest(StrictModel):
    """Research-only prompt probe; intentionally not accepted by production providers."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    base_request: UnknownTargetPerceptionRequest
    condition: ContextCondition
    experimental_prompt: str | None = None

    @model_validator(mode="after")
    def prompt_matches_condition(self) -> ContextInfluenceProbeRequest:
        if self.condition == ContextCondition.NO_CONTEXT and self.experimental_prompt is not None:
            raise ValueError("no-context probe cannot contain a prompt")
        if self.condition != ContextCondition.NO_CONTEXT and not self.experimental_prompt:
            raise ValueError("contextual probe requires an experimental prompt")
        return self


class TimeSpan(StrictModel):
    start_seconds: NonNegative
    end_seconds: NonNegative

    @model_validator(mode="after")
    def end_after_start(self) -> TimeSpan:
        if self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must not precede start_seconds")
        return self


class TranscriptAlternative(StrictModel):
    transcript: str
    confidence: Probability | None = None


class TimedToken(StrictModel):
    text: str
    span: TimeSpan
    confidence: Probability | None = None


class UnknownTargetPerceptionResult(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    transcript: str
    alternatives: tuple[TranscriptAlternative, ...] = ()
    confidence: Probability | None = None
    tokens: tuple[TimedToken, ...] = ()
    segments: tuple[TimedToken, ...] = ()
    uncertainty: JsonValue | None = None
    detected_language: str | None = None


class PhoneAssessment(StrictModel):
    phone: str
    score: Score | None = None
    span: TimeSpan | None = None
    error_classification: str | None = None


class SyllableAssessment(StrictModel):
    text: str | None = None
    pinyin: str | None = None
    score: Score | None = None
    phones: tuple[PhoneAssessment, ...] = ()
    reference_tone: str | None = None
    detected_tone: str | None = None
    tone_score: Score | None = None
    span: TimeSpan | None = None
    confidence: Probability | None = None
    error_classifications: tuple[str, ...] = ()


class KnownTargetAssessmentResult(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    overall_score: Score | None = None
    pronunciation_score: Score | None = None
    fluency_score: Score | None = None
    completeness_score: Score | None = None
    syllables: tuple[SyllableAssessment, ...] = ()
    provider_error_classifications: tuple[str, ...] = ()
    confidence: Probability | None = None
    unsupported_capabilities: tuple[str, ...] = ()


class PitchPoint(StrictModel):
    timestamp_seconds: NonNegative
    f0_hz: NonNegative | None = None
    voicing_probability: Probability | None = None
    energy_rms: NonNegative | None = None
    normalized_semitones: float | None = None
    z_log_f0: float | None = None


class VoicedSegment(StrictModel):
    span: TimeSpan
    median_f0_hz: NonNegative | None = None


class AcousticAnalysisResult(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    pitch_algorithm: str
    algorithm_version: str
    sample_rate_hz: int = Field(gt=0)
    normalization_method: str | None = None
    f0: tuple[PitchPoint, ...]
    voiced_segments: tuple[VoicedSegment, ...] = ()
    contour_features: dict[str, float | None] = Field(default_factory=dict)


class AlignmentUnit(StrictModel):
    label: str
    span: TimeSpan
    confidence: Probability | None = None


class AlignmentResult(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    algorithm: str
    algorithm_version: str
    words: tuple[AlignmentUnit, ...] = ()
    phones: tuple[AlignmentUnit, ...] = ()
    confidence_proxy: Probability | None = None
    warnings: tuple[str, ...] = ()


class ProviderError(StrictModel):
    error_type: str
    message: str
    retryable: bool = False
    provider_code: str | None = None


class ProviderRun(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    run_id: str
    provider: str
    product: str
    provider_version: str | None = None
    adapter_version: str
    git_commit_sha: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    benchmark_sample_id: str
    request_mode: RequestMode
    request_configuration: dict[str, JsonValue] = Field(default_factory=dict)
    audio_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    sample_rate_hz: int | None = Field(default=None, gt=0)
    transport_timings_seconds: dict[str, NonNegative] = Field(default_factory=dict)
    response_latency_seconds: NonNegative | None = None
    audio_duration_seconds: NonNegative | None = None
    estimated_billable_units: NonNegative | None = None
    estimated_cost_usd: NonNegative | None = None
    normalized_result: (
        UnknownTargetPerceptionResult
        | KnownTargetAssessmentResult
        | AcousticAnalysisResult
        | AlignmentResult
        | None
    ) = None
    raw_response: JsonValue | None = None
    raw_response_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    evidence_origin: EvidenceOrigin = EvidenceOrigin.UNKNOWN
    status: RunStatus
    error: ProviderError | None = None
    context_condition: ContextCondition | None = None

    @model_validator(mode="after")
    def status_is_coherent(self) -> ProviderRun:
        if self.status == RunStatus.SUCCEEDED and self.normalized_result is None:
            raise ValueError("successful run requires normalized_result")
        if self.status == RunStatus.FAILED and self.error is None:
            raise ValueError("failed run requires error")
        return self


class BlindListenerResponse(StrictModel):
    perceived_text: str
    perceived_pinyin: tuple[str, ...] = ()
    understood_first_pass: bool
    would_request_repetition: bool
    confidence: Probability
    notes: str | None = None


class RaterProfile(StrictModel):
    rater_id: str = Field(min_length=3, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]+$")
    native_mandarin_self_report: bool
    role: ListenerRole = ListenerRole.ORDINARY_NATIVE_LISTENER
    region_or_accent_note: str | None = None


class BlindAnnotationCommit(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    annotation_id: str
    sample_id: str
    listener_id: str
    rater_profile: RaterProfile | None = None
    randomized_order: int = Field(ge=0)
    response: BlindListenerResponse
    committed_at: datetime
    commit_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class RevealedTargetResponse(StrictModel):
    tone_problem: bool
    affected_syllable_indices: tuple[int, ...] = ()
    initial_problem: bool
    final_problem: bool
    rhythm_or_prosody_issue: bool
    still_understandable: bool
    severity: Literal["none", "minor", "moderate", "severe"]
    semantic_severity: SemanticSeverity | None = None
    perceived_produced_tones: tuple[str, ...] = ()
    invalid_sample: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def affected_indices_are_unique_nonnegative(self) -> RevealedTargetResponse:
        if any(index < 0 for index in self.affected_syllable_indices):
            raise ValueError("affected syllable indices must be nonnegative")
        if len(set(self.affected_syllable_indices)) != len(
            self.affected_syllable_indices
        ):
            raise ValueError("affected syllable indices must be unique")
        return self


class RevealedAnnotationCommit(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    annotation_id: str
    sample_id: str
    listener_id: str
    blind_commit_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    response: RevealedTargetResponse
    committed_at: datetime


class HumanListenerAnnotation(StrictModel):
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION
    blind: BlindAnnotationCommit
    revealed: RevealedAnnotationCommit | None = None

    @model_validator(mode="after")
    def revealed_references_blind_commit(self) -> HumanListenerAnnotation:
        if self.revealed is not None:
            if self.revealed.blind_commit_sha256 != self.blind.commit_sha256:
                raise ValueError("revealed stage does not reference the committed blind response")
            if self.revealed.sample_id != self.blind.sample_id:
                raise ValueError("annotation stages reference different samples")
            if self.revealed.listener_id != self.blind.listener_id:
                raise ValueError("annotation stages reference different listeners")
        return self


class CalibrationSplitManifest(StrictModel):
    benchmark_version: str
    split_version: str
    strategy: str = "deterministic_stratified_sha256_v1"
    calibration_sample_ids: tuple[str, ...]
    held_out_sample_ids: tuple[str, ...]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def split_is_disjoint(self) -> CalibrationSplitManifest:
        calibration = set(self.calibration_sample_ids)
        held_out = set(self.held_out_sample_ids)
        if calibration & held_out:
            raise ValueError("calibration and held-out partitions overlap")
        if len(calibration) != len(self.calibration_sample_ids) or len(held_out) != len(
            self.held_out_sample_ids
        ):
            raise ValueError("split partitions contain duplicate sample IDs")
        return self


class CalibrationRunManifest(StrictModel):
    benchmark_version: str
    git_commit_sha: str
    provider_adapter_versions: dict[str, str]
    provider_configurations: dict[str, dict[str, JsonValue]]
    included_sample_ids: tuple[str, ...]
    excluded_sample_ids: tuple[str, ...]
    human_annotation_version: str
    split_version: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
