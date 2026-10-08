# Validation and reproducibility

The acceptance result is **failed integration**, despite passing software checks. The proposed frame rule removes protected human low-F0 evidence; the stricter variant leaves the physical artifacts and scale distortion. No production change was made to accommodate either result.

## Executed checks

| Check | Result / scope |
| --- | --- |
| Current production extraction | All six explicitly requested canonical WAVs analyzed locally once; original file SHA-256 captured. No normalization rerun, replacement recording or other tracker. |
| Frozen baseline preservation | All six newly saved tracks reproduce exactly from unchanged raw evidence/current production selection. Existing baseline `contours.py` and `pitch_evidence.py` copies remain byte-equal to current source. |
| Private historical replay | 49 saved production snapshots, no re-extraction. Every current retained timestamp matches its frozen production list. 617/617 protected low-register times initially selected; ten protected below 70 Hz. |
| Parameter neighborhood | Nine one-factor settings, exact physical rejected sets identical. Frame-rule false rejection of protected 54.610 Hz repeats in all nine. Complete-run variant preserves all protected samples in all nine. |
| Research checks | **16 passed**. Deterministic branch/gap/low/sweep/raw/metadata/projection/eligibility contracts and explicit falsification using the real low-F0 excerpt. This green result records the candidate rule's failure; it is not approval to integrate. |
| Targeted backend | **233 passed**: utterance pitch, contours/readings, acoustic frontend, evidence region, final calibration, sentence graph, observed gesture/groups. Existing production Praat synthetic unit checks are included; no alternative tracker/model inference. |
| Connected speech | **69 passed**: connected speech and connected replay. |
| Diagnostic viewer | Passed in local Chromium: seven recordings, 13 event zooms, 20 saved PNGs; exact counts, frame/consensus toggle, protected counterexample and candidate hover. HTTP/HTTPS blocked; no server or remote assets. |
| Visual inspection | All six overview plots and decisive A1/B4/F1/protected zooms inspected; persistent extremes and scale compression agree with exported metrics. Additional event zooms remain available for review. |
| API Ruff | Passed over `src` and `tests`. |
| Research Ruff | Passed for the three added Python files with the API configuration. |
| Touched Python formatting | Three research Python files pass. No repository formatting sweep or debt cleanup. |
| Source mypy | Passed: **78 source files**. |
| JS / artifact checks | Browser checker syntax and runtime pass; report JSON/CSV parse; local links, hashes and expected output counts checked. |
| `git diff --check` | Passed. |

The broader pronunciation/API suite and real PostgreSQL reuse tests were conditional on a production change surviving acceptance. That condition was not met; they were not rerun. Existing reuse/immutability/grouping coverage in the targeted backend suite passed. Mobile native/web, Practice/Free Practice, lint, typecheck and exports were not rerun because no mobile file changed. These omissions are explicit scope decisions, not passing claims.

## Commands

From repository root using installed environments:

```sh
# First capture only, when these private baseline files are absent:
PYTHONPATH=.:services/api/src services/api/.venv/bin/python -m \
  benchmark.pronunciation_v2.octave_ambiguity_report --extract

# Subsequent replay: no extraction and no overwrite of frozen baselines.
PYTHONPATH=.:services/api/src services/api/.venv/bin/python -m \
  benchmark.pronunciation_v2.octave_ambiguity_report

PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q \
  benchmark/pronunciation_v2/test_octave_ambiguity.py

timeout 120 services/api/.venv/bin/pytest -q \
  services/api/tests/test_utterance_pitch.py \
  services/api/tests/test_readings_contours.py \
  services/api/tests/test_acoustic_frontend.py \
  services/api/tests/test_tone_evidence_region.py \
  services/api/tests/test_final_acoustic_calibration.py \
  services/api/tests/test_sentence_tone_graph.py \
  services/api/tests/test_observed_gesture_groups.py

PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q \
  benchmark/pronunciation_v2/test_connected_speech.py \
  benchmark/pronunciation_v2/test_connected_replay.py

node --check benchmark/pronunciation_v2/octave_ambiguity_browser_check.cjs
node benchmark/pronunciation_v2/octave_ambiguity_browser_check.cjs

services/api/.venv/bin/ruff check --config services/api/pyproject.toml \
  benchmark/pronunciation_v2/octave_ambiguity.py \
  benchmark/pronunciation_v2/octave_ambiguity_report.py \
  benchmark/pronunciation_v2/test_octave_ambiguity.py
services/api/.venv/bin/ruff format --check --config services/api/pyproject.toml \
  benchmark/pronunciation_v2/octave_ambiguity.py \
  benchmark/pronunciation_v2/octave_ambiguity_report.py \
  benchmark/pronunciation_v2/test_octave_ambiguity.py
(cd services/api && .venv/bin/ruff check src tests && .venv/bin/mypy src)
git diff --check
git diff --stat
git status --short
```

The initial six extraction snapshots were captured directly through `PraatAcousticAnalyzer`/`build_pitch_track` before constructing the report CLI; `--extract` reproduces that capture on an absent baseline. Snapshots store source path, SHA-256, analyzer version/configuration, complete result and immutable track. The replay refuses to silently replace a baseline after production selection changes.

Generated logs, frozen snapshots, viewer data and plots are under ignored `services/api/var/octave-ambiguity/`. [Final git outputs](../../../../services/api/var/octave-ambiguity/final-git-state.txt) include the entire pre-existing uncommitted V2 working tree. `git diff --stat` omits untracked files; this pass adds five research source files and eight report/data files, with **zero production modifications**. No recordings or generated waveform/spectrogram assets enter the tracked-source scope.

## Environment and known unrelated limitations

The first sandboxed Chromium attempt could not create a required local socket (`setsockopt: Operation not permitted`; browser pipe reset). A narrowly scoped sandbox escalation for the local browser command was approved automatically; rendering and validation then completed with outbound HTTP/HTTPS blocked. No user confirmation was needed and no approval rejection remains outstanding.

Earlier research documents known speech-presence false acceptance, 11 strict presence XFAILs, five stalled streaming cases and 32 files of pre-existing formatter debt. Those broad checks were not rerun, fixed or reclassified here. See the [previous checkpoint validation](../2026-10-06-checkpoint-scope/validation.md) for their exact identities. This pass's saved negative replay confirms that selected periodic/accidental-background pitch remains; it does not reopen or certify speech presence. Existing synthetic 70 Hz production attrition (159 raw voiced, two selected) also remains visible in the results.

No new test failure remains in the executed software checks. The unresolved product failure is the candidate-rule acceptance gate itself, not a hidden XFAIL, altered corpus label or softened assertion.
