# Conversation + Practice milestone — 2026-09-16

Historical milestone report. The [transcript-conditioned analysis correction](perceived-speech-analysis.md)
supersedes the original free-speech feedback presentation. The subsequent [runtime feedback/concurrency/playback pass](speech-concurrency-playback.md)
supersedes its sequential-processing description and automated-validation counts; the paid
evaluation results and model/voice decisions below remain unchanged.

This pass builds on the user's uncommitted mobile Free Talk work. Nothing was reset, reverted,
staged, or committed. HEAD remains `b3ab72c20786d370a9e754424ba7187f5658a7ce`.
Before editing, tracked changes were saved to `/tmp/benma-before-conversation-practice.patch`
and untracked files to `/tmp/benma-before-conversation-practice-untracked.tar.gz`.

## User-facing structure and exact flows

Home presents **Conversation** and **Practice**. History and calibration remain secondary tools.
The old `/perception` and `/pronunciation` laboratory routes remain internally accessible;
`/free-talk` remains an alias for Conversation. No backend endpoint was removed.

**Conversation:** record → Expo File multipart upload → audio-only perception → immediately
render the returned immutable heard text → contextual interpretation → persist user turn →
generate and persist assistant text → return text → request speech by persisted generation ID →
cache protected bytes locally → wait for native readiness → autoplay. Subsequent recordings use
that same persisted conversation. A newer recording or playback choice suppresses late autoplay.

Authoritative `ConversationTurn` records contain `perceived_text`, `interpretation_decision`,
and `resolved_text`. Provisional perception display reconciles by perception/turn identity and is
not a second semantic history. If the response request fails after persistence, the client reloads
server turns while retaining any otherwise unlinked heard text. Successful text never depends on
successful speech, and speech retry sends `{}` to the existing generation-scoped endpoint.

**Free Practice:** record → upload → audio-only perception → heard text and conservative speech
feedback → optional replay/re-record. It creates neither a conversation reply nor a pronunciation
attempt. **Target Practice:** learner explicitly enters/prepares target → existing target/pinyin
and ReferenceSpeech → record → upload → audio-only perception → existing PronunciationAttempt →
assessment/acoustics/alignment/interpretation → result, Reference/Mine playback, and repeat.
Reference failure does not block target assessment. Target changes clear stale retry checkpoints.

`submitSpeech` / `useSpeechTurn`, `SpeechControls`, and `SpeechEvidence` share capture, upload,
perception, selectable display, processing stages, and safe error recovery. Completed upload,
perception, and attempt IDs are retained for suitable retries. The original laboratory's specialized
reference, pinyin, pitch, history, and A/B controls remain available.

## Evidence and feedback

PRESERVE shows heard text without redundant understood text. INFER shows both when wording
materially differs, plus the changed character/span: “Benma heard … where the conversation
suggested …”. CLARIFY remains explicitly unsure; no alternative is displayed as resolved truth.
All Mandarin speech/reply/target/pinyin text is selectable.

Free speech has no target-relative score and no inferred-text pronunciation target. Existing
acoustic F0 remains diagnostic; no new learner verdict is manufactured from it. Target Practice
uses the existing known-target pipeline and its conservative experimental wording/quality gates.
Raw perception, contextual interpretation, and explicit targets remain separate. Append-only
provenance, exact clarification allowlisting, and account ownership checks remain intact.

The general interpretation policy now distinguishes genuine semantic ambiguity from a single
well-supported near miss, protects coherent odd grammar, and considers sentence context without
requiring prior history. It contains no phrase-specific replacement rules. Live model limitations
remain, as recorded below; contract tests are not presented as proof of model intelligence.

## Protected audio

AssistantSpeech and ReferenceSpeech both use `useCachedAudio`:

`protected resource path → authenticated expo/fetch → bytes → Paths.cache File → expo-audio`

