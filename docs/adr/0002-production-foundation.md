# ADR 0002: Production foundation preserves speech evidence boundaries

- Status: Accepted
- Date: 2026-08-03

## Context

Pass 1 created domain models optimized for controlled corpus experiments: benchmark sample IDs,
local recording paths, blinded annotations, and provider-run comparisons. A user-facing product
instead needs ownership, sessions, durable object storage, immutable utterances, retries, and
authentication. Reusing benchmark models would leak laboratory assumptions into product speech.

The first production slice also needs to expose imperfect vendor evidence without allowing an
intended target or later correction to rewrite what an unknown-target system heard.

## Decision

1. `benchmark/`, `services/api/`, and `apps/mobile/` remain independently runnable layers.
   Production code does not import benchmark domain models. Semantic invariants are shared through
   tests and documentation, not database or class reuse.
2. The backend is a modular monolith. Auth, audio, perception, pronunciation, storage, and database
   modules are internal boundaries in one FastAPI deployment and one PostgreSQL schema. A
   seconds-long provider call remains request-response; no queue or distributed service is added.
3. Every recording retains original user bytes and a separate canonical 16 kHz mono PCM16 WAV.
   The original is committed before conversion so transformation failure cannot erase source
   evidence. Product models store object keys, never host paths.
4. Unknown-target perception and known-target assessment use unrelated input types and ports.
   Unknown input cannot represent a target, prompt, pinyin, correction, history, or context. Its
   service repository can load only owned canonical audio and append a run.
5. `PerceptionRun`, `AssessmentRun`, `AcousticRun`, and `UserCorrection` are append-only in ordinary
   domain sessions. Retries create new rows. Assessments retain a target snapshot. Corrections add
   intended text without modifying a transcript.
6. Provider choice is an explicit typed setting and a closed registry. Broken live configuration
   fails; it cannot fall back to replay. No provider is treated as permanent.
7. Replay adapters exist only for credential-free development and tests. Their normalized evidence
   is always marked `synthetic_replay`, and mobile screens render that status prominently.

## Consequences

The schema has more entities than an all-in-one speech request, but ownership, provenance, failure,
and retries remain explicit. A provider can be replaced without changing utterance identity or old
evidence. Product recordings cannot automatically become benchmark data. This pass deliberately
does not add conversation inference, calibrated learner judgments, surface-tone interpretation,
TTS selection, queues, or microservices.

Future work must preserve the separate input contracts and append-only evidence history even if it
adds contextual conversation or richer pronunciation interpretation.
