# Final validation

All external speech/AI providers remained unused. No new recordings, downloads, RMVPE execution or 49-file tracker benchmark rerun occurred. Replay reads saved production JSON. The only focused extraction measurement in this pass used the unchanged production Praat analyzer on one existing human recording; production invariant tests use local fixtures.

## Executed suites

| Check | Final result |
|---|---|
| Bounded API suite, including audio/pitch, pronunciation, contours, tone graph, perception truth, reference fixes and presence | **525 passed**, 4 opt-in PostgreSQL cases skipped, 22 streaming/meaning cases deselected; 32.77 s |
| Actual PostgreSQL concurrency/reuse, separate isolated schemas | **4 passed**, 1.34 s |
| Connected speech + connected replay | **69 passed**, 1.13 s |
| Mobile, both native and web projects | **331 passed**, 26 suites, 5.53 s |
| Ruff, API tree | Pass |
| Ruff, new saved-only replay script | Pass |
| Touched Python formatting | **16 files** pass |
| Strict mypy | **78 source files** pass |
| Mobile lint and typecheck | Pass |
| Web export and Android export | Pass; local artifacts only |
| `git diff --check` | Pass |

The two exact historical presence regressions were included by supplying a local manifest for the existing original/periodic silence files; they were not skipped in the final bounded suite. The newest accidental silence was replayed separately and remains accepted, as documented in `presence-replay.json`. The API suite also covers narrow 要 quantity resolution and 个 lexical/surface handling; these source files were not changed.

Mobile coverage includes SentenceToneGraph, gesture matching, Practice, free-talk/Conversation screens and workflow, shared Free Practice workflows, transcript feedback, native and web rendering. Tests verify uncertain comparison for every eligibility state, stale saved observations, grouped words, reference identity, incomplete/unstable wording and unchanged plot timestamps. Tap-detail evidence wording now uses backend eligibility, not the old mobile frame-count “Clear/Limited” diagnostic.

## Reproducible commands

From the repository root, with the existing API environment:

```sh
BENMA_TRUST_RECORDINGS=/home/jacob/benma/services/api/var/utterance-evidence/presence-inventory.json services/api/.venv/bin/pytest -q services/api/tests -k 'not stream and not meaning_bytes'
PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q benchmark/pronunciation_v2/test_connected_speech.py benchmark/pronunciation_v2/test_connected_replay.py
PYTHONPATH=services/api/src services/api/.venv/bin/python benchmark/pronunciation_v2/utterance_evidence_replay.py
npm --prefix apps/mobile test
```

In `services/api`: `BENMA_TEST_POSTGRES=1 .venv/bin/pytest -q tests/test_perceived_postgres.py`, `.venv/bin/ruff check .`, `.venv/bin/mypy src`.

In `apps/mobile`: `npm run lint`, `npm run typecheck`, and `CI=1 npx --no-install expo export --platform web --output-dir /tmp/benma-utterance-web-export` / corresponding `android` export.

Local logs are under `services/api/var/utterance-evidence/`. Reports and saved replay results remain under this directory. Generated OpenAPI/TypeScript were regenerated with the repository's existing exporter.

## PostgreSQL and immutable evidence

Two parameterized integration checks cover warmup present/absent, duplicate perceived/raw-acoustic requests and duplicate target requests. They assert one acoustic invocation/run and demonstrate ASR persistence while the acoustic worker is held. Worker SQL sessions remain isolated from request-owned sessions.

The earlier sandboxed attempt could not connect to localhost. Authorized local access succeeded. After the continuation's execution environment lost `/tmp` state and the local server was stopped, the existing repository PostgreSQL container was started with `--pull never`; final checks passed. No image was downloaded. Tests create and drop uniquely named test schemas, not application data. An old concurrency fixture used invalid `b"fixture audio"`; it now uses the existing WAV helper so the unchanged presence guard can run. Another calibration mock incorrectly used a character end as the whole-waveform duration; its fixture duration now encompasses the saved frames. These are bounded test-fixture corrections, not changes to presence behavior.

New tests cover actual production Praat reuse across text/target/empty metadata, distinct persisted perceptions, full snapshot equality, raw preservation, deterministic digest/JSON replay, frozen nested frames, forbidden linguistic fields, exact projection ownership, punctuation, final frame, word grouping, unvoiced initials, rising/falling controls, coherent 54/60/70-Hz support, tail attrition, sparse evidence, discontinuities and the saved failure set. Existing target-revision tests now also compare typed tracks.

## Replay evidence and latency

152 regions in 35 recordings: 71 sufficient, 20 incomplete, 16 unstable, 45 insufficient. Speech-only classifiable observations: 50 before → 37 after. Named healthy controls: 3/3 preserved. Six negative controls and every available 120/200/400-ms negative window were replayed. The 61 locally sufficient accidental-silence windows are intentionally retained as the reason to keep comparison permission separate and disabled.

Final saved-region local medians/maxima:

| Operation | Median | Maximum |
|---|---:|---:|
| Projection | 0.0261 ms | 0.0825 ms |
| Eligibility | 0.0525 ms | 0.3288 ms |
| Existing gesture classification + gate | 0.5642 ms | 1.0412 ms |

Separate one-waveform production timing: 41.56-ms warm extraction, 7.54-ms typed construction, 0.59-ms serialization, 1.25-ms saved typed replay. Mobile comparison-policy execution on local Node: median 0.0000235 ms/call, maximum batch average 0.000734 ms/call over 100,000 calls. This is not physical-device rendering or end-to-end ASR latency. Existing concurrency is preserved, not newly introduced.

## Unrelated/execution limitations

The first unbounded API attempt stalled in an unchanged conversation streaming test and was interrupted. The final bounded suite explicitly excludes 22 streaming/meaning tests; no passing full-unbounded-suite claim is made and no unrelated streaming code was changed. Other Conversation/perception/workflow regressions run in the bounded API/mobile suites.

One native graph render test hit its existing 5-second timeout while mobile builds and other checks ran concurrently. The full mobile suite passed when rerun without build contention; no timeout was enlarged or assertion removed. Existing React test-renderer warnings are non-failing.

## Preservation and working tree

`preservation.json` verifies all **133 saved RMVPE artifacts** and **466 original frozen evidence artifacts** unchanged. The original 467-entry index also mentions a now-missing volatile Matplotlib font cache; this is explicitly recorded, not treated as changed audio/F0/salience/alignment/metrics. No evidence was regenerated to repair a checksum. The guard, guard service, readings, surface rules, warmup and route source hashes match the pre-pass snapshot.

The current Git state includes the substantial pre-existing uncommitted work. The existing deletion of `PronunciationFeedback.tsx` predates this pass and was not restored or discarded. New untracked files do not appear in ordinary `git diff --stat`; `git status --short` lists them. The final full outputs are in [git-state.txt](git-state.txt). No commit, push or deployment was performed.
