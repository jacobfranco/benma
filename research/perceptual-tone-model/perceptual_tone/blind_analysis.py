"""Reliability-first, read-only analysis of a frozen solo perceptual review.

No inference or training entry points. The gate is a descriptive analyst decision;
the earlier numerical protocol is reported separately, never retuned.
"""

from collections import Counter

from .blind_packet import CHOICES, VERSION, require, validate_review
from .common import digest

PACKET_SHA = "f5c041a22f03ddf41337472fd494397a055adfee9fd16ba234c75d3ea2ead6a4"
FROZEN_GATE_SHA = "665faecead89421a79e83762b9260319c409600922d241317f68ec76aa71c1b4"
TONES = tuple(CHOICES)
NUMBERED = TONES[:4]


def fraction(n, d):
    return {"n": n, "d": d, "fraction": n / d if d else None}


def validate_export(manifest, review):
    require(digest(manifest) == PACKET_SHA, "packet_hash")
    require(manifest["packet_version"] == VERSION, "packet_version")
    ids = [r["annotation_id"] for r in manifest["items"]]
    require(len(ids) == len(set(ids)) == 52, "packet_population")
    result = validate_review({**manifest, "packet_sha256": PACKET_SHA}, review)
    require(review["reviewer"].strip().lower() == "jacob", "unexpected_reviewer")
    return result


def join_key(review, key):
    require(key["packet_sha256"] == review["packet_sha256"], "key_hash")
    require(key["packet_version"] == review["packet_version"], "key_version")
    ids = [r["annotation_id"] for r in review["reviews"]]
    require([r["annotation_id"] for r in key["items"]] == ids, "key_ids")
    require(len(ids) == len(set(ids)) == 52, "join_population")
    joined = [{**k, "human": r} for k, r in zip(key["items"], review["reviews"], strict=True)]
    by_id = {r["annotation_id"]: r for r in joined}
    for r in joined:
        require(r["base_role"] in ("control", "learner"), "base_role")
        if r["duplicate_of"]:
            original = by_id.get(r["duplicate_of"])
            require(original is not None, "missing_repeat_original")
            require(not original["duplicate_of"] and original["order"] < r["order"], "repeat_order")
            require(r["role"] == "repeat", "repeat_role")
            require(all(original[k] == r[k] for k in ("unit_id", "base_role")), "repeat_identity")
        else:
            require(r["role"] == r["base_role"], "original_role")
    require(sum(bool(r["duplicate_of"]) for r in joined) == 8, "repeat_count")
    for role, count in [("control", 28), ("learner", 16)]:
        originals = [r for r in joined if r["base_role"] == role and not r["duplicate_of"]]
        require(len(originals) == len({r["unit_id"] for r in originals}) == count, "unique_count")
    return joined


def control_metrics(rows):
    matrix = {t: {p: 0 for p in TONES} for t in TONES[:-1]}
    for r in rows:
        matrix[r["native_control_gold_tone"]][r["human"]["perceived_tone"]] += 1
    numbered_ref = [r for r in rows if r["native_control_gold_tone"] in NUMBERED]
    numbered = [r for r in numbered_ref if r["human"]["perceived_tone"] in NUMBERED]
    numbered_any_ref = [r for r in rows if r["human"]["perceived_tone"] in NUMBERED]
    non_abstain = [r for r in rows if r["human"]["perceived_tone"] != "UNCLEAR"]

    def correct(items):
        return sum(r["native_control_gold_tone"] == r["human"]["perceived_tone"] for r in items)

    return {
        "matrix": matrix,
        "full_exact": fraction(correct(rows), len(rows)),
        "non_unclear_coverage": fraction(len(non_abstain), len(rows)),
        "non_unclear_conditional": fraction(correct(non_abstain), len(non_abstain)),
        "numbered_judgment_coverage_all_controls": fraction(len(numbered_any_ref), len(rows)),
        "numbered_judgment_conditional_all_controls": fraction(
            correct(numbered_any_ref), len(numbered_any_ref)
        ),
        "numbered_reference_coverage": fraction(len(numbered), len(numbered_ref)),
        "numbered_reference_conditional": fraction(correct(numbered), len(numbered)),
        "numbered_reference_full": fraction(correct(numbered_ref), len(numbered_ref)),
        "unclear": fraction(len(rows) - len(non_abstain), len(rows)),
        "recall": {t: fraction(matrix[t][t], sum(matrix[t].values())) for t in matrix},
    }


