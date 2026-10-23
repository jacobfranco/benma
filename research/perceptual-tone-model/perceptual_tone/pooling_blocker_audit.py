"""Bounded offline diagnosis of sealed pooling outputs. No encoder replay or fitting."""

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from .common import PACKAGE, ROOT, digest, file_hash, read_json, write_json
from .frame_attribution import CLASSES, affine_head, frame_scores
from .pooling_confirmatory import LOCK
from .pooling_confirmatory import OUT as PRIOR

OUT = PACKAGE / "data/generated/pooling-blocker-audit-v1"
EVIDENCE = PACKAGE / "data/generated/learner-transfer-v1-20261019/primary/deterministic"
GATE = PACKAGE / "data/generated/realized-tone-analysis-v1-20261019/03-reliability-gate.json"
HEADS = ("expanded", "pilot")
ARM = "ACOUSTIC_WEIGHTED"
RIGHT = "CONTRACT_RIGHT"


def load_sealed():
    assert (
        file_hash(PRIOR / "representation-manifest.json")
        == read_json(PRIOR / "representation-manifest-seal.json")["sha256"]
    )
    manifest = read_json(PRIOR / "representation-manifest.json")
    reps = {(r["id"], r["arm"], r["perturbation"]): r for r in manifest["records"]}
    preds = {
        (r["id"], r["arm"], r["perturbation"], r["head"]): r
        for r in read_json(PRIOR / "predictions.json")["rows"]
    }
    return reps, preds


def right_frame(base, right):
    """Extract sealed entries, checking exact one-frame deletion and renormalization."""
    assert right["frame_ids"] == base["frame_ids"][:-1]
    w = np.asarray(base["normalized_weights"], float)
    np.testing.assert_allclose(right["normalized_weights"], w[:-1] / w[:-1].sum(), atol=1e-15)
    a, b = base["ownership_span"]
    audit = base["acoustic_audit"]
    return {
        "removed_frame_id": base["frame_ids"][-1],
        "timestamp": base["frame_centers"][-1],
        "mapped_timestamp": audit["mapped_timestamps"][-1],
        "owner_relative_location": (base["frame_centers"][-1] - a) / (b - a),
        "owner_start": a,
        "owner_end": b,
        "removed_raw_weight": audit["raw_weights"][-1],
        "removed_weight_share": float(w[-1]),
        "removed_rms": audit["rms_20ms"][-1],
        "removed_high_band_fraction": audit["high_band_fraction"][-1],
        "neighbor_frame_ids": base["frame_ids"][-4:-1],
        "neighbor_weights": w[-4:-1].tolist(),
        "neighbor_raw_weights": audit["raw_weights"][-4:-1],
        "effective_n": base["effective_n"],
        "effective_n_after": right["effective_n"],
        "frame_count": base["frame_count"],
        "remaining_frames": right["frame_count"],
        "support_ms": base["support_ms"],
        "support_after_ms": right["support_ms"],
        "max_weight_share": float(max(w)),
        "first_weight_share": float(w[0]),
        "final_quarter_share": float(
            w[np.asarray(base["frame_centers"]) >= a + 0.75 * (b - a)].sum()
        ),
        "effective_n_fraction": base["effective_n"] / base["frame_count"],
    }


def selection_rows(reps, preds):
    rows = []
    for (i, arm, state), b in sorted(reps.items()):
        if arm != ARM or state != "BASE" or b["dataset"] not in ("native", "learner_primary"):
            continue
        if (i, ARM, "BASE", "expanded") not in preds:
            continue
        w = b["normalized_weights"]
        r = {
            "id": i,
            "dataset": b["dataset"],
            "tone": b["native_label"],
            "frame_count": b["frame_count"],
            "support_ms": b["support_ms"],
            "effective_n": b["effective_n"],
            "removed_weight_share": w[-1],
        }
        for h in HEADS:
            p = preds[i, ARM, "BASE", h]
            r[h + "_prediction"] = p["prediction"]
            q = preds.get((i, ARM, RIGHT, h))
            r[h + "_tv"] = (
                float(np.abs(np.array(p["probabilities"]) - q["probabilities"]).sum() / 2)
                if q
                else None
            )
            r[h + "_flip"] = p["prediction"] != q["prediction"] if q else None
        rows.append(r)
    return rows


