# Benma production API

This FastAPI application is a PostgreSQL-oriented modular monolith. It owns accounts, opaque
sessions, audio ingest, utterances, targets, speech-provider orchestration, and append-only
evidence. It is intentionally independent of the root benchmark package.

## Run

From the repository root:

```bash
cp services/api/.env.example services/api/.env
make api-db-up
make api-sync
make api-migrate
make api-dev
```

The server listens on `0.0.0.0:8000`; health is available at `GET /health`, and interactive
OpenAPI documentation is at `/docs` in development. FFmpeg and FFprobe must be installed.

## Configuration

Settings use the `BENMA_` prefix and fail on invalid values. Important controls are:

- `BENMA_ENVIRONMENT`: `development`, `test`, or `production`.
- `BENMA_DATABASE_URL`: SQLAlchemy PostgreSQL URL outside isolated tests.
- `BENMA_AUDIO_STORAGE_DIR`: root for generated object keys, never exposed as an API path.
- `BENMA_DEV_AUTH_ENABLED`: development-only phone login switch.
- `BENMA_MAX_UPLOAD_BYTES` and `BENMA_MAX_AUDIO_DURATION_SECONDS`: ingest limits.
- `BENMA_PERCEPTION_PROVIDER`: `disabled`, `replay`, or `openai`.
- `BENMA_ASSESSMENT_PROVIDER`: `disabled`, `replay`, `azure`, `tencent_sentence`,
  `tencent_pinyin`, or `iflytek`.
- `BENMA_REFERENCE_SPEECH_PROVIDER`: `disabled`, `replay`, or `azure`.
- `BENMA_ACOUSTIC_PROVIDER`: dependency-free `autocorrelation` or `disabled`.
- `BENMA_ALIGNMENT_PROVIDER`: `disabled`, development `replay`, or optional `mfa`.
- `BENMA_CONTEXTUAL_INTERPRETATION_PROVIDER`: `disabled` or `openai`.
- `BENMA_OPENAI_CONTEXTUAL_INTERPRETATION_MODEL`,
  `BENMA_OPENAI_CONTEXTUAL_INTERPRETATION_REASONING_EFFORT`, and
  `BENMA_CONTEXTUAL_INTERPRETATION_TIMEOUT_SECONDS`: live interpreter controls.
- `BENMA_CONTEXTUAL_INTERPRETATION_VERSION`: persisted interpreter-policy metadata.
- `BENMA_ASSISTANT_GENERATION_PROVIDER`: `disabled` or `openai`.
- `BENMA_OPENAI_ASSISTANT_GENERATION_MODEL`,
  `BENMA_OPENAI_ASSISTANT_GENERATION_REASONING_EFFORT`, and
  `BENMA_ASSISTANT_GENERATION_TIMEOUT_SECONDS`: live response-generation controls.
- `BENMA_ASSISTANT_GENERATION_POLICY_VERSION`: persisted generation-policy metadata.
- `BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION`: factual evidence agreement language.
- `BENMA_ENABLE_CATEGORICAL_TONE_JUDGMENT`: intentionally rejected until calibrated.

The application refuses production startup with development auth enabled and refuses configured
live providers without their required credentials. It never silently selects replay.

## Audio lifecycle

`POST /v1/utterances` validates MIME, size, corruption, and duration. It generates an opaque
storage key, persists the original bytes and their SHA-256 first, then creates a distinct 16 kHz,
mono, PCM16 WAV derivative. If canonicalization fails, the original database row and object remain
for recovery; no utterance is created until both assets are valid.

Authenticated playback resolves a storage key only after account ownership is verified. Absolute
filesystem paths, user filenames, signed provider URLs, and provider credentials never enter the
public contract.

## Resource API

```text
GET    /health
POST   /v1/dev/auth
GET    /v1/me
DELETE /v1/auth/session
POST   /v1/conversations
GET    /v1/conversations/{id}
GET    /v1/conversations/{id}/turns
POST   /v1/conversations/{id}/user-turns
GET    /v1/assistant-generations/{id}
POST   /v1/practice-sessions
GET    /v1/practice-sessions/{id}
POST   /v1/utterances
GET    /v1/utterances
GET    /v1/utterances/{id}
GET    /v1/utterances/{id}/audio
POST   /v1/utterances/{id}/perceptions
GET    /v1/perceptions/{id}
POST   /v1/perceptions/{id}/contextual-interpretations
GET    /v1/contextual-interpretations/{id}
POST   /v1/utterances/{id}/corrections
POST   /v1/pronunciation-targets
POST   /v1/pronunciation-targets/{id}/pinyin-corrections
POST   /v1/pronunciation-targets/{id}/reference-speech
GET    /v1/reference-speech/{id}/audio
GET    /v1/pronunciation-targets/{id}
POST   /v1/pronunciation-attempts
GET    /v1/pronunciation-attempts/{id}
POST   /v1/pronunciation-attempts/{id}/assessments
POST   /v1/pronunciation-attempts/{id}/analyze
GET    /v1/pronunciation-attempts/{id}/result
GET    /v1/pronunciation-targets/{id}/attempts
POST   /v1/pronunciation-attempts/compare
```

