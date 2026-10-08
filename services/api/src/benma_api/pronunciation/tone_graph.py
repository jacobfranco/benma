"""Typed presentation evidence, using existing selection without changing raw F0.

raw tracker / energy-gated measurements -> existing display filter's retained
samples -> sentence-relative semitones. Mine keeps the existing within-segment
median smoothing and simplification. Detail retains unsmoothed selected samples.
No expected tone, classifier output or intended text is an input.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from benma_api.pronunciation.contours import simplify_display
from benma_api.pronunciation.pitch_types import UtterancePitchTrack
from benma_api.schemas import (
    DisplayContour,
    DisplayPitchPoint,
    PerceivedSyllable,
    PerceivedTimingGroup,
    SentencePitchEvidence,
    TrackerPitchFrame,
)


def sentence_pitch_evidence(
    raw: list[dict[str, Any]],
    display: DisplayContour,
    syllables: list[PerceivedSyllable],
    timing_groups: Sequence[PerceivedTimingGroup] = (),
    *,
    track: UtterancePitchTrack | None = None,
) -> SentencePitchEvidence:
    by_time = {p["timestamp_seconds"]: p for p in raw}
    retained = {p.timestamp_seconds for segment in display.segments for p in segment}
    # Split before simplifying: even a short zero-evidence unit must remain empty.
    # Unit ownership is [start, end), matching syllable_contour. Exact shared
    # boundaries start a new segment; final endpoints and inter-unit samples stay
    # in real-time evidence but are not owned by a syllable. Never move timestamps.
    spans: list[PerceivedSyllable | PerceivedTimingGroup] = [*syllables, *timing_groups]
    boundaries = sorted(
        {t for s in spans for t in (s.start_seconds, s.end_seconds) if t is not None}
    )
    segments: list[list[DisplayPitchPoint]] = []
    for segment in display.segments:
        current: list[DisplayPitchPoint] = []
        for point in segment:
            if current and any(
                current[-1].timestamp_seconds < t <= point.timestamp_seconds for t in boundaries
            ):
                segments.append(current)
                current = []
            current.append(point)
        if current:
            segments.append(current)
    mine = simplify_display(display.model_copy(update={"segments": segments}))
    # The existing baseline is rounded for transport. Use that same baseline in Raw.
    baseline = display.baseline_hz
    filtered = display.model_copy(
        update={
            "method": "selected-measurements-relative-semitones-v1",
            "segments": [
                [
                    DisplayPitchPoint(
                        timestamp_seconds=p.timestamp_seconds,
                        normalized_semitones=12
                        * math.log2(by_time[p.timestamp_seconds]["f0_hz"] / baseline),
                    )
                    for p in segment
                ]
                for segment in segments
            ]
            if baseline
            else [],
        }
    )
    return SentencePitchEvidence(
        track_evidence_id=track.evidence_id if track else None,
        mine=mine,
        filtered=filtered,
        raw=[
            TrackerPitchFrame(
                timestamp_seconds=p["timestamp_seconds"],
                tracker_f0_hz=p.get("tracker_f0_hz"),
                f0_hz=p.get("f0_hz"),
                selected_f0_hz=track.frames[i].selected_f0_hz if track else p.get("selected_f0_hz"),
                source_frame_index=i if track else None,
                exclusion_reasons=track.frames[i].exclusion_reasons if track else (),
                retained=p["timestamp_seconds"] in retained,
            )
            for i, p in enumerate(raw)
        ],
    )