def select(rows):
    """Only sealed predictions, native labels, support and weights enter selection."""
    native = [r for r in rows if r["dataset"] == "native"]
    reasons = {}
    for r in native:
        if any(r[h + "_flip"] for h in HEADS):
            reasons[r["id"]] = ["any_head_RIGHT_flip"]
    for key in ("expanded_tv", "pilot_tv", "removed_weight_share"):
        for r in sorted(native, key=lambda r: (-r[key], r["id"]))[:3]:
            reasons.setdefault(r["id"], []).append("top3_" + key)
    cases = sorted(reasons)
    lookup = {r["id"]: r for r in rows}
    # Fixed low-TV definition for matching only, never an acceptance/representation rule.
    eligible = [
        r
        for r in native
        if r["id"] not in cases
        and all(
            not r[h + "_flip"] and r[h + "_tv"] <= 0.02 and r[h + "_prediction"] == r["tone"]
            for h in HEADS
        )
    ]
    controls, used = [], set()
    for i in cases:
        c = lookup[i]
        pool = [r for r in eligible if r["id"] not in used]
        best = min(
            pool,
            key=lambda r: (
                r["tone"] != c["tone"],
                abs(r["frame_count"] - c["frame_count"]),
                abs(r["support_ms"] - c["support_ms"]),
                abs(r["effective_n"] - c["effective_n"]),
                r["id"],
            ),
        )
        controls.append({"case": i, "control": best["id"]})
        used.add(best["id"])
    learner = [r for r in rows if r["dataset"] == "learner_primary"]
    disagree = sorted(r["id"] for r in learner if r["expanded_prediction"] != r["pilot_prediction"])
    agree = [r for r in learner if r["id"] not in disagree]
    matches, used = [], set()
    for i in disagree:
        c = lookup[i]
        pool = [r for r in agree if r["id"] not in used]
        if not pool:
            break
        best = min(
            pool,
            key=lambda r: (
                abs(r["frame_count"] - c["frame_count"]),
                abs(r["support_ms"] - c["support_ms"]),
                abs(r["effective_n"] - c["effective_n"]),
                r["id"],
            ),
        )
        matches.append({"case": i, "control": best["id"]})
        used.add(best["id"])
    return {
        "native_cases": cases,
        "native_reasons": reasons,
        "native_controls": controls,
        "learner_disagreements": disagree,
        "learner_controls": matches,
        "learner_base_usable_ids": sorted(r["id"] for r in learner),
    }


def seal():
    OUT.mkdir(parents=True, exist_ok=True)
    reps, preds = load_sealed()
    selection = select(selection_rows(reps, preds))
    if (OUT / "selection.json").exists():
        assert read_json(OUT / "selection.json") == selection
    else:
        write_json(OUT / "selection.json", selection)
    plan = {
        "sealed_at": datetime.now(UTC).isoformat(),
        "selection_sha256": file_hash(OUT / "selection.json"),
        "stage": "before detailed contributions and learner evidence interpretation",
        "native_rule": (
            "Union of every acoustic RIGHT argmax flip in either head and top "
            "three per head TV and top three removed shares; descending value, ID "
            "tie break; never cap away flips."
        ),
        "native_controls": (
            "One unique stable BOTH-head-correct control per case, TV <= .02 "
            "each; lexicographic same native tone, frame count distance, duration "
            "distance, effective_n distance, ID. No contribution/phonetic "
            "selection."
        ),
        "learner_rule": (
            "All natural learner acoustic BASE head disagreements; unique "
            "agreement controls matched by frame count, duration, effective_n, "
            "ID, without learner tone/grade inputs."
        ),
        "bins": {
            "removed_weight_share": [0, 0.05, 0.10, 0.20, 0.30, 0.40, 1.01],
            "effective_n": [0, 3, 5, 10, 20, 10000],
        },
        "descriptive_concentration_slice": (
            "Top decile of removed native RIGHT shares; not a model cutoff. Also "
            "report fixed bins and rank correlations."
        ),
        "geometry_labels": (
            "Descriptive only: low probability top-two margin < .20; confident >= "
            ".50; intermediate otherwise. No classifier decision changes."
        ),
        "evidence_rubric": (
            "STRONG requires already reliable independent listener/reference "
            "realization; MODERATE requires frozen F0 eligibility=eligible and "
            "familySafe deterministic measured family; WEAK for present but "
            "invalid/ambiguous contour; UNAVAILABLE for no retained evidence. "
            "Strong/moderate compatibility is evidence, never gold. Failed solo "
            "annotation prohibited."
        ),
        "attribution": (
            "Existing frame_scores standardized origin; exact weighted deletion "
            "plus remaining-weight renormalization; also save raw-origin "
            "decomposition. Pair = BASE winner vs RIGHT winner if flip, otherwise "
            "BASE runner-up."
        ),
        "no_replay": True,
    }
    if not (OUT / "audit-preregistration.json").exists():
        write_json(OUT / "audit-preregistration.json", plan)
    inherited = read_json(PRIOR / "freeze-before.json")["files"]
    paths = {ROOT / p for p in inherited}
    paths.update(p for p in PRIOR.rglob("*") if p.is_file())
    paths.update(PACKAGE.glob("perceptual_tone/*.py"))
    paths.update(PACKAGE.glob("tests/*.py"))
    paths.update(PACKAGE.glob("*.md"))
    paths.update(EVIDENCE.glob("*.json"))
    paths.add(GATE)
    # New audit code is intentionally outside the protected pre-existing tree.
    paths = {
        p
        for p in paths
        if "pooling_blocker_audit" not in p.name and "pooling-blocker-audit" not in p.name
    }
    files = {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(paths)}
    assert all(files[str((ROOT / p).relative_to(ROOT))] == h for p, h in inherited.items())
    write_json(
        OUT / "freeze-before.json",
        {
            "files": files,
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
            "inherited_freeze_verified": True,
        },
    )
    print(json.dumps({k: len(v) for k, v in selection.items()}))


