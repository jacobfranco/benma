# Benma mobile

The Expo/React Native client implements two foreground-only speech workflows: unknown-target
perception and known-target pronunciation. It uses strict TypeScript, Expo Router, current
`expo-audio`, and Expo SecureStore on native platforms.

## Run on a phone

```bash
make mobile-sync
EXPO_PUBLIC_BENMA_API_URL=http://YOUR_LAN_IP:8000 make mobile-dev
```

The API URL is public application configuration, not a secret. Never place speech-provider keys
in an `EXPO_PUBLIC_` variable or the mobile bundle. Android cleartext LAN access may require a
development build/network configuration if Expo Go policy changes; production should use HTTPS.

## Screens

- Home: development authentication, sign-out, and links to the two real workflows and history.
- What did I say?: record, stop, replay, upload, run target-free perception, retry analysis on the
  same utterance, and append an optional correction while preserving the transcript.
- Pronunciation: create a target, show provisional pinyin, record/upload, create an attempt, append
  assessments, show only supported evidence, replay attempts, and record unlimited new attempts.
- History / Development: reload the account's recent persisted utterances and stream their original
  audio through authenticated requests after an app restart.

The advanced panels keep IDs, provider metadata, status, latency, and normalized evidence out of
the default learner presentation. Synthetic providers add a prominent development-fixture banner.

## Audio and session boundaries

Recorder lifecycle and permission/interruption state live in `useAudioCapture`, not screens.
Recording uses complete files in the app document directory. Background playback and background
recording are both disabled in app configuration and runtime audio mode. Streaming PCM, phone-call
mode, background sessions, and target TTS are deferred.

The native bearer token is stored in SecureStore, never AsyncStorage. Web development uses browser
local storage because SecureStore is native-only; web is not a production auth target for this pass.

## Generated API types and checks

`src/api/openapi.generated.ts` is generated from the checked-in FastAPI schema. Regenerate both
contract files at the repository root with `make openapi`.

```bash
make mobile-check
```

This runs lint, the strict TypeScript compiler, Jest state/client/auth tests, and an Android Expo
export. Physical microphone, audio-route, and Bluetooth validation remains manual.
