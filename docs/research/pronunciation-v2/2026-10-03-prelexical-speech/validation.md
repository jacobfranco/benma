# Validation and runtime

Continued the existing uncommitted working tree on `pronunciation-v2-research`. No reset, revert, stash, checkout, commit, push, deployment, speech-provider call, model download, training or user-audio addition. Existing graph/no-speech changes and deleted legacy UI remain intact. The local PostgreSQL container was started with its existing volume for a read-only evidence inventory; no persisted speech records were changed.

## Automated validation

| Check | Result |
|---|---|
| Bounded full API suite | **492 passed**, 4 opt-in PostgreSQL skips, 5 known streaming cases deselected |
| Focused contour, perceived speech, graph, new groups and speech-presence suite | **179 passed**, including both private silence regressions |
| Connected-speech + connected replay | **69 passed** |
| Focused native/web graph and gesture policy tests | **52 passed**, 3 suites |
| Full mobile native/web suites, including Practice, Free Practice, Conversation, legacy learner verdict | **336 passed**, 26 suites |
| Existing classifications recomputed exactly | **77/77 timed units**, 19 recordings, all labels/confidences/reasons/features equal |
| Exact original audio no-speech replay | **19/19 expected decisions**: both historical false accepts rejected; 17 speech takes accepted |
| API Ruff | Passed |
| All changed/new API Python formatting | Passed, **23 files** |
| API mypy | Passed, **76 source files** |
| Mobile lint / TypeScript | Both passed |
| Production web / Android export | Both passed, existing installed Expo, local `/tmp` output |
| `git diff --check` | Passed |

The new tests cover acoustic/reference independence, coexistence of 贵/T4/dipping and 州/T1/falling, moderate fall-vs-T2 difference, rise-vs-T2 consistency, low-confidence/instability/contamination/discontinuity abstention, T3/neutral handling, whole-cell/accessibility semantics and explicit tap copy. Group tests verify exact source offsets, no anonymous/equal splitting, no character F0, raw immutability, group-only contour ownership, correct shared span, visible characters, no individual grade, word-edge simplification, old-response enrichment, synthetic suppression, elapsed-time detail, malformed/mismatching/out-of-audio/overlapping/omitted/inserted word rejection and partial-character nonoverlap.

No-speech code and thresholds were untouched. The earlier 67-case attenuation/speed/excerpt stress study remains historical; it is not counted as a new 67-case run. Here both original private files are hash-verified through the existing opt-in regressions and replay. Physical-device microphone/ASR smoke remains manual. Native/web renderer tests and exports are not reported as physical-device or new browser screenshot validation.

## Commands

From `services/api`:

```sh
BENMA_TRUST_RECORDINGS=/tmp/benma-observed-gesture/recordings.json .venv/bin/python -m pytest -q tests -k 'not test_stream_orders_authoritative_interpretation_before_committed_reply and not test_stream_generation_failure_keeps_perception_and_rejects_other_account and not test_meaning_bytes_leave_server_while_generation_is_still_running'
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/python scripts/export_openapi.py
```

Focused backend command, from root:

```sh
BENMA_TRUST_RECORDINGS=/tmp/benma-observed-gesture/recordings.json services/api/.venv/bin/python -m pytest -q services/api/tests/test_observed_gesture_groups.py services/api/tests/test_sentence_tone_graph.py services/api/tests/test_readings_contours.py services/api/tests/test_perceived_speech.py services/api/tests/test_speech_presence.py
PYTHONPATH=. services/api/.venv/bin/python -m pytest -q benchmark/pronunciation_v2/test_connected_speech.py benchmark/pronunciation_v2/test_connected_replay.py
```

From `apps/mobile`:

```sh
npm run lint
npm run typecheck
npm test -- --watch=false
npm test -- --watch=false --testPathPattern='sentenceToneGraph|toneGestureMatch'
CI=1 npx --no-install expo export --platform web --output-dir /tmp/benma-observed-gesture/web
CI=1 npx --no-install expo export --platform android --output-dir /tmp/benma-observed-gesture/android
```

Ruff format was checked against the union of `git diff --name-only` and untracked API `.py` files, not unrelated files. Generated OpenAPI/TypeScript are produced by the repo exporter. Repository `git diff --check` is the final whitespace check.

## Added runtime

Warm local measurements, no network or acoustic extraction included. Group transformation: 200 repetitions per exact saved recording, median/p95, Python `perf_counter_ns`. Comparison: installed Node/TypeScript policy, 210 batches × 1000 utterances, first 10 batches discarded, all allocated output objects consumed after each timed batch. This is generation time, not device render or end-to-end latency.

| Latest case | Group transform median / p95 ms | Comparison median / p95 ms |
|---|---:|---:|
| 我想买五把雨伞 | .012002 / .012958 | .000119 / .000417 |
| 我要一个苹果 | .008033 / .008976 | .000133 / .000317 |
| 我们去吧 | .005537 / .005660 | .000096 / .000328 |
| 贵州 | .003450 / .003591 | .000143 / .000160 |

These local timings support negligible added computational latency; mobile hardware/render latency was not measured. No new acoustic pass, model call or provider round trip. Group boundaries join the existing small simplification boundary list. No optional model probe entered production.

## Known unrelated limitations

The same five previously stalled streaming cases remain excluded: three parameterizations of `test_stream_orders_authoritative_interpretation_before_committed_reply`, one `test_stream_generation_failure_keeps_perception_and_rejects_other_account`, one `test_meaning_bytes_leave_server_while_generation_is_still_running`. They are not claimed passing or repaired. The separate no-speech streaming preflight remains tested. Four optional PostgreSQL concurrency cases were not enabled. Existing React test-renderer/act warnings remain in passing logs. Unrelated full-tree formatting debt remains untouched.

No failing check remains in the executed final suites. During implementation, TypeScript caught a test fixture's narrowed timing type; mypy caught Pydantic property-decorator typing and a union-list inference. Those were resolved before the passing static checks.

## Private local artifacts

`/tmp/benma-observed-gesture/`: `recordings.json` contains IDs, hashes, original local audio paths and saved evidence; `latest.json`, `audit.json`, `presentation.json`, `verdicts.json`, `gate-replay.json`, `group-performance.json`, `comparison-performance.json`, `critical-traces.svg`/`.png`; inventory/audit/presentation scripts and transpiled TypeScript utilities; validation logs and both exports. Audio remains in the existing ignored API object store. No raw audio was copied into tracked files. The final working-tree status/stat is saved as `final-git-state.txt`.