def weighted_decomposition(scores, bias, weights):
    """z = b + Σ w*s; z_right-z = -w_last*s_last + w_last*z_right_without_bias."""
    weights = np.asarray(weights, float)
    scores, bias = np.asarray(scores, float), np.asarray(bias, float)
    before = weights @ scores + bias
    after = weights[:-1] @ scores[:-1] / weights[:-1].sum() + bias
    removed = weights[-1] * scores[-1]
    renormalization = weights[-1] * (after - bias)
    np.testing.assert_allclose(after - before, -removed + renormalization, atol=2e-12)
    return {
        "before": before.tolist(),
        "after": after.tolist(),
        "bias": bias.tolist(),
        "removed_contribution": removed.tolist(),
        "renormalization_delta": renormalization.tolist(),
        "delta": (after - before).tolist(),
    }


def describe(values):
    v = np.array([x for x in values if x is not None], float)
    return (
        {
            "n": len(v),
            "mean": float(v.mean()),
            "median": float(np.median(v)),
            "min": float(v.min()),
            "max": float(v.max()),
        }
        if len(v)
        else {"n": 0}
    )


def save_table(name, rows):
    write_json(OUT / (name + ".json"), rows)
    with (OUT / (name + ".csv")).open("x") as f:
        writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v
                for k, v in r.items()
            }
            for r in rows
        )


def independent_evidence(raw, deterministic):
    """Explicit whitelist: no expected/lexical labels, grade or human judgment accepted."""
    eligibility = raw["eligibility"]
    segments = [
        [{"time": p["timestamp_seconds"], "semitones": p["normalized_semitones"]} for p in seg]
        for seg in raw["segments"]
    ]
    measurements = []
    for seg in segments:
        y = np.array([p["semitones"] for p in seg])
        measurements.append(
            {
                "n": len(y),
                "start": seg[0]["time"],
                "end": seg[-1]["time"],
                "net_st": float(y[-1] - y[0]),
                "range_st": float(np.ptp(y)),
                "rise_sum_st": float(np.maximum(np.diff(y), 0).sum()),
                "fall_sum_st": float(-np.minimum(np.diff(y), 0).sum()),
                "max_gap_ms": float(1000 * max(np.diff([p["time"] for p in seg]), default=0)),
            }
        )
    shape = deterministic["shape"]
    safe = eligibility["state"] == "sufficient" and shape.get("familySafe", False)
    quality = "MODERATE" if safe else "WEAK" if segments else "UNAVAILABLE"
    # An independent deterministic family is reportable only behind both existing validity gates.
    family = deterministic["prediction"] if safe else None
    return {
        "id": raw["example_id"],
        "quality": quality,
        "eligibility": eligibility,
        "segments": segments,
        "segment_measurements": measurements,
        "family_safe": shape.get("familySafe", False),
        "usable_family": family,
        "evidence_status": "usable_acoustic_family"
        if safe
        else "present_but_invalid_or_ambiguous"
        if segments
        else "no_retained_independent_contour",
        "independent_listener_truth": None,
        "solo_annotation_used": False,
        "source": str(EVIDENCE.relative_to(ROOT)),
        "interpretation": "unresolved"
        if not safe
        else "acoustic evidence only; not realized-tone gold",
    }


def margin_category(prob_margin):
    return "low" if prob_margin < 0.20 else "confident" if prob_margin >= 0.50 else "intermediate"


def summarize_native(rows):
    return {
        "n": len(rows),
        "flips": sum(r["flip"] for r in rows),
        "base_wrong": sum(not r["base_correct"] for r in rows),
        "right_wrong": sum(not r["right_correct"] for r in rows),
        "correct_to_wrong": sum(r["base_correct"] and not r["right_correct"] for r in rows),
        "wrong_to_correct": sum(not r["base_correct"] and r["right_correct"] for r in rows),
        "tv": describe([r["tv"] for r in rows]),
        "removed_weight_share": describe([r["removed_weight_share"] for r in rows]),
        "effective_n": describe([r["effective_n"] for r in rows]),
        "label_supported_by_edge_net": sum(r["label_margin_edge_effect"] > 0 for r in rows),
        "label_opposed_by_edge_net": sum(r["label_margin_edge_effect"] < 0 for r in rows),
    }


