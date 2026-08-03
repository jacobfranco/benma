# Running and reproducing the benchmark

## Environment

Python 3.11+ and FFmpeg are required. The core/replay harness intentionally avoids heavy acoustic
dependencies.

```bash
uv sync --extra dev
uv run python -m benchmark validate-corpus
```

Optional scientific comparisons:

```bash
uv sync --extra dev --extra acoustics
```

Torch is large; install the correct CPU/CUDA build for the host before using torchcrepe. Install
Montreal Forced Aligner in its recommended isolated Conda environment, then download current
Mandarin models:

```bash
mfa model download acoustic mandarin_mfa
mfa model download dictionary mandarin_mfa
```

Record `mfa version` and exact model version in run metadata. The code does not download models or
audio automatically.

## Corpus

The checked-in manifest is data, generated once from reviewable seed tables:

```bash
uv run python -m benchmark init-corpus
uv run python -m benchmark validate-corpus
```

To import an existing recording while preserving source bytes:

```bash
uv run python -m benchmark import-audio SAMPLE_ID /path/to/source.m4a
```

To capture locally through FFmpeg (Linux PulseAudio defaults shown):

```bash
uv run python -m benchmark record SAMPLE_ID \
  --input-format pulse --input-device default --duration 5
```

macOS commonly uses `avfoundation`; Windows uses `dshow`. List FFmpeg devices on the host and pass
an explicit input device. The utility shows target/error condition, captures, plays back, allows
retry, preserves original, creates canonical mono 16 kHz PCM16, hashes it, and updates the manifest.

## Human annotation

Generate a seeded randomized sample order outside the target-visible view, then run:

```bash
uv run python -m benchmark annotate-blind SAMPLE_ID ANN_ID LISTENER_ID --order 17
uv run python -m benchmark annotate-reveal SAMPLE_ID ANN_ID
```

The second command refuses to run before the hashed blind commit exists.

## Credential-free reproducibility

```bash
uv run python -m benchmark run-fixtures
uv run python -m benchmark report --fixtures
```

Outputs:

- `benchmark/reports/outputs/comparative.json`
- `benchmark/reports/outputs/runs.csv`
- `benchmark/reports/outputs/cost-scenarios.json`
- `benchmark/reports/outputs/report.md`

All say `replay_fixture_only`. Fixture values are designed to exercise semantic repair, provider
differences, tone false acceptance, unavailable tone fields, and disagreement—not to simulate
actual provider quality.

## Live smoke tests

After exporting variables from [provider setup](providers.md) and recording a sample:

```bash
uv run python -m benchmark smoke-live openai SAMPLE_ID
uv run python -m benchmark smoke-live google SAMPLE_ID
uv run python -m benchmark smoke-live azure SAMPLE_ID
uv run python -m benchmark report
```

A failed live request is persisted as a failed `ProviderRun` with sanitized configuration; secrets
are never included. Before bulk cost, manually inspect the first raw response and normalized result.

## Acoustic and alignment experiments

```bash
uv run python -m benchmark acoustics canonical.wav \
  --output-json result.json --output-svg plot.svg

uv run python -m benchmark acoustics canonical.wav --algorithm parselmouth \
  --output-json praat.json --output-svg praat.svg

uv run python -m benchmark align canonical.wav '你好' --output alignment.json
```

Inspect every pilot alignment against waveform/audio. A timestamp is not proof of a correct
boundary. Keep bad alignments and warnings in the failure gallery.

## Final validation

```bash
uv run pytest
uv run ruff check .
uv run mypy benchmark
uv run python -m benchmark run-fixtures
uv run python -m benchmark report --fixtures
git grep -n -E '(sk-|SecretKey|API_KEY=.+)' -- . ':!uv.lock'
```

CI requires no paid credentials. Live smoke tests are opt-in and should run only on consented
audio. A new provider should require only a new adapter and fixtures; corpus/evaluation/report code
must remain unchanged.

