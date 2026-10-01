# Environment, reproduction, and validation

Branch: `pronunciation-v2-research`. Starting and final HEAD:
`1b40cda7026e06e397394ecc70cbb8a7c44e9c9c`.
The task began with a clean tree. All additions are research code or this report
directory. No production/API/mobile edits, label changes, training, learned-model
inference, tuning, new representation, cropping experiment, staging, commit, or
push occurred. No packages were installed and no remote data was acquired.

| Component | Version |
|---|---|
| Existing API virtualenv Python | 3.12.13 |
| OS | Linux 7.2.6-arch2-1 x86_64, glibc 2.44 |
| NumPy | 2.5.3 |
| praat-parselmouth / Praat | 0.4.7 / 6.1.38 |
| Production analyzer | 1.2.0-parselmouth-0.4.7-praat-6.1.38 |
| Pydantic | 2.13.4 |
| pytest | 9.1.1 |
| FFmpeg | n9.0.1 |
| Node | v24.18.0 |
| Chromium | 153.0.8010.36 |

The extraction uses the existing API environment for the unchanged acoustic
pipeline. Existing model-harness unit tests use the already installed research
virtualenv and its original dependency lock. Neither environment was modified.
The browser check uses Node standard-library modules and installed Chromium;
Playwright or a browser download is not required.

## Inputs and provenance

`provenance.json` records the exact input CSV hashes, all 131 verified original
audio hashes and paths, extraction source hashes, production parameters, runtime,
generated CSV/HTML hashes, and protected tracked-file hashes for production,
mobile, Experiment 1, Experiment 2 preflight and Experiment 2 results.

- The 118-row manifest retains its historical name,
  `../2026-09-30-experiment-2-preflight/sealed-test-manifest.csv`. It is now
  **opened/inspected**, not a new sealed evaluation.
- Predictions are read from the completed Experiment 2 `fresh-test-predictions.csv`
  and `stress-predictions.csv`. No heads or encoder checkpoints are loaded.
- Luilui membership comes from the original clean-corpus manifest: exactly all 13
  included test T3s for `lingualibre:Q301531`. It remains separate from the fresh set.
- Fresh audio remains in the existing ignored
  `benchmark/corpus/recordings/original/experiment-2-preflight/commons/` directory.
  Luilui audio remains in its existing local cache.
- Canonical PCM16 files exist only inside automatically removed temporary
  directories. Their hashes are retained in diagnostic CSVs; waveforms are not.
- `validation.json` supplements extraction provenance with completed verification
  commands, counts, report/checker hashes, and the final state. It is a validation
  receipt, not a new extraction receipt or an evaluation opening.

No large frame arrays, embeddings, hidden states, or model weights are duplicated.
The extra `luilui-t3-comparison.csv` is the only additional diagnostic population;
all required filenames from the request are present.

## Reproduction commands

From `/home/jacob/benma`, full acoustic regeneration, when actually needed:

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/error_audit.py
# Independent replay, leaving the curated output directory alone:
services/api/.venv/bin/python benchmark/pronunciation_v2/error_audit.py \
  --output /tmp/benma-error-audit-replay
```

These commands overwrite only the named derived diagnostic output, not the
source manifests, predictions, audio, or historical evaluation receipts. The
extractor generates the CSVs, blind page/template and provenance; review.md and
environment.md are the written interpretation and execution record. Rerunning
extraction is unnecessary for reading or completing these documents.

The original validation run was:

```sh
services/api/.venv/bin/python -m pytest -q \
  benchmark/pronunciation_v2/test_error_audit.py \
  benchmark/pronunciation_v2/test_acoustic_forensics.py \
  benchmark/pronunciation_v2/test_evaluation_preflight.py

PYTHONPATH=benchmark/pronunciation_v2 \
  benchmark/pronunciation_v2/.venv/bin/python -m unittest \
  test_pilot test_preflight test_model_probe test_temporal_pooling -v

services/api/.venv/bin/python -m pytest -q \
  services/api/tests/test_acoustic_frontend.py \
  services/api/tests/test_tone_evidence_region.py \
  services/api/tests/test_readings_contours.py
