"""Conservative boundary support, not phoneme recognition or tone-template fitting.

Only weak attacks and independently rejected, fading terminal tracker branches
can be excluded. Interior dropouts/creak remain in the evidence. No expected
tone, spelling, display smoothing or candidate octave repair enters selection.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToneEvidenceRegion:
    aligned_start: float
    aligned_end: float
    start: float
    end: float
    onset_frames: int = 0
    terminal_frames: int = 0
    method: str = "aligned_span"

    @property
    def selected(self) -> bool:
        return self.method != "aligned_span"


def select_tone_evidence(raw: list[dict[str, Any]], start: float, end: float) -> ToneEvidenceRegion:
    fallback = ToneEvidenceRegion(start, end, start, end)
    if not 0.12 <= end - start <= 1.5:
        return fallback
    window = [p for p in raw if start <= p.get("timestamp_seconds", -1) < end]
    voiced = [p for p in window if p.get("f0_hz")]
    if len(voiced) < 14 or any(
        not isinstance(p.get(key), (int, float)) or not math.isfinite(p[key])
        for p in window
        for key in ("energy_rms", "voicing_probability")
    ):
        return fallback

    def supported(p: dict[str, Any]) -> bool:
        hz, comparison = p.get("f0_hz"), p.get("comparison_f0_hz")
        return bool(
            hz
            and comparison
            and p.get("quality_usable") is True
            and p["voicing_probability"] >= 0.8
            and abs(12 * math.log2(hz / comparison)) <= 1
        )

    # Require sustained independent periodicity support. Never search for a
    # level/rising/falling subsection or discard a supported onset gesture.
    anchor = next(
        (
            i
            for i in range(len(window) - 2)
            if all(supported(p) for p in window[i : i + 3])
            and window[i + 2]["timestamp_seconds"] - window[i]["timestamp_seconds"] <= 0.025
        ),
        None,
    )
    if anchor is None:
        return fallback
    strong = [p for p in window if supported(p)]
    energy = statistics.median(p["energy_rms"] for p in strong)
    first = voiced[0]["timestamp_seconds"]
    last = voiced[-1]["timestamp_seconds"]
    a = window[anchor]["timestamp_seconds"]
    prefix = [p for p in voiced if p["timestamp_seconds"] < a]
    attack = [p for p in window if first <= p["timestamp_seconds"] < a]
    onset = bool(
        prefix
        and a - first <= 0.08 + 1e-9
        and a - first <= (last - first + 0.01) * 0.2
        # Weak-but-continuous voiced initials may carry genuine tone. Exclusion
        # also needs path loss/disagreement, not just a rising amplitude envelope.
        and any(
            not p.get("f0_hz") or not p.get("comparison_f0_hz") or p.get("quality_usable") is False
            for p in attack
        )
        and all(p["voicing_probability"] < 0.8 and p["energy_rms"] <= energy * 0.6 for p in prefix)
        and all(p["energy_rms"] <= energy * 0.6 for p in window if p["timestamp_seconds"] < a)
    )
    if not onset:
        a = start

    usable = [p for p in voiced if p.get("quality_usable") is True]
    if not usable:
        return fallback
    tail_start = round(usable[-1]["timestamp_seconds"] + 0.01, 4)
    tail = [p for p in voiced if p["timestamp_seconds"] >= tail_start - 1e-9]
    # This is exclusion, never octave correction. The independent comparison
    # must continue the preceding measured pitch while the raw path disagrees.
    # A high-energy unvoiced vowel/offset is NOT silent padding.
    terminal = bool(
        tail
        and last - usable[-1]["timestamp_seconds"] <= 0.08 + 1e-9
        and all(
            p.get("quality_usable") is False
            and p["energy_rms"] <= energy * 0.35
            and p.get("filter_disagreement_st", 0) > 6
            and p.get("comparison_f0_hz")
            and abs(12 * math.log2(p["comparison_f0_hz"] / usable[-1]["f0_hz"])) <= 1.5
            for p in tail
        )
        and all(
            p["energy_rms"] <= energy * 0.35
            for p in window
            if p["timestamp_seconds"] >= tail_start - 1e-9
        )
    )
    b = tail_start if terminal else end
    retained = [p for p in voiced if a <= p["timestamp_seconds"] < b - 1e-9]
    if not (onset or terminal) or len(retained) < 14 or len(retained) / len(voiced) < 0.7:
        return fallback
    return ToneEvidenceRegion(
        start,
        end,
        a,
        b,
        len(prefix) if onset else 0,
        len(tail) if terminal else 0,
        "periodicity_energy_supported_boundaries_v1",
    )
