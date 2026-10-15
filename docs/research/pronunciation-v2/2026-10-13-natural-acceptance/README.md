# Natural Acceptance + Pitch Branch Robustness — 2026-10-13

The Natural Acceptance + Pitch Branch Robustness pass is complete. No further implementation work is needed.

This pass continued the existing working tree. The finalization continuation changed only audit documentation and evidence records. No reset, commit, push, deployment, database update, or provider reanalysis was performed. Existing analyses retain their saved selection; the new policy applies to newly analyzed audio and the explicit local replays recorded here.

## 1. Natural-match learner grading

Tone family, physical gesture magnitude, and correctness confidence remain separate. A trustworthy compatible numbered family is green when all of these hold:

| Condition | Required value |
| --- | --- |
| Family decision / evidence | `NUMBERED` / `trustworthy`, best family equals reported tone |
| Winning family support | ≥ 0.70 |
| Winner–runner-up margin | ≥ 0.30 |
| Perturbation consensus | At least seven probes, ≥ 6/7 agree with the reported family |
| Family clarity | ≥ 0.90 |
| Gesture excursion | No additional minimum for green |

These support values are heuristics, not calibrated probabilities. Both full and weak gestures must meet the confidence gates. Compatible borderline evidence remains amber; trustworthy conflicting families remain red; ambiguous or unavailable evidence remains gray. A clear T4 does not become acceptable T3 because the target is T3.

Weak gesture coaching survives green grading and single-constituent chunk aggregation. The newest human 我 and 买 both still display **“Dip is shallow.”**

