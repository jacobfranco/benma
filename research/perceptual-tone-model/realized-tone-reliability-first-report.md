**Benma realized-tone review: reliability-first analysis — 2026-10-19**

**Reviewer reliability: INSUFFICIENT. The solo blind reviewer did not meet the preregistered credibility bar.** Native-control exact agreement is 10/28 and exact categorical repeat agreement is 3/8. These labels cannot determine what learner tones were actually realized. All learner comparisons below are **EXPLORATORY SOLO PERCEPTUAL ANNOTATION**; they cannot validate, reject, select, train, adapt, or calibrate either model, redefine the benchmark, or change production behavior.

The decision was saved before learner-label inspection and remains frozen. Export validation, control scoring, repeat matching and the credibility decision were reused after the continuation request. The initial learner analysis remains preserved as `04-learner-exploratory.json`; `05-final-exploratory-analysis.json` adds QA identifiers and explicitly separates ten numbered expectations from the additional neutral expectation. No annotation or frozen input was rewritten.

**Export and response distribution.** Schema, packet version/hash, reviewer Jacob, exact ordered opaque IDs, all 52 presentations, allowed tone/confidence/usability values, timestamp validity and playback flags passed. The original export was copied byte-for-byte before the key join. Primary tone-bearing playback is recorded for 52/52; whole-target playback for 40/52. Telemetry records completion booleans, not replay counts, durations, attention or subjective perception. Low confidence and UNCLEAR are intended responses, not missing data or annotation defects.

| Perceived label | All 52 presentations | 16 learner first exposures |
| --- | --- | --- |
| T1 | 7 | 3 |
| T2 | 4 | 0 |
| T3 | 19 | 6 |
| T4 | 9 | 3 |
| NEUTRAL | 2 | 0 |
| UNCLEAR | 11 | 4 |

| Confidence | All 52 | 28 controls | 16 learners |
| --- | --- | --- | --- |
| 1 | 11 | 6 | 3 |
| 2 | 22 | 10 | 7 |
| 3 | 10 | 6 | 3 |
| 4 | 5 | 5 | 0 |
| 5 | 4 | 1 | 3 |

All-review usability: unspecified 45, UNUSABLE 6, CLEAR 1, BORDERLINE 0. Confidence 3–5 occurs on 19/52 presentations; 33/52 are confidence 1–2. UNCLEAR occurs on 11/52 (21.2%). A high confidence value on UNCLEAR is preserved as confidence in that response, never converted to confidence in a numbered family.

**Native-control reliability, before learner comparisons.** Exactly 28 unique controls: six each T1–T4 and four neutral. These span 12 speakers and 28 recordings; observations are clustered by speaker. References are frozen AISHELL-3 corpus read-tone labels. All selected controls had release-level QA acceptance and mechanical checks, but none had an individual listening PASS. The reference/crop quality is therefore a limitation, not independently established phonetic truth.

| Measure | Result | Denominator / interpretation |
| --- | --- | --- |
| Full exact-match agreement | 10/28 (35.7%) | All 28 controls; abstentions remain in denominator |
| Any non-UNCLEAR coverage | 23/28 (82.1%) | Numbered or NEUTRAL responses |
| Conditional agreement, non-UNCLEAR | 10/23 (43.5%) | 23 non-abstaining responses |
| Numbered-judgment coverage, all controls | 21/28 (75.0%) | 21 numbered responses among all 28 controls |
| Conditional numbered-judgment accuracy, all controls | 9/21 (42.9%) | Includes two numbered predictions on neutral references |
| Numbered-reference coverage | 19/24 (79.2%) | Numbered responses on the 24 T1–T4 references |
| Conditional numbered accuracy, numbered references | 9/19 (47.4%) | Nine exact matches among 19 numbered responses |
| Full numbered-reference agreement | 9/24 (37.5%) | All 24 numbered references |
| UNCLEAR rate | 5/28 (17.9%) | Five abstentions among all 28 |

Conditional scores exclude UNCLEAR rather than recoding it as an incorrect numbered prediction. NEUTRAL is also outside the four-class conditional score. The full-reference fractions retain all observations; no difficult control is discarded.

| Reference | Recall |
| --- | --- |
| T1 | 1/6 (16.7%) |
| T2 | 1/6 (16.7%) |
| T3 | 4/6 (66.7%) |
| T4 | 3/6 (50.0%) |
| NEUTRAL | 1/4 (25.0%) |

