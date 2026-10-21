# Practice UI restoration — 2026-10-21

**READY for physical testing.** The polished Practice workspace renders learned
results through a presentation adapter. Real microphone quality and audible
device playback remain manual checks.

## Cause and exact baseline

The starting working tree was clean at
`64e4f3cae8bafe2a62b0145aad89ba86725cba40` (learned dev integration).
Its parent, `200aff668ac01fae01af1c7ee7cb6954ad540608`, is the exact
pre-integration UI baseline. The workspace itself last changed in `eaf9c43`.

The integration added an early return in `PronunciationWorkspace.tsx` that sent
dev learned results to `LearnedToneWorkspace.tsx`. That separate component used
larger spacing, a diagnostic heading, top-level target/heard explanations, full
sentence and selected raw charts, and a different selection/detail layout.
The original polished component remained in the same file as
`LegacyPronunciationWorkspace`; its styling had not been deleted.

Other integration changes under mobile were transport/schema/workflow plumbing:
`api/client.ts`, `api/openapi.generated.ts`, `api/openapi.json`, and
`speech/workflow.ts`. These remain unchanged from the integrated HEAD.

## Selective restoration

| File/component | Result |
| --- | --- |
| `src/speech/PronunciationWorkspace.tsx` | Removes the alternate-workspace branch and restores the original component as the sole workspace. Uses the adapter for family, expectation, and feedback. Its complete StyleSheet is byte-identical to `200aff6`. |
| `src/speech/LearnedToneWorkspace.tsx` | Removed the diagnostic replacement screen. |
| `src/speech/learnedToneView.ts` | New presentation adapter into the existing chunk/constituent feedback contract. |
| `src/speech/LearnedToneEvidence.tsx` | Raw learned evidence, mounted only inside the existing More details → Technical details section. |
| Learned native/web tests and Practice screen tests | Cover restored interactions, semantics, and the normal prepared-target path. |

The following are byte-identical to `200aff6`: Practice screen, SpeechEvidence,
WorkspaceActions/dialog, PitchShapePlot, PitchPlot, ExactPlaybackButton,
pronunciationChunks, chunkPitchGrade, and learnerPitchGrade. Navigation, target
preparation, reference audio, recording controls, history, and repeat attempts
therefore retain their existing implementations.

## Learned pipeline and adapter

No backend, research, inference, timing, API transport, generated schema, or
workflow source was modified. Azure timing → clamped retained F0 envelope →
continuity guard → usable span/abstention → resident frozen Chinese HuBERT →
learned family remains intact, including target independence, resident reuse,
feature gates, neutral handling, and absence of synchronous MFA.

The adapter joins learned units by saved syllable index and characters rather
than array position. It preserves original chunk membership, timing, pitch
projection, acoustic shape, and contextual neutral support. Learned family and
downstream comparison replace deterministic numbered-tone family/grade in the
learner view. A missing learned unit fails closed; it cannot fall back to a
deterministic correctness judgment. Saved responses are not mutated.

The old grade keys and palette are retained:

- Green: usable evidence with downstream experimental agreement, or the existing
  structurally supported contextual-neutral acceptance. It is not percent correct.
- Amber: a downstream experimental difference, explicitly not a confirmed error.
- Gray: abstention, missing/unusable evidence, unresolved surface expectation or
  target mapping, unsupported grouped judgments, and standalone neutral judgment.
- Red remains reserved for strong, stable incompatible evidence. The current
  learned contract does not provide that decisive evidence and fixes correction
  to false, so this adapter never emits red for learned results. Feature-off
  conservative red behavior is unchanged. No new confidence thresholds were added.

Unresolved surface expectations never fall back to lexical correctness. A usable
heard family stays visible, with a gray status and no correction. Neutral tones
retain contextual reading and existing chunk non-veto behavior; no T1–T4 error is
forced. Abstention retains measured pitch and timed playback where available.
Only the existing backend-supported measured explanation can supply learned
coaching; old deterministic correction advice is not carried over.

## Chart, details, and necessary visual differences

The original 96 px compact PitchShapePlot is back beside the selected identity
and playback button. Full details retain the 152 px chart, 120 px constituent
chart, expected-pitch descriptions, and technical sentence graph. Ownership
projections, gaps, domain/layout rules, playback spans, and playback cancellation
on selection/unmount are unchanged. No new contour or playback synchronization
behavior was invented.

Necessary differences from the baseline when learned evidence is present:

