"""Append final evidence to the immutable pre-inference report prefix, once."""

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perceptual_tone.common import PACKAGE, file_hash, read_json, write_json
from perceptual_tone.pooling_experiment import OUT

s = read_json(OUT / "analysis-summary.json")
cases = read_json(OUT / "six-diagnostic-cases.json")
manifest = read_json(OUT / "representation-manifest.json")
meta = read_json(OUT / "evaluation-metadata.json")
predictions = read_json(OUT / "predictions.json")["rows"]
lookup = {(r["id"], r["arm"], r["head"]): r for r in predictions}
arms = ("CURRENT_REFERENCE", "UNIFORM_SAFE_OWNER", "CENTRAL_HALF", "ACOUSTIC_WEIGHTED")
short = dict(zip(arms, ("Reference", "Uniform", "Central", "Acoustic"), strict=True))
heads = ("expanded", "pilot")
parts = []


def para(text):
    parts.append(text.strip() + "\n\n")


def table(headers, rows):
    parts.append("| " + " | ".join(headers) + " |\n")
    parts.append("| " + " | ".join("---" for _ in headers) + " |\n")
    for row in rows:
        parts.append("| " + " | ".join(str(v) for v in row) + " |\n")
    parts.append("\n")


def pct(x):
    return f"{100 * x:.2f}%"


def accuracy_delta(head, arm):
    delta = s["native_metrics"][head][arm]["paired_deltas_from_reference"]["accuracy"]
    return f"{100 * delta['absolute']:+.2f}; {100 * delta['relative']:+.2f}%"


para("""
**Final decision: NO_CLEAR_WINNER. NOT READY for dev integration.**
Acoustic weighting is the strongest candidate in this experiment: it largely preserves
frozen native recognition, reduces the early low-energy and quiet-tail contributions,
and reduces head disagreement. It does not consistently resolve strong-frication
sensitivity or the opposite head interpretations of take-1 这 and take-3 我. Central
pooling removes some peripheral frames but can concentrate other problematic material
and substantially worsens expanded native recognition. These mixed findings do not
justify integration, a tuned rule, or a head-retraining recommendation.

All physical outputs below are diagnostic. No dictionary, expected/surface tone, learner
grade, or physical correctness score entered representation construction or evaluation.
Neither head is perceptual ground truth. Smaller distance to CURRENT_REFERENCE is
descriptive stability, not proof of better recognition on learner speech.
""")

para("""
Exactly three candidate definitions were sealed. **Uniform** uses every center in the
fixed safely owned span, with weight 1/N. **Central** uses K=ceil(N/2), starts at
floor((N-K)/2), and keeps K consecutive IDs with weight 1/K. This selects the earlier
window on a tie: N=4 → offsets [1,2]; N=5 → [1,2,3]; N=6 → [1,2,3]; N=11 → [2,…,7].
**Acoustic** assigns raw weight RMS_20ms * (1-high_band_fraction), then divides by the
sum in float64. It keeps the full eligible frame set; it does not trim ownership.

RMS is sqrt(mean(x²)) of the uncentered 20 ms waveform. Spectral power is
abs(rFFT((x-mean(x))*Hann))², with the symmetric NumPy Hann window. The high-band
fraction is power at frequencies ≥3400 Hz divided by max(total power, 1e-24), exactly
the previous low-level diagnostic definition. The hop is 5 ms. Physical features are
read from the frozen diagnostic CSVs; native features use the same equations on
canonical PCM16 16 kHz audio. Each encoder center maps to the nearest timestamp,
earlier on a tie; no interpolation, F0, periodicity estimate, or pitch mask is used.
Only negative RMS and out-of-range band fractions are clamped to their mathematical
domains. Nonfinite values fail. A total weight ≤float64.tiny
(2.2250738585072014e-308) abstains; there is no uniform fallback or weight floor.

All arms require at least three encoder frames AND ≥60 ms of contiguous selected
20 ms frame-cell support clipped to the owner. Arithmetic tolerance is 1e-9 seconds.
No outward expansion is allowed. Kish effective_n=1/sum(w²), and effective_n*20 ms,
are descriptive only; no concentration cutoff is applied. Owner duration, center
extent, cell support, clipped support, and effective support are separately saved.
""")