def first_stage(joined):
    """Only control reference labels and repeat judgments enter this output."""
    controls = [r for r in joined if r["base_role"] == "control" and not r["duplicate_of"]]
    require(
        Counter(r["native_control_gold_tone"] for r in controls)
        == {"T1": 6, "T2": 6, "T3": 6, "T4": 6, "NEUTRAL": 4},
        "control_balance",
    )
    metrics = control_metrics(controls)
    by_id = {r["annotation_id"]: r for r in joined}
    pairs = []
    for r in joined:
        if not r["duplicate_of"]:
            continue
        a, b = by_id[r["duplicate_of"]]["human"], r["human"]
        pairs.append(
            {
                "original_id": r["duplicate_of"],
                "repeat_id": r["annotation_id"],
                "base_role": r["base_role"],
                "first": a,
                "second": b,
                "exact": a["perceived_tone"] == b["perceived_tone"],
                "both_numbered": all(x["perceived_tone"] in NUMBERED for x in (a, b)),
                "informative_exact": a["perceived_tone"] == b["perceived_tone"]
                and a["perceived_tone"] != "UNCLEAR"
                and all(x["usability"] != "UNUSABLE" for x in (a, b)),
                "confidence_delta": b["confidence"] - a["confidence"],
                "unclear_transition": (a["perceived_tone"] == "UNCLEAR")
                != (b["perceived_tone"] == "UNCLEAR"),
            }
        )
    return {
        "controls": metrics,
        "control_rows": [
            {
                k: r[k]
                for k in (
                    "annotation_id",
                    "unit_id",
                    "speaker_id",
                    "native_control_gold_tone",
                    "human",
                )
            }
            for r in controls
        ],
        "control_confidence": {
            str(c): control_metrics([r for r in controls if r["human"]["confidence"] == c])
            for c in range(1, 6)
        },
        "control_usability": {
            str(c): control_metrics([r for r in controls if r["human"]["usability"] == c])
            for c in (None, "CLEAR", "BORDERLINE", "UNUSABLE")
        },
        "pairs": pairs,
        "repeat_exact": fraction(sum(p["exact"] for p in pairs), len(pairs)),
        "repeat_informative_exact": fraction(
            sum(p["informative_exact"] for p in pairs), len(pairs)
        ),
        "repeat_numbered": fraction(
            sum(p["exact"] and p["both_numbered"] for p in pairs),
            sum(p["both_numbered"] for p in pairs),
        ),
        "repeat_by_role": {
            role: fraction(
                sum(p["exact"] for p in pairs if p["base_role"] == role),
                sum(p["base_role"] == role for p in pairs),
            )
            for role in ("control", "learner")
        },
        "mean_absolute_confidence_delta": sum(abs(p["confidence_delta"]) for p in pairs)
        / len(pairs),
        "unclear_transitions": sum(p["unclear_transition"] for p in pairs),
    }


def registered_checks(stage, review):
    c = stage["controls"]
    # UNUSABLE may never earn gate credit, even if its recorded category matches.
    unusable_correct = Counter(
        r["native_control_gold_tone"]
        for r in stage["control_rows"]
        if r["human"]["usability"] == "UNUSABLE"
        and r["human"]["perceived_tone"] == r["native_control_gold_tone"]
    )
    checks = {
        "full_control_23_of_28": c["full_exact"]["n"] - sum(unusable_correct.values()) >= 23,
        "numbered_20_of_24": c["numbered_reference_full"]["n"]
        - sum(unusable_correct[t] for t in NUMBERED)
        >= 20,
        "each_numbered_4_of_6": all(
            c["recall"][t]["n"] - unusable_correct[t] >= 4 for t in NUMBERED
        ),
        "neutral_3_of_4": c["recall"]["NEUTRAL"]["n"] - unusable_correct["NEUTRAL"] >= 3,
        "informative_repeat_7_of_8": stage["repeat_informative_exact"]["n"] >= 7,
        "confidence_39_of_52": sum(r["confidence"] >= 3 for r in review["reviews"]) >= 39,
        "unclear_at_most_5_of_52": sum(r["perceived_tone"] == "UNCLEAR" for r in review["reviews"])
        <= 5,
    }
    return {
        "criteria": checks,
        "passed": all(checks.values()),
        "note": (
            "Historical numerical protocol; confidence/UNCLEAR criteria span all presentations. "
            "Descriptive classification uses controls and repeats only."
        ),
    }


