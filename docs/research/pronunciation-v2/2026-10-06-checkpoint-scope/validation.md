# Checkpoint validation

All commands used installed local environments. No live provider request, model download, new recording, new F0/VAD evaluation, dependency installation or deployment occurred. Model-inference research tests are outside this checkpoint scope. Earlier raw logs and exports were written under `/tmp/benma-checkpoint/`, outside the commit. The continuation execution environment did not retain that temporary directory; completed broad results are preserved here rather than rerun. Final focused-check logs are in ignored `services/api/var/checkpoint-scope/`.

## Final results

| Check | Result and limits |
|---|---|
| Bounded API, including pronunciation, pitch/evidence, tone graph, perception/perception truth, speech presence, Conversation and concurrency | **593 passed, 4 skipped, 5 deselected, 11 strict XFAIL**, 36.95 s. Four skips are the separately executed PostgreSQL tests; five streaming cases are listed below. Private presence corpus was enabled. |
| Real PostgreSQL integration/concurrency | **4 passed**, 1.17 s, warmup present/absent and duplicate perceived/target work, isolated schemas |
| Standalone private presence corpus | **50 passed, 11 strict XFAIL**, 5.09 s in the final focused rerun after narrowing the expected exception type; same cases were included in the 593-pass API run, not additional unique coverage |
| Connected speech + connected replay + Silero saved-artifact checks | **122 passed**, 1.04 s = 69 connected + 53 artifact tests; no inference |
| Portable Silero saved-artifact subset | **50 passed, 3 deselected**, 0.26 s; excludes private waveform/model hashing and generated viewer inspection |
| F0 research contract/numeric helper tests | **8 passed, 6 deselected**, 0.39 s; six actual estimator extraction tests explicitly excluded |
| Mobile native and web | **332 passed, 27 suites**, 5.579 s; 18 native suites / 202 tests and 9 web suites / 130 tests |
| API Ruff | Passed |
| Research Ruff | Passed, 17 added research Python files under API lint configuration |
| API Python formatting, scoped | **36 changed/added Python files passed**; changed `config.py` has existing HEAD formatting debt, excluded from the clean subset |
| Research Python formatting | **17 files passed** |
| Repository-wide API Python formatting | **FAIL: 32 files would be reformatted, 107 already formatted**; all 32 also fail when checking HEAD content with the same tool/configuration; no unrelated debt reformatted |
| Strict mypy | Passed, **78 source files** |
| Mobile lint and typecheck | Passed |
| OpenAPI and generated TypeScript | Byte-for-byte equal to canonical exporter output; no additional regeneration needed |
| Web export | Passed, offline Expo export to `/tmp/benma-checkpoint/web-export` |
| Android export | Passed, offline Expo export to `/tmp/benma-checkpoint/android-export` |
| `git diff --check` | Passed |
| Candidate private/secret/binary audit | Final 258-path allowlist verified; 25 local outputs excluded; 94 JSON files parsed; no candidate binaries, secret/credential-assignment/contact findings; private `.env` ignored and absent from index |
| Final report/artifact checks | Six required Markdown files present; all links from this report and current development summary resolve locally; category totals and allowlist exactly match the working tree; production presence source hashes unchanged |

After the completed broad suites, only documentation, retention inventory and the narrow presence-test exception guard changed. The affected presence file was rerun (50 passed / 11 strict XFAIL), with Ruff and formatting passing; no production code changed and no broad suite was repeated.

The mobile suite covers SentenceToneGraph geometry, native/web rendering, neutral comparison, eligibility wording, grouped words, stale/legacy evidence, Practice, Free Practice and Conversation workflows. The added legacy screen test processes a mocked result containing an old “detected Tone” message, selects A/B history, verifies no ordinary exposure, then confirms the historical payload survives under labeled diagnostics. A backend test verifies the off default and uncalibrated provider-label wording. Existing laboratory experiment tests now opt in explicitly; the architecture has not been removed.

## Exact streaming exclusion — five cases in three functions

Under `services/api/tests/test_speech_concurrency.py`:

1. `test_stream_orders_authoritative_interpretation_before_committed_reply[preserve]`
2. `test_stream_orders_authoritative_interpretation_before_committed_reply[infer]`
3. `test_stream_orders_authoritative_interpretation_before_committed_reply[clarify]`
4. `test_stream_generation_failure_keeps_perception_and_rejects_other_account`
5. `test_meaning_bytes_leave_server_while_generation_is_still_running`

