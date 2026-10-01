# Pronunciation V2 offline probe

This research harness does not alter production behavior. Corpus audio, checkpoint weights, pooled embeddings, scaler/head arrays and detailed V1 traces stay outside Git. The 2026-09-29 study uses isolated lexical labels with unknown native-Mandarin status; it is not audited surface-tone gold.

## Experiment 2: frozen temporal-pooling comparison

`temporal_pooling.py` implements the separate 2026-09-30 protocol. It does not run
Experiment 1's selection grid. It verifies the sealed 118-clip manifest and local
audio before each stage, uses the pinned local checkpoint on CPU FP32, and fixes
layer 8 / C=0.1. A has 768 whole-mean features; B has 2,304 chronological third-mean
features with boundaries `(0, N//3, (2*N)//3, N)`. Both fail for fewer than three
valid frames. Only the original 386 training rows fit either primary head.

The completed run lives in
`docs/research/pronunciation-v2/2026-09-30-experiment-2-temporal-pooling/`.
Unlike Experiment 1, this directory retains the two compact fitted `head-*.npz`
artifacts (scalers and linear coefficients) so the locked heads remain available.
Audio, model weights and pooled-feature caches stay local and ignored; no hidden
frame arrays are retained. Existing receipts prevent silently repeating a stage.
These are the original execution commands, not overwrite instructions:

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/evaluation_preflight.py verify
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/temporal_pooling.py develop
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/temporal_pooling.py lock
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/temporal_pooling.py fresh
# Inspect/report the fresh results before running the known stress set.
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/temporal_pooling.py stress
```

`develop` first reproduces A against Experiment 1's hash-verified development
features, selected scaler/head and validation metrics. Failure stops execution.
It then fits B and the two protocol-defined source diagnostics without selection.
`lock` hashes code, inputs, environment and fitted parameters before fresh feature
extraction. `fresh` writes an exclusive opening receipt before extraction, and
`stress` requires the completed fresh result. Any later corrective run must be
explicitly documented separately, preserving the original outputs.

Run tests in their existing environments without changing the ML dependency lock:

```sh
PYTHONPATH=benchmark/pronunciation_v2 benchmark/pronunciation_v2/.venv/bin/python -m unittest test_pilot test_preflight test_model_probe test_temporal_pooling -v
services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_evaluation_preflight.py -q
```

## Environment

Use a separate ignored research virtualenv, never the production API environment for ML installs:

```sh
UV_CACHE_DIR=/tmp/benma-v2-uv uv venv benchmark/pronunciation_v2/.venv --python services/api/.venv/bin/python
UV_CACHE_DIR=/tmp/benma-v2-uv uv pip install --python benchmark/pronunciation_v2/.venv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
UV_CACHE_DIR=/tmp/benma-v2-uv uv pip install --python benchmark/pronunciation_v2/.venv/bin/python -r benchmark/pronunciation_v2/requirements.txt
```

`requirements-lock.txt` records all installed transitive versions. To reproduce those exactly, use it instead of `requirements.txt` after the CPU Torch install. Existing FFmpeg supplies audio decoding. V1 runs separately using the unchanged API virtualenv (Praat/parselmouth already installed).

## Ordered experiment stages

1. Run `remediate.py` with `--manifest`, `--cache` (persistent acquisition cache), and `--output`. It freshly validates all audio, records exclusions without rewriting the acquisition manifest, and freezes deterministic primary membership.
2. `model_probe.py download`: downloads only the authorized `facebook/wav2vec2-base` checkpoint and its metadata. First acquisition resolves and records a revision. For exact replay, preserve the recorded snapshot and `checkpoint.json`; do not resolve a new main revision.
3. Run focused tests before model selection.
4. `model_probe.py select`: extract train/validation features once, fit nine candidates, select on validation, save local head/scaler and create `experiment-config.locked.json`.
5. `model_probe.py test`: verifies locked inputs/code/environment, creates an exclusive opening receipt, extracts the 60 held-out clips and records the primary result once.
6. `model_probe.py groups`: fixed-config leave-one-source-group-out diagnostic, after the primary result exists.
7. `model_probe.py compare`: unchanged V1 adapter, common-subset metrics and error records.

Defaults: output `docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec`, model/cache `~/.cache/benma/pronunciation-v2-model`. The model commands use the isolated research Python. Set `HF_HUB_DISABLE_XET=1` for conventional checkpoint download. Offline stages require no network.

```sh
benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s benchmark/pronunciation_v2 -p 'test_*.py'
HF_HUB_DISABLE_XET=1 HF_HOME=/home/jacob/.cache/benma/pronunciation-v2-model/hf-home benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py download
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py select
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py test
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py groups
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py compare
```

Feature caches and the test receipt deliberately refuse silent replacement. Use a separately documented run/output/cache for a new experiment, never delete the existing receipt to disguise a retry. After opening test metrics, do not change the selected configuration or code and pretend the test remained pristine.

## Scientific controls

- Encoder gets only each unchanged full waveform, decoded mono at 16 kHz and normalized with the checkpoint's own feature extractor. No trimming or augmentation. FFmpeg defaults handle channel mixing; retained corpus files are mono.
- One waveform per forward avoids group-norm padding effects. Pool valid hidden frames only. `hidden_states[k]` means output after Transformer block k; index zero precedes the Transformer stack. Only 4/6/8 enter primary selection.
- `eval()`, `requires_grad_(False)`, `inference_mode()`, before/after state hashes and gradient checks enforce freezing. First-clip repeated extraction tests determinism.
- StandardScaler fits training features only. Head is unweighted multinomial L2 logistic regression, C in 0.1/1/10. Selection uses macro F1, balanced accuracy, mean T2/T3 recall, then smaller C and lower layer, with metric ties rounded to 12 decimals.
- Raw softmax is uncalibrated. Max probability >=0.9 is solely an error-report flag, never an acceptance or abstention threshold.
- The V1 adapter verifies historical code against `68057aa`, uses existing production-equivalent canonical decoding and whole isolated-clip bounds, and supplies no expected tone or text. Coverage and common-subset results accompany its abstentions.

## Experiment 3: nonlinear-head preflight

The preregistered comparison uses the same frozen layer-8 whole-mean features and
386 training rows. The only nonlinear arm is `768 → 8 → tanh → 4`, trained with
one seed, full-batch AdamW and exactly 200 epochs. The protocol and receipts are in
`docs/research/pronunciation-v2/2026-10-01-experiment-3-preflight/`.
The opened 118 and Luilui are diagnostics; the bounded source audit did not find
sufficient independent new speakers, so no fresh panel was sealed.

Preflight has locked the protocol, reproduced the linear baseline and exercised
nonlinear training on synthetic data. The next execution fits and locks the
nonlinear head on the original training rows, without opening test predictions:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/nonlinear_head.py verify
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/nonlinear_head.py develop
```

`lock`, `reproduce` and the metadata-only `nonlinear_sources.py` audit were already
run; their outputs refuse replacement. `develop` similarly writes an exclusive
receipt. Do not delete receipts to disguise a retry. There is no fresh-test command.
A later evaluation pass must acquire/seal a qualifying panel and lock its runner
against the protocol, seal and both fitted heads before opening predictions.