1. Heard-family labels and status colors now reflect learned evidence.
2. Unresolved/neutral status uses “Pitch not judged”; abstention/unresolved
   explanations can add a short caption in the existing caption style.
3. More details includes selected target/transcript reading and heard-tone reading
   in the existing reference typography, plus a short explanation that these are
   tone marks on the same syllables. Unclear numbered tones remain `[unclear]`.
4. Technical details includes Dev evidence JSON. It is not mounted on the normal
   result screen or when only More details is open; reopening the dialog collapses
   technical details again.

No diagnostic heading, extra screen, confirmation step, or new primary card remains.

## Before/after verification

The actual baseline component was temporarily extracted with `git show
200aff6:apps/mobile/src/speech/PronunciationWorkspace.tsx` and rendered alongside
the restored component using the same saved physical pitch/chunk fixture.
Native and web comparisons passed full serialized rendered-tree equality with
learned evidence absent at six states: initial, selected 这个, More details,
selected neutral constituent, Technical details, and closed dialog. The temporary
comparison component/tests were removed afterward; the log is
`/tmp/benma-ui-baseline-comparison.log` (2 passing comparisons).

No historical image snapshot files were available in the repository. This is
source/style and rendered-tree equality, not a claimed historical pixel diff.
The restored learned UI was additionally exercised and visually inspected in
Chromium at 1280×900 and 390×844:

- `/tmp/benma-ui-prepared-desktop.png`
- `/tmp/benma-ui-result-desktop.png`
- `/tmp/benma-ui-result-narrow.png`

The browser used explicit fixture responses and a fake microphone, made no paid
provider calls, and ran no learned inference. It exercised Add target → 我想买这个
→ Prepare target → record → result, selection of 这个, canonical segment audio
retrieval, target/heard details, technical expansion, and dialog closing. There
was no narrow-width document overflow and there were zero uncaught page errors.
The prepared-target analysis request retained the target ID and made no laboratory
analysis request. Browser evidence: `/tmp/benma-ui-browser.log`.

## Tests and freeze

- Final mobile native/web suite: **779 passed, 47 suites**.
- Learned-result selection: **20 passed**, native and web.
- Practice-screen selection including the new 我想买这个 flow: **66 passed**.
- Backend learned integration: **19 passed** in `test_dev_learned_tone.py`;
  these use mocks/fixtures, not model benchmarks.
- Lint, TypeScript, web production export, Android production export, and web dev
  export all passed. `git diff --check` passed.
- Existing exact-playback, chart, chunk, pronunciation, recording, and workflow
  tests are included in the full mobile suite.
- `git diff HEAD -- services/api research apps/mobile/src/api
  apps/mobile/src/speech/workflow.ts` is empty.
- Production settings/defaults and dev gates are unchanged. No training, tuning,
  research benchmark reruns, commits, pushes, or deployments were performed.

Logs: `/tmp/benma-ui-final-tests.log`, `/tmp/benma-ui-final-lint.log`,
`/tmp/benma-ui-mobile-validate.log`, `/tmp/benma-ui-api-tests.log`,
`/tmp/benma-ui-web-export.log`, `/tmp/benma-ui-android-export.log`.

## Launch for physical testing

From `/home/jacob/benma`, using the existing API `.env` and database:

```bash
BENMA_ENVIRONMENT=development \
BENMA_ENABLE_DEV_LEARNED_TONE=true \
BENMA_ALIGNMENT_PROVIDER=azure \
BENMA_ACOUSTIC_PROVIDER=praat \
benchmark/pronunciation_v2/.venv/bin/python services/api/scripts/dev_learned_server.py
```

In a second terminal from the same directory:

```bash
EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE=true \
EXPO_PUBLIC_BENMA_API_URL=http://192.168.68.57:8000 \
npm --prefix apps/mobile start -- --clear
```

`192.168.68.57` is this machine's observed LAN address at verification time. Use
`127.0.0.1` for a browser on this machine. The phone must reach the LAN address;
LAN browser testing also needs its exact Expo page origin in the existing CORS
allowlist. No configuration file was changed to enable either feature flag.

Open **Practice → Add target → 我想买这个 → Prepare target**, then record. The first
usable attempt still pays resident-model initialization; subsequent attempts
reuse the process. Inspect optional raw evidence under **More details → Technical
details**. Physical microphone, audible playback, and live provider latency were
not remeasured in this restoration.