def analyze():
    from .learner_transfer import load_models

    plan = read_json(OUT / "audit-preregistration.json")
    assert file_hash(OUT / "selection.json") == plan["selection_sha256"]
    reps, preds = load_sealed()
    selection = read_json(OUT / "selection.json")
    assert select(selection_rows(reps, preds)) == selection
    assert (OUT / "freeze-before.json").exists()
    models = load_models(read_json(LOCK)["model_method"])
    biases = {h: affine_head(m)[3] for h, m in models.items()}
    native, native_details, reconstruction = [], [], []
    detailed = set(selection["native_cases"]) | {m["control"] for m in selection["native_controls"]}
    for i in sorted(
        {
            i
            for (i, a, s), r in reps.items()
            if a == ARM and s == "BASE" and r["dataset"] == "native"
        }
    ):
        base, right = reps[i, ARM, "BASE"], reps[i, ARM, RIGHT]
        structural = right_frame(base, right)
        for h in HEADS:
            p, q = preds[i, ARM, "BASE", h], preds[i, ARM, RIGHT, h]
            z, zr = np.array(p["logits"]), np.array(q["logits"])
            w = structural["removed_weight_share"]
            # Exact identity from existing logits; no head/encoder replay of 659 items.
            removed = (z - biases[h]) - (1 - w) * (zr - biases[h])
            renorm = w * (zr - biases[h])
            current = CLASSES.index(p["prediction"])
            competitor = (
                CLASSES.index(q["prediction"])
                if p["prediction"] != q["prediction"]
                else int(np.argsort(z)[-2])
            )
            label = CLASSES.index(base["native_label"])
            label_comp = max((j for j in range(4) if j != label), key=lambda j: z[j])

            def pair(values, a=current, b=competitor):
                return float(values[a] - values[b])

            r = {
                "id": i,
                "head": h,
                "tone": base["native_label"],
                **structural,
                "base_prediction": p["prediction"],
                "right_prediction": q["prediction"],
                "base_correct": p["prediction"] == base["native_label"],
                "right_correct": q["prediction"] == base["native_label"],
                "flip": p["prediction"] != q["prediction"],
                "tv": float(np.abs(np.array(p["probabilities"]) - q["probabilities"]).sum() / 2),
                "uniform_tv": float(
                    np.abs(
                        np.array(preds[i, "UNIFORM_SAFE_OWNER", "BASE", h]["probabilities"])
                        - preds[i, "UNIFORM_SAFE_OWNER", RIGHT, h]["probabilities"]
                    ).sum()
                    / 2
                ),
                "base_logit_margin": p["logit_margin"],
                "base_probability_margin": p["probability_margin"],
                "margin_pair": [CLASSES[current], CLASSES[competitor]],
                "margin_before": pair(z),
                "margin_after": pair(zr),
                "removed_margin_contribution": pair(removed),
                "renormalization_margin_delta": pair(renorm),
                "removed_class_logit_contributions": removed.tolist(),
                "renormalization_class_logit_delta": renorm.tolist(),
                "label_competitor": CLASSES[label_comp],
                "label_margin_edge_effect": float((z - zr)[label] - (z - zr)[label_comp]),
                "removed_label_margin_contribution": float(removed[label] - removed[label_comp]),
                "starting_margin_category": margin_category(p["probability_margin"]),
            }
            native.append(r)
            if i in detailed:
                hidden = np.load(base["hidden_path"], allow_pickle=False)[base["frame_ids"]]
                scores, bias, raw_scores, intercept = frame_scores(hidden, models[h])
                d = weighted_decomposition(scores, bias, base["normalized_weights"])
                raw_d = weighted_decomposition(raw_scores, intercept, base["normalized_weights"])
                for k, target in (("before", z), ("after", zr), ("removed_contribution", removed)):
                    np.testing.assert_allclose(d[k], target, atol=2e-11)
                reconstruction.append(
                    float(
                        max(
                            np.max(np.abs(np.array(d["before"]) - z)),
                            np.max(np.abs(np.array(d["after"]) - zr)),
                        )
                    )
                )
                direct, ren = -pair(removed), pair(renorm)
                drivers = []
                if r["flip"]:
                    if direct < 0:
                        drivers.append("direct_removal_erodes_BASE_winner")
                    if ren < 0:
                        drivers.append("renormalization_erodes_BASE_winner")
                    if r["starting_margin_category"] == "low":
                        drivers.append("low_starting_margin")
                native_details.append(
                    {
                        **r,
                        "role": "case" if i in selection["native_cases"] else "control",
                        "decomposition": d,
                        "raw_origin_decomposition": raw_d,
                        "removed_unweighted_class_scores": scores[-1].tolist(),
                        "frame_class_scores": scores.tolist(),
                        "mechanisms": drivers or ["no_flip"],
                        "without_renormalization_pair_margin": pair(z - removed),
                        "renormalization_only_pair_margin": pair(z + renorm),
                    }
                )
    save_table("native-right-all", native)
    save_table("right-edge-contributions", native_details)
    topcut = float(
        np.quantile([r["removed_weight_share"] for r in native if r["head"] == HEADS[0]], 0.9)
    )
    correlations, bins, per_tone = [], [], []
    features = (
        "removed_weight_share",
        "effective_n",
        "effective_n_fraction",
        "frame_count",
        "support_ms",
        "removed_rms",
        "removed_high_band_fraction",
        "base_logit_margin",
        "base_probability_margin",
    )
    for h in HEADS:
        group = [r for r in native if r["head"] == h]
        for f in features:
            for target in ("tv", "flip"):
                x, y = np.array([r[f] for r in group]), np.array([r[target] for r in group], float)
                correlations.append(
                    {
                        "head": h,
                        "feature": f,
                        "outcome": target,
                        "n": len(group),
                        "pearson": float(np.corrcoef(x, y)[0, 1]),
                        "spearman": float(spearmanr(x, y).statistic),
                    }
                )
        for f, edges in plan["bins"].items():
            for lo, hi in pairwise(edges):
                rr = [r for r in group if lo <= r[f] < hi]
                bins.append(
                    {
                        "head": h,
                        "feature": f,
                        "lower_inclusive": lo,
                        "upper_exclusive": hi,
                        **summarize_native(rr),
                    }
                )
        for tone in CLASSES:
            rr = [r for r in group if r["tone"] == tone]
            high = [r for r in rr if r["removed_weight_share"] >= topcut]
            per_tone.append(
                {
                    "head": h,
                    "tone": tone,
                    **summarize_native(rr),
                    "high_concentration": summarize_native(high),
                    "high_concentration_ids": [r["id"] for r in high],
                }
            )
    save_table("native-correlations", correlations)
    save_table("native-bins", bins)
    save_table("per-tone-summary", per_tone)
    concentration = []
    for h in HEADS:
        for high in (False, True):
            group = [
                r
                for r in native
                if r["head"] == h and (r["removed_weight_share"] >= topcut) == high
            ]
            concentration.append(
                {
                    "head": h,
                    "top_decile": high,
                    "descriptive_cut": topcut,
                    **summarize_native(group),
                }
            )
    save_table("concentration-legitimacy", concentration)
    raw = {r["example_id"]: r for r in read_json(EVIDENCE / "raw.json")}
    deterministic = {r["example_id"]: r for r in read_json(EVIDENCE / "output.json")}
    gate = read_json(GATE)
    assert not gate["confirmatory_model_evaluation_permitted"]
    learner, evidence, geometry = [], [], []
    for i in selection["learner_base_usable_ids"]:
        b, rr = reps[i, ARM, "BASE"], reps[i, ARM, RIGHT]
        w = np.array(b["normalized_weights"])
        a, end = b["ownership_span"]
        e = independent_evidence(raw[i], deterministic[i])
        assert [raw[i]["start"], raw[i]["end"]] == b["ownership_span"]
        p = {h: preds[i, ARM, "BASE", h] for h in HEADS}
        disagreement = i in selection["learner_disagreements"]
        outcome = "unresolved"
        if e["quality"] in ("STRONG", "MODERATE") and e["usable_family"]:
            favored = [h for h in HEADS if p[h]["prediction"] == e["usable_family"]]
            outcome = "both" if len(favored) == 2 else favored[0] if favored else "neither"
        evidence.append({**e, "disagreement": disagreement, "head_comparison": outcome})
        structural = {
            "id": i,
            "disagreement": disagreement,
            "frame_count": b["frame_count"],
            "support_ms": b["support_ms"],
            "effective_n": b["effective_n"],
            "effective_n_fraction": b["effective_n"] / b["frame_count"],
            "max_weight_share": float(w.max()),
            "first_weight_share": float(w[0]),
            "right_weight_share": float(w[-1]),
            "final_quarter_share": float(
                w[np.array(b["frame_centers"]) >= a + 0.75 * (end - a)].sum()
            ),
            "right_admissible": rr["pooled_vector"] is not None,
            "expanded_prediction": p["expanded"]["prediction"],
            "pilot_prediction": p["pilot"]["prediction"],
            "pair": p["expanded"]["prediction"] + "/" + p["pilot"]["prediction"],
        }
        for h in HEADS:
            for state in ("CONTRACT_LEFT", RIGHT):
                q = preds.get((i, ARM, state, h))
                structural[h + "_" + state + "_tv"] = (
                    float(np.abs(np.array(p[h]["probabilities"]) - q["probabilities"]).sum() / 2)
                    if q
                    else None
                )
                structural[h + "_" + state + "_flip"] = (
                    p[h]["prediction"] != q["prediction"] if q else None
                )
        learner.append(structural)
        pooled = np.array(b["pooled_vector"])
        pair = [CLASSES.index(p[h]["prediction"]) for h in HEADS]
        directions = []
        for h in HEADS:
            mu, _scale, _coef, bias, weights = affine_head(models[h])
            direction = weights[pair[0]] - weights[pair[1]]
            offset = float(bias[pair[0]] - bias[pair[1]] - direction @ mu)
            directions.append(direction)
            z = np.array(p[h]["logits"])
            np.testing.assert_allclose(
                pooled @ direction + offset, z[pair[0]] - z[pair[1]], atol=1e-11
            )
            scores, f_bias, _, _ = frame_scores(
                np.load(b["hidden_path"])[b["frame_ids"]], models[h]
            )
            np.testing.assert_allclose(w @ scores + f_bias, z, atol=1e-11)
            geometry.append(
                {
                    "id": i,
                    "disagreement": disagreement,
                    "head": h,
                    "prediction": p[h]["prediction"],
                    "probabilities": p[h]["probabilities"],
                    "logits": p[h]["logits"],
                    "probability_margin": p[h]["probability_margin"],
                    "logit_margin": p[h]["logit_margin"],
                    "margin_category": margin_category(p[h]["probability_margin"]),
                    "pooled_embedding": pooled.tolist(),
                    "pair_orientation": [CLASSES[j] for j in pair],
                    "margin_direction_raw": direction.tolist(),
                    "margin_offset_raw": offset,
                    "pair_margin": float(z[pair[0]] - z[pair[1]]),
                    "frame_pair_contributions": (
                        w * (scores[:, pair[0]] - scores[:, pair[1]])
                    ).tolist(),
                    "pair_bias": float(f_bias[pair[0]] - f_bias[pair[1]]),
                }
            )
        structural["pair_direction_cosine"] = (
            float(
                directions[0]
                @ directions[1]
                / (np.linalg.norm(directions[0]) * np.linalg.norm(directions[1]))
            )
            if disagreement
            else None
        )
        structural["margin_categories"] = "/".join(
            margin_category(p[h]["probability_margin"]) for h in HEADS
        )
    save_table("learner-structure", learner)
    save_table("independent-evidence", evidence)
    save_table("classifier-margins", geometry)
    group_summaries = []
    for disagreement in (False, True):
        group = [r for r in learner if r["disagreement"] == disagreement]
        group_summaries.append(
            {
                "disagreement": disagreement,
                "n": len(group),
                **{
                    k: describe([r[k] for r in group])
                    for k in (
                        "frame_count",
                        "support_ms",
                        "effective_n",
                        "effective_n_fraction",
                        "max_weight_share",
                        "first_weight_share",
                        "right_weight_share",
                        "final_quarter_share",
                    )
                },
            }
        )
    save_table("learner-group-comparison", group_summaries)
    learner_corr = [
        {
            "feature": k,
            "spearman_with_disagreement": float(
                spearmanr([r[k] for r in learner], [r["disagreement"] for r in learner]).statistic
            ),
        }
        for k in (
            "effective_n",
            "effective_n_fraction",
            "max_weight_share",
            "right_weight_share",
            "final_quarter_share",
        )
    ]
    pairs = []
    for dataset in ("native", "learner_primary"):
        for arm in ("UNIFORM_SAFE_OWNER", ARM):
            ids = sorted(
                {
                    i
                    for (i, a, s, h), p in preds.items()
                    if a == arm and s == "BASE" and h == "expanded" and p["dataset"] == dataset
                }
            )
            counts = Counter(
                preds[i, arm, "BASE", "expanded"]["prediction"]
                + "/"
                + preds[i, arm, "BASE", "pilot"]["prediction"]
                for i in ids
                if preds[i, arm, "BASE", "expanded"]["prediction"]
                != preds[i, arm, "BASE", "pilot"]["prediction"]
            )
            pairs.append(
                {
                    "dataset": dataset,
                    "arm": arm,
                    "n": len(ids),
                    "disagreements": sum(counts.values()),
                    "pairs": dict(sorted(counts.items())),
                }
            )
    save_table("class-pair-summary", pairs)
    write_json(
        OUT / "cross-synthesis.json",
        {
            "learner_structure_correlations": learner_corr,
            "evidence_quality_disagreements": {
                k: sum(e["quality"] == k and e["disagreement"] for e in evidence)
                for k in ("STRONG", "MODERATE", "WEAK", "UNAVAILABLE")
            },
            "independent_head_outcomes": dict(
                Counter(e["head_comparison"] for e in evidence if e["disagreement"])
            ),
            "learner_margin_categories": dict(
                Counter(r["margin_categories"] for r in learner if r["disagreement"])
            ),
            "native_reconstruction_max_absolute_error": max(reconstruction),
            "native_count": 659,
            "native_detailed_items": len(detailed),
            "failed_solo_gate": gate,
            "no_reliable_listener_realization_reference_found": True,
            "eligibility_schema_note": (
                "The preregistered term eligible means the frozen schema state "
                "sufficient; no rule or threshold changed."
            ),
            "summary_digest": digest(
                {"native": native, "learner": learner, "evidence": evidence, "pairs": pairs}
            ),
        },
    )
    print("Analysis complete; cached artifacts only, no encoder inference or fitting.")


