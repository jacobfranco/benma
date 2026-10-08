# Benma mobile

The Expo/React Native client has two primary modes: Conversation and Practice. Both use
`useSpeechTurn` / `submitSpeech` for capture, upload, target-free perception, checkpoints, and
layer-specific recovery. Actual Mandarin text is selectable.

## Run on a phone

```bash
make mobile-sync
EXPO_PUBLIC_BENMA_API_URL=http://YOUR_LAN_IP:8000 make mobile-dev
```

The API URL is public application configuration, not a secret. Never place speech-provider keys
in an `EXPO_PUBLIC_` variable or the mobile bundle. Android cleartext LAN access may require a
development build/network configuration if Expo Go policy changes; production should use HTTPS.

For Expo web, the API permits `http://localhost:8081` and `http://127.0.0.1:8081` in development.
If the browser opens a LAN address, add that frontend origin to the API's
`BENMA_CORS_ALLOWED_ORIGINS` JSON array and restart the API. See the
[CORS configuration](../../services/api/README.md#development-web-cors). Native requests do not
need this browser allowlist.

Web and native prefill the same development phone number from
[`src/auth/development.ts`](src/auth/development.ts), matching the optional API seed account.
Press **Continue with development account** without editing the field to sign in; edit the number
to use another development account. Existing saved sessions continue to restore normally.

## Screens

- **Conversation** (`/conversation`, with `/free-talk` retained as an alias): create a persisted
  conversation, show perception immediately, reconcile authoritative turns, show separate inferred
  meaning/clarification and speech feedback, render the reply, then request speech by generation ID.
  Recording is available while voice is preparing. Late voice never autoplays over a newer recording.
- **Practice** (`/practice`): free speech shows perception, measured pitch, and conservative surface-tone expectations; dictionary tones stay separate and no intended-target accuracy is claimed.
  An optional manually prepared target enables reference audio, pinyin revisions, and the existing
  known-target attempt persistence. Both modes draw Tone Graph V2 exclusively from perceived-text
  analysis; target differences are a separate text comparison. Reference failure still permits
  a recording. Both modes support replaying the learner recording.
- **Internal tools:** `/perception` and `/pronunciation` retain the old debugging/laboratory flows,
  including corrections, reference/mine playback, pitch diagnostics, history, and A/B comparisons.
  Home offers only Conversation and Practice as primary products. History and calibration remain
  secondary development tools.

Free-speech feedback compares server-returned heard and inferred wording; it never diagnoses a
pronunciation error from inferred text. Tone Graph V2 attaches measured pitch to large perceived-character cells,
with reference pronunciation explicitly behind character tap for the exact persisted heard text. Word-only timing spans one grouped contour without internal character assignment. Untimed characters
keep their cells; technical explanation is behind tap and More detail. Silence/no-speech
returns a concise retry state before successful perception or target assessment; a conservative post-ASR acoustic check also rejects unsupported multi-character claims. More detail exposes
retained samples; Raw is nested developer detail. Missing pitch stays blank, untimed characters
remain visible, and uncertain readings never erase timing. Conservative whole-cell tone-gesture states are consistent/different/uncertain for eligible T1/T2/T4 evidence; T3 and neutral remain uncertain. Observed pitch and reference tone are explicit behind tap. No overall pronunciation grade appears in
these primary flows. Synthetic perception/results retain a fixture banner.

See [Tone Graph V2 semantics, validation, and five-case smoke packet](../../docs/development/tone-graph-v2.md).

## Audio and session boundaries

Recording uploads use Metro platform resolution for `audio/recordingUploadSource`:
the default/native implementation appends a real SDK 57 `expo-file-system` File and sends it
with `expo/fetch`; the `.web.ts` implementation fetches Expo Audio's `blob:` URL, reads a real
browser Blob, and uses browser FormData/fetch. Neither path sets a multipart boundary.
Both keep bearer authentication and the optional practice-session field.

Expo Audio 57 requests WebM on web when supported, otherwise the browser chooses its recording
format. Upload uses the Blob's actual MIME (including codec parameters), with `.webm`, `.m4a`,
or another matching supported extension. Missing MIME is inferred from the container header,
never from the native `.m4a` preset or a hardcoded web hint. The API accepts parameters only for
its existing MIME allowlist and still inspects/canonicalizes the original bytes.

The capture hook retains the latest browser recording for upload retries and local replay.
Replacing it or leaving the screen releases that ownership; uploads and local players hold their
own references until finished. The object URL is revoked only when its last owner releases it.
Conversion errors use the upload failure path. Development diagnostics report only platform,
stage, media type, extension, and byte count. See the
[browser/native upload retest](../../docs/testing/physical-device.md#browser-and-native-recording-upload-retest).

`useCachedAudio` supplies protected AssistantSpeech, ReferenceSpeech and learner playback.
Shared `audioData` validates resource paths, WAV chunks and MIME/container agreement. Metro
chooses the device implementation:

- Native: authenticated `expo/fetch` → bytes → verified `Paths.cache` File → `expo-audio`.
  Replaying the current source reuses its file. Replacement/unmount/session reset clean private
  media. iOS never receives `replace(null)`; an empty record detaches its audio item.
- Chromium: authenticated browser fetch → Blob/validated bytes → object URL → HTMLAudioElement.
  Replay reuses the URL. Replacement and reset detach before revocation; cancelled downloads
  cannot install media after recording, navigation or logout. At most 12 recently used protected
  player sources stay cached across mounted conversation cards; older sources refetch on replay.
  This cap bounds retained browser media during long conversations.

Browser `play()` Promise rejection is observed. A `NotAllowedError` leaves **Play response**
available and does not mark TTS failed or show “audio unavailable.” Manual replay calls play
within the click handler when the source is cached. Actual decoding/download failures retain
completed transcript, chart and assistant text. No bearer token enters media URLs or logs.

All players keep the iOS session active across pause. `useAudioCapture` stops pending/current
playback and blocks new playback before preparing the recorder; stop, interruption, or unmount
releases that block. Both primary modes use temporary cache recordings. Background recording and
playback remain disabled. SecureStore holds the native auth token; provider keys never enter the
bundle. Web local storage remains development-only.

Raw acoustic warmup overlaps perception on the server. Perception runs beside known-target analysis. Free-speech timing and contour analysis begins after
perception and runs beside contextual interpretation. The server fans
out target assessment, acoustics, and alignment, then persists their exact lineage. Conversation
meaning arrives as a server NDJSON event before generation completes; one heard-text component
remains mounted through the committed reply. Optional analysis and voice do not gate recording.

Development logs separate server compute, branch wall time, upload, perception, TTS, cache,
local load-to-play request, and totals from Stop to heard/chart/meaning/text/native-playing status.
Native playing is an audible-response proxy, not a measurement of speaker output. These metrics
are not UI text. See the [current analysis report](../../docs/development/perceived-speech-analysis.md).

The [latest timing/pitch report](../../docs/development/perception-alignment-pitch-2026-09-18.md)
supersedes the earlier live-aligner limitation. Readings load while alignment runs; Expected here
uses surface tones and Mine uses measured acoustic shapes. More detail retains dictionary tones
and quality-gate reasons. Non-Han perception remains visible in a compact unavailable state.

## Generated API types and checks

`src/api/openapi.generated.ts` is generated from the checked-in FastAPI schema. Regenerate both
contract files at the repository root with `make openapi`.

```bash
make mobile-check
```

This runs lint, the strict TypeScript compiler, native/web Jest tests, and both web and Android Expo
exports. Physical microphone, audio-route, and Bluetooth validation remains manual.

## Supported milestone platforms

| Feature | iOS / Android (Expo) | Chromium desktop |
| --- | --- | --- |
| Development auth / refresh / logout | Supported | Supported |
| Recording / upload | Supported | Supported; localhost or HTTPS microphone access |
| Conversation / early transcript / concurrent analysis | Supported | Supported |
| Tone chart / selectable text | Supported | Supported; bounded desktop layout and narrow viewport |
| Learner replay | Supported | Supported, including WebM/Opus |
| Assistant speech | Supported | Supported; manual play remains available if autoplay is blocked |
| Reference speech | Supported | Supported |
| Free Practice / target Practice | Supported | Supported |

“Supported” describes implementation, not physical-device certification. Chromium 153 was
exercised with a fake microphone and unpaid fixture providers against the real API. Browser
play promises resolved; physical microphone quality and audible speaker output were not measured.
iPhone/Android device validation remains manual. Safari/Firefox are not validated for this
milestone; codec, permission and autoplay differences may require follow-up.

Web auth uses development-only localStorage, while native uses SecureStore. Product routes wait
for auth restoration. Cleanup failures cannot block token installation; unavailable storage
shows a recoverable sign-in error. Static web hosting must serve `index.html` for route URLs.

See [the full audit and validation report](../../docs/testing/web-compatibility.md) for the
browser smoke commands, exact limits, remaining checks, and dependency audit.
