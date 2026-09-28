# Validation and reproduction

No paid providers were invoked. The corpus export was read-only; PostgreSQL tests used temporary isolated schemas. Final validation began after focused implementation stabilized.

| Check | Result / log |
|---|---|
| New focused acoustic tests | 32 passed, including two API target-revision integrations; included in final API coverage |
| Full API including pronunciation/acoustics | 422 passed, four opt-in skips across two disjoint portions; see explanation below |
| Opt-in PostgreSQL | Four passed: [log](postgres-validation.log); **426 total API tests passed** |
| API Ruff / strict mypy | Passed, 73 source files: [log](api-lint.log) |
| Full mobile Jest / Practice / verdicts | 22 suites, 235 tests passed: [log](mobile-validation.log) |
| TypeScript / ESLint | Passed in mobile validation |
| Offline benchmark | 96 tests, Ruff/mypy and corpus commands passed: [log](benchmark-validation.log) |
| Persisted corpus + WAV re-extraction | 51 recordings /93 numerical spans, two changed categories: [log](corpus-validation.log) |
| Isolated classifier measurements | 31 alternating repetitions per authorized span: [log](metrics-validation.log) |
| Expo web export | Passed: [log](web-validation.log) |
| Chromium desktop / Pixel 7 touch | Matches / Close / Close / Matches; charts, raw details, fixture-score exclusion, playback and target persistence passed: [log](browser-validation.log) |
| Git diff check / high-confidence secret scan | Passed: [log](hygiene-validation.log) |

The sandbox prevented socket operations. The initial API run completed **381 collected items (377 passes +4 PostgreSQL skips)**, then stalled in `test_stream_orders_authoritative_interpretation_before_committed_reply[preserve]`. It was stopped. Exactly the **remaining 45 collected test IDs** ran with local socket access and passed; already-completed tests were not rerun. See [initial portion](api-validation.log) and [remaining portion](api-remainder-validation.log). The four opt-in PostgreSQL tests then passed separately. This is complete suite coverage across partitions, not a claim that the stalled command exited successfully.

Mobile's initial final lint invocation found an import-group blank-line error in the new test file and stopped before typecheck/Jest. After that test-formatting fix, the complete mobile command passed. A focused API integration initially used an artificial recording duration that made timing coverage fall just below its existing gate; the test fixture duration was corrected. No production timing threshold was changed. No acoustic implementation changed during final validation.

## Reproduction

The retained local snapshot `/tmp/benma-final-narrow-corpus/corpus.json` contains persisted acoustic data, diagnostic timing authority and all 51 canonical WAVs. No audio was added to the repository. The pre-pass working-tree classifier is `/tmp/benma-final-narrow-before/contours.py`; using committed HEAD would incorrectly compare against several earlier uncommitted passes.

From `services/api`:

```sh
.venv/bin/python scripts/architecture_review.py \
  --corpus /tmp/benma-final-narrow-corpus \
  --output ../../docs/calibration/2026-09-24-final \
  --baseline-contours /tmp/benma-final-narrow-before/contours.py
.venv/bin/pytest -q tests/test_final_acoustic_calibration.py
.venv/bin/pytest -q
BENMA_TEST_POSTGRES=1 .venv/bin/pytest -q tests/test_perceived_postgres.py
.venv/bin/ruff check .
.venv/bin/mypy
```

The full API command requires local socket permission. The PostgreSQL command uses the configured local development database and disposable schemas.

From repository root:

```sh
node apps/mobile/scripts/review-verdicts.cjs \
  docs/calibration/2026-09-24-final/recomputation.json \
  docs/calibration/2026-09-24-final/learner-recomputation.json
npm --prefix apps/mobile run validate
make benchmark-check
bash scripts/scan-secrets.sh
git diff --check
```

The new browser harness defaults to `/tmp/final-browser-results.json`, a read-only projection of the four actual results. It supports `BENMA_BROWSER_RESULTS`, `BENMA_WEB_URL`, `BENMA_BROWSER_OUTPUT` and `PLAYWRIGHT_MODULE`. Serve the exported web directory locally and run `node apps/mobile/scripts/final-acoustic-browser.cjs`; all API endpoints are intercepted. Screenshots are browser acceptance using persisted human evidence and synthetic playback transport, not new physical recordings.

`recomputation.json` contains all before/after features, selected regions, local WAV recomputation and timing authority. `tone2-tone3-corpus.csv` summarizes the relevant authorized comparison spans; `gap-trace.json` retains raw flank candidates and the old discontinuity calculation; `summary.json` contains counts, every changed result and runtime summaries. No independently reviewed pilot labels were supplied, so learner report accuracy rates remain null.
