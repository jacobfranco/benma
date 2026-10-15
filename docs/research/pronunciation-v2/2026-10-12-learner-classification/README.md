# Learner classification pass — October 12, 2026

Complete. No further implementation work is needed for the three requested cases.
Finalization changed documentation only after all browser replays passed.

The pass continued from the existing dirty working tree. Production changes are
limited to `pitchShape.ts`, `toneLikeness.ts`, `chunkPitchGrade.ts`, and one neutral
explanation sentence in `PronunciationWorkspace.tsx`. Tracker, preprocessing,
energy gate, VAD, ASR, alignment, pitch ownership, graph projection, display
smoothing, silence, lexical/surface resolution and learner colors are unchanged.
No commit, push, deployment, provider call, recording edit or saved-evidence edit
occurred. The new fixture copies the two saved analysis payloads without changing
their values. Audio remains private and outside the fixture.

## Evidence and replay

The [numeric before/after audit](replay-results.json) includes physical features,
shape reasons, family, strength, grade, role, support, six perturbations, frozen
controls, validation results and input hashes. [Provenance](physical-provenance.json)
records saved analysis IDs, creation times and canonical audio hashes, verified
with a read-only local database query. Browser playback verifies those exact WAV
hashes before use. The Google/human labels follow the supplied physical-case
description; neither label is an input to classification.

| Take | Analysis | Saved UTC |
| --- | --- | --- |
| Google TTS physical take | `df7476d5-5716-4399-a528-924075c3a0fb` | 2026-10-12 20:08:52 |
| Human physical take | `208711dc-c437-4afe-b6d3-2aa0e16fb7cb` | 2026-10-12 20:00:41 |

## Completed shallow valley

The new path runs only for one structurally supported island whose existing
broad result is LEVEL or UNCLEAR. It uses local landmarks with the existing
three-point interior median and preserves endpoint values, avoiding suppression
of a short onset by the 20–40 ms start-region median. The valley and subsequent
recovery peak come from measured geometry; no fixed suffix is discarded.

`COMPLETED_SHALLOW_VALLEY` requires all of:

- Local fall ≥0.2 st, ≥2× local noise, and <1.5 st; fall/recovery ≥0.15.
- Recovery ≥1 st and ≥3× local noise. Noise is the 75th percentile of absolute
  residuals between measurements and their three-point summary.
- Falling support ≥20 ms, recovery support ≥40 ms, completed primary support
  ≥100 ms, and ≥0.8 directional consistency on each limb.
- Valley position **10–60%** of retained extent; recovery peak position ≥72%.
- A subsequent retreat with magnitude >0 and ≤50% of recovery, occupying ≤25%
  of both total time and sample support.

Full-track sample/order/coverage/gap/discontinuity checks still apply. Raw branch
flags disable this new exception. All six region/endpoint/deletion perturbations
must preserve DIP_RISE, and the existing ranking margin and ±0.1 st feature
perturbations still apply. The new `completed_shallow_valley` variant is always
**weak T3**, never full strength. Measured summary features remain intact; new
local features are explicit, separate diagnostics.

Thresholds were checked against the existing canonical, dominant-gesture,
reduced-T3, perturbation and corruption regressions, the 53-unit historical
corpus, the two new takes and synthetic counterexamples. The 10% valley floor
retains the existing interior-valley boundary: an initial candidate without that
floor incorrectly promoted frozen `89cee47e:买` (local minimum at 7.14%). That
candidate was rejected. Final historical rows, including that control, are exact
matches to arrival. These are bounded heuristic thresholds, not an independent
tone-recognition calibration.

Google 想 has a 0.617 st local fall, 1.291 st recovery, 0.620 st retreat, 21.43%
valley position and 85.71% recovery position. Its final two frames occupy 13.33%
of support. It survives all six perturbations and becomes weak T3/amber against
the unchanged lexical T3 fallback. Human 想 has only a small rebound followed by
a substantial fall; its existing perturbation-sensitive UNCLEAR result remains.

Synthetic controls cover transposition by ±24 st, intended-target changes,
coherent shallow valleys, trivial onset jitter in a T2 rise, late valleys,
insufficient onset/recovery, competing gestures, substantial terminal retreat,
missing support and raw branch flags. No learner-visible point is changed.

## Dominant main island with tiny late fragment

This classification-only exception is considered at `contradictory_fragments`.
It requires exactly two nonempty islands and a primary island that independently
passes the existing numbered-shape geometry. `SUBORDINATE_LATE_ISLAND` requires:

- Main island ≥75% of usable sample support.
- Secondary island ≤4 frames and ≤40 ms timestamp extent, starting at ≥75%
  of the entire retained extent.