Each of the three function-level invocations was bounded by `timeout 15` and exited **124**, without completing. For the parameterized function, this proves the first case stalls, not that each parameter independently ran. These streaming tests already existed at HEAD and earlier reports documented their stall. This pass does not diagnose its root cause or claim all streaming behavior is sound. Nonstreaming Conversation, stream preflight rejection, CORS and mobile streaming workflow tests do run.

An initial broad `-k 'not stream and not meaning_bytes'` run produced 526 passed, 62 skipped and 25 deselected after the semantic fix. That filter also excluded unrelated **15 upstream-evidence tests**, two stream CORS checks and three corpus stream cases. The final command narrows exclusion to the three function names above, includes the private corpus, and executes those other 20 cases. An intermediate attempt used wrong full-path `--deselect` IDs (pytest roots these as `tests/...`), failed to exclude the stall, and hit its 180-second timeout; it is not counted as a successful suite. The final name-based command below completed normally.

## Known failures by category

### A — Real product blockers

**Speech-presence false acceptance.** The following six `test_frozen_negative_presence_requirement[...]` cases fail the desired rejection assertion:

- `silence_accidental`
- `neg_clicks`
- `padding_human_head`
- `padding_human_tail`
- `padding_low_voice`
- `padding_phone`

`test_transcript_cannot_rescue_known_periodic_background` also fails: the retained Han-count corroboration means the decision can change with transcript. Four `test_persisted_negative_is_gated_before_feedback[...]` cases fail for accidental silence, with endpoints `practice`, `free_practice`, `conversation`, `stream`. The integration tests execute the real guard and raise `PresenceGateEscaped` immediately after acceptance to stop downstream work.

Together these are **11 strict XFAILs**, restricted to `KnownPresenceFalseAccept` (a dedicated assertion subtype) or `PresenceGateEscaped`, with explicit unresolved-limitation reasons. Each negative-case reason names its corpus identity; the periodic case names the Han-count dependence and the four endpoint cases name accidental-silence guard escape. The final audit tightened the former broad `AssertionError` restriction: failed corpus hashes, lost historical rejection assertions, missing files, malformed data and other unrelated exceptions now fail normally. An unexpected pass also fails because every mark is strict. None is relabeled as a true positive, silently omitted, or counted as successful rejection. General learner tone grading also remains unvalidated and disabled; there is no claimed grading-accuracy test result.

### B — Intentionally excluded/stalled tests

The five streaming cases above. They remain a separate release validation concern. No timeout was enlarged to hide them, assertion removed, or xfail newly added.

### C — Optional dependency/database conditions

The first PostgreSQL run failed all four cases because sandbox localhost access was unavailable. A narrowly approved rerun against the existing local server passed all four; schemas were uniquely named and removed by the tests. No production application rows, migrations or database reset were involved.

An initial research-suite collection included `test_f0_foundation_rmvpe.py`; it failed at import because the API environment lacks Matplotlib, before any tests/model inference ran. No dependency was installed. The corrected checkpoint scope uses connected-speech tests, artifact checks and numeric F0 helpers only. RMVPE/Silero real-model tests require ignored pinned research dependencies/weights/private audio and are deliberately not run here. This is not a claim those historical suites pass in a bare production environment.

The full 53-test Silero artifact suite passed locally with existing private inputs and generated figures. A clean checkpoint supports the 50-test portable subset without those outputs. The three deselected tests are `test_frozen_manifest_and_audio_hashes_are_still_exact`, `test_model_and_baseline_provenance`, and `test_static_viewer_and_all_required_representatives`. Running them requires the separately retained local evidence/model/generated presentation; no silent network fallback exists.

### D — Research expectation failures

Saved Silero results still accept the critical negative and reject four of 37 positives at default. The frozen 0.30–0.70 sweep never rejects the critical negative. These are documented **research outcomes**, not fresh runs or newly failing artifact-integrity tests. F0 eligibility's 37/50 retention and 3/3 healthy controls are historical saved results. No research threshold or truth label was changed to make a test green.

### E — Unrelated pre-existing issues and resolved test setup

The 32-file formatter debt below is verified against HEAD. It is not folded into the checkpoint diff. A newly added mobile test initially failed because its test-side lookup could not find an unlabeled advanced toggle; an explicit accessibility label and direct selector corrected the regression harness. The full final mobile suite then passed. Existing React test-renderer deprecation warnings remain non-failing. No device/audio-route behavior is certified by Jest or an export.

## Reproducible final commands

From repository root, with existing private evidence available:

