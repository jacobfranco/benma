# Experiment 2 environment and reproduction

Branch: pronunciation-v2-research. Starting/current HEAD: `64ae7e17c92dac0b5db563ff56725fea784a4e3f`.
Python 3.12.13; Linux-7.2.6-arch2-1-x86_64-with-glibc2.44.
ffmpeg version n9.0.1 Copyright (c) 2000-2026 the FFmpeg developers.

CPU FP32, Torch threads=4, fit BLAS threads=1, deterministic algorithms=True,
seed=20260929; frozen encoder with before/after state hashes and first-clip
bitwise repetition for each extraction stage. All 31 existing research dependency
versions match requirements-lock.txt. No packages were changed or downloaded.
Only the pinned cached encoder was loaded, with HF_HUB_OFFLINE=1 and
TRANSFORMERS_OFFLINE=1. No network access or GPU execution was needed.

| Package | Version |
| --- | --- |
| certifi | 2026.7.22 |
| charset-normalizer | 3.5.1 |
| cloudpickle | 3.1.2 |
| filelock | 3.32.3 |
| fsspec | 2026.7.0 |
| hf-xet | 1.6.0 |
| huggingface-hub | 0.36.2 |
| idna | 3.20 |
| jinja2 | 3.1.6 |
| joblib | 1.6.0 |
| markupsafe | 3.0.3 |
| mpmath | 1.3.0 |
| networkx | 3.6.1 |
| numpy | 2.3.3 |
| packaging | 26.3 |
| pypinyin | 0.55.0 |
| pyyaml | 6.0.3 |
| regex | 2026.9.29 |
| requests | 2.34.2 |
| safetensors | 0.8.0 |
| scikit-learn | 1.7.2 |
| scipy | 1.16.2 |
| setuptools | 78.1.0 |
| sympy | 1.14.0 |
| threadpoolctl | 3.7.0 |
| tokenizers | 0.22.2 |
| torch | 2.8.0+cpu |
| tqdm | 4.70.1 |
| transformers | 4.57.6 |
| typing-extensions | 4.16.0 |
| urllib3 | 2.8.0 |

| Extraction | Clips | Seconds | Peak process RSS MiB | Min frames | Max frames |
| --- | --- | --- | --- | --- | --- |
| development | 435 | 47.85180787197896 | 897.51171875 | 29 | 82 |
| fresh-test | 118 | 14.030983445001766 | 863.703125 | 30 | 60 |
| stress | 60 | 7.632258961995831 | 805.48828125 | 39 | 52 |

Peak RSS is process high-water RSS, not incremental model memory. Wall times
include loading and determinism checks, not fitting or decoding-verifier time.
Every clip had at least three valid frames; no short-clip exclusion occurred.

Raw historical audio/checkpoint remain in the original ~/.cache/benma locations.
Fresh CC BY-SA 4.0 audio stays in the existing ignored preflight cache.
New pooled features and auxiliary diagnostic heads are local and ignored under
`benchmark/corpus/recordings/original/experiment-2-temporal-cache`. Full hidden states are discarded.
The two compact primary head NPZs are preserved with the reports for reproducibility;
both parameter-array hashes and file-byte hashes are locked. The copied training
manifest preserves the exact 386 original rows and their audio provenance.

Ordered commands and validation commands are documented in
`benchmark/pronunciation_v2/README.md`. Stage receipts and exclusive writes prohibit
silent overwrite/reopening. To reproduce elsewhere, preserve source, inputs and
dependency locks; use an explicitly separate run/cache and report its lineage.
Never delete a receipt to make a rerun look pristine. On this workspace the fresh
panel is now inspected. `temporal_pooling_report.py` only verifies arithmetic and
writes derived reports; it never extracts, fits or predicts.

Validation: 66 research/model tests and 54 seal/preflight tests passed. New source
passes Ruff check/format; directory-wide checks have the pre-existing report.py:95
failure. The unsuccessful broad discovery and successful split-suite runs are
recorded in provenance, without environment mutation.
