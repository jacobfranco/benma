"""Deterministic report renderer; consumes completed analysis, never model files."""
# ruff: noqa: E501, RUF001 -- report prose, intentional Unicode and wide table cells

from .blind_analysis import TONES, control_metrics


def f(value):
    n, d = value["n"], value["d"]
    return f"{n}/{d} ({100 * n / d:.1f}%)" if d else "0/0 (not estimable)"


def table(headers, rows):
    def cell(v):
        return str(v).replace("|", "\\|").replace("\n", " ")

    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(cell(v) for v in row) + " |" for row in rows],
        ]
    )


def model(r, name):
    return f"{r[name]} / {r[name + '_confidence']:.4f}"


def expected(r):
    return r["expected"] or "unresolved (T2/T3 alternatives)"


def deterministic(r):
    observed = r["deterministic_observed"]
    return (
        r["deterministic"]
        or f"ABSTAIN ({observed['decision']}; {observed.get('reason', 'unspecified')})"
    )


def render(review, stage, gate, checks, a, freeze):
    c = stage["controls"]
    rows = a["rows"]
    out = []

    def paragraph(text):
        out.append(text)

    paragraph("**Benma realized-tone review: reliability-first analysis — 2026-10-19**")
    paragraph(
        "**Reviewer reliability: INSUFFICIENT. The solo blind reviewer did not meet the preregistered credibility bar.** Native-control exact agreement is 10/28 and exact categorical repeat agreement is 3/8. These labels cannot determine what learner tones were actually realized. All learner comparisons below are **EXPLORATORY SOLO PERCEPTUAL ANNOTATION**; they cannot validate, reject, select, train, adapt, or calibrate either model, redefine the benchmark, or change production behavior."
    )
    paragraph(
        "The decision was saved before learner-label inspection and remains frozen. Export validation, control scoring, repeat matching and the credibility decision were reused after the continuation request. The initial learner analysis remains preserved as `04-learner-exploratory.json`; `05-final-exploratory-analysis.json` adds QA identifiers and explicitly separates ten numbered expectations from the additional neutral expectation. No annotation or frozen input was rewritten."
    )
    paragraph(
        "**Export and response distribution.** Schema, packet version/hash, reviewer Jacob, exact ordered opaque IDs, all 52 presentations, allowed tone/confidence/usability values, timestamp validity and playback flags passed. The original export was copied byte-for-byte before the key join. Primary tone-bearing playback is recorded for 52/52; whole-target playback for 40/52. Telemetry records completion booleans, not replay counts, durations, attention or subjective perception. Low confidence and UNCLEAR are intended responses, not missing data or annotation defects."
    )
    paragraph(
        table(
            ["Perceived label", "All 52 presentations", "16 learner first exposures"],
            [
                [
                    t,
                    sum(r["perceived_tone"] == t for r in review["reviews"]),
                    a["tone_distribution"][t],
                ]
                for t in TONES
            ],
        )
    )
    paragraph(
        table(
            ["Confidence", "All 52", "28 controls", "16 learners"],
            [
                [
                    i,
                    sum(r["confidence"] == i for r in review["reviews"]),
                    stage["control_confidence"][str(i)]["full_exact"]["d"],
                    a["confidence_distribution"][str(i)],
                ]
                for i in range(1, 6)
            ],
        )
    )
    paragraph(
        "All-review usability: unspecified 45, UNUSABLE 6, CLEAR 1, BORDERLINE 0. Confidence 3–5 occurs on 19/52 presentations; 33/52 are confidence 1–2. UNCLEAR occurs on 11/52 (21.2%). A high confidence value on UNCLEAR is preserved as confidence in that response, never converted to confidence in a numbered family."
    )
    paragraph(
        "**Native-control reliability, before learner comparisons.** Exactly 28 unique controls: six each T1–T4 and four neutral. These span 12 speakers and 28 recordings; observations are clustered by speaker. References are frozen AISHELL-3 corpus read-tone labels. All selected controls had release-level QA acceptance and mechanical checks, but none had an individual listening PASS. The reference/crop quality is therefore a limitation, not independently established phonetic truth."
    )
    paragraph(
        table(
            ["Measure", "Result", "Denominator / interpretation"],
            [
                [
                    "Full exact-match agreement",
                    f(c["full_exact"]),
                    "All 28 controls; abstentions remain in denominator",
                ],
                [
                    "Any non-UNCLEAR coverage",
                    f(c["non_unclear_coverage"]),
                    "Numbered or NEUTRAL responses",
                ],
                [
                    "Conditional agreement, non-UNCLEAR",
                    f(c["non_unclear_conditional"]),
                    "23 non-abstaining responses",
                ],
                [
                    "Numbered-judgment coverage, all controls",
                    f(c["numbered_judgment_coverage_all_controls"]),
                    "21 numbered responses among all 28 controls",
                ],
                [
                    "Conditional numbered-judgment accuracy, all controls",
                    f(c["numbered_judgment_conditional_all_controls"]),
                    "Includes two numbered predictions on neutral references",
                ],
                [
                    "Numbered-reference coverage",
                    f(c["numbered_reference_coverage"]),
                    "Numbered responses on the 24 T1–T4 references",
                ],
                [
                    "Conditional numbered accuracy, numbered references",
                    f(c["numbered_reference_conditional"]),
                    "Nine exact matches among 19 numbered responses",
                ],
                [
                    "Full numbered-reference agreement",
                    f(c["numbered_reference_full"]),
                    "All 24 numbered references",
                ],
                ["UNCLEAR rate", f(c["unclear"]), "Five abstentions among all 28"],
            ],
        )
    )
    paragraph(
        "Conditional scores exclude UNCLEAR rather than recoding it as an incorrect numbered prediction. NEUTRAL is also outside the four-class conditional score. The full-reference fractions retain all observations; no difficult control is discarded."
    )
    paragraph(table(["Reference", "Recall"], [[t, f(c["recall"][t])] for t in TONES[:-1]]))
    paragraph(
        "Confusion matrix: rows are corpus reference, columns are solo responses; counts include all 28 controls."
    )
    paragraph(
        table(
            ["Reference \\ Response", *TONES],
            [[t, *[c["matrix"][t][p] for p in TONES]] for t in TONES[:-1]],
        )
    )
    paragraph(
        "**T2/T3:** two of six T2 controls were called T3 (33.3%); zero of six T3 controls were called T2. Only one T2 was identified as T2. The other T2 responses were two T1 and one NEUTRAL. T3 recall was 4/6. This asymmetry matters when interpreting the absence of T2 among learner first exposures; it cannot be corrected post hoc. Neutral recall was 1/4; the other neutral controls were two T3 and one UNCLEAR."
    )
    paragraph(
        table(
            [
                "Control confidence",
                "Full exact agreement",
                "Numbered-reference coverage",
                "Conditional numbered accuracy",
            ],
            [
                [
                    i,
                    f(stage["control_confidence"][str(i)]["full_exact"]),
                    f(stage["control_confidence"][str(i)]["numbered_reference_coverage"]),
                    f(stage["control_confidence"][str(i)]["numbered_reference_conditional"]),
                ]
                for i in range(1, 6)
            ],
        )
    )
    paragraph(
        "Higher reported confidence did not consistently identify correct control responses: confidence 4 gave 1/5 full matches. Confidence 5 has only one control. No threshold was selected to improve performance. Control usability was unspecified on 27 controls (10/27 matches), UNUSABLE on one (0/1), and never CLEAR/BORDERLINE; unspecified is not silently equated with CLEAR."
    )
    played = []
    for heard in (True, False):
        subset = [r for r in stage["control_rows"] if r["human"]["whole_target_heard"] == heard]
        played.append(
            ["yes" if heard else "no", len(subset), f(control_metrics(subset)["full_exact"])]
        )
    paragraph(table(["Whole target played, controls", "N", "Full exact agreement"], played))
    paragraph(
        "Whole-target use was self-selected in response to difficulty. This descriptive split cannot establish that either view improves perception or justify exclusions."
    )
    paragraph(
        "**All eight hidden repeat pairs.** First exposure remains the learner annotation used below. Repeats are consistency checks, never extra independent units or replacements for awkward originals. No broader T2/T3-compatible-family equivalence was preregistered; none is introduced."
    )
    paragraph(
        table(
            [
                "Original opaque ID",
                "Repeat opaque ID",
                "Role",
                "First → second",
                "Confidence",
                "Δ confidence",
                "Exact",
                "UNCLEAR transition",
                "Usability first → second",
            ],
            [
                [
                    p["original_id"],
                    p["repeat_id"],
                    p["base_role"],
                    p["first"]["perceived_tone"] + " → " + p["second"]["perceived_tone"],
                    str(p["first"]["confidence"]) + " → " + str(p["second"]["confidence"]),
                    p["confidence_delta"],
                    "yes" if p["exact"] else "no",
                    "yes" if p["unclear_transition"] else "no",
                    str(p["first"]["usability"]) + " → " + str(p["second"]["usability"]),
                ]
                for p in stage["pairs"]
            ],
        )
    )
    paragraph(
        f"Primary exact categorical repeat agreement: **{f(stage['repeat_exact'])}**. One success is UNCLEAR→UNCLEAR with UNUSABLE on both exposures; it does not establish tone-family stability. The preregistered informative exact score, excluding UNCLEAR/UNUSABLE pairs as successes while keeping all eight in the denominator, is {f(stage['repeat_informative_exact'])}. Both responses are numbered in four pairs; exact agreement there is {f(stage['repeat_numbered'])}, with coverage 4/8. Control pairs agree 1/5; learner pairs agree 2/3, including the UNCLEAR pair. Mean absolute confidence difference is 1.0 point; three pairs cross into or out of UNCLEAR. No pair changes usability; all values are shown."
    )
    paragraph(
        "**Frozen credibility checks and interpretation.** The exact preregistered requirements remain unchanged; every requirement fails. The all-presentation confidence/UNCLEAR checks below were registered before review. The descriptive INSUFFICIENT classification itself uses control discrimination and repeat consistency only, with no learner/model agreement input."
    )
    paragraph(
        table(
            ["Preregistered criterion", "Required", "Observed", "Result"],
            [
                ["Full control agreement", "≥23/28", "10/28", "FAIL"],
                ["Numbered control agreement", "≥20/24", "9/24", "FAIL"],
                ["Each numbered recall", "≥4/6 each", "1/6, 1/6, 4/6, 3/6", "FAIL"],
                ["Neutral agreement", "≥3/4", "1/4", "FAIL"],
                ["Informative exact repeats", "≥7/8", "2/8", "FAIL"],
                ["Confidence 3–5", "≥39/52", "19/52", "FAIL"],
                ["UNCLEAR", "≤5/52", "11/52", "FAIL"],
            ],
        )
    )
    paragraph(gate["rationale"])
    paragraph(
        "This does not mean every response is wrong, that Jacob cannot hear Mandarin tones in ordinary speech, that either model is correct, or that learner validation is unnecessary. It means this annotation source cannot resolve model-versus-learner ambiguity under this task. Observed contributors are low control discrimination, unstable repeated judgments, frequent uncertainty, asymmetric T2/T3 responses and neutral confusion. The reported difficulty and frequent whole-target use are consistent with a demanding isolated-snippet protocol. They do not distinguish reviewer limitations from crop/reference problems or the loss of natural context. There is no randomized comparison of listening protocols here; no causal attribution is justified."
    )
    paragraph(
        "**EXPLORATORY SOLO PERCEPTUAL ANNOTATION: 16 accepted natural units.** All are first exposures from the frozen release: seven S01, five S02, four S03, one speaker and three takes. Selection was by prior crop acceptance, not representative sampling. Unit IDs below are exact; repeated 天 tokens remain distinct by index and QA ID. Human confidence is ordinal 1–5. Model confidence is the saved probability of its chosen family, not a calibrated probability of correctness on this learner."
    )
    paragraph(
        table(
            [
                "Unit ID",
                "QA",
                "Take",
                "Hanzi / pinyin",
                "Lexical",
                "Expected",
                "Solo label",
                "Confidence",
                "Whole used",
                "Usability",
            ],
            [
                [
                    r["unit_id"],
                    r["qa_id"],
                    r["take"],
                    r["hanzi"] + " / " + r["pinyin"],
                    r["lexical"],
                    expected(r),
                    r["human"]["perceived_tone"],
                    r["human"]["confidence"],
                    "yes" if r["human"]["whole_target_heard"] else "no",
                    r["human"]["usability"] or "unspecified",
                ]
                for r in rows
            ],
        )
    )
    paragraph(
        table(
            [
                "QA / take / target",
                "Expanded / confidence",
                "Pilot / confidence",
                "Frozen deterministic Benma",
            ],
            [
                [
                    r["qa_id"] + " / " + r["take"] + " / " + r["hanzi"],
                    model(r, "expanded"),
                    model(r, "pilot"),
                    deterministic(r),
                ]
                for r in rows
            ],
        )
    )
    paragraph(
        "Deterministic outputs abstain on 14/16 units; the two numbered outputs are S02 我→T4 and S03 种→T2. Full saved deterministic evidence is preserved in the hidden key; the machine-readable analysis includes its observed decision and reason. No F0 explanation is inferred from a model prediction or an abstention."
    )
    paragraph(
        "Learner label distribution: T1=3, T2=0, T3=6, T4=3, NEUTRAL=0, UNCLEAR=4. Confidence 1–5 counts are 3, 7, 3, 0, 3. Ten labels have confidence ≤2 and remain explicitly low confidence. All four UNCLEAR learner items are also UNUSABLE. Usability: unspecified 11, UNUSABLE 4, CLEAR 1, BORDERLINE 0; whole target used 11/16. Confidence ≥3 includes six responses, two of which are UNCLEAR/UNUSABLE; only four enter the numbered model comparison."
    )
    paragraph(
        table(
            ["Confidence ≥3: QA / take / target", "Solo response", "Confidence", "Usability"],
            [
                [
                    r["qa_id"] + " / " + r["take"] + " / " + r["hanzi"],
                    r["human"]["perceived_tone"],
                    r["human"]["confidence"],
                    r["human"]["usability"] or "unspecified",
                ]
                for r in a["confidence_at_least_3_rows"]
            ],
        )
    )
    paragraph(
        "Low-confidence responses (≤2): "
        + ", ".join(
            r["qa_id"]
            + " "
            + r["take"]
            + " "
            + r["hanzi"]
            + "="
            + r["human"]["perceived_tone"]
            + " (c"
            + str(r["human"]["confidence"])
            + ")"
            for r in rows
            if r["human"]["confidence"] <= 2
        )
        + "."
    )
    paragraph(
        "**A. Expected versus solo human, exploratory only.** There are ten resolved numbered expectations, one additional resolved NEUTRAL (S01 吧), and five unresolved expectations. Unresolved sandhi alternatives remain unresolved; neither text, model consensus nor human labels resolve them."
    )
    paragraph(
        table(
            ["QA / take / target", "Expected", "Solo response", "Confidence", "Expanded", "Pilot"],
            [
                [
                    r["qa_id"] + " / " + r["take"] + " / " + r["hanzi"],
                    r["expected"],
                    r["human"]["perceived_tone"],
                    r["human"]["confidence"],
                    r["expanded"],
                    r["pilot"],
                ]
                for r in a["expected_rows"]
            ],
        )
    )
    paragraph(
        "For the ten resolved numbered expectations: 6/10 exact matches, two numbered disagreements, and two UNCLEAR/UNUSABLE responses. Numbered-response coverage is 8/10 (80%); conditional expected–human agreement is 6/8 (75%). The two numbered disagreements are S01 second 天 (expected T1, solo T4/c2) and S02 天 (expected T1, solo T3/c2). S01 不 and 我 are UNCLEAR. The additional expected-neutral S01 吧 was called T1/c2; both models chose T3. Including it gives 6/11 full categorical expected–human agreement. These observations do not prove learner-production errors or their frequency."
    )
    paragraph(
        "**B and C. Expanded–human and pilot–human, separately and exploratory only.** All non-UNCLEAR labels happen to be numbered and none is UNUSABLE, giving the same 12-item eligible subset for both models. Expanded agrees on 6/12 (50.0%); pilot on 8/12 (66.7%). Both match on six, pilot alone on two, expanded alone on zero, neither on four. These are descriptive agreements with an insufficient annotation source, not model accuracy or a ranking/selection claim. Four UNCLEAR/UNUSABLE items are excluded from conditional agreement and retained in the distribution; human NEUTRAL count is zero."
    )
    paragraph(
        table(
            ["Human confidence subset", "Expanded–human agreement", "Pilot–human agreement"],
            [
                [
                    ("all numbered / non-UNCLEAR" if t == "1" else "≥" + t),
                    f(v["expanded"]),
                    f(v["pilot"]),
                ]
                for t, v in a["strata"].items()
            ],
        )
    )
    paragraph(
        "Confidence ≥4 contains only two eligible units, both confidence 5: S02 去 and S03 买. These raw counts are too small for a stable comparison. The preregistered confidence 4–5 AND explicitly CLEAR subset contains only S02 去: both agree 1/1. Missing usability is reported separately and not promoted to CLEAR. No confidence threshold was optimized for a model. Human NEUTRAL would be reported separately with each numbered model choice and excluded from four-tone scores; there are no such learner responses in this export."
    )
    paragraph(
        "Does human comparison improve on expected-tone comparison? On the original ten resolved numbered expectations, expanded–expected is 5/10 and pilot–expected 7/10. Comparing those directly with 6/12 and 8/12 would change denominators. On the same eight units with resolved numbered expectations and eligible human responses, expanded–expected is 4/8 versus expanded–human 5/8; pilot–expected and pilot–human are both 6/8. This is one additional descriptive match for expanded and no net change for pilot, with no validation implication. Across all 11 resolved expectations including neutral, model–expected counts are expanded 5/11 and pilot 7/11, reported separately from four-tone agreement."
    )
    paragraph(
        "**Seven frozen expanded-T2 disagreements.** Every case remains included regardless of confidence or usability."
    )
    paragraph(
        table(
            [
                "Unit ID / QA",
                "Take / target",
                "Expected",
                "Solo / confidence",
                "Expanded / confidence",
                "Pilot / confidence",
                "Deterministic",
            ],
            [
                [
                    r["unit_id"] + " / " + r["qa_id"],
                    r["take"] + " / " + r["hanzi"],
                    expected(r),
                    r["human"]["perceived_tone"] + " / " + str(r["human"]["confidence"]),
                    model(r, "expanded"),
                    model(r, "pilot"),
                    r["deterministic"] or "ABSTAIN",
                ]
                for r in a["t2_disagreement_rows"]
            ],
        )
    )
    paragraph(
        "First-exposure solo pattern: 0/7 T2, 3/7 T3, 1/7 T1, 3/7 UNCLEAR. Thus four responses name another numbered family and three abstain; two of the four numbered responses are low confidence (c2). The other numbered responses are S02 晚=T3/c3 and S03 买=T3/c5. The overall pattern is mixed between another family and unresolved/low-confidence responses. It does not corroborate the claim that the reviewer independently heard T2 on these first exposures. The exploratory solo labels contradict that narrow corroboration prediction, but are not reliable enough to adjudicate the expanded-T2 hypothesis. Whether expanded detects actual learner T2 realizations or exhibits a learner-domain T2 error remains unresolved. T2 control recall is only 1/6. Among learner repeats, S03 水 changes from T3/c3 to T2/c2; that repeat is reported without replacing its first response and is outside the seven model-disagreement cases."
    )
    paragraph("**Requested primary cases, without special scoring.**")
    special = [
        r
        for r in rows
        if (r["take"], r["hanzi"])
        in {
            ("S01", "我"),
            ("S02", "我"),
            ("S03", "想"),
            ("S03", "买"),
            ("S03", "种"),
            ("S03", "水"),
        }
    ]
    paragraph(
        table(
            ["QA / case", "Expected", "Solo / confidence", "Expanded", "Pilot", "Deterministic"],
            [
                [
                    r["qa_id"] + " / " + r["take"] + " " + r["hanzi"],
                    expected(r),
                    r["human"]["perceived_tone"] + " / " + str(r["human"]["confidence"]),
                    r["expanded"],
                    r["pilot"],
                    r["deterministic"] or "ABSTAIN",
                ]
                for r in special
            ],
        )
    )
    paragraph(
        "S01 我 is UNCLEAR/UNUSABLE, so it cannot arbitrate expanded T2 versus pilot T3. S02 我 is solo T3/c2, both learned models T3, deterministic T4; agreement is not independent truth. S03 想 is solo T3/c2 with both models T3. S03 买 is solo T3/c5, expanded T2, pilot T3; it is a high-value independent-listener case, not an adjudicated model error. S03 种 is UNCLEAR/UNUSABLE despite expanded and deterministic T2. S03 水 is solo T3/c3 while both learned models choose T1. All four S03 expectations remain unresolved. The repeated S03 水 changes T3/c3→T2/c2; S02 晚 remains T3/c3→T3/c2. Neither repeat rescues the gate."
    )
    paragraph(
        "**What remains established.** Native-domain recognition remains strong/replicated. Learner-domain transfer remains **MIXED / unresolved**. Legitimate nucleus/coda pooling remains **NO GENERAL IMPROVEMENT DEMONSTRATED**. Insufficient solo labels neither strengthen nor weaken these model conclusions. They do establish that this solo annotation route did not resolve the evidence bottleneck. Model consensus, model–expected agreement and deterministic–model agreement are never substituted for an independent perceptual reference."
    )
    paragraph(
        "**Strict product criterion and purpose of learner validation.** Benma should be strict when a competent Mandarin listener hears the wrong tone. If expected T3 is produced as perceptually T2-like speech and HuBERT returns T2, correcting the learner is desired behavior. If competent listeners consistently hear T3 but HuBERT returns T2 because of unrelated vowel quality, timing or accent features, that is a learner-domain recognition failure. The validation question is whether model strictness corresponds to Mandarin listener perception. No accent-tolerant pass rule or inference of intended tone is warranted."
    )
    paragraph(
        "**Next decision: C — SOLO LABELS INSUFFICIENT.** Do not use this solo source to evaluate learner transfer. A small independent-listener check is still necessary before calling the recognizer trustworthy for product integration; a giant formal learner benchmark is not required. Exact next action: arrange a separately authorized, unpaid blind review with three independent competent Mandarin listeners, such as willing native-speaking language-exchange contacts or friends. This report proposes the design only; no outreach, packet construction, or new annotation occurs in this pass."
    )
    paragraph(
        "Proposed small packet per listener: **16 accepted learner syllables + 8 native controls + 4 hidden repeats = 28 presentations**. Keep the same 16 learner units and frozen spans/predictions. Balance the eight controls across T1–T4 and neutral, including more than one T2 and T3; one feasible allocation is T1=1, T2=2, T3=2, T4=1, NEUTRAL=2. Use controls with independent listening/crop checks and diverse speakers, chosen without learner-model outcomes. Use two learner and two control repeats, with pairs and spacing fixed before review. Randomize opaque presentation order separately per listener. Hide roles, repeats, Hanzi, pinyin, expected tones, source IDs and every model prediction. Collect tone family, confidence, usability, and both playback flags independently, with no discussion or cross-listener answers before sealing exports. Preserve UNCLEAR/NEUTRAL."
    )
    paragraph(
        "Before collecting the next labels, specify how control/repeat evidence and listener disagreement will be assessed; eight controls are a check, not a precise competence estimate. Do not invent thresholds after seeing model agreement. Review whether the isolated tone-bearing task is too difficult: consider making the existing whole-target audio readily available to everyone, with the tone-bearing crop as an optional additional view. Fix that protocol in advance and report it as a protocol change; do not widen frozen spans or selectively change playback for model disagreements. Keep independent initial judgments even if later acoustic adjudication is needed."
    )
    paragraph(
        "If reliable independent listeners generally agree with frozen HuBERT on learner realizations, learner transfer is sufficient for the next product-integration experiment on this narrow sample: integrate trustworthy learned recognition, preserve linguistic rules, return to physical/manual Benma testing, and validate grading, abstention, explanations and UX. That would not establish population-wide generalization or calibration. If reliable listeners systematically disagree on usable, clearly judged learner units, treat that as evidence of learner-domain model failure after checking crop/reference integrity; then investigate additional labeled learner speech, classifier adaptation, temporal heads or partial encoder fine-tuning. If listeners themselves remain uncertain or inconsistent, improve the perceptual protocol or obtain independent acoustic adjudication; do not force either engineering branch. No adaptation precedes this distinction."
    )
    paragraph(
        "**Road back to manual Benma testing and preserved architecture.** The intended loop is: natural learner speech → ASR/segmentation → learned perceived-tone recognition → independent expected contextual-tone resolution → correctness/concern grading → evidence-supported acoustic coaching → target-versus-heard feedback. Recognition must not receive the expected answer as a shortcut. Linguistic expectations retain lexical tone, sandhi and neutral/contextual realization. Learned recognition identifies acoustic/perceptual family, with neutral/abstention support as appropriate in future work. F0, contour and timing remain the interpretable explanation layer. Show target pronunciation, what Benma heard, mismatching syllables, pitch visualization and specific coaching only where measured evidence supports it. A recognizer T4 prediction alone does not prove a falling contour or justify a diagnosis about recovery/rise. The target-versus-heard idea, such as expected 想 T3 versus heard T4-like, remains intact. Subsequent physical tests should focus on false corrections, grading quality, explanations, confidence/abstention, usability and sentence-level feedback; no such product work is implemented here."
    )
    paragraph(
        "**Reproducibility and freeze.** "
        + str(freeze["baseline_hashes_unchanged"])
        + " deterministic baseline hashes, "
        + str(freeze["preexisting_files_unchanged"])
        + " files in the packet starting-state snapshot, and "
        + str(freeze["packet_artifact_hashes_unchanged"])
        + " packet-sealed artifact hashes verify unchanged. Both learned model files, native and learner releases, and saved expanded/pilot/deterministic predictions across primary and supplemental phases verify against their frozen seals. No model was loaded or run. Production pronunciation inference, grading, app UI, APIs and deployment files are unchanged; changes are confined to new research files. No training, tuning, adaptation, benchmark edits, production integration, commit, push or deployment occurred."
    )
    paragraph(
        table(
            ["Artifact", "SHA-256"],
            [
                ["Canonical blind packet", freeze["packet_sha256"]],
                ["Original human export", freeze["export_sha256"]],
                ["Hidden answer key", freeze["answer_key_sha256"]],
                ["Learner release manifest", freeze["learner_release_manifest_sha256"]],
                ["Native release", freeze["native_release_sha256"]],
                ["Primary prediction file", freeze["prediction_file_hashes"]["primary"]],
            ],
        )
    )
    paragraph(
        "Blinding verification: the sealed review page remains byte-identical and passes the visible leakage audit; it exposes no expected labels, roles or model results. Selection/order/audio were frozen before saved model outputs were joined into the private key. The export was preserved before any analysis. Thus the audited annotation pipeline supplied no model-output influence. Independent memory or filesystem access by the reviewer cannot be verified from these artifacts, so absolute psychological independence is not claimed."
    )
    paragraph(
        "**Validation and report paths.** Focused lightweight tests cover schema/IDs/telemetry, key joins, control-only scoring, repeat links and abstention, fixed preregistered checks, frozen-gate integrity, learner population, exploratory-only guard, neutral separation, confidence strata, T2 cases, deterministic report generation, no training/inference entry points, baseline preservation and whitespace. See `data/generated/realized-tone-analysis-v1-20261019/tests.log` and `07-test-validation.json` for executed results. No native training, embedding generation, packet regeneration or browser listening simulation is required."
    )
    paragraph(
        "Final narrative: `research/perceptual-tone-model/realized-tone-reliability-first-report.md`. Final machine-readable analysis: `data/generated/realized-tone-analysis-v1-20261019/05-final-exploratory-analysis.json`. Ordered records in that directory: `human-export.original.json`, `01-export-validation.json`, `02-controls-and-repeats.json`, `03-reliability-gate.json`, `03-registered-checks.json`, preserved preliminary `04-learner-exploratory.json`, final `05-final-exploratory-analysis.json`, `06-freeze-verification.json`, and test/validation logs. All paths are relative to the research package unless prefixed with `research/`."
    )
    paragraph(
        "New research source/report files in this pass: `perceptual_tone/blind_analysis.py`, `perceptual_tone/blind_analysis_report.py`, `scripts/blind_analysis.py`, `tests/test_blind_analysis.py`, and `realized-tone-reliability-first-report.md`. Earlier uncommitted research work and sealed inputs were retained unchanged. Reproduce the report with `benchmark/pronunciation_v2/.venv/bin/python research/perceptual-tone-model/scripts/blind_analysis.py`; existing outputs are compared, never overwritten. Run focused tests with `PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p test_blind_analysis.py -v`."
    )
    paragraph(
        "The solo blind annotation failed its preregistered reliability gate, so its learner labels remain exploratory. Benma should remain strict when learner speech sounds like the wrong Mandarin tone. Resolve whether HuBERT tracks competent Mandarin listener perception through a small independent multi-listener check, then either integrate learned recognition and return to physical Benma testing or, only if listener disagreement is systematic, investigate learner-domain adaptation."
    )
    return "\n\n".join(out) + "\n"
