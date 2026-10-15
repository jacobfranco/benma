# Learner pronunciation experience — 2026-09-17, finalized 2026-09-18

## October 10, 2026 — dominant tone families and primary learner grades

This policy supersedes earlier comparison/color descriptions below. The acoustic
layer classifies the dominant supported measured gesture without knowing target,
characters, readings, lexical tones, expected tones, transcript or reference TTS.
A small boundary counter-movement may remain subordinate to a coherent primary
rise, fall or valley. Full-track corruption gates and perturbation checks remain.

The linguistic layer supplies explicit surface expectations where resolved. Those
expectations remain authoritative, including 一, 不 and resolved T3 sandhi. When
surface realization is null but reading/pinyin and lexical tone 1–4 are resolved,
the learner layer may grade against that lexical family. It does not rewrite the
surface field. Details say “Tone N family” and “Connected-speech realization may
vary here.” Contextual coaching refines the explanation without erasing a useful
family judgment. Unresolved readings remain unavailable.

As of October 13, learner correctness uses an asymmetric conservative policy:
trustworthy compatible numbered families default to green (“Pitch acceptable”);
meaningful interpretation uncertainty is amber (“Pitch may be off”); only strong,
stable incompatible evidence is red; unavailable evidence or unresolved required
context is gray. Compatible families with fewer than 6/7 agreeing probes remain
amber because of interpretation sensitivity. Small excursion alone never changes
a grade. `LearnerPitchGrade.coaching` remains independent, including on green units.

Red requires support ≥0.90, maximum acceptable-family support ≤0.20,
winner–acceptable margin ≥0.70, winner–runner-up margin ≥0.60, clarity ≥0.90,
and at least seven probes with 100% agreement. Explicit surface rules remain
authoritative; the existing unresolved adjacent-T3 fallback may accept T3/T2,
never T4. See the [conservative grading audit](../research/pronunciation-v2/2026-10-13-conservative-grading/README.md)
for the exact rules, every changed grade, threshold rationale and validation.

Neutral uses contextual dependent-syllable acceptance, without a fixed numbered
tone. In recognized chunks with separate accepted timing and exact playback,
structurally supported neutral can be positively accepted. Unmeasured neutral can
remain non-vetoing. Neither can hide a red, amber or unavailable grade-bearing head. Standalone,
optional-neutral, unresolved and grouped cases remain bounded.

See [implementation, frozen replay and validation](../research/pronunciation-v2/2026-10-09-product-feedback/dominant-gesture-pass.md).


This pass continues the existing dirty tree without resetting, replacing, staging, or committing
prior work. It preserves the perception → independent pronunciation/meaning branches and does
not start another milestone. No paid speech provider or benchmark was run.

## Separate meanings and evidence

| Concept | Question answered | Permitted source |
| --- | --- | --- |
| Reading resolution | Which pronunciation does this exact perceived text have in its own lexical context? | Immutable transcript, phrase dictionary, narrow grammar rules, or exact persisted pronunciation tokens |
| Contextual interpretation | What did the learner probably mean? | Downstream interpretation; may propose different characters, never an alignment reference |
| Observed contour | What acoustic tone-like shape did the learner produce? | Full-resolution recorded F0 and trustworthy syllable boundaries |
| Intended-target accuracy | How well did the learner realize a legitimately known target? | Explicit target and existing provider assessment/interpretation |

Free speech provides lexical expectations and observed acoustic shapes, never target-relative
accuracy. For perceived **周谋** with inferred **周末**, reading/alignment remain **zhōu móu**.
Lexical tones and expected surface tones stay separate. Free speech labels citation tones; known
targets retain existing modeled sandhi rules. An unmodeled surface tone now stays null instead
of silently falling back to a lexical tone under a surface-tone label.

## Root cause, resolution hierarchy, neutral tones and polyphones

The previous resolver called `pypinyin(..., heteronym=True)` and rejected every result with more
than one alternative. In installed pypinyin 0.55, **聊聊**, **周末**, and **今天** are absent from the
phrase dictionary. The first two consequently expose rare single-character alternatives
(`liao2/liu2`, `mo4/me5`). **吧** has particle and lexical readings. This was a resolver-policy and
lexicon-coverage problem, not evidence that the learner said something ambiguous.

