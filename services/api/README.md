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
- `BENMA_ASSESSMENT_PROVIDER`: `disabled`, `replay`, or `azure`.

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
POST   /v1/practice-sessions
GET    /v1/practice-sessions/{id}
POST   /v1/utterances
GET    /v1/utterances
GET    /v1/utterances/{id}
GET    /v1/utterances/{id}/audio
POST   /v1/utterances/{id}/perceptions
GET    /v1/perceptions/{id}
POST   /v1/utterances/{id}/corrections
POST   /v1/pronunciation-targets
GET    /v1/pronunciation-targets/{id}
POST   /v1/pronunciation-attempts
GET    /v1/pronunciation-attempts/{id}
POST   /v1/pronunciation-attempts/{id}/assessments
```

There are no generic PATCH or DELETE routes for evidence.

## Providers

| Adapter | Implementation | Fixture-tested | Live-tested in this repository | Runtime requirement |
|---|---:|---:|---:|---|
| Replay perception | Yes | Yes | Not applicable | Explicit `replay` selection |
| OpenAI transcription | Yes | Transport contract | No | API key; no prompt is sent |
| Replay pronunciation | Yes | Yes | Not applicable | Explicit `replay` selection |
| Azure pronunciation | Yes | Transport/normalization contract | No | Speech key and region |
| Disabled ports | Yes | Yes | Not applicable | Explicit `disabled` selection |

Replay is development evidence and always returns `synthetic_replay`. OpenAI log probabilities,
when present, are retained as provider-native uncertainty rather than converted to confidence.
Azure evidence explicitly declares tone detection and surface-tone interpretation unsupported.

## Quality and schema

```bash
make api-check
make openapi
```

Tests use isolated SQLite where useful; CI additionally boots PostgreSQL 17, applies the Alembic
migration from empty, and runs `alembic check`. OpenAPI JSON and generated mobile DTOs are checked
in so contract drift fails CI.
