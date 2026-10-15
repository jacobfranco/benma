# Minimum Learner-Concern Threshold continuation — 2026-10-13

The Minimum Learner-Concern Threshold continuation is complete.

The existing working tree was preserved. Only the production learner grader changed; all other executable changes are grading tests, a browser test, or audit scripts. No reset, revert, commit, push, deployment, provider call, upstream retuning, or saved-analysis rewrite occurred.

**An incompatible acoustic score leader does not automatically imply learner-facing concern.**

The product burden of proof is now: GREEN means **no meaningful learner concern**; AMBER means **meaningful but non-decisive learner concern**; RED means **decisive learner correction**; GRAY means **cannot judge**. Green does not claim that the acoustic classifier agrees with the expected family.

## Exact grading order

1. **GRAY:** existing missing-pitch, unreliable/UNAVAILABLE evidence, unresolved expectation, standalone neutral and invalid/nonfinite-input checks are unchanged. Neutral constituent non-veto handling is unchanged.
2. **Trustworthy ambiguity:** existing UNCLEAR interpretation, unclear reported family or inconsistent reported/best family remains AMBER. See the individual ambiguity review below; these are interpretation concerns, not unavailable measurements.
3. **Compatible numbered family:** GREEN with at least seven probes and at least 6/7 agreement, independent of family support, excursion or strength. Existing insufficient-probe/unstable-compatible interpretation stays AMBER. Contextual acceptable-family resolution is unchanged.
4. **Incompatible numbered family:** apply the unchanged RED certificate first. If it fails, require **every** minimum-concern gate below for AMBER. Otherwise return GREEN with reason `insufficient_mismatch_concern` and message “There is not enough evidence of a pitch problem here.” No observation is relabeled.

| Evidence | AMBER minimum concern | RED, unchanged |
| --- | ---: | ---: |
| Winner support | ≥0.65 | ≥0.90 |
| Maximum support over every acceptable family | ≤0.40 | ≤0.20 |
| Winner minus maximum acceptable support | ≥0.50 | ≥0.70 |
| Winner minus strongest other family, bounded by supplied classifier margin | ≥0.45 | ≥0.60 |
| Family clarity | ≥0.90 | ≥0.90 |
| Probe count | ≥7 | ≥7 |
| Winner agreement across probes | ≥6/7 | 100% |
| Context/reliability | Trustworthy numbered reported/best family, resolved expected family, winner outside acceptable set | Same |

The AMBER certificate applies only after RED fails. Missing a concern gate is insufficient affirmative evidence to warn about a **numbered incompatible leader**, not a new reliability classification. True family ambiguity and compatible perturbation uncertainty retain their separate existing rules. Scores are heuristic supports, not probabilities. Gesture strength never chooses color.

## Corpus derivation

The four weak historical numbered mismatches have support .447657–.541947 and runner-up gaps .198090–.429081. The five remaining historical mismatches have support .719343–.923052; the older physical AMBER control is .711321. Those six meaningful concerns all have runner-up gaps ≥.487712, acceptable gaps ≥.615434, acceptable support ≤.307618, clarity ≥.995495, and 7/7 probe agreement.

The .65 support floor lies in the observed .542–.711 gap; .45 runner-up separation lies in the .429–.488 gap. The .40 acceptable-support cap and .50 acceptable-margin floor conservatively admit the strong .923 valley with .308 expected-rise support while refusing an insufficiently separated acceptable alternative. These safeguards are not independently fitted listener thresholds: the corpus does not isolate every boundary. Clarity .90 reuses the existing clean-evidence standard; seven probes with 6/7 agreement reuses the compatible policy's established stability tolerance. RED still requires all probes.

Support alone is insufficient: tests hold high support while independently exercising plausible acceptable support, insufficient acceptable separation, a competing incompatible family, low clarity, incomplete/unstable probes and a smaller supplied classifier margin. A 51-step synthetic ladder smoothly raises incompatible support from .45 to .95 while lowering acceptable support from .20 to zero and visits GREEN → AMBER → RED without reversal.

## Historical replay and all newly green leaders