Confusion matrix: rows are corpus reference, columns are solo responses; counts include all 28 controls.

| Reference \ Response | T1 | T2 | T3 | T4 | NEUTRAL | UNCLEAR |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 1 | 0 | 2 | 1 | 0 | 2 |
| T2 | 2 | 1 | 2 | 0 | 1 | 0 |
| T3 | 1 | 0 | 4 | 1 | 0 | 0 |
| T4 | 0 | 1 | 0 | 3 | 0 | 2 |
| NEUTRAL | 0 | 0 | 2 | 0 | 1 | 1 |

**T2/T3:** two of six T2 controls were called T3 (33.3%); zero of six T3 controls were called T2. Only one T2 was identified as T2. The other T2 responses were two T1 and one NEUTRAL. T3 recall was 4/6. This asymmetry matters when interpreting the absence of T2 among learner first exposures; it cannot be corrected post hoc. Neutral recall was 1/4; the other neutral controls were two T3 and one UNCLEAR.

| Control confidence | Full exact agreement | Numbered-reference coverage | Conditional numbered accuracy |
| --- | --- | --- | --- |
| 1 | 0/6 (0.0%) | 1/5 (20.0%) | 0/1 (0.0%) |
| 2 | 5/10 (50.0%) | 9/9 (100.0%) | 5/9 (55.6%) |
| 3 | 3/6 (50.0%) | 4/4 (100.0%) | 2/4 (50.0%) |
| 4 | 1/5 (20.0%) | 4/5 (80.0%) | 1/4 (25.0%) |
| 5 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) |

Higher reported confidence did not consistently identify correct control responses: confidence 4 gave 1/5 full matches. Confidence 5 has only one control. No threshold was selected to improve performance. Control usability was unspecified on 27 controls (10/27 matches), UNUSABLE on one (0/1), and never CLEAR/BORDERLINE; unspecified is not silently equated with CLEAR.

| Whole target played, controls | N | Full exact agreement |
| --- | --- | --- |
| yes | 23 | 8/23 (34.8%) |
| no | 5 | 2/5 (40.0%) |

Whole-target use was self-selected in response to difficulty. This descriptive split cannot establish that either view improves perception or justify exclusions.

**All eight hidden repeat pairs.** First exposure remains the learner annotation used below. Repeats are consistency checks, never extra independent units or replacements for awkward originals. No broader T2/T3-compatible-family equivalence was preregistered; none is introduced.

| Original opaque ID | Repeat opaque ID | Role | First → second | Confidence | Δ confidence | Exact | UNCLEAR transition | Usability first → second |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aea194ced3e71146c4cc4 | A6498552760d1befc9b57 | control | NEUTRAL → UNCLEAR | 3 → 1 | -2 | no | yes | None → None |
| A4dffff4d275b8e0703d6 | A12c6c021690fcde20fda | control | T1 → T3 | 1 → 2 | 1 | no | no | None → None |
| A5c9faf927b4295923349 | Ab4d9531228aac61ade70 | learner | UNCLEAR → UNCLEAR | 1 → 1 | 0 | yes | no | UNUSABLE → UNUSABLE |
| A528dfdbdd0efb7e9d5ce | A587675271a90235a110c | control | UNCLEAR → T4 | 1 → 2 | 1 | no | yes | None → None |
| Ad9e676faa13d509d3577 | A224f74f4bf5ceeaa1059 | control | T3 → T3 | 2 → 2 | 0 | yes | no | None → None |
| Aa01c0424fd91aa9270dc | A9e7d3bade77566edb072 | control | UNCLEAR → T2 | 1 → 3 | 2 | no | yes | None → None |
| Acac2d7b1739cc0e05439 | Aa2cc2896947d107204fa | learner | T3 → T2 | 3 → 2 | -1 | no | no | None → None |
| Ae0eb4bc7157122c38bcf | A739191683ec1355ff3d9 | learner | T3 → T3 | 3 → 2 | -1 | yes | no | None → None |

Primary exact categorical repeat agreement: **3/8 (37.5%)**. One success is UNCLEAR→UNCLEAR with UNUSABLE on both exposures; it does not establish tone-family stability. The preregistered informative exact score, excluding UNCLEAR/UNUSABLE pairs as successes while keeping all eight in the denominator, is 2/8 (25.0%). Both responses are numbered in four pairs; exact agreement there is 2/4 (50.0%), with coverage 4/8. Control pairs agree 1/5; learner pairs agree 2/3, including the UNCLEAR pair. Mean absolute confidence difference is 1.0 point; three pairs cross into or out of UNCLEAR. No pair changes usability; all values are shown.

