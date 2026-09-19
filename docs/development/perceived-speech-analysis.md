# Transcript-conditioned speech analysis — 2026-09-17

This correction continues the current dirty Conversation/Practice milestone. Existing work and
playback architecture are retained. Nothing is committed; no subsequent milestone has begun.

The later [learner-experience pass](pronunciation-learner-experience.md) supersedes this report's
reading, scatterplot and untimed-strip presentation: context-aware lexical resolution, paired
Expected/Mine cards, stable async placeholders, separate filtered display contours, conservative
acoustic shape labels and validated timing reuse. The semantic and persistence boundaries below
remain in force; historical validation counts below describe the earlier pass.

## Four separate meanings

| Concept | Source and use |
| --- | --- |
| Perceived text | Immutable `PerceptionRun.transcript`: what audio-only perception heard. |
| Alignment reference | Exact persisted perceived-text snapshot for free speech. Conditions acoustic alignment and lexical-tone lookup; does not establish intention. |
| Contextual interpretation | Downstream preserve/infer/clarify result. May propose other wording; cannot rewrite perception or the reference. |
| Intended target | Explicitly prepared/confirmed learner phrase represented by the existing `PronunciationTarget`. Supports the existing provider target-relative assessment. |

For **周谋 → context suggests 周末**, the free-speech analysis retains **周谋 / zhōu móu / 1 2**.
It never constructs a target or assesses 末 from inference. A later correction appends evidence;
re-requesting the old analysis returns the old reference/result. A separate future intended-target
assessment can coexist with it.

## Workflow and public contract

```text
record → upload/canonical audio → audio-only perception → persisted perceived transcript
                                                          ├→ heard text immediately
                                                          ├→ transcript-conditioned analysis
                                                          │   ├→ pitch extraction ─┐
                                                          │   └→ alignment ────────┴→ persist → chart
                                                          └→ contextual interpretation
                                                               → assistant generation → text
                                                                    → AssistantSpeech → cache → play

explicit target + uploaded audio → known-target assessment / acoustics / alignment
                                    → persisted pronunciation interpretation and result
```

Free Practice uses the top flow without the interpretation/assistant branch. Known-target Practice
still begins analysis after upload alongside perception, and uses the existing reference speech and
provider assessment pipeline. Neither chart completion nor TTS holds the next recording control.

`POST /v1/perceptions/{id}/speech-analysis` accepts only an empty object. Strict request validation
rejects supplied text, inferred wording, or target IDs. The server authorizes perception, utterance,
and canonical audio and requires a successful nonempty perception. It reads no contextual record,
correction, or target. The exact normalized provider transcript is copied without trimming or
rewriting punctuation. Character offsets refer to that unchanged snapshot.

The response includes ID, perception/utterance IDs, reference text/kind, version, status, latency,
creation time, and a typed data projection: syllables, marked pinyin, lexical tones, reading sources
and alternatives, optional timestamps, schematic tone points, measured pitch with null unvoiced
spans, duration, voiced coverage, quality markers, safe observations, and branch timings.
`GET /v1/perceived-speech-analyses/{id}` retrieves that owned immutable result. No provider payload,
file path, credential, model prompt, or internal configuration enters this contract. OpenAPI and
mobile types are generated from these schemas.

## Reading, timing, and acoustic limits

The existing `parse_mandarin_target` pure dictionary parser is reused for contiguous Han text;
no target object is created. Its name is historical: parsing a reading does not establish intention.
Punctuation and unsupported non-Han tokens do not become syllables. Original character offsets
are preserved. The installed pypinyin version and the reading/normalization policy are recorded.
Phrase-dictionary evidence can resolve readings (for example 银行). A persisted pronunciation token
with matching text and exact character offsets takes precedence. Ordinary ASR text/logprob tokens
do not establish a reading. Unresolved polyphones retain alternatives and null pinyin/tone;
there is no semantic-model substitution or unmarked dictionary guess.

