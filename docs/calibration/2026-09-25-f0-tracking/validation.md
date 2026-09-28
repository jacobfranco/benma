# Validation and reproduction

This pass changes analysis artifacts only. No production source/contract/UI change, database evidence mutation, provider call, dependency installation, commit or push occurred. The current corpus snapshot and completed corrected experiment were reused after interruption.

| Check | Result |
|---|---|
| Focused research tests | `services/api/.venv/bin/pytest -q docs/calibration/2026-09-25-f0-tracking/test_bakeoff.py`: **13 passed in 0.65 s** on the final objective/data |
| Identity adapter | Exact production acoustic dictionaries match on all **67 WAVs** |
| Persisted vs current audio extraction | All **101** category/confidence/reason tuples match; one older subharmonic fixture differs in features, documented in review |
| Analysis lint | Ruff `--select F,I` passed; [log](lint-validation.log) |
| Analysis formatting | Ruff format check passed; same log |
| JavaScript syntax | `node --check …/learner-verdicts.cjs` passed |
| Actual learner model | Existing TypeScript learnerVerdict evaluated over every numerical span/method; [outputs](learner-verdicts.json) |
| Data validation | JSON/SVG parsing; 67/59/101/95 counts; summaries and exhaustive change inventories reconciled; rejected timing remains unclear; [log](artifact-validation.log) |
| Saved forensic reuse | All saved per-frame alternate inputs match final corrected fresh traces; plots did not need another acoustic run |
| Plot inspection | Main 马 SVG and three sample-level zooms rendered using installed `rsvg-convert` and visually inspected |
| Preservation | All **293** pre-existing modified/untracked files byte-identical to initial fingerprints |
| Hygiene | `git diff --check` and repository secret scan passed; [log](hygiene-validation.log) |
| Full API/mobile/benchmark suite | Intentionally not rerun: no production behavior change; prior consistency-pass validation remains historical evidence, not a claimed fresh run |

The tests cover level/rise/valley/fall paths, mandatory missing regions, weak/unvoiced onset, competing weaker octave candidates, actual-candidate membership, input preservation, target-metadata independence, adapter equality and timing quarantine. These are research-tool invariants, not a claim of independently validated human F0 accuracy.

A development check corrected the custom DP UV silence-score scaling before the final full comparison. The final completed run supplies every table. The two category changes in the stronger-continuity variant are experimental findings, not changes applied to production. Formatting and report generation do not require another expensive corpus extraction.

NAC is an existing independent implementation in the correlation family, not a separate pYIN/neural package. Its diagnostic quality adapter borrows nearest-frame baseline energy/spectral/high-pass evidence, never interpolated F0. Strength scales are not calibrated between trackers. Its timings exclude the already-computed production comparison cost. Fallback timing is estimated as the sum of measured primary and CC times without routing overhead.

## Reproduce from the existing snapshot

From repository root, using the API virtual environment:

```sh
# Reuse the completed comparison unless changing the experiment.
services/api/.venv/bin/python docs/calibration/2026-09-25-f0-tracking/audit.py
node docs/calibration/2026-09-25-f0-tracking/learner-verdicts.cjs
services/api/.venv/bin/python docs/calibration/2026-09-25-f0-tracking/report-tables.py

# Only if extraction actually needs recomputing:
services/api/.venv/bin/python docs/calibration/2026-09-25-f0-tracking/bakeoff.py
# Then repeat the three summarization commands above.

# Only if forensic source data changes:
services/api/.venv/bin/python docs/calibration/2026-09-25-f0-tracking/forensics.py
services/api/.venv/bin/python docs/calibration/2026-09-25-f0-tracking/waveform-zooms.py

services/api/.venv/bin/pytest -q docs/calibration/2026-09-25-f0-tracking/test_bakeoff.py
services/api/.venv/bin/ruff check docs/calibration/2026-09-25-f0-tracking --select F,I
services/api/.venv/bin/ruff format --check docs/calibration/2026-09-25-f0-tracking
node --check docs/calibration/2026-09-25-f0-tracking/learner-verdicts.cjs
git diff --check
bash scripts/scan-secrets.sh
```

`/tmp/benma-f0-corpus` contains canonical WAV copies, corpus.json with snapshot evidence, and complete `<utterance>.tracks.json` files. Audio was not added to the report directory. The full-recomputation script produces comparison/traces/latencies; audit.py adds the cached fallback experiment and exhaustive frame changes; report-tables.py supplies confidence/verdict/runtimes and control tables. Fresh diagnostics and acoustic/candidate traces remain in this directory even if `/tmp` is later removed.

If the snapshot is lost, `export-corpus.py` can rebuild it from the local development database when run from `services/api`; it opens a repeatable-read read-only transaction and copies WAVs to /tmp. That is a **new snapshot**, potentially with additional recordings, so its counts must be reviewed rather than silently substituted for this report. The current 67-recording snapshot was not rediscovered on continuation. A separate read-only lookup checked only the four already-identified raw alignment rows and saved their whole-syllable phone timing in [phone-timing-audit.json](phone-timing-audit.json).

The attempted Playwright preview initially lacked its expected bundled browser executable. No browser was downloaded; installed `rsvg-convert` supplied the successful plot render/inspection. No learner browser acceptance was needed because no rendered app data or UI code changed.
