# Experiment environment and reproduction

Continuation branch **pronunciation-v2-research**, starting commit **5d92c73**. Initial tree clean. No staging, commit or push. Original acquisition manifest, production/API/mobile code and production dependency files remain unchanged. The prior stopped pass is preserved in `preflight.md`; this document now describes the completed continuation.

## Hardware and runtime

Inspected `nvidia-smi`, `lscpu`, `free -h`, `df -h /home/jacob/benma`: Intel **i7-10700F**, 8 physical cores/16 logical CPUs, approximately **31 GiB RAM / 24 GiB available**, **194 GiB disk available** at start. NVIDIA driver communication failed. No CUDA inference was attempted; no paid compute used.

CPU FP32 with **four Torch threads**, deterministic algorithms, seed **20260929**. Development feature extraction: **44.6796 s**, approximate peak process RSS **927.7 MiB**. Test extraction: **7.5337 s**, approximate peak RSS **820.4 MiB**. Total **52.2133 s**. These are measured wall times inside extraction, including model loading, state hashing and one first-clip determinism repeat, excluding downloads/head fitting. A separate one-training-clip pre-selection smoke took **1.6204 s** and peaked around **783.2 MiB**. These are offline short-clip measurements, not a production latency or concurrency guarantee. CPU linear fits are bounded to one BLAS thread.

## Research-only dependencies

Created ignored `benchmark/pronunciation_v2/.venv`, Python **3.12.13**; no production environment packages changed. Installed direct dependencies:

| Package | Version |
|---|---|
| torch | 2.8.0+cpu |
| transformers | 4.57.6 |
| scikit-learn | 1.7.2 |
| numpy | 2.3.3 |
| scipy | 1.16.2 |
| pypinyin | 0.55.0 |

`benchmark/pronunciation_v2/requirements.txt` pins these direct requirements. `requirements-lock.txt` records all 31 installed packages, including Hugging Face Hub **0.36.2**, tokenizers **0.22.2** and safetensors **0.8.0**. Stable pinned versions were used; no claim that these are the newest versions is made. Existing Ruff **0.16.1** handles lint/format. FFmpeg/ffprobe **n9.0.1** handle decoding.

V1 runs in the original `services/api/.venv` with existing NumPy **2.5.3**, parselmouth **0.4.7**, Praat **6.1.38**. Its acoustic/contour/evidence-region source bytes match `68057aa`. V1 receives production-equivalent 16-kHz mono PCM16; V2 receives 16-kHz mono float32 and checkpoint waveform normalization. No new F0 system or model inputs were introduced.

Only `facebook/wav2vec2-base` was downloaded, revision **0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8**, with its config, processor config, README and `pytorch_model.bin`. The downloaded [model card](https://huggingface.co/facebook/wav2vec2-base/blob/0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8/README.md) retains Apache-2.0, consistent with prior reconnaissance. The full model/processor config and loading information are recorded in `development-extraction.json`; expected unused pretraining quantizer/projection weights do not imply missing acoustic encoder parameters.

## Local artifacts, outside Git

Persistent cache: `/home/jacob/.cache/benma/pronunciation-v2-model/` (approximately **378 MiB**).

- `hf/`: hash-pinned checkpoint snapshot.
- `development-features.npz`: 435 × 768 vectors at each of layers 4/6/8, with asset IDs.
- `test-features.npz`: 60 × 768 vectors at selected layer 8, with asset IDs.
- Matching JSON extraction reports.
- `selected-head.npz`: training-only scaler mean/variance/scale, 4 × 768 coefficients, four intercepts and class order. No encoder/head pickle is required.
- `v1-evidence.json`: detailed local Praat evidence and observed-contour results.

The acquisition audio cache was read only. Package download cache uses `/tmp/benma-v2-uv`; model weights, features and selected head use the persistent cache above. The research virtualenv occupies approximately **1.1 GiB** and is ignored. Initial uv creation failed because its default cache was read-only; redirecting the package cache resolved it. Authorized network/cache writes succeeded without a user-facing approval interruption.

## Exact main commands

Run from `/home/jacob/benma`:

```sh
git branch --show-current
git status --short
git log -5 --oneline
nvidia-smi
lscpu
free -h
df -h /home/jacob/benma
services/api/.venv/bin/python benchmark/pronunciation_v2/remediate.py \
  --manifest docs/research/pronunciation-v2/2026-09-28-data-feasibility/pilot-manifest.jsonl \
  --cache /home/jacob/.cache/benma/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec
UV_CACHE_DIR=/tmp/benma-v2-uv uv venv benchmark/pronunciation_v2/.venv --python services/api/.venv/bin/python
UV_CACHE_DIR=/tmp/benma-v2-uv uv pip install --python benchmark/pronunciation_v2/.venv/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
UV_CACHE_DIR=/tmp/benma-v2-uv uv pip install --python benchmark/pronunciation_v2/.venv/bin/python -r benchmark/pronunciation_v2/requirements.txt
UV_CACHE_DIR=/tmp/benma-v2-uv uv pip freeze --python benchmark/pronunciation_v2/.venv/bin/python > benchmark/pronunciation_v2/requirements-lock.txt
HF_HUB_DISABLE_XET=1 HF_HOME=/home/jacob/.cache/benma/pronunciation-v2-model/hf-home benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py download
benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s benchmark/pronunciation_v2 -p 'test_*.py'
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py select
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py test
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py groups
benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/model_probe.py compare
.venv/bin/ruff check benchmark/pronunciation_v2/{remediate,features,model_probe,v1_adapter,test_model_probe}.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/{remediate,features,model_probe,v1_adapter,test_model_probe}.py
git diff --check
git diff --stat
git status --short
```

Local execution logs remain at `/tmp/benma-v2-{remediation,download,tests,select,test,groups,compare}.log`; they are convenience logs, not sole provenance. Curated artifacts preserve the key outputs and hashes. Downloads and cache writes needed sandbox escalation and were automatically authorized under the user's explicit scope.

Do **not** rerun the primary test against this output directory: the exclusive opening receipt intentionally refuses it. For a separately documented reproducibility run, use a new cache/output and preserve the pinned checkpoint revision and split; it cannot become a new pristine evaluation after seeing these results. No exact replay requires downloading new corpus audio.

## Validation and pre-test corrections

**52 focused tests passed** before selection. New tests use synthetic signals/tiny random encoders and corpus metadata; they never fit or select on final test audio. The one synthetic stereo test originally assumed arithmetic averaging, whereas FFmpeg's default conversion uses equal-power mixing; the expectation and frequency check were corrected **before selection/test opening**. All 495 primary files are mono. There were no post-test code/model changes. Tiny-model hooks verify layer indexing; whole-state hashes and absent gradients verify freezing. Actual checkpoint and V1 smoke tests used only one training clip.

Ruff passes for every new Python file. The existing `report.py:95` line-length issue from the prior checkpoint remains outside this change. Production tests were not run because shared production code was unchanged. Recorded-output metrics, hashes, OOF membership, source scope and report links were independently checked without another model evaluation.