- Inter-island gap ≤50 ms and jump ≤3 st.
- Secondary excursion ≤0.75 st and ≤25% of primary excursion.
- No internal gap >25 ms in either island; existing full-track coverage/order
  gates, primary discontinuity checks and all six perturbations remain required.
- Raw corruption flags disable the exception. Repeated fragmentation, comparable
  support, ambiguous primary geometry, substantial secondary motion and large or
  octave-like branches cannot use it.

The returned diagnostics identify primary support and geometry separately from
full-track support, full-track extent, terminal value, jump and secondary range.
Tone ranking uses the approved primary geometry; display still receives both
original islands. No missing region is filled and no input segment is mutated.

Human 这 has 11 primary frames and three secondary frames: 78.57% primary support,
100 ms primary extent, 20 ms secondary extent, 30 ms gap, 1.870 st jump and
0.079 st secondary range. Stable falling primary geometry survives every
perturbation and produces full T4/green. Synthetic long T4 and T3 plus tiny late
islands pass; comparable support, early fragments, repeated fragmentation,
substantial contradictory motion, large jumps and octave jumps abstain.

## Neutral state and aggregation

The existing eligibility contract is unchanged: accepted recorded audio, exact
playback/timing, a recognized multi-syllable chunk, separate nonoverlapping timing,
resolved neutral reading/surface 0 and a non-neutral head. No character identity
is hardcoded.

| Eligible dependent | Role | Own grade | Effect on head |
| --- | --- | --- | --- |
| No retained pitch | `neutral_unmeasured_nonveto` | Unavailable | Non-veto |
| Structurally trustworthy measured pitch | `neutral_measured_accepted` | Positive contextual acceptance | Non-veto |
| Structurally unreliable measured pitch | `neutral_unreliable_nonveto` | Unavailable; no positive credit | Non-veto |

The new unavailable reason is `unreliable_contextual_neutral`. A reliable head
can make the chunk green; a missing/unavailable head still makes it unavailable,
an incorrect head red and a weak head amber. Standalone neutral, optional quantity
个, unresolved reading, grouped timing, absent playback and unrecognized context
keep their existing bounds. 那个 exercises the same semantic path.

## Physical results

Colors below describe pitch agreement only. Source evidence and contextual
expectations are unchanged. Google origin and speaker intention never override
the measured family.

| Google unit | Before | After |
| --- | --- | --- |
| 我 | Full T2 / red | Unchanged |
| 想 | UNCLEAR / gray | Weak T3 / amber (`completed_shallow_valley`) |
| 买 | UNCLEAR / gray (`contradictory_fragments`) | Unchanged; large branch retained |
| 这 | Full T4 / green | Unchanged |
| 个 | Measured, structurally unreliable; gray, `grade_bearing` | Still gray, `neutral_unreliable_nonveto`; no positive credit |
| 这个 | Gray | Green from strong 这; neutral does not veto |

Google 个 retains its existing measured LEVEL/T1-like description. That numbered
family does not provide neutral correctness credit; raw structural uncertainty
keeps its own grade unavailable. Google 我/这 keep their pre-existing measured
family judgments and raw diagnostics; this pass does not relabel their tracker
evidence as clean.

| Human unit | Before | After |
| --- | --- | --- |
| 我 | Full T1 / red | Unchanged |
| 想 | UNCLEAR / gray (`perturbation_sensitive`) | Unchanged |
| 买 | Full T3 / green | Unchanged |
| 这 | UNCLEAR / gray (`contradictory_fragments`) | Full T4 / green (`dominant_supported_island`) |
| 个 | No pitch / gray, `neutral_unmeasured_nonveto` | Unchanged |
| 这个 | Gray | Green from strong 这; neutral does not veto |

## Historical audit and corrupt controls

**Zero changed historical rows out of 53.** Full serialized production rows match
arrival, including shape, family, strength, features, fits, reasons, expectations,
grades and colors. There are no historical label changes to list. Distribution
remains 15 green / 4 amber / 10 red / 24 gray, with 29 classifiable shapes.

The only changed existing constructed control is `constructed:这个-contradictory-neutral`:

1. Its 个 stays gray/unavailable; role changes from `grade_bearing` to
   `neutral_unreliable_nonveto`, with the explicit unavailable-neutral reason.
2. Its 这个 changes from gray to green because strong 这 now determines the chunk.

Frozen 买 controls remain unavailable:

| Control | Shape/family | Preserved reason |
| --- | --- | --- |
| Historical `89cee47e:买` | UNCLEAR | `ambiguous_geometry` |
| Physical `e5c17b4e:买` | UNCLEAR | `missing_critical_support` |
| Measurement `430fcc2e:买` | UNCLEAR | `insufficient_support` |
| New Google `df7476d5:买` | UNCLEAR | `contradictory_fragments` |

