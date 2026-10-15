# Earlier continuation validation and physical smoke

Historical record of the preceding pass. The [focused dominant-gesture pass](dominant-gesture-pass.md) supersedes its context-gray, orange and measured-neutral policies.

## Worktree reconstruction and scope

Continued in `/home/jacob/benma` on `pronunciation-v2-research`. The worktree already
had 12 modified tracked files plus intentional untracked graph, chunks, projection,
acceptance and research artifacts. Initial status and per-file SHA-256 values are
captured in `/tmp/benma-tone-start.json`; the continuation's full tracked diff is
`/tmp/benma-tone-continuation.diff`. Existing work was neither recreated nor removed.

This pass changes the existing workspace component and its workspace/chunk tests,
and updates this research README. Added production modules are `toneLikeness.ts`,
`learnerPitchGrade.ts`, and `chunkPitchGrade.ts`. Added regression files are
`toneLikeness.test.ts`, `learnerPitchGrade.test.ts`, `chunkPitchGrade.test.ts`,
`toneFeedbackWorkspace.test.ts` and its web entry, shared test helpers, and the fresh
numeric/metadata fixture. Added research tooling is `tone_feedback.cjs`,
`tone_feedback_audit.cjs`, `test_tone_feedback.cjs`, and `tone-feedback-browser.cjs`.
The CSV/JSON calibration and four policy documents plus this validation note record
the concrete output.

Hash checks against arrival confirm these remain byte-for-byte unchanged:

- `pitchShape.ts`, `pitchShapeEvidence.ts`, `pitchShapeDisplay.ts`, `PitchShapePlot.tsx`,
  `PitchPlot.tsx`, `pronunciationWorkspace.ts`, `pronunciationChunks.ts`.
- Backend `perceived.py`, `schemas.py`, `chunks.py`, and both generated OpenAPI files.
- Existing `language_preflight.py`, `product_acceptance.py`, earlier frozen corpus,
  older `89cee47e` fixture and prior acceptance research artifacts.

Only read-only local database queries located the fresh take and its audio metadata.
No reanalysis/provider call, acceptance change, timing/chunk expansion, tracker/VAD
experiment, raw-F0 edit, commit, push or deployment occurred. No backend production
change was needed. No raw audio was added to versioned files.

## Checks

| Check | Result |
| --- | --- |
| Focused native/web geometry, tone, grades, chunks and workspace | 223 passed / 10 suites |
| Additional focused recheck after reduced-family deletion guard and final symbols | 66 passed / 5 suites |
| Final full mobile suite, including web projects | 607 passed / 40 suites |
| Expo lint | Pass |
| TypeScript `tsc --noEmit` | Pass |
| Web export | Pass: `/tmp/benma-tone-feedback/web` |
| Android export | Pass: `/tmp/benma-tone-feedback/android` |
| Existing frozen geometry/product research regressions | 29 passed |
| New production numeric replay regressions | 2 passed |
| Deterministic replay and published CSV/JSON equality | Pass |
| Existing source SHA preservation | Pass |
| Offline responsive Chromium | 320/390/412 px; no page errors or horizontal overflow |
| `git diff --check` | Pass |

Focused checks preceded broad checks. Stale tests were updated to expect the new
most-like default copy and accessible pitch state while still verifying measured
shape and old diagnostics in their correct detail layers. One synthetic margin
control initially carried inconsistent perturbation metadata; its explicit boundary
setup was corrected. One optional test-fixture field needed a type annotation fix.
No failing assertions were removed, tests skipped, or old physical data relabeled.
Existing React test-renderer deprecation/act warnings remain.

The browser serves a fresh export only on loopback, mocks every `/v1/` call, checks
the exact fresh canonical audio SHA, and plays fresh 我/这个/这/个. Constructed pitch
controls are never passed off as physical audio. Screenshots and `review.json` live
in `/tmp/benma-tone-feedback/browser`. The final run includes the frozen grouped
雨伞 projection on its existing timing span. Its grade stays unavailable and no
constituent audio controls appear. Keyboard Enter/Space selection, focus containment,
Escape, history replay and the always-reachable New Attempt footer also pass.

Reproduction from the repository root:

```sh
node benchmark/pronunciation_v2/tone_feedback_audit.cjs
node benchmark/pronunciation_v2/test_tone_feedback.cjs
services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_gesture_readability.py benchmark/pronunciation_v2/test_product_feedback.py -q
```

The existing research tests only read frozen acceptance artifacts; no acceptance
experiment was rerun. Browser reproduction uses `BENMA_WEB_URL`, `PLAYWRIGHT_MODULE`
and `BENMA_TONE_AUDIO` with `apps/mobile/scripts/tone-feedback-browser.cjs`. The audio
must match the documented SHA. There is no dependency installation or network
research requirement. Expo checks run from `apps/mobile`.

## Limits and checkpoint

All four integration gates are earned within their documented evidence scope.
**READY FOR PHYSICAL TONE-FEEDBACK SMOKE.** This is not a physical-device pass or
independently calibrated tone-recognition accuracy result.

The largest remaining semantic limit is contextual resolution: 16 classifiable
original corpus units have unresolved surface context, including fresh 我/想's
long-T3-chain rule. Their observed labels are useful and unconditional on context;
their color remains gray. Reduced low-tail T3 has constructed numeric support and
bounded amber semantics; it is not a validated universal half-third detector.
Neutral non-veto says nothing about unmeasured pitch correctness, stress, consonants
or vowels. Grouped timing does not establish character-specific tone.

The fresh valid 我 has retained F0 down to 84.607 Hz (median 91.3275 Hz), and its
measured valley is classified normally. These are saved-frame metadata, not a new
low-F0 acceptance experiment or a classifier Hz threshold. The unrelated protected
low-F0 / throat-clear UNKNOWN-language boundary remains exactly as it was.

Acceptance is still an existing, separate blocker. This pass makes no claim to fix
language preflight, English rejection, silence, speech presence or provider behavior.

## Physical smoke checklist

1. Say **我想买这个**. Inspect unchanged graphs and exact playback.
2. Clear dip-rise 我 and 想 should show **Most like Tone 3**. Gray is expected while
   the saved T3-chain context is unresolved; details must explain that distinction.
3. Deliberately poor 买 should show **Tone unclear**, gray, when support is ambiguous.
4. Falling 这 should show **Most like Tone 4**, green in constituent details.
5. **这个 should be green** with strong falling 这 and expected-neutral unmeasured 个.
   个 itself remains unmeasured and its graph remains empty.
6. Deliberately rise on 这: **Most like Tone 2**, and **orange 这个** against falling
   expectation. Ambiguous 这 should make the chunk gray instead.
7. Try an exaggerated third tone and a shallow stable valley. Both can remain
   T3-like; weak geometry gets amber only when contextual T3 is resolved.
8. Open More Details/Technical details; inspect neutral role, expected context and
   old source diagnostics. Check native text scaling and VoiceOver/TalkBack.

**One next step:** run this physical tone-feedback smoke on the current worktree.
Resolve any observed feedback regression before starting a separate context or
acceptance pass.
