"""Fixed, label-independent numeric feature contract. No text/IDs/paths/coaching."""

import numpy as np

VERSION = "benma-numeric-v1"
GEOMETRY = (
    "start_st",
    "end_st",
    "minimum_st",
    "excursion_st",
    "fall_st",
    "recovery_st",
    "minimum_position",
    "net_st",
    "measured_net_st",
    "dominant_excursion_st",
    "counter_excursion_st",
    "gesture_end_position",
    "fall_consistency",
    "rise_consistency",
    "support_seconds",
    "selected_extent_seconds",
)
QUALITY = (
    "raw_voiced_frames",
    "selected_frames",
    "retained_fraction",
    "early_retained_fraction",
    "middle_retained_fraction",
    "late_retained_fraction",
    "largest_island_seconds",
    "selected_islands",
    "largest_raw_gap_seconds",
    "largest_selected_gap_seconds",
    "missing_head_seconds",
    "missing_tail_seconds",
    "maximum_raw_jump_semitones",
    "discontinuities",
)


def _number(value):
    if value is None:
        return np.nan
    if not isinstance(value, (int, float, bool)) or not np.isfinite(value):
        raise ValueError("Non-numeric/non-finite value in allowlisted numeric feature")
    return float(value)


def vector(row, group):
    values = {}

    def put(key, value):
        values[key] = _number(value)

    def one_hot(key, value, categories):
        for category in (*categories, None):
            values[f"{key}={category}"] = float(
                value == category if value in categories else category is None
            )

    if group == "benma":
        d = row["deterministic"]
        if d is None:
            raise ValueError("Run frozen Benma replay before feature export")
        for tone in range(1, 5):
            put(f"family_support.T{tone}", d["family_scores"].get(f"TONE_{tone}"))
        for key in (
            "winner_support",
            "runner_up_support",
            "clarity",
            "duration_seconds",
            "structural_reliability",
        ):
            put(key, d.get(key))
        for key in ("acoustic", "runner_up"):
            put(f"margin.{key}", d["margins"].get(key))
        for key in ("agreeing", "total", "fraction"):
            put(f"probe.{key}", d["probe_agreement"].get(key))
        for key in GEOMETRY:
            put(f"shape.{key}", (d.get("shape") or {}).get("features", {}).get(key))
        for key in QUALITY:
            put(f"quality.{key}", (d.get("eligibility") or {}).get("metrics", {}).get(key))
        one_hot(
            "reliability", d.get("evidence_reliability"), ("trustworthy", "fragile", "unavailable")
        )
        one_hot("gesture", d.get("gesture_strength"), ("full", "weak", "unavailable"))
        one_hot(
            "family", d.get("observed_family"), ("TONE_1", "TONE_2", "TONE_3", "TONE_4", "UNCLEAR")
        )
        points = [
            p.get("normalized_semitones", p.get("st"))
            for segment in d.get("normalized_f0_segments", [])
            for p in segment
        ]
        points = np.asarray([_number(p) for p in points], dtype=float)
        points = points[np.isfinite(points)]
        for key, value in zip(
            ("min", "q25", "median", "q75", "max"),
            np.quantile(points, [0, 0.25, 0.5, 0.75, 1]) if len(points) else [None] * 5,
            strict=True,
        ):
            put(f"contour.{key}", value)
        put("contour.range", float(np.ptp(points)) if len(points) else None)
        put("contour.points", len(points))
        put("contour.segments", len(d.get("normalized_f0_segments", [])))
    elif group == "context":
        expected = row["expected"]
        for key in ("lexical_tone", "surface_tone", "previous_tone", "next_tone"):
            one_hot(key, expected.get(key), (0, 1, 2, 3, 4))
        for tone in range(1, 5):
            put(f"acceptable_family.T{tone}", f"TONE_{tone}" in expected["acceptable_families"])
        put("neutral_context", expected.get("neutral_context"))
        put(
            "target_is_neutral",
            None if expected["lexical_tone"] is None else expected["lexical_tone"] == 0,
        )
        put("syllable_index", row["target"]["syllable_index"])
        one_hot(
            "phrase_position",
            expected.get("phrase_position"),
            ("initial", "medial", "final", "isolated"),
        )
    else:
        raise ValueError(f"Unknown feature group: {group}")
    return list(values), np.array(list(values.values()), dtype=np.float64)


def matrix(rows, groups, embeddings=None):
    columns, blocks = [], []
    if not groups or len(set(groups)) != len(groups):
        raise ValueError("Feature groups must be nonempty and unique")
    for group in groups:
        if group == "embeddings":
            if embeddings is None or set(embeddings) != {r["example_id"] for r in rows}:
                raise ValueError("Embedding/example identity mismatch")
            block = np.stack([embeddings[r["example_id"]] for r in rows])
            if block.ndim != 2 or not np.isfinite(block).all():
                raise ValueError("Invalid embeddings")
            columns.extend(f"embedding.{i}" for i in range(block.shape[1]))
        else:
            extracted = [vector(row, group) for row in rows]
            names = extracted[0][0]
            if any(names != item[0] for item in extracted):
                raise ValueError("Feature schema drift")
            block = np.stack([item[1] for item in extracted])
            columns.extend(f"{group}.{name}" for name in names)
        blocks.append(block)
    values = np.concatenate(blocks, axis=1)
    # Missing indicators exist for every column, including held-out-only missingness.
    return np.concatenate([values, np.isnan(values).astype(float)], axis=1), columns + [
        f"missing.{c}" for c in columns
    ]


def baseline_prediction(row):
    return {
        "STRONG_MATCH": "acceptable",
        "PARTIAL_OR_WEAK": "borderline",
        "CLEAR_DIFFERENCE": "incorrect",
        "UNAVAILABLE": "abstain",
    }[row["deterministic"]["learner_grade"]["agreement"]]
