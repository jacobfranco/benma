"""Render the sealed learner QA/evaluation artifacts; never infer or select models."""
# ruff: noqa: E501 -- report prose and wide table cells

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from perceptual_tone.common import PACKAGE, read_json, read_rows, write_json
from perceptual_tone.learner_release import RELEASE, RUN, verify_release


def table(columns, rows):
    rows = list(rows)
    if any(len(row) != len(columns) for row in rows):
        raise ValueError("report_table_width_mismatch:" + str(columns))

    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    return "\n".join(
        ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        + ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    )


def tone(value):
    return "unknown/unresolved" if value is None else "neutral" if value == 5 else f"T{value}"


def prediction(row, name):
    item = row[name]
    return item["prediction"] or "ABSTAIN"


def agreement(model, key="expected_surface_tone"):
    value = model[key + "_agreement"]
    if not value["resolved_numbered_n"]:
        return "N/A; 0 resolved"
    return (
        f"{value['matches']}/{value['covered_n']} covered; {value['resolved_numbered_n']} resolved"
    )


def confidence_stats(rows, name):
    values = [r[name]["confidence"] for r in rows]
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "count_ge_0_80": sum(v >= 0.8 for v in values),
        "count_ge_0_90": sum(v >= 0.9 for v in values),
    }


def report():
    seal = verify_release()
    manifest = read_json(RELEASE / "release-manifest.json")
    acceptance = read_json(RELEASE / "review-acceptance.json")
    units = read_rows(RELEASE / "all-units.jsonl")
    master = read_rows(RELEASE / "selected-take-provenance.jsonl")
    aliases = {}
    for take in master:
        names = [Path(s["path"]).stem for s in take["sources"]]
        aliases[take["source_id"]] = next(
            (n for n in names if n in ("S01", "S02", "S03", "S13")), take["names"][0][:8]
        )
    phases = {
        p: read_rows(RUN / p / "predictions.jsonl") for p in ("primary", "diagnostic", "unknown")
    }
    summaries = {p: read_json(RUN / p / "summary.json") for p in phases}
    primary = sorted(phases["primary"], key=lambda r: (aliases[r["source_id"]], r["index"]))
    comparisons = read_rows(RUN / "representation-comparison/predictions.jsonl")
    comparison = {r["example_id"]: r for r in comparisons}
    historical = read_rows(RELEASE / "historical-special-cases.jsonl")
    historical_ids = {r["example_id"] for r in historical}
    historical_rows = [r for r in phases["unknown"] if r["example_id"] in historical_ids]
    old_baselines = read_rows(
        PACKAGE / "data/generated/learner-alignment-v1/historical-benma.jsonl"
    )
    old_by_id = {
        (r["recording_id"], r["target"]["syllable_index"]): r
        for r in old_baselines
        if r["target"]["unit_kind"] == "syllable"
    }
    text = [
        "# Learner QA acceptance, frozen release and transfer evaluation — 2026-10-19",
        "",
        "**MIXED TRANSFER, provisionally.** The expanded model has useful signal but substantial "
        "disagreement with expectations and the pilot. Legitimate nucleus/coda pooling does not "
        "demonstrate a general material improvement over the earlier whole-syllable probe. "
        "A separate blinded realized-tone annotation stage is necessary before judging acoustic "
        "correctness or product utility. No model was trained, adapted or reselected.",
        "This report supersedes the earlier pending-QA handoff reports. The finishing continuation "
        "reuses all completed release, inference, comparison and reproduction artifacts; it performs "
        "no new encoder extraction, native-corpus work or model selection.",
        "",
        "The completed learner QA was accepted from the draft using substantive judgments as "
        "authoritative and playback telemetry as provenance-only.",
        "",
        "**Ingestion and acceptance.** Schema, packet hash, all 123 unique item IDs, item hashes, "
        "unit/source identity, reviewer Jacob, 123 whole judgments, 123 tone judgments, and notes "
        "for every non-PASS were validated. Zero substantive decisions are missing. "
        f"Raw draft SHA-256: `{acceptance['raw_draft_sha256']}`. "
        "The byte-identical draft and original developer request are preserved in the release. "
        "All note strings and recorded flags remain unchanged.",
        "",
        table(["Telemetry false", "Count"], acceptance["false_playback_counts"].items()),
        "",
        "`accepted_by_developer_attestation = true`; `playback_telemetry_complete = false`. "
        "Every heard_all=false item also has context=false; whole=false and tone=false overlap "
        "that set. Context was optional in actual use, and whole/tone telemetry did not reliably "
        "register. No missing playback event is inferred. No flag excludes an evaluation unit. "
        "The research validator and new research review page require reviewer, whole decision, "
        "tone decision, and non-PASS notes. Missing-field errors identify the exact field and item. "
        "The original reviewed page is preserved; the updated page is under "
        "`data/generated/learner-transfer-v1-20261019/review-with-optional-telemetry/qa/index.html`. "
        "Production UI is unchanged.",
        "",
        table(
            ["Whole decision", "Count"],
            [
                (k, acceptance["whole_decisions"].get(k, 0))
                for k in ("PASS", "START ISSUE", "END ISSUE", "BOTH", "WRONG UNIT")
            ],
        ),
        "",
        table(
            ["Tone-bearing decision", "Count"],
            [
                (k, acceptance["tone_decisions"].get(k, 0))
                for k in ("PASS", "TOO LITTLE MATERIAL", "WRONG UNIT", "CONTAMINATED", "CLIPPED")
            ],
        ),
        "",
        "**Adjudication and alignment audit.** 21 whole non-PASS and 21 tone non-PASS produce "
        "22 unique units. Q037 (不) has a whole onset objection and tone PASS: PASS_AS_IS. "
        "Q073 (去) has whole PASS and tone TOO LITTLE MATERIAL: QUARANTINE_UNIT. "
        "All 21 tone non-PASS units are quarantined. Of 32 natural candidates, **17 are implicated**, "
        "including Q037; 16 are quarantined and 16 accepted. Automatic flags are review evidence, "
        "not automatic exclusions. No timestamps or source clips were changed.",
        "",
        "**Systematic bug found: no demonstrated general defect. Repaired: 0.** All 123 saved "
        "units reconstruct from existing TextGrids with exact word/phone ownership, nested spans, "
        "and nucleus/coda projection; all 369 clips equal source samples. This checks representation "
        "integrity, not acoustic correctness of forced alignment. The high natural quarantine rate "
        "and wrong-unit judgments show substantial crop usability problems. Their cause remains "
        "unresolved between alignment limitations and learner production; no general correction "
        "is established. Short spans do not prove a bug, and no span was widened to preserve N. "
        "No re-review packet is needed because no crop changed.",
        "",
        "**Full 22-unit adjudication inventory.** Labels are intended lexical / expected surface; "
        "unknown/unresolved is not a realized-tone judgment. Notes below are the developer's "
        "original strings; the immutable JSONL preserves exact whitespace. Durations are milliseconds.",
        "",
    ]
    adjudication = sorted(
        [u for u in units if u["adjudication_required"]], key=lambda u: u["qa_item_id"]
    )
    text.append(
        table(
            [
                "QA",
                "Source / take",
                "Phrase",
                "Target / pinyin",
                "Intended / contextual",
                "Provenance",
                "Whole / tone decision",
                "Developer note (verbatim)",
                "Automatic flags",
                "Whole / tone ms",
                "Adjudication",
            ],
            [
                [
                    u["qa_item_id"],
                    u["source_id"] + " / " + aliases[u["source_id"]],
                    u["intended_phrase"] or u["transcript"],
                    u["hanzi"] + " / " + u["alignment_pinyin"],
                    tone(u["intended_lexical_tone"]) + " / " + tone(u["expected_surface_tone"]),
                    u["provenance_category"],
                    u["qa"]["whole"] + " / " + u["qa"]["tone"],
                    u["qa"]["notes"],
                    "; ".join(u["alignment_flags"]) or "none",
                    f"{u['whole_duration_seconds'] * 1000:.0f} / {u['tone_duration_seconds'] * 1000:.0f}",
                    u["adjudication"],
                ]
                for u in adjudication
            ],
        )
    )
    text += [
        "",
        "**Frozen sets.**",
        "",
        table(
            ["Set", "Candidates", "Accepted", "Quarantined"],
            [
                [p, c["candidate"], c["accepted"], c["quarantined"]]
                for p, c in manifest["counts"].items()
            ],
        ),
        "",
        f"Release: `{seal['version']}`. Manifest SHA-256: `{seal['manifest_sha256']}`. "
        "Write-once creation, read-only artifact files, a manifest inventory and per-file hash checks "
        "enforce release integrity. The manifest covers source hashes, original spans, context, "
        "take provenance, labels, raw review, attestation, all adjudications and quarantines. "
        "Its three sets are disjoint; historical-special-cases.jsonl is a labeled view of supplemental "
        "records, not extra independent data. All six short 我想买 recordings retain UNKNOWN_PROVENANCE. "
        "Unknown human identity/intent is not upgraded. Controls remain excluded.",
        "",
        "**Frozen inference.** Expanded AISHELL-3 Chinese HuBERT and the original pilot: frozen "
        "encoder, context input, layer 9, owned nucleus/coda frame-center mean, balanced logistic "
        "regression C=0.1. The existing encoder preprocessing and 200-sample edge padding are "
        "unchanged. Text, expected labels, QA notes and provenance never enter the encoder. "
        "Primary results were sealed before diagnostic/unknown inference or representation comparisons. "
        "Four-way outputs do not model neutral tone. All confidence values are maximum classifier "
        "probabilities, not validated learner calibration. Frozen deterministic Benma uses the unchanged "
        "Praat analyzer and acoustic-family functions on accepted whole spans; it can abstain. "
        "These are fresh research acoustic outputs, not production grading or historical saved crops.",
        "",
        table(
            ["Model", "SHA-256"],
            [
                (name, spec["sha256"])
                for name, spec in read_json(RELEASE / "inference-config.json")["models"].items()
            ],
        ),
        "",
        "**Every accepted primary-natural syllable.** Take IDs and phrases are mapped in the next "
        "table; # is the original one-based syllable position, so quarantined gaps remain visible. "
        "Probabilities are displayed to six decimals; full precision is in primary/predictions.jsonl. "
        "No disagreement is removed.",
        "",
        table(
            [
                "QA / unit ID",
                "Take / #",
                "Target / tone-stripped pinyin",
                "Lexical / surface",
                "Whole / tone ms",
                "P(T1)",
                "P(T2)",
                "P(T3)",
                "P(T4)",
                "Expanded / confidence",
                "Pilot / confidence",
                "Deterministic / reason",
            ],
            [
                [
                    r["qa_item_id"] + " / " + r["example_id"],
                    aliases[r["source_id"]] + f" / {r['index'] + 1}",
                    r["hanzi"] + " / " + r["pinyin"],
                    tone(r["intended_lexical_tone"]) + " / " + tone(r["expected_surface_tone"]),
                    f"{r['whole_duration_seconds'] * 1000:.0f} / {r['tone_duration_seconds'] * 1000:.0f}",
                    *[f"{v:.6f}" for v in r["expanded"]["probabilities"]],
                    f"{r['expanded']['prediction']} / {r['expanded']['confidence']:.6f}",
                    f"{r['pilot']['prediction']} / {r['pilot']['confidence']:.6f}",
                    prediction(r, "deterministic")
                    + " / "
                    + r["deterministic"]["observed"]["reason"],
                ]
                for r in primary
            ],
        ),
        "",
        "**DESCRIPTIVE primary agreement.** Of 16 accepted units, intended lexical labels have "
        "15 numbered tones and one neutral. Expected surface labels have 10 resolved numbered tones, "
        "one neutral and five unresolved T3-chain cases. Neutral and unresolved labels are reported "
        "but excluded from numbered-tone agreement denominators. All realized acoustic labels remain UNKNOWN.",
        "",
        table(
            [
                "Model",
                "Lexical agreement",
                "Expected-surface agreement",
                "Numbered outputs / abstentions",
            ],
            [
                [
                    name,
                    agreement(m, "intended_lexical_tone"),
                    agreement(m),
                    f"{m['covered']} / {m['abstentions']}",
                ]
                for name, m in summaries["primary"]["models"].items()
            ],
        ),
        "",
        "Expanded vs pilot: 9/16 agree (56.25%). Expanded vs deterministic: 1/2 jointly covered "
        "agree; pilot vs deterministic: 0/2. Deterministic has 0/2 lexical matches and 0/1 expected "
        "surface matches among covered units; coverage is only 2/16. Abstentions are not counted "
        "as numbered-tone errors. None of these quantities measures realized-tone accuracy.",
        "",
        "**Each natural take.** Sequences include accepted units in source order only.",
        "",
    ]
    take_rows = []
    for ident in sorted(summaries["primary"]["takes"], key=aliases.get):
        t = summaries["primary"]["takes"][ident]
        take_rows.append(
            [
                aliases[ident] + " / " + ident,
                t["phrase"],
                t["n"] + t["quarantined"],
                f"{t['n']} / {t['quarantined']}",
                t["models"]["expanded"]["expected_surface_tone_agreement"]["resolved_numbered_n"],
                " ".join(r["hanzi"] for r in primary if r["source_id"] == ident),
                " ".join(t["sequences"]["expanded"]),
                " ".join(t["sequences"]["pilot"]),
                " ".join(v or "—" for v in t["sequences"]["deterministic"]),
                agreement(t["models"]["expanded"]),
                agreement(t["models"]["pilot"]),
                f"{t['model_agreement']['expanded_vs_pilot']['matches']}/{t['n']}",
                f"{t['models']['expanded']['confidence']['mean']:.3f} / {t['models']['pilot']['confidence']['mean']:.3f}",
            ]
        )
    text += [
        table(
            [
                "Take / source ID",
                "Phrase",
                "Pre-QA",
                "Accepted / quarantined",
                "Resolved expected numbered",
                "Accepted characters",
                "Expanded sequence",
                "Pilot sequence",
                "Deterministic sequence",
                "Expanded expected agreement",
                "Pilot expected agreement",
                "Expanded/pilot agreement",
                "Mean confidence expanded / pilot",
            ],
            take_rows,
        ),
        "",
        "S01: both models disagree with expected T1 for both accepted 天 syllables. Expanded 不→T2 "
        "agrees with the contextual 不-before-T4 expectation; pilot 不→T4 agrees with lexical tone. "
        "Expanded 我→T2 differs from pilot T3. The accepted 30 ms 不 remains supported by human tone "
        "PASS, not by its high model confidence. Its whole onset objection remains recorded. "
        "S02: both models produce 我→T3 while frozen deterministic returns T4; expanded 天→T2 and "
        "晚→T2 disagree with expected T1/T3, while pilot matches those expectations. "
        "S03: none of its four accepted expected surface tones is resolved because prosodic T3 "
        "grouping was not adjudicated. Expected-tone agreement is therefore N/A, not zero. "
        "种 differs between expanded T2 (also deterministic T2) and pilot T1; 水 is T1 in both "
        "learned models despite lexical T3. These require realized-tone evidence.",
        "",
        "**Confidence.**",
        "",
        table(
            [
                "Model",
                "Min / median / mean / max",
                "[.25,.5) / [.5,.8) / [.8,.9) / [.9,1]",
                "Count ≥ .80 / ≥ .90",
                "Expected disagreements at confidence ≥ .8",
            ],
            [
                [
                    name,
                    " / ".join(
                        f"{m['confidence'][k]:.3f}" for k in ("min", "median", "mean", "max")
                    ),
                    " / ".join(str(v) for v in m["confidence"]["bins"].values()),
                    f"{sum(r[name]['confidence'] >= 0.8 for r in primary)} / {sum(r[name]['confidence'] >= 0.9 for r in primary)}",
                    m["confidence"]["expected_numbered_disagreements_at_least_0_8"],
                ]
                for name, m in summaries["primary"]["models"].items()
                if "confidence" in m
            ],
        ),
        "",
        "Expanded confidence is higher despite lower expected-tone agreement. Three expanded "
        "expected-numbered disagreements have confidence ≥0.8 (S01 second 天 and 我; S02 天), "
        "versus one for the pilot (S01 second 天). These are disagreements, not established errors. "
        "No confidence threshold was fitted. Deterministic family supports are not probabilities.",
        "",
        "**Exploratory supplemental results, frozen after primary.**",
        "",
        table(
            ["Set", "Model", "Expected agreement", "Coverage / abstentions"],
            [
                [phase, name, agreement(m), f"{m['covered']} / {m['abstentions']}"]
                for phase in ("diagnostic", "unknown")
                for name, m in summaries[phase]["models"].items()
            ],
        ),
        "",
        "Many supplemental intended labels are unknown. Contextual expectations may use recorded "
        "reading hypotheses, not independently verified intended text. Diagnostic intended targets "
        "can deliberately differ from the spoken unit. None of these rows enters primary statistics.",
        "",
        "**Historical 我 and 我想买这个.** All five non-control 我想买这个 takes are separately "
        "reported; three 个 units are quarantined. The five takes contribute 22 accepted / 3 "
        "quarantined units. The two prior 我→T4 takes contribute 11 accepted / 1 quarantined unit "
        "across their phrases (contaminated 一 is quarantined). The seven-take historical view "
        "therefore has 33 accepted / 4 quarantined units, already included in unknown provenance. "
        "The two TTS/control takes are excluded. Full historical accepted sequences follow.",
        "",
    ]
    historical_sequences = []
    for ident in sorted({r["source_id"] for r in historical_rows}, key=aliases.get):
        rows = sorted(
            [r for r in historical_rows if r["source_id"] == ident], key=lambda r: r["index"]
        )
        historical_sequences.append(
            [
                aliases[ident],
                rows[0]["transcript"],
                " ".join(r["hanzi"] for r in rows),
                " ".join(prediction(r, "expanded") for r in rows),
                " ".join(prediction(r, "pilot") for r in rows),
                " ".join(prediction(r, "deterministic") for r in rows),
                len([u for u in historical if u["source_id"] == ident and u["quarantined"]]),
            ]
        )
    text += [
        table(
            [
                "Take",
                "Phrase",
                "Accepted characters",
                "Expanded",
                "Pilot",
                "Fresh deterministic",
                "Quarantined",
            ],
            historical_sequences,
        ),
        "",
    ]
    historical_wo = []
    for row in phases["diagnostic"] + phases["unknown"]:
        if row["hanzi"] != "我":
            continue
        c = comparison[row["example_id"]]
        old = c["prior_external_whole"]
        old_d = old_by_id.get((row["source_id"], row["index"]))
        historical_wo.append(
            [
                aliases[row["source_id"]] + " / " + row["source_id"],
                row["transcript"],
                row["provenance_category"],
                tone(row["intended_lexical_tone"]) + " / " + tone(row["expected_surface_tone"]),
                old_d["deterministic"]["observed_family"]
                if old_d
                else (old["baseline_prediction"] or "ABSTAIN / " + old["baseline_decision"])
                if old
                else "not archived",
                (old["prediction"] + f" / {max(old['probabilities']):.3f}")
                if old
                else "not in prior probe",
                f"{c['controlled_whole']['pilot']['prediction']} / {c['controlled_whole']['pilot']['confidence']:.3f}",
                f"{row['pilot']['prediction']} / {row['pilot']['confidence']:.3f}",
                f"{row['expanded']['prediction']} / {row['expanded']['confidence']:.3f}",
                prediction(row, "deterministic"),
                ("YES" if old["prediction"] != row["pilot"]["prediction"] else "no")
                if old
                else "no prior comparison",
            ]
        )
    text += [
        table(
            [
                "Every accepted supplemental 我: take / source",
                "Phrase",
                "Provenance",
                "Intended / expected tone",
                "Archived deterministic 我",
                "Prior pilot whole / confidence",
                "Same-context pilot whole / confidence",
                "Pilot nucleus/coda / confidence",
                "Expanded nucleus/coda / confidence",
                "Fresh deterministic 我",
                "Prior→reviewed pilot argmax changed",
            ],
            sorted(historical_wo),
        ),
        "",
        "Pilot a5acd04c 我 changes from prior T4 (.394) to T3 (.397); its probabilities remain "
        "diffuse and the expanded model predicts T4 (.866). Pilot 8faf1a90 我 was already T3 (.596), "
        "and remains T3 (.989), with expanded T3 (.811) and fresh deterministic T4. "
        "For 89cee47e 我, pilot changes prior T2 (.600) to T3 (.722), while expanded predicts T2 "
        "(.583). This is a changed conclusion for particular exploratory outputs, not proof that "
        "the earlier perceptual conclusion was wrong or that natural T3 is now reliably recognized. "
        "Fresh deterministic a5acd04c is T1 on the new whole span; the archived T4 remains preserved "
        "as a separate result on earlier timing. bb27924c was not in the earlier learned probe.",
        "",
        "**Representation question.** No general material improvement is demonstrated. "
        "64 accepted units overlap the prior pilot probe (59 unknown-provenance, 5 diagnostic). "
        "15/64 pilot argmaxes change. Among 32 matched units with resolved numbered expectations, "
        "prior expected agreement is 19/32 and current nucleus/coda agreement is 15/32; intended "
        "lexical labels are unknown for all 64. These are not primary natural results. Prior source "
        "segmentation and context also differ, so this comparison cannot isolate pooling.",
        "",
        "A controlled exploratory comparison keeps the newly reviewed whole span and context "
        "fixed and changes only pooling. It excludes Q037 from aggregate comparisons because its "
        "whole crop is non-PASS. On the remaining 15 primary units (9 resolved expected numbered "
        "tones), expanded expected agreement stays 4/9 and pilot stays 7/9. Expanded changes "
        "4/15 argmaxes; pilot changes 1/15. Lexical agreement changes 7/14→5/14 for expanded and "
        "10/14→9/14 for pilot. This does not justify switching the frozen configuration. All "
        "controlled whole outputs, including Q037 marked unsuitable for aggregate whole comparison, "
        "are retained. On unknown supplemental units, same-context whole→nucleus expected agreement "
        "changes 30/43→26/43 for expanded and 21/43→23/43 for pilot.",
        "",
        "**Domain-transfer question: MIXED TRANSFER (provisional).** Coherent examples exist, "
        "including S02 我, 跟 and 去, and some historical cases. But expected agreement, cross-model "
        "agreement and take behavior do not support a strong transfer claim. Expanded is below "
        "pilot on this descriptive comparison, with several high-confidence disagreements. "
        "Neither model was reselected based on learner results. Three takes from one documented "
        "speaker, only 16/32 surviving units, unresolved sandhi, neutral outside the model and "
        "absent realized-tone labels make both generalization and calibration claims premature. "
        "The accepted subset is selected for crop usability, not a representative random sample.",
        "The sealed native-domain expanded-model result remains strong: 90.38% corpus-test "
        "classification accuracy and 90.17% balanced accuracy in "
        "`aishell3-multispeaker-generalization-report.md`. Those native corpus metrics are not "
        "learner realized-tone metrics and were not rerun. The hypothesis that mixed learner "
        "results were caused mainly by approximate whole-syllable pooling is not supported. "
        "A native-to-learner domain-transfer uncertainty therefore remains.",
        "",
        "**Exact next research step: BLINDED LEARNER REALIZED-TONE ANNOTATION / PERCEPTUAL "
        "VALIDATION.** Design that stage separately under the project's zero-budget constraint; "
        "do not assume paid annotators. Establish perceived/realized tone families independently "
        "of intended phrase, expected lexical tone and either model's output. Avoid model-output "
        "leakage. This stage is necessary because learner production may itself differ from "
        "expectations, and current agreement cannot separate learner production from model failure. "
        "No annotation protocol or new annotation UI is implemented here. Realized-tone ground "
        "truth is the main bottleneck; do not train learner models before resolving it.",
        "",
        "**Reproduction and validation.** Both frozen classifiers were independently reloaded for "
        "all 102 accepted nucleus/coda units and all 102 whole-pooling controls. Maximum probability "
        "delta was 0.0. Fresh encoder extraction without cache reuse on one accepted unit per "
        "each of the 22 takes had maximum vector delta 0.0. Full deterministic extraction and "
        "classification reproduced exactly for all 102 accepted units. No fitting was performed. "
        "Phase result seals link primary-before-supplemental execution to the immutable release. "
        "The initial primary attempt stopped on a missing dependency in the research Python "
        "environment before deterministic output or result sealing; it is preserved separately. "
        "The successful run uses the existing service Python environment, matching the native workflow.",
        "",
        "All 413 deterministic baseline hashes, 7,839 pinned native artifacts, 343 source-file "
        "references, 847 construction files and the original review-v2 packet/page are unchanged. "
        "Production pronunciation inference, learner grading, application UI, backend API and "
        "deployment files are unchanged. No commit, push or deployment occurred. "
        "Focused Python and Chromium checks cover draft/attestation, optional telemetry, required "
        "decisions, notes, all 22 adjudications, separation/quarantine, immutability, inference "
        "reproduction, no training and descriptive naming. See validation.json and test logs for "
        "exact test counts. Ruff, JavaScript syntax and git diff --check also pass.",
        "",
        "**Research files changed in this continuation.** Updated "
        "`perceptual_tone/learner_finalization.py`, `scripts/learner_review_v2.js`, "
        "`scripts/learner_review_v2_smoke.cjs`, and `tests/test_learner_finalization.py`. "
        "Added `perceptual_tone/learner_release.py`, `perceptual_tone/learner_transfer.py`, "
        "`scripts/learner_transfer.py`, `scripts/learner_transfer_report.py`, "
        "`scripts/learner_transfer_verify.py`, `tests/test_learner_release.py`, "
        "`tests/test_learner_transfer.py`, and this report. Pre-existing uncommitted construction "
        "work remains in place. Private generated artifacts live under the ignored release and run directories.",
        "",
        "**Artifact paths and reruns.**",
        "",
        f"- Release: `{RELEASE}`",
        f"- Evaluation and verification: `{RUN}`",
        "- Full adjudication: release `adjudication.jsonl`; all original notes/telemetry: `raw-draft.json`.",
        "- Full probabilities and deterministic evidence: run `{primary,diagnostic,unknown}/predictions.jsonl`.",
        "- Frozen comparison: run `representation-comparison/predictions.jsonl`.",
        "- Read-only verification: `benchmark/pronunciation_v2/.venv/bin/python research/perceptual-tone-model/scripts/learner_transfer_verify.py`.",
        "- Focused tests: `PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p 'test_learner_*.py' -v`.",
        "",
    ]
    confidence = {}
    confidence_rows = []
    for name in ("expanded", "pilot"):
        confidence[name] = {}
        for subset, records in (
            ("all accepted primary", primary),
            (
                "resolved expected-tone disagreements",
                [
                    r
                    for r in primary
                    if r["expected_surface_tone"] in (1, 2, 3, 4)
                    and r[name]["prediction"] != f"T{r['expected_surface_tone']}"
                ],
            ),
        ):
            stats = confidence_stats(records, name)
            confidence[name][subset] = stats
            confidence_rows.append(
                [
                    name,
                    subset,
                    stats["n"],
                    *[f"{stats[k]:.3f}" for k in ("mean", "median", "min", "max")],
                    stats["count_ge_0_80"],
                    stats["count_ge_0_90"],
                    "; ".join(
                        f"{r['qa_item_id']} {r['hanzi']} {r[name]['confidence']:.3f}"
                        for r in records
                    )
                    if subset.startswith("resolved")
                    else "see full primary table",
                ]
            )
    disagreements = [r for r in primary if r["expanded"]["prediction"] != r["pilot"]["prediction"]]
    extra = [
        "**Confidence on expected-tone disagreements, separately.**",
        "",
        table(
            [
                "Model",
                "Subset",
                "N",
                "Mean",
                "Median",
                "Min",
                "Max",
                "≥.80",
                "≥.90",
                "Disagreement items / confidence",
            ],
            confidence_rows,
        ),
        "",
        "**All seven expanded/pilot disagreement syllables.**",
        "",
        table(
            [
                "QA / take",
                "Target / pinyin",
                "Expected surface",
                "Tone span ms",
                "Expanded / confidence",
                "Pilot / confidence",
                "Deterministic",
            ],
            [
                [
                    r["qa_item_id"] + " / " + aliases[r["source_id"]],
                    r["hanzi"] + " / " + r["pinyin"],
                    tone(r["expected_surface_tone"]),
                    f"{r['tone_duration_seconds'] * 1000:.0f}",
                    f"{r['expanded']['prediction']} / {r['expanded']['confidence']:.3f}",
                    f"{r['pilot']['prediction']} / {r['pilot']['confidence']:.3f}",
                    prediction(r, "deterministic"),
                ]
                for r in disagreements
            ],
        ),
        "",
        "Disagreements span S01 (3/7), S02 (2/5), and S03 (2/4), rather than concentrating in "
        "one take. All seven are expanded T2 predictions; the pilot predicts no T2 anywhere in "
        "the primary set. Their lexical tones are four T3, two T1 and one T4; resolved expected "
        "tones are two T1, two T3 and one T2, with two unresolved. 天 recurs in two takes; the "
        "other targets differ. Disagreement tone spans range 20-230 ms (median 110 ms), compared "
        "with 60-120 ms (median 90 ms) for model agreements. Both accepted spans under 60 ms "
        "disagree, but five disagreements have 100-230 ms spans. Four of seven expanded "
        "predictions have confidence ≥.80, versus one pilot prediction. Disagreement is neither "
        "limited to short spans nor exclusively low confidence. These are descriptive patterns "
        "from N=16, not learned rules. Exact computational reproduction establishes numerical "
        "repeatability; robustness across repeat recordings or acoustic perturbations was not tested.",
        "",
        "**Per-take confidence detail.**",
        "",
        table(
            ["Take", "Model", "Mean", "Median", "Min", "Max", "≥.80", "≥.90"],
            [
                [
                    aliases[ident],
                    name,
                    *[f"{stats[k]:.3f}" for k in ("mean", "median", "min", "max")],
                    stats["count_ge_0_80"],
                    stats["count_ge_0_90"],
                ]
                for ident in sorted(summaries["primary"]["takes"], key=aliases.get)
                for name in ("expanded", "pilot")
                for stats in [
                    confidence_stats([r for r in primary if r["source_id"] == ident], name)
                ]
            ],
        ),
        "",
    ]
    insertion = text.index("**Exploratory supplemental results, frozen after primary.**")
    text[insertion:insertion] = extra
    text += [
        "Learner-domain transfer is MIXED and legitimate nucleus/coda pooling does not explain "
        "away the earlier external-probe uncertainty. Realized-tone ground truth is now the "
        "primary evaluation bottleneck.",
        "",
    ]
    analysis = {
        "primary_confidence": confidence,
        "model_disagreement_items": [r["qa_item_id"] for r in disagreements],
        "historical_wo_count": len(historical_wo),
    }
    analysis_path = RUN / "report-analysis.json"
    if not analysis_path.exists():
        write_json(analysis_path, analysis)
    elif read_json(analysis_path) != analysis:
        raise ValueError("report_analysis_changed")
    destination = PACKAGE / "learner-domain-transfer-report.md"
    destination.write_text("\n".join(text))
    result = {
        "classification": "MIXED TRANSFER",
        "realized_tone_annotation_needed": True,
        "material_pooling_improvement_demonstrated": False,
        "release": seal,
        "primary": summaries["primary"],
        "report": str(destination),
    }
    target = RUN / "research-conclusions.json"
    if not target.exists():
        write_json(target, result)
    elif read_json(target) != result:
        raise ValueError("conclusions_changed")
    return destination


if __name__ == "__main__":
    print(report())
