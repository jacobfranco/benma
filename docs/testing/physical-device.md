# Physical-device speech test plan

Record device model, OS version, app build, API commit, selected providers, network, and audio route
with each run. Replay is acceptable for pipeline testing only when the fixture banner is visible.

## Primary acceptance run

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
