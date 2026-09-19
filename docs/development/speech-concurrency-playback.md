# Speech feedback, concurrency, and local playback — final runtime pass

The playback implementation and earlier validation below remain applicable.
The [transcript-conditioned analysis correction](perceived-speech-analysis.md) adds migration 0010
and supersedes the original free-speech presentation. Current dependency graph:

```text
record → stop → upload/canonicalize (owned immutable utterance)
  ├─ unknown-target perception → persisted perceived text → heard text immediately
  │    ├─ transcript-conditioned pitch/alignment analysis → tone chart
  │    └─ Conversation: contextual interpretation → meaning progress
  │         → assistant generation → commit user/assistant evidence → assistant text
  │              → AssistantSpeech → authenticated download → validated local file
  │                   → native loaded → play → native playing status
  └─ known target: create attempt from explicit target
       ├─ provider assessment ─┐
       ├─ acoustic analysis ──┼─ persist exact branch results → pronunciation interpretation
       └─ target alignment ───┘
```

The mobile client starts transcript-conditioned analysis and contextual interpretation immediately
after successful perception. Known-target analysis still starts after upload alongside perception.
The server owns internal pitch/alignment/assessment work and persists exact evidence lineage.
A session is never shared between concurrent workers.

Free speech displays the measured pitch contour and a schematic lexical-tone reference for the
persisted perceived text. The autocorrelation algorithm remains experimental: octave errors,
uncalibrated voicing thresholds, and utterance-local normalization prohibit categorical tone or
intended-target accuracy claims. These limits do not suppress visual evidence. Missing alignment
uses a clearly untimed tone strip; unresolved readings stay uncertain. Meaning is a separate block.

Each UI turn retains its perception identity while meaning, feedback, assistant text,
and voice arrive. Optional analysis never holds the reply, TTS, or next recording.
Interpretation progress comes from the server and remains provisional until persistence.
A successful transaction commits the user/assistant pair. As before, a handled generation
failure commits the user turn, interpretation, and failed generation provenance without an
assistant turn. A failed response clears provisional meaning and reloads durable turns,
leaving the independently committed perception and acoustic evidence intact.

The upload is a prerequisite for all audio consumers. Meaning needs perception;
generation needs meaning and locked conversation history; TTS needs persisted
generation text; native playback needs a verified local artifact and a loaded player.
These dependencies remain sequential. No reasoning benchmark or model/voice default
changes are part of this work.

Timing separates server computation (per provider), parallel branch wall time, UI
receipt of heard/meaning/assistant text, cache time, native load-to-play request, and
native playing status. Native playing status is an audible-response proxy; physical
speaker onset still requires an iPhone measurement. Summing concurrent provider times
does not measure elapsed pipeline latency.

## Final behavior and implementation review

The interrupted work was retained and reviewed in the existing dirty tree. No reset, revert,
checkout, stash, staging, or commit was performed. The existing Conversation/Practice structure,
`gpt-5.6-terra` medium defaults, separate interpretation/generation calls, grounded clarification,
DragonHDFlash assistant voice, and existing ReferenceSpeech voice are preserved. No paid provider
experiment was rerun. This earlier playback pass made no schema change; the current correction adds migration 0010.

The old `SpeechEvidence` conditional replaced all speech feedback with the CLARIFY uncertainty
message. It now always renders the heard-speech feedback independently and places uncertainty in
**Meaning**. PRESERVE retains the transcript without redundant understood text. INFER additionally
shows explicit changed wording and distinct understood text, without treating that text as a target.
CLARIFY retains the transcript, conservative feedback, and replay alongside unresolved meaning and
the grounded assistant clarification. Incomplete speech receives the same evidence-based treatment;
punctuation does not establish an acoustic pause, trailing off, wrong tone, or unfinished proposition.