The expectation adapter has a bounded context fallback: a lexical T3 with saved `prosodic_grouping_unresolved` may accept T3 or T2 when the next resolved-reading character is an adjacent lexical T3. Explicit saved surface tone takes precedence; a final T3 receives no such fallback; T4 is never licensed by it. This changes only the learner expectation, not lexical/surface resolution, acoustic family scoring, or saved evidence. It produced no expectation changes in the 53 historical units. The context distinction is consistent with the prosodic dependence of longer T3 chains described in this [Speech Prosody 2022 study](https://www.isca-archive.org/speechprosody_2022/tu22_speechprosody.pdf).

## 2. Newest physical takes

The fixture identities, capture times, and canonical WAV SHA-256 hashes are in [physical-provenance.json](physical-provenance.json). The private audio was read locally; audio files are not copied into this audit. These are saved physical takes, not new live recordings made during validation.

Human analysis: `cc8be88b-1211-4ef1-ae7e-0ebf8b99327c`, captured 2026-10-13 14:11:33 UTC.

| Unit | Before | After | Interpretation |
| --- | --- | --- | --- |
| 我 | Trustworthy weak T3, amber | Same weak T3, green | Support 0.878212, margin 0.700475; 7/7 probes; “Dip is shallow.” |
| 想 | Trustworthy full T4, red | Same full T4, red | Support 0.974079; a clear fall conflicts with T3/T2 expectations. |
| 买 | Trustworthy weak T3, amber | Same weak T3, green | Support 0.821823, margin 0.616767; 7/7 probes; “Dip is shallow.” |
| 这 | Unavailable because of the raw branch jump | Trustworthy full T4, green | Original coherent 14-frame fall survives; seven certified ambiguous branch frames are rejected across the recording. |
| 个 | Unavailable, neutral non-veto | Unavailable, neutral non-veto | Only two retained samples after branch exclusion; no independent green numbered-tone claim. |
| 这个 | Gray | Green | Trustworthy 这 plus an eligible unreliable neutral dependent; the neutral policy is unchanged. |

The primary 这 samples run from 1.5024 to 1.6324 s and fall from 129.347 to 96.463 Hz. The branch runs from 1.6724 to 1.7324 s: three samples belong to 这, one lies between aligned units, and three belong to 个. The complete seven-frame raw branch is examined before any character projection. The later 186 Hz island begins at 1.8024 s, 70 ms after the branch; it is not hidden by truncating the branch at the 这 boundary.

Google/background analysis: `8ae4e60f-964b-480a-b9c7-0c44592841fc`, captured 2026-10-13 14:20:31 UTC. Persistent low-band energy extends before and after speech. Before this pass, 我/想/买/这 were already unavailable, but the contaminated 个 acquired a weak T3 family and neutral acceptance. After rejection, **all five syllables have unavailable pitch feedback and no numbered family**; 这个 stays gray. The recording is a noise-control fixture, not a speech pass-rate target.

The background rule marks **160 raw low-frequency selections** with `persistent_background_periodicity`. This count includes frames already excluded by earlier gates; it does not mean 160 previously retained samples were removed. No replacement F0 is inferred. Remaining measurable fragments do not establish a trustworthy family.

## 3. Candidate-supported ambiguous branch rejection

The detector consumes recording-wide acoustic points, without text, expected tone, ASR, alignment, or character ownership. Raw voiced islands split at timestamp gaps greater than 15 ms. Every condition below is required; one favorable candidate alone is insufficient.

| Criterion | Exact implemented condition | Newest human 这 evidence |
| --- | --- | --- |
| Primary support | ≥12 raw frames and endpoint extent ≥110 ms (about 120 ms supported at a 10 ms hop) | 14 frames; 130 ms extent / 140 ms support |
| Position | Branch immediately follows the primary raw island, with gap >15 ms and ≤50 ms | 40 ms gap |
| Branch support | 2–7 frames, ≤half the primary count, extent ≤60 ms (about 70 ms support) | Seven frames; ratio 0.5; 60 ms extent / 70 ms support |
| Boundary jump | Strictly >6 and <15 semitones | 8.678308 semitones |
| Primary selection | Every primary frame quality-usable and selected | All 14 satisfy this |
| Primary coherence | Maximum adjacent step ≤1.5 semitones | 0.830992 semitones |
| Primary periodicity | Median ≥0.75 | 0.8854 |
| Filter agreement | Comparison F0 exists for every primary frame and differs by ≤1 semitone | Maximum 0.007539 semitones |
| Primary candidate preference | Selected periodicity minus strongest candidate >6 semitones away is ≥0 on every frame; median advantage ≥0.05 | Minimum 0.0477; median 0.12705 |
| Alternate relationship | Each branch frame has an alternate 12±1.5 semitones from its raw selection, inside the primary frequency envelope expanded by ±1 semitone | All seven have qualifying approximately 122–128 Hz candidates |
| Alternate support | Every alternate strength ≥0.40 and ≥75% of the frame's selected periodicity; ≥two alternates have strength ≥0.50 | All seven pass; six exceed 0.50 |
| Branch stability | Every branch value within 2 semitones of its first value | Maximum 1.584117 semitones |
| Repeated switching | Reject exemption if an incoming or outgoing neighboring island has a >6-semitone jump across a gap ≤50 ms | No qualifying neighboring repeated switch |
| Alignment independence | Evaluate the whole raw island, including energy-gated and unowned frames; never clip at character boundaries | Full branch spans 这, the alignment gap, and 个 |

The branch candidates are evidence of ambiguity, not replacement values:

| Time (s) | Raw Hz / strength | Qualifying alternate Hz / strength |
| --- | --- | --- |
| 1.6724 | 58.433 / 0.6718 | 123.767 / 0.5808 |
| 1.6824 | 58.479 / 0.7585 | 122.836 / 0.6906 |
| 1.6924 | 62.785 / 0.7130 | 127.251 / 0.6774 |
| 1.7024 | 64.032 / 0.8220 | 128.118 / 0.6387 |
| 1.7124 | 63.445 / 0.6132 | 124.699 / 0.6081 |
| 1.7224 | 62.609 / 0.5404 | 123.430 / 0.5673 |
| 1.7324 | 60.697 / 0.5090 | 122.100 / 0.4089 |

Accepted rejection sets `quality_usable=false`, `selected_f0_hz=null`, and `selection_reason=candidate_supported_ambiguous_branch`. Existing environmental rejection keeps its reason. Raw F0 and candidates are untouched.

Comparable or sustained branches fail the duration/count tests. Unsupported branches fail candidate tests. An ambiguous or weak primary fails coherence, selection, periodicity, filter, or preference tests. Repeated switching fails the neighboring-island test. There is no general exemption for low endings.

Only the explicit candidate certificate can retire the frontend raw-jump veto. Backend eligibility independently rechecks the retained primary only on native tracks with at least twice as many selected samples as certified exclusions and no more than one other missing raw sample, which must be energy-gated. The original raw diagnostics remain present. The backend contour calculation excludes certified frames from interpretation while preserving original raw maximum jump and frame count; newest 这 becomes `4-like`. No candidate is copied into the retained track.

## 4. Recording-level persistent low-frequency contamination

The detector uses audio spectra independently of F0 selection. It does not modify VAD, silence detection, alignment, or pitch ownership.

1. Compute DC-removed Hann-window spectra over 200 ms windows at a 50 ms hop.
2. Define a quiet-background **proxy** as 120–4000 Hz power ≤8% of the recording maximum in that band. These are not provider-labeled non-speech windows.
3. A quiet window is low-band dominated when 40–80 Hz power is ≥65% of 40–4000 Hz power and its low-band peak is 50–75 Hz.
4. Require ≥10 dominated quiet windows, ≥70% of all quiet windows, and first-to-last dominated-window span ≥max(0.6 s, 60% of recording duration).
5. Require the 90th–10th percentile spread of dominated-window peak frequencies to be ≤15 Hz. This is a low-band concentration and peak-stability test, not an additional spectral-line-width measurement.
6. Only with that recording-level proof, reject raw F0 in [45, 80) Hz whose existing local low-frequency energy fraction is ≥0.45. The previous global per-frame 0.70 contamination threshold remains unchanged.

The washer fixture has **27/28** dominated quiet windows, a **2.45 s** background span over a 2.6703 s recording, and peaks spanning **50–70 Hz** with the required quantile stability. It triggers 160 explicit rejections. The human fixture has only 2/29 dominated quiet windows and does not trigger.

Protection for low-pitched speech comes from independent persistence during quiet high-band intervals plus local spectral corroboration, not from an assumption that every low F0 is noise. Synthetic harmonic 65 Hz speech, clean speech, and transient rumble do not trigger the recording detector; hum plus speech does. A sustained real low branch receives no candidate exception. These are bounded controls, not a guarantee for all low voices or mixed sources.

All historical recordings fail both the ten-window minimum and 70% quiet-window fraction:

| Recording | Dominated / quiet windows | New selected-frame changes |
| --- | --- | --- |
| d47274bc | 0 / 95 | 0 |
| 7e6b6fe9 | 1 / 25 | 0 |
| 8faf1a90 | 0 / 25 | 0 |
| 6b5b2135 | 4 / 39 | 0 |
| 8d252264 | 0 / 48 | 0 |
| ee8a8b32 | 3 / 54 | 0 |
| 5c70f317 | 0 / 18 | 0 |
| a5acd04c | 0 / 30 | 0 |
| 89cee47e | 1 / 31 | 0 |
| 4b9dbd2b | 0 / 85 | 0 |
| 40357072 | 0 / 41 | 0 |
| 0b194cf9 | 1 / 22 | 0 |
| b9067bec | 0 / 11 | 0 |

Candidate rejection also marks zero frames in each of these 13 recordings. Canonical audio hashes were verified. [historical-rejection-audit.json](historical-rejection-audit.json) records each detector result. **13 historical recordings: selected-frame changes from new artifact rejection = 0.**

## 5. Manual review of all four historical grade changes

All four remain trustworthy **weak T3**, retain the same acoustic family and selected measurements, and have 7/7 matching probes: first-point deletion, last-point deletion, every-tenth deletion, early/late timing perturbation, and the two region-scale probes. Clarity is 1.000000, 1.000000, 0.999988, and 0.999963 respectively. Values below are rounded; [results.json](results.json) retains full precision and individual observations.

| Fixture / syllable | Family / support | Runner-up / support | Margin | Strength / probes | Old → new | Retained coaching |
| --- | --- | --- | --- | --- | --- | --- |
| 0b194cf9 / 我 | T3 / 0.884493 | T2 / 0.185660 | 0.698833 | Weak / 7 of 7 | Amber → green | Dip is shallow. |
| 40357072 / 想 | T3 / 0.760900 | T2 / 0.165848 | 0.595052 | Weak / 7 of 7 | Amber → green | Dip is shallow. |
| 40357072 / 五 | T3 / 0.850589 | T2 / 0.220538 | 0.630050 | Weak / 7 of 7 | Amber → green | Dip is shallow. |
| 5c70f317 / 我 | T3 / 0.834863 | T4 / 0.245508 | 0.589354 | Weak / 7 of 7 | Amber → green | Recovery is weak. |

- **0b194cf9 / 我:** Both valley limbs are coherent. Family separation and all probes justify confidence; limited physical excursion was the sole prior amber gate.
- **40357072 / 想:** The stable valley passes support, margin, clarity, and perturbation gates. No structural or raw-ambiguity waiver is involved.
- **40357072 / 五:** The coherent shallow valley has clear T3 support. Its weak magnitude remains useful coaching, with unchanged family, timing, and points.
- **5c70f317 / 我:** Supported lowering and recovery favor T3 over T4 by 0.589354. Weak recovery does not negate the stable family match and remains explicit coaching.

The 53-unit replay has **zero acoustic-family changes**, exactly these four grade changes, and no unexplained drift. Counts change from green 12 / amber 5 / red 12 / gray 24 to green 16 / amber 1 / red 12 / gray 24. The remaining amber `ee8a8b32:我` has support 0.659824 and only 5/7 consensus, so it fails the confidence gates.

Separate saved physical fixtures outside that 53-unit corpus also show the intended policy effect: older Google `df7476d5` 想 and saved `e5c17b4e` 想 move from amber to green with stable weak T3 evidence. Older human `208711dc` 我 stays amber. These are distinct recordings, not the newest washer recording, and are not counted among the four historical changes.

## 6. Corruption controls and conservative evidence boundary

| Frozen 买 fixture | Result | Reason |
| --- | --- | --- |
| 89cee47e | Unavailable | `raw_tracker_discontinuity` |
| e5c17b4e | Unavailable | `missing_critical_support` |
| df7476d5 | Unavailable | `contradictory_fragments` |
| 430fcc2e | Unavailable | `insufficient_support` |

Comparable/sustained branches, missing alternate candidates, weak or competing primary paths, and repeated switching receive no exemption. Ambiguous level-versus-direction cases remain amber or gray; full magnitude alone does not bypass correctness confidence. Robust weak T2/T4 matching controls may be green under the same gates.

The base 14-frame human 这 passes the classifier's seven internal probes. Applying an extra external every-tenth deletion and then the internal deletion probes returns `UNAVAILABLE / unstable_measurement_support`. This is an accepted support boundary. The rule was not loosened to pass the doubly perturbed control. First/last single deletions, timing jitter, and transposition controls remain stable.

## 7. Provenance and unchanged boundaries

[provenance-audit.json](provenance-audit.json), [raw-tracker-audit.json](raw-tracker-audit.json), and [measurement-audit.json](measurement-audit.json) record the checks:

- Raw `tracker_f0_hz`, raw F0 values, and Praat candidates are preserved. Canonical PCM retracking of the newest two takes and `430fcc2e` gives identical raw F0 and candidate lists with unchanged numeric Praat estimator parameters.
- Selected F0 is either the original raw selection or null; alternate candidates are never inserted. Every excluded native frame carries a reason.
- Alignment source/evidence IDs, status, groups, syllable times, lexical/surface fields, and owned frame indices match the saved inputs. The snapshots do not contain complete raw provider timing payloads, so the audit does not claim a byte comparison of those absent payloads.
- Display segment gaps and graph coordinates match the selected evidence. Rejected points are not bridged; the human 这个 graph preserves the gap before its two remaining 个 points.
- Both detectors are audio-only functions. Production rejection code contains no target text, Google identity, washer identity, fixture ID, or character-specific condition.
- ASR, Azure alignment, VAD/silence behavior, ownership, graph projection rules, neutral policy, T3 family scoring, and lexical/surface resolution are unchanged by this pass. Context adaptation occurs only in learner expectations.

Algorithm metadata advances to acoustics 1.3.0 / `spectral-filter-background-candidate-v2`, eligibility `voiced-support-completeness-v2-candidate-branch`, and contour interpretation `acoustic-shape-quality-v7.1-candidate-rejection`. Generated API defaults reflect the eligibility version; numeric tracker settings are unchanged.

## 8. Validation and unrelated baseline failures

| Check | Completed result |
| --- | --- |
| Mobile `npm run validate` | Lint, typecheck, **720 tests / 44 suites passed** |
| Focused mobile regression | 126 tests / six suites passed |
| Final established backend/research selection | **275 passed**; includes the physical replay and rejection controls |
| Node audit regressions | Four tests passed; final deterministic acceptance audit also passed |
| Python static checks | Mypy: 80 source files clean; focused Ruff clean |
| OpenAPI / mobile web export | Regeneration and export succeeded |
| Historical PCM/projection replay | 13 recordings / 53 units verified; immutable prior corpus/projection outputs preserved |
| Raw tracker / provenance / graph measurement | Passed; no raw substitutions, ownership drift, or graph bridging |
| Browser verification | **24 viewport cases** across six harness groups, widths 320/390/412; no reported browser errors or overflow |
| Final hygiene | `git diff --check`, pass-specific added-line whitespace, and provenance assertions passed |

Browser groups cover newest physical (six cases), older physical (six), tone classification (three), measurement fidelity (three), pronunciation chunks (three), and product feedback (three). They verify exact graph coordinates, canonical audio playback, history, neutral aggregation, controls, and coaching on green weak T3s. The earlier browser assertion expecting “Recovery is weak.” for newest 我 was corrected to the actual intended “Dip is shallow.”; no product-rendering change was needed. The finalization work did not change executable code or rerun expensive successful suites.

The broader pronunciation API run reported **247 passed, two failed**. Exact unrelated failures:

```text
services/api/tests/test_final_acoustic_calibration.py::test_api_target_revision_preserves_acoustic_evidence[1]
services/api/tests/test_final_acoustic_calibration.py::test_api_target_revision_preserves_acoustic_evidence[3]
```

Both fail at `test_final_acoustic_calibration.py:233` with **`KeyError: 'id'`**, accessing `target["id"]`. The preceding pinyin-corrections request with `{"pinyin":"ma2"}` returns **HTTP 422 Unprocessable Entity**, so the response has no `id`. Both reproduced against the untouched arrival implementation:

```bash
PYTHONPATH=/tmp/benma-robustness/before/services/api/src services/api/.venv/bin/pytest -q services/api/tests/test_final_acoustic_calibration.py -k api_target_revision
# 2 failed, 31 deselected in 0.66s
```

The baseline log is preserved in [baseline-api-failures.log](baseline-api-failures.log). No production change was made for these failures. This report does not claim the entire API suite passed: an exploratory whole-API run was interrupted, and an exploratory whole research-directory collection encountered five optional legacy ML modules requiring unavailable `torch`. The established relevant regression selection above passed in full.

[validation.json](validation.json) records completed results and log hashes; [browser-results.json](browser-results.json) preserves the browser review records. [changed-files.md](changed-files.md) lists this pass's edits against the arrival snapshot, separating them from the substantial work already present on arrival.

## 9. Remaining concrete uncertainty

The two newest physical takes and 13-recording historical set are small; these thresholds are not population-level calibration. No new live microphone recording or deployment was performed. Background detection needs observable quiet intervals, is not source separation, and cannot guarantee separation of a real low voice from coincident low-band machinery. Candidate rejection requires explicit alternate support and deliberately abstains on ambiguous or insufficient primary evidence. The double-thinned 这 remains unavailable. These limits do not leave implementation work outstanding for this pass.
