"""Public API schemas with strict write contracts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from benma_api.pronunciation.pitch_types import (
    PitchInterpretationEligibility,
    PitchRegionProjection,
    UtterancePitchTrack,
)


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DevAuthRequest(StrictRequest):
    phone_number: str = Field(min_length=7, max_length=32)


class AuthTokenResponse(BaseModel):
    token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    account_id: uuid.UUID


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime


class ConversationCreate(StrictRequest):
    pass


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    account_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserConversationTurnCreate(StrictRequest):
    utterance_id: uuid.UUID
    perception_run_id: uuid.UUID


class ConversationTurnResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    account_id: uuid.UUID
    sequence_number: int
    role: Literal["user", "assistant"]
    assistant_text: str | None
    resolved_text: str | None
    perceived_text: str | None
    interpretation_decision: Literal["preserve", "infer", "clarify"] | None
    utterance_id: uuid.UUID | None
    perception_run_id: uuid.UUID | None
    contextual_interpretation_run_id: uuid.UUID | None
    assistant_generation_run_id: uuid.UUID | None
    assistant_speech: AssistantSpeechRunResponse | None
    created_at: datetime


class AssistantGenerationRunResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    conversation_id: uuid.UUID
    triggering_user_turn_id: uuid.UUID
    provider: str
    product: str
    provider_version: str | None
    adapter_version: str
    model: str
    generator_version: str
    generator_configuration: dict[str, Any]
    generation_type: Literal["reply", "clarification"]
    input_snapshot: dict[str, Any]
    generated_text: str | None
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime
    status: str
    error_code: str | None
    error_message: str | None


class PracticeSessionCreate(StrictRequest):
    mode: Literal["perception_test", "pronunciation"]
    metadata: dict[str, Any] = Field(default_factory=dict)


class PracticeSessionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    mode: str
    started_at: datetime
    ended_at: datetime | None
    metadata: dict[str, Any]


class AudioAssetResponse(BaseModel):
    id: uuid.UUID
    kind: str
    mime_type: str
    sha256: str
    size_bytes: int
    sample_rate_hz: int | None
    channels: int | None
    sample_width_bits: int | None
    duration_seconds: float | None


class AssistantSpeechCreate(StrictRequest):
    pass


class AssistantSpeechRunResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    conversation_id: uuid.UUID
    assistant_generation_run_id: uuid.UUID
    assistant_turn_id: uuid.UUID
    provider: str
    product: str
    provider_version: str | None
    adapter_version: str
    model: str
    voice: str
    locale: str
    generation_configuration: dict[str, Any]
    text_snapshot: str
    audio_asset: AudioAssetResponse | None
    audio_url: str | None
    latency_ms: int | None
    status: Literal["succeeded", "failed"]
    error_code: str | None
    error_message: str | None
    created_at: datetime


class FreeTalkTurnResponse(ConversationTurnResponse):
    """Backward-compatible user turn plus the server-created assistant result."""

    assistant_turn: ConversationTurnResponse


class UtteranceResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    practice_session_id: uuid.UUID | None
    created_at: datetime
    original_audio: AudioAssetResponse
    canonical_audio: AudioAssetResponse
    audio_url: str


class UnknownPerceptionRequest(StrictRequest):
    language_hint: Literal["zh"] = "zh"
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)


class PerceptionRunResponse(BaseModel):
    id: uuid.UUID
    utterance_id: uuid.UUID
    provider: str
    product: str
    provider_version: str | None
    adapter_version: str
    transcript: str | None
    alternatives: list[dict[str, Any]] | None
    provider_uncertainty: Any | None
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime
    status: str
    error_code: str | None
    error_message: str | None


class ContextualInterpretationUncertainty(StrictRequest):
    level: Literal["unknown", "low", "medium", "high"] = "unknown"
    rationale: str | None = Field(default=None, max_length=1000)
    alternatives: list[str] = Field(default_factory=list, max_length=10)


class ContextualInterpretationCreate(StrictRequest):
    context_snapshot: dict[str, Any] = Field(default_factory=dict)


class ContextualInterpretationRunResponse(BaseModel):
    id: uuid.UUID
    perception_run_id: uuid.UUID
    interpreter: str
    interpreter_version: str
    interpreter_configuration: dict[str, Any]
    context_snapshot: dict[str, Any]
    decision: Literal["preserve", "infer", "clarify"]
    inferred_text: str | None
    uncertainty: ContextualInterpretationUncertainty
    clarification_needed: bool
    created_at: datetime


class ConversationStreamEvent(BaseModel):
    """One NDJSON event. Meaning progress is provisional until complete commits."""

    type: Literal["interpretation", "complete", "error"]
    interpretation: ContextualInterpretationRunResponse | None = None
    result: FreeTalkTurnResponse | None = None
    interpretation_ms: int | None = None
    generation_ms: int | None = None
    error_code: str | None = None


class UserCorrectionCreate(StrictRequest):
    intended_text: str = Field(min_length=1, max_length=500)
    perception_run_id: uuid.UUID | None = None


class UserCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    utterance_id: uuid.UUID
    perception_run_id: uuid.UUID | None
    intended_text: str
    created_at: datetime


class PronunciationTargetCreate(StrictRequest):
    text: str = Field(min_length=1, max_length=200)
    target_source: Literal["generated", "manual", "imported"] = "manual"


class PronunciationTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    text: str
    display_pinyin: str
    pinyin_syllables: list[str]
    lexical_tones: list[int | None]
    target_source: str
    pinyin_source: str
    pinyin_alternatives: list[list[str]]
    syllable_units: list[dict[str, Any]]
    surface_tone_expectation: dict[str, Any]
    parent_target_id: uuid.UUID | None
    created_at: datetime


class PinyinCorrectionCreate(StrictRequest):
    pinyin: str = Field(min_length=2, max_length=500)


class PronunciationAttemptCreate(StrictRequest):
    utterance_id: uuid.UUID
    target_id: uuid.UUID


class PronunciationAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    utterance_id: uuid.UUID
    target_id: uuid.UUID
    created_at: datetime


class AssessmentRequest(StrictRequest):
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)


class AssessmentRunResponse(BaseModel):
    id: uuid.UUID
    pronunciation_attempt_id: uuid.UUID
    provider: str
    product: str
    provider_version: str | None
    adapter_version: str
    target_snapshot: dict[str, Any]
    git_commit_sha: str
    audio_sha256: str | None
    sample_rate_hz: int | None
    request_configuration: dict[str, Any]
    transport_timings_ms: dict[str, int]
    estimated_billable_units: float | None
    estimated_cost_usd: float | None
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime
    status: str
    error_code: str | None
    error_message: str | None


class ReferenceSpeechRequestBody(StrictRequest):
    force: bool = False
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)


class ReferenceSpeechResponse(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    provider: str
    voice: str
    locale: str
    model_version: str
    generation_config: dict[str, Any]
    target_snapshot: dict[str, Any]
    status: str
    error_code: str | None
    error_message: str | None
    audio_url: str | None
    acoustic_result: dict[str, Any] | None
    created_at: datetime


class AcousticRunResponse(BaseModel):
    utterance_pitch_track: UtterancePitchTrack | None = None
    id: uuid.UUID
    utterance_id: uuid.UUID
    algorithm: str
    algorithm_version: str
    parameters: dict[str, Any]
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    status: str
    error_code: str | None
    error_message: str | None
    created_at: datetime


class AlignmentRunResponse(BaseModel):
    id: uuid.UUID
    pronunciation_attempt_id: uuid.UUID
    algorithm: str
    algorithm_version: str
    normalized_result: dict[str, Any] | None
    quality: str
    latency_ms: int | None
    status: str
    error_code: str | None
    error_message: str | None
    created_at: datetime


class InterpretationRunResponse(BaseModel):
    id: uuid.UUID
    pronunciation_attempt_id: uuid.UUID
    interpreter_version: str
    interpreter_configuration: dict[str, Any]
    input_evidence_run_ids: dict[str, str | None]
    structured_observations: list[dict[str, Any]]
    capability_state: str
    created_at: datetime


class PronunciationAnalyzeRequest(StrictRequest):
    reuse_existing: bool = True
    rerun_provider: bool = False
    rerun_acoustics: bool = False
    rerun_alignment: bool = False


class DisplayPitchPoint(BaseModel):
    timestamp_seconds: float
    normalized_semitones: float


class DisplayContour(BaseModel):
    segments: list[list[DisplayPitchPoint]] = Field(default_factory=list)
    baseline_hz: float | None = None
    minimum_semitones: float = -3
    maximum_semitones: float = 3
    rejected_points: int = 0
    method: str = "local-hampel-median-no-interpolation-v1"


class ObservedContour(BaseModel):
    classification: Literal["1-like", "2-like", "3-like", "4-like", "neutral-like", "unclear"] = (
        "unclear"
    )
    confidence: Literal["moderate", "low"] = "low"
    reason: str = "timing_unavailable"
    voiced_coverage: float = 0
    features: dict[str, float] = Field(default_factory=dict)


class PronunciationSyllableResult(BaseModel):
    # Separate release permission: local pitch eligibility cannot establish speech presence.
    tone_comparison_policy: Literal["experimental"] = "experimental"
    pitch_projection: PitchRegionProjection | None = None
    pitch_eligibility: PitchInterpretationEligibility = Field(
        default_factory=PitchInterpretationEligibility
    )
    display_contour: DisplayContour | None = None
    observed_contour: ObservedContour = Field(default_factory=ObservedContour)
    syllable_index: int
    characters: str
    pinyin: str
    lexical_tone: int | None
    expected_surface_tone: int | None
    surface_tone_reason: list[dict[str, Any]]
    provider_evidence: dict[str, Any] | None
    acoustic_evidence: dict[str, Any] | None
    timing: dict[str, Any] | None
    interpretation: dict[str, Any] | None
    capability_state: str


class PronunciationResultResponse(BaseModel):
    display_contour: DisplayContour | None = None
    attempt: PronunciationAttemptResponse
    target: PronunciationTargetResponse
    recording_audio_url: str
    reference_audio: ReferenceSpeechResponse | None
    overall_evidence: dict[str, Any]
    syllables: list[PronunciationSyllableResult]
    assessment: AssessmentRunResponse | None
    acoustic: AcousticRunResponse | None
    alignment: AlignmentRunResponse | None
    interpretation: InterpretationRunResponse | None
    capability_policy: dict[str, Any]


class AttemptComparisonRequest(StrictRequest):
    first_attempt_id: uuid.UUID
    second_attempt_id: uuid.UUID


class AttemptComparisonResponse(BaseModel):
    first: PronunciationResultResponse
    second: PronunciationResultResponse
    disclaimer: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PerceivedAnalysisCreate(StrictRequest):
    """Only the path's persisted perception ID supplies analysis input."""


