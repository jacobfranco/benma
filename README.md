# Benma

Benma is a Mandarin speech-learning project built around one permanent distinction:
what a speaker produced is evidence; what they intended is later interpretation. The repository
now contains three deliberately separate applications:

```text
benchmark/       reproducible speech-provider research laboratory
services/api/    production modular-monolith API and persistence
apps/mobile/     Expo mobile client for the first speech workflows
```

The production API does not import benchmark domain models. Both layers preserve the same
truth rules, especially the prohibition on feeding targets, corrections, prompts, or conversation
context into unknown-target perception.

## Local vertical slice

Prerequisites are Python 3.12, `uv`, Node 22, Docker, FFmpeg/FFprobe, and an iOS or Android
device/simulator. Copy `services/api/.env.example` to `services/api/.env`; its explicit replay
providers produce synthetic development evidence and require no vendor credentials.

Terminal 1 — PostgreSQL and schema:

```bash
make api-db-up
make api-sync
make api-migrate
```

Terminal 2 — API:

```bash
make api-dev
```

Terminal 3 — mobile:

```bash
make mobile-sync
EXPO_PUBLIC_BENMA_API_URL=http://YOUR_LAN_IP:8000 make mobile-dev
```

Use development authentication in the app with a real-looking test number such as
`+12025550123`. The API normalizes it to E.164, returns an opaque token once, and persists only
the token hash. `make api-seed` optionally creates that account plus three target records; it
does not create evidence rows.

## What works

- **Conversation:** record Mandarin, immediately see immutable heard text, then distinct inferred
  meaning when applicable, a transcript-conditioned pitch/tone chart, and a persisted reply. Text returns before
  optional DragonHDFlash speech is requested and autoplays. Voice failure never erases text.
- **Practice:** speak freely with a pitch/tone chart and no assistant reply, or prepare a known target and reference voice
  for the existing pronunciation assessment/acoustic/alignment pipeline. Both states share the
  Conversation recording/upload/perception foundation and selectable speech evidence UI.
- The internal perception and pronunciation laboratory routes retain correction, pinyin revision,
  detailed diagnostics, attempt history, and A/B comparison. They are no longer primary modes.
- Calibration: capture a paired development pilot, export a selected attempt only through an
  explicit confirmation-gated command, run a tokenized browser annotator with immutable blind and
  revealed stages, compare identical audio across implemented Mandarin providers, persist a held-
  out split, and generate a real-only FAR/FRR/readiness report. The current report is correctly
  blocked at 0/50 real recordings and zero live providers.
- Authenticated history survives app restart because the bearer token uses SecureStore on native
  platforms and recordings remain server-owned behind authorized streaming.
- Replay evidence is prominently labeled `synthetic_replay`; live provider failures never fall
  back to replay.

Conversation remains turn-based, with progressive heard text, server interpretation, and committed
reply text. It does not stream microphone audio or perform free-speech pronunciation grading.
The project does not claim human-calibrated correctness, intelligibility,
or tone grading. Free speech never receives a target-relative accuracy score.

See the [Conversation/Practice milestone report](docs/development/conversation-practice.md)
for measured provider latency, checks, remaining physical validation, and changed files.
The [runtime follow-up report](docs/development/speech-concurrency-playback.md) covers independent
feedback, concurrent processing, local iOS playback, and the next physical acceptance run.

## Validation

```bash
make benchmark-check
make api-check
make mobile-check
make secret-scan
```

The API exports both the canonical OpenAPI snapshot and generated mobile DTOs with `make openapi`.
CI regenerates both and rejects drift. The benchmark, API, and mobile app have independent CI jobs;
no live provider credentials are used.

## Documentation

- [Development guide](docs/development.md)
- [Production foundation decision](docs/adr/0002-production-foundation.md)
- [Speech truth invariants](docs/architecture/speech-truth-invariants.md)
- [Physical-device test plan](docs/testing/physical-device.md)
- [Pass 4 manual action kit](docs/calibration/manual-action-kit.md)
- [Speech-provider calibration decision](docs/adr/0004-speech-provider-calibration-and-truth-gates.md)
- [Benchmark guide](docs/benchmark/running.md)
- [API guide](services/api/README.md)
- [Mobile and Chromium guide](apps/mobile/README.md)
- [Cross-platform audit and validation](docs/testing/web-compatibility.md)

Provider selection remains provisional. The checked-in benchmark and development replay results
are fixtures, not vendor-selection evidence.

See [perceived text, alignment references, and intended targets](docs/development/perceived-speech-analysis.md)
for the current analysis contract and physical acceptance checklist.

The [checkpoint acceptance record](docs/testing/pronunciation-manual-acceptance.md#checkpoint-acceptance--2026-09-18)
documents completed real-human Chromium testing, deliberately conservative Mine/Unclear feedback,
and deferred calibration, UX polish, physical latency and iPhone acceptance.