The new deterministic resolver uses longest multi-character matches in the existing phrase
lexicon, with reviewed supplements for 聊聊/聊天/周末/今天 and lexical 吧 compounds. It then applies
clause-final 吧 → ba5 and restricted plural-suffix 们 → men5 rules. Unique character readings and
three reviewed modern defaults (聊/末/去) follow. It does **not** choose the first reading of every
polyphone. Bare 行, 重, and 吧 remain unresolved. Exact persisted pronunciation tokens retain
precedence, with matching character offsets. Phrase lookup and character lookup use bounded
immutable caches; there is no language-model request.

The example resolves to:

| Characters | Pinyin | Lexical tones |
| --- | --- | --- |
| 你好 | nǐ hǎo | 3 3 |
| 今天 | jīn tiān | 1 1 |
| 我们 | wǒ men | 3 0 |
| 聊聊 | liáo liáo | 2 2 |
| 周末 | zhōu mò | 1 4 |
| 吧 | ba | 0 |

Tests include 银行/行走, 音乐/快乐, 长大/长江, 重新/重量, 酒吧 versus 去吧, and genuinely unresolved
bare polyphones. Each occurrence keeps its original character offsets, marked pinyin, lexical
tone, source, alternatives and resolution confidence. Neutral tone is 0 with a variable shape;
no fixed neutral-tone F0 is invented. Greedy lexical segmentation and these grammar rules are
conservative heuristics, not a complete Mandarin syntax or proper-name parser.

