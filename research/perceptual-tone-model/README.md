# Perceptual tone ML feasibility infrastructure

**Active research track (2026-10-17): AISHELL-3 released; first training pass complete.**
Round 2 passed all 18 whole-unit and tone-bearing reviews. The immutable release
has 729 numbered-tone units, 58 neutral units retained separately, and two original
quarantines excluded, across the unchanged 10/3/3 speaker split.
The [training report](aishell3-training-report.md) records all 29 validation trials,
selected models, sealed test metrics, every selected-model error and the external
probe. Validation-selected Chinese HuBERT layer 9 with context and logistic regression
achieves 90.40% test accuracy / 89.78% macro F1. Frozen Benma covers 64.41% and reaches
28.95% covered accuracy. This is promising pilot evidence, heavily concentrated in
one test speaker. **Core tone-ML feasibility: CLEARLY PROMISING. Current product
generalization: MIXED / UNPROVEN.** No production integration.
The [AISHELL-3 recovery report](aishell3-recovery-report.md),
[18-item Round-2 comparison](data/generated/aishell3/round2-final/index.html), and
[review/ingestion record](aishell3-qa.md) preserve earlier data and QA history.
The [boundary report](aishell3-boundary-remediation-report.md) separates the
one-sample export correction from the experimental nucleus-plus-coda pooling span.
Original read-unit evidence, corpus labels and speaker partitions are preserved.
The failed THCHS-30 [Phase A report](native-evaluation-report.md),
[corpus decision](native-corpus-recon.md), and [weak-label policy](tone-labeling-policy.md)
are preserved historical records, not AISHELL-3's labeling policy.
The listener-acceptability workflow below is preserved historical infrastructure,
not a prerequisite for the current native-tone experiment. No recruited listeners
or intentionally wrong-tone training recordings are required for the active track.

The active experiment predicts four corpus numbered-tone labels from audio only.
It does not evaluate native-listener acceptability or create learner color thresholds.

This package is offline research only. The historical pilot below asks whether a small learned classifier
can predict **native-listener contextual acceptability** better than the frozen
Benma grader on unseen speakers. It does not integrate ML into the app, retune
acoustic rules, change extraction/alignment, or claim that a model solves Benma.

The deterministic baseline is committed at
`eaf9c4343b0b35f3a5572864fc9f4fc8e17e2a98`. Its manifest SHA-256 is
`23177e44e58a3f7c991ee51ac5b4677899ddd71f5a6ef73ecf47a8213d59a52e`.
Every command checks that manifest against the commit and verifies all **413**
pinned file hashes. The existing root-level schema/evaluator and Stage-0 archives
remain untouched. The older manifest records the pre-commit working-tree state;
`configs/baseline.json` now anchors that exact content to the committed checkpoint.
Never regenerate the frozen manifest to legitimize a changed grader.

## Package map

| Path | Purpose |
| --- | --- |
| [data/](data/README.md) | Canonical v2 JSONL schema and audio provenance |
| [annotations/](annotations/README.md) | Blinded packets, append-only import and bilingual listener rubric |
| [features/](features/README.md) | Allowlisted Benma/context numeric features and missingness |
| [embeddings/](embeddings/README.md) | Pinned HuBERT/WavLM, frozen extraction, pooling and verified cache |
| [models/](models/README.md) | Models 0–4, logistic regression, small MLP |
| [evaluation/](evaluation/README.md) | Safety, classification, coverage and calibration metrics |
| `perceptual_tone/` | Research implementation; never imported by application code |
| `scripts/pilot.py`, `configs/` | CLI and versioned experiment recipes |
| `tests/test_pilot.py` | Focused contract/leakage/reproducibility checks |
| [EXPERIMENT.md](EXPERIMENT.md) | Hypothesis, collection stages, evaluation protocol and decision gate |
| [reports/stage0-summary.json](reports/stage0-summary.json) | Small engineering validation record, not quality evidence |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Preserved deterministic architecture checkpoint |

## Setup and smoke test

Run from repository root. The already-installed research environment has the
required Python packages; existing `apps/mobile/node_modules` provides the pinned
TypeScript replay/AJV dependencies. It is reused read-only, without changing its
dependencies. A separate environment can be created with Python 3.12 and
`uv pip install --python research/perceptual-tone-model/.venv/bin/python -r
research/perceptual-tone-model/requirements-lock.txt` after `uv venv` creation.
CPU package versions are pinned; production dependencies are not changed.

```sh
P=research/perceptual-tone-model
PY=benchmark/pronunciation_v2/.venv/bin/python

# One-time public weight download, if the ignored local cache is empty.
# This is the only command here that accesses the network.
$PY "$P/scripts/download_encoders.py"

$PY "$P/scripts/pilot.py" verify-baseline
PYTHONPATH="$P" $PY -m unittest discover -s "$P/tests" -v
node --test "$P/test_evaluate.cjs"

# OUTPUT must be a new directory. All generated artifacts stay ignored.
$PY "$P/scripts/pilot.py" --config "$P/configs/stage0.json" stage0 \
  --output "$P/data/generated/stage0-new-run"
```

