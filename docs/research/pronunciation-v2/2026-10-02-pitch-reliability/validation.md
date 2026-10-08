# Validation — 2026-10-02

> **Superseded by the [Trust Pass](trust-pass.md).** The second real silence case exposed a periodic-background false accept. Current behavior adds post-ASR acoustic corroboration, removes default reference-tone labels, and keeps the primary pitch tracker. The content below records the earlier pass.

Continued the existing dirty `pronunciation-v2-research` working tree. Earlier V2
alignment, transport, generated schemas and perceived-graph changes were preserved.
No reset, stash, checkout, commit, push, deployment, live provider request, model
download or user-audio addition. Tracker experiments were completed once; the
continuation used saved results and only replayed the finished presence guard.

## Automated checks

| Check | Result |
|---|---|
| Focused speech-presence and sentence-tone-graph API tests | 46 passed |
| Bounded full API suite, including touched perception/pronunciation/workflow paths | 464 passed, 4 optional PostgreSQL skips, 5 known streaming cases deselected |
| Connected-speech and connected replay | 69 passed |
| Full mobile native/web suite | 25 suites, 308 tests passed |
| API Ruff lint | Passed |
| Ruff format for all 20 changed/new Python files | Passed |
| API mypy, using `services/api/pyproject.toml` | Passed, 75 source files |
| Mobile Expo lint / TypeScript | Passed |
| Web export / Android export | Both passed |
| `git diff --check` | Passed |

Commands (API commands from `services/api`, mobile commands from `apps/mobile`):

```sh
.venv/bin/python -m pytest -q tests/test_speech_presence.py tests/test_sentence_tone_graph.py
.venv/bin/python -m pytest -q -k 'not test_stream_orders_authoritative_interpretation_before_committed_reply and not test_stream_generation_failure_keeps_perception_and_rejects_other_account and not test_meaning_bytes_leave_server_while_generation_is_still_running'
.venv/bin/ruff check .
.venv/bin/ruff format --check <changed-and-new-Python-files>
.venv/bin/mypy src
npm run validate
CI=1 npx expo export --platform web --output-dir /tmp/benma-pitch-reliability/web
CI=1 npx expo export --platform android --output-dir /tmp/benma-pitch-reliability/android
```

Connected checks from repository root:

```sh
PYTHONPATH=. services/api/.venv/bin/python -m pytest -q benchmark/pronunciation_v2/test_connected_speech.py benchmark/pronunciation_v2/test_connected_replay.py
git diff --check
```

The five excluded cases comprise three parameterizations of the first streaming test
and one each of the next two. Their previously observed stalls were not repaired or
reported as passing. The separate new no-speech streaming preflight regression passes.
The four skipped PostgreSQL cases remain opt-in. Full-tree Ruff formatting still
reports **32 unrelated files**; those were left alone. Existing React test-renderer /
act-environment console warnings remain in the passing mobile log. An initial mypy
invocation from the repository root missed the API Python-3.12 configuration; the
correct API-directory invocation above passes.

## Presence guard replay and product integration

The exact saved R6 noise/click recording is rejected. All other nine original
recordings pass. Their 18 variants at 0.1× / 0.01× amplitude and nine real
provider-timed single-character excerpts pass: **37/37 expected decisions**.
Original-record guard latency was 3.0–15.8 ms on this machine. These excerpts use
provider timing, not independently annotated phonetic boundaries.

Committed tests use deterministic synthetic silence, near-silence, low stationary
noise, a click, quiet/short periodic stand-ins and sustained aperiodic activity.
Actual Mandarin sentences and character excerpts stay in the local replay, with
provenance in [results](results.md); no real audio enters the test repository.

Integration coverage verifies no successful upload/utterance or attempt on absence,
no provider call and no transcript on a rejected legacy perception, and no perceived
graph, attempt, conversation or streaming response from an old hallucinated record.
The old stored transcript itself remains unchanged. Mobile regressions cover rejection
at upload, thrown perception errors and failed perception resources; deferred perception
cannot start target assessment. Practice retains its target and allows a fresh recording;
Conversation gets no response. Valid target/perceived analysis completion orders stay
independent, with perceived evidence authoritative for the graph.

## Browser layout and truth checks

Offline Playwright Chromium ran at a Pixel 7 viewport and a 1100 px desktop viewport.
The temporary fixture route used saved T3, apple, 去吧 and 贵州 analysis plus a 35-cell
untimed sentence and a no-speech state. Network API calls were blocked. The route and
fixture JSON were moved out of the repository before final production exports.

Both viewports passed all five graph cases (7 / 6 / 4 / 2 / 35 cells), final-cell
reachability, equal cell widths, 34 px characters, new-result scroll reset to zero,
tap-state reset, no page overflow and no browser runtime errors. Trailing 雨/伞 exist
and their tap reports unavailable timing. More detail and Raw open. Silence has no
graph. Default technical copy is absent; target 广州 / heard 贵州。 renders 广 → 贵.
Screenshot inspection led to whole-cell initial viewport sizing and cell-start snapping.
Normal clipping during an active horizontal gesture remains native scroll behavior;
labels are neither ellipsized nor clipped inside their own cells.