**Frozen credibility checks and interpretation.** The exact preregistered requirements remain unchanged; every requirement fails. The all-presentation confidence/UNCLEAR checks below were registered before review. The descriptive INSUFFICIENT classification itself uses control discrimination and repeat consistency only, with no learner/model agreement input.

| Preregistered criterion | Required | Observed | Result |
| --- | --- | --- | --- |
| Full control agreement | ≥23/28 | 10/28 | FAIL |
| Numbered control agreement | ≥20/24 | 9/24 | FAIL |
| Each numbered recall | ≥4/6 each | 1/6, 1/6, 4/6, 3/6 | FAIL |
| Neutral agreement | ≥3/4 | 1/4 | FAIL |
| Informative exact repeats | ≥7/8 | 2/8 | FAIL |
| Confidence 3–5 | ≥39/52 | 19/52 | FAIL |
| UNCLEAR | ≤5/52 | 11/52 | FAIL |

Native exact agreement is 10/28; T1 and T2 recall are each 1/6; numbered conditional agreement is 9/19. Exact repeat agreement is 3/8, including one UNCLEAR/UNUSABLE pair, with informative agreement 2/8. Weak discrimination and repeat consistency prevent using this solo perceptual reference for learner-transfer evaluation. This decision uses controls and repeats only, not learner/model agreement.

This does not mean every response is wrong, that Jacob cannot hear Mandarin tones in ordinary speech, that either model is correct, or that learner validation is unnecessary. It means this annotation source cannot resolve model-versus-learner ambiguity under this task. Observed contributors are low control discrimination, unstable repeated judgments, frequent uncertainty, asymmetric T2/T3 responses and neutral confusion. The reported difficulty and frequent whole-target use are consistent with a demanding isolated-snippet protocol. They do not distinguish reviewer limitations from crop/reference problems or the loss of natural context. There is no randomized comparison of listening protocols here; no causal attribution is justified.

**EXPLORATORY SOLO PERCEPTUAL ANNOTATION: 16 accepted natural units.** All are first exposures from the frozen release: seven S01, five S02, four S03, one speaker and three takes. Selection was by prior crop acceptance, not representative sampling. Unit IDs below are exact; repeated 天 tokens remain distinct by index and QA ID. Human confidence is ordinal 1–5. Model confidence is the saved probability of its chosen family, not a calibrated probability of correctness on this learner.

| Unit ID | QA | Take | Hanzi / pinyin | Lexical | Expected | Solo label | Confidence | Whole used | Usability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| learner:4cf712ee935667d1ab00dd9f:1 | Q100 | S01 | 天 / tian1 | T1 | T1 | T1 | 2 | yes | unspecified |
| learner:4cf712ee935667d1ab00dd9f:2 | Q051 | S01 | 天 / tian1 | T1 | T1 | T4 | 2 | yes | unspecified |
| learner:4cf712ee935667d1ab00dd9f:4 | Q037 | S01 | 不 / bu4 | T4 | T2 | UNCLEAR | 5 | yes | UNUSABLE |
| learner:4cf712ee935667d1ab00dd9f:5 | Q027 | S01 | 错 / cuo4 | T4 | T4 | T4 | 2 | yes | unspecified |
| learner:4cf712ee935667d1ab00dd9f:6 | Q065 | S01 | 我 / wo3 | T3 | T3 | UNCLEAR | 1 | no | UNUSABLE |
| learner:4cf712ee935667d1ab00dd9f:10 | Q047 | S01 | 走 / zou3 | T3 | unresolved (T2/T3 alternatives) | UNCLEAR | 1 | yes | UNUSABLE |
| learner:4cf712ee935667d1ab00dd9f:12 | Q064 | S01 | 吧 / ba5 | NEUTRAL | NEUTRAL | T1 | 2 | no | unspecified |
| learner:39e33220c5dec271b192f561:0 | Q031 | S02 | 我 / wo3 | T3 | T3 | T3 | 2 | yes | unspecified |
| learner:39e33220c5dec271b192f561:2 | Q092 | S02 | 天 / tian1 | T1 | T1 | T3 | 2 | no | unspecified |
| learner:39e33220c5dec271b192f561:3 | Q053 | S02 | 晚 / wan3 | T3 | T3 | T3 | 3 | yes | unspecified |
| learner:39e33220c5dec271b192f561:5 | Q091 | S02 | 跟 / gen1 | T1 | T1 | T1 | 1 | yes | unspecified |
| learner:39e33220c5dec271b192f561:8 | Q006 | S02 | 去 / qu4 | T4 | T4 | T4 | 5 | yes | CLEAR |
| learner:0b44eac1332ea0859ac54d67:1 | Q063 | S03 | 想 / xiang3 | T3 | unresolved (T2/T3 alternatives) | T3 | 2 | no | unspecified |
| learner:0b44eac1332ea0859ac54d67:2 | Q028 | S03 | 买 / mai3 | T3 | unresolved (T2/T3 alternatives) | T3 | 5 | yes | unspecified |
| learner:0b44eac1332ea0859ac54d67:4 | Q033 | S03 | 种 / zhong3 | T3 | unresolved (T2/T3 alternatives) | UNCLEAR | 3 | yes | UNUSABLE |
| learner:0b44eac1332ea0859ac54d67:5 | Q118 | S03 | 水 / shui3 | T3 | unresolved (T2/T3 alternatives) | T3 | 3 | no | unspecified |

