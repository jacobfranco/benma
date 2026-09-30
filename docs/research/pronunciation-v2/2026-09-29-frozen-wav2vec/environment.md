# Environment — preflight only

Starting/current branch: `pronunciation-v2-research`; commit `30820a449df3ed7f50ddd2c0013910e3844048a1`. Initial working tree clean. The latest finalized pilot checkpoint is present. `git diff 68057aa HEAD --stat -- services/api/src/benma_api/pronunciation apps/mobile` is empty.

Hardware inspected with `nvidia-smi`, `lscpu`, `free -h`, and `df -h /home/jacob/benma /tmp`: Intel Core i7-10700F, 8 physical cores / 16 logical CPUs; 31 GiB RAM with approximately 24 GiB available; approximately 194 GiB workspace disk available. NVIDIA driver communication failed. CPU would be the feasible inference device, but no encoder ran. Model extraction runtime, peak model memory and GPU performance are **not measured**.

Used existing `services/api/.venv/bin/python`: Python **3.12.13**, pypinyin **0.55.0**. Existing system FFmpeg and ffprobe **n9.0.1** decode unchanged originals; inherited diagnostic PCM is float32 at each file's original rate/channels, not model preprocessing. Existing `.venv/bin/ruff` **0.16.1** performs lint/format checks. No dependencies, lockfiles, production runtime configuration, caches or model artifacts were installed or changed.

The `facebook/wav2vec2-base` [canonical model card](https://huggingface.co/facebook/wav2vec2-base/raw/main/README.md) still declares Apache-2.0 and audio-only pretraining at 16 kHz, consistent with the previous reconnaissance. Only documentation was read. No checkpoint revision was resolved or downloaded. No model config, parameters, scaler, head, embeddings or scores exist for this stopped pass.

Exact verification commands:

```sh
git branch --show-current
git status --short
git log -5 --oneline
nvidia-smi
lscpu
free -h
df -h /home/jacob/benma /tmp
services/api/.venv/bin/python benchmark/pronunciation_v2/preflight.py \
  --manifest docs/research/pronunciation-v2/2026-09-28-data-feasibility/pilot-manifest.jsonl \
  --cache /home/jacob/.cache/benma/benma-pronunciation-v2-pilot \
  --output docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec
services/api/.venv/bin/python -m unittest discover \
  -s benchmark/pronunciation_v2 -p 'test_*.py' -v
.venv/bin/ruff check benchmark/pronunciation_v2/preflight.py benchmark/pronunciation_v2/test_preflight.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/preflight.py benchmark/pronunciation_v2/test_preflight.py
```

The audit was rerun after distinguishing unmarked pinyin from an affirmative conflicting tone; this happened before any model work. No test predictions or metrics were opened, so there was no test-driven model change. Inspecting test-file metadata and signal integrity was part of the requested preflight, not model selection.

Validation: **39 focused tests passed**, including eight new preflight regressions. New-file Ruff lint/format checks passed. A broader `ruff check benchmark/pronunciation_v2` attempt found a pre-existing E501 in unchanged `report.py:95`; it was not repaired as part of this stopped experiment. Artifact row counts, local report links, unchanged input-manifest hash and the expected stop status were verified.
