# Final narrow acoustic calibration — 2026-09-24

**Outcome:** two low-confidence recoveries, exactly two changed human-corpus labels. Latest 马 becomes **3-like / low / Close**; latest 骂 becomes **4-like / low / Close**. Latest 妈 and 天 remain **1-like / moderate / Matches**. Stop acoustic calibration here; the recommended next milestone is pronunciation-feedback UI design, not another acoustic pass.

Work remains on `pronunciation-calibration`, committed baseline `a8bdfab3d00365c00e1a10881e8999df63f2823c`. Existing uncommitted work is preserved. No commit, provider call, production evidence write, tracker retuning, UI redesign or performance milestone occurred. Database export used a read-only transaction; audio copies stayed in `/tmp`.

## Verified persisted identities

These are persisted attempt timestamps in UTC, not filename-derived identities. Acoustic/perception data and target rows were read from the local database.

| Target | Attempt ID | Utterance ID | Attempt created UTC | Perception |
|---|---|---|---|---|
| 妈 ma1 | `6abef80b-2882-4865-91eb-3dbaf368503f` | `7df21c20-b0a3-4c9f-a72b-279d222407a6` | 2026-09-24 17:03:42.746495 | 吗 |
| 马 ma3 | `5df43f9b-aa9a-437b-9e2e-ebc2033b1f95` | `f047a3c9-bdbf-46e7-aa00-7bea281efa43` | 2026-09-24 17:08:10.987500 | 吗 |
| 骂 ma4 | `ad53695c-58d3-4022-8043-4db7750fc9c6` | `701bdfcb-f014-4522-80f2-de5005a8db6c` | 2026-09-24 17:11:41.403065 | 嘛 |
| 天 tian1 | `f84e4cdf-a47b-4e82-986a-0c6b88d316a6` | `79a1f0d4-027a-49ce-8f71-cb11651c7d9e` | 2026-09-24 17:13:38.028137 | 钱 |

There is also an earlier 骂 attempt `d1319348-c495-4708-810b-598ecc68468c`, utterance `2668c1df-0455-4323-be0f-1c56a8547dda`, created 17:11:26.519849 UTC. Its timing is unavailable and remains rejected. This explains why the current corpus adds five recordings to the previous 46, although four usable new attempts were requested for inspection.

## 马: exact decision and narrow change

The aligned window is .53–1.19 s. All 30 voiced observations at .6509–.9409 s survive reliable filtering: a continuous 300-ms active core, no gaps, contamination or large jumps, and no selected peripheral evidence exclusion. Relative semitones are derived from measured F0 against its median baseline, with the existing within-segment median-of-three filter and five equal-count median bins. The client display normalization is not consulted.

Bins: **[.8542, −.0560, −.2518, .2303, 1.8807]**. Trough position .5; fall into the trough **1.1060 st**; recovery **2.1326 st**; net change **+1.0265 st**; broad range **2.1326 st**; broad path **3.2386 st**. Raw/reliable mean disagreement .0111 st; raw local residual p90 .1978 st; reliable residual p90 .1819 st. No quality gate rejects it.

The original rule path was:

1. Level fails: range >1.5 and absolute change >1.
2. Rising fails: change <2; path 3.2386 also exceeds 1.8 × change (about 1.8477). Its onset-sag and minimum-position conditions would pass.
3. Dipping fails **only because pre-minimum fall 1.1060 <1.5 st**. The .2–.8 minimum-position and recovery ≥1.5 conditions pass.
4. Falling fails: change is positive, not ≤−2.
5. Fallback: `unclear / low / ambiguous_shape`.

For this evidence the categorical rejection was too conservative. This is a weak but observed two-limb gesture, not a tracker failure. That conclusion describes the acoustic shape; it does not establish native pronunciation or validate the intended target from user intent.

The added **fallback**, after all existing category rules, requires:

- Central minimum in the five broad bins, with two descending steps and two ascending steps.
- Fall and recovery each ≥1 st; each must represent ≥25% of the broad path.
- Continuous evidence, active-core coverage ≥.95, and voiced duration ≥200 ms.
- Reliable residual p90 ≤.35 st, raw residual p90 ≤.5 st, and raw/reliable mean disagreement ≤.25 st.
- All existing quality gates must pass.

