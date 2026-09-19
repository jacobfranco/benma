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
- `BENMA_ACOUSTIC_PROVIDER`: `praat` (default), dependency-free `autocorrelation`, or `disabled`.
- `BENMA_ALIGNMENT_PROVIDER`: `auto` (default), `azure`, `mfa`, `replay`, or `disabled`.
  Auto uses Azure only with `BENMA_AZURE_ALIGNMENT_ENABLED=true` and configured credentials;
  explicit `azure` also opts in. Disabled never requests Azure timing. The current local `.env`
  opts into Azure timing; `.env.example` keeps paid timing off until explicitly enabled.
- `BENMA_ALIGNMENT_TIMEOUT_SECONDS`: 12 by default. Azure short-audio timing supports up to 30s;
  longer recordings retain text and pitch with timing unavailable.
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
- `BENMA_ASSISTANT_SPEECH_PROVIDER`: `disabled` or `azure`.
- `BENMA_ASSISTANT_SPEECH_VOICE`, `BENMA_ASSISTANT_SPEECH_LOCALE`,
  `BENMA_ASSISTANT_SPEECH_MODEL_VERSION`, `BENMA_ASSISTANT_SPEECH_RATE`, and
  `BENMA_ASSISTANT_SPEECH_TIMEOUT_SECONDS`: conversational Mandarin rendering controls, persisted
  independently from pronunciation reference configuration.
- `BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION`: factual evidence agreement language.
- `BENMA_ENABLE_CATEGORICAL_TONE_JUDGMENT`: intentionally rejected until calibrated.

The application refuses production startup with development auth enabled and refuses configured
live providers without their required credentials. It never silently selects replay.

## Development web CORS

In `development`, browser requests are allowed from `http://localhost:8081` and
`http://127.0.0.1:8081`. Add other exact frontend origins through a JSON array in the API's
`services/api/.env`, then restart the API. For example, for the current Expo LAN address:

```dotenv
BENMA_CORS_ALLOWED_ORIGINS=["http://192.168.68.59:8081"]
```

Use the origin of the **Expo page in the browser**, including its port, rather than the API URL.
This LAN address is an example, not a built-in allowlist entry. HTTPS origins are also supported.
Paths, query strings, fragments, embedded credentials, and wildcard origins are rejected.
Host names and default ports are normalized; a trailing root slash is optional.

`test` and `production` have no implicit origins: only `BENMA_CORS_ALLOWED_ORIGINS` entries apply.
Keep it empty in production unless cross-origin browser access is intended. The middleware permits
GET, POST, and DELETE, handles OPTIONS preflight without authentication, and allows Authorization
and Content-Type plus the browser's standard safelisted headers. Only development exposes the
existing Server-Timing response header. Cookie credentials and wildcard matching remain disabled.

CORS does not grant API access: protected routes still require a valid bearer token, and development
auth remains unavailable in production. Requests without an Origin header (including native/API
clients) continue through the existing routes unchanged.

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
POST   /v1/conversations/{id}/user-turns/stream
GET    /v1/assistant-generations/{id}
POST   /v1/assistant-generations/{id}/speech
GET    /v1/assistant-speeches/{id}
GET    /v1/assistant-speeches/{id}/audio
POST   /v1/practice-sessions
GET    /v1/practice-sessions/{id}
POST   /v1/utterances
GET    /v1/utterances
GET    /v1/utterances/{id}
GET    /v1/utterances/{id}/audio
POST   /v1/utterances/{id}/perceptions
POST   /v1/utterances/{id}/acoustics
POST   /v1/perceptions/{id}/speech-analysis
GET    /v1/perceived-speech-analyses/{id}
GET    /v1/perceptions/{id}/readings
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

The Conversation user-turn response includes immutable `perceived_text`, the explicit
`interpretation_decision`, downstream `resolved_text`, and the persisted `assistant_turn`.
It returns text without invoking TTS or constructing a speech provider. The client then POSTs `{}`
to `/v1/assistant-generations/{id}/speech`; the server loads its exact persisted text. Every speech
attempt appends evidence, including failures. Listing turns exposes the latest attempt. The client
can keep talking after voice failure and can request another speech attempt without providing text.
Development responses expose numeric interpretation/generation timings in `Server-Timing`;
production responses omit this development header.

The `/user-turns/stream` variant emits typed NDJSON interpretation progress and the committed
reply through the same service transaction; it does not combine the two model calls. Progress is
provisional until persistence succeeds, and response failures reconcile from durable turns.
`POST /perceptions/{id}/speech-analysis` receives only `{}`. It uses the exact persisted perceived
transcript as an alignment reference, independently of meaning/generation. It appends a
`PerceivedSpeechAnalysis` tied to the audio and `AcousticRun`, never a `PronunciationTarget`.
Structured pitch, separate lexical/surface-tone expectations, readings, timing, and availability markers feed the shared
mobile chart. Unavailable alignment or uncertain readings do not suppress measured pitch.
See [semantics, provenance, and limitations](../../docs/development/perceived-speech-analysis.md).

The [2026-09-18 evidence report](../../docs/development/perception-alignment-pitch-2026-09-18.md)
documents the fixed server-owned Mandarin transcription profile, exact-text Azure offsets,
Praat quality gates, and real 你好 results. Raw acoustics start alongside ASR; PostgreSQL locks
make warmup and foreground requests reuse the same versioned acoustic evidence. Readings can
load before alignment, and neither optional branch blocks the assistant response.

Read-only development diagnostics (latest utterance, or supply `--utterance-id UUID`):

```sh
uv run python -m benma_api.pronunciation.diagnostic
```

This command makes no provider requests. It prints only the local transcript, readings,
lexical/surface tones, real spans, quality metrics, Mine labels and recorded stage latencies.
Optional analysis has a separate bounded worker budget from upload/perception/TTS. Known-target
analysis prepares owned inputs on one database session, computes provider/acoustic/alignment
branches concurrently, then persists exact evidence IDs on that same session. PostgreSQL
`FOR NO KEY UPDATE` serializes utterance analysis reuse without blocking perception FK inserts.
See the [implemented DAG and validation report](../../docs/development/speech-concurrency-playback.md).

Conversational speech defaults to `zh-CN-Xiaochen:DragonHDFlashLatestNeural`, configurable through
`BENMA_ASSISTANT_SPEECH_VOICE` and `BENMA_ASSISTANT_SPEECH_MODEL_VERSION`. Pronunciation reference
speech retains its separate DragonHD default. OpenAI model/effort defaults remain unchanged after
the small [latency evaluation](../../docs/development/conversation-practice.md).

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
| Azure assistant speech | Yes | Transport/persistence contract | Optional smoke command | Speech key and region |
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

The assistant-speech smoke command renders the fixed Mandarin validation corpus through Azure,
persists each result in a temporary database/object store, validates playable WAV structure, and
prints only non-secret metadata and hashes. Temporary audio is removed on exit:

```bash
cd services/api
uv run python scripts/assistant_speech_smoke.py
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