| QA / take / target | Expanded / confidence | Pilot / confidence | Frozen deterministic Benma |
| --- | --- | --- | --- |
| Q100 / S01 / 天 | T2 / 0.4769 | T4 / 0.7666 | ABSTAIN (UNAVAILABLE; missing_critical_support) |
| Q051 / S01 / 天 | T4 / 0.9738 | T4 / 0.9758 | ABSTAIN (UNAVAILABLE; missing_critical_support) |
| Q037 / S01 / 不 | T2 / 0.9946 | T4 / 0.5760 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q027 / S01 / 错 | T4 / 0.8928 | T4 / 0.7408 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q065 / S01 / 我 | T2 / 0.8769 | T3 / 0.9366 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q047 / S01 / 走 | T1 / 0.6003 | T1 / 0.5950 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q064 / S01 / 吧 | T3 / 0.6239 | T3 / 0.5612 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q031 / S02 / 我 | T3 / 0.9895 | T3 / 0.9816 | T4 |
| Q092 / S02 / 天 | T2 / 0.8935 | T1 / 0.4274 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q053 / S02 / 晚 | T2 / 0.7325 | T3 / 0.6183 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q091 / S02 / 跟 | T1 / 0.9653 | T1 / 0.9453 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q006 / S02 / 去 | T4 / 0.9351 | T4 / 0.9862 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q063 / S03 / 想 | T3 / 0.9997 | T3 / 0.9900 | ABSTAIN (UNAVAILABLE; missing_critical_support) |
| Q028 / S03 / 买 | T2 / 0.6103 | T3 / 0.7135 | ABSTAIN (UNAVAILABLE; insufficient_support) |
| Q033 / S03 / 种 | T2 / 0.9838 | T1 / 0.6541 | T2 |
| Q118 / S03 / 水 | T1 / 0.7972 | T1 / 0.9889 | ABSTAIN (UNAVAILABLE; insufficient_support) |

Deterministic outputs abstain on 14/16 units; the two numbered outputs are S02 我→T4 and S03 种→T2. Full saved deterministic evidence is preserved in the hidden key; the machine-readable analysis includes its observed decision and reason. No F0 explanation is inferred from a model prediction or an abstention.

Learner label distribution: T1=3, T2=0, T3=6, T4=3, NEUTRAL=0, UNCLEAR=4. Confidence 1–5 counts are 3, 7, 3, 0, 3. Ten labels have confidence ≤2 and remain explicitly low confidence. All four UNCLEAR learner items are also UNUSABLE. Usability: unspecified 11, UNUSABLE 4, CLEAR 1, BORDERLINE 0; whole target used 11/16. Confidence ≥3 includes six responses, two of which are UNCLEAR/UNUSABLE; only four enter the numbered model comparison.