The reference track contains schematic **lexical** tone shapes, on its own ordinal height scale.
The shapes use the conventional 55/35/214/51 citation patterns on a five-level scale, rescaled
to 0..1 ([Berkeley phonetics reference](https://linguistics.berkeley.edu/acip/appendix/languages/chinese/chinese_tone.html)).
It is not reference-speaker F0. Third-tone sandhi, prosody, coarticulation, and neutral tones can
change the expected surface realization; no difference from a lexical shape is graded as wrong.
Neutral tone is labeled 0 and variable, with no invented fixed contour. Unknown readings have no
invented shape. The known-target surface-tone interpreter remains unchanged.

The existing autocorrelation analyzer produces F0, utterance-relative semitones, voicing evidence,
and recording quality. It can double/halve pitch, has uncalibrated thresholds, and does not establish
a speaker's full range. Version 2.1.0 fixes mobile downsampling to preserve the recording tail and
representative unvoiced gaps without exceeding 240 points. Full-resolution evidence is retained in
`AcousticRun`; no missing F0 is interpolated. The chart plots only available measurements.

The optional existing aligner now calls its generic input `reference_text`. Valid, ordered syllable
intervals use recording time for both measured and expected tracks. Invalid/non-finite boundaries,
missing aligner, mixed unsupported speech, or unresolved readings leave timing unavailable. The UI
still shows measured pitch, with a separate expected strip explicitly labeled text order. Replay
alignment is synthetic and never presented as measured timing. No live aligner was newly installed
or calibrated in this pass; default disabled alignment remains an honest untimed fallback.

Free-speech analysis can show what was heard, its reading/reference pattern, actual pitch estimates,
coverage, and trustworthy timing where available. It cannot establish what the learner intended,
pronunciation accuracy against that intention, categorical wrong tones, or a defensible overall
correctness percentage. It returns **no scores** and never calls a pronunciation-assessment provider.

## Persistence and failure isolation

Migration **0010**, after 0009, adds only `perceived_speech_analyses`. Each append-only row stores:

- account, utterance, perception, canonical audio and acoustic-run IDs, plus canonical audio SHA-256;
- exact alignment-reference snapshot, analyzer version, configuration and configuration SHA-256;
- reading engine/policy, acoustic algorithm/version/parameters, alignment algorithm/version/models/timeout;
- derived typed acoustic/alignment result, status/error code, total latency and creation time.

The table has no intended-target or contextual-interpretation foreign key. ORM append-only guards
protect both old perception and new analysis. The unique `(perception_run_id, configuration_sha256)`
constraint and PostgreSQL `FOR NO KEY UPDATE` lock serialize identical requests through commit.
Failed outcomes are reused too; a different analyzer version/config appends a new row. Corrections
do not change this key or any prior evidence. Successful acoustic reuse also checks parameters.

The service prepares input on its owning database session, computes acoustic and alignment work in
separate threads without SQL, then persists exact results on the original session. The optional
analysis capacity budget remains separate from upload/perception/TTS. Perception and utterance
locks permit foreign-key key-share insertion by the meaning/conversation branch.

Alignment failure preserves pitch; pitch failure persists failed evidence plus reference/readings.
Meaning/generation failure cannot cancel the analysis. Analysis failure preserves heard text,
conversation continuation, reply/TTS, replay, and the next recording. Mobile retains the analysis
promise across retries and keys free-speech feedback by **perception ID**, avoiding collisions when
multiple perceptions refer to the same utterance. No SQL session is shared between worker threads.

## Mobile presentation and playback

`SpeechEvidence` is shared by Conversation and Practice: heard text, distinct understood text only
for infer, Pronunciation, learner replay, an explicit differing-wording note, and separate Meaning
for clarify. Preserve omits redundant understood text. Unfinished speech keeps the same chart.
The old generic target-required/listen-again/recording-duration presentation is removed.

`TranscriptFeedback` and `SyllableToneStrip` render the new structured result. `PitchPlot` remains
the common native pitch visualization used by free speech, known-target Practice, and the legacy
laboratory. Its regions and points now share the full recording time axis, including trailing silence.
Timed long sentences share a horizontal scroll for the measured chart and tone strip. Untimed
references scroll in text order below the raw chart. Pinyin/tone labels and unresolved alternatives
are server-derived; mobile does not reconstruct linguistic analysis.

Known-target feedback retains target text/pinyin, full provider assessment, conservative tone
interpretation, chart, ReferenceSpeech, and learner audio. A supported provider pronunciation score
is labeled as accuracy versus the explicit target. That label never appears in free speech.

Shared authenticated audio download/cache, container validation, WAV/M4A/WebM handling, native
readiness, replay, interruption, and cleanup remain intact. No `replace(null)` was reintroduced.
Physical iPhone speaker output and native routing remain unverified by automated tests.

Development logs include transcript-analysis request wall time, persisted total, pitch extraction,
alignment, and Stop→chart availability, alongside Stop→heard/text/native-playing. The chart metric
marks UI update dispatch, not a measured physical display frame. Timings stay out of production UI.

## Automated validation

| Check | Final result |
| --- | --- |
| Focused mobile chart / Conversation / Practice / workflow / playback / API client | 82 passed, 8 suites |
| Full mobile Jest | 89 passed, 11 suites |
| Mobile ESLint and TypeScript, including regenerated contracts | Passed |
| Android Expo export | Passed; `/tmp/benma-tone-android` |
| Focused API speech/perception/context/conversation/generation/provider/ownership/concurrency | 159 passed |
| Full API, with real PostgreSQL concurrency enabled | 181 passed |
| New perceived-analysis + PostgreSQL focused checks | 21 passed |
| API Ruff and strict mypy | Passed; 65 source files |
| SQLite migration upgrade/downgrade and Alembic schema check | Passed in full API suite |
| Local PostgreSQL migration | Applied 0009 → 0010; `alembic check` reports no drift; head is 0010 |
| OpenAPI/mobile DTO generation | Passed; second generation verified identical SHA-256 hashes |
| Offline benchmark tests | 96 passed |
| `git diff --check` | Passed |
| Repository secret scan | No high-confidence secret patterns found |

The restricted-sandbox API run stalled on the existing streaming thread-to-event-loop wakeup;
it was stopped. The full and focused API suites passed outside that sandbox with the same tests.
The opt-in PostgreSQL test (`BENMA_TEST_POSTGRES=1`) uses an isolated random schema in the configured
local database, confirms duplicate requests invoke acoustic extraction only once, verifies meaning
can persist while extraction is blocked, and removes its own schema afterward. No test was weakened.
No paid model/TTS benchmark ran, and no new physical latency figures are claimed.

Final logs: `/tmp/benma-api-tone-full-unsandboxed.log`, `/tmp/benma-api-tone-regression.log`,
`/tmp/benma-api-tone-postgres.log`, `/tmp/benma-mobile-tone-full.log`,
`/tmp/benma-mobile-tone-focused.log`, `/tmp/benma-benchmark-tone.log`, and
`/tmp/benma-tone-android.log`. Historical milestone reports retain their earlier check counts.

## Shortest physical acceptance run

Run `benma-api` and `benma-mobile` in separate zsh terminals, open the Expo QR link on the iPhone,
sign in, and use the configured live providers. The existing `benma-api` helper runs migrations
automatically; this workspace's local PostgreSQL database is already at 0010.

1. **Conversation:** say **你好，今天我们聊聊周末吧。** Check early heard text, measured chart,
   sane pinyin/tone segmentation with uncertainty exposed, reference tied to heard text, independent
   assistant text arrival, assistant autoplay, **Play response**, and **Play mine**.
2. Say it again while intentionally pronouncing **周末** poorly. If perception differs, preserve
   that raw text and its chart; show a context-suggested **周末** separately. No target-relative score.
3. Say **你好，今天我……**. Chart/replay remain; Meaning may be unresolved.
4. **Free Practice:** say arbitrary Mandarin. Verify heard text, chart, replay, no assistant reply,
   and no target-required message.
5. **Known-target Practice:** prepare **你好**, play ReferenceSpeech, record, inspect the chart and
   provider target-relative assessment, and replay the learner recording.

Capture **Stop→heard**, **Stop→chart**, **Stop→assistant text**, and **Stop→audible reply** for the
Conversation turns. Note whether alignment is configured or the explicitly untimed fallback is used.
The broader interruption/cache/auth checklist remains in [physical-device.md](../testing/physical-device.md).


## Final semantic review and remaining acceptance

The complete dirty diff was reviewed, including the inherited playback/concurrency changes.
Searches found no learner-facing target-required dead end, free-speech score, inferred-text input
to analysis, automatically perceived-text-created target, duplicate pitch implementation, or
`replace(null)` call. Only explicit target creation/pinyin revision endpoints instantiate targets.
The generic internal aligner reference field is distinct from the `PronunciationTarget` domain.
Obsolete free-speech duration-only documentation and Home wording were updated.

There is no remaining automated-validation or migration blocker for physical acceptance. Actual
microphone-to-screen latency, iOS speaker/autoplay/replay, native routing, and live-provider speech
quality still require the iPhone checklist. Optional live forced alignment is not configured by
this correction; unavailable timing remains visible and does not hide pitch. Commit remains pending
physical acceptance and the user's separate instruction. No commit or new milestone was started.

## Complete working-tree inventory

This includes inherited uncommitted work and this correction. Nothing has been staged.
There are 71 changed/new files. `git diff --stat` below includes tracked files only;
the file inventory and status also include new files.

### Files changed

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
apps/mobile/src/__tests__/perceivedFixture.ts
apps/mobile/src/__tests__/practiceScreen.test.ts
apps/mobile/src/__tests__/transcriptFeedback.test.ts
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
apps/mobile/src/components/PitchPlot.tsx
apps/mobile/src/components/Ui.tsx
apps/mobile/src/freeTalk/state.ts
apps/mobile/src/freeTalk/workflow.ts
apps/mobile/src/speech/PronunciationFeedback.tsx
apps/mobile/src/speech/SpeechControls.tsx
apps/mobile/src/speech/SpeechEvidence.tsx
apps/mobile/src/speech/TranscriptFeedback.tsx
apps/mobile/src/speech/useSpeechTurn.ts
apps/mobile/src/speech/workflow.ts
docs/benchmark/conversation-latency-2026-09-16.json
docs/development/conversation-practice.md
docs/development/perceived-speech-analysis.md
docs/development/speech-concurrency-playback.md
docs/testing/physical-device.md
services/api/.env.example
services/api/README.md
services/api/migrations/versions/0010_perceived_speech_analysis.py
services/api/pyproject.toml
services/api/scripts/conversation_latency.py
services/api/src/benma_api/api/blocking.py
services/api/src/benma_api/api/routes.py
services/api/src/benma_api/config.py
services/api/src/benma_api/contextual_interpretation/openai.py
services/api/src/benma_api/conversation/service.py
services/api/src/benma_api/db/models.py
services/api/src/benma_api/pronunciation/acoustics.py
services/api/src/benma_api/pronunciation/alignment.py
services/api/src/benma_api/pronunciation/laboratory.py
services/api/src/benma_api/pronunciation/perceived.py
services/api/src/benma_api/pronunciation/service.py
services/api/src/benma_api/schemas.py
services/api/tests/test_assistant_generation.py
services/api/tests/test_assistant_speech_provider.py
services/api/tests/test_blocking.py
services/api/tests/test_contextual_interpretation_provider.py
services/api/tests/test_migrations.py
services/api/tests/test_perceived_postgres.py
services/api/tests/test_perceived_speech.py
services/api/tests/test_speech_concurrency.py
```

### Full git diff --stat

```text
 README.md                                          |   28 +-
 apps/mobile/README.md                              |   70 +-
 apps/mobile/expo-env.d.ts                          |    6 +-
 apps/mobile/package-lock.json                      |   21 +-
 apps/mobile/package.json                           |    1 +
 apps/mobile/src/__tests__/apiClient.test.ts        |  249 +++-
 apps/mobile/src/api/client.ts                      |  157 ++-
 apps/mobile/src/api/openapi.generated.ts           |   64 +
 apps/mobile/src/api/openapi.json                   | 1301 +++++++++++++++++---
 apps/mobile/src/api/types.ts                       |    7 +
 apps/mobile/src/app/_layout.tsx                    |    3 +
 apps/mobile/src/app/history.tsx                    |    6 -
 apps/mobile/src/app/index.tsx                      |   18 +-
 apps/mobile/src/app/pronunciation.tsx              |    5 -
 apps/mobile/src/audio/PlaybackButton.tsx           |   62 +-
 apps/mobile/src/audio/useAudioCapture.ts           |   64 +-
 apps/mobile/src/components/PitchPlot.tsx           |   23 +-
 apps/mobile/src/components/Ui.tsx                  |    4 +-
 docs/testing/physical-device.md                    |  103 +-
 services/api/.env.example                          |    4 +-
 services/api/README.md                             |   38 +-
 services/api/pyproject.toml                        |    3 +
 services/api/src/benma_api/api/blocking.py         |   10 +
 services/api/src/benma_api/api/routes.py           |  242 +++-
 services/api/src/benma_api/config.py               |    4 +-
 .../benma_api/contextual_interpretation/openai.py  |   37 +-
 services/api/src/benma_api/conversation/service.py |   42 +-
 services/api/src/benma_api/db/models.py            |   34 +
 .../api/src/benma_api/pronunciation/acoustics.py   |  107 +-
 .../api/src/benma_api/pronunciation/alignment.py   |  136 +-
 .../api/src/benma_api/pronunciation/laboratory.py  |  141 ++-
 .../api/src/benma_api/pronunciation/service.py     |  143 ++-
 services/api/src/benma_api/schemas.py              |   74 ++
 services/api/tests/test_assistant_generation.py    |   39 +-
 .../api/tests/test_assistant_speech_provider.py    |   12 +
 services/api/tests/test_blocking.py                |   16 +
 .../test_contextual_interpretation_provider.py     |   40 +
 services/api/tests/test_migrations.py              |    1 +
 38 files changed, 2744 insertions(+), 571 deletions(-)
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
 M apps/mobile/src/components/PitchPlot.tsx
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
 M services/api/src/benma_api/db/models.py
 M services/api/src/benma_api/pronunciation/acoustics.py
 M services/api/src/benma_api/pronunciation/alignment.py
 M services/api/src/benma_api/pronunciation/laboratory.py
 M services/api/src/benma_api/pronunciation/service.py
 M services/api/src/benma_api/schemas.py
 M services/api/tests/test_assistant_generation.py
 M services/api/tests/test_assistant_speech_provider.py
 M services/api/tests/test_blocking.py
 M services/api/tests/test_contextual_interpretation_provider.py
 M services/api/tests/test_migrations.py
?? apps/mobile/.gitignore
?? apps/mobile/src/__tests__/assistantPlayback.local-cache.test.ts
?? apps/mobile/src/__tests__/audioCapture.test.ts
?? apps/mobile/src/__tests__/freeTalkScreen.test.ts
?? apps/mobile/src/__tests__/freeTalkWorkflow.test.ts
?? apps/mobile/src/__tests__/homeScreen.test.ts
?? apps/mobile/src/__tests__/perceivedFixture.ts
?? apps/mobile/src/__tests__/practiceScreen.test.ts
?? apps/mobile/src/__tests__/transcriptFeedback.test.ts
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
?? services/api/migrations/versions/0010_perceived_speech_analysis.py
?? services/api/scripts/conversation_latency.py
?? services/api/src/benma_api/pronunciation/perceived.py
?? services/api/tests/test_perceived_postgres.py
?? services/api/tests/test_perceived_speech.py
?? services/api/tests/test_speech_concurrency.py
```