seal = read_json(OUT / "representation-manifest-seal.json")
start = read_json(OUT / "inference-start.json")
para(f"""
The representation seal was written at **{seal["sealed_at"]}**; inference began at
**{start["started_at"]}**. The report's original prefix and coverage table were also
hashed before that inference event (`pre-inference-report-seal.json`).
The primary manifest hashes every pooled vector and layer-9 tensor; its own hash is
`{seal["sha256"]}`. It contains all 828 item/arm records, including explicit
abstentions, plus the available historical reference records. The separately sealed
`pre-inference-inventory.json` adds source/speaker, explicit frame counts and central
window offsets, and links native-only evaluation labels. No sealed representation
was overwritten, invalidated, or changed. The two frozen heads produced
{len(predictions)} saved head/representation outputs, once per unique combination.
""")

para("""
The native control uses 64 items per T1/T2/T3/T4, selected from the existing 915
primary-eligible test units by deterministic round robin over sorted speaker IDs,
with lexicographically sorted item IDs within each speaker/tone. The exact 256 IDs
were persisted before encoder extraction or classifier inference. All 12 held-out
speakers are represented and disjoint from both heads' training speakers. Labels
are used only for native stratification and metrics, never pooling. No new model
was fitted. These 256 items are clustered within speakers/utterances; descriptive
changes of one item do not establish statistical equivalence or superiority.

Native ownership is the existing frozen MFA whole read-unit boundary; physical
ownership is the persisted GAP_AWARE_AZURE result. This is an explicit limitation:
the native control tests representation transfer under frozen ownership, not the
Azure ownership selector. CURRENT_REFERENCE is the historical physical pooling
or native nucleus/coda pooling in the identical encoder context, not a fourth
candidate. Historical native references shorter than 60 ms remain historical
comparators; none are used to relax candidate support rules.
""")

para("""
Coverage must separate representation availability from class inventory. All arms
provide representations for 19/20 physical/Google units. The one unavailable unit
is ownership-ambiguous take-2 买, unchanged under all arms. The four neutral units
have usable representations but are outside the heads' T1-T4 inventory: they are
**head exclusions, not model abstentions**. Thus each arm has 15 usable numbered-tone
head inputs out of 16 numbered units. Native units are all numbered and ownership-valid.
""")
table(
    ["Dataset", "Arm", "Usable / total", "Abstained", "Head usable", "Support failures"],
    [
        [
            r["dataset"],
            short[r["arm"]],
            f"{r['usable']}/{r['total']}",
            r["abstained"],
            r["head_usable"],
            r["reasons"].get("insufficient_60ms_support", 0),
        ]
        for r in s["coverage"]
    ],
)
para("""
The shared native failure is `aishell3:SSB02870020:2`: its 60 ms owner contains
three centers, but clipped cell support is **59.96875 ms** under the sealed half-sample
geometry. It remains rejected; the threshold was not rounded down after observing
data. Central additionally rejects `aishell3:SSB05700009:14` and
`aishell3:SSB07860039:11`, each retaining two frames / 40 ms. No zero-weight failure
occurred. There are zero effective-support exclusions because that statistic has
no gating role.
""")

