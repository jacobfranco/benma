# Environment and reproduction

Started on `pronunciation-v2-research` with a clean tree at `1cc57c3756009cc450ab7b051fa0ba4a0a01ad5e` (`research: evaluate frozen wav2vec tone probe`). The starting five commits were `1cc57c3`, `5d92c73`, `30820a4`, `3cabc1f`, and `28766bd`. No user changes needed preservation beyond the already committed research artifacts. No commit, push, staging, model loading, training, cloud service, network request, or dependency installation was performed.

Existing local runtime:

| Component | Version |
|---|---|
| OS | Linux 7.2.6-arch2-1 x86_64, glibc 2.44 |
| API virtualenv Python | 3.12.13 |
| NumPy | 2.5.3 |
| praat-parselmouth / Praat | 0.4.7 / 6.1.38 |
| Production analyzer version | 1.2.0-parselmouth-0.4.7-praat-6.1.38 |
| Pydantic | 2.13.4 |
| pytest | 9.1.1 |
| FFmpeg | n9.0.1 |
| Node | v24.18.0 |
| Mobile TypeScript | 6.0.3 |

The existing API virtualenv runs extraction; the existing mobile `node_modules/typescript` transpiles the pure display helpers. Neither environment is modified. The original frozen-wav2vec environment and requirements files remain unchanged. SVG generation is dependency-free; existing ImageMagick rasterized a few plots to `/tmp` for inspection. These raster previews are not repository artifacts.

## Inputs and provenance

- Frozen metadata: `../2026-09-29-frozen-wav2vec/clean-corpus-manifest.csv`.
- Frozen model outputs: `../2026-09-29-frozen-wav2vec/test-results.csv`.
- Frozen V1 categories: `../2026-09-29-frozen-wav2vec/v1-results.csv`.
- Existing original audio: `/home/jacob/.cache/benma/benma-pronunciation-v2-pilot/audio/`.
- Saved V1 evidence for exact-equality tests: `/home/jacob/.cache/benma/pronunciation-v2-model/v1-evidence.json`.
- `selection.json` records the deterministic rule, all 34 identities, and frozen input CSV SHA-256 hashes.
- `provenance.json` records current HEAD, runtime, unchanged analyzer parameters, research source hashes, and hashes of all 267 tracked files under production API, mobile, and the frozen experiment output directory. Tests verify those hashes and `git diff HEAD` for these protected paths.
- Each per-clip JSON records original audio SHA-256, verified against the frozen manifest before extraction, and the temporary canonical PCM16 WAV SHA-256. Canonical durations can differ by a fraction of a sample from source metadata because FFmpeg resamples; classification uses the exact decoded sample count, matching the frozen V1 adapter.

All writes are new research code under `benchmark/pronunciation_v2/`, this new report directory, or temporary files. Canonical audio is automatically deleted after analysis. No source audio, weights, head coefficients, or embeddings are copied into Git. The result contains diagnostic frame samples and pitch candidates, not waveforms.

## Main commands

Run from `/home/jacob/benma`:

```sh
git branch --show-current
git status --short
git log -5 --oneline

services/api/.venv/bin/python benchmark/pronunciation_v2/acoustic_forensics.py
services/api/.venv/bin/python -m pytest -q benchmark/pronunciation_v2/test_acoustic_forensics.py

services/api/.venv/bin/python -m pytest -q \
  services/api/tests/test_acoustic_frontend.py \
  services/api/tests/test_tone_evidence_region.py \
  services/api/tests/test_readings_contours.py \
  services/api/tests/test_final_acoustic_calibration.py \
  services/api/tests/test_pronunciation_diagnostic.py \
  services/api/tests/test_pronunciation_laboratory.py

npm --prefix apps/mobile test -- --selectProjects native --runTestsByPath \
  src/__tests__/learnerGestureContour.test.ts \
  src/__tests__/learnerVerdict.test.ts \
  src/__tests__/pitchPlot.test.ts

.venv/bin/ruff check benchmark/pronunciation_v2/{acoustic_forensics,forensics_plots,test_acoustic_forensics}.py
.venv/bin/ruff format --check benchmark/pronunciation_v2/{acoustic_forensics,forensics_plots,test_acoustic_forensics}.py
git diff --check
git diff --stat
git status --short
```

The analyzer supports `--output /tmp/benma-forensics-replay` for an independent artifact replay. The artifact-integrity tests intentionally inspect the curated default output and existing frozen V1 cache; run the default generation first if those artifacts are absent. Reproduction has no model-training or primary-test-opening side effects. Running the analyzer again overwrites only its derived files in the selected output directory, not the frozen experiment or original audio.

## Validation

- **8 research tests passed:** complete/deterministic 13+21 selection; T4 selection independent of predictions; actual-audio extraction invariant to changed text, pinyin, expected tone and model output; direct imported-pipeline equivalence; preservation of the known `你 → 4-like` failure; null/gap semantics; mobile display bridging separate from measured data; all 34 acoustic and observed results exactly equal the frozen saved results; protected-file integrity; and all 35 SVGs present, parseable and linked from the gallery.
- **171 existing API tests passed** across the six acoustic, evidence-region, contour, calibration, diagnostic, and laboratory test files above.
- **39 existing mobile tests passed** across learner gesture, verdict, and pitch plotting (3 suites).
- Ruff lint and format checks pass on the three new Python files. Node bridge syntax is validated through execution in generation/tests. `git diff --check` passes.
- Visual inspection of rasterized `你`, `五`, `晚`, and the comparison plot checked readable axes, missing spans, separate display geometry, and the reference labeling. A missing comparison-plot invocation found during that inspection was fixed and covered by the artifact test before completion.

These tests establish reproduction and truth-boundary invariants; they do not validate a new tone classifier or a clinical phonation measurement. The complete report preserves the existing failures.