Stage 0 uses 24 real syllable windows from six existing recordings, six explicitly
**non-scientific fixture** speaker IDs, and 72 mock listener judgments independent
of Benma predictions. Six ungradable rows remain in coverage and are excluded
from fitting. All Models 0–4 and both small classifiers execute; real Chinese
HuBERT embeddings run on all 24 items, and real WavLM embeddings on two wider
context items. The cache rerun checks 24 exact vector reuses. These mock metrics
are only exercise of the report plumbing, never product-performance evidence.

## First real pilot: exact workflow

First recruit 6–10 identified speakers and native listeners. Collect connected
speech with consent/access arrangements, retain each speaker's pseudonym across
sessions, save canonical WAVs and full analysis JSON using the **frozen upstream
pipeline**, and assemble its v1 syllable records as described in
[data/README.md](data/README.md). This harness consumes saved evidence; it does not
call live ASR or add production export endpoints. The frozen evaluator can replay
those records before annotation:

```sh
P=research/perceptual-tone-model
PY=benchmark/pronunciation_v2/.venv/bin/python
D="$P/data/generated/pilot-round1"
mkdir -p "$D"
# Place collected v1 records at $D/source.dataset.jsonl and the persistent
# recording_id -> speaker_id JSON registry at $D/speakers.json.
node "$P/evaluate.cjs" "$D/source.dataset.jsonl" "$D/source.baseline.jsonl"

$PY "$P/scripts/pilot.py" init \
  --input "$D/source.baseline.jsonl" --speakers "$D/speakers.json" \
  --dataset-version pilot-round1-v1 --output "$D/manifest.jsonl"

# First concrete annotation preparation command:
$PY "$P/scripts/pilot.py" preflight \
  --input "$D/manifest.jsonl" --output "$D/prepared.jsonl" \
  --packet "$D/packet"
```

Give **only `packet/public/`** to three native listeners per item. Have each fill
`responses.template.jsonl` independently using the included guide. Combine their
completed JSONL lines into `judgments.jsonl`; keep the private map locally.
The main prompt asks whether the target sounds acceptable in that utterance;
optional tone-family answers stay separate.

```sh
$PY "$P/scripts/pilot.py" import-annotations \
  --input "$D/prepared.jsonl" --judgments "$D/judgments.jsonl" \
  --mapping "$D/packet/private-map.json" --output "$D/labeled.jsonl"

$PY "$P/scripts/pilot.py" split \
  --input "$D/labeled.jsonl" --output "$D/split.dataset.jsonl" \
  --split-output "$D/split.json"

$PY "$P/scripts/pilot.py" run \
  --input "$D/split.dataset.jsonl" --split "$D/split.json" \
  --output "$P/reports/runs/pilot-round1"
```

The default real-pilot config rejects temporary identities, Stage-0 examples and
mock judgments. It derives targets from raw judgments, ignores stored consensus
for fitting, checks all audio and partitions, and replays deterministic outputs
before training. Resolve labeling/identity/coverage errors instead of disabling
these checks. `--config PATH` goes **before** the subcommand. Use a new versioned
config/run directory for encoder, window, aggregation or classifier experiments.
Do not choose configurations after inspecting test results.

## Artifacts and reproducibility

`data/generated/` holds private manifests, WAV crops and packets;
`.cache/huggingface/` holds downloaded weights; `embeddings/generated/` holds
content-addressed NPY/JSON entries; `reports/runs/` holds matrices, fitted heads,
per-example predictions and full reports. Parallel directory-specific `generated/`
paths under annotations/features/models are also ignored. No large audio,
embedding, fitted model, or private packet is added to Git. Removing a generated
cache is safe only after retaining the original recordings/analyses and labels.

Runs record dataset/config/split hashes and versions, seeds, exact encoder/model
file hashes, layer/pooling/window/device, feature schemas, hyperparameters,
Python/dependency/platform versions, research source hashes and baseline identity.
Manifests retain their local artifact paths, so relocating/revising a manifest
changes its audit hash. Reuse the saved run manifest/config/split for exact local
reproduction. Numerical bit identity is verified on the recorded CPU environment;
other hardware/library builds require their own reproducibility check.

For independent tools, `export-features` exports verified Benma/context matrices,
and `embed` creates an embedding index using the selected config. Both accept
`--input` and `--output`; the feature output is a new directory and the embedding
output is a new JSON file. These commands never call an encoder training method.

Final frozen replay verification (choose a fresh temporary output):

```sh
node "$P/evaluate.cjs" "$P/stage0.dataset.jsonl" /tmp/benma-pilot-replay.jsonl
cmp "$P/stage0.baseline.jsonl" /tmp/benma-pilot-replay.jsonl
git diff --check
```

Before meaningful training: verified speaker identity, independent native-listener
judgments, all three classes across training speakers, adequate held-out coverage,
a frozen annotation/split/operating-point protocol, and enough diverse real
connected speech. Infrastructure passing is not evidence of perceptual quality.