def verify():
    before = read_json(OUT / "freeze-before.json")
    # Finish request explicitly prohibits another full freeze scan.
    models = read_json(LOCK)["model_method"]["models"]
    paths = [
        PRIOR / name
        for name in (
            "representation-manifest.json",
            "representation-manifest-seal.json",
            "predictions.json",
            "preregistration.json",
            "preregistration-seal.json",
        )
    ]
    paths += [Path(m["path"]) for m in models.values()]
    paths += [LOCK, GATE, EVIDENCE / "raw.json", EVIDENCE / "output.json"]
    paths += [
        PACKAGE / "perceptual_tone" / name
        for name in ("pooling_representation.py", "pooling_confirmatory.py", "frame_attribution.py")
    ]
    checked = {str(p.relative_to(ROOT)): file_hash(p) for p in paths}
    changed = [p for p, h in checked.items() if before["files"][p] != h]
    assert not changed, changed
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    assert head == before["git_head"]
    assert (
        file_hash(OUT / "selection.json")
        == read_json(OUT / "audit-preregistration.json")["selection_sha256"]
    )
    write_json(
        OUT / "freeze-verification.json",
        {
            "unchanged_files_checked": len(checked),
            "checked_files": checked,
            "full_scan_repeated": False,
            "initial_freeze_inventory_count": len(before["files"]),
            "changed_files": changed,
            "git_head_unchanged": True,
            "manifest_sha256": file_hash(PRIOR / "representation-manifest.json"),
            "head_sha256": {h: file_hash(m["path"]) for h, m in models.items()},
            "selection_sha256": file_hash(OUT / "selection.json"),
            "pooling_source_sha256": file_hash(
                PACKAGE / "perceptual_tone/pooling_representation.py"
            ),
        },
    )
    print("Verified unchanged:", len(checked), "targeted pre-existing files; no full rescan")