Resource kind/ID, isolated player slots, and auth resets protect cache identity. There are no token
URLs, token filenames, persisted credential metadata, or base64 paths. Current-source replay
reuses local audio; replacements, unmounts, auth changes, previous processes, and the legacy
assistant cache clean obsolete files. WAV, M4A, and WebM are recognized from bytes. The same
transport therefore also preserves saved learner-recording playback.

Native readiness events gate play, including fast replacements where React skips the transient
unloaded render. All foreground players stop before recording and keep the iOS audio session
active through pause; delayed downloads/seeks cannot restart over a new recording. The physical
iOS result remains to be confirmed, despite automated lifecycle coverage.
The prepared Practice reference player stays mounted, disabled during recording, so the same
reference can replay from its existing cache after capture.

Conversation defaults to `zh-CN-Xiaochen:DragonHDFlashLatestNeural` / `DragonHDFlashLatestNeural`.
Both remain environment-configurable. Pronunciation reference keeps
`zh-CN-Xiaochen:DragonHDLatestNeural`. The effective local configuration was checked, and the
existing Azure smoke test produced valid 24 kHz mono PCM WAV for all three synthetic phrases.

## OpenAI evaluation and one-call investigation

The existing configured model is `gpt-5.6-terra`. The repo already supports `medium`, `low`, and
`none`, which are also listed in the [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-terra).
No new model or reasoning value was introduced. Model and reasoning overrides remain unchanged.

The [complete normalized results](../benchmark/conversation-latency-2026-09-16.json) contain
68 paid requests total across policy drafts, three effort levels, a four-call combined prototype,
and explicit-context checks. All inputs were fixed synthetic text. No production audio,
conversations, or personal data were read, and no research run created database evidence.
There was one sample per case/configuration, no automatic retries, and at most 512 output tokens
per ordinary invocation (1024 for the combined research response).

| Evaluation | Effort | Expected semantic decisions | Median interpretation + generation |
| --- | --- | --- | --- |
| Initial draft | medium | 3/4 | 7.149 s |
| Initial draft | low | 2/4 | 4.939 s |
| Initial draft | none | 2/4 | 4.107 s |
| Revised v3 policy | medium | 3/4 | 4.397 s |
| Revised v3 policy | low | 4/4 | 4.546 s |
| Revised v3 policy | none | 3/4 | 3.995 s |
| Final v4 policy | medium | 3/4 | 4.387 s |
| v3 combined research invocation | medium | 3/4 | 2.879 s |

The four cases cover coherent odd grammar, the opening 周谋/周末 near miss, a reference to two
possible destinations, and a contextual follow-up. Under the final policy, odd grammar preserved,
the genuinely ambiguous reference clarified with exact grounded alternatives, and the follow-up
preserved and received a natural reply. **The opening 周谋 case still clarified without prior
context.** This is a failed semantic expectation, not a passed test hidden by schema validation.
An additional context-supported 公元/公园 near miss inferred correctly at every tested effort;
its final-v4 medium run took 3.391 s interpretation + 1.750 s generation.

**Decision: keep medium defaults.** Low did not materially improve total latency on the revised
set; none retained a semantic failure. These few samples cannot establish broad model quality.
All generation outputs passed structural/allowlist checks, which cannot prove the absence of every
implicit unquoted assumption. The conservative empty-alternative behavior is still enforced.

**One-call production orchestration is deferred.** The research-only structured invocation
returned separate interpretation/assistant sections and ran the existing interpretation and exact
clarification validators. On the v3 cases its median was 34.5% lower than the sequential baseline,
but it still missed the near-miss case. More importantly, production generation currently loads
an already-persisted interpretation and snapshots its authoritative input. Replacing that with
one speculative invocation needs an explicit shared-call provenance/failure contract and defended
snapshot validation before retaining separate queryable records. No production shortcut or silent
fallback was added. The prototype remains only in the opt-in benchmark script.

## Latency: measured values versus device estimates

No post-change physical iPhone measurement was available during this pass. It would be incorrect
to report an observed end-to-end device improvement. The baseline below is supplied physical
measurement; the new values are projections, not physical results.