Browser fixture silence is a UI-state check, not a microphone/provider integration test.
The API and workflow tests establish the rejection path separately. Native rendering
was checked by the native test suite and Android export, not a physical-device session.
The five-case live manual packet remains in the [development guide](../../../development/tone-graph-v2.md#five-case-final-manual-check).

Pitch tests preserve target independence, raw immutability, deterministic retained
selection, perceived identity independent of timing, punctuation handling and the S13
贵州/广州 boundary. Diagnostic collection yields the same display selection as the
uninstrumented path. All ten saved production frame lists equal offline re-extraction.
No new pitch filter or bridge was introduced.

## Local artifacts and decisions

`/tmp/benma-pitch-reliability/` contains `api-bounded.log`, `focused-final.log`,
`connected.log`, `mobile-final.log`, `mypy-final.log`, `touched-format.log`,
`all-format.log`, `web-export.log`, `android-export.log`, `browser.log`, both
`*-browser.json` reports and `phone-*.png` / `desktop-*.png`. `gate-replay.json`
contains all 37 decisions. `report.html` contains waveform, periodicity and pitch plots;
`audit.json`, `attrition.csv` and `tracker-metrics.csv` contain the completed bakeoff.
The `preview/`, `web/` and `android/` exports are local-only artifacts.

- **Pitch: KEEP CURRENT.** Existing selection/filtering also remains unchanged; no bridge.
- **No speech: BLOCKED** for the reproduced hallucination and tested paths. This is
  not a universal hallucination-prevention or calibrated VAD claim.
- **Product structure: YES**, ready for formal UI polish after the five-case manual
  smoke check. Missing 吧 pitch and the suspicious raw 州 branch remain acknowledged
  limitations; no missing evidence is fabricated.

After the manual checks pass, the only recommended next step is the formal UI polish pass.

## Trust Pass validation

Current results after the new periodic-background check, post-ASR corroboration,
reference-label removal, plot padding and cached-assessment guard:

| Check | Result |
|---|---|
| Final bounded API suite | 479 passed, 4 optional PostgreSQL skipped, 5 known streaming cases deselected |
| Final focused presence/graph/laboratory tests | 79 passed |
| Exact private audio replay | 67/67 expected decisions; both real false accepts rejected |
| Connected-speech/replay regressions | 69 passed |
| Full mobile native/web suite | 25 suites, 314 tests passed |
| API Ruff lint | Passed |
| Format check on 10 Trust Pass Python files | Passed |
| API mypy | Passed, 76 source files |
| Mobile Expo lint / TypeScript | Passed |
| Production web / Android exports | Both passed |
| Offline Chromium phone / desktop layout | Both passed; all five graph cases plus silence |
| `git diff --check` | Passed |

API command from `services/api`:

```sh
BENMA_TRUST_RECORDINGS=/tmp/benma-tone-trust/recordings.json .venv/bin/python -m pytest -q tests -k 'not test_stream_orders_authoritative_interpretation_before_committed_reply and not test_stream_generation_failure_keeps_perception_and_rejects_other_account and not test_meaning_bytes_leave_server_while_generation_is_still_running'
```

The local inventory enables the two exact-ID/SHA audio regressions; without it those
private-fixture tests skip. The repository contains no user audio. Synthetic hum and
transient regressions remain available without private fixtures. Tests verify rejection
before successful perception publication; empty product transcript after rejection;
legacy graph/attempt/Conversation/stream protection; cached target-assessment rejection;
retry preserving Practice target; anonymous syllable timing abstention; no primary-only
pitch fabrication; and original high-branch/gap preservation.

Mobile runs `npm run validate`. Production exports used installed Expo with
`CI=1 npx --no-install expo export --platform web` and `--platform android`, writing
under `/tmp/benma-tone-trust/`. Temporary preview files were removed before production
exports. Browser checks used actual saved latest analysis fixtures, intercepted API
requests and no provider calls. Equal widths, centered characters/plot boxes, missing
reference labels, explicit tap references, final-cell reachability, scroll reset,
More detail/Raw, no page overflow, no browser errors and silence state passed. This is
not a physical-device microphone test.

Known unrelated limitations: the same five previously stalled streaming cases were
excluded, not reported as passing. Four optional PostgreSQL tests were not enabled.
Existing React test-renderer/act warnings remain in successful test logs. Earlier
full-tree formatting debt was left untouched; the current check covers the ten Python
files changed in this Trust Pass. No failing test remains in the executed final suites.

Local final logs: `api-final.log`, `focused-final.log`, `mobile-final.log`, `connected.log`,
`ruff-final.log`, `format-final.log`, `mypy-final.log`, `web-export.log`,
`android-export.log`, `browser.log`; exact metrics in `forensics.json`, `audit.json`,
`fallback.json`, `gate-replay.json`, `performance.json`. Complete findings and decisions:
[Trust Pass](trust-pass.md).
