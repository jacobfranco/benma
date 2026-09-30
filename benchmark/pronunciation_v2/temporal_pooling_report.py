"""Read-only arithmetic verification and reporting of completed Experiment 2.

This post-result reporting module never extracts features, fits or predicts.
It creates only derived reports and their provenance, preserving locked artifacts.
"""

import json
import subprocess
from datetime import datetime
from itertools import pairwise
from pathlib import Path

import numpy as np
import temporal_pooling as experiment
from preflight import sha256

OUT = experiment.OUTPUT
SUMMARY = ("accuracy", "balanced_accuracy", "macro_f1")


def read(name):
    return json.loads((OUT / name).read_text())


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(str(x) for x in row) + " |" for row in rows],
        ]
    )


def panel(name, result):
    lines = [
        f"## {name}",
        "",
        table(
            ["Metric", "A", "B", "B - A"],
            [
                [k, result["A"][k], result["B"][k], result["B"][k] - result["A"][k]]
                for k in ("n", *SUMMARY)
            ],
        ),
        "",
        table(
            [
                "Tone",
                "Support",
                "A precision",
                "B precision",
                "A recall",
                "B recall",
                "A F1",
                "B F1",
            ],
            [
                [
                    t,
                    result["A"]["per_tone"][str(t)]["support"],
                    *[
                        result[a]["per_tone"][str(t)][k]
                        for k in ("precision", "recall", "f1")
                        for a in "AB"
                    ],
                ]
                for t in range(1, 5)
            ],
        ),
        "",
        "Confusion matrices: true rows / predicted columns, T1-T4.",
        "",
        "```text",
        "A                              B",
    ]
    for a, b in zip(result["A"]["confusion_matrix"], result["B"]["confusion_matrix"], strict=True):
        lines.append(f"{a!s:30s} {b}")
    lines.extend(
        [
            "```",
            "",
            table(
                ["Directed confusion", "A count", "A rate", "B count", "B rate"],
                [
                    [
                        key,
                        *[
                            result[a]["directed_confusions"][key][k]
                            for a in "AB"
                            for k in ("count", "rate")
                        ],
                    ]
                    for key in ("T2->T3", "T3->T2", "T3->T4", "T4->T3")
                ],
            ),
            "",
            "Rates use true-tone support. Bidirectional T2↔T3 counts: "
            f"A={result['A']['bidirectional_confusions']['T2<->T3']}, "
            f"B={result['B']['bidirectional_confusions']['T2<->T3']}; T3↔T4: "
            f"A={result['A']['bidirectional_confusions']['T3<->T4']}, "
            f"B={result['B']['bidirectional_confusions']['T3<->T4']}.",
            "",
            "Paired correctness: "
            + "; ".join(f"{k}={v}" for k, v in result["paired_correctness"].items())
            + ".",
            "",
        ]
    )
    return "\n".join(lines)


