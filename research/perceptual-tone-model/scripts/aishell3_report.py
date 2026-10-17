"""Render the sealed experiment's tables and complete error/probe appendices."""
# ruff: noqa: E501, RUF001 -- long rendered prose, paths and intentional typography

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_train import DEFAULT_RELEASE, DEFAULT_RUN
from perceptual_tone.common import PACKAGE, file_hash, read_json

NAMES = {
    "model0_benma": "0 Frozen Benma",
    "model1_acoustic": "1 Acoustic LR",
    "model2_hubert": "2 Chinese HuBERT LR",
    "model3_wavlm": "3 WavLM LR",
    "model4_mlp": "4 Small MLP",
    "model6_combined": "6 HuBERT + acoustics LR",
}


def pct(value):
    return "—" if value is None else f"{100 * value:.2f}%"


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |",
                *["| " + " | ".join(str(c) for c in row) + " |" for row in rows],
            ]
        )
        + "\n"
    )


def render():
    folder = DEFAULT_RUN
    release = read_json(DEFAULT_RELEASE / "release.json")
    selected = read_json(folder / "selected.json")
    result = read_json(folder / "test-results.json")
    trials = read_json(folder / "validation-trials.json")
    probe = read_json(folder / "external-probe.json")
    reproduction = read_json(PACKAGE / "reports/aishell3-training-validation.json")
    finalization = read_json(PACKAGE / "reports/aishell3-finalization-audit.json")
    runlink = "models/generated/aishell3-first-four-tone-v1/"
    metrics = result["metrics"]
    out = [
        "# AISHELL-3 first four-tone training pass — 2026-10-17",
        "**CORE TONE-ML FEASIBILITY: CLEARLY PROMISING.** "
        "Learned connected-speech tone perception is materially more promising than the frozen deterministic "
        "Benma family scorer on this AISHELL-3 pilot.",
        "**CURRENT PRODUCT GENERALIZATION: MIXED / UNPROVEN.** "
        "This pilot does not yet establish reliable generalization to Benma learner recordings. "
        "The natural learner-speech problem has not been solved.",
        "**Hypothesis:** a small classifier on frozen speech representations can predict corpus numbered "
        "tones from audio on held-out speakers more accurately than the frozen acoustic-family scorer. "
        "The experiment tests this corpus-feasibility question separately from learner acceptability or "
        "product readiness.",
        "The validation-selected model is frozen Chinese HuBERT layer 9, ±250 ms context, nucleus-plus-coda "
        "frame-center mean pooling, and balanced multinomial logistic regression with C=0.1. "
        "It gets 160/177 test units correct (90.40%), balanced accuracy 89.30%, and macro F1 89.78%. "
        "Benma covers 114/177 (64.41%), abstains on 63, and gets 33/114 covered units correct (28.95%). "
        "On exactly those same 114 covered units, HuBERT gets 102/114 (89.47%).",
        "**Concentration is the main limitation:** SSB0043 supplies 164/177 units (92.66%), "
        "29/31 T3s (93.55%), and all 17 HuBERT errors. The other two speakers contribute only 4 and 9 units. "
        "The gain is numerically dominated by SSB0043; this cannot establish robust across-speaker generalization. "
        "No unit-level confidence interval is presented as a substitute for independent speakers.",
        "## Human QA and immutable release",
        "Round 2: **18/18 PASS for both whole units and tone-bearing targets**. Schema, packet hash, item hashes, "
        "reviewer, timestamps, context/final listening flags, completeness and uniqueness passed. "
        "Round 1 remains 18 PASS / 8 non-PASS; its history was not rewritten. A nested-label summary bug in the "
        "ingestion adapter was fixed and regression-tested; there was no alignment-integrity mismatch.",
        f"Dataset version: `{release['dataset_version']}`. Manifest SHA-256:\n\n`{release['manifest_sha256']}`.",
        "The release has 787 accepted units, 729 T1–T4 primary units, 58 preserved neutral units, and the original "
        "two >500 ms phone quarantines excluded. Original read-unit timing, reviewed nucleus/coda pooling, and "
        "short context remain separate. The old derived-span fields `eligible_for_training=false` and "
        "`ml_target_changed=false` are preserved pre-review evidence; release-level `primary_eligible` and the "
        "accepted representation govern this experiment. `training_started=false` records the release instant, "
        "not the current experiment status. The release was not rewritten after training.",
        f"[Release manifest and evidence](data/generated/aishell3/releases/{release['dataset_version']}/release.json) "
        "pin source subset/audio hashes, speaker registry, MFA 3.3.9, Mandarin MFA model 3.0.0, dictionary/config, "
        "lexicon audits, parser/reconstruction source, decimal half-up half-open sample extraction, "
        "nucleus/coda policy, both original QA exports and normalized decisions, and quarantines.",
        table(
            ["Partition", "T1", "T2", "T3", "T4", "Primary", "T5 retained"],
            [
                [
                    p,
                    *[release["class_counts"][p].get("T" + str(i), 0) for i in range(1, 5)],
                    sum(release["class_counts"][p].get("T" + str(i), 0) for i in range(1, 5)),
                    release["class_counts"][p]["T5"],
                ]
                for p in ("train", "validation", "test")
            ],
        ),
        "\n".join(f"- **{p}:** " + ", ".join(v) for p, v in release["speaker_split"].items()),
        "Speaker, utterance, source PCM and all 2,361 target/context/final derivative-audio checks passed. "
        "Each primary partition contains all four classes. Split membership was not changed.",
        "## Fixed protocol and feature inputs",
        "All 729 annotation-mutation checks passed before classifier training. Encoders receive only verified "
        "audio reference/hash and three numeric spans. Acoustic features use a fixed 86-column numeric schema: "
        "duration, existing contour geometry, family-noise/clarity/scale, voicing/projection metrics, acoustic "
        "family support, F0 contour quantiles, and missingness indicators. Tone, numbered/marked pinyin, Hanzi, "
        "expected tone and contextual acceptable families never enter primary feature matrices. Labels are "
        "used only as training targets or scoring metadata. Transcript-conditioned forced alignment remains "
        "an upstream assumption; mutation tests do not prove its timing is free of every annotation influence.",
        "[Protocol]("
        + runlink
        + "protocol.json), [feature schema]("
        + runlink
        + "acoustic-feature-schema.json), "
        "[selected models]("
        + runlink
        + "selected.json), and [all validation trials]("
        + runlink
        + "validation-trials.json) "
        "record exact source hashes, dependencies, hyperparameters, weighting and seed 20261017. "
        "Median imputation and scaling fit on train only; no train+validation refit. The LR search is C∈{0.1,1}, "
        "layers 6/9/12, target/context, mean pooling only. Selection order is validation macro F1, balanced "
        "accuracy, accuracy, then stable trial order. There were 29 attempted head configurations. "
        "Optional model 5 (phonetic identity) was omitted to keep this pass strictly audio-only.",
        "TencentGameMate/chinese-hubert-base revision "
        "`fce0375452b1dd6c080ac3248d423d4d037bc831`; microsoft/wavlm-base-plus revision "
        "`4c66d4806a428f2e922ccfa1a962776e232d487b`. Both encoders stay frozen in eval mode; "
        "three hidden layers are extracted in one forward pass. CPU, four torch/BLAS threads, deterministic "
        "torch operations. Whole utterances are polyphase-resampled to mono 16 kHz PCM16 before cropping. "
        "Target input is the original read-unit crop; context adds up to 250 ms on each side. "
        "Uniform 200-sample zero padding per edge is applied before the pinned feature extractor so the "
        "shortest accepted finals retain convolutional frame centers. Pooling timestamps are shifted by "
        "that padding; no neighboring frame centers are pooled. Contextual hidden states can still encode "
        "surrounding speech. Every used span has at least one owned center. HuBERT uses its pinned waveform "
        "normalization; WavLM uses its pinned no-normalization setting.",
        "Model 0 uses unchanged production Praat, pitch-track/display, raw-discontinuity and family functions "
        "on whole-read-unit timing. It is acoustic-family inference, not the contextual learner grade. "
        "Family supports are not calibrated probabilities. No production scorer compatibility rules changed.",
        "Label-free acoustic measurements and fixed baseline outputs were cached for all 729 units. "
        "Selection used train/validation rows only. Learned test embeddings, model predictions and "
        "all label-based test scoring followed the configuration/model freeze.",
        f"Selection/models frozen at `{selected['frozen_at']}`; test evaluation at `{result['evaluated_at']}`; "
        f"external probe began at `{probe['protocol']['started_at']}` after the test-result seal. "
        "No choices were changed from test errors or external predictions.",
        "A preflight test caught reuse of the corpus-only 44.1 kHz WAV decoder for canonical 16 kHz audio. "
        "The research adapter was fixed before any classifier fit; its failed preflight protocol is archived. "
        "No failed or successful test metrics were used for model selection.",
        "## Every validation configuration",
        "All speech configurations below use tone-bearing frame-center mean pooling. "
        "HuBERT context/layer 9/C=0.1 won because its validation macro F1, 95.1541%, was the highest "
        "across all 29 trials. Its validation accuracy was 95.5414% and balanced accuracy 95.0595%. "
        "Neither test accuracy nor external predictions were a selection criterion. "
        "WavLM's own winner was context/layer 6/C=0.1, validation macro F1 73.4715%.",
        table(
            [
                "Trial",
                "Family",
                "View",
                "Layer",
                "C",
                "Accuracy",
                "Balanced accuracy",
                "Macro F1",
                "T3 recall",
            ],
            [
                [
                    t["trial"],
                    NAMES[t["family"]],
                    t["config"].get("view", "—"),
                    t["config"].get("layer", "—"),
                    t["config"].get("C", "fixed MLP"),
                    *[
                        pct(t["validation"][k])
                        for k in ("accuracy", "balanced_accuracy", "macro_f1")
                    ],
                    pct(t["validation"]["per_tone"]["T3"]["recall"]),
                ]
                for t in trials
            ],
        ),
        "### Selected-family validation comparison",
        "Frozen Benma validation metrics below were calculated during finalization from its existing "
        "cached outputs for reporting only. It has no fitted or selected parameters. All learned "
        "validation metrics are the original, pre-test trial records.",
        table(
            ["Model", "Coverage", "Accuracy", "Balanced accuracy", "Macro F1", "T3 recall"],
            [
                [
                    NAMES[f],
                    pct(s["coverage"]),
                    *[pct(s[k]) for k in ("accuracy", "balanced_accuracy", "macro_f1")],
                    pct(s["per_tone"]["T3"]["recall"]),
                ]
                for f, s in {
                    "model0_benma": finalization["baseline_validation"],
                    **{f: v["validation"] for f, v in selected["models"].items()},
                }.items()
            ],
        ),
        "## Selected models on the sealed test set",
        table(
            [
                "Model",
                "Selected configuration",
                "Coverage",
                "Accuracy",
                "Balanced accuracy",
                "Macro F1",
                "T3 recall",
                "T3→T4 /31",
                "T3→T2 /31",
            ],
            [
                [
                    NAMES[f],
                    ("frozen" if f == "model0_benma" else str(selected["models"][f]["config"])),
                    pct(s["coverage"]),
                    *[pct(s[k]) for k in ("accuracy", "balanced_accuracy", "macro_f1")],
                    pct(s["per_tone"]["T3"]["recall"]),
                    f"{s['T3_to_T4']['count']} ({pct(s['T3_to_T4']['rate_all_T3'])})",
                    f"{s['T3_to_T2']['count']} ({pct(s['T3_to_T2']['rate_all_T3'])})",
                ]
                for f, s in metrics.items()
            ],
        ),
        "Benma accuracy, balanced accuracy, macro F1 and the recall column above are conditional on coverage. "
        "Its T3 recall is 4/20 covered (20.00%), or 4/31 total (12.90%). Its T3→T4 rate is 15/31 total "
        "(48.39%), or 15/20 covered (75%); T3→T2 is 1/31 total (3.23%), or 1/20 covered (5%). "
        "HuBERT has no abstentions: T3 recall 26/31 (83.87%), T3→T4 2/31 (6.45%), "
        "T3→T2 3/31 (9.68%). Thus T3→T2 increases while the much larger T3→T4 failure declines.",
        "A coverage-aware interpretation counts correct numbered decisions over all test units: "
        "Benma is 33/177 (18.64%), with 81 wrong numbered decisions and 63 abstentions. HuBERT is "
        "160/177 (90.40%), with 17 wrong decisions and no abstentions. This does not assume abstention "
        "has the same practical cost as a wrong confident prediction.",
        "The fixed MLP uses one 64-unit hidden layer, alpha=0.01, lbfgs, max_iter=400 and balanced train sample "
        "weights. Train accuracy is 100%, validation 94.90%, test 87.01%; its generalization gap and 13 "
        "high-confidence errors are worse than the selected LR. It offered no benefit. Combined embeddings "
        "+ acoustics also failed to improve validation and test over HuBERT LR. No convergence warnings "
        "occurred in the 29 head fits. WavLM emitted a torch attention-mask deprecation warning during "
        "extraction, without failed or nonfinite outputs.",
        "## Per-tone metrics and confusion matrices",
        "Rows are corpus T1/T2/T3/T4, columns predicted T1/T2/T3/T4. Benma matrices exclude abstentions; "
        "abstention counts and all-example recall are shown separately. Macro F1 always averages the fixed "
        "four classes; absent classes receive zero in per-speaker F1, so two tiny speakers have macro F1 "
        "0.75 despite perfect accuracy. Balanced accuracy averages present true classes.",
    ]
    for family, s in metrics.items():
        out += [
            "### " + NAMES[family],
            table(
                ["Tone", "Precision", "Covered recall", "F1", "All-example recall", "Abstentions"],
                [
                    [
                        tone,
                        pct(v["precision"]),
                        pct(v["recall"]),
                        pct(v["f1"]),
                        pct(v["recall_all"]),
                        v["abstentions"],
                    ]
                    for tone, v in s["per_tone"].items()
                ],
            ),
            table(
                ["Truth / prediction", "T1", "T2", "T3", "T4"],
                [["T" + str(i + 1), *r] for i, r in enumerate(s["confusion"])],
            ),
        ]
    out += [
        "## Held-out speakers",
        table(
            ["Model", "Speaker", "n", "T1/T2/T3/T4", "Covered", "Accuracy", "T3→T4", "T3→T2"],
            [
                [
                    NAMES[f],
                    speaker,
                    s["n"],
                    "/".join(str(s["class_counts"].get("T" + str(i), 0)) for i in range(1, 5)),
                    s["covered"],
                    pct(s["accuracy"]),
                    s["T3_to_T4"]["count"],
                    s["T3_to_T2"]["count"],
                ]
                for f, speakers in result["per_speaker"].items()
                for speaker, s in speakers.items()
            ],
        ),
        "HuBERT is 4/4 on SSB0038, 147/164 on SSB0043, and 9/9 on SSB0133. "
        "Benma is 3/4, 26/105 and 4/5 covered respectively. SSB0038 has no T1; SSB0133 has no T2. "
        "The 17 HuBERT errors all belong to SSB0043: five T1→T2, two T1→T4, four T2→T3, "
        "one T2→T4, three T3→T2, two T3→T4. All 54 test T4s are recovered.",
        "## Confidence and complete error review",
        "Probabilities are uncalibrated classifier outputs. No learner thresholds were created. "
        "The following confidence-bin counts are the histogram; all bins were fixed before test.",
    ]
    for family, s in metrics.items():
        if family == "model0_benma":
            continue
        out += [
            "### " + NAMES[family] + f" — {s['high_confidence_errors']} errors at confidence ≥0.8",
            table(
                ["Max-probability bin", "n", "Correct", "Incorrect", "Accuracy"],
                [
                    [
                        f"[{b['lower']:.2f}, {b['upper']:.2f}" + ("]" if b["upper"] == 1 else ")"),
                        b["n"],
                        b["correct"],
                        b["incorrect"],
                        pct(b["accuracy"]),
                    ]
                    for b in finalization["confidence"][family]["bins"]
                ],
            ),
        ]
    out += [
        "### Selected HuBERT high-confidence errors",
        table(
            ["Example", "Truth→prediction", "Confidence"],
            [
                [r["example_id"], r["truth"] + "→" + r["prediction"], pct(max(r["probabilities"]))]
                for r in finalization["confidence"]["model2_hubert"]["high_confidence_errors"]
            ],
        ),
        "The five error identities are also shown with all four probabilities and provenance below. "
        "[Finalization audit](reports/aishell3-finalization-audit.json) preserves exact bin counts and "
        "high-confidence error identities for every learned model.",
        "All 17 selected-model errors were inspected through their released timing/phone provenance, "
        "neighbors, probabilities and frozen acoustic evidence. This is a metadata/acoustic review, not "
        "a new native-listener label adjudication. Seven errors have confidence <0.6, five ≥0.8. "
        "Only 啄 has a flagged <60 ms final (30 ms). That is a sensitivity candidate, not proof of residual "
        "misalignment. Two T3 errors are utterance-final: 鸟→T2 and 使→T4. 宝宝 has a high-confidence "
        "T2/T3 reversal across adjacent units; label-order, actual realization and sandhi deserve a future "
        "independent audit. All tested labels, spans and predictions remain frozen. There is insufficient "
        "repeated segment/speaker evidence to infer a general segment-specific mechanism.",
        table(
            [
                "Speaker",
                "Utterance",
                "Example / unit",
                "Base",
                "Truth→pred",
                "P1/P2/P3/P4",
                "Whole / final ms",
                "Prev / next",
                "Benma",
                "Review",
            ],
            [
                [
                    r["speaker"],
                    r["utterance"],
                    r["example_id"] + " " + r["hanzi"],
                    r["phonetic_base"],
                    r["truth"] + "→" + r["prediction"],
                    "/".join(f"{v:.4f}" for v in r["probabilities"]),
                    f"{1000 * r['target_duration']:.0f} / {1000 * r['tone_bearing_duration']:.0f}",
                    f"{r['previous_tone'] or 'start'} / {r['next_tone'] or 'end'}",
                    r["baseline_prediction"] or "abstain",
                    ", ".join([*r["categories"], "SSB0043-concentration"]),
                ]
                for r in result["best_model_errors"]
            ],
        ),
        "[Full error records and per-speaker confusion matrices]("
        + runlink
        + "test-results.json). "
        "No errors were used to retune, quarantine or reclassify this test set.",
        "## External physical recordings — exploratory only",
        probe["protocol"]["pooling_limitation"],
        "The inventory covers 77 suitable units across the archived Stage-0 recordings and additional "
        "tone-feedback/classification physical fixtures. One grouped timing unit was excluded rather than "
        "split artificially. All six distinct archived 我想买这个 takes with verified audio and individual "
        "timings are included below (30 syllables). The two Google/phone-TTS takes are not claimed as human "
        "speech. This is the available archived evidence inventory, not a claim that every unindexed WAV "
        "on disk has been transcribed. Sources and full recording IDs are in the "
        "[sealed probe](" + runlink + "external-probe.json).",
        table(
            [
                "Take",
                "Unit",
                "P(T1)",
                "P(T2)",
                "P(T3)",
                "P(T4)",
                "Learned",
                "Confidence",
                "Frozen Benma",
            ],
            [
                [
                    r["recording"][:8],
                    r["syllable"],
                    *[f"{p:.4f}" for p in r["probabilities"]],
                    r["prediction"],
                    f"{max(r['probabilities']):.4f}",
                    r["baseline_prediction"] or "abstain",
                ]
                for r in probe["predictions"]
                if "我想买这个" in r["transcript"]
            ],
        ),
        "No current frozen 我 prediction in these six full-phrase takes is T4: they are T3 or abstentions. "
        "The earlier natural-我→T4 concern must not be attributed to a newer frozen T3 result. "
        "Two archived other-phrase 我 units do retain frozen T4 predictions:",
        table(
            ["Take / phrase", "Benma", "P(T1)", "P(T2)", "P(T3)", "P(T4)", "Learned"],
            [
                [
                    r["recording"][:8] + " " + r["transcript"],
                    r["baseline_prediction"],
                    *[f"{p:.4f}" for p in r["probabilities"]],
                    r["prediction"],
                ]
                for r in probe["predictions"]
                if r["syllable"] == "我" and r["baseline_prediction"] == "T4"
            ],
        ),
        "**Partial improvement, not a solved external failure:** 我要一个苹果 / 8faf1a90 changes from T4 "
        "to T3 (P3≈0.596). 我有一个苹果 / a5acd04c stays T4 (P4≈0.394, P2≈0.384, P3≈0.147). "
        "On human d7b27845, 我 is T3 but 想 becomes T1 and 买 T2; 4f1ab9ed retains 想→T4. "
        "Google/phone-TTS b8049b3e and cad88597 yield T2/T2/T3 on 我/想/买, compatible with a "
        "possible sandhi realization but not independently adjudicated here. Neutral 个 is outside the "
        "four-class task; its forced four-way probabilities cannot be treated as a tone error or grade. "
        "Naturalness, prosodic grouping and expected acceptability are not determined by lexical tone alone.",
        "This probe differs in microphone/environment, speaker population (the human learner takes "
        "do not constitute a new multi-speaker study), alignment provenance and pooling. It is "
        "exploratory external evidence, not a product-accuracy test or a matched-representation test "
        "of the AISHELL-3 model. The TTS phone-playback takes remain distinct from human learner speech.",
        "## Reproduction, validation and limits",
        "All five selected heads were serialized/reloaded and retrained with the frozen seed. Maximum "
        "test-probability delta is **0.0** for both reload and seeded refit. Fresh uncached HuBERT and "
        "WavLM speech extraction also reproduces the cached vectors exactly. Verified 2,562 training/test "
        "embedding cache entries and 2,361 released audio derivatives, including nonempty pooling. "
        "Temporary cache corruption is rejected. Canonical WAV/source corruption, annotation mutation, "
        "train-only preprocessing, metrics and immutable-release tampering tests pass.",
        "Exact tolerances: reload and cached prediction checks use absolute tolerance 1e-12; the "
        "previous seeded head-refit check used 1e-10; the previous fresh embedding check used 1e-6, "
        "all with rtol=0. Observed maximum differences were 0.0, so probabilities were numerically "
        "identical, not merely within tolerance. Seeded refits were not compared as serialized model "
        "bytes. Separately, 5,737 generated artifact files survived a repeat pipeline byte-identically, "
        "and all 1,176 historical evidence hashes stayed unchanged. Another 2,187 resampled model "
        "input/pooling audio comparisons confirmed no partition leakage. The finalization pass uses "
        "cached matrices and saved models only: zero new fits, configurations or encoder extractions.",
        f"{reproduction['python_tests']['passed']} Python tests and three Node research tests pass; scoped Ruff and `git diff --check` pass. "
        "All **413 frozen hashes remain unchanged** and the **63-example replay is byte-identical**. "
        "Only research files were changed. No F0, family scorer, grader, app/UI, API or inference integration "
        "was changed; no commit, push or deployment occurred. Large audio, embeddings and joblib models "
        "remain under ignored generated directories.",
        "The pre-trained encoders may have unknown corpus exposure; this pass does not establish absence "
        "of pretraining contamination. Corpus numbered pronunciation labels are not independent perceptual "
        "judgments; sandhi/label discrepancies remain possible. HuBERT can use spoken segment identity and "
        "surrounding lexical cues even without text inputs, so strong corpus-label prediction is not proof "
        "of purely acoustic tone perception. Sixteen corpus speakers, three very uneven test speakers, "
        "31 test T3s, small validation selection, oracle-like offline timing, future context, phone-recording "
        "domain shift, external pooling mismatch, absent neutral class and uncalibrated probabilities all "
        "limit deployment conclusions.",
        "**Smallest next experiment (proposed, not implemented):** expand the AISHELL-3 subset into a new "
        "version with balanced held-out speaker contributions and T3 examples across several held-out "
        "speakers. Keep the same frozen model methodology and selection discipline; evaluate the existing "
        "checkpoint on the new independent speakers before any new training choices. Preserve this test "
        "set as a completed experiment. A later, separate experiment should add reviewed learner recordings "
        "with matching nucleus/coda spans and realized-tone/sandhi judgments. No production integration.",
        "## Reproduction commands",
        "```sh\nPY=benchmark/pronunciation_v2/.venv/bin/python\n"
        "$PY research/perceptual-tone-model/scripts/aishell3_release.py --verify\n"
        "$PY research/perceptual-tone-model/scripts/aishell3_finalize.py\n"
        "$PY research/perceptual-tone-model/scripts/aishell3_report.py\n"
        "$PY research/perceptual-tone-model/scripts/aishell3_finalize.py --check-report\n"
        "# Historical full-pipeline commands below; finalization does not rerun training/extraction.\n"
        "OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 $PY research/perceptual-tone-model/scripts/aishell3_train.py\n"
        "OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 $PY research/perceptual-tone-model/scripts/aishell3_verify.py\n"
        "$PY research/perceptual-tone-model/scripts/aishell3_probe.py\n"
        "PYTHONPATH=research/perceptual-tone-model $PY -m unittest discover -s research/perceptual-tone-model/tests\n"
        "node --test research/perceptual-tone-model/test_aishell3_baseline.cjs research/perceptual-tone-model/test_native_baseline.cjs research/perceptual-tone-model/test_evaluate.cjs\n```",
        "[Machine summary](reports/aishell3-training-summary.json), "
        "[validation/reproduction record](reports/aishell3-training-validation.json), "
        "[changed research files](reports/aishell3-training-changed-files.txt).",
    ]
    (PACKAGE / "aishell3-training-report.md").write_text("\n\n".join(out) + "\n")
    summary = {
        "core_ml_feasibility": "CLEARLY PROMISING",
        "product_generalization": "MIXED / UNPROVEN",
        "release": release,
        "selected": selected,
        "test": result,
        "validation_trials": trials,
        "external_probe": probe,
        "reproduction": reproduction,
        "finalization": finalization,
        "artifact_hashes": {
            name: file_hash(folder / name)
            for name in (
                "protocol.json",
                "selected.json",
                "test-results.json",
                "test-seal.json",
                "external-probe.json",
                "external-probe-seal.json",
            )
        },
    }
    (PACKAGE / "reports/aishell3-training-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    render()
