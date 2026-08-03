# Benma speech foundation research

This repository is currently in the **research/benchmark phase**. The benchmark exists to
determine Benma's speech foundation before the product is built. There is no mobile product,
account system, conversation engine, or production backend here.

Benma's governing rule is that raw perception evidence must describe what reached a listener,
not what context says the speaker probably meant. The code therefore has two incompatible
request types:

- `UnknownTargetPerceptionRequest`: audio, a Mandarin language hint, and timeout only.
- `KnownTargetAssessmentRequest`: audio plus explicit target text/pinyin/tone metadata.

Pydantic rejects extra fields, and tests prove target/context cannot enter the unknown-target
contract. Provider responses are stored twice: untouched raw JSON and a provider-neutral
normalized result. Later interpretation may reference evidence; it cannot rewrite it.

## Quick start

```bash
uv sync --extra dev
uv run python -m benchmark validate-corpus
uv run python -m benchmark run-fixtures
uv run python -m benchmark report --fixtures
uv run pytest
uv run ruff check .
uv run mypy benchmark
```

`report` automatically falls back to explicitly labeled replay fixtures when no live runs exist.
Replay numbers validate metrics/reporting only; they are not evidence for vendor selection.

## What exists

- Versioned schemas for corpus samples, provider runs, both evaluation modes, acoustic evidence,
  alignment, and immutable two-stage human annotations.
- A 384-utterance target design with a materialized pilot manifest covering all tone pairs,
  required lexical examples, sandhi, English-speaker segmental contrasts, exact-one-error
  sentences, context probes, and controls.
- Original-preserving recording/import and canonical mono 16 kHz PCM16 generation.
- Live adapter boundaries for OpenAI Transcription, Google Chirp 3, Azure Pronunciation
  Assessment, and local FunASR/Whisper commands; replay boundaries cover unavailable services.
- Independent autocorrelation F0, optional torchcrepe and Praat/Parselmouth comparisons,
  speaker-relative normalization, static SVG diagnostics, and an MFA experiment boundary.
- Exact metrics, latency/cost modeling, scorecards, failure galleries, and deterministic reports.

Start with [running the benchmark](docs/benchmark/running.md), then read the
[technology landscape](docs/research/technology-landscape.md) and the provisional
[architecture decision](docs/adr/0001-speech-foundation.md).

## Status

No provider has won. The checked-in output is based only on synthetic replay fixtures. Real
selection requires recorded learner/native audio and blind native-listener annotations.