| Confidence ≥3: QA / take / target | Solo response | Confidence | Usability |
| --- | --- | --- | --- |
| Q037 / S01 / 不 | UNCLEAR | 5 | UNUSABLE |
| Q053 / S02 / 晚 | T3 | 3 | unspecified |
| Q006 / S02 / 去 | T4 | 5 | CLEAR |
| Q028 / S03 / 买 | T3 | 5 | unspecified |
| Q033 / S03 / 种 | UNCLEAR | 3 | UNUSABLE |
| Q118 / S03 / 水 | T3 | 3 | unspecified |

Low-confidence responses (≤2): Q100 S01 天=T1 (c2), Q051 S01 天=T4 (c2), Q027 S01 错=T4 (c2), Q065 S01 我=UNCLEAR (c1), Q047 S01 走=UNCLEAR (c1), Q064 S01 吧=T1 (c2), Q031 S02 我=T3 (c2), Q092 S02 天=T3 (c2), Q091 S02 跟=T1 (c1), Q063 S03 想=T3 (c2).

**A. Expected versus solo human, exploratory only.** There are ten resolved numbered expectations, one additional resolved NEUTRAL (S01 吧), and five unresolved expectations. Unresolved sandhi alternatives remain unresolved; neither text, model consensus nor human labels resolve them.

| QA / take / target | Expected | Solo response | Confidence | Expanded | Pilot |
| --- | --- | --- | --- | --- | --- |
| Q100 / S01 / 天 | T1 | T1 | 2 | T2 | T4 |
| Q051 / S01 / 天 | T1 | T4 | 2 | T4 | T4 |
| Q037 / S01 / 不 | T2 | UNCLEAR | 5 | T2 | T4 |
| Q027 / S01 / 错 | T4 | T4 | 2 | T4 | T4 |
| Q065 / S01 / 我 | T3 | UNCLEAR | 1 | T2 | T3 |
| Q064 / S01 / 吧 | NEUTRAL | T1 | 2 | T3 | T3 |
| Q031 / S02 / 我 | T3 | T3 | 2 | T3 | T3 |
| Q092 / S02 / 天 | T1 | T3 | 2 | T2 | T1 |
| Q053 / S02 / 晚 | T3 | T3 | 3 | T2 | T3 |
| Q091 / S02 / 跟 | T1 | T1 | 1 | T1 | T1 |
| Q006 / S02 / 去 | T4 | T4 | 5 | T4 | T4 |

For the ten resolved numbered expectations: 6/10 exact matches, two numbered disagreements, and two UNCLEAR/UNUSABLE responses. Numbered-response coverage is 8/10 (80%); conditional expected–human agreement is 6/8 (75%). The two numbered disagreements are S01 second 天 (expected T1, solo T4/c2) and S02 天 (expected T1, solo T3/c2). S01 不 and 我 are UNCLEAR. The additional expected-neutral S01 吧 was called T1/c2; both models chose T3. Including it gives 6/11 full categorical expected–human agreement. These observations do not prove learner-production errors or their frequency.

**B and C. Expanded–human and pilot–human, separately and exploratory only.** All non-UNCLEAR labels happen to be numbered and none is UNUSABLE, giving the same 12-item eligible subset for both models. Expanded agrees on 6/12 (50.0%); pilot on 8/12 (66.7%). Both match on six, pilot alone on two, expanded alone on zero, neither on four. These are descriptive agreements with an insufficient annotation source, not model accuracy or a ranking/selection claim. Four UNCLEAR/UNUSABLE items are excluded from conditional agreement and retained in the distribution; human NEUTRAL count is zero.

| Human confidence subset | Expanded–human agreement | Pilot–human agreement |
| --- | --- | --- |
| all numbered / non-UNCLEAR | 6/12 (50.0%) | 8/12 (66.7%) |
| ≥2 | 5/11 (45.5%) | 7/11 (63.6%) |
| ≥3 | 1/4 (25.0%) | 3/4 (75.0%) |
| ≥4 | 1/2 (50.0%) | 2/2 (100.0%) |

Confidence ≥4 contains only two eligible units, both confidence 5: S02 去 and S03 买. These raw counts are too small for a stable comparison. The preregistered confidence 4–5 AND explicitly CLEAR subset contains only S02 去: both agree 1/1. Missing usability is reported separately and not promoted to CLEAR. No confidence threshold was optimized for a model. Human NEUTRAL would be reported separately with each numbered model choice and excluded from four-tone scores; there are no such learner responses in this export.

