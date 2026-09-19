# Web compatibility review — 2026-09-17

Checkpoint update (2026-09-18): [real-human Chromium acceptance was performed](pronunciation-manual-acceptance.md#checkpoint-acceptance--2026-09-18).
The manual gates below describe this earlier audit. Physical iPhone acceptance, physical
Stop → chart latency, classifier calibration and pronunciation UX polish remain follow-ups
and do not block the checkpoint.

Audit performed before code changes in the existing dirty milestone tree. A = already
cross-platform; B = platform adapter needed; C = acceptable internal/native behavior;
D = product blocker. Validation and final platform matrix are recorded below after execution.

| Area | Initial classification / finding | Resolution |
| --- | --- | --- |
| Protected audio | D: shared `useCachedAudio` imports filesystem; reset creates `Paths.cache` | Browser Blob/HTMLAudioElement adapter; preserve native cache |
| Browser playback | D: Expo 57 web `play()` discards HTMLMediaElement's Promise | Browser player observes rejection; policy block keeps manual play |
| Recording | A/B: Expo MediaRecorder selects supported MIME; stop stops tracks; hook unmount does not stop recorder | Keep Expo recording; add lifecycle cleanup and reset |
| Recording URL ownership | A/B: leases protect uploads and replay; auth reset needs cleanup | Preserve leases; release capture/player ownership on reset |
| Upload | A: native File/Expo fetch; web real Blob/FormData/browser fetch; actual MIME inferred if absent | Preserve native transport; browser integration retest |
| Protected download | B: Expo fetch resolves to global fetch on web, but bytes() is not universal | Platform response reader returns browser Blob with validated bytes |
| Conversation progress | A: installed Expo fetch.web reexports browser fetch; ReadableStream/NDJSON works | Preserve stream and independent analysis/semantic branches |
| Auth storage | A: SecureStore only called on native; web localStorage guarded by Platform | Preserve; handle storage/restore failure without stuck loading |
| Auth transition/reset | D: cleanup can throw before token installation | Isolate each cleanup; token installed even on cleanup failure |
| Routes / deep links | D: product screens can create requests before token restoration | Auth-gated Stack; defer router mount through cold restore |
| Filesystem / URI | B: only cache and native upload runtime imports found | Web resolution excludes filesystem runtime product modules |
| Layout | B: shared ScrollView stretches across desktop | Center bounded content on web; retain native padding |
| Tone chart | A/B: Views/onLayout, no SVG/native-only dependency; timed width fixed | Resize timed viewport; retain shared model and honest gaps |
| Copy | A: heard, inferred, assistant, target and pinyin selectable | Preserve; body text selectable |
| Lifecycle/audio sessions | A/B: native Expo session configuration, browser no-op; pending recording needs cancellation | Stop on unmount/reset and handle late setup/stop |
| Linking / native components | A: Expo Router/Linking and RN screens support web; no custom native-only UI | Keep shared navigation |
| window/document | A: localStorage via globalThis; no module-level DOM evaluation | Browser media objects created on interaction/effect only |
| Internal screens | C: calibration, legacy pronunciation/perception diagnostics use native MIME hints on native | Keep diagnostics; web upload uses actual Blob MIME |
| CORS/auth | A: explicit dev origins, GET/POST/DELETE and Authorization/Content-Type; no wildcard credentials | Verify preflights, auth and protected media |
| Dependencies | A pending checks: Expo 57/RN 0.86.3 aligned; explicit web deps | Check graph, override, exports and audit separately |

Expo's installed `AudioPlayer.web.ts` calls `media.play()` without returning or catching its
Promise. Browser playback therefore uses HTMLAudioElement directly. A rejected
[play Promise](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play)
with `NotAllowedError` is a request for user interaction, not a synthesis failure.
[Expo audio web notes](https://docs.expo.dev/versions/latest/sdk/audio/) also document missing
WebM duration metadata and browser codec differences. Microphones require localhost or
[HTTPS](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).

## Final implementation and platform status

| Feature | iOS / Android through Expo | Chromium web |
| --- | --- | --- |
| Development auth, restore, reset/logout | Supported; SecureStore | Supported; development localStorage |
| Home / routing | Supported | Supported; deep links wait for restoration |
| Recording | Expo native recorder → file URI | Expo MediaRecorder → owned Blob URL |
| Upload | Expo File → FormData → expo/fetch | Fetch recording URL without auth → actual Blob → FormData → browser fetch |
| Conversation / multiple turns | Shared workflow | Two turns exercised against real API |
| Free Practice | Shared workflow, no reply/target requirement | Exercised, no assistant reply |
| Known-target Practice | Shared explicit target / assessment | Target, reference, assessment and chart exercised |
| Early heard text / analysis / meaning / reply | Existing independent DAG preserved | Same shared DAG; progress stream uses browser fetch |
| Tone chart | Shared Views/onLayout, native tests | Desktop 1440 px and narrow 390 px checked |
| Learner replay | Native player / filesystem protected cache | WebM/Opus through authenticated Blob cache |
| Assistant / reference speech | Validated WAV files / expo-audio | Validated WAV Blob URLs / HTMLAudioElement |
| Text selection | Selectable RN text | Selectable RN-web text; clipboard gestures remain manual |

This is implementation support, not physical-device certification. No physical iPhone or
Android was available in this pass. Chromium 153.0.8010.36 is the exercised desktop browser;
Safari/Firefox are not certified. HTTPS or localhost is required for browser microphone access.
LAN HTTP plus CORS alone is insufficient. Browser formats are negotiated; upload never assumes
M4A, 44.1 kHz, or an unparameterized MIME. The observed input was WebM/Opus, mono, 48 kHz.
The API's original-preserving ingest and canonical WAV conversion remain unchanged in this pass.

Native protected media still uses authenticated Expo fetch, shared container/MIME validation,
filesystem cache and Expo playback. WAV chunk checks, post-write verification, load readiness,
recording coordination, and iOS's non-null replacement contract are retained. The default
`.ts` native adapters are also TypeScript's fallback; `.web.ts` overrides select browser devices.
The exported web source map contains all expected web adapters and **zero expo-file-system
sources**, zero native `useCachedAudio.ts`, and zero native `recordingUploadSource.ts`.

The web cache uses authenticated browser fetch, Blob/byte validation and object URLs. Current
source replay reuses its URL; replacements detach the element before revoking the old URL.
Downloads finishing after interruption/reset cannot install a source. Unmount/logout revoke
owned URLs. A global LRU cap retains at most 12 protected player sources, including paused
sources in old mounted conversation cards. Eviction detaches/revokes the oldest source; revisiting
an evicted turn downloads again. Recording URLs use the existing capture/upload/replay leases.
Capture now stops an active microphone on unmount/reset and discards a recorder prepared after
its owner has gone away. Normal native multipart behavior is unchanged.

HTMLAudioElement is used on web because installed Expo Audio drops the `play()` Promise.
Allowed autoplay is attempted. `NotAllowedError` preserves the prepared source and manual
**Play response** control without reporting TTS failure. Download/decode failures show an audio
error while completed text and analysis remain. Recording stops playing/pending media. The
browser smoke observed resolved play Promises, including manual recovery; it did **not** measure
speaker output. Fixture assistant WAV is synthetic/silent, not actual provider speech.

Auth cleanup isolates each owner, so one disposed player cannot prevent installing a token or
cleaning another owner. Cold storage failures resolve to a sign-in error instead of indefinite
loading. Logout clears local auth even on a revocation network error; failed storage clearing is
reported. SecureStore's existing platform abstraction is preserved. Stack protection delays
product startup until restoration and prevents signed-out deep links from creating conversations.
Web hosting must provide an index.html fallback for Expo Router paths.

Desktop content is centered with a 900 px maximum including padding; native sizing is unchanged.
Timed plots now use viewport width when wider than their syllable minimum; long/narrow strips
scroll horizontally. Legends wrap, observed dots preserve gaps, expected lexical shapes stay
separate, and loading buttons keep their phase labels visible. No analysis model was forked.
Legacy perception/pronunciation/calibration/history tools were audited for safe module evaluation;
they were not included in browser product smoke coverage. Their native MIME hints remain because
the existing web upload adapter uses actual Blob evidence.

## CORS and security

Existing explicit development localhost/127.0.0.1:8081 origins and configured LAN origins remain.
GET/POST/DELETE and Authorization/Content-Type preflights are covered. No credentials wildcard,
query token, disabled auth, or broader production default was introduced. Protected media fetches
use bearer headers; browser object URLs contain no token or protected source path. Stable UI/audio
errors avoid logging free-form native/browser exceptions. Unknown API validation payloads now
produce the HTTP fallback rather than an optional-property TypeError.

The earlier reported 422 did not reproduce after startup/cache repairs: the first smoke and all
four full-run recordings returned 201. There was therefore no new validation failure body to
capture, and no backend validation was relaxed. Multipart boundaries are supplied by browser
FormData; the native File/expo-fetch adapter was left intact.

## Dependencies

Online `npx expo install --check`: **Dependencies are up to date**. Installed Expo 57.0.23,
expo-audio 57.0.5, expo-file-system 57.0.7, Router 57.0.21, RN 0.86.3, React/React DOM 19.2.3,
react-native-web 0.21.2 and @expo/metro-runtime 57.0.15 form the checked graph. Constants resolves
to 57.0.18 within its existing ~57.0.8 range. `npm ls --all --json` exits successfully.
There are no major-version changes among matching lockfile package paths versus HEAD; web
dependencies and SDK patch alignment are intentional existing milestone changes.

The Jest override is **no longer required** with the aligned packages. RN now peers on exactly
0.86.3 and jest-expo peers on ^0.86.3. A fresh temporary resolution without the override selected
0.86.3. The redundant override was removed; an offline lock-only install left the lockfile's SHA
unchanged. The project graph still resolves a single preset at 0.86.3. A fresh unlocked temporary
graph also selects newer optional worklets with peer warnings; none of those temporary changes
were applied to the locked app (worklets 0.10.3 / reanimated 4.5.3).

`npm audit` on 2026-09-17 reports **18 findings: 13 moderate, 5 high; no critical**. High findings:
image-size, js-yaml, metro, metro-config, metro-transform-worker. Moderate findings: @expo/cli,
@expo/config, @expo/config-plugins, @expo/inline-modules, @expo/local-build-cache-provider,
@expo/metro-config, @expo/prebuild-config, decode-uri-component, expo, expo-router, query-string,
uuid and xcode. This includes transitive/meta vulnerabilities, not 18 independent exploits.
No audit fixes, major upgrades or paid provider runs were performed.

## Executed validation

| Check | Result |
| --- | --- |
| Full mobile Jest | 20 suites, **174 tests passed**, native and web projects |
| Focused media adapter regressions | Included: native File upload/cache/null replacement; web Blob transport, WAV/WebM validation, reuse/revoke/cap, late cancellation, autoplay denial, capture unmount |
| Shared product behavior on web | Same Conversation/Practice, failure-isolation, concurrency and transcript-chart tests executed via web resolution |
| TypeScript / Expo ESLint | Passed |
| Expo web export (+ source maps) | Passed; browser bundle contains no filesystem sources |
| Expo Android export | Passed |
| Online Expo install check / npm graph | Passed |
| API CORS/auth/audio/upload tests | Passed within full suite, including 31 CORS tests |
| Full API pytest | **215 passed, 1 skipped** (opt-in PostgreSQL integration) |
| API Ruff / strict mypy | Passed; mypy checks 65 source files |
| OpenAPI generation | Regenerated; both checked-in files hash-identical before/after |
| Migrations | SQLite upgrade/downgrade tests passed in full API suite; no migration added by this pass |
| Offline benchmark suite | **96 passed**, Ruff/mypy, corpus validation, fixtures, fixture report and calibration command passed |
| git diff --check / secret scan | Passed |

The restricted runtime stalled a threaded streaming API test. The complete suite was rerun
outside it and passed in 30.81 seconds. Chromium also required ordinary local socket/process
access outside the restricted runtime. No approval rejection prevented work.
React-test-renderer emits its standard deprecation warnings; Jest passes. The benchmark command
refreshed only the tracked calibration manifest's current git SHA and timestamp. It still reports
0/50 real pilot recordings / calibration not ready; this is an existing calibration limitation,
not evidence of browser pronunciation accuracy. That generated change is left reviewable.

## Actual browser smoke

The repository harness is `apps/mobile/scripts/web-smoke.cjs` with
`services/api/tests/web_smoke_app.py`. The harness uses real FastAPI routing/auth, a temporary
SQLite database, real multipart ingestion/FFmpeg, persistence and workflows. Only speech/provider
ports use deterministic fixtures; no network provider keys or charges are needed. Native-style
UI tests do not substitute for this actual Chromium execution.

Verified in Chromium 153.0.8010.36:

- Signed-out deep link, development auth, home refresh and Conversation route refresh.
- Four actual fake-microphone recordings, consecutive starts/stops and duration; all uploads 201.
- Two Conversation turns: transcript, speech analysis/chart, interpretation stream, assistant text,
  assistant WAV download/play; replay reused the current URL without another download.
- Learner WebM playback and recording interrupting playback.
- Successful allowed autoplay and an injected NotAllowedError followed by successful manual play.
  Injected denial tests recovery; it does not claim every Chromium autoplay policy was reproduced.
- Free Practice: transcript, analysis/chart, learner replay and no assistant control.
- Target Practice: explicit target, reference WAV playback, learner upload, assessment, feedback/chart.
- Desktop 1440 px and narrow 390 px rendering; no document overflow at narrow width.
- Router navigation cleanup, logout, refresh remaining signed out: **0 live owned object URLs,
  0 live microphone tracks, no persisted session token**. **0 uncaught page errors**.

Screenshots/logs from this run are in `/tmp/benma-conversation-desktop.png`,
`/tmp/benma-conversation-narrow.png`, `/tmp/benma-practice-desktop.png`, and
`/tmp/benma-browser-smoke.log`. Full command outputs are in `/tmp/benma-mobile-validate.log`,
`/tmp/benma-api-pytest.log`, `/tmp/benma-web-export.log`, `/tmp/benma-android-export.log`,
`/tmp/benma-benchmark.log`, and `/tmp/benma-npm-audit.json`.

To reproduce, with an installed Chromium and Playwright available (no app dependency added):

```sh
cd services/api
uv run uvicorn --app-dir tests web_smoke_app:app --host 127.0.0.1 --port 8000
# In another terminal, from apps/mobile:
CI=1 npx expo export --platform web --output-dir /tmp/benma-web-parity-export
BENMA_PLAYWRIGHT_MODULE=/absolute/path/to/@playwright/test node scripts/web-smoke.cjs
```

The harness serves the exported app on localhost:8081 with SPA fallback and removes its temporary
server on exit. Do not aim it at a live/paid-provider API. It is intentionally an unpaid fixture
integration test, not a provider-quality benchmark.

## Remaining manual checks before committing the milestone

No known code blocker remains in the exercised Chromium path. Manual gates remain:

1. Real desktop microphone and audible speakers/headphones with the configured providers: two
   turns, free/target Practice, reference/response/mine replay, actual policy-blocked autoplay,
   clipboard gestures, permission denial, device disconnection, background/tab transitions.
2. Physical iPhone (and Android): M4A native upload, filesystem audio replacement including the
   prior iOS null-source regression, recording/playback interruption, session reset, silent mode,
   Bluetooth/audio routes, and narrow chart/text presentation.
3. Opt-in PostgreSQL concurrency/integration test was not run; SQLite migration/workflow and
   SQL-lock compilation tests passed. Existing calibration corpus and npm audit findings remain
   separately tracked; this pass makes no provider calibration or cross-browser certification claim.

## Files changed during this pass

Existing dirty work was preserved. No reset/revert/checkout/stash or commit was performed.
The full git outputs below include the preceding milestone's changes, not only this review.
This pass changed:

- `Makefile` (web export in mobile-check), root/mobile READMEs and physical-device guide.
- `apps/mobile/package.json` (remove redundant override; lockfile unchanged by this pass).
- API client transport/error fallback; auth provider restoration/logout; protected Stack routing.
- Shared capture/session coordination, `useCachedAudio` shared validation extraction; shared UI,
  PitchPlot legend wrapping, TranscriptFeedback responsive viewport and removal of provider jargon
  from primary pronunciation score text (retaining its experimental qualification).
- New audioData, native/web audioTransport and discardRecording adapters, useBrowserPlayer,
  web useCachedAudio and web PlaybackButton.
- Web protected-audio tests, web versions of auth/Conversation/Practice/chart/domain tests,
  recording-URI lifecycle test, and platform-aware existing Conversation MIME-hint expectation.
- Browser smoke script and isolated API fixture app.
- This audit/report; benchmark-generated calibration manifest metadata refresh.

## Full git diff --stat

This standard command excludes untracked files; they appear in the status below.

```text
 Makefile                                           |    1 +
 README.md                                          |   31 +-
 apps/mobile/README.md                              |  137 +-
 apps/mobile/expo-env.d.ts                          |    6 +-
 apps/mobile/package-lock.json                      | 2008 ++++++++++++--------
 apps/mobile/package.json                           |   58 +-
 apps/mobile/src/__tests__/apiClient.test.ts        |  249 ++-
 apps/mobile/src/api/client.ts                      |  168 +-
 apps/mobile/src/api/openapi.generated.ts           |   64 +
 apps/mobile/src/api/openapi.json                   | 1301 +++++++++++--
 apps/mobile/src/api/types.ts                       |    7 +
 apps/mobile/src/app/_layout.tsx                    |   18 +-
 apps/mobile/src/app/history.tsx                    |    6 -
 apps/mobile/src/app/index.tsx                      |   23 +-
 apps/mobile/src/app/pronunciation.tsx              |    5 -
 apps/mobile/src/audio/PlaybackButton.tsx           |   64 +-
 apps/mobile/src/audio/useAudioCapture.ts           |   97 +-
 apps/mobile/src/auth/AuthProvider.tsx              |   13 +-
 apps/mobile/src/components/PitchPlot.tsx           |   25 +-
 apps/mobile/src/components/Ui.tsx                  |   19 +-
 .../pronunciation-calibration.manifest.json        |    4 +-
 docs/testing/physical-device.md                    |  152 +-
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
 .../api/src/benma_api/pronunciation/acoustics.py   |  107 +-
 .../api/src/benma_api/pronunciation/alignment.py   |  136 +-
 .../api/src/benma_api/pronunciation/laboratory.py  |  141 +-
 .../api/src/benma_api/pronunciation/service.py     |  143 +-
 services/api/src/benma_api/schemas.py              |   74 +
 services/api/tests/test_assistant_generation.py    |   39 +-
 .../api/tests/test_assistant_speech_provider.py    |   12 +
 services/api/tests/test_audio_utterances.py        |   24 +-
 services/api/tests/test_auth_config.py             |   16 +
 services/api/tests/test_blocking.py                |   16 +
 .../test_contextual_interpretation_provider.py     |   40 +
 services/api/tests/test_migrations.py              |    1 +
 45 files changed, 4284 insertions(+), 1405 deletions(-)
```

## Full git status --short

```text
 M Makefile
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
?? docs/development/
?? docs/testing/web-compatibility.md
?? services/api/migrations/versions/0010_perceived_speech_analysis.py
?? services/api/scripts/conversation_latency.py
?? services/api/src/benma_api/pronunciation/perceived.py
?? services/api/tests/test_cors.py
?? services/api/tests/test_perceived_postgres.py
?? services/api/tests/test_perceived_speech.py
?? services/api/tests/test_speech_concurrency.py
?? services/api/tests/web_smoke_app.py
```