def finish():
    """Cheap additive summaries from persisted audit tables and sealed outputs only."""
    native = read_json(OUT / "native-right-all.json")
    learner = read_json(OUT / "learner-structure.json")
    selection = read_json(OUT / "selection.json")
    plan = read_json(OUT / "audit-preregistration.json")
    assert file_hash(OUT / "selection.json") == plan["selection_sha256"]
    reps, preds = load_sealed()
    topcut = read_json(OUT / "concentration-legitimacy.json")[0]["descriptive_cut"]

    def rates(rows):
        n = len(rows)
        return {
            **summarize_native(rows),
            "flip_rate": sum(r["flip"] for r in rows) / n if n else None,
            "base_accuracy": sum(r["base_correct"] for r in rows) / n if n else None,
            "right_accuracy": sum(r["right_correct"] for r in rows) / n if n else None,
            **{
                k: describe([r[k] for r in rows])
                for k in (
                    "base_logit_margin",
                    "base_probability_margin",
                    "remaining_frames",
                    "support_after_ms",
                    "removed_rms",
                    "removed_high_band_fraction",
                    "removed_margin_contribution",
                    "label_margin_edge_effect",
                )
            },
        }

    bins, joint, stable = [], [], []
    for h in HEADS:
        group = [r for r in native if r["head"] == h]
        for lo, hi in zip(
            plan["bins"]["removed_weight_share"][:-1],
            plan["bins"]["removed_weight_share"][1:],
            strict=True,
        ):
            bins.append(
                {
                    "head": h,
                    "weight_lower": lo,
                    "weight_upper": hi,
                    **rates([r for r in group if lo <= r["removed_weight_share"] < hi]),
                }
            )
        for high in (False, True):
            for margin in ("low", "intermediate", "confident"):
                joint.append(
                    {
                        "head": h,
                        "top_decile_concentration": high,
                        "margin_category": margin,
                        **rates(
                            [
                                r
                                for r in group
                                if (r["removed_weight_share"] >= topcut) == high
                                and r["starting_margin_category"] == margin
                            ]
                        ),
                    }
                )
        for status in ("stable_correct", "flip", "other_no_flip"):
            rr = [
                r
                for r in group
                if r["removed_weight_share"] >= topcut
                and (
                    "flip"
                    if r["flip"]
                    else "stable_correct"
                    if r["base_correct"] and r["tv"] <= 0.02
                    else "other_no_flip"
                )
                == status
            ]
            stable.append(
                {
                    "head": h,
                    "status": status,
                    "descriptive_top_decile": topcut,
                    "ids": [r["id"] for r in rr],
                    **rates(rr),
                }
            )
    save_table("weight-bins-complete", bins)
    save_table("concentration-margin-joint", joint)
    save_table("high-weight-stable-vs-flip", stable)
    extra = []
    for h in HEADS:
        rr = [r for r in native if r["head"] == h]
        for f in ("remaining_frames", "support_after_ms"):
            for outcome in ("tv", "flip"):
                extra.append(
                    {
                        "head": h,
                        "feature": f,
                        "outcome": outcome,
                        "spearman": float(
                            spearmanr([r[f] for r in rr], [r[outcome] for r in rr]).statistic
                        ),
                        "pearson": float(
                            np.corrcoef([r[f] for r in rr], [r[outcome] for r in rr])[0, 1]
                        ),
                    }
                )
    save_table("remaining-support-correlations", extra)
    for r in learner:
        b = reps[r["id"], ARM, "BASE"]
        w = np.array(b["normalized_weights"])
        r.update(
            weight_entropy_nats=float(-np.sum(w[w > 0] * np.log(w[w > 0]))),
            normalized_entropy=float(-np.sum(w[w > 0] * np.log(w[w > 0])) / np.log(len(w))),
            pooled_embedding_norm=float(np.linalg.norm(b["pooled_vector"])),
        )
        for h in HEADS:
            p = preds[r["id"], ARM, "BASE", h]
            for k in (
                "l2_to_reference",
                "cosine_to_reference",
                "standardized_distance_to_reference",
                "standardized_norm",
                "distance_to_training_mean",
            ):
                r[h + "_" + k] = p[k]
    save_table("learner-structure-extended", learner)
    fields = (
        "effective_n",
        "effective_n_fraction",
        "max_weight_share",
        "first_weight_share",
        "right_weight_share",
        "final_quarter_share",
        "frame_count",
        "support_ms",
        "weight_entropy_nats",
        "normalized_entropy",
        "pooled_embedding_norm",
        "expanded_l2_to_reference",
        "expanded_cosine_to_reference",
        "expanded_standardized_distance_to_reference",
        "pilot_standardized_distance_to_reference",
        "expanded_distance_to_training_mean",
        "pilot_distance_to_training_mean",
    )
    comparison = [
        {
            "disagreement": flag,
            **{k: describe([r[k] for r in learner if r["disagreement"] == flag]) for k in fields},
        }
        for flag in (False, True)
    ]
    save_table("learner-group-comparison-extended", comparison)
    llookup = {r["id"]: r for r in learner}
    matched = [
        {
            **m,
            "disagreement_minus_control": {
                k: llookup[m["case"]][k] - llookup[m["control"]][k] for k in fields
            },
        }
        for m in selection["learner_controls"]
    ]
    save_table("learner-matched-differences", matched)
    patterns, pair_geometry, stability = [], [], []
    for dataset in ("native", "learner_primary"):
        ids = sorted(
            {
                i
                for (i, a, s, h), p in preds.items()
                if a == ARM and s == "BASE" and h == "expanded" and p["dataset"] == dataset
            }
        )
        for i in ids:
            p, q = [preds[i, ARM, "BASE", h] for h in HEADS]
            if p["prediction"] != q["prediction"]:
                pattern = "/".join(margin_category(x["probability_margin"]) for x in (p, q))
                pair_geometry.append(
                    {
                        "id": i,
                        "dataset": dataset,
                        "pair": p["prediction"] + "/" + q["prediction"],
                        "pattern": pattern,
                        "expanded_probability_margin": p["probability_margin"],
                        "pilot_probability_margin": q["probability_margin"],
                        "expanded_logit_margin": p["logit_margin"],
                        "pilot_logit_margin": q["logit_margin"],
                    }
                )
        patterns.append(
            {
                "dataset": dataset,
                "n": len(ids),
                "patterns": dict(
                    Counter(r["pattern"] for r in pair_geometry if r["dataset"] == dataset)
                ),
            }
        )
    for h in HEADS:
        for state in ("CONTRACT_LEFT", RIGHT):
            for disagree in (None, False, True):
                ids = [
                    i
                    for i in selection["learner_base_usable_ids"]
                    if (i, ARM, state, h) in preds
                    and (disagree is None or (i in selection["learner_disagreements"]) == disagree)
                ]
                stability.append(
                    {
                        "head": h,
                        "state": state,
                        "disagreement": disagree,
                        "n": len(ids),
                        "flips": sum(
                            preds[i, ARM, "BASE", h]["prediction"]
                            != preds[i, ARM, state, h]["prediction"]
                            for i in ids
                        ),
                    }
                )
    save_table("native-learner-margin-patterns", patterns)
    save_table("native-learner-disagreement-geometry", pair_geometry)
    save_table("learner-stability", stability)
    # Sensitivity analysis retains every original ID; this is an explicitly labeled stratum.
    eligible = [r for r in learner if r["right_admissible"]]
    save_table(
        "learner-admissible-stratum",
        [
            {
                "disagreement": flag,
                "n": sum(r["disagreement"] == flag for r in eligible),
                **{
                    k: describe([r[k] for r in eligible if r["disagreement"] == flag])
                    for k in fields
                },
            }
            for flag in (False, True)
        ],
    )
    print("Cheap finishing summaries complete; case sets unchanged.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["seal", "analyze", "finish", "verify"])
    stage = parser.parse_args().stage
    {"seal": seal, "analyze": analyze, "finish": finish, "verify": verify}[stage]()


if __name__ == "__main__":
    main()