```sh
BENMA_PRESENCE_CORPUS=1 \
BENMA_TRUST_RECORDINGS="$PWD/services/api/var/utterance-evidence/presence-inventory.json" \
services/api/.venv/bin/pytest -q services/api/tests \
  -k 'not test_stream_orders_authoritative_interpretation_before_committed_reply and not test_stream_generation_failure_keeps_perception_and_rejects_other_account and not test_meaning_bytes_leave_server_while_generation_is_still_running'

(cd services/api && BENMA_TEST_POSTGRES=1 .venv/bin/pytest -q tests/test_perceived_postgres.py --tb=short)

PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q \
  benchmark/pronunciation_v2/test_connected_speech.py \
  benchmark/pronunciation_v2/test_connected_replay.py \
  benchmark/pronunciation_v2/test_silero_vad_artifacts.py

PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q \
  benchmark/pronunciation_v2/test_silero_vad_artifacts.py \
  -k 'not frozen_manifest_and_audio_hashes and not model_and_baseline_provenance and not static_viewer'

PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q \
  benchmark/pronunciation_v2/test_f0_foundation.py -k 'not actual_extraction'

npm --prefix apps/mobile test
(cd services/api && .venv/bin/ruff check . && .venv/bin/mypy src)
EXPO_OFFLINE=1 npm --prefix apps/mobile run lint
npm --prefix apps/mobile run typecheck
(cd apps/mobile && CI=1 EXPO_OFFLINE=1 EXPO_NO_TELEMETRY=1 node_modules/.bin/expo export --platform web --output-dir /tmp/benma-checkpoint/web-export)
(cd apps/mobile && CI=1 EXPO_OFFLINE=1 EXPO_NO_TELEMETRY=1 node_modules/.bin/expo export --platform android --output-dir /tmp/benma-checkpoint/android-export)
git diff --check
```

A clean clone without private inputs must leave `BENMA_PRESENCE_CORPUS` and `BENMA_TRUST_RECORDINGS` unset and report those explicit skips; it must not substitute fake recordings for the known regressions. Portable research checks use the subset command above. The retained corpus hashes and opt-in tests define how to replay private evidence when separately provisioned.

Research Ruff/format checks used `services/api/pyproject.toml` for the 17 Python additions listed under category E in the inventory. Scope formatting checked the 36 changed API Python paths other than pre-existing `config.py` debt. Full formatting was separately run and failed as reported, rather than hidden behind the scoped pass.

## Full formatting debt (all also fail at HEAD)

- `services/api/migrations/versions/0001_production_foundation.py`
- `services/api/migrations/versions/0002_pronunciation_laboratory.py`
- `services/api/migrations/versions/0005_contextual_interpretation.py`
- `services/api/migrations/versions/0008_assistant_generation.py`
- `services/api/scripts/calibration_upstream.py`
- `services/api/scripts/export_openapi.py`
- `services/api/scripts/pronunciation_diagnostic.py`
- `services/api/src/benma_api/assistant_generation/contracts.py`
- `services/api/src/benma_api/assistant_generation/openai.py`
- `services/api/src/benma_api/assistant_generation/repository.py`
- `services/api/src/benma_api/assistant_generation/service.py`
- `services/api/src/benma_api/assistant_speech/repository.py`
- `services/api/src/benma_api/assistant_speech/service.py`
- `services/api/src/benma_api/auth/service.py`
- `services/api/src/benma_api/config.py`
- `services/api/src/benma_api/contextual_interpretation/service.py`
- `services/api/src/benma_api/db/models.py`
- `services/api/src/benma_api/speech/providers/azure.py`
- `services/api/src/benma_api/speech/providers/factory.py`
- `services/api/src/benma_api/speech/providers/iflytek.py`
- `services/api/src/benma_api/speech/providers/tencent.py`
- `services/api/src/benma_api/speech/synthesis.py`
- `services/api/tests/test_assistant_generation.py`
- `services/api/tests/test_assistant_generation_provider.py`
- `services/api/tests/test_audio_utterances.py`
- `services/api/tests/test_contextual_interpretation.py`
- `services/api/tests/test_contextual_interpretation_provider.py`
- `services/api/tests/test_conversations.py`
- `services/api/tests/test_migrations.py`
- `services/api/tests/test_provider_adapters.py`
- `services/api/tests/test_research_export.py`
- `services/api/tests/web_smoke_app.py`

## Physical smoke decision

Automated confidence is sufficient for the four-case graph/product-boundary smoke in [commit-plan.md](commit-plan.md). It is not enough to certify speech-presence reliability or production Conversation behavior. No physical capture or live provider execution occurred in this checkpoint pass. The smoke remains the one next step, before a separately authorized commit.
