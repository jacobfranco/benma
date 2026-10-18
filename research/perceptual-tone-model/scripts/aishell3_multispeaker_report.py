"""Render the completed, sealed generalization experiments without fitting or tuning."""
# ruff: noqa: E501, RUF001 -- report prose, table headers and intentional typography

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json
from aishell3_multispeaker_acquire import ROOT
from aishell3_multispeaker_train import RUN, checked_release, verify_experiment_a
from perceptual_tone.common import PACKAGE, file_hash, read_json


def pct(x):
    return "—" if x is None else f"{100 * x:.2f}%"


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        ]
    )


def render(outcome):
    release, info = checked_release(ROOT)
    verify_experiment_a(RUN)
    if file_hash(RUN / "test-results.json") != read_json(RUN / "test-seal.json")["sha256"]:
        raise ValueError("unsealed_test_results")
    result = read_json(RUN / "test-results.json")
    adjudication = read_json(release / "adjudication.json")
    scope = read_json(ROOT / "adjudication/scope-supplement.json")
    split = read_json(release / "split.json")
    acquisition = read_json(ROOT / "acquisition.json")
    validation = read_json(ROOT / "final-validation.json")
    models = result["results"]
    names = {
        "experiment_A": "A: unchanged pilot HuBERT",
        "experiment_B": "B: expanded fixed HuBERT",
        "deterministic_Benma": "Frozen deterministic Benma",
        "acoustic_LR": "Fixed acoustic LR",
    }
    out = [
        "# AISHELL-3 multi-speaker generalization — 2026-10-17",
        f"**Pass complete. Outcome: {outcome.replace('_', ' ')}. Research only.**",
        "Human spot-check adjudication, release and Experiment A were frozen before expanded-model training. "
        "No encoder, layer, context, pooling, classifier, C or grading threshold was selected from these tests.",
        "## Human decisions and adjudication",
        "The original 24-item export is preserved byte-for-byte: **22 final PASS / 2 CLIPPED**, "
        "and **23 whole-unit PASS / 1 BOTH**. The raw enums, notes, reviewer, timestamps, hashes and "
        "listening confirmations were ingested unchanged. Two uncertain final starts were quarantined. "
        "The whole-target outlier retains its explicit final PASS. No additional auditory judgments were "
        "fabricated; the assistant inspected alignment, exact sample exports and spectrograms.",
        table(
            ["Example", "Partition", "Unit", "Raw whole / final", "Classification", "Outcome"],
            [
                [
                    a["example_id"],
                    a["partition"],
                    a["hanzi"] + " " + a["pinyin"],
                    a["original_human_review"]["decision"]
                    + " / "
                    + a["original_human_review"]["final_decision"],
                    a["classification"],
                    a["outcome"],
                ]
                for a in adjudication["items"]
            ],
        ),
    ]
    for a in adjudication["items"]:
        out += [
            f"### {a['example_id']}",
            a["diagnosis"],
            f"Actual-reading label **{a['actual_reading_tone']}**; previous "
            f"{a['previous']['hanzi']} {a['previous']['corpus_pinyin']}; next "
            f"{a['next']['hanzi']} {a['next']['corpus_pinyin']}. "
            f"Whole interval {a['whole_seconds']}; pooling {a['pooling_seconds']} "
            f"({1000 * a['pooling_duration_seconds']:.0f} ms); context {a['context_seconds']}. "
            f"Pooling starts at the nucleus; neighbor phones included: {a['neighbor_phones_in_pool']}. "
            f"Source sample bounds: {a['pooling_sample_bounds']} at 44.1 kHz, half-open.",
            "MFA phones: `"
            + " / ".join(f"{p['phone']} {p['start']:.3f}–{p['end']:.3f}" for p in a["mfa_phones"])
            + "`. "
            "Pooled phones: `" + " / ".join(p["phone"] for p in a["tone_bearing_phones"]) + "`.",
            f"Whole and final WAV byte-identical: **{a['whole_and_final_wav_byte_identical']}**. "
            "No timestamp, phone inventory, padding, MFA or derivation changes.",
        ]
    impact = adjudication["full_corpus_impact"]
    out += [
        "### Corpus scope and gate",
        f"All {impact['primary_units_scoped']:,} pre-adjudication primary units were covered by the structural "
        f"integrity audit: **0 proven derivation/export defects**. {impact['same_single_phone_whole_equals_final_pattern']} "
        "units share the single-phone whole=final structure; only the two flagged units have that structure "
        "with duration at least 480 ms. This is descriptive, not a new duration rejection rule. "
        f"The complete MFA predecessor check finds {scope['count']} same-segment transitions. "
        "An append-only scope supplement corrects the earlier count of eight, which omitted the already "
        "quarantined 30 ms preceding yu2. It changes no adjudication, example membership or timestamp.",
        "**QA gate satisfied:** 22 direct final PASS (including the whole-target outlier) plus two explicit "
        "quarantines. Both quarantines are outside TEST (one train T3 and one validation T1). "
        "There is no demonstrated systematic ownership defect; automatic timing accuracy remains a limitation.",
        "## Acquisition and immutable release",
        f"Downloaded {acquisition['utterances']} individually selected publisher-mirror recordings, "
        f"{acquisition['audio_bytes']:,} audio bytes (119.69 MB), from **60 new verified speakers**. "
        "They are disjoint from all 16 historical pilot speakers: 76 verified speakers across both studies, "
        "60 in this release. The pinned mirror revision is `f20d5db4a31fe779ef07bb1af4ea92da5c786622`; "
        "speaker metadata and an overlap recording match retained official-source bytes exactly. "
        "Source: [publisher mirror](https://huggingface.co/datasets/AISHELL/AISHELL-3/tree/f20d5db4a31fe779ef07bb1af4ea92da5c786622), "
        "cross-checked against retained [OpenSLR 93](https://www.openslr.org/93/) bytes. "
        "No full-corpus download. File URLs, receipts, byte counts, SHA-256 and PCM provenance are retained "
        "in the acquisition manifest. The full official archive checksum is unavailable for this bounded acquisition.",
        "All 63,262 train transcript lines parsed. MFA 3.3.9 and Mandarin acoustic/dictionary 3.0.0 were reused. "
        "Twenty new dictionary-backed corrections resolve observed G2P failures using the pilot correction "
        "procedure; original corrections and corpus labels are unchanged. 227/227 utterances aligned. "
        "Automatic quarantine: 10 implausible read-unit durations and 1 extreme phone duration. "
        "Human adjudication adds 2 units, giving **13 total quarantines**.",
        f"Release **`{info['dataset_version']}`**: **{info['primary_numbered']:,} T1–T4 units + "
        f"{info['neutral']} neutral units**. Manifest SHA-256:\n\n`{info['manifest_sha256']}`.",
        f"Release descriptor SHA-256: `{file_hash(release / 'release.json')}`. "
        f"Final split SHA-256: `{file_hash(release / 'split.json')}`.",
        table(
            ["Partition", "Speakers", "T1", "T2", "T3", "T4", "Primary", "T5 retained"],
            [
                [
                    p,
                    len(s["speakers"]),
                    *[s["class_counts"].get(t, 0) for t in ("T1", "T2", "T3", "T4")],
                    s["primary"],
                    s["neutral"],
                ]
                for p, s in split["partitions"].items()
            ],
        ),
    ]
    out += [
        f"**{p}:** " + ", ".join(split["partitions"][p]["speakers"])
        for p in ("train", "validation", "test")
    ]
    out += [
        "<details><summary>All 60 speakers: partition and tone counts</summary>\n\n"
        + table(
            ["Speaker", "Partition", "T1", "T2", "T3", "T4", "T5"],
            [
                [speaker, d["partition"], *[d["counts"].get(f"T{i}", 0) for i in range(1, 6)]]
                for speaker, d in split["per_speaker"].items()
            ],
        )
        + "\n\n</details>"
    ]
    c = split["concentration"]
    out += [
        f"Test: {c['test_units']} units / {c['test_speakers']} speakers; {c['test_t3']} T3s across "
        f"{c['test_speakers_with_t3']} speakers. Largest speaker share **{pct(c['largest_test_speaker_share'])}**, "
        f"largest T3 speaker share **{pct(c['largest_test_t3_speaker_share'])}**; effective test speakers "
        f"{c['effective_test_speakers']:.2f}. Counts range from {min(c['test_sample_counts'].values())} to "
        f"{max(c['test_sample_counts'].values())}. This fixes the pilot's 92.66% overall / 93.55% T3 "
        "single-speaker concentration.",
        "## Frozen methods and chronology",
        "Chinese HuBERT revision `fce0375452b1dd6c080ac3248d423d4d037bc831`, context ±250 ms, hidden layer 9, "
        "owned nucleus/coda frame-center mean pooling, unchanged 200-sample edge padding, balanced "
        "multinomial LR C=0.1. Median imputation and scaling fit on train only. Validation reports sanity "
        "metrics, with no search or train+validation refit. The existing cache extracts layers 6/9/12 "
        "in one forward pass; only the fixed layer 9 enters either primary model.",
        f"A sealed at `{read_json(RUN / 'experiment-A-seal.json')['sealed_at']}`. "
        f"B heads frozen at `{read_json(RUN / 'models-frozen.json')['frozen_at']}`. "
        f"Final test seal at `{read_json(RUN / 'test-seal.json')['sealed_at']}`. "
        "A never retrained. B and acoustic LR used only expanded TRAIN. Secondary acoustic LR keeps the "
        "pilot's C=1.0. WavLM is omitted to avoid a second full encoder extraction; its earlier "
        "context/layer6/C0.1 configuration remains unchanged. No external Benma recording probe.",
        f"Validation sanity accuracy: B {pct(result['validation']['experiment_B']['validation']['accuracy'])}; "
        f"acoustic LR {pct(result['validation']['acoustic_LR']['validation']['accuracy'])}. No setting changed.",
        "## Overall results",
        table(
            [
                "Model",
                "Coverage",
                "Accuracy (covered)",
                "Balanced accuracy",
                "Macro F1 (covered)",
                "Correct / all",
                "T3 recall / all",
                "T3→T4",
                "T3→T2",
            ],
            [
                [
                    names[k],
                    pct(m["overall"]["coverage"]),
                    pct(m["overall"]["accuracy"]),
                    pct(m["overall"]["balanced_accuracy"]),
                    pct(m["overall"]["macro_f1"]),
                    pct(m["overall"]["correct_fraction_all"]),
                    pct(m["overall"]["per_tone"]["T3"]["recall_all"]),
                    f"{m['overall']['T3_to_T4']['count']}/167 ({pct(m['overall']['T3_to_T4']['rate_all_T3'])})",
                    f"{m['overall']['T3_to_T2']['count']}/167 ({pct(m['overall']['T3_to_T2']['rate_all_T3'])})",
                ]
                for k, m in models.items()
            ],
        ),
        f"Benma abstains on **{models['deterministic_Benma']['overall']['abstentions']}/915**. "
        "Benma precision/F1 and the covered-recall column below condition on covered examples; "
        "recall/all and correct/all include abstentions in their denominators. Learned models cover all examples.",
    ]
    for key, analysis in models.items():
        m = analysis["overall"]
        out += [
            f"### {names[key]}",
            table(
                ["Tone", "n", "Covered", "Precision", "Recall covered", "Recall/all", "F1"],
                [
                    [
                        t,
                        d["n"],
                        d["covered_n"],
                        pct(d["precision"]),
                        pct(d["recall"]),
                        pct(d["recall_all"]),
                        pct(d["f1"]),
                    ]
                    for t, d in m["per_tone"].items()
                ],
            ),
            "Confusion rows=true and columns=predicted, ordered T1/T2/T3/T4; abstentions excluded:",
            table(
                ["True / predicted", "T1", "T2", "T3", "T4"],
                [[f"T{i + 1}", *r] for i, r in enumerate(m["confusion"])],
            ),
            table(
                [
                    "Speaker",
                    "n",
                    "T1/T2/T3/T4",
                    "Covered",
                    "Accuracy",
                    "Macro F1",
                    "T3 correct/total",
                    "Confusions",
                ],
                [
                    [
                        s,
                        d["n"],
                        "/".join(
                            str(d["class_counts"].get(t, 0)) for t in ("T1", "T2", "T3", "T4")
                        ),
                        d["covered"],
                        pct(d["accuracy"]),
                        pct(d["macro_f1"]),
                        f"{d['t3_correct']}/{d['t3_total']}",
                        "; ".join(f"{k}: {v}" for k, v in d["major_confusions"].items()) or "none",
                    ]
                    for s, d in analysis["per_speaker"].items()
                ],
            ),
            "Unweighted speaker accuracy: "
            + ", ".join(f"{k} **{pct(v)}**" for k, v in analysis["speaker_accuracy"].items())
            + ".",
            table(
                ["T3 context", "n", "Correct", "Recall/all", "Predictions"],
                [
                    [k, d["n"], d["correct"], pct(d["recall_all"]), str(d["predictions"])]
                    for k, d in analysis["t3_context"].items()
                ],
            ),
        ]
        if "confidence_bins" in m:
            out += [
                table(
                    ["Confidence bin", "n", "Accuracy"],
                    [
                        [f"{b['lower']}–{b['upper']}", b["n"], pct(b["accuracy"])]
                        for b in m["confidence_bins"]
                    ],
                ),
                f"High-confidence errors (max probability ≥0.8): **{m['high_confidence_errors']}**. "
                "These are reporting bins, not learner grading thresholds. Probabilities have not been calibrated.",
                table(
                    ["True tone", "n", "Confidence min/Q1/median/Q3/max"],
                    [
                        [t, d["n"], "/".join(f"{v:.3f}" for v in d["quantiles_0_25_50_75_100"])]
                        for t, d in analysis["confidence_by_true_tone"].items()
                    ],
                ),
            ]
        if "speaker_bootstrap" in analysis:
            boot = analysis["speaker_bootstrap"]
            out += [
                "Speaker cluster bootstrap: 2,000 replicates, 12 independent speakers, 95% percentile intervals. "
                + "; ".join(f"{k}: {pct(v[0])}–{pct(v[1])}" for k, v in boot["intervals"].items())
                + "."
            ]
    out += [
        "## Expanded-model error patterns",
        "Descriptive only; no retuning or exclusions from these errors.",
        "```json\n"
        + json.dumps(models["experiment_B"]["error_groups"], ensure_ascii=False, indent=2)
        + "\n```",
        "Complete error records, per-speaker metrics, confidence distributions, contextual breakdowns and "
        "bootstrap intervals are preserved in [the machine summary](reports/aishell3-multispeaker-summary.json). "
        "Phrase position is used only for the 214/227 utterances whose auxiliary prosody matches exactly; "
        "13 mismatches remain unattached. Phrase/next-tone groups overlap and must not be summed.",
        "## Old pilot comparison and interpretation",
        table(
            [
                "Study",
                "Primary units",
                "Speakers",
                "Test speakers",
                "Test accuracy",
                "Macro F1",
                "T3 recall",
            ],
            [
                ["Preserved pilot", 729, 16, 3, "90.40%", "89.78%", "83.87%"],
                [
                    "A: old head, new speakers",
                    4452,
                    60,
                    12,
                    *[pct(models["experiment_A"]["overall"][k]) for k in ("accuracy", "macro_f1")],
                    pct(models["experiment_A"]["overall"]["per_tone"]["T3"]["recall"]),
                ],
                [
                    "B: fixed method, expanded train",
                    4452,
                    60,
                    12,
                    *[pct(models["experiment_B"]["overall"][k]) for k in ("accuracy", "macro_f1")],
                    pct(models["experiment_B"]["overall"]["per_tone"]["T3"]["recall"]),
                ],
            ],
        ),
        "Pilot T3→T4 remains 2/31 and its manifest remains "
        "`8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f`. "
        "The historical report, model files, decisions, predictions and splits are unchanged.",
    ]
    if outcome == "STRONGLY_REPLICATED":
        out += [
            "A is 0.89 percentage points below the old 90.40% despite zero retraining. B is 90.38%, "
            "with T3 recall improved to 91.02%. Both learned models outperform Benma's covered accuracy "
            "for every test speaker as well as in aggregate. This supports strong replication of the "
            "learned advantage, not uniform speaker performance: B's lowest speaker is still 75.00%. "
            "A and B uncertainty intervals overlap; this pass does not establish a precise overall "
            "gain from the larger training set. B has 39 high-confidence errors versus A's 30, "
            "and lower T3 precision despite higher recall.",
            "**Learned connected-speech tone recognition has replicated across a substantially more "
            "diverse held-out AISHELL-3 speaker set.**",
            "**The next research bottleneck is learner-domain transfer rather than native connected-speech "
            "tone recognition.** The smallest next step is a separate, reviewed learner-domain dataset "
            "with legitimate nucleus/coda timing and realized-tone judgments, keeping this corpus test frozen.",
        ]
    else:
        out += [
            f"**{outcome.replace('_', ' ')}.** Do not proceed to production; diagnose speaker variance "
            "in a separately planned follow-up without tuning this test."
        ]
    out += [
        "## Limits, validation and production freeze",
        "This is native connected-speech corpus-label prediction, not learner grading or native-listener "
        "acceptability. Sixty speakers were selected from the available pinned mirror, with pre-split tone "
        "coverage selection; this is not a probability sample of Mandarin speakers or natural tone prevalence. "
        "There are only 12 independent test speakers. Encoder pretraining exposure is unknown. "
        "Text-conditioned forced alignment and context/segment cues remain potential sources of information "
        "beyond pure tone acoustics. Same-corpus lexical/prosodic regularities, offline future context, sparse "
        "per-speaker T3 denominators, no T5 classifier, uncalibrated confidence and no learner-domain evaluation "
        "limit transfer claims. Structural ownership checks do not prove every acoustic boundary; the two "
        "uncertain human findings were excluded without pretending to resolve their sound identity.",
        "Validation:\n\n```json\n" + json.dumps(validation, ensure_ascii=False, indent=2) + "\n```",
        "All 413 frozen deterministic baseline hashes and the 63-example replay are unchanged. "
        "All 11,719 historical evidence files retain their hashes. Only new research files were added. "
        "No pronunciation UI, grading, F0, family scorer, production inference/API or deployment change. "
        "No commit, push or deployment.",
        "## Reproduction commands",
        "```sh\nPY=benchmark/pronunciation_v2/.venv/bin/python\nP=research/perceptual-tone-model\n"
        "$PY $P/scripts/aishell3_multispeaker_verify.py\n"
        "$PY $P/scripts/aishell3_multispeaker_train.py verify-a\n"
        "# Completed experiments return verified sealed results; do not select new configurations.\n"
        "$PY $P/scripts/aishell3_multispeaker_train.py experiment-a\n"
        "$PY $P/scripts/aishell3_multispeaker_train.py experiment-b\n"
        "$PY $P/scripts/aishell3_multispeaker_reproduce.py\n```",
    ]
    summary = {
        "outcome": outcome,
        "release": info,
        "split": split,
        "adjudication": adjudication,
        "scope_supplement": scope,
        "acquisition": {k: v for k, v in acquisition.items() if k != "members"},
        "results": models,
        "validation": validation,
        "pilot_unchanged": True,
        "external_probe": "not_run",
        "production_changes": False,
    }
    stable_json(PACKAGE / "reports/aishell3-multispeaker-summary.json", summary)
    (PACKAGE / "aishell3-multispeaker-generalization-report.md").write_text("\n\n".join(out) + "\n")
    changed = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "research/perceptual-tone-model"],
        text=True,
    )
    inventory_path = PACKAGE / "reports/aishell3-multispeaker-changed-files.txt"
    inventory = set(changed.splitlines()) | {
        "research/perceptual-tone-model/reports/aishell3-multispeaker-changed-files.txt"
    }
    inventory_path.write_text("\n".join(sorted(inventory)) + "\n")
    print(PACKAGE / "aishell3-multispeaker-generalization-report.md")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--outcome",
        required=True,
        choices=["STRONGLY_REPLICATED", "PARTIALLY_REPLICATED", "NOT_REPLICATED"],
    )
    render(p.parse_args().outcome)