The immediate arrival baseline is [concern-baseline.json](concern-baseline.json). The older pre-conservative acoustic/measurement baseline remains [baseline.json](baseline.json). `results.json.concernDistribution` and `concernChanges` describe **this continuation**; `distribution` and `historicalChanges` retain comparison against the earlier pre-conservative baseline.

| Grade | Arrival | Current |
| --- | ---: | ---: |
| GREEN | 16 | 20 |
| AMBER | 20 | 16 |
| RED | 3 | 3 |
| GRAY | 14 | 14 |

All 53 units replayed. Exactly four AMBER→GREEN changes occurred; no other historical colors changed. All four measurements are trustworthy and all four acoustic families remain numbered and incompatible. The saved [retained-contour sheet](red-contours.svg) was visually inspected for every softened case, together with all family scores, contextual alternatives, both margins, clarity and probes. This is an engineering evidence review, not a new listening study.

| Fixture:syllable | Expected | Observed | Support | Acceptable support | Acceptable gap | Runner-up gap | Clarity | Probes | Old→new |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 4b9dbd2b:要 | T4 | T2 | 0.480073 | 0.000000 | 0.480073 | 0.377040 | 0.999964 | 7/7 | AMBER→GREEN |
| a5acd04c:我 | T3 | T4 | 0.541947 | 0.000000 | 0.541947 | 0.358397 | 0.993358 | 7/7 | AMBER→GREEN |
| a5acd04c:一 | T2 | T1 | 0.447657 | 0.000000 | 0.447657 | 0.198090 | 0.999291 | 5/7 | AMBER→GREEN |
| b9067bec:想 | T3 | T4 | 0.484375 | 0.000000 | 0.484375 | 0.429081 | 1.000000 | 7/7 | AMBER→GREEN |

- **4b9dbd2b:要:** A rise ends in a substantial downward retreat. T2 wins at only .480 with .377 separation. Seven agreeing probes repeat the same weak interpretation; consistency cannot supply missing family support. The substantial retreat and low absolute support do not warrant a learner warning; grade green.
- **a5acd04c:我:** The contour first rises and crests before falling. The weak fall scores .542 with .358 separation. The fall is only a marginal score leader over a mixed crest-and-fall gesture. Stable probes cannot supply enough affirmative support for a learner warning; keep the family and grade green.
- **a5acd04c:一:** A shallow crest, dip, and terminal recovery compete within this contour. The level winner scores .448 with .198 separation and only 5/7 probe agreement. T3 (.250) and T4 (.190) remain alternatives. These independent weak-support, narrow-margin and instability signals do not establish a learner problem; grade green while preserving the level score leader.
- **b9067bec:想:** An early dip and a later hump precede the final fall. The falling family is stable but only .484 supported. A .429 margin against weak alternatives cannot turn low absolute support into a meaningful learner concern. The mixed dip/hump/fall does not establish a coherent wrong family; grade green.

Zero expected-family support is not affirmative proof of a wrong tone. In these four cases a weak absolute winner cannot earn a warning merely by beating even weaker alternatives. Three have perfect probe agreement; that repeats the weak ranking without making its evidence stronger. None meets the RED certificate, and all eight existing RED controls remain RED.

## Every remaining numbered AMBER mismatch

These are all six recorded numbered mismatch concerns across the historical and older/newest physical replays. All have trustworthy evidence, clarity ≥.995495 and 7/7 agreement. The newest human recording has no numbered AMBER mismatch.

| Fixture:syllable | Expected | Observed | Support | Acceptable support | Acceptable gap | Runner-up gap | Clarity | Probes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 8d252264:果 | T3 | T2 | 0.758660 | 0.000000 | 0.758660 | 0.725584 | 0.995495 | 7/7 |
| 4b9dbd2b:一 | T2 | T4 | 0.719343 | 0.000000 | 0.719343 | 0.487712 | 1.000000 | 7/7 |
| 4b9dbd2b:苹 | T2 | T3 | 0.923052 | 0.307618 | 0.615434 | 0.615434 | 1.000000 | 7/7 |
| 8faf1a90:一 | T2 | T4 | 0.803377 | 0.000000 | 0.803377 | 0.726324 | 0.998984 | 7/7 |
| a5acd04c:苹 | T2 | T4 | 0.866789 | 0.000000 | 0.866789 | 0.844068 | 1.000000 | 7/7 |
| 208711dc:想 | T3/T2 | T4 | 0.711321 | 0.000000 | 0.711321 | 0.632461 | 1.000000 | 7/7 |