Result: `3-like / low / shallow_coherent_valley`. Existing accepted categories take precedence, including accepted rises with onset sag. This rule does not require symmetry, a parabola, equal fall and recovery, or final pitch above the onset. It deliberately covers a narrow class of weak centered valleys; it is not a new universal definition of Tone 3 or recognition of all contextual/half-third realizations.

### Tone 2 versus Tone 3 corpus evidence

The [comparison CSV](tone2-tone3-corpus.csv) includes every timing-authorized span with expected Tone 2/3 or an independently observed 2-/3-like category, including rejected/noisy evidence. Full timing-rejected spans remain in [recomputation.json](recomputation.json). Expected labels are metadata, not acoustic ground truth.

All **six previously accepted 2-like** and **six previously accepted 3-like** spans retain their category, confidence and reason. Accepted rising examples have onset falls of 0–.668 st, including a centered .532-st sag in neutral-target 嘛. None qualifies for the weak-valley fallback. The existing synthetic rising control with an .8-st onset sag also remains rising.

Useful conservative human controls:

- `af62c9a6…` 你, intended surface Tone 2: 1.103-st fall and 3.360-st recovery, but an **early** minimum at .25. It stays ambiguous; the new rule does not promote every mathematical valley.
- `c1510778…` 我: centered, but only .893-st fall. It stays ambiguous. The threshold is a conservative heuristic, not a claimed physiological boundary.
- `0277d1ba…` 麻: 1.836-st fall, only .514-st recovery, late minimum .75. It stays ambiguous.
- Earlier unstable 马 `ea5a4a3e…`, `17026603…` remain tracker-rejected; `618b19d5…` remains contamination-rejected.

Only one human shallow-valley recovery is available here. Corpus stability supports this bounded change; it does not establish speaker/dialect accuracy or justify broad threshold relaxation.

## 骂: exact dropout and evidence on both sides

The aligned window is .80–1.32 s. There are 29 retained observations in two segments, 8 and 21 frames, over a .3100-s active core. Voiced duration .2901 s; active-core coverage **.9358**. No contamination, octave-like jump or tracker-instability rejection occurs.

The endpoint gap is **.9603–.9902 s =29.9 ms**. Two missing observations occur at .9703 and .9803 s; subtracting the ordinary roughly 10-ms hop leaves about 19.9 ms of missing frame support. No peripheral region is selected and the gap is not trimmed away.

| Time s | Raw F0 Hz | Selected strength | RMS | High-pass F0 Hz |
|---|---:|---:|---:|---:|
| .9503 | 149.787 | .9484 | .032144 | 149.759 |
| .9603 | 149.049 | .8506 | .026997 | 148.992 |
| .9703 | missing | 0 | .031289 | missing |
| .9803 | missing | 0 | .038726 | missing |
| .9902 | 123.440 | .7309 | .047701 | 123.452 |
| 1.0002 | 122.532 | .9367 | .054515 | 122.528 |
| 1.0102 | 122.144 | .9752 | .059409 | 122.141 |

Energy remains present and increases; periodicity drops materially and recovers. The gap is missing reliable F0, not measured silence. Gap candidates 165.744 Hz/.4017 and 123.122 Hz/.3697 are below the unchanged voicing gate and are **not** graded. Harmonic/subharmonic candidates exist around voiced frames, including a near-equal half-frequency candidate at 1.0102 s. The selected path and independent high-pass estimate agree, with no supported selected octave branch. We do not claim to know the true trajectory during the missing frames.

Across the gap, measured endpoint change is **−3.2637 st**. The existing local-slope extrapolation predicts only **−.146211 st**, leaving **3.117489 st** residual, above the **1.5-st discontinuity threshold**. Therefore `discontinuous_gap_count=1` caused `fragmented_voicing`. The gap-length limit itself (90 ms) did not reject it.

