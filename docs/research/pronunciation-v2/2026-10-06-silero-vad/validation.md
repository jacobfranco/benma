# Completed validation and preserved working tree

The bounded evaluation is complete. **37/37 positive cases, 10/10 negative cases and 1/1 unresolved case completed inference; zero skipped or failed files.** All 48 timelines contain timestamps, raw probabilities, valid/padded chunk boundaries, original/normalized sample rate, waveform identity and model/runtime provenance. There are **3,681 saved probabilities**. The unresolved case is never counted in positive/negative results.

## Executed checks

| Check | Result |
| --- | --- |
| Real-model research tests | **106 passed**, 8.36 s; no skips/xfails |
| Final artifact-only research tests | **53 passed**, 0.28 s; no skips/xfails, no inference |
| Same-waveform deterministic inference | All 48 exact, including intervening-utterance state reset |
| Official wrapper versus same-model NumPy adapter | All 48 timelines bit-for-bit equal |
| Saved-probability segmentation versus official direct audio helper | All 48 exact at default |
| Transcript and intended-target invariance | **288/288 contexts exact**: 48 waveforms ×6 contexts |
| Sample-rate unit tests | 8, 16, 24, 44.1 and 48 kHz; duration/sample count/frequency/amplitude/tail coverage pass |
| Frozen manifest identity and audio hashes | All 48 exact; every excerpt parent hash verified |
| Fresh current Benma baseline replay | All 48 match the prior frozen decisions |
| Default and threshold artifact completeness | 48 rows each; only the five authorized thresholds; counts/interval summaries cross-checked |
| Static viewer | Eight PNGs, all local resource links present, required six categories covered; representative plots visually inspected |
| Ruff, all five new research Python files | Passed with API repository lint configuration |
| Touched Python formatting | **5 files already formatted** |
| `git diff --check` | Passed |
| Original working-tree/evidence preservation | **22,258 files unchanged; zero changed, zero missing** |

The 106 real-model checks and all CPU timing were already completed when the closing instruction arrived. No completed model inference, timing, or threshold sweep was restarted afterward. Final checks only inspect saved artifacts and hashes. The production/API suites were not rerun because production behavior did not change.

The metadata contexts are valid Mandarin, nonsense, non-Chinese, empty, absent, and changed intended target. Metadata is held by the test harness; only the waveform bytes enter the adapter. Equality covers full raw probabilities and speech intervals, including incorrect decisions. It verifies independence, not accuracy.

Threshold tests check the actual upstream inclusive start (`>=`), strict exit (`<`), hysteresis, 30 ms padding, strict minimum duration, and actual EOF length instead of the zero-padded final chunk. No alternate duration policy is evaluated by the short-audio unit checks: 110 ms and exactly 250 ms remain rejected at the mandated default, while 256 ms of high-probability unit evidence passes. These scalar/numerical unit fixtures are not additional corpus recordings.

## Validation findings resolved during this pass

The first research-test invocation lacked the existing benchmark package's Pydantic dependency. The final command reuses the already installed API site-packages for test collection; nothing was added to production. The complete real-model suite then passed.

An artifact assertion caught an incorrect draft reporting assumption that all inputs were 16 kHz. Saved metadata correctly records **46 ×16 kHz and 2 ×24 kHz** (`native_gain`, `native_bandlimit`). Both 24 kHz cases were already correctly normalized by the original adapter and tested for deterministic/upstream parity. Documentation and the artifact assertion were corrected; results were not rerun or changed. Ruff/format findings in the new research files were also corrected without altering model calculations. Final output logs are in [validation-output.txt](validation-output.txt).

## Local verification commands

From `/home/jacob/benma`, this artifact-only command uses the existing API environment and does **not** run inference:

```sh
PYTHONPATH=.:services/api/src services/api/.venv/bin/python -m pytest -q benchmark/pronunciation_v2/test_silero_vad_artifacts.py --tb=short
services/api/.venv/bin/ruff check --config services/api/pyproject.toml benchmark/pronunciation_v2/silero_vad_audit.py benchmark/pronunciation_v2/silero_vad_latency.py benchmark/pronunciation_v2/silero_vad_report.py benchmark/pronunciation_v2/test_silero_vad_audit.py benchmark/pronunciation_v2/test_silero_vad_artifacts.py
services/api/.venv/bin/ruff format --check --config services/api/pyproject.toml benchmark/pronunciation_v2/silero_vad_audit.py benchmark/pronunciation_v2/silero_vad_latency.py benchmark/pronunciation_v2/silero_vad_report.py benchmark/pronunciation_v2/test_silero_vad_audit.py benchmark/pronunciation_v2/test_silero_vad_artifacts.py
git diff --check
```

Historical commands used earlier in this pass are recorded for reproducibility, **not a request to rerun completed work**:

```sh
PYTHONPATH=services/api/var/silero-vad/deps:. benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/silero_vad_audit.py default
# Default result was inspected before the next command.
PYTHONPATH=services/api/var/silero-vad/deps:. benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/silero_vad_audit.py thresholds
PYTHONPATH=services/api/var/silero-vad/deps:services/api/.venv/lib/python3.12/site-packages:. benchmark/pronunciation_v2/.venv/bin/python -m pytest -q benchmark/pronunciation_v2/test_silero_vad_audit.py --tb=short
PYTHONPATH=services/api/var/silero-vad/deps:. benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/silero_vad_latency.py
```

The default command refuses to overwrite its initial saved result. No script downloads missing models or audio. The exact wheel, source and model hashes are in [model.md](model.md), with environment versions in [environment.json](environment.json). Private audio and ignored research runtime files must exist for model tests; there is no silent skip or network fallback.

The viewer and tables can be regenerated from saved probabilities without inference:

```sh
MPLCONFIGDIR=/tmp/benma-silero-matplotlib PYTHONPATH=services/api/var/silero-vad/deps:. benchmark/pronunciation_v2/.venv/bin/python benchmark/pronunciation_v2/silero_vad_report.py
```

## Preservation and scope

[preservation.json](preservation.json) records zero changed/missing files against the initial **22,258-file** snapshot, including existing research environments. The separately listed **1,446 non-environment files** cover production/mobile source and tests, prior research code/docs, frozen evidence, acoustic/ASR/alignment results, waveform assets and dependency manifests. Their original hashes are in [protected-files-sha256.json](protected-files-sha256.json). The larger initial snapshot remains in ignored local scratch storage with its digest in the receipt.

This pass adds only:

- `benchmark/pronunciation_v2/silero_vad_audit.py`
- `benchmark/pronunciation_v2/silero_vad_latency.py`
- `benchmark/pronunciation_v2/silero_vad_report.py`
- `benchmark/pronunciation_v2/test_silero_vad_audit.py`
- `benchmark/pronunciation_v2/test_silero_vad_artifacts.py`
- `docs/research/pronunciation-v2/2026-10-06-silero-vad/`

Ignored downloads, package files and logs stay under `services/api/var/silero-vad/`. No model weights or new audio are included in the report. No other VAD/model, duration sweep, acoustic combination, provider call or new recording was used. No production source/dependency/runtime configuration, pitch evidence/eligibility, tone comparison or UI was modified. No database/application-data mutation, commit, push, checkout, reset, stash or deployment occurred.

The branch remains `pronunciation-v2-research`. [Final Git outputs](git-state.txt) include the large pre-existing uncommitted working tree; ordinary `git diff --stat` omits untracked research additions, while `git status --short` shows them. **Tracker and VAD-model search are closed; integration is not recommended.**