class MeasuredPitchPoint(BaseModel):
    timestamp_seconds: float = Field(ge=0, allow_inf_nan=False)
    f0_hz: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    normalized_semitones: float | None = Field(default=None, allow_inf_nan=False)
    voicing_probability: float | None = Field(default=None, ge=0, le=1)


class TrackerPitchFrame(BaseModel):
    """Allowlisted tracker measurements; retained means selected by the existing filter."""

    timestamp_seconds: float = Field(ge=0, allow_inf_nan=False)
    tracker_f0_hz: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    f0_hz: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    selected_f0_hz: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    retained: bool
    exclusion_reasons: tuple[str, ...] = ()
    source_frame_index: int | None = None


class SentencePitchEvidence(BaseModel):
    track_evidence_id: str | None = None
    mine: DisplayContour
    filtered: DisplayContour
    raw: list[TrackerPitchFrame]


class ExpectedTonePoint(BaseModel):
    position: float = Field(ge=0, le=1)
    height: float = Field(ge=0, le=1)


ObservedGesture = Literal["level", "rising", "dipping", "falling", "unclear"]
OBSERVED_GESTURES: dict[str, ObservedGesture] = {
    "1-like": "level",
    "2-like": "rising",
    "3-like": "dipping",
    "4-like": "falling",
}