Both observed segments support the same broad fall. Three-region median levels are **[5.6026, 3.5341, 3.3492]** before and **[0, −.0416, −2.1535]** after the gap. Five whole-core bins are **[3.7964, 1.6319, .0643, −.6570, −2.3555]**, a monotonic **−6.1519-st** broad gesture. Small post-gap fluctuations do not form an opposing broad branch. Raw/reliable disagreement is .0087 st; both local residual p90 values are .5484 st.

### Bounded short-gap exception

Only an existing discontinuity rejection is eligible. The certificate requires:

- Exactly one gap, endpoint interval ≤40 ms; missing support beyond one hop ≤10% of the active core; core coverage ≥.90.
- At least six observed frames on each side; no voiced frames discarded by reliable filtering, no contamination and no raw >6-st jump.
- Raw and reliable local residual p90 ≤.75 st; mean raw/reliable disagreement ≤.25 st.
- Broad net movement ≥2 st. Both segments independently move ≥.5 st in that direction; their three median regions and the whole-core five bins permit no opposing step larger than .25 st.
- The gap endpoint step has the same direction.
- The three observed frames on each flank have measured periodicity ≥.65 and independent high-pass F0 within .5 st. Missing comparison/strength or octave disagreement fails closed.
- Remaining duration, coverage, noise and shape gates still apply.

Result: `4-like / low / coherent_short_gap`. The measured `discontinuous_gap_count` remains **1** for honest diagnostics; `coherent_short_gap=1` records why that particular veto was waived. The classifier does not lower the generic discontinuity threshold.

This exception is direction-symmetric: synthetic rising evidence passes the same conditions as falling evidence. Existing clean level + tiny dropout and observable dip/recovery + tiny dropout retain their original classifications without needing an exception. A discontinuous gap hiding a valley cannot get a new certificate from this monotonic rule. Multiple fragmentation, long gaps, opposing step/limb, octave branches, weak flanks, contamination, missing tracker comparison and inadequate evidence remain rejected in focused tests. Ordinary previously accepted small-residual gaps retain their existing policy; this pass does not globally redefine fragmentation.

## Evidence boundaries and learner integration

No artificial F0 is generated. Raw arrays remain byte-for-value unchanged; missing frames remain missing; the 骂 reliable contour still has **two segments /29 points**. The exception reads observed endpoints and segment medians. It never inserts a line or samples. Tests replace the entire display argument with a fabricated level drawing and obtain identical classifications. Existing display-only normalization and bridging code is unchanged.

Target labels are absent from extraction, region selection and classifier interfaces. API tests run the same persisted shallow-valley and short-gap evidence against original and Tone-2 revised targets, asserting identical raw F0, observed category/features and displayed measured contour. Only target-relative fields differ. Raw metadata label substitutions also leave region selection unchanged.

Learner semantics remain **Matches / Close / Different / Unclear**. A minimal integration change admits the two new diagnostic reasons and permits the gap certificate through the existing client quality veto only when reason, certificate and single-gap count agree. The existing rule then yields **Close** for low-confidence agreement and **Unclear** for low-confidence disagreement. No hard-coded target result or automatic Matches was added. New client tests reject missing certificates, extra gaps, contamination and tracker failure.

**Praat settings/version: unchanged in this pass. Evidence-region logic and selected intervals: unchanged (0 region changes).** No pitch floor/ceiling, time step, candidate count, voicing/silence threshold, octave cost or octave-jump cost changed. Acoustic extraction, target persistence, immutable perception, fixture/provider truth boundaries, reference separation and neutral semantics remain intact.

The tone/segmental distinction is explicitly deferred. 妈/吗 and 天/钱 retain their tone evidence; ASR character equality is not a pronunciation score and does not establish a specific phoneme error. The next UI milestone should distinguish tone, syllable sounds, what was heard and overall feedback. The existing tone-only Matches wording has not been redesigned here.

## Full real-speech regression

**51 persisted recordings /93 numerical spans /87 timing-authorized spans /6 timing-rejected spans.** Among the 87 authorized spans, **42** remain acoustically unclear and **45** have a category. Counting the six timing-rejected spans gives 48 total unclear, down from 50. These are convenience calibration recordings, not independently labeled pilot judgments. Real pilot readiness remains **0/50**.

Every changed real-speech category (and every changed reason/confidence tuple) is listed below; there are no others:

