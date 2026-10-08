# Validation, preservation and local reproduction

## Final RMVPE extension — completed

**22 research tests passed** in 22.44 seconds. These cover all six estimators' short metadata regressions plus RMVPE actual historical four-context invariance, deterministic full salience, exact native semantics, frozen-corpus completeness, known-F0 accounting, negative handling, removal-only gate behavior and viewer data. No completed 49-file extraction from the previous five trackers was rerun. Upstream pyworld/Matplotlib deprecation warnings are non-failing.

- All **49 canonical corpus hashes and 32 original capture hashes** verified.
- **245 previous raw tracks and 36 saved audio-only alignment paths unchanged**; **467 original frozen artifacts** hash-identical.
- RMVPE: **49 native tracks, 49 full salience archives, 13,318 frames × 360 bins**, zero failures/skips. Source/checkpoint hashes verified.
- Four historical-waveform metadata contexts byte-identical; cold/warm output and upstream public method identical.
- Combined exports verified field-by-field against prior saved rows plus new RMVPE rows: 637 recording metrics, 468 pairwise comparisons, 364 diagnostic windows, 36 perturbations, 234 low-proxy rows, 39 lowest-proxy rows and 195 support rows.
- Chromium passed: 49 cards, six complete raw/minimal/confidence groups per card, all six toggles, native display, view switch, production overlay, local audio decoding/playback. Screenshot visually inspected. Local Chromium required execution outside the filesystem sandbox after sandboxed startup failed; no remote page, provider or audio transfer.
- Ruff check and format passed for research Python; `git diff --check` passed.
- **Pre-existing tracked binary diff is identical** to the RMVPE pass start. Only existing research harness/report files and new research artifacts changed; no production behavior, manifests or lockfiles changed.

The extension receipt is [rmvpe-artifact-verification.json](rmvpe-artifact-verification.json), distinct from the historical five-tracker receipts below. Durable new outputs, source/model, logs and their file hashes are in `services/api/var/f0-foundation/rmvpe/`. The six-tracker viewer is `services/api/var/f0-foundation/viewer.html`; figures are `figures-six/`. The old `/tmp/benma-f0-bakeoff/` corpus/outputs and five-tracker viewer remain unchanged. [Initial blinded notes](rmvpe-blind-review-before-reveal.md) were saved before reading the fresh key; review limitations are explicit.

### Read-only reproduction from saved evidence

```sh
export PYTHONPATH=.
/tmp/benma-f0-bakeoff/.venv/bin/python benchmark/pronunciation_v2/f0_foundation_report.py --output services/api/var/f0-foundation
/tmp/benma-f0-bakeoff/.venv/bin/python benchmark/pronunciation_v2/f0_foundation_rmvpe_audit.py
node benchmark/pronunciation_v2/f0_foundation_browser_check.cjs
```

The report generator joins saved numerical rows, preserves prior aggregate/timing values, and exports the one RMVPE threshold sweep. The audit validates corpus, native evidence, prior values, source/model, blinded notes and the pre-existing tree snapshot. Its production-preservation comparison describes this completed RMVPE pass; later authorized production work will require its own baseline. No estimator inference is needed to inspect or regenerate these reports. Do not rerun RMVPE for the subsequent architecture pass.

### Historical five-tracker validation

The remainder records the previous pass, not additional production-suite runs in the RMVPE extension.


This continuation completed analysis/reporting from saved outputs. It did not rebuild the 49-file corpus, rerun completed extraction jobs, redownload CREPE or rerun passed production suites. Targeted research regression tests invoke short deterministic signals; separate fresh-process timing/invariance verification had already completed for all five trackers.

## Results

| Check | Result |
| --- | --- |
| Actual-estimator metadata invariant plus research metric/immutability tests | **13 passed**, 18.88 s |
| Fresh-process historical `f5dc0cc1` metadata invariant | Byte-identical for all five estimators |
| Three warm repeated extractions per timing waveform | Identical canonical evidence hashes within every fixed tracker configuration |
| Frozen audio hashes / native track correspondence | **49 audio hashes, 245 raw tracks verified** |
| CREPE completeness | **49/49, zero failed or skipped**; 49 activation files |
| Production ablation artifacts | 49 files |
| Table joins | 539 metrics, 396 pairwise rows, 308 diagnostic windows, 30 perturbations, 198 low-proxy rows, 33 lowest-proxy rows, 165 acoustic-support rows |
| Local Chromium viewer | 49 cards; all five raw/clean track groups; initial native view, tracker toggle, raw/clean switch, production overlay, local audio decoding/playback passed |
| Ruff format/check | Passed on new Python research tools/tests |
| Existing backend focused validation | **222 passed**, retained result |
| Existing connected-speech validation | **69 passed**, retained result |
| Existing native/web tone-graph validation | **52 passed** across three suites, retained result |
| Pre-existing tree preservation | **774 file states unchanged**, including the pre-existing deleted file; tracked binary diff identical to start |
| Whitespace/diff validation | `git diff --check` passed |

