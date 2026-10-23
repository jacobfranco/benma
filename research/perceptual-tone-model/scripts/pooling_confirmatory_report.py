"""Render sealed confirmatory results and descriptive audit tables, without inference."""
# Long report prose and mathematical symbols are intentional.
# ruff: noqa: E501, RUF001

import csv
import json

import numpy as np
from perceptual_tone.common import PACKAGE, file_hash, read_json, write_json
from perceptual_tone.pooling_analysis import CASE_GROUPS
from perceptual_tone.pooling_confirmatory import ARMS, OUT, STATES
from perceptual_tone.pooling_confirmatory_analysis import describe

REPORT = PACKAGE / "pooling-confirmatory-report.md"
SHORT = {
    ARMS[0]: "Uniform",
    ARMS[1]: "Acoustic",
    "CURRENT_REFERENCE": "Reference",
    "BASE": "BASE",
    "CONTRACT_LEFT": "LEFT",
    "CONTRACT_RIGHT": "RIGHT",
}


def pct(x):
    return f"{100 * x:.2f}%"


def num(x):
    return f"{x:.4f}"


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *["| " + " | ".join(str(v) for v in r) + " |" for r in rows],
            ]
        )
        + "\n\n"
    )


def correlation(a, b):
    return (
        float(np.corrcoef(a, b)[0, 1]) if len(a) > 1 and np.std(a) > 0 and np.std(b) > 0 else None
    )