| Utterance / target | Old | New | Exact responsible rule |
|---|---|---|---|
| `f047a3c9-bdbf-46e7-aa00-7bea281efa43` / 马 ma3 | unclear / low / ambiguous_shape | 3-like / low / shallow_coherent_valley | New weak centered-valley fallback |
| `701bdfcb-f014-4522-80f2-de5005a8db6c` / 骂 ma4 | unclear / low / fragmented_voicing | 4-like / low / coherent_short_gap | Two stable observed limbs certify one short same-direction discontinuity |

Local WAV re-extraction confirms exactly the same two authorized category changes. Unvalidated timing probes remain quarantined. All six accepted rises, six accepted dips, eight accepted falls, prior unstable/low-frequency controls and neutral outcomes are preserved. Latest 妈 and 天 remain moderate-confidence 1-like. The complete before/after evidence is in [recomputation.json](recomputation.json), with [actual TypeScript learner verdicts](learner-recomputation.json) and [summary counts](summary.json).

## Synthetic controls, timing and validation

Synthetic controls establish deterministic invariants, **not human validation**. They cover canonical/shallow valleys (including final below onset), sustained rise, onset sag, centered tiny sag, level jitter, fall-only, multi-turn wiggle, insufficient recovery, repeated tracker glitches, both gap directions, level/valley dropout, long/multiple gaps, reversed endpoint/limb, octave branch, contamination, low evidence, weak/unknown periodicity, missing/disagreeing independent pitch, noisy limbs, target revisions and fabricated display input. Persisted fixtures separately cover the five new recordings including rejected timing; prior human fixtures protect earlier controls.

No new network or DSP pass occurs. Alternating before/after classifier measurements, 31 repetitions per authorized span, give median span runtimes **.860028→.860940 ms**, p95 **2.156620→2.149673 ms**. Median paired change is effectively zero at this measurement precision. Full extraction plus classification, seven runs per recording, gives median **26.302→26.607 ms**, p95 **82.929→81.577 ms**. These are noisy local measurements, not a production SLA; the additions are trivial local math. No optimization work was started.

Validation details are in [validation.md](validation.md). API: **426 tests passed in aggregate**, including four isolated PostgreSQL checks. Mobile: **22 suites /235 tests passed**. Offline benchmark: **96 passed**, no real pilot additions. Ruff, strict mypy, TypeScript, ESLint, Expo web export, desktop/touch Chromium acceptance, diff whitespace and secret checks passed. Chromium uses actual persisted result projections with intercepted API routes and synthetic transport audio; it is not a new physical-phone test.

## Changed files and checkpoint

Production changes in this pass only:

- `services/api/src/benma_api/pronunciation/contours.py`: version v7, weak-valley fallback, bounded discontinuity certificate and numeric diagnostics.
- `apps/mobile/src/speech/learnerVerdict.ts`: recognition of the two certified reasons through existing verdict semantics.

Added test/tool artifacts:

- `services/api/tests/test_final_acoustic_calibration.py`
- `services/api/tests/fixtures/final_narrow_pitch.json`
- `apps/mobile/src/__tests__/finalAcousticVerdict.test.ts`
- `apps/mobile/src/__tests__/fixtures/finalNarrowAcceptance.json`
- `apps/mobile/scripts/final-acoustic-browser.cjs`
- This report directory: corpus results, CSV, traces, runtime measurements, logs and screenshots.

The requested offline benchmark refreshes the already-dirty calibration manifest's run timestamp/provenance; pilot readiness stays zero. Other dirty/untracked files predate this pass. [Initial status](initial-status.txt), [final status](final-status.txt), [initial aggregate diff stat](initial-diff-stat.txt) and [final aggregate diff stat](final-diff-stat.txt) distinguish the larger existing branch from this narrow addition. Git diff statistics omit untracked files, including the already-untracked learner verdict file.

**Ready for a reviewed development checkpoint: yes. No commit was made.** This means the bounded calibration changes and regressions are reviewable, not that pronunciation accuracy is production-calibrated. Human-label coverage remains limited. Stop acoustic work here and proceed next to the separate UI/feedback-design milestone; that milestone was not started.