para(
    "Native metrics are conditional on the arm's covered items. Recalls and "
    "confusion matrices use T1,T2,T3,T4 order. All-selected correct "
    "fractions and paired denominators follow so coverage cannot hide "
    "errors."
)
table(
    ["Head", "Arm", "N", "Accuracy", "Balanced accuracy", "Macro F1", "Recall T1/T2/T3/T4"],
    [
        [
            h,
            short[a],
            (m := s["native_metrics"][h][a]["all_selected"])["covered"],
            pct(m["accuracy"]),
            pct(m["balanced_accuracy"]),
            pct(m["macro_f1"]),
            " / ".join(pct(m["per_tone"][t]["recall"]) for t in ("T1", "T2", "T3", "T4")),
        ]
        for h in heads
        for a in arms
    ],
)
table(
    ["Head", "Arm", "Confusion: truth rows * predicted columns"],
    [
        [
            h,
            short[a],
            "`; `".join(str(row) for row in s["native_metrics"][h][a]["all_selected"]["confusion"]),
        ]
        for h in heads
        for a in arms
    ],
)
table(
    [
        "Head",
        "Arm",
        "Correct / all 256",
        "Accuracy on common 253",
        "Paired accuracy Δ (pp; relative)",
    ],
    [
        [
            h,
            short[a],
            pct(s["native_metrics"][h][a]["all_selected"]["correct_fraction_all"]),
            pct(s["native_metrics"][h][a]["common_covered"]["accuracy"]),
            accuracy_delta(h, a),
        ]
        for h in heads
        for a in arms
    ],
)
para("""
Paired deltas compare each arm with the reference on that arm's covered IDs.
Acoustic changes expanded accuracy by **+0.39 pp (+0.43% relative)** and pilot
by **-0.39 pp (-0.44% relative)**: one additional correct expanded item and one
fewer correct pilot item. Central changes expanded by **-7.11 pp (-7.79% relative)**,
while pilot is unchanged on the same 253 items. Native balanced accuracy and macro
F1 deltas, including relative differences, are saved in `native-metrics.json`.
These are recognition metrics only for known native labels.
""")

para(
    "The six required cases below show expanded/pilot predictions and "
    "probability top-two margins. Logit margins and all four probabilities "
    "are saved alongside them in `six-diagnostic-cases.json` and `all-"
    "predictions.csv`."
)
table(
    ["Case", "Arm", "Expanded", "Pilot", "Probability margins E / P", "Logit margins E / P"],
    [
        [
            c["display"],
            short[a],
            d["outputs"]["expanded"]["prediction"],
            d["outputs"]["pilot"]["prediction"],
            " / ".join(f"{d['outputs'][h]['probability_margin']:.4f}" for h in heads),
            " / ".join(f"{d['outputs'][h]['logit_margin']:.4f}" for h in heads),
        ]
        for c in cases
        for a in arms
        if (d := c["arms"][a])["outputs"]["expanded"] is not None
    ],
)
para("""
**Take-1 这:** central keeps IDs 15-20. It removes earliest IDs 13-14 but retains
15 and increases the mass on all added early material (13-19) from 63.64% to
83.33%. Acoustic reduces that mass to 28.48%; earliest 13-15 mass drops from
27.27% to 13.65%. Expanded/pilot remain opposite under every arm: uniform and
central give T2/T3, acoustic gives T3/T2. Acoustic expanded's probability margin
is only .0349 (logit .0989). This reduces early weight without resolving the
head-dependent low-margin instability. The old prediction is not a truth label.

**Take-2 这:** central keeps IDs 15-20 and excludes both influential below-gate
frames 13-14. Acoustic assigns them .005825 and .007484 normalized weight
(RMS .001594/.001839; high-band .1654/.0706), together **1.33% versus 18.18%**
uniform. Later speech IDs 20-23 receive .156702/.232366/.234311/.262977 each;
the early pair is far less influential in the weighted mean. Both candidates give
T3/T3, whereas uniform gives T4/T3. Acoustic expanded's margin rises to .6188,
but pilot's falls to .0770; head agreement does not mean both heads became more certain.

**Take-3 想:** known strong-frication IDs 13-16 have high-band fractions
.6688/.4539/.5593/.5364 and RMS .226988/.267388/.225599/.159438. Acoustic
weights are .034885/.067761/.046134/.034302, totaling **18.31% versus 23.53%**
uniform, only a 22.19% relative reduction. Frame 14 actually increases from
5.88% uniform to 6.78%: strong RMS can outweigh the spectral penalty. Central
keeps 17-25 and excludes all four fricative frames, but both alternatives still
give expanded T2 / pilot T1. Acoustic expanded's logit margin .3611 is close to
uniform .3873. This does not establish that frication sensitivity is solved;
contextual encoder vectors can carry information outside their local center.

**Take-3 买:** quiet tail IDs 29-35 have RMS .024342-.036308, versus
.043861-.133777 in IDs 13-28. Acoustic tail weights are
.022830/.017551/.019372/.015743/.012623/.017742/.015240, totaling
**12.11% versus 30.43%** uniform. Central keeps 18-29 and only one tail frame,
8.33% total tail weight, but still gives T2/T3. Acoustic gives T3/T3 with margins
.4142/.8174. Central also removes early body frames with different projections;
less tail mass alone is insufficient. Acoustic improves head consistency here,
without establishing a correct perceived tone.

**Google 买:** uniform and acoustic retain 15 frames and 290 ms clipped support;
central retains 8 frames and 160 ms. Acoustic effective_n is 10.37. All three
remain usable without F0 and produce T3/T3. Its existing pitch status is reported
only as metadata; neither missing pitch nor the T3 output selects the representation.

**Take-3 我:** uniform/acoustic retain 24 frames / 470 ms; central retains 12 /
240 ms. All arms give expanded T2 / pilot T3. Acoustic increases pilot margin
from .5304 to .8501 while retaining expanded margin .7399: confident disagreement
persists. Neither output is called correct. There is no usable CURRENT_REFERENCE
comparison for this unit or Google 买.
""")