- **8d252264:果:** The sustained stepwise rise, .759 support, .726 runner-up separation and 7/7 probes give affirmative reason to check the missing low/dip. The early reversal and small gap keep this below decisive correction; retain amber.
- **4b9dbd2b:一:** The broad fall ends in a rebound. The fall has .719 support and T3 remains at .232, leaving only .488 runner-up separation. The explicit T2 surface rule is preserved, but a categorical correction is too strong.
- **4b9dbd2b:苹:** An asymmetric valley has a much larger recovery than initial fall. T3 is strong (.923), yet expected T2 retains .308 support. This is exactly the case where a high winning score alone must not erase a plausible acceptable explanation.
- **8faf1a90:一:** The small fall includes a flattened middle and terminal wavering. T4 has .803 support with 7/7 probes and no T2 support. It is a plausible mismatch, but does not reach the conservative .900 support floor. Weak strength is not the veto.
- **a5acd04c:苹:** A small opening crest precedes a large clean fall. The fall scores .867 with .844 separation and 7/7 probes. This is the closest softened historical red to the support cutoff; it remains a meaningful amber concern, not green. Its support falls below the .923–.976 high-support cluster.
- **208711dc:想:** The older human contour falls, briefly recovers/levels, then falls again. Its T4 family has .711 support and 7/7 probes. It is less decisive than the newest .974 fall; retain possible-mismatch advice in amber. No gesture-strength gate is involved.

The browser additionally exercises a constructed moderate rise against T4: support .755287, runner-up .251783, separation .503504, no acceptable T4 support, clarity 1 and 7/7 probes. This stays AMBER. The prior browser's .658588 rising control had only .236268 separation from level and now correctly becomes GREEN; it is retained as the weak-mismatch browser control, with its original geometry unchanged. A separate stronger constructed input supplies the moderate control.

## Trustworthy ambiguity and green audit

All ten historical trustworthy ambiguities remain AMBER, as does the existing compatible `ee8a8b32:我` with only 5/7 stable T3 probes. No ambiguous label becomes a numbered mismatch. Unreliable cases remain GRAY.

The cases with plausible expected-family support were explicitly reconsidered: `8d252264:一`, `8faf1a90:要`, `a5acd04c:果`, `b9067bec:我` and `5c70f317:想` remain ambiguous because the retained geometry and probes support conflicting direction/family readings. The warning is about that unresolved gesture, not the technical score leader. This deliberately preserves the prior interpretation-uncertainty policy; its perceptual calibration is still an uncertainty.

- **89cee47e:想:** The measured gesture spans 5.407 semitones with opposing movement; T3 support is zero and all seven probes remain unclear. The mixed contour gives reason to ask for a clearer low/dip, without claiming that the weak T4 leader is correct.
- **6b5b2135:我:** A 3.461-semitone recovery with direction reversals competes with a low/dip interpretation; four probes choose a rise and three abstain, while expected T3 has only .084 support. This mixed rise/low interpretation remains a possible concern.
- **6b5b2135:想:** Substantial opposing movements (1.520-semitone fall and 3.413 recovery in the family features) do not resolve into a coherent low/dip; all probes abstain and T3 support is zero. Mixed geometry, not the weak T4 leader, warrants amber.
- **ee8a8b32:想:** The 2.323-semitone mixed gesture lacks a coherent low/dip, with zero T3 support and seven unclear probes. The concern is conflicting movement, not the weak level score leader.
- **8d252264:一:** The .410-semitone dip before a 2.130 rise creates real rise/valley competition: probes return T3 four times, expected T2 once, and unclear twice. T2 support .428 is plausible, so no correction is justified; preserve the specific interpretation warning.
- **8d252264:苹:** The 3.400-semitone mixed movement is split almost equally between rising and falling duration; every probe abstains. A nominal expected T2 lead of .206 does not resolve the contradictory gesture, so retain the ambiguity warning.
- **8faf1a90:要:** The expected fall competes with a level/low interpretation in a 1.140-semitone gesture; probes yield six unclear results and one T3. Expected T4 support .286 remains possible, but the measured direction is unresolved enough to mention cautiously.
- **a5acd04c:果:** The .806-semitone dip is followed by a 5.178-semitone rise; T3 and T2 differ by only .052, and four probes abstain. The dominant recovery makes a genuine rise/valley question despite plausible expected T3.
- **b9067bec:我:** A 1.695-semitone family fall with little recovery competes with acceptable reduced T3 (.403); five probes choose T4 and two abstain. This is a real fall-versus-low ambiguity, not enough for correction but worth a cautious check.
- **5c70f317:想:** A dip, recovery and opposing terminal movement span 2.503 semitones; six probes abstain and only one retains T3. The expected-family leader does not settle the mixed contour, so the trustworthy ambiguity stays amber.

