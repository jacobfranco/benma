"""Experimental acoustic output; expectations never enter the inference contract."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ToneFamily = Literal["T1", "T2", "T3", "T4"]


class LearnedRealization(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    status: Literal["ok", "abstained"] = "abstained"
    reason: str | None = None
    probabilities: dict[ToneFamily, float] | None = None
    prediction: ToneFamily | None = None
    confidence: float | None = None
    confidence_is_calibrated_correctness: Literal[False] = False
    version: str = "dev-fast-learned-tone-v1"
    model_sha256: str = "b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b"
    encoder_revision: str = "fce0375452b1dd6c080ac3248d423d4d037bc831"
    encoder_weights_sha256: str = "2fefccd26c2794a583b80f6f7210c721873cb7ebae2c1cde3baf9b27855e24d8"
    layer: Literal[9] = 9
    pooling: str = "nucleus_coda_frame_center_mean"
    azure_span: list[float] | None = None
    pooling_span: list[float] | None = None
    context_span: list[float] | None = None
    continuity: dict[str, Any] = Field(default_factory=dict)
    retained_frames: int = 0
    owned_encoder_frames: int | None = None


class LearnedComparison(BaseModel):
    # Family comparison only. Keep legacy state/correction keys compatible;
    # the workspace assigns final learner severity using existing F0 safeguards.
    state: Literal[
        "experimental_match", "experimental_mismatch", "unresolved", "neutral", "insufficient"
    ]
    correction: Literal[False] = False
    message: str
    explanation: str | None = None


class LearnedUnit(BaseModel):
    index: int
    characters: str
    target_pinyin: str | None
    lexical_tone: int | None
    expected_surface_tone: int | None
    acceptable_surface_tones: list[int] | None = None
    expected_neutral: bool | None = None
    expectation_resolution: Literal["exact", "alternatives", "neutral", "unresolved"] | None = None
    surface_rule: str | None
    contextual_rule: str | None = None
    heard_pinyin: str | None
    realization: LearnedRealization
    comparison: LearnedComparison


class LearnedAnalysis(BaseModel):
    version: str = "dev-fast-learned-tone-v1"
    expectation_basis: Literal["intended_target", "perceived_text"]
    target_text: str
    target_mapping_resolved: bool = True
    units: list[LearnedUnit]
    timings_ms: dict[str, float]
    runtime: dict[str, Any]