def verify_artifacts(development, fresh, stress):
    experiment.verify_seal()
    locked = experiment.require_lock(experiment.environment())
    times = [
        read(n)[key]
        for n, key in (
            ("baseline-reproduction.json", "completed_at"),
            ("lock.json", "locked_at"),
            ("fresh-test-opened.json", "opened_at"),
            ("fresh-test-completed.json", "completed_at"),
            ("stress-opened.json", "opened_at"),
            ("stress-completed.json", "completed_at"),
        )
    ]
    if not all(datetime.fromisoformat(a) < datetime.fromisoformat(b) for a, b in pairwise(times)):
        raise ValueError("Incorrect execution chronology")
    reports = [
        ("development", development["validation"], 49),
        ("fresh-test", fresh, 118),
        ("stress", stress, 60),
    ]
    reports += [
        (f"development-{name}", value["results"], value["results"]["A"]["n"])
        for name, value in development["source_diagnostics"].items()
    ]
    counts = {}
    for prefix, report, count in reports:
        records = experiment.csv_rows(OUT / f"{prefix}-predictions.csv")
        if len(records) != count:
            raise ValueError("Prediction denominator changed")
        for row in records:
            for a in "AB":
                row[f"{a}_prediction"] = int(row[f"{a}_prediction"])
                p = np.array([float(row[f"{a}_p_T{t}"]) for t in range(1, 5)])
                if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
                    raise ValueError("Invalid probabilities")
                np.testing.assert_allclose(p.sum(), 1, rtol=0, atol=1e-12)
                if (
                    int(p.argmax()) + 1 != row[f"{a}_prediction"]
                    or p.max() != float(row[f"{a}_confidence"])
                    or (row[f"{a}_correct"] == "True")
                    != (row[f"{a}_prediction"] == int(row["tone"]))
                ):
                    raise ValueError("Prediction/probability/correctness mismatch")
        summary = experiment.summarize(records)
        for key, value in summary.items():
            if report[key] != value:
                raise ValueError(f"Aggregate arithmetic mismatch: {prefix}/{key}")
        for name, speaker in report["per_speaker"].items():
            if speaker != experiment.summarize([r for r in records if r["speaker_name"] == name]):
                raise ValueError("Per-speaker arithmetic mismatch")
        counts[prefix] = count
    if {r["source_asset_id"] for r in experiment.csv_rows(OUT / "fresh-test-predictions.csv")} != {
        r["source_asset_id"]
        for r in experiment.csv_rows(experiment.PREFLIGHT / "sealed-test-manifest.csv")
    }:
        raise ValueError("Fresh prediction IDs differ from seal")
    for a in "AB":
        arrays = np.load(OUT / f"head-{a}.npz", allow_pickle=False)
        for key, fields in (
            ("scaler_sha256", ("mean", "var", "scale", "n_samples_seen")),
            ("classifier_sha256", ("coef", "intercept", "classes")),
        ):
            if experiment.arrays_hash({k: arrays[k] for k in fields}) != locked["fitted"][a][key]:
                raise ValueError("Fitted parameter hash mismatch")
        if arrays["n_samples_seen"].item() != 386:
            raise ValueError("Scaler training denominator changed")
    old_stress = {
        r["source_asset_id"]: r for r in experiment.csv_rows(experiment.OLD / "test-results.csv")
    }
    stress_probability_delta = 0.0
    for r in experiment.csv_rows(OUT / "stress-predictions.csv"):
        previous = old_stress[r["source_asset_id"]]
        if r["A_prediction"] != previous["prediction"]:
            raise ValueError("Stress A differs from historical baseline")
        for t in range(1, 5):
            stress_probability_delta = max(
                stress_probability_delta, abs(float(r[f"A_p_T{t}"]) - float(previous[f"p_T{t}"]))
            )
    if stress_probability_delta > experiment.REPRO_ATOL:
        raise ValueError("Stress A numerical mismatch")
    for prefix in ("fresh-test", "stress"):
        for name, expected in read(f"{prefix}-completed.json")["artifacts"].items():
            if sha256(OUT / name) != expected:
                raise ValueError("Completed result changed")
        if read(f"{prefix}-opened.json")["lock_sha256"] != sha256(OUT / "lock.json"):
            raise ValueError("Opening lock hash differs")
    return dict(
        passed=True,
        checked_at=experiment.now(),
        chronological_stages=times,
        prediction_counts=counts,
        identical_AB_ids=True,
        original_386_training_only=True,
        locked_source_and_parameters_unchanged=True,
        metric_recomputation_passed=True,
        stress_A_historical_probability_max_absolute_difference=stress_probability_delta,
        no_corrective_rerun=True,
    )


def comparison(panels):
    rows = []
    for name, result in panels:
        values = {k: {a: result[a][k] for a in "AB"} for k in SUMMARY}
        for tone in range(1, 5):
            for metric in ("precision", "recall", "f1", "support"):
                values[f"T{tone}_{metric}"] = {
                    a: result[a]["per_tone"][str(tone)][metric] for a in "AB"
                }
        for directed in result["A"]["directed_confusions"]:
            for metric in ("count", "rate"):
                values[f"{directed}_{metric}"] = {
                    a: result[a]["directed_confusions"][directed][metric] for a in "AB"
                }
        for metric, value in values.items():
            rows.append(
                dict(
                    panel=name,
                    n=result["A"]["n"],
                    metric=metric,
                    A=value["A"],
                    B=value["B"],
                    B_minus_A=value["B"] - value["A"],
                )
            )
    experiment.exclusive_csv(OUT / "comparison.csv", rows)