Free speech exposes exact perception, learner replay, measured F0, expected lexical-tone shapes,
and the comparison between heard and understood wording. The new perceived-speech analysis endpoint
appends evidence tied to the exact PerceptionRun. It never creates a pronunciation target or a
provider pronunciation assessment. Raw acoustic evidence remains separately persisted.

Known-target Practice still uses the learner's explicitly prepared target, immutable target snapshot,
full provider assessment, acoustic/alignment evidence, calibration-gated interpretation, and existing
reference/learner playback and pitch display. No inferred conversation wording reaches this pipeline.

## Actual task dependencies and concurrency

| Task | Required inputs / prerequisite | Concurrency in the implemented path |
| --- | --- | --- |
| Stop and finalize recording | Active recorder | Finishes before upload |
| Upload and canonicalization | Complete local recording | Persists owned original and canonical audio before consumers start |
| Unknown-target perception | Uploaded utterance only | Runs beside known-target analysis; free-speech analysis starts after its result |
| Transcript-conditioned analysis | Owned canonical audio and successful persisted perception | Pitch and alignment overlap; independent of meaning, generation, TTS, and next recording |
| Heard-text display | Successful perception with a transcript | Immediate callback; does not await optional analysis or meaning |
| Contextual interpretation | Perception and locked server conversation history | Sequential after perception; can overlap optional acoustic work |
| Meaning display | Server interpretation NDJSON event | Before generation completes; client does not derive semantic evidence |
| Assistant generation | Interpretation and conversation context | Sequential after interpretation; can overlap optional acoustic work |
| Assistant text display | Committed user/assistant response | Before TTS; retains the same keyed heard-text component |
| AssistantSpeech | Persisted generation ID/text | Separate retryable resource; can overlap lingering optional analysis |
| Audio fetch/cache | Successful AssistantSpeech or ReferenceSpeech, or owned learner recording | Authenticated bytes, verified before native replacement |
| Native playback | Valid local file, current loaded item, no active recording | `play()` follows native readiness; native playing status supplies the audible proxy |
| Known-target attempt | Uploaded utterance and explicitly prepared target | Does not depend on perception |
| Provider assessment | Owned attempt, audio, immutable target snapshot | Concurrent with acoustic analysis and alignment on server workers |
| Acoustic analysis for target | Owned canonical audio | Concurrent with assessment/alignment; reused if already present |
| Target alignment | Owned audio, target text/pinyin, duration | Concurrent with provider assessment/acoustics; no dependency on either output |
| Pronunciation interpretation | The exact completed assessment/acoustic/alignment runs | Runs after branch results are available and flushed; failed branches remain explicit evidence |

The client starts separate public resources and stores server results for presentation. Internal
pronunciation fan-out, reuse, ownership checks, failure evidence, and lineage selection remain
server-owned. The three prepared computations do not access a SQLAlchemy session; one calling
session appends their results and derives interpretation using those objects' exact IDs. Response
projection is pinned to the resulting interpretation ID and its referenced evidence IDs, not a race
between separate “latest” queries. Reuse requests hold attempt/utterance locks through commit.

