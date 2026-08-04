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
- [ ] 12. Open Pronunciation, enter `生活`, and confirm `shēng huó` is secondary to the characters.
- [ ] 13. Record and upload a pronunciation attempt.
- [ ] 14. Run assessment; confirm only supported scores/syllables/phones/tones appear.
- [ ] 15. Replay the attempt, record a second one, and replay both from session-local history.
- [ ] 16. Kill and restart the app; confirm native auth restoration and server-backed audio history.
- [ ] 17. Sign out; confirm the revoked token cannot reload history.
- [ ] 18. Disconnect the network during upload and confirm a useful failure state.
- [ ] 19. Restore the network and retry without app corruption; when upload had completed, retry
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

## Evidence inspection

Use the advanced panel and API/database only in development. Confirm account/utterance/run IDs,
duration, provider/product, adapter version, latency, status, and normalized evidence correspond.
Do not paste raw provider payloads containing user speech into bug reports without appropriate
handling, and never capture bearer tokens or provider credentials.
