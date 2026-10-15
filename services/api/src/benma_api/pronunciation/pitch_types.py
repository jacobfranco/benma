"""Immutable acoustic contracts. No text, reading, target, or tone enters a track."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TRACK_VERSION = "utterance-pitch-v1"
ELIGIBILITY_VERSION = "voiced-support-completeness-v2-candidate-branch"


class FrozenEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class PitchCandidate(FrozenEvidence):
    frequency_hz: float = Field(gt=0)
    strength: float


class UtterancePitchFrame(FrozenEvidence):
    timestamp_seconds: float = Field(ge=0)
    raw_f0_hz: float | None = Field(default=None, gt=0)
    energy_gated_f0_hz: float | None = Field(default=None, gt=0)
    analyzer_selected_f0_hz: float | None = Field(default=None, gt=0)
    selected_f0_hz: float | None = Field(default=None, gt=0)
    periodicity: float | None = None
    energy_rms: float | None = None
    comparison_f0_hz: float | None = None
    filter_disagreement_st: float | None = None
    candidates: tuple[PitchCandidate, ...] = ()
    exclusion_reasons: tuple[str, ...] = ()
    # Existing within-run smoothing, display only; selected Hz remain unsmoothed.
    display_semitones: float | None = None


class UtterancePitchTrack(FrozenEvidence):
    schema_version: str = TRACK_VERSION
    evidence_id: str
    audio_sha256: str
    tracker_source: str
    tracker_version: str
    # Canonical JSON is immutable and preserves heterogeneous tracker parameters.
    tracker_configuration_json: str
    selection_version: str
    raw_provenance: Literal["native_tracker", "legacy_energy_gated"]
    frame_cadence_seconds: float | None = Field(default=None, gt=0)
    duration_seconds: float = Field(ge=0)
    baseline_hz: float | None = None
    frames: tuple[UtterancePitchFrame, ...]

    @model_validator(mode="after")
    def ordered_frames(self) -> UtterancePitchTrack:
        if any(
            a.timestamp_seconds >= b.timestamp_seconds
            for a, b in zip(self.frames, self.frames[1:], strict=False)
        ):
            raise ValueError("pitch timestamps must be strictly increasing")
        if self.frames and self.frames[-1].timestamp_seconds > self.duration_seconds:
            raise ValueError("pitch timestamps must belong to the waveform")
        return self


class PitchRegionProjection(FrozenEvidence):
    track_evidence_id: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    timing_source: str | None = None
    timing_evidence_id: str | None = None
    # Source indices are the ownership contract; no new/interpolated timestamps.
    frame_indices: tuple[int, ...] = ()


class PitchSupportMetrics(FrozenEvidence):
    raw_voiced_frames: int = 0
    selected_frames: int = 0
    raw_start_seconds: float | None = None
    raw_end_seconds: float | None = None
    selected_start_seconds: float | None = None
    selected_end_seconds: float | None = None
    retained_fraction: float = 0
    early_retained_fraction: float = 0
    middle_retained_fraction: float = 0
    late_retained_fraction: float = 0
    largest_island_seconds: float = 0
    selected_islands: int = 0
    largest_raw_gap_seconds: float = 0
    largest_selected_gap_seconds: float = 0
    missing_head_seconds: float = 0
    missing_tail_seconds: float = 0
    maximum_raw_jump_semitones: float = 0
    discontinuities: int = 0


class PitchInterpretationEligibility(FrozenEvidence):
    version: str = ELIGIBILITY_VERSION
    state: Literal["sufficient", "incomplete", "unstable", "insufficient"] = "insufficient"
    reasons: tuple[str, ...] = ("timing_unavailable",)
    metrics: PitchSupportMetrics = Field(default_factory=PitchSupportMetrics)