The research test run emits one upstream pyworld `pkg_resources` deprecation warning; it is not a test failure. Browser execution required the local Chromium process outside the filesystem sandbox after its sandboxed process exited; no external page or audio upload was involved. The viewer itself uses no remote assets.

The machine-readable receipt is [artifact-verification.json](artifact-verification.json); [archive-verification.json](archive-verification.json) confirms the 583-file, 191,090,584-byte durable copy, including identical raw tracks and audio. Exact per-tracker timing and waveform/evidence hashes are in `verification-*.json` in this report. Test, browser and extraction logs remain in the ignored artifact directory. No production tracker, narrow 要/个 fix, downstream graph/gesture code, dependency manifest or lockfile was edited by this pass. Nothing was committed, pushed or deployed.

## Artifact locations

Primary durable local outputs: **`/home/jacob/benma/services/api/var/f0-foundation/`** (ignored by Git).

Open **`/home/jacob/benma/services/api/var/f0-foundation/viewer.html`** directly in a local browser. The archive contains local audio copies under `audio-links/`, all 49 overlays, 15 blind panels, raw tracks, full CREPE activations, production ablations, alignment paths, manifests, metrics, initial blind notes, model/source download receipt, the single already-downloaded checkpoint, browser screenshot, logs and validation scripts. The archive copy adds no downloaded model and does not change the original artifacts.

The original working directory **`/tmp/benma-f0-bakeoff/`** is preserved, including the isolated research environment and package/JIT caches. Its manifest preserves the exact extraction-time source paths. `manifest-local.json` in the durable directory supplies equivalent local audio paths; hashes remain the same. `artifact-sha256.json` verifies durable files. Existing originals remain in `services/api/var/audio/`.

Tracked/reviewable work is limited to `benchmark/pronunciation_v2/f0_foundation*.py`, the viewer template, `f0_acoustic_windows.json`, research tests and this report directory. Raw audio, frame arrays and weights remain ignored. Git's final ordinary diff stat describes pre-existing tracked changes; the new research files are untracked and therefore absent from that stat.

## Reproduce views without extraction

From `/home/jacob/benma`, while the original isolated environment exists:

```sh
export PYTHONPATH=.:services/api/src
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMBA_CACHE_DIR=/tmp/benma-f0-bakeoff/numba
export MPLCONFIGDIR=/tmp/benma-f0-bakeoff/mpl
/tmp/benma-f0-bakeoff/.venv/bin/python benchmark/pronunciation_v2/f0_foundation_report.py
python /tmp/benma-f0-bakeoff/check-artifacts.py
```

The report command reads saved metrics and rewrites numerical tables/CSVs only. The audit reads completed artifacts and checks hashes/joins; it never invokes an estimator. `refresh-support.py` can recompute the post-hoc acoustic/low-proxy views from saved native tracks without extraction or production replay. The functioning viewer needs no rebuild.

The optional research regression command is:

```sh
/tmp/benma-f0-bakeoff/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_f0_foundation.py -q
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/f0_foundation*.py benchmark/pronunciation_v2/test_f0_foundation.py
git diff --check
```

Environment package versions are captured in [research-environment.txt](research-environment.txt); [tracker-inventory.md](tracker-inventory.md) records configuration, implementation revision, licenses and the one model hash. Temporary-environment paths are machine-local, not a portable production lockfile. Reconstruction elsewhere requires the same pinned implementations and the already-authorized audio/model artifacts. It must not silently substitute another checkpoint or mix the old hash-placeholder provenance with the later literal-hash configuration.

## Measurement limitations

The real corpus is small and opportunistic. Most speech lacks independent frame-level F0 truth; coarse spectrogram review is semi-blinded and post-hoc. The protected low-F0 proxy favors the baseline, and its 11 lowest samples cannot establish a general error rate. DTW uses audio only but cannot erase genuine source/prosodic differences. Confidence scales differ and the one fixed cleanup is not a calibrated equal-operating-point comparison. Runtime is measured on one desktop CPU and does not certify a target server/mobile deployment. These limits constrain claims of superiority; they do not erase the observed raw branch errors, known-negative false pitch or synthetic failures.