## Validation and browser replay

| Check | Result |
| --- | --- |
| Focused classification, likeness, learner/chunk grade and measurement tests | 137 passed, six suites |
| `npm run validate` | Lint and typecheck passed; 675 tests, 42 suites passed |
| Backend ownership/projection and pronunciation-v2 research regressions | 250 passed |
| Existing tone audit and deterministic numeric replay | Pass; two tests |
| Existing measurement replay | Pass; two tests |
| Saved gesture/PCM projection audit | 53 units replayed; frozen artifacts unchanged |
| Final historical equality check | All 53 complete rows equal arrival |
| Expo web export | Pass |
| New physical browser replay | Both takes × 320/390/412 px: six runs passed |
| Established tone browser replay | 320/390/412 px passed, including corrupt-neutral control |
| Established measurement browser replay | 320/390/412 px passed |
| `git diff --check` | Pass |

New physical browser assertions check weak Google 想, gray human 想, strong human
这, both green chunks and independently unavailable neutrals. Every rendered line
is compared to the complete owned source projection within 0.1 px; counts,
coordinates, islands and gaps agree. No topology change, page error or horizontal
overflow occurred. Exact hashed canonical playback and history work. The existing
tone suite also verifies keyboard selection, focus containment, Escape, grouped
timing and all four color states. Screenshots were inspected for Google amber 想,
human gray 想, disconnected human 这 and the green Google chunk.

Logs, screenshots and detailed browser reviews remain in `/tmp/benma-classification/`.
Full validation completed before finalization; because finalization made no code
changes and found no browser defect, expensive suites were not rerun. Existing
React test-renderer deprecation/act warnings remain in the test log. Loopback
database/browser access required sandbox execution approval and then succeeded;
no check remains blocked.

## Reproduction

From `apps/mobile`, focused tests:

```sh
npm test -- --runTestsByPath src/__tests__/toneClassification.test.ts src/__tests__/pitchShape.test.ts src/__tests__/toneLikeness.test.ts src/__tests__/learnerPitchGrade.test.ts src/__tests__/chunkPitchGrade.test.ts src/__tests__/pitchMeasurement.test.ts
npm run validate
CI=1 ./node_modules/.bin/expo export --platform web --output-dir /tmp/benma-classification/web
```

From the repository root, existing audit/replay commands:

```sh
node benchmark/pronunciation_v2/tone_feedback_audit.cjs
node benchmark/pronunciation_v2/test_tone_feedback.cjs
node benchmark/pronunciation_v2/test_measurement_audit.cjs
services/api/.venv/bin/python -m benchmark.pronunciation_v2.gesture_readability_audit
services/api/.venv/bin/python -m pytest services/api/tests/test_acoustic_frontend.py services/api/tests/test_canonical_audio.py services/api/tests/test_pitch_projection_contract.py services/api/tests/test_utterance_pitch.py services/api/tests/test_sentence_tone_graph.py services/api/tests/test_tone_evidence_region.py services/api/tests/test_pronunciation_chunks.py benchmark/pronunciation_v2/test_raw_tracker_audit.py benchmark/pronunciation_v2/test_gesture_readability.py benchmark/pronunciation_v2/test_product_feedback.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py benchmark/pronunciation_v2/test_relative_pitch_fragments.py
```

Serve the export on loopback, then run browser commands in another shell:

```sh
python -m http.server 8098 --bind 127.0.0.1 --directory /tmp/benma-classification/web
```

```sh
export BENMA_WEB_URL=http://127.0.0.1:8098
export PLAYWRIGHT_MODULE=/home/jacob/filefruit/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright
node apps/mobile/scripts/tone-classification-browser.cjs
BENMA_BROWSER_OUTPUT=/tmp/benma-classification/tone-browser BENMA_TONE_AUDIO=/home/jacob/benma/services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/19d8333bc4e04ce4bf026e393ea1f3e7.wav node apps/mobile/scripts/tone-feedback-browser.cjs
BENMA_BROWSER_OUTPUT=/tmp/benma-classification/measurement-browser node apps/mobile/scripts/measurement-fidelity-browser.cjs
git diff --check
```

## Changed files and limits

The [pass-specific file inventory](changed-files.json) compares arrival hashes and
contents, including files that were already untracked. Ordinary `git diff --stat`
includes earlier work and omits untracked files; it reports 14 tracked files,
653 insertions and 60 deletions. Those numbers are not the size of this pass.

The implementation is complete within the requested evidence scope. This was
saved-analysis and offline browser replay, not a new physical-device recording
or an independent population-level accuracy study. The thresholds remain
heuristic; human 想 remains unavailable because the measured evidence does not
support the new rule. No remaining concrete implementation defect was found.
