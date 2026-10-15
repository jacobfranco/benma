# Dominant supported tone-family pass — October 10, 2026

## Continuation and scope

The starting tree already contained uncommitted backend chunk metadata, generated
API schemas, retained pitch/shape UI, pronunciation chunks, tone-likeness, learner
and chunk graders, physical fixtures, browser tools and research artifacts. This
pass preserved that work. On the follow-up request, the partial dominant-gesture,
lexical-fallback, red and neutral changes and focused tests were already present;
work continued in place with final validation and documentation.

No reset, commit, push, deployment, provider request, dependency installation,
backend/API-schema edit, alignment rewrite or physical-evidence edit occurred.
The acoustic function inputs remain numeric retained measurements, shape features
and raw discontinuity timestamps. Perceived timing owns evidence; linguistic
context only supplies expectations after classification. Neither acoustic function
reads intended target, characters, lexical/expected tone, transcript or reference TTS.

## Implementation

`pitchShape` summarizes a supported primary excursion with a near-boundary turning
point (position ≥0.72), support ≥0.12 s, excursion ≥1.5 st, and counter-excursion
≤25% of primary magnitude. Rise/fall consistency must be ≥0.8; a valley requires
both limbs ≥0.7. Counter-excursion uses the entire smoothed tail range, including
post-valley wobble. Named constants and numerical features make the decision auditable.
The measured endpoint/net remain separate from the dominant gesture endpoint/net.
No points are removed from the graph. Existing full-track support, missing-gap,
fragment contradiction and discontinuity gates still precede all geometry.
All six endpoint/window/deletion perturbations still validate numbered-family output.

The reduced-T3 low-tail candidate is separate from a dominant boundary fall with
small rebound. Strength comes from the measured dominant gesture. Tests include
cases where the final endpoint alone previously weakened the otherwise full gesture.

`PitchExpectation.basis` distinguishes resolved surface, lexical family, neutral and
unresolved. Resolved numbered surface rules win, including 一, 不 and T3→T2 sandhi.
Only null surface plus resolved reading/pinyin and lexical tone 1–4 enables family
fallback. Saved surface fields are never mutated or falsely resolved. Details show
“Tone N family” with connected-speech coaching.

The grading-layer T3-vs-T4 and T3-vs-T1 exceptions were removed. Strong compatible
family is green, weak/reduced compatible family amber, stable incompatible family
red, and unavailable judgment gray. Red uses #a32332 on #fcecef, with ≠ and the
accessible “Pitch differs” label. Audit colors come from production presentation.

Neutral now distinguishes unmeasured non-veto from measured contextual acceptance.
Separate accepted timing, recorded playback, recognized chunk context, resolved
surface 0, a non-neutral head and structural pitch support are required. Numbered
family ambiguity alone does not veto a neutral. Raw branch flags, corrupt support
and unstable measurements cannot earn acceptance. Measured neutral cannot hide a
bad, absent or weak head. Standalone 吧, optional quantity 个, unresolved readings,
grouped timing, absent playback and unrecognized chunks stay bounded. 那个 passes
through the same semantic path, without character hardcoding.

## Immutable fresh physical replay

Shape and observed family are unchanged before/after this pass.

| Unit | Shape before → after | Family / strength / variant | Basis before → after | Grade before → after | Reason after |
| --- | --- | --- | --- | --- | --- |
| 我 | DIP_RISE → DIP_RISE | T3 / full / ordinary | Unresolved surface → lexical T3 family | Gray → green | Stable compatible family |
| 想 | DIP_RISE → DIP_RISE | T3 / weak / ordinary | Unresolved surface → lexical T3 family | Gray → amber | Shallow dip: 1.033 st fall, 2.190 st recovery |
| 买 | UNCLEAR → UNCLEAR | Unclear / unavailable / ordinary | Unresolved surface → lexical T3 family | Gray → gray | Missing/fragmented critical support; broken branch not repaired |
| 这 | FALLING → FALLING | T4 / full / ordinary | Resolved surface T4 → same | Green → green | Stable compatible family |
| 个 | UNCLEAR → UNCLEAR | Unclear / unavailable / ordinary | Neutral → same | Gray → gray | Zero retained pitch; neutral_unmeasured_nonveto |