def gate_record(stage, classification, rationale):
    require(classification in ("STRONG", "USABLE_WITH_CAUTION", "INSUFFICIENT"), "classification")
    require(bool(rationale.strip()), "gate_rationale")
    return {
        "classification": classification,
        "rationale": rationale,
        "basis": "controls_and_repeats_only",
        "first_stage_sha256": digest(stage),
        "confirmatory_model_evaluation_permitted": classification != "INSUFFICIENT",
    }


def require_gate(stage, gate):
    require(gate["basis"] == "controls_and_repeats_only", "gate_basis")
    require(gate["first_stage_sha256"] == digest(stage), "gate_evidence")
    require(
        gate["classification"] in ("STRONG", "USABLE_WITH_CAUTION", "INSUFFICIENT"),
        "gate_classification",
    )


def tone(value):
    return "NEUTRAL" if value == 5 else f"T{value}" if value in (1, 2, 3, 4) else None


def compare(rows, field, reference="human"):
    return fraction(
        sum(
            r[field] == (r["human"]["perceived_tone"] if reference == "human" else r[reference])
            for r in rows
        ),
        len(rows),
    )


def learner_analysis(joined, release, stage, gate):
    require_gate(stage, gate)
    require(digest(gate) == FROZEN_GATE_SHA, "frozen_gate_changed")
    metadata = {r["example_id"]: r for r in release}
    selected = [r for r in joined if r["base_role"] == "learner" and not r["duplicate_of"]]
    require({r["unit_id"] for r in selected} == set(metadata), "learner_population")
    rows = []
    for r in selected:
        m = metadata[r["unit_id"]]
        require(m["eligible_for_training"] is False and not m["quarantined"], "release_eligibility")
        require(r["expected_surface_tone"] == m["expected_surface_tone"], "expected_mismatch")
        rows.append(
            {
                "unit_id": r["unit_id"],
                "annotation_id": r["annotation_id"],
                "take": r["learner_take"][0].split("/")[-1].removesuffix(".wav"),
                "index": m["index"],
                "hanzi": m["hanzi"],
                "pinyin": m["intended_pinyin"],
                "qa_id": m["qa_item_id"],
                "lexical": tone(r["lexical_tone"]),
                "expected": tone(r["expected_surface_tone"]),
                "surface_alternatives": r["surface_alternatives"],
                "human": r["human"],
                "expanded": r["expanded_model_result"]["prediction"],
                "expanded_confidence": r["expanded_model_result"]["confidence"],
                "pilot": r["pilot_model_result"]["prediction"],
                "pilot_confidence": r["pilot_model_result"]["confidence"],
                "deterministic": r["deterministic_result"]["prediction"],
                "deterministic_observed": r["deterministic_result"]["observed"],
            }
        )
    rows.sort(key=lambda r: (r["take"], r["index"]))
    eligible = [
        r
        for r in rows
        if r["human"]["perceived_tone"] in NUMBERED and r["human"]["usability"] != "UNUSABLE"
    ]
    resolved = [r for r in rows if r["expected"] is not None]
    resolved_numbered = [r for r in resolved if r["expected"] in NUMBERED]
    non_unclear = [r for r in rows if r["human"]["perceived_tone"] != "UNCLEAR"]
    expected_eligible = [r for r in resolved if r in eligible and r["expected"] in NUMBERED]
    strata = {}
    for threshold in (1, 2, 3, 4):
        subset = [r for r in eligible if r["human"]["confidence"] >= threshold]
        strata[str(threshold)] = {
            "unit_ids": [r["unit_id"] for r in subset],
            "expanded": compare(subset, "expanded"),
            "pilot": compare(subset, "pilot"),
            "paired": dict(
                Counter(
                    "both"
                    if r["expanded"] == r["pilot"] == r["human"]["perceived_tone"]
                    else "expanded_only"
                    if r["expanded"] == r["human"]["perceived_tone"]
                    else "pilot_only"
                    if r["pilot"] == r["human"]["perceived_tone"]
                    else "neither"
                    for r in subset
                )
            ),
        }
    high_clear = [
        r for r in eligible if r["human"]["confidence"] >= 4 and r["human"]["usability"] == "CLEAR"
    ]
    disagreements = [r for r in rows if r["expanded"] != r["pilot"]]
    require(
        len(disagreements) == 7 and all(r["expanded"] == "T2" for r in disagreements),
        "frozen_disagreement_population",
    )
    return {
        "status": "EXPLORATORY_ONLY_NOT_TRANSFER_VALIDATION"
        if gate["classification"] == "INSUFFICIENT"
        else "DESCRIPTIVE_SOLO_PERCEPTUAL_COMPARISON",
        "gate_sha256": digest(gate),
        "rows": rows,
        "tone_distribution": {
            t: sum(r["human"]["perceived_tone"] == t for r in rows) for t in TONES
        },
        "confidence_distribution": {
            str(c): sum(r["human"]["confidence"] == c for r in rows) for c in range(1, 6)
        },
        "usability_distribution": dict(Counter(str(r["human"]["usability"]) for r in rows)),
        "whole_target_usage": fraction(
            sum(r["human"]["whole_target_heard"] for r in rows), len(rows)
        ),
        "confidence_at_least_3_rows": [r for r in rows if r["human"]["confidence"] >= 3],
        "non_unclear_comparison": {m: compare(non_unclear, m) for m in ("expanded", "pilot")},
        "non_unclear_comparison_note": (
            "Categorical descriptive agreement; any human NEUTRAL is "
            "retained here and separately reported, never treated as a four-tone score."
        ),
        "low_confidence_unit_ids": [r["unit_id"] for r in rows if r["human"]["confidence"] <= 2],
        "strata": strata,
        "high_confidence_clear": {
            "expanded": compare(high_clear, "expanded"),
            "pilot": compare(high_clear, "pilot"),
        },
        "excluded_numbered_scoring": {
            "unclear": [r["unit_id"] for r in rows if r["human"]["perceived_tone"] == "UNCLEAR"],
            "neutral": [r for r in rows if r["human"]["perceived_tone"] == "NEUTRAL"],
            "unusable": [r["unit_id"] for r in rows if r["human"]["usability"] == "UNUSABLE"],
            "usability_unspecified": sum(r["human"]["usability"] is None for r in rows),
        },
        "expected_rows": resolved,
        "expected_numbered_rows": resolved_numbered,
        "expected_neutral_rows": [r for r in resolved if r["expected"] == "NEUTRAL"],
        "expected_human_full": compare(resolved, "expected"),
        "expected_human_numbered_full": compare(resolved_numbered, "expected"),
        "expected_human_numbered_conditional": compare(expected_eligible, "expected"),
        "expected_human_numbered_coverage": fraction(
            len(expected_eligible), len(resolved_numbered)
        ),
        "models_vs_expected_full": {
            m: compare(resolved, m, "expected") for m in ("expanded", "pilot")
        },
        "models_vs_expected_numbered_full": {
            m: compare(resolved_numbered, m, "expected") for m in ("expanded", "pilot")
        },
        "models_vs_expected_same_human_subset": {
            m: compare(expected_eligible, m, "expected") for m in ("expanded", "pilot")
        },
        "models_vs_human_same_expected_subset": {
            m: compare(expected_eligible, m) for m in ("expanded", "pilot")
        },
        "t2_disagreement_rows": disagreements,
        "t2_human_distribution": {
            t: sum(r["human"]["perceived_tone"] == t for r in disagreements) for t in TONES
        },
        "by_take": {
            take: {
                t: sum(r["take"] == take and r["human"]["perceived_tone"] == t for r in rows)
                for t in TONES
            }
            for take in sorted({r["take"] for r in rows})
        },
        "no_training_adaptation_or_inference": True,
    }