Does human comparison improve on expected-tone comparison? On the original ten resolved numbered expectations, expanded–expected is 5/10 and pilot–expected 7/10. Comparing those directly with 6/12 and 8/12 would change denominators. On the same eight units with resolved numbered expectations and eligible human responses, expanded–expected is 4/8 versus expanded–human 5/8; pilot–expected and pilot–human are both 6/8. This is one additional descriptive match for expanded and no net change for pilot, with no validation implication. Across all 11 resolved expectations including neutral, model–expected counts are expanded 5/11 and pilot 7/11, reported separately from four-tone agreement.

**Seven frozen expanded-T2 disagreements.** Every case remains included regardless of confidence or usability.

| Unit ID / QA | Take / target | Expected | Solo / confidence | Expanded / confidence | Pilot / confidence | Deterministic |
| --- | --- | --- | --- | --- | --- | --- |
| learner:4cf712ee935667d1ab00dd9f:1 / Q100 | S01 / 天 | T1 | T1 / 2 | T2 / 0.4769 | T4 / 0.7666 | ABSTAIN |
| learner:4cf712ee935667d1ab00dd9f:4 / Q037 | S01 / 不 | T2 | UNCLEAR / 5 | T2 / 0.9946 | T4 / 0.5760 | ABSTAIN |
| learner:4cf712ee935667d1ab00dd9f:6 / Q065 | S01 / 我 | T3 | UNCLEAR / 1 | T2 / 0.8769 | T3 / 0.9366 | ABSTAIN |
| learner:39e33220c5dec271b192f561:2 / Q092 | S02 / 天 | T1 | T3 / 2 | T2 / 0.8935 | T1 / 0.4274 | ABSTAIN |
| learner:39e33220c5dec271b192f561:3 / Q053 | S02 / 晚 | T3 | T3 / 3 | T2 / 0.7325 | T3 / 0.6183 | ABSTAIN |
| learner:0b44eac1332ea0859ac54d67:2 / Q028 | S03 / 买 | unresolved (T2/T3 alternatives) | T3 / 5 | T2 / 0.6103 | T3 / 0.7135 | ABSTAIN |
| learner:0b44eac1332ea0859ac54d67:4 / Q033 | S03 / 种 | unresolved (T2/T3 alternatives) | UNCLEAR / 3 | T2 / 0.9838 | T1 / 0.6541 | T2 |

First-exposure solo pattern: 0/7 T2, 3/7 T3, 1/7 T1, 3/7 UNCLEAR. Thus four responses name another numbered family and three abstain; two of the four numbered responses are low confidence (c2). The other numbered responses are S02 晚=T3/c3 and S03 买=T3/c5. The overall pattern is mixed between another family and unresolved/low-confidence responses. It does not corroborate the claim that the reviewer independently heard T2 on these first exposures. The exploratory solo labels contradict that narrow corroboration prediction, but are not reliable enough to adjudicate the expanded-T2 hypothesis. Whether expanded detects actual learner T2 realizations or exhibits a learner-domain T2 error remains unresolved. T2 control recall is only 1/6. Among learner repeats, S03 水 changes from T3/c3 to T2/c2; that repeat is reported without replacing its first response and is outside the seven model-disagreement cases.

**Requested primary cases, without special scoring.**

| QA / case | Expected | Solo / confidence | Expanded | Pilot | Deterministic |
| --- | --- | --- | --- | --- | --- |
| Q065 / S01 我 | T3 | UNCLEAR / 1 | T2 | T3 | ABSTAIN |
| Q031 / S02 我 | T3 | T3 / 2 | T3 | T3 | T4 |
| Q063 / S03 想 | unresolved (T2/T3 alternatives) | T3 / 2 | T3 | T3 | ABSTAIN |
| Q028 / S03 买 | unresolved (T2/T3 alternatives) | T3 / 5 | T2 | T3 | ABSTAIN |
| Q033 / S03 种 | unresolved (T2/T3 alternatives) | UNCLEAR / 3 | T2 | T1 | T2 |
| Q118 / S03 水 | unresolved (T2/T3 alternatives) | T3 / 3 | T1 | T1 | ABSTAIN |