```

Results: **69 + 66 + 118 = 253 tests passed**. The 69-test run includes seven new
audit tests, eight prior forensic tests and 54 preflight tests. Its deterministic
replay test re-extracted all 118 fresh plus 13 stress clips twice into separate
temporary outputs, compared all generated files byte-for-byte, and matched the
curated outputs. Acoustic extraction code and generated CSV/HTML artifacts have
not changed since that successful replay.

After the user's continuation instruction, existing outputs were reused. Final
focused verification excluded the already-completed full extraction replay:

```sh
services/api/.venv/bin/python -m pytest -q \
  benchmark/pronunciation_v2/test_error_audit.py \
  -k 'not full_deterministic_replay'

.venv/bin/ruff check \
  benchmark/pronunciation_v2/error_audit.py \
  benchmark/pronunciation_v2/test_error_audit.py
.venv/bin/ruff format --check \
  benchmark/pronunciation_v2/error_audit.py \
  benchmark/pronunciation_v2/test_error_audit.py
node --check benchmark/pronunciation_v2/error_audit_browser_check.cjs
node benchmark/pronunciation_v2/error_audit_browser_check.cjs
git diff --check
git diff --stat
git status --short
```

Final focused result: **6 passed, 1 deliberately deselected**; the deselection
avoids repeating the full extraction, not a failed or unsupported test. Only the
independence test re-extracts one fresh waveform under changed metadata. Ruff lint
and formatting pass on both new Python files; Node syntax check passes.
`git diff --check` passes. The new files are untracked, so their whitespace was
also checked directly instead of assuming Git's tracked diff covered additions.

A separate artifact-only verification checked exactly 13 unique Luilui T3 rows,
all corresponding immutable labels and A probabilities/predictions, and the 2/13
correct count against the saved stress outputs. Existing tests establish 118
fresh identities, the exact confusion matrix, unchanged lexical labels, unique
blank annotation joins, prediction-blind whitelisting, protected source hashes,
and absence of audio/array files in the artifact directory. The final index is
empty; no audio or other file is staged.

Final artifact-only deterministic regeneration recomputed every error-group
summary from the saved per-clip CSVs and rebuilt the blind HTML/template from the
original manifest. All three outputs were byte-identical. This needed no acoustic
extraction. All required output files, unchanged protected trees, and whitespace
in the new untracked files were also verified directly.

## Browser verification and audit use

The functional check passed in real headless Chromium: all 118 item identities,
initial/last-item rendering, Previous/Next navigation, browser persistence,
CSV quoting and unique ID export, JSON save/restore, invalid-schema rejection,
selection of an existing local WAV, decoding its duration and starting playback.
It also captures the real blank form for visual inspection at
`/tmp/benma-error-audit-page.png`. The displayed prompt, pseudonym, audio control,
annotation choices, certainty and note fields were visually inspected. No
predictions or diagnostics appear on the form.

Chromium's startup socket was blocked in the restricted process sandbox. Running
the local browser check outside that sandbox was approved and succeeded. An
initial `--dump-dom` harness returned before asynchronous media initialization;
the final checker uses a local DevTools pipe and waits for actual completion.
These were harness/startup issues, not failed human annotations. The final check
needs no HTTP server or network connection and disables background networking.

Browser test responses are explicitly synthetic and temporary. A temporary copy
of the page embeds one existing WAV for File API testing; that copy and its
browser profile are removed. Neither test responses nor audio enter the research
artifacts. The real annotation template remains completely blank. This verifies
software behavior, not a Mandarin-speaking human's pronunciation judgment.

For real annotation, open `human-audit/index.html` directly, select the ignored
original audio folder, listen, and save JSON regularly. Export CSV includes all
118 source IDs for deterministic joining. JSON is the browser restore format;
CSV is the analysis export or spreadsheet workflow. LocalStorage is optional
convenience persistence and is not a durable backup. Full instructions and the
prediction-blind handoff boundary are in review.md.