The five natural calibration ambiguities also stay AMBER: nearly flat rise/level, rise/valley, fall/low, level/valley and opposing-hump interpretations. Their raw scores and all probe results remain unchanged in `results.json.calibration`. The supplemental `projection:89cee47e:想` repeats the same historical ambiguity. No ambiguity or neutral rule was edited.

GREEN is asymmetric by design: a stable compatible family needs no ideal-strength proof, and a numbered incompatible leader needs affirmative evidence before it can raise concern. The four newly green historical leaders are weak, not decisive incompatible realizations. Synthetic high-support cases with insufficient separation or stability test the same burden of proof. The unchanged RED check runs first, so the concern fallback cannot swallow a valid RED certificate.

## Physical regressions

| Newest human unit | Observed/support | Current grade | Behavior |
| --- | --- | --- | --- |
| 我 | T3 / .878212 | GREEN | “Dip is shallow.” retained |
| 想 | T4 / .974079 | RED | Clean fall; T3/T2 support zero; incompatible; 7/7 probes |
| 买 | T3 / .821823 | GREEN | “Dip is shallow.” retained |
| 这 | T4 / .971139 | GREEN | Same retained frames |
| 个 | Unavailable neutral | GRAY | Unreliable neutral does not veto |
| 这个 | T4 head + neutral | GREEN | Same aggregation and neutral roles |

Newest human ID: `cc8be88b-1211-4ef1-ae7e-0ebf8b99327c`. Newest background/washer fixture remains GRAY throughout. Exact canonical-WAV replay reproduced both published newest physical fixtures; every selected F0 equals its retained raw F0. No fixture was rewritten.

Older human `208711dc-c437-4afe-b6d3-2aa0e16fb7cb:想` stays **AMBER**, T4 support .711321, acceptable support zero, runner-up separation .632461, clarity 1 and 7/7 probes. Older physical replay preserves its shape, scores, contextual expectations, measurements and neutral roles; its 我 stays GREEN with shallow-dip coaching.

## Every remaining RED

All three historical REDs, the newest human physical RED and four established constructed controls remain RED. Each clears **every** unchanged gate; all have clarity effectively 1, at least seven probes with 100% agreement, and no contextual licensing. No RED changed color in this continuation. Chunk REDs inherit these same constituents.

