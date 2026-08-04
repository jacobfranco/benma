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

- Unknown target: record, replay, persist original and canonical audio, run perception, preserve
  what the provider heard, and append an optional user correction without rewriting the run.
- Known target: enter Chinese text, retain generated pinyin provenance and lexical tones, record
  unlimited attempts, revise polyphonic readings without overwriting the generated target, replay
  reference speech, preserve assessment/acoustic/alignment evidence separately, inspect relative
  pitch and surface-tone expectations, and replay/compare durable attempts.
- Calibration: capture a paired development pilot, export a selected attempt only through an
  explicit confirmation-gated command, run a tokenized browser annotator with immutable blind and
  revealed stages, compare identical audio across implemented Mandarin providers, persist a held-
  out split, and generate a real-only FAR/FRR/readiness report. The current report is correctly
  blocked at 0/50 real recordings and zero live providers.
- Authenticated history survives app restart because the bearer token uses SecureStore on native
  platforms and recordings remain server-owned behind authorized streaming.
- Replay evidence is prominently labeled `synthetic_replay`; live provider failures never fall
  back to replay.

This is not conversation mode and it does not claim human-calibrated correctness, intelligibility,
or tone grading.

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
- [Mobile guide](apps/mobile/README.md)

Provider selection remains provisional. The checked-in benchmark and development replay results
are fixtures, not vendor-selection evidence.