| Milestone from Stop | Supplied baseline | New path estimate using the same baseline stages |
| --- | --- | --- |
| Heard transcript | Raw heard text was not displayed; first resolved text waited roughly 14.63 s | 2.83 s (0.33 upload + 2.50 perception) |
| Assistant text | Roughly 14.63 s, including TTS | 12.43 s with unchanged 6.0 + 3.6 reasoning stages; TTS excluded |
| Audible response | Roughly 14.72 s | 13.51 s using supplied 0.992 s Flash median and 0.09 s cache/load |

Using the final synthetic provider-call median of 4.387 s instead of the supplied 9.6 s reasoning
sum would project about **7.22 s text / 8.30 s play request**. This mixes different runs and inputs
and is deliberately only a planning estimate. The actual live measurements are the provider
latencies above; physical heard/text/audible timings still need the checklist run.

The user's separate controlled Azure comparison measured DragonHD at 2.867 s median versus
DragonHDFlash at 0.992 s, about 65% lower synthesis latency. This pass's three-phrase Flash smoke
confirmed valid audio, not a new comparative latency measurement.

Development-only logs capture recording duration, upload, perception, interpretation, generation,
TTS, fetch/cache, load-to-play, and totals from Stop. Backend interpretation/generation timings use
a numeric `Server-Timing` header only in development. The audible log ends at native `play()` and
is a proxy for output onset; it does not measure the speaker. No provider payload/secret is logged.

## Validation

All final checks below completed successfully after resuming; no paid provider benchmark was rerun.

| Check | Final result |
| --- | --- |
| Focused mobile: Conversation/workflow, Practice, cache/playback, recording, API client | 52 tests passed, 6 suites |
| Full mobile Jest | 61 tests passed, 10 suites |
| Mobile ESLint (`npm run lint`) | Passed, no warnings |
| Mobile TypeScript after contract regeneration (`npm run typecheck`) | Passed |
| Android Expo export (`CI=1 npx expo export --platform android --output-dir /tmp/benma-expo-export`) | Passed |
| Focused API perception/context/conversation/generation/speech and pronunciation/reference regressions | 125 tests passed |
| Full API pytest | 149 tests passed |
| API Ruff (`.venv/bin/ruff check .`) | Passed |
| API strict mypy (`.venv/bin/mypy`) | Passed, 64 source files |
| Alembic consistency | Full-suite upgrade, `command.check`, downgrade, and backfill tests passed |
| OpenAPI + mobile DTO export | Regenerated using `scripts/export_openapi.py` |
| OpenAPI idempotence | Second export preserved SHA-256 for both generated files |
| Root benchmark pytest, offline | 96 tests passed |
| `git diff --check` | Passed |
| `bash scripts/scan-secrets.sh` | No high-confidence secret patterns found |

No database schema or migration changed. The two additive public response fields are generated
from backend schemas, not handwritten into the mobile OpenAPI/DTO files. The initial resumed
focused API command used a nonexistent test filename and collected no tests; the corrected
selection produced the 125-test result above. Final validation logs are in `/tmp/benma-*-final.log`.

The complete diff and untracked source were reviewed for shared workflow reuse, raw versus inferred
versus target semantics, ownership, speech failure durability, audio lifecycle, and old navigation.
The final review kept the Practice reference player mounted during capture and removed an obsolete
submission wrapper in favor of the small, used persisted-generation speech request helper.
No app/runtime imports the opt-in latency research script. Its combined-call experiment and
sanitized synthetic results remain development artifacts; production still makes two model calls.
No temporary build output, cache, credentials, or raw provider dump is included in the change list.
`expo-env.d.ts` was already tracked and modified in the incoming work; its Expo-managed contents
are preserved. Expo's generated ignore entry remains, and `.expo`/Android export output is untracked
and ignored or outside the repository. OpenAPI JSON and TypeScript DTOs remain intentional tracked
contracts.