para("""
The complete 20-unit inventory is below. Each candidate has identical representation
and head coverage on these recordings. Full per-arm probabilities, margins, support,
weights, and existing pitch status are in `physical-20-unit-comparison.csv`.
Pitch status is copied only after inference for interpretation; it is absent from
the sealed representation function's inputs.
""")
physical_rows = []

with (OUT / "physical-20-unit-comparison.csv").open() as stream:
    physical_csv = list(csv.DictReader(stream))
for identifier in [i for i, m in meta.items() if m["native_label"] is None]:
    r = next(x for x in physical_csv if x["id"] == identifier)
    outputs = []
    for arm in arms[1:]:
        e, p = lookup.get((identifier, arm, "expanded")), lookup.get((identifier, arm, "pilot"))
        outputs.append(
            f"{e['prediction']}/{p['prediction']}"
            if e
            else "neutral: excluded"
            if not meta[identifier]["head_compatible"]
            else "ownership abstained"
        )
    physical_rows.append(
        [
            meta[identifier]["display"],
            r["ownership"],
            "usable" if not r["representation_reason"] else "abstained",
            r["pitch_evidence_status_metadata_only"],
            *outputs,
        ]
    )
table(
    [
        "Unit",
        "Ownership",
        "Representation (all arms)",
        "Saved pitch status",
        "Uniform E/P",
        "Central E/P",
        "Acoustic E/P",
    ],
    physical_rows,
)

para(
    "Pairwise stability uses mutually usable numbered-tone units: 15 among "
    "candidates and 13 against the available reference. TV is half the L1 "
    "probability-vector difference. Embedding cosine/L2 are independent of "
    "the head and appear once per pair."
)
table(
    [
        "Pair",
        "N",
        "Expanded agree; mean TV",
        "Pilot agree; mean TV",
        "Mean embedding cosine",
        "Mean embedding L2",
    ],
    [
        [
            short[e["left"]] + " → " + short[e["right"]],
            e["n"],
            f"{e['argmax_agree']}/{e['n']}; {e['tv']['mean']:.4f}",
            f"{p['argmax_agree']}/{p['n']}; {p['tv']['mean']:.4f}",
            f"{e['embedding_cosine']['mean']:.4f}",
            f"{e['embedding_l2']['mean']:.4f}",
        ]
        for e in s["stability"]
        if e["dataset"] == "physical" and e["head"] == "expanded"
        for p in s["stability"]
        if p["dataset"] == "physical"
        and p["head"] == "pilot"
        and (p["left"], p["right"]) == (e["left"], e["right"])
    ],
)
table(
    ["Dataset", "Arm", "Head disagreement", "Rate", "Mean head TV"],
    [
        [
            r["dataset"],
            short[r["arm"]],
            f"{r['disagreements']}/{r['n']}",
            pct(r["disagreements"] / r["n"]),
            f"{r['tv']['mean']:.4f}",
        ]
        for r in s["head_agreement"]
    ],
)
para(
    "On the same 13 reference-covered physical units, disagreements are "
    "reference 4, uniform 6, central 4, acoustic 3. This paired comparison "
    "avoids confusing the reference's smaller coverage with better "
    "agreement. Agreement and TV improve in different ways; none is an "
    "accuracy score for physical speech."
)