S01 我 is UNCLEAR/UNUSABLE, so it cannot arbitrate expanded T2 versus pilot T3. S02 我 is solo T3/c2, both learned models T3, deterministic T4; agreement is not independent truth. S03 想 is solo T3/c2 with both models T3. S03 买 is solo T3/c5, expanded T2, pilot T3; it is a high-value independent-listener case, not an adjudicated model error. S03 种 is UNCLEAR/UNUSABLE despite expanded and deterministic T2. S03 水 is solo T3/c3 while both learned models choose T1. All four S03 expectations remain unresolved. The repeated S03 水 changes T3/c3→T2/c2; S02 晚 remains T3/c3→T3/c2. Neither repeat rescues the gate.

**What remains established.** Native-domain recognition remains strong/replicated. Learner-domain transfer remains **MIXED / unresolved**. Legitimate nucleus/coda pooling remains **NO GENERAL IMPROVEMENT DEMONSTRATED**. Insufficient solo labels neither strengthen nor weaken these model conclusions. They do establish that this solo annotation route did not resolve the evidence bottleneck. Model consensus, model–expected agreement and deterministic–model agreement are never substituted for an independent perceptual reference.

**Strict product criterion and purpose of learner validation.** Benma should be strict when a competent Mandarin listener hears the wrong tone. If expected T3 is produced as perceptually T2-like speech and HuBERT returns T2, correcting the learner is desired behavior. If competent listeners consistently hear T3 but HuBERT returns T2 because of unrelated vowel quality, timing or accent features, that is a learner-domain recognition failure. The validation question is whether model strictness corresponds to Mandarin listener perception. No accent-tolerant pass rule or inference of intended tone is warranted.

**Next decision: C — SOLO LABELS INSUFFICIENT.** Do not use this solo source to evaluate learner transfer. A small independent-listener check is still necessary before calling the recognizer trustworthy for product integration; a giant formal learner benchmark is not required. Exact next action: arrange a separately authorized, unpaid blind review with three independent competent Mandarin listeners, such as willing native-speaking language-exchange contacts or friends. This report proposes the design only; no outreach, packet construction, or new annotation occurs in this pass.

Proposed small packet per listener: **16 accepted learner syllables + 8 native controls + 4 hidden repeats = 28 presentations**. Keep the same 16 learner units and frozen spans/predictions. Balance the eight controls across T1–T4 and neutral, including more than one T2 and T3; one feasible allocation is T1=1, T2=2, T3=2, T4=1, NEUTRAL=2. Use controls with independent listening/crop checks and diverse speakers, chosen without learner-model outcomes. Use two learner and two control repeats, with pairs and spacing fixed before review. Randomize opaque presentation order separately per listener. Hide roles, repeats, Hanzi, pinyin, expected tones, source IDs and every model prediction. Collect tone family, confidence, usability, and both playback flags independently, with no discussion or cross-listener answers before sealing exports. Preserve UNCLEAR/NEUTRAL.

Before collecting the next labels, specify how control/repeat evidence and listener disagreement will be assessed; eight controls are a check, not a precise competence estimate. Do not invent thresholds after seeing model agreement. Review whether the isolated tone-bearing task is too difficult: consider making the existing whole-target audio readily available to everyone, with the tone-bearing crop as an optional additional view. Fix that protocol in advance and report it as a protocol change; do not widen frozen spans or selectively change playback for model disagreements. Keep independent initial judgments even if later acoustic adjudication is needed.

If reliable independent listeners generally agree with frozen HuBERT on learner realizations, learner transfer is sufficient for the next product-integration experiment on this narrow sample: integrate trustworthy learned recognition, preserve linguistic rules, return to physical/manual Benma testing, and validate grading, abstention, explanations and UX. That would not establish population-wide generalization or calibration. If reliable listeners systematically disagree on usable, clearly judged learner units, treat that as evidence of learner-domain model failure after checking crop/reference integrity; then investigate additional labeled learner speech, classifier adaptation, temporal heads or partial encoder fine-tuning. If listeners themselves remain uncertain or inconsistent, improve the perceptual protocol or obtain independent acoustic adjudication; do not force either engineering branch. No adaptation precedes this distinction.