| Fixture/control | Expected | Winner | Support | Acceptable support | Acceptable gap | Runner-up gap | Clarity | Probes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4b9dbd2b:个 | T4 | T3 | 0.954732 | 0.049255 | 0.905477 | 0.855429 | 1.000000 | 7/7 |
| 8faf1a90:我 | T3 | T4 | 0.954739 | 0.002195 | 0.952544 | 0.952544 | 1.000000 | 7/7 |
| 8faf1a90:苹 | T2 | T4 | 0.976289 | 0.000000 | 0.976289 | 0.967672 | 1.000000 | 7/7 |
| constructed:sandhi-full-valley | T2 | T3 | 0.967742 | 0.000000 | 0.967742 | 0.906952 | 1.000000 | 7/7 |
| constructed:stable-fall-against-t3 | T3 | T4 | 0.954116 | 0.008129 | 0.945987 | 0.945987 | 1.000000 | 7/7 |
| constructed:这个-mismatch:这 | T4 | T2 | 0.968617 | 0.000000 | 0.968617 | 0.968616 | 1.000000 | 7/7 |
| constructed:我想:我 | T2 | T3 | 0.968213 | 0.000000 | 0.968213 | 0.908724 | 1.000000 | 7/7 |
| cc8be88b:想 | T3/T2 | T4 | 0.974079 | 0.000000 | 0.974079 | 0.974079 | 1.000000 | 7/7 |

The recorded corrections remain a deep valley against expected T4 (`4b9dbd2b:个`), clean falls against T3 (`8faf1a90:我`, newest 想) and a clean fall against T2 (`8faf1a90:苹`). The synthetic controls retain full incompatible valleys, a full fall or a full rise. Focused tests still exercise all twelve ordered incompatible numbered-family pairs as RED, independently of full/weak gesture strength.

## Presentation and validation

No UI redesign or production presentation code changed. Labels remain GREEN “Pitch acceptable”, AMBER “Pitch may be off”, RED “Pitch differs” with corrective mismatch wording, and GRAY “Pitch unavailable”. Newly green mismatch leaders keep their acoustic “Most like Tone …” detail, with no AMBER warning; grading feedback says there is insufficient evidence of a problem. Existing independent coaching and chunk aggregation remain intact.

- Focused grading/aggregation/physical tests first: **124 passed, six suites**.
- `npm run validate`: **lint, typecheck, 757 tests in 45 suites passed**.
- Five established Node audit files passed, including the updated conservative grading audit and original acoustic/measurement invariants.
- Historical PCM replay: **13 recordings / 53 units**, corpus and selected projection byte-identical.
- Newest canonical-audio physical replay and older physical grading replay passed; no saved analysis was rewritten.
- Expo web export passed. All six browser suites passed at **320/390/412 px**, **24 suite-fixture/viewport cases**: newest physical, older physical, tone feedback, measurement fidelity, pronunciation chunks and product feedback. Within each tone-browser case, weak-mismatch GREEN, moderate-mismatch AMBER, decisive RED, true ambiguity and unavailable evidence are explicitly checked.
- Browser assertions preserve canonical playback, neutral non-veto, graph coordinates, history, layout and accessibility behavior. No page errors. Weak-mismatch and moderate-mismatch 320 px screenshots were visually reviewed.
- `git diff --check`, arrival-relative whitespace and scope checks passed. All 186 frozen upstream source/input hashes match; production changes are confined to `learnerPitchGrade.ts`. `pitchExpectation`, RED constants and the RED decision expression are byte-identical to arrival.

**Acoustic-family changes: 0. Measurement changes: 0. Selected-frame changes: 0.**

Reproducible commands, log digests and results: [concern-validation.json](concern-validation.json). Browser reports: [concern-browser-results.json](concern-browser-results.json). Arrival-relative file inventory and diff stat: [concern-changed-files.md](concern-changed-files.md). Existing `validation.json`, `browser-results.json`, `changed-files.md` and `finalization.json` describe the prior Conservative Native-Speaker pass and are preserved as prior-stage records.

No unrelated backend suites were repeated. The prior two API target-revision failures remain outside scope and were not rerun; their prior evidence remains unchanged. Browser APIs are mocked and use saved canonical audio, not a new live device recording.

## Remaining uncertainty

This is conservative calibration against a small selected diagnostic corpus, not a native-tutor listening study or an error-probability model. The support and runner-up floors have observed separation; the acceptable-support, clarity and probe safeguards lack independent per-boundary corpus estimates. Real borderline outcomes and the retained ambiguity policy still need independent listening validation. No claim is made that every tutor would agree or that the historical AMBER percentage predicts ordinary product usage.

The Minimum Learner-Concern Threshold continuation is complete. No commit, push or deployment occurred.