There is no remaining automated-validation blocker. Physical iPhone acceptance is outstanding,
and the opening near-miss interpretation limitation is explicitly retained. Nothing was staged or
committed, and no further milestone was started.

## Physical iPhone validation

Run **`benma-api`** and **`benma-mobile`** in separate zsh terminals. Follow the exact three-turn
Conversation, free Practice, target Practice, interruption, selection, replay, and timing checklist
in [physical-device.md](../testing/physical-device.md). Native iOS audio, multipart serialization,
text selection, and perceived quality still require that device run. No commit or next milestone
was started.

## Final working-tree inventory

HEAD: `b3ab72c20786d370a9e754424ba7187f5658a7ce`. 29 tracked files modified and 23 untracked files; these totals include the incoming Free Talk changes. The standard diff stat omits untracked files.

### Tracked files changed

```text
README.md
apps/mobile/README.md
apps/mobile/expo-env.d.ts
apps/mobile/package-lock.json
apps/mobile/package.json
apps/mobile/src/__tests__/apiClient.test.ts
apps/mobile/src/api/client.ts
apps/mobile/src/api/openapi.generated.ts
apps/mobile/src/api/openapi.json
apps/mobile/src/api/types.ts
apps/mobile/src/app/_layout.tsx
apps/mobile/src/app/history.tsx
apps/mobile/src/app/index.tsx
apps/mobile/src/app/pronunciation.tsx
apps/mobile/src/audio/PlaybackButton.tsx
apps/mobile/src/audio/useAudioCapture.ts
apps/mobile/src/components/Ui.tsx
docs/testing/physical-device.md
services/api/.env.example
services/api/README.md
services/api/pyproject.toml
services/api/src/benma_api/api/routes.py
services/api/src/benma_api/config.py
services/api/src/benma_api/contextual_interpretation/openai.py
services/api/src/benma_api/conversation/service.py
services/api/src/benma_api/schemas.py
services/api/tests/test_assistant_generation.py
services/api/tests/test_assistant_speech_provider.py
services/api/tests/test_contextual_interpretation_provider.py
```

### New/untracked files

```text
apps/mobile/.gitignore
apps/mobile/src/__tests__/assistantPlayback.local-cache.test.ts
apps/mobile/src/__tests__/audioCapture.test.ts
apps/mobile/src/__tests__/freeTalkScreen.test.ts
apps/mobile/src/__tests__/freeTalkWorkflow.test.ts
apps/mobile/src/__tests__/homeScreen.test.ts
apps/mobile/src/__tests__/practiceScreen.test.ts
apps/mobile/src/app/conversation.tsx
apps/mobile/src/app/free-talk.tsx
apps/mobile/src/app/practice.tsx
apps/mobile/src/audio/session.ts
apps/mobile/src/audio/useAssistantPlayback.ts
apps/mobile/src/audio/useCachedAudio.ts
apps/mobile/src/freeTalk/state.ts
apps/mobile/src/freeTalk/workflow.ts
apps/mobile/src/speech/PronunciationFeedback.tsx
apps/mobile/src/speech/SpeechControls.tsx
apps/mobile/src/speech/SpeechEvidence.tsx
apps/mobile/src/speech/useSpeechTurn.ts
apps/mobile/src/speech/workflow.ts
docs/benchmark/conversation-latency-2026-09-16.json
docs/development/conversation-practice.md
services/api/scripts/conversation_latency.py
```

### git diff --stat

