"""Preregistered, target-independent offline pooling rules; no classifier imports."""

import numpy as np

ARMS = ("UNIFORM_SAFE_OWNER", "CENTRAL_HALF", "ACOUSTIC_WEIGHTED")
MIN_SECONDS = 0.060
ZERO_EPSILON = np.finfo(np.float64).tiny


def central_half(ids):
    """ceil(N/2) consecutive frames, floor((N-K)/2) start; ties go earlier."""
    ids = np.asarray(ids, dtype=int)
    count = (len(ids) + 1) // 2
    start = (len(ids) - count) // 2
    return ids[start : start + count]


def acoustic_features(values, rate):
    """Exact RMS/high-band equations from ownership_diagnostics.features only."""
    size, hop = round(0.020 * rate), round(0.005 * rate)
    frequencies = np.fft.rfftfreq(size, 1 / rate)
    rows = []
    for center in range(size // 2, len(values) - size // 2 + 1, hop):
        x = values[center - size // 2 : center + size // 2]
        power = abs(np.fft.rfft((x - x.mean()) * np.hanning(size))) ** 2
        rows.append(
            {
                "time": center / rate,
                "rms_20ms": float(np.sqrt(np.mean(x * x))),
                "high_band_fraction": float(
                    power[frequencies >= 3400].sum() / max(float(power.sum()), 1e-24)
                ),
            }
        )
    return rows


def acoustic_weights(rms, high_band_fraction):
    rms, high = np.asarray(rms, float), np.asarray(high_band_fraction, float)
    if rms.shape != high.shape or not (np.isfinite(rms).all() and np.isfinite(high).all()):
        raise ValueError("invalid_acoustic_values")
    return np.maximum(rms, 0) * (1 - np.clip(high, 0, 1))


def map_acoustics(centers, features):
    """Nearest timestamp, earlier timestamp on a tie; no interpolation."""
    times = np.array([r["time"] for r in features])
    if not len(times) or not np.all(np.diff(times) > 0):
        raise ValueError("invalid_acoustic_timestamps")
    indices = [int(np.abs(times - t).argmin()) for t in centers]
    return [features[i] for i in indices]


def representation(arm, ownership, owner_span, ids, centers, features):
    """Numeric owner/geometry/acoustics only. Eligibility for heads is separate."""
    if arm not in ARMS:
        raise ValueError("unknown_arm")
    ids, centers = np.asarray(ids, int), np.asarray(centers, float)
    selected = central_half(ids) if arm == "CENTRAL_HALF" else ids
    c = centers[selected]
    support_span = (
        [max(owner_span[0], float(c[0] - 0.010)), min(owner_span[1], float(c[-1] + 0.010))]
        if len(c)
        else None
    )
    support = max(0.0, support_span[1] - support_span[0]) if support_span else 0.0
    result = {
        "arm": arm,
        "ownership": ownership,
        "ownership_span": owner_span,
        "eligible_frame_ids": ids.tolist(),
        "frame_ids": selected.tolist(),
        "frame_centers": c.tolist(),
        "raw_acoustic_weights": None,
        "mapped_acoustics": None,
        "normalized_weights": [],
        "effective_n": 0.0,
        "effective_support_ms": 0.0,
        "frame_cell_support_ms": len(c) * 20,
        "support_span": support_span,
        "support_ms": support * 1000,
        "center_extent_ms": float((c[-1] - c[0]) * 1000) if len(c) else 0,
        "owner_duration_ms": (owner_span[1] - owner_span[0]) * 1000,
        "abstention_reason": None,
    }
    if ownership != "safe":
        result["abstention_reason"] = "ownership_" + ownership
        return result
    raw = np.ones(len(c), dtype=float)
    if arm == "ACOUSTIC_WEIGHTED":
        mapped = [
            {k: r[k] for k in ("time", "rms_20ms", "high_band_fraction")}
            for r in map_acoustics(c, features)
        ]
        raw = acoustic_weights(
            [r["rms_20ms"] for r in mapped], [r["high_band_fraction"] for r in mapped]
        )
        result.update(mapped_acoustics=mapped, raw_acoustic_weights=raw.tolist())
    total = float(raw.sum())
    if total <= ZERO_EPSILON:
        result["abstention_reason"] = "zero_usable_weight"
        return result
    weights = raw / total
    effective_n = float(1 / np.sum(weights**2))
    result.update(
        normalized_weights=weights.tolist(),
        effective_n=effective_n,
        effective_support_ms=20 * effective_n,
    )
    if len(c) < 3 or support < MIN_SECONDS - 1e-9:
        result["abstention_reason"] = "insufficient_60ms_support"
    # Kish effective_n is descriptive: no new concentration threshold is fitted.
    return result


def native_subset(rows, per_tone=64):
    """Test/primary only, per-tone round robin sorted speakers and exact item IDs."""
    selected = []
    for tone in ("T1", "T2", "T3", "T4"):
        groups = {}
        for row in rows:
            o = row["original"]
            if o["partition"] == "test" and row["primary_eligible"] and o["label"] == tone:
                groups.setdefault(o["speaker_id"], []).append(row)
        for group in groups.values():
            group.sort(key=lambda r: r["example_id"])
        ordered = []
        while any(groups.values()):
            for speaker in sorted(groups):
                if groups[speaker]:
                    ordered.append(groups[speaker].pop(0))
        if len(ordered) < per_tone:
            raise ValueError("insufficient_native_tone_stratum")
        selected.extend(ordered[:per_tone])
    return selected
