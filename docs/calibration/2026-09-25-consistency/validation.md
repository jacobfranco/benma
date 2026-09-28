# Validation and reproduction

No paid provider calls. Database export used `SET TRANSACTION READ ONLY`; API PostgreSQL tests used isolated disposable schemas. Original recording/evidence rows were not modified. No commit.

| Check | Result |
|---|---|
| Focused primary/normalized/verdict/geometry | 3 suites, 39 passed; [log](focused-mobile.log) |
| Focused acoustic/interface tests | 33 passed after adding exact-summary and full-detail assertions; included in full API run |
| Full API, including opt-in PostgreSQL | **427 passed in 34.51 s**; [log](api-validation.log) |
| Ruff / strict mypy | Passed, 73 source files; [log](api-lint.log) |
| TypeScript / ESLint / full mobile Jest | **23 suites /244 passed**; [log](mobile-validation.log) |
| Real timed corpus + local WAV re-extraction | 55 recordings /97 spans /91 authorized; zero category/confidence/reason changes; [log](corpus-validation.log) |
| TypeScript before/after projection + runtime | [Exact outputs and pixel ranges](display-traces.json) |
| Expo web export | Passed; [log](web-validation.log) |
| Chromium desktop / Pixel 7 touch | Eight persisted cases, seven requested categories plus fresh ambiguous fall; [log](browser-validation.log) |
| Diagnostic field-label follow-up | 2 tests passed, Ruff and mypy passed; [log](diagnostic-followup.log) |
| Secret scan / git diff --check | Passed; [log](hygiene-validation.log) |
| Offline benchmark | Not rerun: no acoustic decision, filtering, selection or Praat logic changed |

Development checks caught one new line-length issue and a ReactNode typing error from rendering generic timing dictionary values. Both were fixed before final validation. The export probe printed a missing `perception` field after writing its files; perception is independently persisted and the safe diagnostic has `perceived_text`. No evidence was lost; snapshot files and identity matches were verified. A later developer-diagnostic wording correction separated measured fallback from broad primary graph; only diagnostic tests and lint/types were repeated. Final acoustic/UI behavior was not changed after full validation.

## Local artifacts

- `/tmp/benma-consistency-corpus/all-corpus.json`: all 63 acoustic-record snapshots, including rows with no timing.
- `/tmp/benma-consistency-corpus/corpus.json`: the comparable 55-recording numeric-span corpus.
- `/tmp/benma-consistency-corpus/<utterance UUID>.wav`: copied canonical recordings, not checked into this repository.
- `/tmp/benma-consistency-corpus/results.json` and `results-after.json`: read-only result projection before and after added display-summary metadata.
- `/tmp/benma-consistency-before/contours.py`, `SyllableComparison.tsx`, `normalizedDisplayContour.ts`: pre-pass working-tree snapshots.
- `/tmp/consistency-browser-results.json`: eight selected real results with browser-only case metadata.
- `/tmp/benma-consistency-web`: exported app.
- `/tmp/benma-consistency-browser/node_modules/playwright`: temporary browser harness dependency; no package/lockfile changed.

Full JSON in this report retains reproducible fresh acoustic/display evidence if temporary snapshots are later deleted. Corpus recomputation JSON keeps all before/after features and timing authority. Raw audio was not added to docs. The synthetic playback WAV is transport-only and was never acoustically graded.

## Commands

From `services/api` (API/DB checks require local socket access):

```sh
BENMA_TEST_POSTGRES=1 .venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python scripts/architecture_review.py \
  --corpus /tmp/benma-consistency-corpus \
  --output ../../docs/calibration/2026-09-25-consistency \
  --baseline-contours /tmp/benma-consistency-before/contours.py
```

From the repository root:

```sh
npm --prefix apps/mobile run validate
node apps/mobile/scripts/review-verdicts.cjs \
  docs/calibration/2026-09-25-consistency/recomputation.json \
  docs/calibration/2026-09-25-consistency/learner-recomputation.json
node apps/mobile/scripts/consistency-review.cjs
PLAYWRIGHT_MODULE=/tmp/benma-consistency-browser/node_modules/playwright \
  node apps/mobile/scripts/consistency-browser.cjs
bash scripts/scan-secrets.sh
git diff --check
```

Browser command expects the exported app at `http://localhost:8083`; all `/v1` calls are intercepted. Browser screenshots are not physical-device acoustic re-recordings. The three-view diagnostic uses shared ±4-st axes and the exact same saved evidence; its primary horizontal coordinate fits representative bin times, while filtered/raw views preserve the aligned time interval. Images were opened and visually inspected.