这个 remains green through its strong head and aligned unmeasured neutral dependent.
No measured neutral contour was fabricated in the recording. The synthetic controls
represent the later clean observations separately.

- Physical fixture SHA-256: `2dacaf05518f262b63293da3969cac0ae59881af329ce6eef890789cf94d56ee` (matches arrival).
- Frozen corpus SHA-256: `7f20f855e5059687907d1a28b4064c7b630bbe16b48633ec1e5fde70607397b3` (matches arrival).
- Canonical audio SHA-256: `b3e0f2964bb4a9831e008475d184fb7db3fb19b9dc2fd59f2d3547d3566d757d` (browser verifies before playback).

## Reviewed aggregate changes

All 53 historical corpus shape/family labels remain unchanged: 29 classified,
24 unclear (T1=2, T2=3, T3=18, T4=6). The grade distribution changes from
4 green / 2 amber / 7 differences / 40 gray to 15 green / 4 amber / 10 red / 24 gray.
The 16 context-only gray cases become 11 green, 3 amber, 2 red. One prior amber
T4-against-T3 becomes red. No acoustic corruption abstention was removed.

Quantity 个 in `4b9dbd2b` and `8faf1a90` is graded against lexical T4 fallback;
it is not silently relabeled neutral. This explains its red and green respectively.

| Changed corpus case | Before → after | Observation / strength | Expectation basis |
| --- | --- | --- | --- |
| 89cee47e:我 | gray → green | TONE_3 / full | lexical_family |
| 7e6b6fe9:我 | gray → green | TONE_3 / full | lexical_family |
| 7e6b6fe9:想 | gray → green | TONE_3 / full | lexical_family |
| 7e6b6fe9:买 | gray → green | TONE_3 / full | lexical_family |
| 0b194cf9:我 | gray → amber | TONE_3 / weak | lexical_family |
| 0b194cf9:想 | gray → green | TONE_3 / full | lexical_family |
| 0b194cf9:买 | gray → green | TONE_3 / full | lexical_family |
| ee8a8b32:我 | gray → red | TONE_4 / full | lexical_family |
| ee8a8b32:买 | gray → green | TONE_3 / full | lexical_family |
| 40357072:我 | gray → green | TONE_3 / full | lexical_family |
| 40357072:想 | gray → amber | TONE_3 / weak | lexical_family |
| 40357072:五 | gray → amber | TONE_3 / weak | lexical_family |
| 4b9dbd2b:个 | gray → red | TONE_3 / full | lexical_family |
| 8faf1a90:我 | amber → red | TONE_4 / full | resolved_surface |
| 8faf1a90:个 | gray → green | TONE_4 / full | lexical_family |
| b9067bec:买 | gray → green | TONE_3 / full | lexical_family |
| 5c70f317:买 | gray → green | TONE_3 / full | lexical_family |

The current JSON/CSV are regenerated production projections. Earlier `shape-results`
and research comparison artifacts remain historical, without rewriting their evidence
or features. The portable regression now checks preserved historical shape decisions
and abstention reasons; current full diagnostics are checked by tone-feedback replay.

## Regression coverage and validation

Clean textbook/late-fall/wobble T3, T2 plus boundary fall, and T4 plus rebound pass.
Comparable opposing movements abstain; gaps, branch jumps, fragment contradictions,
insufficient support and deletion-sensitive geometry remain unavailable. Synthetic
cases retain family under ±24 st transposition and intended-target-only changes.
Matching T1–T4, weak and reduced matches, stable T1/T4-vs-T3 mismatches, unresolved
readings, strong/weak lexical T3 fallback and explicit sandhi precedence are covered.
一 and 不 continue grading against resolved T2; a lexical-family match cannot override
explicit surface T2. Ordinal 一 remains T1. Neutral tests include canonical and
noncanonical trajectories, corrupt/sparse support, timing boundaries and head vetoes.

Commands from `apps/mobile`:

