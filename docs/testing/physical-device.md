# Physical-device speech test plan

Checkpoint status (2026-09-18): [real-human Chromium acceptance was performed](pronunciation-manual-acceptance.md#checkpoint-acceptance--2026-09-18).
Physical iPhone final acceptance and physical Stop → chart latency measurement remain pending
follow-ups; neither blocks this checkpoint.

Record device model, OS version, app build, API commit, selected providers, network, and audio route
with each run. Replay is acceptable for pipeline testing only when the fixture banner is visible.

## Conversation + Practice on a physical iPhone

In two zsh terminals, run the existing helpers:

```zsh
benma-api
```

```zsh
benma-mobile
```

The `benma-api` helper applies migrations automatically; local PostgreSQL is already at 0010.
Open the Expo QR link on the iPhone and sign in. The API must have live perception,
interpretation, generation, assessment, and reference providers configured as needed. Current
conversational voice defaults to `zh-CN-Xiaochen:DragonHDFlashLatestNeural`; explicit environment
voice overrides still take precedence. ReferenceSpeech keeps the existing DragonHD voice.

- [ ] Home shows **Conversation** and **Practice** as the two primary modes.
- [ ] Open Conversation and say: **你好，今天我们聊聊周末吧。**
- [ ] Recording survives until Stop. “What Benma heard” appears as soon as transcription returns,
      while “Understanding meaning…” remains visible. Long-press and copy the heard text.
- [ ] A measured tone/pitch chart and pinyin/tone strip appear for the heard text. Missing alignment
      is labeled as text order; uncertain readings remain explicit. The reply does not wait for it.
      Replay **Play mine** and **Play response**, and check automatic assistant audio.
- [ ] “What Benma understood” appears only for a distinct inferred reading; the heard text stays
      visible. Feedback compares wording without claiming a pronunciation error.
- [ ] Benma's selectable reply appears before voice is ready. “Preparing voice…” transitions to
      autoplay. Verify DragonHDFlash in development API evidence/config, then replay twice.
      The replay must issue no second HTTP audio GET. Cache logs should identify WAV, a nonzero
      verified byte size, native loaded, and local load-to-play request without a protected URL.
- [ ] Say: **我周末喜欢去公园散步。你呢？** Start while the first voice is playing once.
      Playback must stop before recording, and the reply must retain the same conversation context.
      Verify a second autoplay/replay cycle and copy the assistant text into Notes.
- [ ] Incomplete turn: say **你好，今天我……** and stop. Heard text, replay, and the pitch/tone chart
      remain available even if meaning is CLARIFY. “Meaning” may remain unresolved; the UI must
      not label the produced speech as failed. Semantic uncertainty must not suppress the chart.
      Optional analysis may finish before or after the reply; it must not hold the next recording.
- [ ] Third turn: use an ambiguous reference or an awkward sentence. For example, after discussing
      two places, say **明天我们去那里吧。** Verify a grounded clarification; no candidate is silently
      promoted to heard text. Coherent awkward grammar should remain preserved.
- [ ] Intentionally pronounce **周末** poorly enough to invite a different perception. The chart
      must use that perceived text; context may suggest **周末** separately. There is no free-speech
      target-relative score, and raw perception stays unchanged. Also exercise a plausible near miss. Context-supported near misses should infer when one
      reading dominates. The live synthetic evaluation still found the opening **周谋** case can
      clarify without prior context; record this explicitly if reproduced, rather than hiding it.
- [ ] Start a new recording while a previous reply says “Preparing voice…”. Late audio must not
      interrupt the microphone. It should remain available for manual replay afterward.
- [ ] Force speech failure once (for example temporarily set assistant speech provider to disabled
      and restart the API). Reply text remains, “Audio unavailable” appears, and another turn works.
      Restore the provider and use “Prepare voice” to append a retry from the persisted generation.
- [ ] Open Practice, leave it free, and say a phrase. Heard text, a pitch/tone chart, and **Play mine** appear.
      There is no assistant reply, invented accuracy score, or target-required message.
- [ ] Tap “Add a target phrase”, enter **你好**, and “Prepare target”. Play **Native reference**
      twice, edit pinyin if needed, and record. Verify heard text first, then the known-target
      pronunciation result, tone chart, provider target-relative accuracy where supported, and Reference/Mine controls. Alternate playback → recording → playback.
- [ ] Deny microphone permission once, double-tap Stop, interrupt upload/perception/assessment,
      and retry. Retries reuse completed upload/perception/attempt checkpoints when appropriate.
- [ ] Back out during processing; no late autoplay should begin on another screen. Sign out and
      back in; previous protected cached audio must not be reused across auth changes.
- [ ] Inspect development logs: recording duration, upload, perception, interpretation, generation,
      transcript-conditioned analysis total, alignment and pitch extraction, TTS, audio cache/download,
      local load-to-play request, total time to heard transcript, meaning, assistant text, and native
      playing. Target Practice additionally reports assessment/alignment compute and analysis wall
      time. Replay should avoid another audio GET. No bearer value/URL/header is logged.

Record **Stop → heard**, **Stop → chart**, **Stop → assistant text**, and **Stop → audible response** for each turn,
plus provider decision and any differences. The logged audible proxy ends at native playing status;
confirm actual speaker onset manually. Android export/Jest cannot validate iOS audio routing,
Expo's native multipart serializer, real text selection, or physical speech quality.

## Browser and native recording upload retest

1. Restart the API and Expo with the current tree. For a browser on this computer, use
   `EXPO_PUBLIC_BENMA_API_URL=http://127.0.0.1:8000 npm --prefix apps/mobile run web` and open
   `http://localhost:8081`. A LAN frontend origin must be in `BENMA_CORS_ALLOWED_ORIGINS`;
   microphone capture also requires a browser secure context (localhost or HTTPS).
2. Sign in with **Continue with development account**. Open browser DevTools Network and
   Console. Open **Conversation**, record 5–10 seconds, and press **Stop recording** once.
   Confirm one `POST /v1/utterances` returns 201 (preflight 200 when not cached), with a bearer
   header and browser-generated multipart boundary. Do not copy bearer values into reports.
3. Inspect the file part: a WebM recording is named `recording.webm`; an MP4 recording is named
   `recording.m4a`. Its part MIME comes from the browser Blob, possibly with codec parameters.
   Development `[recording upload]` diagnostics show platform, MIME, bytes, and conversion stage
   without the object URL. The API should retain original audio and create canonical WAV.
4. Repeat in **Practice** with no target, then with **Add a target phrase** → **Prepare target**.
   Each recording must create exactly one utterance before perception/analysis. Double-tap Stop
   once and confirm there is still only one upload. Retry a failed perception and confirm it
   reuses the existing utterance. Pause the API during upload once, restore it, and retry;
   the local recording should still be available without recording again.
5. Exercise local object-URL replay in the internal `/perception` screen: record, stop, play,
   then upload the same recording. Repeat recordings and leave the screen. Browser object URLs
   should be released as recordings/players become obsolete, without breaking an active upload.
   Server-backed protected playback is a separate path; its existing filesystem cache remains
   native-oriented and is not validated by this upload change.
6. On a physical iPhone and Android device, reload the Expo app using the API's LAN address.
   Repeat Conversation, free Practice, and target Practice. Confirm each native `.m4a` upload
   reaches the API with 201, playback → recording → upload still works, and retries do not
   duplicate completed uploads. This checks Expo's actual native multipart serializer.

Automated verification for this change used the installed Expo Audio 57 web recorder in headless
Chromium with a simulated microphone: `blob:` URI, `audio/webm`, Opus/48 kHz/mono, `recording.webm`,
18,116 original bytes received unchanged with bearer auth. Browser fallback MP4 and object-URL
lifetimes are covered by web Jest tests. A simulated microphone does not replace the physical
speech/device checks above.

## Internal legacy tool acceptance run

- [ ] 1. Launch the app on an iOS or Android physical device.
- [ ] 2. Authenticate with the development phone flow.
- [ ] 3. Grant microphone permission; verify denial and later recovery once as well.
- [ ] 4. Record an arbitrary Mandarin utterance.
- [ ] 5. Stop recording and confirm the state leaves `recording`.
- [ ] 6. Replay the local recording and confirm it is complete and audible.
- [ ] 7. Upload; confirm an utterance remains available if later analysis fails.
- [ ] 8. Run perception using the explicitly configured provider.
- [ ] 9. View “What Benma heard”; for replay, confirm the development-fixture banner.
- [ ] 10. Enter a different intended sentence as a correction.
- [ ] 11. Confirm the original transcript and correction remain visible and distinct.
- [ ] 12. Open Pronunciation, enter `生活`, confirm `shēng huó`, edit to numeric pinyin, and verify
      the correction creates a new prepared reading.
- [ ] 13. Play the native reference repeatedly, then alternate reference/mine through headphones.
- [ ] 14. Record and upload a pronunciation attempt; verify too-quiet/clipped attempts produce a
      recording warning rather than a pronunciation verdict.
- [ ] 15. Analyze and confirm supported syllable, phone, tone, pitch, and alignment evidence appears;
      missing capabilities must be explicit.
- [ ] 16. Inspect the post-utterance pitch plot for stable rendering, unvoiced gaps, syllable regions,
      and reference/user colors. No live microphone pitch should appear.
- [ ] 17. Record at least five retries; replay old attempts and select two for A/B comparison.
- [ ] 18. Kill and restart the app; confirm native auth restoration and server-backed audio history.
- [ ] 19. Sign out; confirm the revoked token cannot reload history.
- [ ] 20. Disconnect the network during reference generation, upload, and analysis; each failure
      must leave the target/attempt usable.
- [ ] 21. Restore the network and retry without app corruption; when upload had completed, retry
      analysis without rerecording and confirm a distinct evidence run.

## Additional Conversation regression checks

- [ ] Confirm the first upload reaches `POST /v1/utterances` on a physical runtime. Jest verifies
      that the client supplies Expo `File` to `FormData` and uses `expo/fetch`, but it does not run
      Expo's native multipart serializer and cannot reproduce device-only serialization failures.
- [ ] Open Conversation and confirm a new conversation becomes ready without exposing an internal ID.
- [ ] Complete three Mandarin turns, including one intentionally awkward utterance. For each turn,
      verify recording stops cleanly, processing progresses, heard text, distinct inferred meaning when applicable, and persisted
      assistant text appear, speech autoplays once, replay works, and recording is immediately
      available again.
- [ ] Long-press the heard text, inferred text, and assistant response, select text, and copy it into a
      different app. Confirm speaker labels and playback/recording controls do not become selectable.
- [ ] For the first assistant response, confirm one authenticated audio GET succeeds, then inspect the
      development logs for `audio download/cache ms` followed by `local load-to-play ms`. Replay the
      same response and confirm there is no second GET; no URL, bearer value, or headers should appear
      in the logs or cache filename.
- [ ] While assistant audio is playing, start the next recording and confirm playback stops before the
      microphone activates. Complete the turn and confirm its new response autoplays, then start a
      third recording immediately after playback.
- [ ] Confirm all three user turns use the same conversation in authenticated API/database
      inspection and that the second and third interpretation snapshots contain prior persisted
      context.
- [ ] Confirm an inferred user turn is labeled as what Benma understood, not as raw ASR evidence;
      confirm a clarification remains explicitly unresolved.
- [ ] Force assistant TTS to fail after text generation. Confirm assistant text remains visible,
      audio is marked unavailable, and the next turn can be recorded.
- [ ] Deny microphone permission, double-tap Stop, interrupt each network stage once, and trigger an
      audio playback error. Confirm denial is actionable, only one turn is submitted, and every
      failure recovers to another recording attempt.

## Audio-route smoke tests

- [ ] Record and replay through the built-in microphone/speaker.
- [ ] Connect wired headphones if supported; repeat recording and replay.
- [ ] Connect a Bluetooth headset; record, stop, replay, and inspect whether input/output routing is
      intelligible and stable.
- [ ] Disconnect headphones/Bluetooth during playback and recording; confirm the app recovers or
      asks for a fresh recording without presenting a partial file as successful.
- [ ] Background the app during recording and verify recording does not continue. This pass has no
      background recording or phone-call mode.
- [ ] Lock the device during foreground recording and during reference/self playback; document
      Android and iOS behavior rather than assuming background continuation.
- [ ] Interrupt recording/playback with another audio app or phone-call simulation and verify a
      recoverable state.

## Evidence inspection

Use the advanced panel and API/database only in development. Confirm account/utterance/run IDs,
duration, provider/product, adapter version, latency, status, and normalized evidence correspond.
Do not paste raw provider payloads containing user speech into bug reports without appropriate
handling, and never capture bearer tokens or provider credentials.

## Pass 4 provider capture

- [ ] Record one consented Mandarin attempt on the phone; replay it and confirm the saved attempt.
- [ ] Explicitly export it; verify original/canonical hashes and canonical 16 kHz mono PCM16 format.
- [ ] Run Azure, Tencent SOE-N sentence, Tencent SOE-N pinyin, and iFlytek through the same-audio
      bakeoff. Confirm every row has the identical SHA-256 and target snapshot.
- [ ] Confirm Tencent uses product 1774, never Basic 884; inspect valid and invalid tone handling.
- [ ] Confirm iFlytek requested full-dimension mode and returned or explicitly lacked its detail.
- [ ] Record provider latency/failures and check no credential/signed URL appears in output.

## Reference speech routes

- [ ] Generate and actually listen to Azure Xiaochen, Yunfan, and Xiaoxiao candidates across the
      worksheet corpus; add Tencent only if accessible.
- [ ] Repeat playback through speaker, wired headphones, and Bluetooth; record route artifacts.
- [ ] Judge naturalness, tone, T3/一/不 sandhi, neutral tone, pacing, and repetition comfort by ear.
      Do not use a provider score to choose the voice.

## Calibration and annotation

- [ ] Capture a correct/error pair for the same target and session; replay/discard/retry before save.
- [ ] Confirm the calibration screen is visibly development-only and shows no provider feedback
      before final save.
- [ ] Export only the selected attempt with explicit confirmation; verify no unrelated account data.
- [ ] Open the tokenized annotation workbench from another browser/device. Before blind commit,
      inspect the UI/network path and confirm target, requested error, sample ID, and provider output
      are absent.
- [ ] Commit Stage A, complete Stage B, restart mid-form to verify recovery, and export/import a
      bundle into a clean annotations directory.

None of these Pass 4 physical-device items was executed by Codex. Check them only after observing
the behavior on real hardware and preserve the resulting device/build/provider manifest.


## Web parity follow-up (2026-09-17)

See [the compatibility audit](web-compatibility.md) for automated Chromium results. Before the
milestone commit, use the actual desktop microphone and speakers for a two-turn Conversation,
free Practice and target Practice. Confirm reference/response/mine playback, blocked-autoplay
manual recovery, copy/paste, resize, refresh and sign-out. Use localhost or HTTPS for microphone
permission; adding a LAN CORS origin alone does not make HTTP a secure media context.

On iPhone, repeat native M4A upload, AssistantSpeech/ReferenceSpeech replacement and replay,
recording interrupting playback, interruption/background handling, silent mode/audio route,
Bluetooth, and logout cleanup. Native `replace(null)` remains prohibited by the installed iOS
bridge. Android export passes but microphone/speaker validation still requires a device.


## Pronunciation comparison follow-up — 2026-09-17

See the [learner-experience report](../development/pronunciation-learner-experience.md).
On physical iPhone, speak 你好，今天我们聊聊周末吧。 and verify immediate pronunciation skeletons,
stable reply placement, nǐ hǎo jīn tiān wǒ men liáo liáo zhōu mò ba, paired lexical/Mine shapes
when real timing exists, honest unclear labels otherwise, horizontal cell scrolling, More detail,
and Mine/reference/assistant replay. Repeat with larger accessibility fonts and interruption.
Browser 390 px validation and Android export do not replace this check. The current untimed
live setup needs a validated aligner before per-character Mine feedback can be certified.
