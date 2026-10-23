"""Offline speech-region candidates. Only timing and saved RMS enter selection.

Energy is support, not proof of phonetic identity. An internal below-gate run
is unresolved ownership, never an invitation to select its largest island.
No production caller imports this diagnostic module.
"""

import math

MIN_SECONDS = 0.060
CELL_HALF = 0.005
MAX_CADENCE = 0.015
CANDIDATES = ("AZURE_WHOLE", "AZURE_ENERGY_SUPPORTED", "AZURE_WITH_SMALL_ONSET_CONTEXT")


def select_region(whole, previous, following, duration, energy, threshold, candidate):
    """energy is a list of (timestamp_seconds, energy_rms), without F0 fields.

    The onset variant adds at most one existing half-cell (5 ms), bounded by
    the midpoint of any unassigned provider gap. Fixed encoder context is
    handled separately. Overlapping provider owners fail closed.
    """
    if candidate not in CANDIDATES:
        raise ValueError("unknown_candidate")
    result = {
        "status": "invalid", "reason": None, "span": None,
        "ownership_status": "invalid", "energy_support_ms": 0.0,
        "above_gate_frames": 0, "internal_below_gate_centers": [],
        "onset_added_ms": 0.0,
    }

    def reject(reason, ownership="invalid"):
        result.update(reason=reason, ownership_status=ownership)
        return result

    def valid_span(span):
        return (span is not None and len(span) == 2
                and all(type(x) in (float, int) and math.isfinite(x) for x in span)
                and 0 <= span[0] < span[1] <= duration)

    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        return reject("invalid_duration")
    if not valid_span(whole) or any(
        span is not None and not valid_span(span) for span in (previous, following)
    ):
        return reject("invalid_or_missing_azure_timing")
    a, b = whole
    if (previous is not None and previous[1] > a) or (
        following is not None and following[0] < b
    ):
        return reject("overlapping_azure_ownership", "ambiguous")
    if (not isinstance(threshold, (int, float)) or not math.isfinite(threshold)
            or threshold <= 0 or not energy
            or any(not all(type(v) in (int, float) and math.isfinite(v) for v in pair)
                   or len(pair) != 2 or pair[1] < 0 for pair in energy)):
        return reject("missing_acoustic_validity_metadata")
    start = a
    if candidate == "AZURE_WITH_SMALL_ONSET_CONTEXT":
        limit = (previous[1] + a) / 2 if previous is not None else 0
        start = max(limit, a - CELL_HALF, 0)
    frames = [(t, e) for t, e in energy if start <= t < b]
    if (not frames or frames[0][0] - start > MAX_CADENCE
            or b - frames[-1][0] > MAX_CADENCE
            or any(not 0 < y[0] - x[0] <= MAX_CADENCE + 1e-9
                   for x, y in zip(frames, frames[1:]))):
        return reject("missing_acoustic_frame_coverage")
    high = [(t, e) for t, e in frames if e >= threshold]
    result.update(span=[start, b], ownership_status="safe")
    if not high:
        return reject("no_energy_support", "invalid")
    supported = [max(start, high[0][0] - CELL_HALF), min(b, high[-1][0] + CELL_HALF)]
    if candidate == "AZURE_ENERGY_SUPPORTED":
        result["span"] = supported
    pool = result["span"]
    low = [t for t, e in frames if high[0][0] < t < high[-1][0] and e < threshold]
    support = sum(max(0, min(pool[1], t + CELL_HALF) - max(pool[0], t - CELL_HALF))
                  for t, _ in high)
    result.update(
        duration_ms=1000 * (pool[1] - pool[0]),
        above_gate_frames=len(high), energy_support_ms=1000 * support,
        energy_envelope=supported, internal_below_gate_centers=low,
        onset_added_ms=1000 * (a - pool[0]) if pool[0] < a else 0.0,
    )
    if low:
        return reject("ambiguous_interrupted_energy_support", "ambiguous")
    if pool[1] - pool[0] < MIN_SECONDS - 1e-9 or support < MIN_SECONDS - 1e-9:
        return reject("too_little_material", "safe")
    result.update(status="valid", reason="continuous_energy_supported_azure_ownership")
    return result