Optional analysis uses its own capacity limiter so it cannot consume upload/perception/TTS worker
slots. During final review, the utterance lock was changed to PostgreSQL `FOR NO KEY UPDATE`:
it still conflicts with another analysis lock but permits the key-share lock used by perception's
foreign-key insert. See [PostgreSQL's row-lock compatibility table](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS).
The tests compile the actual service queries with the PostgreSQL dialect to guard this behavior;
this environment's integration database is SQLite, so multi-connection PostgreSQL locking itself
was not exercised. No local PostgreSQL container was running.

## Failure isolation

- Acoustic failure retains perception and the conversational reply, shows additional analysis as
  unavailable, and does not keep the recording control busy.
- Perception failure retains the uploaded utterance and any known-target analysis. Free-speech
  analysis starts only after a successful retry supplies a persisted perception. Completed analysis
  promises and the server uniqueness/locking policy prevent duplicate analysis on response retries.
- Interpretation/response failure cannot rewrite perception. The UI clears provisional meaning and
  reloads authoritative persisted turns. Existing failed-generation lineage behavior is preserved.
- TTS, cache, or native-player failure leaves assistant text intact. Speech retries reference only
  persisted generation IDs, never client-provided text.
- Individual known-target provider/acoustic/alignment failures become failed branch evidence;
  successful sibling outputs remain available to the conservative pronunciation interpretation.
- Recording, navigation, auth reset, and newer playback requests invalidate pending autoplay.
  Reference playback stays mounted and disabled during recording, preserving its replay cache.

## iOS cache/player defect and fix

The installed `expo-audio` 57.0.3 source distinguishes the optional constructor argument
`AudioSource?` from native `replace`'s required `AudioSource` record in `ios/AudioModule.swift`.
The JS wrapper forwards a null unchanged. The cache hook called `replace(null)` after its success
log and before passing the file URI. That is a concrete native bridge contract defect matching the
reported failure boundary. The filename hypothesis was checked: the incoming hook already selected
`.wav`, `.m4a`, or `.webm`, so extensionless files were not the defect in this tree.

The implementation now replaces the current item directly with the verified `file:///…` URI.
There are **no production `replace(null)` calls**. Auth reset passes an empty source record, which
is valid for the installed native bridge and detaches the iOS item, then clears private cache files.
The stable `useAudioPlayer(null, { keepAudioSessionActive: true })` constructor remains appropriate;
Expo owns disposal on unmount. Keeping the shared iOS session active across pauses preserves the
prior fix for delayed session deactivation. Capture retains recording-enabled/silent-mode audio
configuration and coordinates foreground players before microphone preparation.

Cache validation now checks container signatures, WAV RIFF/chunk bounds (including padded ancillary
chunks), known MIME/container agreement, file existence, size, and exact bytes read back after write.
Expo's installed iOS `File.write(Uint8Array)` writes binary bytes directly; it creates the file at its
cache-directory URI. There is no base64 conversion or protected remote URI handed to the player.
WAV/M4A/WebM extensions follow verified containers; resource kind/opaque ID and a private player
slot form the filename, without a URL or credentials.

Native readiness and the current player's `isLoaded` gate `play()`. A 15-second load timeout surfaces
an otherwise silent load failure. Generation counters, a per-resource in-flight map, listener/timer
cleanup, auth-slot rotation, and stale-download deletion prevent old completions from replacing or
retaining a newer/account-reset source. Loaded replay reuses the local file and seeks to zero after
completion. Recording cancels pending download/load/seek autoplay.

Development-only diagnostics retain extension, verified size/container, readiness, cache timing,
load-to-play request timing, native playing timing, and the failing operation. Exception text is never
printed: diagnostics allow only a fixed category, recognized Apple error domain, and numeric OS code.
No Authorization header, bearer token, protected URL, or provider secret is logged.
See the [Expo Audio](https://docs.expo.dev/versions/latest/sdk/audio/) and
[FileSystem](https://docs.expo.dev/versions/latest/sdk/filesystem/) public contracts; the installed
native code was the authority for the null-source mismatch.

Automated AssistantSpeech WAV and ReferenceSpeech WAV use the same protected cache/loaded-player
path. Learner M4A and WebM extensions and byte preservation, replay, source replacement, auth reset,
stale completion, corruption, and recording interruption are covered. These use mocked native APIs;
they do not prove AVFoundation decoding or speaker output. WebM remains limited to platforms/codecs
that support it. Physical iPhone playback is still **unverified**.

## Timing architecture and measurement limits

| Metric | Supplied iPhone run 1 / run 2 | Current measurement / architecture |
| --- | --- | --- |
| Upload | 311 / 181 ms | Client request wall time, unchanged prerequisite |
| Perception | 1734 / 2070 ms | Client request wall time; optional analysis has separate worker capacity |
| Stop → heard | 2075 / 2274 ms | Callback/UI update dispatch directly after perception; no optional-branch join |
| Speech analysis | Not supplied | Independent branch wall time plus acoustic server computation |
| Interpretation | 3207 / 1693 ms | Server duration on streamed interpretation event; meaning may render immediately |
| Generation | 1514 / 1617 ms | Server provider/validation duration on committed response event |
| Stop → assistant text | 6892 / 5757 ms | UI update dispatch after committed response; independent of analysis/TTS |
| TTS | 1218 / 1533 ms | Separate client request wall time; provider latency also remains in persisted speech evidence |
| Audio cache | 38 / 40 ms | Authenticated download, write, and verification wall time |
| Local load → play request | Failed before local replacement | Measured from local replacement to loaded-gated `play()` |
| Stop → native playing | No successful audible result | Measured when native reports playing; physical speaker onset measured separately |

Before: known-target Practice waited for perception, then ran assessment, acoustics, and alignment
serially. After: perception overlaps the attempt/analysis resource, and the three server computations
overlap. `provider_compute_sum_ms` is explicitly a sum of computation durations;
`analysis_wall_ms` measures server elapsed time and branch wall logs include transport/queueing.
The independent Conversation acoustic branch has no position on the required reply path.

There are no new post-fix iPhone timings yet. The concurrency tests prove overlap using a three-worker
barrier, verify no worker SQL, and require streamed meaning bytes to leave the server before a blocked
generator can finish. Client deferred-promise tests prove early heard/meaning display and text before
TTS. These are dependency/behavior checks, not paid latency benchmarks or physical rendering timings.

## Historical playback-pass validation — 2026-09-17

| Check | Result |
| --- | --- |
| Focused mobile feedback / Conversation / Practice / cached audio / API client | 70 passed, 5 suites |
| Full mobile Jest | 82 passed, 10 suites |
| Mobile ESLint | Passed |
| Mobile TypeScript | Passed, including generated contracts |
| Android Expo export | Passed; `/tmp/benma-runtime-android` |
| Focused API speech, perception, interpretation, conversation, generation, pronunciation, ownership, concurrency | 138 passed |
| Full API suite | 160 passed |
| API Ruff | Passed |
| API strict mypy | Passed, 64 source files |
| OpenAPI regeneration | Passed; schemas/DTOs generated from backend |
| Second OpenAPI/DTO generation | Idempotent; both SHA-256 values unchanged |
| Migration/Alembic regression | Existing migration tests included in passing full API suite; no schema changes |
| Offline benchmark suite | 96 passed |
| `git diff --check` | Passed |
| Secret scan | No high-confidence secret patterns found |

Streaming tests stalled on restricted-sandbox thread-to-event-loop wakeups. They and the focused/full
API suites passed outside that sandbox using the same permitted local pytest invocation; no test was
weakened or skipped for that restriction. Other checks ran in the normal workspace environment.
Final logs are `/tmp/benma-mobile-focused-runtime.log`, `/tmp/benma-mobile-full-runtime.log`,
`/tmp/benma-api-focused-runtime.log`, `/tmp/benma-api-full-runtime.log`,
`/tmp/benma-benchmark-runtime.log`, and `/tmp/benma-android-runtime.log`.

## Shortest next physical iPhone acceptance run

1. In separate zsh terminals run `benma-api` and `benma-mobile`. Open the Expo QR link on the iPhone,
   sign in, and open Conversation.
2. Say **你好，今天我们聊聊周末吧。** Stop. Check early selectable heard text, speech feedback even if
   CLARIFY, optional distinct understood text, assistant text, Flash voice preparation, local WAV
   **autoplay**, then replay with **no second audio HTTP download**.
3. While playback is active, record **我周末喜欢去公园散步。你呢？** Check the playback-to-microphone
   transition, retained conversation context, independent feedback, and second autoplay.
4. Say **你好，今天我……** and stop. Check heard text/replay/feedback remain while Meaning may stay
   unresolved; speech itself must not be reported as failed.
5. Open free Practice: record, check no assistant or invented score, and replay learner audio.
   Add target **你好**, prepare it, play ReferenceSpeech twice, then record and verify full target
   assessment. The reference player must remain usable after recording.
6. Capture upload, perception, Stop→heard, analysis branch, interpretation, generation, Stop→text,
   TTS, cache, local load→play, and Stop→native-playing logs; separately note actual audible onset.
   Confirm selected text copies and repeat with the intended speaker/headphone route.

The expanded interruption, auth reset, and optional-failure checklist is in
[physical-device.md](../testing/physical-device.md). Physical native playback, live NDJSON delivery,
actual latency, text selection, audio routing, and speech quality remain acceptance checks. There is
no remaining automated-validation blocker. This pass did not commit or start another milestone.

## Final working-tree inventory

This inventory includes all incoming work and this follow-up. The standard diff stat excludes
untracked files; the complete file list below includes them without staging anything.

35 modified tracked files and 25 untracked files.

The runtime changes primarily affect the shared speech workflow/evidence UI, progressive
Conversation transport, optional analysis resource, prepared pronunciation computations, shared
audio cache/player, generated contracts, regression suites, and development/acceptance docs.
The existing navigation, recorder, model/voice defaults, and earlier benchmark artifacts remain
part of the incoming uncommitted milestone.

### Files changed (tracked and untracked)

```text
README.md
apps/mobile/.gitignore
apps/mobile/README.md
apps/mobile/expo-env.d.ts
apps/mobile/package-lock.json
apps/mobile/package.json
apps/mobile/src/__tests__/apiClient.test.ts
apps/mobile/src/__tests__/assistantPlayback.local-cache.test.ts
apps/mobile/src/__tests__/audioCapture.test.ts
apps/mobile/src/__tests__/freeTalkScreen.test.ts
apps/mobile/src/__tests__/freeTalkWorkflow.test.ts
apps/mobile/src/__tests__/homeScreen.test.ts
apps/mobile/src/__tests__/practiceScreen.test.ts
apps/mobile/src/api/client.ts
apps/mobile/src/api/openapi.generated.ts
apps/mobile/src/api/openapi.json
apps/mobile/src/api/types.ts
apps/mobile/src/app/_layout.tsx
apps/mobile/src/app/conversation.tsx
apps/mobile/src/app/free-talk.tsx
apps/mobile/src/app/history.tsx
apps/mobile/src/app/index.tsx
apps/mobile/src/app/practice.tsx
apps/mobile/src/app/pronunciation.tsx
apps/mobile/src/audio/PlaybackButton.tsx
apps/mobile/src/audio/session.ts
apps/mobile/src/audio/useAssistantPlayback.ts
apps/mobile/src/audio/useAudioCapture.ts
apps/mobile/src/audio/useCachedAudio.ts
apps/mobile/src/components/Ui.tsx
apps/mobile/src/freeTalk/state.ts
apps/mobile/src/freeTalk/workflow.ts
apps/mobile/src/speech/PronunciationFeedback.tsx
apps/mobile/src/speech/SpeechControls.tsx
apps/mobile/src/speech/SpeechEvidence.tsx
apps/mobile/src/speech/useSpeechTurn.ts
apps/mobile/src/speech/workflow.ts
docs/benchmark/conversation-latency-2026-09-16.json
docs/development/conversation-practice.md
docs/development/speech-concurrency-playback.md
docs/testing/physical-device.md
services/api/.env.example
services/api/README.md
services/api/pyproject.toml
services/api/scripts/conversation_latency.py
services/api/src/benma_api/api/blocking.py
services/api/src/benma_api/api/routes.py
services/api/src/benma_api/config.py
services/api/src/benma_api/contextual_interpretation/openai.py
services/api/src/benma_api/conversation/service.py
services/api/src/benma_api/pronunciation/acoustics.py
services/api/src/benma_api/pronunciation/alignment.py
services/api/src/benma_api/pronunciation/laboratory.py
services/api/src/benma_api/pronunciation/service.py
services/api/src/benma_api/schemas.py
services/api/tests/test_assistant_generation.py
services/api/tests/test_assistant_speech_provider.py
services/api/tests/test_blocking.py
services/api/tests/test_contextual_interpretation_provider.py
services/api/tests/test_speech_concurrency.py
```

### Full git diff --stat

```text
 README.md                                          |  25 +-
 apps/mobile/README.md                              |  68 ++--
 apps/mobile/expo-env.d.ts                          |   6 +-
 apps/mobile/package-lock.json                      |  21 +-
 apps/mobile/package.json                           |   1 +
 apps/mobile/src/__tests__/apiClient.test.ts        | 235 +++++++++++++-
 apps/mobile/src/api/client.ts                      | 146 ++++++++-
 apps/mobile/src/api/openapi.generated.ts           |  12 +
 apps/mobile/src/api/openapi.json                   | 352 +++++++++++++++++++++
 apps/mobile/src/api/types.ts                       |   4 +
 apps/mobile/src/app/_layout.tsx                    |   3 +
 apps/mobile/src/app/history.tsx                    |   6 -
 apps/mobile/src/app/index.tsx                      |  18 +-
 apps/mobile/src/app/pronunciation.tsx              |   5 -
 apps/mobile/src/audio/PlaybackButton.tsx           |  62 +++-
 apps/mobile/src/audio/useAudioCapture.ts           |  64 +++-
 apps/mobile/src/components/Ui.tsx                  |   4 +-
 docs/testing/physical-device.md                    |  97 +++++-
 services/api/.env.example                          |   4 +-
 services/api/README.md                             |  32 +-
 services/api/pyproject.toml                        |   2 +
 services/api/src/benma_api/api/blocking.py         |  10 +
 services/api/src/benma_api/api/routes.py           | 207 +++++++++---
 services/api/src/benma_api/config.py               |   4 +-
 .../benma_api/contextual_interpretation/openai.py  |  37 ++-
 services/api/src/benma_api/conversation/service.py |  42 ++-
 .../api/src/benma_api/pronunciation/acoustics.py   |  96 +++---
 .../api/src/benma_api/pronunciation/alignment.py   | 129 ++++----
 .../api/src/benma_api/pronunciation/laboratory.py  | 141 +++++++--
 .../api/src/benma_api/pronunciation/service.py     | 143 +++++----
 services/api/src/benma_api/schemas.py              |  13 +
 services/api/tests/test_assistant_generation.py    |  39 ++-
 .../api/tests/test_assistant_speech_provider.py    |  12 +
 services/api/tests/test_blocking.py                |  16 +
 .../test_contextual_interpretation_provider.py     |  40 +++
 35 files changed, 1715 insertions(+), 381 deletions(-)
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
 M services/api/src/benma_api/api/blocking.py
 M services/api/src/benma_api/api/routes.py
 M services/api/src/benma_api/config.py
 M services/api/src/benma_api/contextual_interpretation/openai.py
 M services/api/src/benma_api/conversation/service.py
 M services/api/src/benma_api/pronunciation/acoustics.py
 M services/api/src/benma_api/pronunciation/alignment.py
 M services/api/src/benma_api/pronunciation/laboratory.py
 M services/api/src/benma_api/pronunciation/service.py
 M services/api/src/benma_api/schemas.py
 M services/api/tests/test_assistant_generation.py
 M services/api/tests/test_assistant_speech_provider.py
 M services/api/tests/test_blocking.py
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
?? services/api/tests/test_speech_concurrency.py
```