def main():
    development, fresh, stress = (
        read(f"{n}-results.json") for n in ("development", "fresh-test", "stress")
    )
    verification = verify_artifacts(development, fresh, stress)
    experiment.exclusive_json(OUT / "artifact-verification.json", verification)
    locked = read("lock.json")
    panels = [
        ("Development: Levi Highway (49)", development["validation"]),
        ("Fresh speakers: aggregate (118)", fresh),
    ]
    panels += [
        (f"Fresh speaker: {name}", fresh["per_speaker"][name])
        for name in ("Jouketou", "雲角", "Fake estate")
    ]
    panels += [("Luilui: KNOWN / INSPECTED STRESS SET (60)", stress)]
    for name, diagnostic in development["source_diagnostics"].items():
        panels.append((f"Development diagnostic: train {name}", diagnostic["results"]))
        panels += [
            (f"Development diagnostic: train {name}, evaluate {speaker}", result)
            for speaker, result in diagnostic["results"]["per_speaker"].items()
        ]
    comparison(panels)
    intro = f"""# Experiment 2: whole mean versus temporal thirds

**Temporal pooling did not improve fresh-speaker generalization in this frozen comparison.**
A scored 81/118 and B 78/118. Fresh B-A deltas are
accuracy {fresh["B_minus_A"]["accuracy"]},
balanced accuracy {fresh["B_minus_A"]["balanced_accuracy"]},
and macro F1 {fresh["B_minus_A"]["macro_f1"]}.
The modest T3 gain (9/29 to 11/29) accompanies a substantial descriptive T2 recall
regression (19/29 to 15/29, -13.793103448275862 percentage points), concentrated
in 雲角 (5/10 to 2/10). B does not satisfy the protocol's promising-result rule.
No numerical definition of “major” was preregistered; these are observed sizes,
not a new pass/fail cutoff. The conclusion already follows from lower overall
performance, and the T2 tradeoff adds a material concern.

The primary evidence is the fresh 118-clip panel. Luilui is a known/inspected
stress set and has no role in selection. All three fresh contributors have
**UNKNOWN native status**. This is not a native-Mandarin benchmark. Labels are
lexical targets, not independently verified realized-tone labels.

## Execution integrity and fixed configuration

The required offline verifier passed before model access and at each stage;
all 118 local files and recorded hashes verified. The sealed manifest remains
`{experiment.SEAL_HASH}`. Corpus selection/acquisition was not repeated.

Baseline A reproduced Experiment 1 **exactly**, before B fitting and fresh opening:
all 435 development pooled vectors were bitwise equal; scaler mean/variance/scale,
coefficients/intercepts/classes, and all 49 validation probabilities had maximum
absolute difference 0. Predictions were identical. The predeclared absolute
numerical tolerance was 1e-10 (metric tolerance 1e-12), with no relaxation.
Authoritative artifact hashes and checks are in
[baseline-reproduction.json](baseline-reproduction.json).

Lock UTC: **{locked["locked_at"]}**. Lock SHA-256:
`{sha256(OUT / "lock.json")}`. Git HEAD: `{locked["git_HEAD"]}`.
Fresh opening: `{read("fresh-test-opened.json")["opened_at"]}`.
Stress opening: `{read("stress-opened.json")["opened_at"]}`, after the fresh
results were saved and reported to the user. No model implementation/configuration
changed after the lock or opening; no corrective rerun occurred. Reporting-only
code was added after evaluation, separately hashed in provenance.

Both arms use frozen `facebook/wav2vec2-base` revision `{experiment.REVISION}`,
CPU FP32, four Torch threads, eager attention, seed 20260929, deterministic
algorithms and layer 8. Each untrimmed clip is decoded by the unchanged FFmpeg
function to mono 16 kHz and normalized by the checkpoint processor. One unpadded
clip per forward, no encoder attention mask; all emitted frames are valid.

A retains the Experiment 1 mean arithmetic over every valid frame (768 features).
B concatenates the arithmetic means of `[0:N//3)`, `[N//3:(2*N)//3)` and
`[(2*N)//3:N)` in order (2,304 features). N<3 fails both arms. No interpolation,
padding, frame repetition, lexical/expected-tone/speaker/F0 input or augmentation.

Both primary heads use the same original 386 training clips (Wei Gao 326,
CanonNi 60), with train-only StandardScaler (population variance). Each head is
multinomial L2 logistic regression: C=0.1, lbfgs, no class weights,
fit_intercept=True, max_iter=3000, tol=1e-8, random_state=20260929, one BLAS thread.
A converged in 111 iterations; B in 132. No tuning, layer search or model search.
Levi, Luilui, fresh clips and OMPAL never entered fitting. Source diagnostic fits
use only named subsets of those original training rows and do not replace heads.

Compact [head-A.npz](head-A.npz) and [head-B.npz](head-B.npz) preserve fitted mean,
variance, scale, sample count, coefficients, intercepts and class order.
[lock.json](lock.json) records file hashes and canonical scaler/classifier array
hashes, complete configuration, dependencies, code hashes and development metrics.
The exact selected training rows are in [training-manifest.csv](training-manifest.csv).

## Reading the metrics

Values below preserve the saved Python floating-point representations. All
principal panels contain all four tones. Balanced accuracy is mean four-tone
recall; macro F1 is mean four-tone F1; undefined precision/F1 uses zero. T3-only
stress recall is reported separately, without inventing a four-tone balanced
accuracy for a single-tone subset. Raw maximum softmax is uncalibrated and no
confidence rejection/acceptance threshold is used. Predictions cover every clip.
"""
    parts = [intro, *[panel(name, result) for name, result in panels[:5]]]
    parts += [
        "## Equal-speaker fresh means",
        "",
        table(
            ["Metric", "A", "B"],
            [
                [k, fresh["equal_speaker_mean"]["A"][k], fresh["equal_speaker_mean"]["B"][k]]
                for k in SUMMARY
            ],
        ),
        "",
        "B improves Jouketou by one correct clip, loses one on 雲角 and three on Fake estate. "
        "On Fake estate neither arm correctly classifies any of the nine T3 targets; "
        "eight are predicted T4 and one T1. Fake estate T1 recall falls from 9/10 to 7/10. "
        "Fresh T3→T4 errors remain 14/29 in both arms. The T3 gain does not resolve "
        "the primary T3/T4 failure pattern.",
        "",
        panel(*panels[5]),
        "## The 13 known Luilui T3 cases",
        "",
        "Both arms get only 晚 and 表 correct: **2/13 = 0.15384615384615385 recall**. "
        "A predicts T1/T2/T3/T4 counts 3/0/2/8; B predicts 2/0/2/9. "
        "The only T3 label change is 我, T1→T4, still wrong. "
        "Full-set accuracy falls from 43/60 to 42/60. The same locked B head "
        "does not repair this inspected failure.",
        "",
        table(
            [
                "Text",
                "Pinyin",
                "A prediction",
                "A max softmax",
                "A correct",
                "B prediction",
                "B max softmax",
                "B correct",
            ],
            [
                [
                    r["text"],
                    r["pinyin"],
                    r["A_prediction"],
                    r["A_confidence"],
                    r["A_correct"],
                    r["B_prediction"],
                    r["B_confidence"],
                    r["B_correct"],
                ]
                for r in stress["T3_cases"]
            ],
        ),
        "",
        "你、早、笔、等、五、买、狗 remain T4 errors in both arms; 纸 remains T1. "
        "晚 and 表 remain correct but their max-softmax values decrease. "
        "Changes in uncalibrated softmax do not establish changes in actual pronunciation quality.",
        "",
        *[panel(name, result) for name, result in panels[6:]],
        """## Interpretation, limits and next experiment

The exact frozen three-bin representation has worse aggregate and equal-speaker
fresh point estimates. There is one small speaker gain and two speaker declines,
with a T2 recall regression and persistent T3→T4 errors. It is not promising under
the stated rule. This does not establish that all temporal representations fail,
or that this English-pretrained encoder cannot represent Mandarin tones.

The comparison changes both temporal representation and dimensionality (768 to
2,304); fixed C also changes effective regularization across representations.
Consequently it does not isolate temporal order as the sole causal factor.
Whole-clip thirds include recorded silence; they need not coincide with phonetic
onset/middle/offset. Recording conditions, source effects, lexical/realized-tone
mismatch and the chosen coarse partition are plausible explanations, not diagnosed
causes. No F0 analysis, relabeling, listening-based exclusion or alternative fit
was introduced to explain away this result.

Three convenience-sampled contributors cannot establish population performance.
Speaker independence is based on source-profile IDs, not verified biological
identity; exact-byte/PCM deduplication cannot rule out every edited duplicate.
There are no clip-independent significance claims or speaker-population confidence
intervals. UNKNOWN native status and lexical labels limit all tone-error claims.
All 118 clips were retained; the panel is now inspected and cannot be pristine
for later model choices. No aggregate combines development, fresh and stress data.

**Recommended next experiment:** preregister a fixed-head evaluation on a new,
larger speaker-disjoint panel with independent, prediction-blinded realized-tone
annotation, especially T2/T3/T4. Keep these A/B heads frozen; report lexical-target
and realized-tone agreement separately, with uncertainty/ambiguous labels handled
by a rule fixed before prediction access. This would distinguish label mismatch
from continued model error without tuning on this opened panel. It requires a
separate authorization and protocol; no new acquisition/annotation is performed
here. No production/API/mobile integration is supported by these findings.

## Validation and artifact scope

**120 tests pass:** 66 research/model unit tests (52 existing plus 14 new), and
54 existing seal/preflight pytest cases. New controls cover N=3-8 exact basis-vector
bin membership, 768/2,304 dimensions, N<3, frozen deterministic extraction,
training-only scaling, immutable settings, evaluation membership/speaker leakage,
seal-before-access, lock-before-extraction, exclusive opening receipts,
stress-after-fresh, paired row IDs/counts and metric conventions.

The initial broad unittest discovery could not import two API-side test modules
inside the ML-only virtualenv (missing pytest/sqlalchemy). The relevant model and
seal suites were then run in their existing intended environments; no dependencies
were installed or changed. The unrelated acoustic-forensics suite was not rerun.
New Python files pass Ruff check/format. Directory-wide Ruff still identifies the
pre-existing unrelated report.py:95 formatting/line-length issue, left unchanged.

[artifact-verification.json](artifact-verification.json) confirms execution order,
all prediction denominators, same A/B IDs, recomputed aggregate/per-speaker metrics,
probability/argmax/correctness consistency, original training-only scaler count,
unchanged locked source/parameters, and A's historical Luilui probability reproduction.
No hidden-state arrays are retained. Pooled vectors stay in the ignored local cache;
raw CC BY-SA 4.0 fresh audio remains local and uncommitted. The preflight manifest
retains file-level attribution/license evidence and original-byte hashes.

No model/configuration changed after locking; only reports/documentation were
added after results. No corpus repair/reselection, production integration,
staging, commit or push occurred. See [environment.md](environment.md),
[comparison.csv](comparison.csv), [provenance.json](provenance.json), and the
complete development/fresh/stress JSON and prediction CSVs alongside this report.
""",
    ]
    with (OUT / "review.md").open("x") as handle:
        handle.write("\n".join(parts))
    environment = locked["environment"]
    extraction_rows = []
    for stage in ("development", "fresh-test", "stress"):
        r = read(f"{stage}-extraction.json")
        extraction_rows.append(
            [stage, r["n"], r["seconds"], r["peak_rss_mib"], r["min_frames"], r["max_frames"]]
        )
    extraction_table = table(
        ["Extraction", "Clips", "Seconds", "Peak process RSS MiB", "Min frames", "Max frames"],
        extraction_rows,
    )
    text = f"""# Experiment 2 environment and reproduction

Branch: pronunciation-v2-research. Starting/current HEAD: `{locked["git_HEAD"]}`.
Python {environment["python"]}; {environment["platform"]}.
{environment["ffmpeg"]}.

CPU FP32, Torch threads=4, fit BLAS threads=1, deterministic algorithms=True,
seed=20260929; frozen encoder with before/after state hashes and first-clip
bitwise repetition for each extraction stage. All 31 existing research dependency
versions match requirements-lock.txt. No packages were changed or downloaded.
Only the pinned cached encoder was loaded, with HF_HUB_OFFLINE=1 and
TRANSFORMERS_OFFLINE=1. No network access or GPU execution was needed.

{table(["Package", "Version"], sorted(environment["packages"].items()))}

{extraction_table}

Peak RSS is process high-water RSS, not incremental model memory. Wall times
include loading and determinism checks, not fitting or decoding-verifier time.
Every clip had at least three valid frames; no short-clip exclusion occurred.

Raw historical audio/checkpoint remain in the original ~/.cache/benma locations.
Fresh CC BY-SA 4.0 audio stays in the existing ignored preflight cache.
New pooled features and auxiliary diagnostic heads are local and ignored under
`{experiment.CACHE.relative_to(experiment.ROOT)}`. Full hidden states are discarded.
The two compact primary head NPZs are preserved with the reports for reproducibility;
both parameter-array hashes and file-byte hashes are locked. The copied training
manifest preserves the exact 386 original rows and their audio provenance.

Ordered commands and validation commands are documented in
`benchmark/pronunciation_v2/README.md`. Stage receipts and exclusive writes prohibit
silent overwrite/reopening. To reproduce elsewhere, preserve source, inputs and
dependency locks; use an explicitly separate run/cache and report its lineage.
Never delete a receipt to make a rerun look pristine. On this workspace the fresh
panel is now inspected. `temporal_pooling_report.py` only verifies arithmetic and
writes derived reports; it never extracts, fits or predicts.

Validation: 66 research/model tests and 54 seal/preflight tests passed. New source
passes Ruff check/format; directory-wide checks have the pre-existing report.py:95
failure. The unsuccessful broad discovery and successful split-suite runs are
recorded in provenance, without environment mutation.
"""
    with (OUT / "environment.md").open("x") as handle:
        handle.write(text)
    experiment.exclusive_json(
        OUT / "provenance.json",
        dict(
            created_at=experiment.now(),
            git_HEAD=locked["git_HEAD"],
            lock_sha256=sha256(OUT / "lock.json"),
            sealed_manifest_sha256=experiment.SEAL_HASH,
            locked_inputs=locked["inputs"],
            locked_source_code_sha256=locked["source_code_sha256"],
            post_result_reporting_code_sha256={
                str(Path(__file__).resolve().relative_to(experiment.ROOT)): sha256(Path(__file__))
            },
            artifacts_sha256={p.name: sha256(p) for p in sorted(OUT.iterdir()) if p.is_file()},
            local_feature_caches={
                stage: read(f"{stage}-extraction.json")["feature_cache_sha256"]
                for stage in ("development", "fresh-test", "stress")
            },
            raw_audio_policy="evaluation-only local/cache-only; no raw audio in curated output",
            fresh_speakers_native_status="UNKNOWN",
            labels="lexical targets; realized tone unverified",
            scientific_code_changed_after_opening=False,
            corrective_reruns=[],
            validation=dict(
                model_research_tests=66,
                seal_preflight_tests=54,
                initial_discovery="ML environment missing API test dependencies; split suites used",
                new_source_ruff="check and format pass",
                directory_ruff="pre-existing report.py:95 formatting/E501 failure",
            ),
        ),
    )
    print(json.dumps(verification, indent=2))
    print(subprocess.check_output(["git", "status", "--short"], text=True))


if __name__ == "__main__":
    main()