class PerceivedTimingGroup(BaseModel):
    """An exact perceived word span; no internal character timing is implied."""

    pitch_projection: PitchRegionProjection | None = None
    pitch_eligibility: PitchInterpretationEligibility = Field(
        default_factory=PitchInterpretationEligibility
    )

    character_start: int = Field(ge=0)
    character_end: int = Field(gt=0)
    text: str = Field(min_length=2)
    start_seconds: float = Field(ge=0, allow_inf_nan=False)
    end_seconds: float = Field(gt=0, allow_inf_nan=False)
    source: Literal["azure_word"] = "azure_word"
    timing_evidence_id: str

    @model_validator(mode="after")
    def ordered_span(self) -> PerceivedTimingGroup:
        if self.character_end - self.character_start != len(self.text):
            raise ValueError("group text must exactly cover its character span")
        if self.end_seconds <= self.start_seconds:
            raise ValueError("group timing must be ordered")
        return self


class PerceivedSyllable(BaseModel):
    # Separate release permission: local pitch eligibility cannot establish speech presence.
    tone_comparison_policy: Literal["experimental"] = "experimental"
    pitch_projection: PitchRegionProjection | None = None
    pitch_eligibility: PitchInterpretationEligibility = Field(
        default_factory=PitchInterpretationEligibility
    )
    index: int
    character_start: int
    character_end: int
    characters: str
    pinyin: str | None
    lexical_tone: Literal[0, 1, 2, 3, 4] | None
    expected_surface_tone: Literal[0, 1, 2, 3, 4] | None = None
    expected_surface_shape: list[ExpectedTonePoint] = Field(default_factory=list)
    surface_rule: str | None = None
    surface_rule_version: str | None = None
    timing_source: str | None = None
    timing_evidence_id: str | None = None
    reading_source: Literal["perception_token", "phrase", "grammar", "dictionary", "unresolved"]
    resolution_confidence: Literal["high", "unresolved"] = "unresolved"
    display_contour: DisplayContour | None = None
    observed_contour: ObservedContour = Field(default_factory=ObservedContour)
    alternatives: list[str]
    start_seconds: float | None = None
    end_seconds: float | None = None
    expected_tone: list[ExpectedTonePoint]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def observed_gesture(self) -> ObservedGesture:
        """Semantic alias only; no lexical tone identification or new classifier."""
        return OBSERVED_GESTURES.get(self.observed_contour.classification, "unclear")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def observed_confidence(self) -> Literal["moderate", "low"]:
        return self.observed_contour.confidence