table(
    [
        "Acoustic dataset",
        "N usable",
        "Effective_n min / median / max",
        "Effective_n <3 (descriptive)",
    ],
    [
        [
            r["dataset"],
            r["usable"],
            " / ".join(f"{r['effective_n'][k]:.3f}" for k in ("min", "median", "max")),
            r["usable_effective_n_below_3"],
        ]
        for r in s["coverage"]
        if r["arm"] == "ACOUSTIC_WEIGHTED"
    ],
)
para("""
The most concentrated physical item is neutral take-2 个: effective_n 2.905 across
8 eligible frames, maximum weight .4692. It has a representation but no four-class
inference. The lowest numbered physical effective_n is take-2 这, 4.879 across
11 frames. Native `aishell3:SSB02880034:0` has effective_n 2.155 across 7 frames
(max weight .5402), and `aishell3:SSB04070025:0` has 2.671 across 9 (max .4511).
They remain included exactly as preregistered; no post-hoc support exclusions were made.
""")

para(
    "Native distribution diagnostics use only each head's frozen "
    "StandardScaler mean and scales. Standardized norm is a diagonal "
    "variance-scaled distance to that training mean; raw L2 is also shown. "
    "No covariance or new density model is fitted. Smaller norm is not "
    "automatically better: broad uniform averaging can dilute features "
    "toward the mean."
)
table(
    [
        "Head",
        "Arm",
        "Mean standardized norm",
        "Mean raw L2 to training mean",
        "Mean cosine to reference",
        "Mean paired standardized-norm Δ",
    ],
    [
        [
            r["head"],
            short[r["arm"]],
            f"{r['standardized_norm']['mean']:.3f}",
            f"{r['distance_to_training_mean']['mean']:.3f}",
            f"{r['cosine_to_reference']['mean']:.4f}",
            f"{r['paired_standardized_norm_delta']['mean']:+.3f}",
        ]
        for r in s["distribution"]
        if r["dataset"] == "native"
    ],
)
para("""
Central moves native embeddings furthest: reference cosine .7704, expanded
standardized norm 33.33 versus 27.43 reference, and mean standardized vector
distance 23.89. Its expanded recognition loss is consistent with frozen-head
distribution mismatch. However its physical structural benefit is inconsistent,
and pilot native accuracy is preserved, so this is insufficient for decision B.
Acoustic stays closer to the existing representation (cosine .9290, expanded
norm 26.49, standardized distance 11.55), with native metrics essentially unchanged
on this subset. There is no major acoustic head-compatibility regression to justify
retraining. Uniform has norm 24.22 and cosine .8751: pooling toward the mean can
reduce the norm while degrading expanded recognition.

Weight-mass comparisons quantify direct pooling composition, not causal waveform
attribution: HuBERT features are contextual. This pass does not repeat attribution,
change spans, or introduce perturbation/ablation arms. Therefore these results
support reduced peripheral weighting and observed representation stability, not
a complete demonstration of invariance to boundary changes or perceptual superiority.
""")

next_experiment = (
    "One confirmatory offline frozen-head experiment: retain the exact ACOUSTIC_WEIGHTED "
    "formula and Uniform comparator on the remaining 659 eligible native test IDs, "
    "plus a preregistered disjoint set of already frozen learner units. Before inference, "
    "seal exact IDs and one-frame left/right pooling contractions entirely inside each "
    "unchanged safe owner, applied symmetrically to both representations. Measure native "
    "recognition/coverage and within-item TV, argmax and head disagreement under those "
    "fixed perturbations. Keep encoder, heads, 60ms/3-frame rules and weights fixed; "
    "no parameter search, new recordings, integration or head refit."
)
para("""
Central helps geometric exclusion in some cases, but does not reliably reduce the
three known sensitivity patterns and loses expanded native performance. Acoustic
helps the early/pre-vowel and quiet-tail patterns, preserves Google 买 coverage,
and is the most promising overall candidate; the frication result and persistent
head disagreements remain unresolved. Consequently the selected outcome is
**NO_CLEAR_WINNER**, not READY, DISTRIBUTION_MISMATCH, or UNIFORM_BEST.
""")
para("Exact next experiment (recommendation only; not performed): " + next_experiment)