```text
 README.md                                          |  22 ++-
 apps/mobile/README.md                              |  59 ++++---
 apps/mobile/expo-env.d.ts                          |   6 +-
 apps/mobile/package-lock.json                      |  21 +--
 apps/mobile/package.json                           |   1 +
 apps/mobile/src/__tests__/apiClient.test.ts        | 186 ++++++++++++++++++++-
 apps/mobile/src/api/client.ts                      |  98 +++++++++--
 apps/mobile/src/api/openapi.generated.ts           |   4 +
 apps/mobile/src/api/openapi.json                   |  58 +++++++
 apps/mobile/src/api/types.ts                       |   3 +
 apps/mobile/src/app/_layout.tsx                    |   3 +
 apps/mobile/src/app/history.tsx                    |   6 -
 apps/mobile/src/app/index.tsx                      |  18 +-
 apps/mobile/src/app/pronunciation.tsx              |   5 -
 apps/mobile/src/audio/PlaybackButton.tsx           |  62 +++++--
 apps/mobile/src/audio/useAudioCapture.ts           |  64 ++++++-
 apps/mobile/src/components/Ui.tsx                  |   4 +-
 docs/testing/physical-device.md                    |  89 +++++++++-
 services/api/.env.example                          |   4 +-
 services/api/README.md                             |  19 ++-
 services/api/pyproject.toml                        |   1 +
 services/api/src/benma_api/api/routes.py           |  13 +-
 services/api/src/benma_api/config.py               |   4 +-
 .../benma_api/contextual_interpretation/openai.py  |  37 +++-
 services/api/src/benma_api/conversation/service.py |  28 ++--
 services/api/src/benma_api/schemas.py              |   2 +
 services/api/tests/test_assistant_generation.py    |  39 ++++-
 .../api/tests/test_assistant_speech_provider.py    |  12 ++
 .../test_contextual_interpretation_provider.py     |  40 +++++
 29 files changed, 756 insertions(+), 152 deletions(-)
```

### git status --short

```text
 M README.md
 M apps/mobile/README.md
 M apps/mobile/expo-env.d.ts
 M apps/mobile/package-lock.json
 M apps/mobile/package.json
 M apps/mobile/src/__tests__/apiClient.test.ts
 M apps/mobile/src/api/client.ts
 M apps/mobile/src/api/openapi.generated.ts
 M apps/mobile/src/api/openapi.json
 M apps/mobile/src/api/types.ts
 M apps/mobile/src/app/_layout.tsx
 M apps/mobile/src/app/history.tsx
 M apps/mobile/src/app/index.tsx
 M apps/mobile/src/app/pronunciation.tsx
 M apps/mobile/src/audio/PlaybackButton.tsx
 M apps/mobile/src/audio/useAudioCapture.ts
 M apps/mobile/src/components/Ui.tsx
 M docs/testing/physical-device.md
 M services/api/.env.example
 M services/api/README.md
 M services/api/pyproject.toml
 M services/api/src/benma_api/api/routes.py
 M services/api/src/benma_api/config.py
 M services/api/src/benma_api/contextual_interpretation/openai.py
 M services/api/src/benma_api/conversation/service.py
 M services/api/src/benma_api/schemas.py
 M services/api/tests/test_assistant_generation.py
 M services/api/tests/test_assistant_speech_provider.py
 M services/api/tests/test_contextual_interpretation_provider.py
?? apps/mobile/.gitignore
?? apps/mobile/src/__tests__/assistantPlayback.local-cache.test.ts
?? apps/mobile/src/__tests__/audioCapture.test.ts
?? apps/mobile/src/__tests__/freeTalkScreen.test.ts
?? apps/mobile/src/__tests__/freeTalkWorkflow.test.ts
?? apps/mobile/src/__tests__/homeScreen.test.ts
?? apps/mobile/src/__tests__/practiceScreen.test.ts
?? apps/mobile/src/app/conversation.tsx
?? apps/mobile/src/app/free-talk.tsx
?? apps/mobile/src/app/practice.tsx
?? apps/mobile/src/audio/session.ts
?? apps/mobile/src/audio/useAssistantPlayback.ts
?? apps/mobile/src/audio/useCachedAudio.ts
?? apps/mobile/src/freeTalk/
?? apps/mobile/src/speech/
?? docs/benchmark/conversation-latency-2026-09-16.json
?? docs/development/
?? services/api/scripts/conversation_latency.py
```
