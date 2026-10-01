"""Versioned connected-speech research contract; opaque provider payloads stay raw."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Span(EvidenceModel):
    start_ms: float = Field(ge=0)
    end_ms: float = Field(gt=0)
    duration_ms: float = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self):
        if (
            self.end_ms <= self.start_ms
            or abs(self.duration_ms - (self.end_ms - self.start_ms)) > 0.001
        ):
            raise ValueError("invalid timing interval")
        return self


class Reading(EvidenceModel):
    pinyin: str | None = None
    lexical_tone: Literal[0, 1, 2, 3, 4] | None = None
    status: str
    alternatives: list[str] = Field(default_factory=list)
    # Multiple dictionary alternatives may remain even after contextual resolution.
    ambiguous: bool


class Expectation(EvidenceModel):
    reading: Reading
    surface_tone: Literal[0, 1, 2, 3, 4] | None = None
    rule: str
    version: str


class TextEdit(EvidenceModel):
    operation: Literal["match", "substitution", "insertion", "deletion"]
    perceived_offset: int | None
    intended_offset: int | None
    perceived: str | None
    intended: str | None
    # A deterministic edit path is not necessarily a unique correspondence.
    correspondence: Literal["unique_minimum_edit", "ambiguous_minimum_edit"]
    expectation: Expectation | None = None
    diagnosis: Literal["not_inferred_from_text"] = "not_inferred_from_text"


class Perception(EvidenceModel):
    raw_transcript: str
    normalized_transcript: str
    normalization: Literal["identity"] = "identity"
    transcript_sha256: str
    evidence: dict[str, Any]
    raw_response: Any
    request_configuration: dict[str, Any] | None = None
    evidence_status: str


class Pitch(EvidenceModel):
    available: bool
    frame_count: int
    voiced_frame_count: int
    usable_frame_count: int
    voiced_proportion: float | None = None
    active_voiced_proportion: float | None = None
    missing_proportion: float | None = None
    # Raw production frame fields (including nulls) are retained verbatim.
    frames: list[dict[str, Any]]
    filtered_contour: list[dict[str, Any]]
    source: str


class Phone(EvidenceModel):
    label: str
    timing: Span | None = None
    source: str
    semantics: Literal["reference_label_not_observed_phone"] = "reference_label_not_observed_phone"
    score: float | None = None


class Context(EvidenceModel):
    previous_unit: str | None
    next_unit: str | None
    window: Span | None = None


class Unit(EvidenceModel):
    unit_id: str
    perceived_text: str
    character_start: int
    character_end: int
    granularity: Literal["han_character_candidate_syllable"] = "han_character_candidate_syllable"
    timing: Span | None = None
    timing_source: str | None = None
    timing_confidence: float | None = None
    reading: Reading
    pitch: Pitch | None = None
    phones: list[Phone] = Field(default_factory=list)
    observed_tone_model: None = None  # Deliberately not integrated in v1.
    context: Context
    target_comparison: TextEdit | None = None
    quality_flags: list[str]
    judgment: Literal["INSUFFICIENT EVIDENCE"] = "INSUFFICIENT EVIDENCE"
    abstention_reasons: list[str]


class Word(EvidenceModel):
    perceived_text: str
    character_start: int
    character_end: int
    timing: Span | None = None
    timing_source: str
    syllable_timing_status: Literal["unresolved", "mapped"]
    raw_provider_word: dict[str, Any]


class Alignment(EvidenceModel):
    reference_text: str
    source: str
    evidence_status: str
    raw_response: Any = None
    issues: list[str] = Field(default_factory=list)
    words: list[Word] = Field(default_factory=list)


class Audio(EvidenceModel):
    path: str | None = None
    sha256: str | None = None
    canonical_sha256: str | None = None
    duration_ms: float = Field(gt=0)
    provenance: Literal["recorded_audio", "synthetic_fixture"]


class Record(EvidenceModel):
    schema_version: Literal["connected-speech-v1"] = "connected-speech-v1"
    analysis_version: Literal["connected-probe-v1"] = "connected-probe-v1"
    recording_id: str
    audio: Audio
    mode: Literal["free", "practice"]
    provider: str
    language: Literal["zh-CN"] = "zh-CN"
    perception: Perception
    intended_text: str | None = None
    alignment: Alignment
    acoustics: dict[str, Any] | None = None
    units: list[Unit]
    text_comparison: list[TextEdit] | None = None
    target_relative_assessment: None = None
    configuration: dict[str, Any]
    limitations: list[str]

    @model_validator(mode="after")
    def truth_boundary(self):
        import hashlib

        text = self.perception.raw_transcript
        if self.perception.normalized_transcript != text or self.alignment.reference_text != text:
            raise ValueError("perception and alignment references must remain exact")
        if self.perception.transcript_sha256 != hashlib.sha256(text.encode()).hexdigest():
            raise ValueError("perception digest mismatch")
        previous_end = 0.0
        for unit in self.units:
            if text[unit.character_start : unit.character_end] != unit.perceived_text:
                raise ValueError("unit must refer to exact perceived text")
            if unit.timing:
                if (
                    unit.timing.start_ms < previous_end
                    or unit.timing.end_ms > self.audio.duration_ms
                ):
                    raise ValueError("unordered or out-of-audio timing")
                previous_end = unit.timing.end_ms
        return self