verification = s["reference_verification"]
freeze = read_json(OUT / "freeze-after.json")
para(f"""
Validation: 18 focused pooling tests pass, covering deterministic central selection
and earlier ties, acoustic-equation identity with existing diagnostics, nearest mapping,
normalization, effective_n, zero-weight abstention, frame/time minimums, ambiguous
ownership, neutral exclusion, native IDs, forbidden pitch/target/output fields,
manifest reconstruction and hashes, exact vector reconstruction, report-prefix
ordering, unique inference records, and frozen artifacts. Ruff passes on the new
modules/tests. No product/mobile suite or attribution audit was run.

Fresh layer-9 extraction reproduces all 256 historical native reference vectors
within **{verification["max_embedding_absolute_error"]:.3e}** absolute coordinate error;
uniform physical probabilities reproduce the ownership experiment within
**{verification["physical_uniform_probability_max_error"]:.3e}**. Differences are the
documented float64 weighted mean versus the archived float32 Torch mean.
The post-inference freeze verifies **{freeze["verified_files"]} files unchanged** and
the same git HEAD: model joblibs, pinned contracts/configuration, prior ownership,
frame-attribution and F0-independent artifacts, consumed audio, frozen releases,
research source and tracked API/mobile files. The encoder checkpoint hashes also
match the frozen lock. There was no retraining, calibration, classifier modification,
ownership change, Practice/UI/grading/sandhi/Azure timing change, commit, push or deploy.
""")
para("""
Artifacts are additive under `data/generated/pooling-representation-v1/`:
`preregistration.json`, `preregistration-seal.json`, `native-control-ids.json`,
`evaluation-metadata.json`, `representation-manifest.json`,
`representation-manifest-seal.json`, `representations/*.npy`,
`pre-inference-inventory{,-seal}.json`, `pre-inference-report-seal.json`,
`inference-start.json`, `predictions.json`, `analysis-summary.json`,
`native-metrics.{json,csv}`, `physical-20-unit-comparison.csv`,
`six-diagnostic-cases.json`, `case-frame-weights.csv`, `pairwise-stability.csv`,
`expanded-pilot-comparison.csv`, `all-predictions.csv`, `coverage.csv`,
`effective-support.json`, `embedding-distribution.json`, `decision.json`,
`freeze-before.json`, `freeze-after.json`, and verification records.

Added source files: `perceptual_tone/pooling_representation.py`,
`perceptual_tone/pooling_experiment.py`, `perceptual_tone/pooling_analysis.py`,
`scripts/pooling_representation_report.py`, and `tests/test_pooling_representation.py`.
Added report: `pooling-representation-experiment-report.md`. Generated files are
gitignored by existing repository policy; none were force-added. Existing untracked
work from the previous experiments was preserved. **NOT READY for dev integration.**
""")

report = PACKAGE / "pooling-representation-experiment-report.md"
prefix = read_json(OUT / "pre-inference-report-seal.json")
assert report.stat().st_size == prefix["bytes"], "report already finalized; do not append twice"
assert file_hash(report) == prefix["sha256"]
with report.open("a") as stream:
    stream.write("\n" + "".join(parts))
assert hashlib.sha256(report.read_bytes()[: prefix["bytes"]]).hexdigest() == prefix["sha256"]
write_json(
    OUT / "decision.json",
    {
        "decision": "NO_CLEAR_WINNER",
        "dev_integration": "NOT_READY",
        "strongest_candidate": "ACOUSTIC_WEIGHTED",
        "reason": (
            "Native compatibility and early/tail improvements, unresolved "
            "frication and head-dependent behavior; central has structural and "
            "native regressions."
        ),
        "next_experiment_recommendation_only": next_experiment,
        "report_sha256": file_hash(report),
        "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
    },
)
print(json.dumps({"report": str(report), "sha256": file_hash(report)}, indent=2))