class PerceivedAnalysisData(BaseModel):
    pitch_track_evidence_id: str | None = None
    tone_graph: SentencePitchEvidence | None = None
    timing_groups: list[PerceivedTimingGroup] = Field(default_factory=list)
    display_contour: DisplayContour | None = None
    timings_ms: dict[str, float] = Field(default_factory=dict)
    syllables: list[PerceivedSyllable]
    measured_pitch: list[MeasuredPitchPoint]
    duration_seconds: float
    voiced_fraction: float | None
    pitch_status: Literal["available", "unavailable"]
    alignment_status: Literal["aligned", "partial", "unavailable", "synthetic"]
    timing_source: str | None = None
    timing_evidence_id: str | None = None
    timing_coverage: float = 0
    unresolved_spans: list[dict[str, Any]] = Field(default_factory=list)
    alignment_error_code: str | None
    quality_issues: list[str]
    observations: list[str]
    pitch_latency_ms: int | None
    alignment_latency_ms: int
    # Canonical lexical shapes are schematic, not reference F0 or surface-tone grades.
    expected_tone_basis: Literal["schematic_lexical_tones", "conservative_surface_tones"] = (
        "schematic_lexical_tones"
    )
    evidence_status: Literal["synthetic_replay", "recorded_audio"]


class PerceivedReadingResponse(BaseModel):
    perception_run_id: uuid.UUID
    alignment_reference_text: str
    reading_version: str
    surface_version: str
    syllables: list[PerceivedSyllable]
    unresolved_spans: list[dict[str, Any]]


class PerceivedSpeechAnalysisResponse(BaseModel):
    id: uuid.UUID
    perception_run_id: uuid.UUID
    utterance_id: uuid.UUID
    alignment_reference_text: str
    reference_kind: Literal["perceived_text"] = "perceived_text"
    analyzer_version: str
    status: Literal["succeeded", "partial", "failed"]
    error_code: str | None
    latency_ms: int
    created_at: datetime
    data: PerceivedAnalysisData