**Road back to manual Benma testing and preserved architecture.** The intended loop is: natural learner speech → ASR/segmentation → learned perceived-tone recognition → independent expected contextual-tone resolution → correctness/concern grading → evidence-supported acoustic coaching → target-versus-heard feedback. Recognition must not receive the expected answer as a shortcut. Linguistic expectations retain lexical tone, sandhi and neutral/contextual realization. Learned recognition identifies acoustic/perceptual family, with neutral/abstention support as appropriate in future work. F0, contour and timing remain the interpretable explanation layer. Show target pronunciation, what Benma heard, mismatching syllables, pitch visualization and specific coaching only where measured evidence supports it. A recognizer T4 prediction alone does not prove a falling contour or justify a diagnosis about recovery/rise. The target-versus-heard idea, such as expected 想 T3 versus heard T4-like, remains intact. Subsequent physical tests should focus on false corrections, grading quality, explanations, confidence/abstention, usability and sentence-level feedback; no such product work is implemented here.

**Reproducibility and freeze.** 413 deterministic baseline hashes, 19012 files in the packet starting-state snapshot, and 21 packet-sealed artifact hashes verify unchanged. Both learned model files, native and learner releases, and saved expanded/pilot/deterministic predictions across primary and supplemental phases verify against their frozen seals. No model was loaded or run. Production pronunciation inference, grading, app UI, APIs and deployment files are unchanged; changes are confined to new research files. No training, tuning, adaptation, benchmark edits, production integration, commit, push or deployment occurred.

| Artifact | SHA-256 |
| --- | --- |
| Canonical blind packet | f5c041a22f03ddf41337472fd494397a055adfee9fd16ba234c75d3ea2ead6a4 |
| Original human export | 00d21f8b43aea003eab6f9cfcd2c96363754dcca897ed3fc35ddad067d9b99d1 |
| Hidden answer key | 2a7fc0014649f6c7bf99686ed0cf3195806c2fe795b55358dd35ee212f009795 |
| Learner release manifest | 8024a51df91e60b9e336189cd9b04dfbf2d5d8c530fd0656778c731e1306f4ae |
| Native release | 3bb07638eb87fe470e51831bab1e99681bfe01482136ae7f11eb7886ecd1b315 |
| Primary prediction file | acdc7ffb5952752eff2ba9c9b7bf93c18649ba60d5cee2a6c5c04b6988f88f7d |

Blinding verification: the sealed review page remains byte-identical and passes the visible leakage audit; it exposes no expected labels, roles or model results. Selection/order/audio were frozen before saved model outputs were joined into the private key. The export was preserved before any analysis. Thus the audited annotation pipeline supplied no model-output influence. Independent memory or filesystem access by the reviewer cannot be verified from these artifacts, so absolute psychological independence is not claimed.

**Validation and report paths.** Focused lightweight tests cover schema/IDs/telemetry, key joins, control-only scoring, repeat links and abstention, fixed preregistered checks, frozen-gate integrity, learner population, exploratory-only guard, neutral separation, confidence strata, T2 cases, deterministic report generation, no training/inference entry points, baseline preservation and whitespace. See `data/generated/realized-tone-analysis-v1-20261019/tests.log` and `07-test-validation.json` for executed results. No native training, embedding generation, packet regeneration or browser listening simulation is required.

Final narrative: `research/perceptual-tone-model/realized-tone-reliability-first-report.md`. Final machine-readable analysis: `data/generated/realized-tone-analysis-v1-20261019/05-final-exploratory-analysis.json`. Ordered records in that directory: `human-export.original.json`, `01-export-validation.json`, `02-controls-and-repeats.json`, `03-reliability-gate.json`, `03-registered-checks.json`, preserved preliminary `04-learner-exploratory.json`, final `05-final-exploratory-analysis.json`, `06-freeze-verification.json`, and test/validation logs. All paths are relative to the research package unless prefixed with `research/`.

New research source/report files in this pass: `perceptual_tone/blind_analysis.py`, `perceptual_tone/blind_analysis_report.py`, `scripts/blind_analysis.py`, `tests/test_blind_analysis.py`, and `realized-tone-reliability-first-report.md`. Earlier uncommitted research work and sealed inputs were retained unchanged. Reproduce the report with `benchmark/pronunciation_v2/.venv/bin/python research/perceptual-tone-model/scripts/blind_analysis.py`; existing outputs are compared, never overwritten. Run focused tests with `PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p test_blind_analysis.py -v`.

The solo blind annotation failed its preregistered reliability gate, so its learner labels remain exploratory. Benma should remain strict when learner speech sounds like the wrong Mandarin tone. Resolve whether HuBERT tracks competent Mandarin listener perception through a small independent multi-listener check, then either integrate learned recognition and return to physical Benma testing or, only if listener disagreement is systematic, investigate learner-domain adaptation.