The library's documented behavior supports this diagnosis: [pypinyin usage and custom
lexicons](https://pypinyin.readthedocs.io/zh-cn/master/usage.html).

## Raw pitch, display processing, observed classification

`AcousticRun.normalized_result.f0` remains the full raw measurement series. Existing rows are
append-only. `measured_pitch` remains the raw mobile projection. New `display_contour` fields
contain separate segments and an independently derived baseline/domain. Classification never
uses the lexical tone or the provider correctness score as an input.

Display processing is deterministic:

1. Require finite voiced samples in a broad 40–1000 Hz range and confidence ≥0.45 when supplied.
   These display limits are distinct from the existing tracker's 50–550 Hz extraction range.
2. In a contiguous local window, reject a point only when at least two neighbors on **each** side
   support a local median and its deviation exceeds `max(6 st, 3 × 1.4826 × MAD)`.
   This rejects isolated octave/artifact jumps, preserves sustained high/low regions, and does
   not attempt to correct an octave by guessing the true pitch.
3. Recompute a display-only median baseline; normalize to semitones. Smooth with a median of
   three inside each retained region, preserving endpoints.
4. Every missing, unvoiced, rejected, non-increasing, or >45 ms-separated sample breaks the line.
   No samples are interpolated, including across short gaps.
5. Preserve at least a −3…+3 st display domain and retain genuine surviving extrema. An isolated
   rejected tracker artifact cannot stretch the axis.
6. After classification, simplify line vertices to ≤0.15 st linear error within each region.
   Only existing measured timestamps remain, and no region is joined to another. This reduces
   native View count on long recordings; classification retains full-resolution input.

The classifier requires real timing, duration 120–1500 ms, at least eight voiced samples, at least
50% voiced coverage, no >90 ms internal voiced gap, and adequate retention of raw voiced samples.
It rejects jagged paths using total movement versus range. Median start/end windows, range,
minimum location, and total movement yield:

- 1-like: range ≤1.5 st, endpoint change ≤1 st;
- 2-like / 4-like: endpoint change ≥2 st upward/downward with sufficiently monotonic movement;
- 3-like: an interior valley at 20–80%, at least 1.5 st below both endpoint regions;
- unclear: insufficient, fragmented, noisy, or ambiguous evidence.

Confidence is at most `moderate`. Neutral/unstressed classification is intentionally unavailable:
F0 alone does not establish stress. A low level or connected half-third tone cannot be assigned
categorically from this classifier. Sandhi, declination, creaky voice, coarticulation, sustained
tracker errors, and alignment errors remain limitations. This is an approximate shape label,
not a phonological verdict, speaker-range estimate, or provider-grade correctness score.

## Primary UI, stable async layout and secondary chart

Conversation and Free Practice render the Pronunciation section as soon as perceived text exists.
The same `TranscriptFeedback` instance hydrates a predictable 270 px section. Character skeletons,
loaded cells, and error state share the same row height. Cards scroll horizontally; long speech
adds columns rather than vertical height. Each card pairs character/pinyin, expected lexical tone
and schematic line with the measured Mine line and its tone-like label or local uncertainty.

Conversation creates a separate pending BENMA card at perception and preserves its reply key.
Assistant text/TTS still arrive independently of analysis. More detail is a user-controlled
expansion: the whole-utterance connected line chart, methodology, recording issues, and unresolved
reading alternatives are secondary. Normal success has no diagnostic prose wall. Raw points do
not dominate the chart. Known-target Practice reuses the paired cells and processed charts while
retaining scores, reference speech, learner replay, and target-specific interpretation in details.

Actual Chromium measurements with delayed branches:

| State | Pronunciation height | Assistant label Y |
| --- | --- | --- |
| Perception, skeleton | 270 px | pending card reserved |
| Assistant ready, analysis pending | 270 px | 732 px |
| Analysis hydrated | 270 px | 732 px |

The pronunciation DOM node remained the identical node. At 390 px viewport width, its height
remained 270 px and its Y remained 500 px across loading/hydration; no document overflow occurred.
Automatic analysis arrival needs no height animation. Only deliberate details expansion grows it.
Large accessibility-font sizes and physical device gestures still need the device checklist.

## Syllable timing: what improved and what remains unavailable

Three issues explained unavailable timing: unresolved readings stopped the aligner; alignment
is disabled by default; and the TextGrid parser concatenated overlapping word and phone tiers.
It now chooses a single explicit syllable tier, otherwise a word tier, and validates boundaries
and one-to-one labels. A multi-character word interval is never divided into invented syllables.
This matches MFA's documented [word and phone output tiers](https://montreal-forced-aligner.readthedocs.io/en/stable/user_guide/corpus_structure.html).

Free speech also reuses exact persisted one-character ASR token timestamps, when present and
valid, without another alignment call. Known-target Practice can reuse exact provider syllable
or single-character word timestamps when forced alignment is absent. Integration tests verify
this produces expected Tone 4 alongside an independently measured 1-like contour. Invalid spans,
wrong labels, and multi-character word spans do not qualify. Replay timing stays visibly synthetic
and never supplies a learner shape classification.

**Timing is now available when those real existing boundaries exist.** The default live ASR adapter
currently returns text/logprobs, not syllable timestamps, and no MFA executable/model is installed
here. Its default free-speech path therefore still honestly shows timing unavailable. A configured,
validated live syllable aligner is a remaining gate for per-character Mine feedback in that setup.
No unvalidated aligner, acoustic model download, or paid provider call was introduced.

## Latency measurements and changes

These are local fixture measurements, not production-provider or physical-iPhone benchmarks.

| Stage | 3.6-second generated harmonic / SQLite ASGI |
| --- | ---: |
| Reading resolution, cold | 3.22 ms |
| Reading resolution, warm microbenchmark | 0.13 ms |
| Pitch extraction before optimization | 4,754.51 ms |
| Pitch extraction after optimization, same microbenchmark | 1,123.46 ms |
| Pitch extraction inside service profile | 1,162 ms |
| Replay alignment | 0 ms rounded; live MFA latency **unmeasured** |
| Display processing in microbenchmark | 2.09 ms |
| Classification of 11 synthetic timing slices in microbenchmark | 0.62 ms |
| Service display processing/simplification | 2.57 ms (replay timing excludes classification) |
| Acoustic persistence flush | 1.95 ms |
| Analysis insert/commit | 1.34 ms |
| Analysis service wall, including commit | 1,173.40 ms |
| ASGI request total | 1,181.87 ms |
| Same persisted analysis request | 5.70 ms; identical run reused |

Pitch extraction now precomputes Hamming weights and prefix energy sums, and uses a C-backed
multiply iterator for each lag's dot product. This removes repeated work without resampling,
changing the search, adding a decoder/dependency, or modifying old evidence. On the comparison
fixture, **all 357 rounded raw F0/confidence/normalization frames were identical**, with about
**4.2×** faster extraction. This is a single-machine comparison, not a general speed guarantee.

In Chromium with a synthetic harmonic microphone, the ungated 1.38-second recording took
**739 ms Stop → chart**. Its analysis request took **476 ms**, server analysis **457 ms**, pitch
**452 ms**, reading **0.21 ms**, contour processing **1.14 ms**, and acoustic flush **1.35 ms**.
The roughly **19 ms** request/server difference includes auth, database setup, queueing,
serialization and loopback transport; it is not pure network RTT. Response → rendered-frame
was **≤61 ms**, measured with browser observation and two animation frames; automation polling
is included, so this is an upper bound, not a React CPU duration. Live ASR/network/MFA costs are
not represented by the replay providers.

Development logs now expose request overhead, response-to-frame and Stop-to-frame. The server
reports reading/contour/flush timings and logs final commit/wall timing without rewriting the
append-only result. Existing pitch/alignment concurrency, analysis reuse, and retry deduplication
remain. Audio is decoded once per new acoustic run from canonical WAV; analysis adds no FFmpeg
conversion. Lexical caches and display simplification reduce repeated work. Progressive API
streaming was not added: it would require a larger persistence/protocol change for a reading
stage that now takes fractions of a millisecond warm.

## Automated validation

| Check | Result |
| --- | --- |
| Focused reading/acoustic/alignment/target API tests | 77 passed after final timing review |
| Full API | Recorded pass: 256 passed, 1 skipped (opt-in PostgreSQL integration); three additional timing regressions subsequently passed in the focused suite |
| API Ruff / strict mypy | Passed; 67 source files |
| Migrations | Existing migration tests pass in full API suite; this pass adds no migration |
| OpenAPI | Contract regenerated; two successive exports hash-identical |
| Focused pronunciation / Conversation / Practice / geometry UI tests | 59 passed, native and web |
| Full Jest | 20 suites, 179 tests passed |
| TypeScript / Expo ESLint | Passed, no lint warnings |
| Expo web export / Android export | Passed |
| Online Expo dependency check | Dependencies are up to date |
| Offline benchmark pytest | 96 passed |
| Benchmark Ruff / mypy / corpus / fixture run / fixture report | Passed |
| Pronunciation calibration command | Completed; existing 0/50 real pilot recordings, calibration not ready |
| git diff --check / secret scan | Passed |

The continuation reviewed the existing diff and untracked implementation. No production code changed
after the recorded full-suite passes. Three additional timing tests cover synthetic ASR-token rejection,
two independently sliced syllables, and a multi-character TextGrid word remaining unsplit. The updated
focused API suite and Ruff passed; prior full Jest, TypeScript, ESLint, exports, dependency, API/mypy,
OpenAPI and offline benchmark results remain applicable. The optional positive-shape browser preview's
line assertion was changed to wait for asynchronous layout. The expensive speedup benchmark was not rerun.

Tests defend immutable references despite inferred wording; neutral/polyphonic readings; octave
artifacts, preserved raw data, gaps and line geometry; canonical/noisy shape labels; exact-timing
reuse; unresolved surface tones; stable component identity before/after both branches; paired
Expected/Mine cells; hidden global detail; independent response/analysis and no duplicate runs;
and existing auth, Conversation/Practice, playback, platform transport/capture and export paths.
The restricted runtime stalled the threaded streaming API test and the ASGI service profiler;
both completed with normal local process/socket access. No automatic approval rejection blocked
work. React-test-renderer retains its existing deprecation warnings.

## Browser and physical-device validation

Chromium **153.0.8010.36** exercised real multipart/FFmpeg/auth/storage/workflows with isolated
SQLite and unpaid provider fixtures. The fake microphone was fed a generated harmonic WAV.
The fixture perceived text was exactly **你好，今天我们聊聊周末吧。** All expected readings appeared
without spurious question marks. Server gates made each arrival order reviewable. Desktop 1440 px
and narrow 390 px were checked; the global chart contained actual connected line elements.
Conversation, Free Practice, target Practice, learner/reference/assistant replay, response autoplay
and injected autoplay denial recovery, auth restoration/logout and cleanup passed. Four uploads
returned 201; no uncaught page errors, live owned object URLs, or microphone tracks remained.

The harness additionally supports `BENMA_SHAPE_PREVIEW=1`, an explicitly synthetic response-only
render fixture for positive Mine curves/labels. It never changes persisted evidence, and retains
the visible Development fixture banner. The positive-shape preview passed after its layout wait was fixed; the paired rising/falling/dipping/level lines were visually inspected. These preview contours are not real acoustic validation.

A separate headless Chromium run **successfully captured a real local input device** for one
second (48 kHz mono WebM/Opus, 15,752 bytes), then stopped the tracks. Audio was not saved or sent
to providers. No person spoke and verified the requested Mandarin sentence during that check.
Thus real microphone capture works here, but live Mandarin perception, timing/classifier quality,
and audible replay with the configured providers remain unvalidated. No physical iPhone or Android
hardware validation is claimed by browser dimensions or Expo exports.

Artifacts are under `/tmp`: `benma-browser-smoke.log`, `benma-browser-preview-final.log`,
`benma-pronunciation-stable.png`, `benma-paired-shapes-preview.png`, `benma-conversation-narrow.png`,
`benma-contour-detail.png`, `benma-contour-narrow.png`, `benma-practice-desktop.png`,
`benma-real-mic-result.json`, `benma-pitch-profile.json`, and `benma-service-profile.json`.
The machine-readable measurement snapshot is [pronunciation-experience-2026-09-17.json](../benchmark/pronunciation-experience-2026-09-17.json).

## Manual acceptance and commit gates

Use the [short human checklist](../testing/pronunciation-manual-acceptance.md) with `benma-api`
and `benma-mobile`. Readings, layout and audio acceptance can begin immediately. Real per-syllable
Mine acceptance is blocked until trustworthy timing is configured. After human and physical-device
acceptance, no additional code blocker is known from this pass; the opt-in PostgreSQL check remains
unrun, and calibration readiness is still separate from acoustic-shape visualization.


1. Configure and validate real syllable alignment (or an ASR adapter with exact character timing)
   for the currently untimed live free-speech setup. Do not fill this gap with equal partitions.
2. A person must speak the requested example using live configured providers and inspect tone
   shapes, replay and assistant audio. No paid provider benchmark was used as a substitute.
3. Physical iPhone validation: native capture/upload, Mine/reference/assistant playback,
   interruption, routes/silent mode, narrow horizontal scrolling and accessibility text sizes.
   Android export passes; physical Android audio remains a manual check.
4. Opt-in PostgreSQL concurrency/integration remains unrun; the full SQLite/migration and
   concurrency tests pass. Existing calibration-corpus readiness remains a separate limitation.

No known failure remains in the exercised automated and Chromium fixture paths. No commit was
created, no existing dirty work was discarded, and no subsequent milestone was started.

## 20. Files changed in this pass

The list below compares file contents against the initial dirty-tree snapshot. The benchmark
calibration manifest change is regenerated metadata; prior milestone changes remain present.

- `apps/mobile/scripts/web-smoke.cjs`
- `apps/mobile/src/__tests__/freeTalkScreen.test.ts`
- `apps/mobile/src/__tests__/pitchPlot.test.ts`
- `apps/mobile/src/__tests__/practiceScreen.test.ts`
- `apps/mobile/src/__tests__/transcriptFeedback.test.ts`
- `apps/mobile/src/api/openapi.generated.ts`
- `apps/mobile/src/api/openapi.json`
- `apps/mobile/src/api/types.ts`
- `apps/mobile/src/app/free-talk.tsx`
- `apps/mobile/src/components/PitchPlot.tsx`
- `apps/mobile/src/speech/PronunciationFeedback.tsx`
- `apps/mobile/src/speech/SpeechEvidence.tsx`
- `apps/mobile/src/speech/SyllableComparison.tsx`
- `apps/mobile/src/speech/TranscriptFeedback.tsx`
- `apps/mobile/src/speech/workflow.ts`
- `benchmark/reports/outputs/pronunciation-calibration.manifest.json`
- `docs/benchmark/pronunciation-experience-2026-09-17.json`
- `docs/development/perceived-speech-analysis.md`
- `docs/development/pronunciation-learner-experience.md`
- `docs/testing/physical-device.md`
- `docs/testing/pronunciation-manual-acceptance.md`
- `services/api/src/benma_api/pronunciation/acoustics.py`
- `services/api/src/benma_api/pronunciation/alignment.py`
- `services/api/src/benma_api/pronunciation/contours.py`
- `services/api/src/benma_api/pronunciation/laboratory.py`
- `services/api/src/benma_api/pronunciation/perceived.py`
- `services/api/src/benma_api/pronunciation/readings.py`
- `services/api/src/benma_api/schemas.py`
- `services/api/tests/test_perceived_speech.py`
- `services/api/tests/test_pronunciation_laboratory.py`
- `services/api/tests/test_readings_contours.py`
- `services/api/tests/web_smoke_app.py`

## 21. Full git diff --stat

This includes the prior dirty milestone; untracked files are excluded by Git.

```text
 Makefile                                           |    1 +
 README.md                                          |   31 +-
 apps/mobile/README.md                              |  137 +-
 apps/mobile/expo-env.d.ts                          |    6 +-
 apps/mobile/package-lock.json                      | 2008 ++++++++++++--------
 apps/mobile/package.json                           |   58 +-
 apps/mobile/src/__tests__/apiClient.test.ts        |  249 ++-
 apps/mobile/src/__tests__/pitchPlot.test.ts        |    9 +-
 apps/mobile/src/api/client.ts                      |  168 +-
 apps/mobile/src/api/openapi.generated.ts           |   95 +
 apps/mobile/src/api/openapi.json                   | 1454 ++++++++++++--
 apps/mobile/src/api/types.ts                       |   10 +
 apps/mobile/src/app/_layout.tsx                    |   18 +-
 apps/mobile/src/app/history.tsx                    |    6 -
 apps/mobile/src/app/index.tsx                      |   23 +-
 apps/mobile/src/app/pronunciation.tsx              |    5 -
 apps/mobile/src/audio/PlaybackButton.tsx           |   64 +-
 apps/mobile/src/audio/useAudioCapture.ts           |   97 +-
 apps/mobile/src/auth/AuthProvider.tsx              |   13 +-
 apps/mobile/src/components/PitchPlot.tsx           |  218 +--
 apps/mobile/src/components/Ui.tsx                  |   19 +-
 .../pronunciation-calibration.manifest.json        |    4 +-
 docs/testing/physical-device.md                    |  163 +-
 services/api/.env.example                          |    8 +-
 services/api/README.md                             |   63 +-
 services/api/pyproject.toml                        |    3 +
 services/api/src/benma_api/api/blocking.py         |   10 +
 services/api/src/benma_api/api/routes.py           |  242 ++-
 services/api/src/benma_api/app.py                  |    9 +
 services/api/src/benma_api/audio/service.py        |    5 +-
 services/api/src/benma_api/config.py               |   31 +-
 .../benma_api/contextual_interpretation/openai.py  |   37 +-
 services/api/src/benma_api/conversation/service.py |   42 +-
 services/api/src/benma_api/db/models.py            |   34 +
 .../api/src/benma_api/pronunciation/acoustics.py   |  125 +-
 .../api/src/benma_api/pronunciation/alignment.py   |  167 +-
 .../api/src/benma_api/pronunciation/laboratory.py  |  218 ++-
 .../api/src/benma_api/pronunciation/service.py     |  143 +-
 services/api/src/benma_api/schemas.py              |  104 +
 services/api/tests/test_assistant_generation.py    |   39 +-
 .../api/tests/test_assistant_speech_provider.py    |   12 +
 services/api/tests/test_audio_utterances.py        |   24 +-
 services/api/tests/test_auth_config.py             |   16 +
 services/api/tests/test_blocking.py                |   16 +
 .../test_contextual_interpretation_provider.py     |   40 +
 services/api/tests/test_migrations.py              |    1 +
 .../api/tests/test_pronunciation_laboratory.py     |   85 +-
 47 files changed, 4788 insertions(+), 1542 deletions(-)
```

## 22. git status --short

```text
 M Makefile
 M README.md
 M apps/mobile/README.md
 M apps/mobile/expo-env.d.ts
 M apps/mobile/package-lock.json
 M apps/mobile/package.json
 M apps/mobile/src/__tests__/apiClient.test.ts
 M apps/mobile/src/__tests__/pitchPlot.test.ts
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
 M apps/mobile/src/auth/AuthProvider.tsx
 M apps/mobile/src/components/PitchPlot.tsx
 M apps/mobile/src/components/Ui.tsx
 M benchmark/reports/outputs/pronunciation-calibration.manifest.json
 M docs/testing/physical-device.md
 M services/api/.env.example
 M services/api/README.md
 M services/api/pyproject.toml
 M services/api/src/benma_api/api/blocking.py
 M services/api/src/benma_api/api/routes.py
 M services/api/src/benma_api/app.py
 M services/api/src/benma_api/audio/service.py
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
 M services/api/tests/test_audio_utterances.py
 M services/api/tests/test_auth_config.py
 M services/api/tests/test_blocking.py
 M services/api/tests/test_contextual_interpretation_provider.py
 M services/api/tests/test_migrations.py
 M services/api/tests/test_pronunciation_laboratory.py
?? apps/mobile/.gitignore
?? apps/mobile/scripts/
?? apps/mobile/src/__tests__/assistantPlayback.local-cache.test.ts
?? apps/mobile/src/__tests__/audioCapture.test.ts
?? apps/mobile/src/__tests__/developmentAuth.test.ts
?? apps/mobile/src/__tests__/developmentAuth.web.test.ts
?? apps/mobile/src/__tests__/freeTalkScreen.test.ts
?? apps/mobile/src/__tests__/freeTalkScreen.web.test.ts
?? apps/mobile/src/__tests__/freeTalkWorkflow.test.ts
?? apps/mobile/src/__tests__/homeScreen.test.ts
?? apps/mobile/src/__tests__/perceivedFixture.ts
?? apps/mobile/src/__tests__/practiceScreen.test.ts
?? apps/mobile/src/__tests__/practiceScreen.web.test.ts
?? apps/mobile/src/__tests__/protectedAudio.web.test.ts
?? apps/mobile/src/__tests__/recordingUpload.web.test.ts
?? apps/mobile/src/__tests__/recordingUri.web.test.ts
?? apps/mobile/src/__tests__/sharedWorkflows.web.test.ts
?? apps/mobile/src/__tests__/transcriptFeedback.test.ts
?? apps/mobile/src/__tests__/transcriptFeedback.web.test.ts
?? apps/mobile/src/app/conversation.tsx
?? apps/mobile/src/app/free-talk.tsx
?? apps/mobile/src/app/practice.tsx
?? apps/mobile/src/audio/PlaybackButton.web.tsx
?? apps/mobile/src/audio/audioData.ts
?? apps/mobile/src/audio/audioTransport.ts
?? apps/mobile/src/audio/audioTransport.web.ts
?? apps/mobile/src/audio/discardRecording.ts
?? apps/mobile/src/audio/discardRecording.web.ts
?? apps/mobile/src/audio/recordingUploadSource.ts
?? apps/mobile/src/audio/recordingUploadSource.types.ts
?? apps/mobile/src/audio/recordingUploadSource.web.ts
?? apps/mobile/src/audio/recordingUri.ts
?? apps/mobile/src/audio/recordingUri.web.ts
?? apps/mobile/src/audio/session.ts
?? apps/mobile/src/audio/useAssistantPlayback.ts
?? apps/mobile/src/audio/useBrowserPlayer.ts
?? apps/mobile/src/audio/useCachedAudio.ts
?? apps/mobile/src/audio/useCachedAudio.web.ts
?? apps/mobile/src/auth/development.ts
?? apps/mobile/src/freeTalk/
?? apps/mobile/src/speech/
?? docs/benchmark/conversation-latency-2026-09-16.json
?? docs/benchmark/pronunciation-experience-2026-09-17.json
?? docs/development/
?? docs/testing/pronunciation-manual-acceptance.md
?? docs/testing/web-compatibility.md
?? services/api/migrations/versions/0010_perceived_speech_analysis.py
?? services/api/scripts/conversation_latency.py
?? services/api/src/benma_api/pronunciation/contours.py
?? services/api/src/benma_api/pronunciation/perceived.py
?? services/api/src/benma_api/pronunciation/readings.py
?? services/api/tests/test_cors.py
?? services/api/tests/test_perceived_postgres.py
?? services/api/tests/test_perceived_speech.py
?? services/api/tests/test_readings_contours.py
?? services/api/tests/test_speech_concurrency.py
?? services/api/tests/web_smoke_app.py
```