```sh
npm test -- --runTestsByPath src/__tests__/pitchShape.test.ts src/__tests__/toneLikeness.test.ts src/__tests__/learnerPitchGrade.test.ts src/__tests__/chunkPitchGrade.test.ts src/__tests__/toneFeedbackWorkspace.test.ts src/__tests__/toneFeedbackWorkspace.web.test.ts src/__tests__/pronunciationChunks.test.ts src/__tests__/pronunciationChunks.web.test.ts src/__tests__/pronunciationWorkspace.test.ts src/__tests__/pronunciationWorkspace.web.test.ts
npm run validate
CI=1 ./node_modules/.bin/expo export --platform web --output-dir /tmp/benma-tone-pass/web
```

Commands from repository root:

```sh
node benchmark/pronunciation_v2/tone_feedback_audit.cjs
node benchmark/pronunciation_v2/test_tone_feedback.cjs
services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_gesture_readability.py benchmark/pronunciation_v2/test_product_feedback.py -q
python -m http.server 8096 --bind 127.0.0.1 --directory /tmp/benma-tone-pass/web
BENMA_WEB_URL=http://127.0.0.1:8096 PLAYWRIGHT_MODULE=/home/jacob/filefruit/node_modules/.pnpm/playwright@1.61.0/node_modules/playwright BENMA_TONE_AUDIO=/home/jacob/benma/services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/19d8333bc4e04ce4bf026e393ea1f3e7.wav BENMA_BROWSER_OUTPUT=/tmp/benma-tone-pass/browser node apps/mobile/scripts/tone-feedback-browser.cjs
sha256sum -c /tmp/benma-tone-pass/fixture.sha256
git diff --check
git diff --stat
git status --short
```

| Check | Final result |
| --- | --- |
| Focused mobile native/web | 255 passed / 10 suites |
| `npm run validate` | Lint + typecheck pass; 639 tests / 40 suites pass |
| Production tone audit | Deterministic regeneration; 2 replay tests pass |
| Existing portable research regressions | 29 passed |
| Web export | Pass |
| Offline Chromium | 320/390/412 px pass; no page errors or horizontal overflow |
| Browser interactions | Four colors, lexical details, measured neutral, grouped timing, exact saved playback, keyboard/focus, history pass |
| Frozen evidence | Physical/corpus hashes preserved |
| Whitespace | `git diff --check` passes |

Initial command issues were resolved: npm was first invoked from the repository
root (no root package.json), an import-group separator failed lint, and a historical
full-diagnostic snapshot expected the old geometry feature schema. Those checks were
corrected and rerun. The sandbox blocked loopback socket creation and Chromium
startup; both succeeded after execution approval. No requested check remains blocked.
Existing React test-renderer deprecation/act warnings remain in test logs.
Browser screenshots/review and command logs are in `/tmp/benma-tone-pass/`.
This was saved-evidence replay and browser validation, not a new physical recording
or an independent tone-recognition accuracy study.

## Files touched by this focused pass

Production: `pitchShape.ts`, `toneLikeness.ts`, `learnerPitchGrade.ts`,
`chunkPitchGrade.ts`, `pitchShapeEvidence.ts`, `PronunciationWorkspace.tsx`.
Tests: `pitchShape.test.ts`, `toneLikeness.test.ts`, `learnerPitchGrade.test.ts`,
`chunkPitchGrade.test.ts`, `toneFeedbackFixture.ts`, `toneFeedbackWorkspace.test.ts`,
`pronunciationWorkspace.test.ts` (web entry files reuse those suites).
Tools: `tone-feedback-browser.cjs`, `tone_feedback_audit.cjs`,
`test_tone_feedback.cjs`, `test_product_feedback.py`.
Docs: the three development pronunciation/workspace/tone-graph documents and this
research directory's README, learner-grading, neutral-dependent-policy, color-policy,
tone-likeness, historical validation pointer, current JSON/CSV, and this report.

Full `git diff --stat` and `git status --short` are captured in
`/tmp/benma-tone-pass/final-git.txt`. They include the substantial pre-existing work;
Git's diff stat does not include untracked files. The already-dirty backend, API
schemas, evidence fixtures, alignment/projection modules and unrelated UI files
were left as found.

No concrete implementation requirement remains unresolved. The saved weak 想 and
corrupted 买 are evidence-limited outcomes, not outstanding fixes. Synthetic clean
observations are not a substitute for new physical evidence, and neutral acceptance
does not claim to measure stress or articulation.