def run():
    s = read_json(OUT / "analysis-summary.json")
    manifest = read_json(OUT / "representation-manifest.json")
    seal = read_json(OUT / "representation-manifest-seal.json")
    start = read_json(OUT / "inference-start.json")
    freeze = read_json(OUT / "freeze-after.json")
    predictions = read_json(OUT / "predictions.json")["rows"]
    reps = {(r["id"], r["arm"], r["perturbation"]): r for r in manifest["records"]}
    outputs = {(r["id"], r["arm"], r["perturbation"], r["head"]): r for r in predictions}
    with (OUT / "perturbation-item-pairs.csv").open() as f:
        pairs = list(csv.DictReader(f))
    with (OUT / "uniform-acoustic-item-pairs.csv").open() as f:
        arm_pairs = list(csv.DictReader(f))
    with (OUT / "expanded-pilot-item-pairs.csv").open() as f:
        head_pairs = list(csv.DictReader(f))
    datasets = sorted({r["dataset"] for r in pairs})
    arm_tv, paired_heads, correlations, masses = [], [], [], []
    for d in datasets:
        for h in ("expanded", "pilot"):
            for state in STATES:
                rr = [
                    r
                    for r in arm_pairs
                    if (r["dataset"], r["head"], r["perturbation"]) == (d, h, state)
                ]
                arm_tv.append(
                    dict(
                        dataset=d,
                        head=h,
                        perturbation=state,
                        tv=describe([float(r["tv"]) for r in rr]),
                    )
                )
            for state in STATES[1:]:
                u = {
                    r["id"]: r
                    for r in pairs
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                    == (d, h, ARMS[0], state)
                }
                a = {
                    r["id"]: r
                    for r in pairs
                    if (r["dataset"], r["head"], r["arm"], r["perturbation"])
                    == (d, h, ARMS[1], state)
                }
                ids = sorted(a.keys() & u.keys())
                delta = [float(a[i]["tv"]) - float(u[i]["tv"]) for i in ids]
                high = [float(a[i]["removed_high_band_fraction"]) for i in ids]
                relative_rms = [
                    float(a[i]["removed_rms"])
                    / np.mean(reps[i, ARMS[1], "BASE"]["acoustic_audit"]["rms_20ms"])
                    for i in ids
                ]
                correlations.append(
                    dict(
                        dataset=d,
                        head=h,
                        perturbation=state,
                        n=len(ids),
                        high_band_vs_tv_delta=correlation(high, delta),
                        relative_rms_vs_tv_delta=correlation(relative_rms, delta),
                        caveat="Continuous descriptive associations, no causal frication label or threshold.",
                    )
                )
        for a in ARMS:
            base = {
                r["id"]: r
                for r in head_pairs
                if (r["dataset"], r["arm"], r["perturbation"]) == (d, a, "BASE")
            }
            for state in STATES[1:]:
                contracted = {
                    r["id"]: r
                    for r in head_pairs
                    if (r["dataset"], r["arm"], r["perturbation"]) == (d, a, state)
                }
                ids = sorted(base.keys() & contracted.keys())
                agree0 = sum(base[i]["agree"] == "True" for i in ids)
                agree1 = sum(contracted[i]["agree"] == "True" for i in ids)
                paired_heads.append(
                    dict(
                        dataset=d,
                        arm=a,
                        perturbation=state,
                        n=len(ids),
                        base_agree=agree0,
                        contract_agree=agree1,
                        agreement_delta=(agree1 - agree0) / len(ids),
                    )
                )
    for i, groups in CASE_GROUPS.items():
        for a in ARMS:
            for state in STATES:
                r = reps[i, a, state]
                weights = dict(zip(r["frame_ids"], r["normalized_weights"], strict=True))
                for region, ids in groups.items():
                    masses.append(
                        dict(
                            id=i,
                            arm=a,
                            perturbation=state,
                            region=region,
                            weight_mass=sum(weights.get(j, 0) for j in ids),
                        )
                    )
    extremes = sorted(
        [r for r in pairs if r["dataset"] == "native" and r["arm"] == ARMS[1]],
        key=lambda r: float(r["tv"]),
        reverse=True,
    )[:10]
    supplemental = dict(
        uniform_acoustic_tv=arm_tv,
        paired_head_agreement=paired_heads,
        edge_correlations=correlations,
        original_attribution_region_masses=masses,
        largest_native_tv_cases=extremes,
    )
    write_json(OUT / "descriptive-audit.json", supplemental)
    decision = dict(
        decision="PROMISING_NOT_READY",
        full_decision="ACOUSTIC_WEIGHTING PROMISING BUT NOT YET READY",
        dev_integration="NOT READY",
        head_only_refit_justified=False,
        reasons=[
            "Independent native accuracy and average stability improve.",
            "Expanded right-edge tail includes TV 0.838 and 0.557; right-edge cosine is slightly worse than uniform.",
            "Natural learner head agreement falls from 9/14 to 7/14; stable predictions are not independently verified realizations.",
            "Frication-related head disagreement survives both contractions; no evidence it is solely a frozen-head mismatch.",
        ],
        next_step="Preregister a bounded offline audit of the already-sealed largest right-edge changes and disjoint learner head disagreements, inspect frozen audio/boundaries and existing frame/logit contributions, and establish independent realization evidence before deciding whether a head-only refit addresses the blocker. Keep representation and heads frozen; no product integration.",
    )
    write_json(OUT / "decision.json", decision)
    text = [
        "# Confirmatory pooling generalization and perturbation stability replay\n\n",
        "**PROMISING_NOT_READY — ACOUSTIC_WEIGHTING PROMISING BUT NOT YET READY. NOT READY for dev integration.**\n\n",
        "Independent native recognition and mean perturbation stability reproduce the acoustic advantage. This is not full confirmation for integration: concentrated right-edge failures, residual physical frication disagreement, and worse head agreement on the small independent natural learner set remain unresolved. No head-only refit is justified yet.\n\n",
        "## Frozen scope and dataset composition\n\n",
        "All **659** remaining eligible test IDs are included, without resampling: the exact 915-ID eligible frozen release minus the prior sealed 256. The intersection is empty and the union recovers all 915. The 659 units cover **12 held-out speakers**, disjoint from both heads' training speakers; tone counts are **T1 154, T2 139, T3 103, T4 263**. 'Independent' here means excluded from the 256-item pooling control, not never used in the historical frozen-head test evaluation. Speakers and recordings can overlap the earlier test subset; this is item-disjoint confirmation, not a new speaker cohort.\n\n",
        "Also replayed: the original **20 physical units** (three learner takes plus Google playback) and **27 disjoint frozen learner units**: 16 accepted natural units from S01/S02/S03 and 11 accepted diagnostic units from S13 and the documented U-shape recording. All five learner source recordings have decoded PCM identities disjoint from the four physical recordings. Selection uses existing accepted provenance and boundaries, never expected tones, grades, characters, outputs, or acoustic outcomes. Unknown-provenance and quarantined units remain excluded. No learner realized-tone gold exists; no learner accuracy is computed.\n\n",
        "The release contains additional unknown-provenance accepted material; it was not promoted into a new learner benchmark. The existing accepted natural/diagnostic strata are sufficient disjoint material. Exact IDs, source references, PCM hashes and exclusion proof are in `native-ids.json`, `prior-256-exclusion-proof.json`, and `disjoint-learner-ids.json`.\n\n",
        "## Exact unchanged definitions and perturbations\n\n",
        "UNIFORM_SAFE_OWNER takes the float64 uniform mean of every eligible encoder frame in the frozen owner. ACOUSTIC_WEIGHTED uses **RMS_i × (1 − high_band_fraction_i)**: uncentered 20 ms RMS; demeaned 20 ms symmetric Hann FFT; power at **≥3.4 kHz** divided by `max(total_power, 1e-24)`; 5 ms acoustic hop; nearest absolute timestamp mapping, earlier timestamp on ties. Negative RMS is clamped to zero and spectral fraction to [0,1], as in the sealed original. Weights normalize in float64 by their sum; sum ≤ float64.tiny abstains. No new exponent, floor, fallback, threshold, or effective-support rule. The original source file is byte-identical and is called directly.\n\n",
        "BASE retains the eligible sequence. CONTRACT_LEFT removes exactly its first frame; CONTRACT_RIGHT removes exactly its last. A candidate needs ≥3 frames and ≥60 ms of contiguous frame-cell support clipped to the **unchanged owner boundaries**, with the original 1e-9-second arithmetic tolerance. Failed contractions are persisted as `perturbation_not_admissible`, without a vector. Kish effective_n = 1/sum(w²) is descriptive only. No spans expand, shift or change ownership. Physical ownership is the persisted GAP_AWARE result; native and accepted learner ownership use frozen MFA read units. Ambiguous take-2 买 remains ownership-abstained in all six conditions.\n\n",
        "Only these two arms and three variants are candidates. CURRENT_REFERENCE is an unperturbed historical comparator: exact archived native layer-9 nucleus-coda vectors, or the existing physical/learner reference span in the same context. CENTRAL_HALF is excluded. HuBERT layer 9, audio normalization, 200-sample padding, head standardization, class mapping, weights and biases remain frozen. Pre-existing neutral compatibility is applied only after representation sealing; it never changes frame selection.\n\n",
        "## Seal and chronology\n\n",
        f"Manifest SHA-256: **`{seal['sha256']}`**.\n\n",
        f"Preregistration sealed at `{read_json(OUT / 'preregistration-seal.json')['sealed_at']}`; **{seal['row_count']}** manifest rows sealed at `{seal['sealed_at']}`; inference-start recorded at `{start['started_at']}` immediately before loading either classifier. The manifest contains 706 × 2 × 3 = 4,236 candidate records plus 699 historical references. It embeds pooled vectors and records IDs, dataset, speaker, native evaluation label, frozen owners/status, eligible and selected frame IDs/centers, RMS, high-band fractions, raw/normalized weights, support, effective_n and abstention reasons. Hidden artifacts and the complete manifest are hashed. Raw logits and probabilities are persisted.\n\n",
        f"All vectors and the manifest were reconstructed and verified before inference. Native re-extracted reference vectors match the frozen archive within **{manifest['native_reference_max_reextraction_error']:.3g}** absolute coordinate error; inference uses the exact archived reference vectors. This is float64 mean versus archived float32 mean, not an encoder change.\n\n",
        "## Coverage\n\n",
        table(
            [
                "Dataset",
                "Arm",
                "Variant",
                "Intended",
                "Representable",
                "Head usable",
                "Abstention reasons",
            ],
            [
                [
                    r["dataset"],
                    SHORT[r["arm"]],
                    SHORT[r["perturbation"]],
                    r["intended"],
                    r["usable"],
                    r["head_usable"],
                    json.dumps(r["reasons"]),
                ]
                for r in s["coverage"]
                if r["arm"] != "CURRENT_REFERENCE"
            ],
        ),
        "Every native condition covers **659/659**; every native comparison therefore uses all 659 paired items. Physical coverage is 19/20 representations, 15/20 four-class outputs after four neutral exclusions. Learner natural coverage is 15/16 BASE and 14/16 contracted representations; head denominators are 14 and 13 after one neutral exclusion. One natural item fails BASE support, and two fail each contraction (including that item). Diagnostic learner coverage is 11/11 throughout. Failures remain in coverage and manifests.\n\n",
        "## Native performance, every condition\n\n",
        "Percentages below are on usable items. All denominators are 659; all-selected and mutually covered metrics coincide.\n\n",
        table(
            [
                "Head",
                "Arm",
                "Variant",
                "n",
                "Accuracy",
                "Balanced acc.",
                "Macro F1",
                "T1 recall",
                "T2 recall",
                "T3 recall",
                "T4 recall",
            ],
            [
                [
                    r["head"],
                    SHORT[r["arm"]],
                    SHORT[r["perturbation"]],
                    r["covered"],
                    *[pct(r[k]) for k in ("accuracy", "balanced_accuracy", "macro_f1")],
                    *[pct(r["per_tone"][t]["recall"]) for t in ("T1", "T2", "T3", "T4")],
                ]
                for r in s["native_metrics"]
            ],
        ),
        "BASE acoustic is 602/659 correct under each head, versus uniform 585/659 expanded and 586/659 pilot; reference is 594/659 expanded and 589/659 pilot. Acoustic minus uniform is **+2.58 pp expanded, +2.43 pp pilot**; acoustic minus reference is **+1.21 pp expanded, +1.97 pp pilot**.\n\n",
        "The preregistered 10,000-replicate paired speaker-cluster bootstrap (seed 20261022) gives 95% percentile intervals of **[+1.24,+3.94] pp expanded** and **[+1.32,+3.63] pp pilot** for acoustic minus uniform. Paired acoustic-only/uniform-only correct counts are **22/5** and **21/5**. Against reference, acoustic-only/reference-only counts are **17/9** and **20/7**; intervals are **[−0.16,+2.44] pp** and **[+0.29,+4.05] pp**. These 12-speaker descriptive intervals support reproducibility of the direction, not proof of equivalence, population-wide superiority, or perceptual correctness. No significance search or numerical readiness threshold was introduced.\n\n",
        "BASE acoustic-minus-uniform recall changes (T1/T2/T3/T4) are **+7.14/−1.44/+3.88/+1.52 pp expanded** and **+7.14/+0.72/+2.91/+0.38 pp pilot**. Expanded T2 loses a net two correct items out of 139; this deserves visibility despite the overall gain. Against reference, pilot T3 loses two correct items out of 103 (−1.94 pp), while expanded T3 is unchanged. The sample cannot establish absence of a small tone-specific regression. Full pairwise balanced-accuracy, F1, recalls, counts and IDs are in `paired-native-metrics.json`.\n\n",
        "Confusion matrices use true rows and predicted columns in T1/T2/T3/T4 order:\n\n",
        table(
            ["Head", "Arm", "Variant", "Confusion matrix"],
            [
                [r["head"], SHORT[r["arm"]], SHORT[r["perturbation"]], json.dumps(r["confusion"])]
                for r in s["native_metrics"]
            ],
        ),
        "## Perturbation stability\n\n",
        "Each comparison uses only items usable in BASE and the indicated contraction. TV is half the L1 probability difference (0–1 scale); margins are top-one minus top-two. All margin changes are contraction minus BASE.\n\n",
        table(
            [
                "Dataset",
                "Head",
                "Arm",
                "Edge",
                "n",
                "Agreement",
                "Flips",
                "TV mean",
                "TV median",
                "TV max",
                "Embedding cosine mean",
                "L2 mean",
                "Probability margin Δ",
                "Logit margin Δ",
            ],
            [
                [
                    r["dataset"],
                    r["head"],
                    SHORT[r["arm"]],
                    SHORT[r["perturbation"]],
                    r["n"],
                    pct(r["agreement"]),
                    r["flips"],
                    num(r["tv"]["mean"]),
                    num(r["tv"]["median"]),
                    num(r["tv"]["max"]),
                    num(r["embedding_cosine"]["mean"]),
                    num(r["embedding_l2"]["mean"]),
                    num(r["probability_margin_change"]["mean"]),
                    num(r["logit_margin_change"]["mean"]),
                ]
                for r in s["stability"]
            ],
        ),
        "Native acoustic weighting lowers mean TV in all four head/edge comparisons and lowers TV on **551/659 expanded-left, 546/659 expanded-right, 538/659 pilot-left, 515/659 pilot-right** items. Left flips fall **21→5 expanded, 11→6 pilot**; right flips fall **15→14 expanded, 9→7 pilot**. Embedding stability improves clearly on the left. On the right, acoustic mean cosine is **0.99169 versus uniform 0.99275**, despite slightly lower mean L2 and lower mean probability TV. Thus average probability stability is better, but the representation is not uniformly less boundary-sensitive.\n\n",
        "## Per-tone perturbation stability\n\n",
        table(
            [
                "Head",
                "Arm",
                "Edge",
                "Tone",
                "Admissible n",
                "Agreement",
                "Flips",
                "Mean TV",
                "Recall Δ pp",
            ],
            [
                [
                    r["head"],
                    SHORT[r["arm"]],
                    SHORT[r["perturbation"]],
                    r["tone"],
                    r["n"],
                    pct(r["agreement"]),
                    r["flips"],
                    num(r["tv"]["mean"]),
                    f"{100 * r['recall_change']:+.2f}",
                ]
                for r in s["per_tone_stability"]
            ],
        ),
        "Mean acoustic TV is lower than uniform in every native tone/head/edge cell. Flip counts do not improve in every cell: expanded-right T2/T3 have 3/4 acoustic flips versus 2/3 uniform; pilot-left T4 has 3 versus 2; pilot-right T2 has 3 versus 1. Expanded acoustic RIGHT lowers T1/T3/T4 recall by **1.30/1.94/1.52 pp** and raises T2 by 2.16 pp. These small counts and the worst-case tail prevent a blanket robustness claim.\n\n",
        "## Left versus right, quiet tails and frication\n\n",
        "There is no universal dominant edge under uniform: expanded mean TV is slightly higher at the right, pilot at the left; physical cases are more sensitive at the left. Under acoustic weighting, expanded native right mean TV is **0.02078 versus left 0.01443** (44% higher), while pilot edges are similar (**0.01762 right, 0.01792 left**). Acoustic's reduction is larger at the left: **35.6% expanded / 37.7% pilot**, versus **12.8% / 22.0%** at the right. This is aggregate evidence for reduced onset influence, not proof that every removed frame is pre-vowel.\n\n",
        "Quiet-tail suppression is reproduced in take-3 买 and improves average native right sensitivity. However, a loud low-high-band edge can receive a large normalized acoustic weight. For **aishell3:SSB03540048:0 (T3)** the last frame carries **42.23%** of acoustic weight versus uniform 14.29%; removing it gives expanded **TV 0.83816**, versus uniform **0.17960**, and a correct-to-incorrect flip. Six frames and 119.97 ms remain: it is fully admissible, with effective_n 3.806 after contraction. This is not a hidden support failure. Two further expanded-right examples reach TV 0.55673 and 0.43391. The raw RMS and high-band fraction identify these as energetic, low-high-band edges, not quiet tails or evidence that a new effective_n threshold would solve the issue.\n\n",
        "Frication remains unresolved: the take-3 想 high-band region spans multiple frames; a one-frame contraction leaves much of it and expanded/pilot T2/T1 disagreement survives both edges. The native worst right-edge events have very low high-band fractions, so frication is not the only source of instability. Continuous edge RMS/high-band versus TV-delta correlations and original-region weight masses are saved in `descriptive-audit.json`; these are descriptive acoustic proxies, not independent phonetic labels. Across the 659 native pairs, the correlation of relative edge RMS with acoustic-minus-uniform TV is +0.319/+0.231 expanded left/right and +0.499/+0.382 pilot; corresponding high-band correlations are weakly negative (-0.015/-0.027 and -0.110/-0.067). These associations support an energetic-edge concentration concern without assigning phonetic causes. In take-3 想 the originally identified strong-frication region retains 15.36% acoustic weight after LEFT (18.31% BASE), so its influence is broader than the single removed frame. No population-wide frication cure can be inferred from average stability.\n\n",
        "## Six interpretation checks\n\n",
    ]
    cases = read_json(OUT / "six-diagnostic-cases.json")
    text.append(
        table(
            ["Case", "Arm", "Head", "BASE→LEFT→RIGHT", "Left TV", "Right TV"],
            [
                [
                    c["display"],
                    SHORT[a],
                    h,
                    " → ".join(outputs[c["id"], a, state, h]["prediction"] for state in STATES),
                    num(
                        next(
                            r["tv"]
                            for r in c["perturbations"]
                            if (r["arm"], r["head"], r["perturbation"]) == (a, h, STATES[1])
                        )
                    ),
                    num(
                        next(
                            r["tv"]
                            for r in c["perturbations"]
                            if (r["arm"], r["head"], r["perturbation"]) == (a, h, STATES[2])
                        )
                    ),
                ]
                for c in cases
                for a in ARMS
                for h in ("expanded", "pilot")
            ],
        )
    )
    text.extend(
        [
            "Take-1 这: left removal flips expanded uniform T2→T4; acoustic remains T3, with T3/T2 head disagreement. Take-2 这: expanded uniform flips T4→T3; acoustic left TV falls 0.19058→0.01067 and both acoustic heads stay T3. Take-3 想: no flips, but T2/T1 head disagreement persists and contraction does not remove the broader frication region. Take-3 买: right TV falls 0.02536→0.01118 expanded and 0.01137→0.00343 pilot; acoustic heads stay T3. Google 买: all six variants remain usable without F0 and both heads stay T3. Take-3 我: all variants retain expanded T2/pilot T3; neither is declared correct. These checks corroborate the previous attribution patterns without tuning.\n\n",
            "## Expanded/pilot agreement\n\n",
            table(
                ["Dataset", "Arm", "Variant", "n", "Agreement", "Disagreements", "Mean head TV"],
                [
                    [
                        r["dataset"],
                        SHORT[r["arm"]],
                        SHORT[r["perturbation"]],
                        r["n"],
                        pct(r["agreement"]),
                        r["disagreements"],
                        num(r["tv"]["mean"]),
                    ]
                    for r in s["head_agreement"]
                ],
            ),
            "Native uniform→acoustic agreement is **86.04%→90.14% BASE**, **88.16%→91.05% LEFT**, **85.43%→89.07% RIGHT**. Acoustic still diverges somewhat more after RIGHT (65→72 disagreements); uniform changes 92→96. Physical agreement is 8/15→11/15 BASE, 8/15→11/15 LEFT, 9/15→11/15 RIGHT. Independent natural learner BASE agreement worsens **9/14→7/14**. On the 13 items admissible under contraction, acoustic agreement stays **7/13**; uniform changes **9/13→8/13 LEFT** and **9/13→9/13 RIGHT**. Thus contractions are stable under acoustic for these learners, yet the heads remain less concordant than under uniform. The diagnostic learner stratum stays 6/11 for every condition. Agreement is not correctness.\n\n",
            "## Distribution shift\n\n",
            table(
                [
                    "Head",
                    "Arm",
                    "Variant",
                    "Standardized norm mean",
                    "Reference cosine mean",
                    "Reference L2 mean",
                    "Training-mean distance",
                    "Standardized reference distance",
                ],
                [
                    [
                        r["head"],
                        SHORT[r["arm"]],
                        SHORT[r["perturbation"]],
                        *[
                            num(r[k]["mean"])
                            for k in (
                                "standardized_norm",
                                "cosine_to_reference",
                                "l2_to_reference",
                                "distance_to_training_mean",
                                "standardized_distance_to_reference",
                            )
                        ],
                    ]
                    for r in s["distribution"]
                    if r["dataset"] == "native"
                ],
            ),
            "Acoustic BASE is closer to the archived reference than uniform: mean cosine **0.92825 versus 0.88312**, raw L2 **1.97817 versus 2.61899**. Standardized norms are closer to reference under both heads: expanded **26.65 acoustic / 24.41 uniform / 27.55 reference**; pilot **27.53 / 25.20 / 28.46**. Distances to each frozen training mean are reported in raw embedding units; these scalar checks do not establish equality of distributions or validate every outlier. No new distribution model was fitted.\n\n",
            "## Effective support\n\n",
            table(
                ["Variant", "n", "Min", "5th percentile", "Median", "95th percentile", "Max"],
                [
                    [
                        SHORT[r["perturbation"]],
                        r["n"],
                        *[num(r[k]) for k in ("min", "p05", "median", "p95", "max")],
                    ]
                    for r in s["effective_n"]
                    if r["dataset"] == "native"
                ],
            ),
            table(
                ["Variant", "Extreme low-effective-n ID", "effective_n", "Frames", "Support ms"],
                [
                    [
                        SHORT[r["perturbation"]],
                        e["id"],
                        num(e["effective_n"]),
                        e["frame_count"],
                        f"{e['support_ms']:.2f}",
                    ]
                    for r in s["effective_n"]
                    if r["dataset"] == "native"
                    for e in r["lowest_five"][:3]
                ],
            ),
            "The minimum after RIGHT is **2.347**, which remains usable if geometric support passes. No effective_n threshold is introduced. The largest TV case does not have the minimum effective_n; concentration statistics alone do not resolve the observed failure.\n\n",
            "## Disjoint learner stability\n\n",
            "Coverage, left/right TV and flips, and head agreement are reported above separately for natural and diagnostic strata. On the 13 mutually usable natural units, acoustic has **zero flips under either edge or head**, versus uniform expanded 1/1 and pilot 2/1 left/right flips. Mean TV improves for all four natural head/edge comparisons. The 11 diagnostic units have no flips under either arm; expanded acoustic right mean TV is slightly worse (0.03619 versus 0.03377) with a 0.20601 maximum. These are small, correlated samples from one learner, not evidence of learner-tone accuracy.\n\n",
            table(
                [
                    "Learner set",
                    "Head",
                    "Variant",
                    "Paired n",
                    "Uniform-vs-acoustic TV mean",
                    "TV median",
                    "TV max",
                ],
                [
                    [
                        r["dataset"],
                        r["head"],
                        SHORT[r["perturbation"]],
                        r["tv"]["n"],
                        num(r["tv"]["mean"]),
                        num(r["tv"]["median"]),
                        num(r["tv"]["max"]),
                    ]
                    for r in arm_tv
                    if r["dataset"].startswith("learner")
                ],
            ),
            "## Decision and exact next step\n\n",
            "**ACOUSTIC_WEIGHTING PROMISING BUT NOT YET READY (PROMISING_NOT_READY).** Native preservation and the average structural advantage generalize beyond the prior 256. Uniform does not consistently win. Nevertheless, A's complete stability bar is not established: right-edge worst cases are substantially worse, a few per-tone cells gain flips, and independent natural learner head disagreement increases. This conclusion does not rely on a post-hoc cutoff.\n\n",
            "**Head-only refit: not yet justified.** Independent average representation benefit is supported, but frozen-head mismatch is not isolated as the clear blocker. High normalized edge weight can change the embedding itself, and neither head supplies learner realization truth.\n\n",
            decision["next_step"] + "\n\n",
            "## Tests, freeze and reproducibility\n\n",
            "Focused tests cover exact 256/659 disjointness and full inclusion, deterministic ID ordering, one-frame contractions, 3-frame/60ms clipping, immutable owners, acoustic equation/source identity, poisoned F0/expected-tone/character/prediction inputs, vector reconstruction, manifest/hash reproducibility, seal-before-inference, neutral/ambiguous semantics, learner recording disjointness, output completeness, unchanged model/checkpoint and frozen reference hashes. Pre-inference: 14 tests, 13 passed and the prediction-only check skipped. Final: **33 focused pooling tests passed**, with no skips. Test transcript: `focused-tests.txt`.\n\n",
            f"Freeze-after verifies **{freeze['verified_files']} existing files unchanged**, including previous experiments, sources, audio, releases, both head joblibs, pinned configuration and tracked API/mobile files; git HEAD is unchanged. Actual encoder checkpoint hashes are verified separately by focused tests. The new source files pass Ruff. No product/mobile suite, F0 estimator, training, refit, threshold search, ownership recomputation, grading/UI/Practice modification, recording, commit, push or deployment occurred.\n\n",
            "Reproduction phases (write-once artifacts intentionally refuse overwrite):\n\n```sh\nexport PYTHONPATH=research/perceptual-tone-model\nexport OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1\nPY=benchmark/pronunciation_v2/.venv/bin/python\n$PY -m perceptual_tone.pooling_confirmatory preregister\n$PY -m perceptual_tone.pooling_confirmatory construct\n$PY -m unittest discover -s research/perceptual-tone-model/tests -p test_pooling_confirmatory.py -v\n$PY -m perceptual_tone.pooling_confirmatory infer\n$PY -m perceptual_tone.pooling_confirmatory_analysis\n$PY scripts/pooling_confirmatory_report.py # from package directory, or use full path\n```\n\n",
            "Artifacts: `research/perceptual-tone-model/data/generated/pooling-confirmatory-v1/`. Preregistration and its seal; native IDs/exclusion proof; learner IDs/PCM proof; evaluation metadata; full representation manifest and seal; frame arrays; inference-start and raw probabilities/logits; coverage; native and paired metrics; per-tone performance/stability; item-level TV/cosine/L2/margins; expanded/pilot comparisons; distribution diagnostics; effective_n statistics and extremes; six cases; descriptive edge/region audit; decision; freeze-before/after; logs and focused tests. Tables are provided as JSON and CSV. Generated files remain gitignored under existing policy.\n\n",
            "Added source/report files: `perceptual_tone/pooling_confirmatory.py`, `perceptual_tone/pooling_confirmatory_analysis.py`, `scripts/pooling_confirmatory_report.py`, `tests/test_pooling_confirmatory.py`, and `pooling-confirmatory-report.md`. Pre-existing untracked work remains intact. **NOT READY for dev integration.**\n",
        ]
    )
    # Use the repository-root invocation in the reproducibility block.
    rendered = "".join(text).replace(
        "$PY scripts/pooling_confirmatory_report.py # from package directory, or use full path",
        "$PY research/perceptual-tone-model/scripts/pooling_confirmatory_report.py",
    )
    with REPORT.open("x") as f:
        f.write(rendered)
    print(REPORT, file_hash(REPORT))


if __name__ == "__main__":
    run()
