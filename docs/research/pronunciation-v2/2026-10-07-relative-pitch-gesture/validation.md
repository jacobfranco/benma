# Focused validation and reproduction

Production is unchanged. Validation is limited to the research helper/replay, the existing geometry functions it calls, source preservation and the local viewer. Green tests establish projection invariants and accurately record failed physical acceptance; they do not mark the graph ready.

## Results

| Check | Result |
| --- | --- |
| Focused research tests | **30 passed**; no skips in this workspace |
| Frozen six-take replay | 30 accepted units, 961 projected selected points; exact saved track identity, raw/selected values and accepted source-index lists |
| Pairwise semitone invariance | Exhaustive within-unit pairs including across gaps; maximum physical/control error **0.0 st** |
| Register copies | ±12 st deterministic geometry; ×0.5/×2/×8 replay copies; 54.610/55/60/70/350/380/440 Hz shape controls |
| Protected low evidence | **617/617**, including **11/11** saved sub-70-Hz points and 54.610 Hz |
| Frozen controls | **23 recordings / 2,827 selected points**, no loss |
| Actual mobile mapping | Current `normalizedMine`, `normalizedGeometry`, `rawPitch` executed through TypeScript transpilation; no proposed source point added, dropped or duplicated |
| Target/reference mutation | All six geometries identical with target, characters, pinyin and lexical/surface metadata changed but timing preserved |
| Acoustic isolation | All 30 accepted physical units retain classifier/eligibility outputs when the display input changes; frozen tracks unchanged |
| Viewer/browser | Six selections; exact projected counts; grouped 雨伞; empty no-timing Mine; high branch 24 points in two paths; 54.610 Hz; provenance hover; 390 px viewport; six full screenshots |
| Visual review | All six screenshot comparisons inspected; outcome B, no material improvement on primary U take |
| Research static checks | Ruff check and formatting; strict mypy on pure helper; Python compile checks; JS syntax checks |
| Production preservation | All pre-pass mobile/backend source-file SHA-256 values unchanged; proof saved locally |
| Working-tree whitespace | `git diff --check` plus an explicit check of new research source/docs (untracked files are absent from ordinary git diff) |

The focused tests cover rising, falling, U-shaped, gap-containing and mid-unit-octave contours; exact pairwise differences, curvature, extrema, amplitude ratios under a shared domain; group-one-center, no cross-unit connector, half-open overlap ownership, synthetic timing rejection, no accepted timing, input immutability, and the actual frozen acceptance failures. No new product tests were necessary because product code did not change.

## Commands

From repository root, using existing installed environments only:

```sh
PYTHONPATH=. services/api/.venv/bin/python -m benchmark.pronunciation_v2.relative_pitch_report
PYTHONPATH=. services/api/.venv/bin/pytest -q benchmark/pronunciation_v2/test_relative_pitch_gesture.py
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/relative_pitch_gesture.py benchmark/pronunciation_v2/relative_pitch_report.py benchmark/pronunciation_v2/relative_pitch_export.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py
services/api/.venv/bin/ruff format --check benchmark/pronunciation_v2/relative_pitch_gesture.py benchmark/pronunciation_v2/relative_pitch_report.py benchmark/pronunciation_v2/relative_pitch_export.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py
services/api/.venv/bin/mypy --follow-imports=skip benchmark/pronunciation_v2/relative_pitch_gesture.py
node --check benchmark/pronunciation_v2/relative_pitch_geometry.cjs
node --check benchmark/pronunciation_v2/relative_pitch_browser_check.cjs
node benchmark/pronunciation_v2/relative_pitch_browser_check.cjs
git diff --check
```

`relative_pitch_report.py` consumes private frozen files under `services/api/var/octave-ambiguity/before/`, `services/api/var/f0-foundation/production/`, the protected sample list, and `services/api/var/relative-pitch-gesture/saved-analyses.json`. It never runs extraction, a provider, or the database. It writes numeric `replay.json` under this report and generated data/viewer under ignored `var/`.

The optional `relative_pitch_export.py` recovers the six existing saved analysis rows only. Run it from `services/api` with `.venv/bin/python ../../benchmark/pronunciation_v2/relative_pitch_export.py`; it loads existing local settings without printing credentials, begins `SET TRANSACTION READ ONLY`, selects the named canonical assets and their analyses, then writes the private snapshot. There are no database writes, schema changes, provider requests or calls to timing services. This capture was performed once for the pass. The maintained exporter was subsequently formatted and compile-checked without re-querying the database.

The first sandboxed localhost read failed; the same read-only action succeeded with approved local-network access. Sandboxed Chromium could not start its debugging pipe; the approved rerun succeeded with HTTP/HTTPS blocked. Neither escalation was rejected by automatic approval review. No extra user approval was needed to continue authorized work.

Browser checks use installed `/usr/bin/chromium` with a local-file page and debugging pipe; screenshots go under `services/api/var/relative-pitch-gesture/figures/`. No web server, dependency download or external asset is used. Static source templates are retained; rendered viewer data, screenshots and private audio remain ignored.

## Limits and scope

No device re-smoke, fresh audio, independent listener study, proven real-falsetto truth set, tracker/VAD bakeoff, Silero/RMVPE inference, generic threshold search, full mobile suite or unrelated PostgreSQL tests were run. The unchanged development current-state document and earlier research reports were not rewritten; this report is the decision for this pass.

The current graph's supplied smoothed domain and its selected unsmoothed vertices are intentionally distinguished. Re-centering smoothed vertices was computed only as a sensitivity check, not a second accepted prototype. The no-timing fallback domain is not counted as scale improvement. The 617 protected sample control uses explicitly labeled whole-recording fixture units, not fabricated production timing. The saved synthetic-70 result contains only two selected points; both survive, and independent deterministic 70 Hz shape tests cover the transform itself.

Initial formatting/type checks exposed research-only formatting and optional-value typing issues, which were fixed before final validation. No production fix was mixed into this pass. Existing uncommitted work is preserved. No commit, push or deployment.