There are no generic PATCH or DELETE routes for evidence.

Clarification generation receives an explicit `clarification_alternatives` allowlist derived only
from persisted contextual-interpretation alternatives. Structured provider output must declare
every candidate phrase it uses, and Benma rejects non-allowlisted declarations and undeclared
quotation-delimited phrases. This deliberately catches obvious candidate injection; it cannot
prove that arbitrary unquoted natural language contains no implicit candidate phrase, so the
provider prompt also requires an open question whenever the allowlist is empty.

## Providers

| Adapter | Implementation | Fixture-tested | Live-tested in this repository | Runtime requirement |
|---|---:|---:|---:|---|
| Replay perception | Yes | Yes | Not applicable | Explicit `replay` selection |
| OpenAI transcription | Yes | Transport contract | No | API key; no prompt is sent |
| Replay pronunciation | Yes | Yes | Not applicable | Explicit `replay` selection |
| Azure pronunciation | Yes | Transport/normalization contract | No | Speech key and region |
| Tencent SOE-N sentence/pinyin | Yes | Auth/mode/normalization contracts | No | SOE-N AppID, SecretId, SecretKey |
| iFlytek streaming ISE | Yes | Auth/full-dimension/XML contracts | No | AppID, APIKey, APISecret |
| Replay reference | Yes | Yes | Not applicable | Explicit synthetic selection |
| Azure reference | Yes | Transport/cache contract | No | Speech key and region |
| OpenAI contextual interpretation | Yes | Strict-schema transport contract | Optional smoke command | API key |
| OpenAI assistant generation | Yes | Strict-schema transport contract | Optional smoke command | API key |
| Autocorrelation acoustics | Yes | Synthetic signals + API | Local | No optional runtime |
| MFA alignment | Experimental | Parser/sanity fixtures | No | MFA 3.x models and CLI |
| Disabled ports | Yes | Yes | Not applicable | Explicit `disabled` selection |

Replay is development evidence and always returns `synthetic_replay`. OpenAI log probabilities,
when present, are retained as provider-native uncertainty rather than converted to confidence.
Azure evidence explicitly declares tone detection and surface-tone interpretation unsupported.

Developer research tools include `reference_listening_corpus.py`,
`pronunciation_diagnostic.py`, `provider_bakeoff.py`, `replay_interpreter.py`, the generic
`contextual_interpretation_smoke.py`, `assistant_generation_smoke.py`, and the confirmation-gated
`export_pronunciation_attempt.py`. They never run automatically.

The contextual smoke command accepts representative downstream inputs and prints only normalized
decision evidence and non-secret interpreter metadata; it does not save provider captures:

```bash
cd services/api
uv run python scripts/contextual_interpretation_smoke.py \
  --perceived '我想卖水果。' \
  --context-json '{"situation":"discussing buying fruit at a supermarket"}'
```

Use `scripts/provider_smoke.py` to test a live known-target provider without the mobile app. It
validates canonical WAV metadata, refuses missing credentials, prints normalized evidence and
provenance, and can optionally persist a sanitized live capture:

```bash
cd services/api
uv run python scripts/provider_smoke.py tencent_sentence \
  --sample ../../benchmark/recordings/example.wav --target 生活 --pinyin sheng1 huo2
```

Documentation examples are never labeled as live captures.

The assistant-generation smoke command exercises the infer, clarify, and preserve Free Talk
generation contracts without persisting captures or adding phrase-specific production logic:

```bash
cd services/api
uv run python scripts/assistant_generation_smoke.py
```

`provider_bakeoff.py` invokes all four implemented configurations against identical canonical
bytes and writes an audio-hash manifest. `replay_interpreter.py --output PATH` compares the current
version/configuration against stored interpretation observations over the same immutable evidence
IDs and assessment raw hash. Neither tool mutates evidence or silently retries billable calls.

## Quality and schema

```bash
make api-check
make openapi
```

Tests use isolated SQLite where useful; CI additionally boots PostgreSQL 17, applies the Alembic
migration from empty, and runs `alembic check`. OpenAPI JSON and generated mobile DTOs are checked
in so contract drift fails CI.
