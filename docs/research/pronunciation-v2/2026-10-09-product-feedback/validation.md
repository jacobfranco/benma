# Validation and worktree reconstruction

## Preservation

Worked on `pronunciation-v2-research` in `/home/jacob/benma`. Initial status had ten
modified tracked files plus intentional untracked chunking/research/test artifacts.
The initial diff/status were captured at `/tmp/benma-product-feedback-initial.diff`
and `/tmp/benma-product-feedback-initial-status.txt`; continuation reconstruction is
`/tmp/benma-product-feedback/continuation.diff`. No work was reset, reverted, stashed,
discarded, staged, committed, pushed or deployed.

The initial API `perceived.py`, `schemas.py`, both generated OpenAPI files, the older
pronunciation-screen cleanup and pronunciationSafety regression diff remain byte-for-byte
identical to the initial handoff. Existing pronunciation-chunk policy and all 这/个
ownership/energy conclusions were preserved. Backend production was not changed by
this pass; no backend suite or closed tracker/VAD experiment was rerun.

This pass changed existing `PitchPlot.tsx`, `PronunciationWorkspace.tsx`, the comment
in `pronunciationWorkspace.ts`, workspace/chunk/transcript tests and development docs.
It added `PitchShapePlot.tsx`, `pitchShape.ts`, `pitchShapeDisplay.ts`,
`pitchShapeEvidence.ts`, `pitchShape.test.ts`, `product-feedback-browser.cjs`, the
`product_feedback.cjs` production-model replay bridge, numeric audit, acceptance
prototype, approved-request runner, portable research tests and this research directory.
The chunk tests were already untracked on arrival and were extended in place, not
replaced. Existing old research files and chunk browser script remain available.

## Completed checks

| Check | Result |
| --- | --- |
| Focused workspace/chunk/transcript/shape native-web suites | **181 passed / 6 suites** |
| Full mobile suite after the hierarchy updates | **541 passed / 35 suites** |
| Expo lint | Pass |
| TypeScript | Pass |
| Web export | Pass, `/tmp/benma-product-feedback/web` |
| Android export | Pass, `/tmp/benma-product-feedback/android` |
| Portable new research tests | **14 passed** |
| Ruff on four new Python research files | Pass |
| Frozen TS replay determinism and source SHA | Pass |
| Responsive offline Chromium | **320/390/412 × 844; zero page errors** |
| `git diff --check` | Pass |

Focused checks preceded full-suite validation. Initial failures were stale assumptions:
More Details used to mount the sentence evidence plot/Raw directly, and grouped detail
used to expose playback only once. Assertions now explicitly verify technical content
is collapsed, then check the preserved real evidence after opening Technical details.
They still verify immutable perception, target independence and no individual playback
invented for grouped 雨伞. Existing React test-renderer deprecation/act warnings remain;
no test failures or skipped tests are concealed. A first command used the repository
root rather than `apps/mobile` for npm; corrected execution supplied the results above.

## Browser review and reproduction

`apps/mobile/scripts/product-feedback-browser.cjs` intercepts API calls with existing
saved fixtures; no live provider, new capture or private audio export is used. A fresh
web export was served only on loopback at port 8094. The already installed Playwright
module and `/usr/bin/chromium` were used. Screenshots and `review.json` live in
`/tmp/benma-product-feedback/browser`; previous-design screenshots remain in
`/tmp/benma-pitch-cleanup-review`. Screenshot artifacts stay outside the repository.

Reviewed normal 我, exaggerated 我/想/买, partial 这个, unavailable standalone/constituent
个, grouped 雨伞, short rise/fall, long chunk navigation, More Details, Technical details
and Raw at all three widths. 我/想/买 graph left position and width are asserted equal
despite different durations. Reviewed the rendered normalized below-header alternative
and chose the beside layout; no second production layout remains.

Browser checks cover Enter/Space selection, selected state, >=44 px touch targets,
canonical audio playback, constituent inspection, dialog focus containment and Escape,
History replay, New Attempt, Clear target, untargeted Practice and collapsed Conversation.
No horizontal page overflow; the New Attempt footer remains reachable. Technical content
scrolls inside its dialog. These checks validate UI/audio routing, not perceptual phone
listening or VoiceOver/TalkBack certification.

Numeric tests cover fixed normalized timing bounds across durations, truthful gaps and
chunk proportions, unchanged source points, all-point Y visibility, 6 st minimum range,
weak noise, level/rise/fall/valley/above-start/shallow valleys, contradictory fragments,
missing critical support, discontinuities, perturbation instability, transposition,
required exaggerated valleys and every previously useful frozen control. Expected-label
checks preserve T3/sandhi/neutral/一/不 context and unresolved surface behavior.

Research tests use only versioned numeric/metadata fixtures. The shape audit reads
`expected-context.json` rather than silently depending on private snapshots. Two identical
production-model replays must agree byte-for-byte; the original corpus SHA must match.
Acceptance tests deliberately preserve the known low-F0 UNKNOWN failure and timeout.
Semantic comparison tests are research-only and cannot authorize production colors.

## Approved external experiment

Exactly nine additional manifest requests ran, after explicit user authorization:
**eight HTTP 200 responses, one ReadTimeout**. No retry or extra upload occurred.
The previously approved English probe is recorded separately. Frozen output contains
text, derived metrics, language metadata and hashes; no waveform or credential bytes.
This is the only new provider experiment. Local database queries were read-only.

## Limits and physical smoke

Overall **CORE FEEDBACK STILL BLOCKED** by product acceptance. Graph, broad measured
shape and learner-details integration are ready for their own phone smoke. No universal
speech/language safety, lexical-tone accuracy, independent geometry accuracy, comparison
color validity, or physical-device success is claimed.

Phone checklist for the earned UI slice:

1. Replay normal/exaggerated 我 → 想 → 买: stable graph bounds, visible valleys, accurate exact audio.
2. Confirm useful shallow recovery remains visible without a full textbook U requirement.
3. Select 这个: truthful partial graph and whole-chunk playback; inspect unavailable 个.
4. Select 雨伞: one accepted span, no invented individual character playback.
5. Open More Details: larger normalized graph, measured shape and contextual expectation.
6. Open Technical details/Raw: old strict diagnostics, times and source information remain recoverable.
7. Check native touch targets, dynamic text, VoiceOver/TalkBack and short recording playback.

The confirmed negatives remain acceptance blockers in production, so do not treat their
continued failure as a regression in the graph pass or claim they are fixed. No colors
or new acceptance rejection semantics are integrated.

**One next step:** resolve the specific UNKNOWN-language boundary between the frozen
throat-clear and protected low-F0 speech before integrating acceptance. The saved pair
must remain distinct product outcomes; any additional live audio request needs new approval.
