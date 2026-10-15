# Validation and checkpoint

**PRONUNCIATION CHUNKS V1 EARNED INTEGRATION.**

**READY FOR PHYSICAL CHUNK UX SMOKE.**

## Automated results

| Check | Result |
| --- | --- |
| Initial focused mobile chunk/workspace/PCM selection | 127 passed, five native/web suites |
| Final full mobile suite | **508 passed, 34 native/web suites** |
| Initial focused API candidate/readings/timing/projection selection | 174 passed |
| Final relevant API suite, also including perception truth and laboratory | **221 passed** |
| Full API suite with expected experiment defaults and local socket access | **607 passed, 67 skipped, 2 pre-existing failures** |
| Isolated HEAD source reproduction of those two failures | Same two failures reproduced |
| Mobile lint and TypeScript | Passed |
| API Ruff and mypy | Passed; 79 source files checked by mypy |
| Deterministic OpenAPI/DTO export | Both files unchanged across two successive generations |
| Web and Android exports | Passed; `/tmp/benma-chunks-web`, `/tmp/benma-chunks-android` |
| Chromium 320/390/412 × 844 | Passed; no horizontal overflow or page errors |
| `git diff --check` | Passed |

The full-suite exceptions are
`test_final_acoustic_calibration.py::test_api_target_revision_preserves_acoustic_evidence[1]`
and `[3]`. They request target reading `ma2`, which the current supported-reading contract
rejects with HTTP 422; the old test then indexes the error response as a target and raises
`KeyError: 'id'`. The same tests fail against an isolated `git archive HEAD` source copy
under `/tmp/benma-chunks-baseline`. Neither those tests nor the reading validator changed
in this pass. They were not weakened or deleted to claim a green full suite.

The first sandboxed full run was interrupted after stalling near the concurrency portion;
it also inherited the local experimental-tone flag, causing the previously documented
laboratory-default mismatch. The completed run used
`BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION=false` and
`BENMA_ENABLE_CATEGORICAL_TONE_JUDGMENT=false`, with local socket access. No `.env` or
production flag was edited. The 67 skips are opt-in PostgreSQL/private presence-corpus
checks. Tracker/VAD/gesture research bakeoffs were not rerun.

## Reproduction

From `apps/mobile`:

```sh
npm test -- --silent
npm run lint
npm run typecheck
npx expo export --platform web --output-dir /tmp/benma-chunks-web
npx expo export --platform android --output-dir /tmp/benma-chunks-android
```

From `services/api`, use the existing `.venv/bin` executables:

```sh
BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION=false .venv/bin/pytest \
  tests/test_pronunciation_chunks.py tests/test_perceived_speech.py \
  tests/test_readings_contours.py tests/test_observed_gesture_groups.py \
  tests/test_quantity_reference.py tests/test_pitch_projection_contract.py \
  tests/test_perception_truth.py tests/test_pronunciation_laboratory.py -q
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/python scripts/export_openapi.py
```

For the browser check, serve the web export on localhost, set `BENMA_WEB_URL` and
`PLAYWRIGHT_MODULE` to an existing Playwright install, and run
`apps/mobile/scripts/pronunciation-chunks-browser.cjs`. It requires the existing private
six-take viewer and canonical `89cee47e` audio; `BENMA_CHUNK_AUDIO` may specify that file.
The script verifies its SHA-256 against the saved physical fixture before playback.
All API/provider responses are intercepted. No user audio is copied into review outputs.

Logs use `/tmp/benma-chunks-*`. Screenshots and `review.json` are in
`/tmp/benma-chunks-review/`. These are local review artifacts, not a deployment.

## Regression coverage

- Exact four-expression whitelist and actual API/mobile candidate fixture parity.
- Quantity metadata, citation vs surface-tone separation, unresolved readings and saved
  overrides; no broad reading-phrase, neutral-particle, or classifier attachment.
- Exact offsets across punctuation, Latin text, digits, and unknown symbols.
- Ordered partition, repeated IDs, unknown/old API fallback, partial timing, synthetic
  timing, reversed bounds, and refusing to consume half a grouped timing unit.
- Existing ≥ .30 s visible-pause veto, short gaps, and no adjacency/F0-created chunks.
- Physical 这个 source indices **245–259 and 263–267**, all owned by 这; zero selected
  个 evidence. Source gaps and objects survive; graph equals constituent union.
- Gap-point exclusion, half-open endpoints, later-start overlap ownership, and unchanged
  common attempt Y scale.
- Canonical PCM equality for chunk and constituent crops, with zero padding or boundary
  mutation; saved grouped 雨伞 graph and playback remain identical.
- One default chunk button/panel, one details inspector, partial-pitch wording, and no
  individual 雨/伞 playback when internal timing is absent.
- Target changes/no target, 贵州 versus 广州, History reconstruction, New Attempt/reset,
  Clear target, collapsed Conversation, and the existing Practice/entry/audio suites.

The pre-existing physical projection tests remain unchanged and still cover the older
API/no-candidate path. New tests cover those same original timing units under the chunk
layer. This preserves the earlier evidence investigation rather than replacing it.

## Responsive and accessibility review

| Width | 我想买这个 | Longer phrase | Result |
| --- | --- | --- | --- |
| 320 px | One compact row; 这个 one button | Three chunk rows; whole-recording action wraps normally | No horizontal overflow; footer remains fixed; details scroll |
| 390 px | One compact row | Three chunk rows | No horizontal overflow; one reusable detail panel |
| 412 px | One compact row | Three chunk rows | No horizontal overflow; target/footer controls remain compact |

The longer phrase is 我想买这个雨伞和那个雨伞再要一个苹果, a clearly labelled layout
fixture. Screenshots for the primary chunk at all three widths, long layouts at all
three widths, and both constituent inspectors were visually reviewed. The graph shows
the retained 这 fragments and empty trailing 个 interval at all widths.

Chromium checks Enter/Space, explicit web pressed state, one visible selection target,
44×48 minimum chunk hit areas, focus containment/Escape, chunk and constituent playback,
quantity/grouped-word playback, repeated lifecycle transitions, untargeted Practice,
History, and collapsed Conversation. The browser review caught and fixed missing web
selection state without changing native selected semantics. VoiceOver/TalkBack and
actual phone listening remain untested.

## Known limits

- Four reviewed expressions only; missed useful words/classifiers are intentional.
- Clients receiving old API responses use singleton/group fallback until they receive
  the additive candidates. Old saved data without `yi_quantity` cannot infer it afresh.
- Existing grouped timing can be longer than a desirable practice chunk; it remains
  indivisible until trustworthy internal timing exists.
- The pause threshold is the established visual separator, not newly validated prosody.
- History remains session-local. Policy V1 is stable within a saved response; a future
  policy migration must be explicit and cannot be silently accepted by the V1 client.
- Partial pitch reports coverage, not correctness. The existing energy/gesture issues
  remain separate; chunking neither repairs nor conceals them.
- No live provider/device integration, physical smoke, or deployment was performed.
- Full backend suite retains the two baseline failures explained above.

## Physical smoke checklist — pending user test

1. Record 我想买这个 and confirm 我 / 想 / 买 / 这个 when accepted timing permits.
2. Tap 这个; confirm one detail panel and whole-这个 playback.
3. Inspect the combined graph: only real retained pitch, gaps preserved. The saved
   fixture has missing 个 pitch; a new recording may truthfully have different evidence.
4. Open More Details; inspect 这 reading, original timing, exact playback, and graph.
5. Inspect 个 independently; missing retained pitch must remain missing where applicable.
6. Try 那个 and quantity-use 一个; verify chunk playback and preserved reading context.
7. Try 雨伞; an accepted timing group must not offer invented 雨/伞 exact playback.
8. Make an untargeted attempt and verify the same chunk policy.
9. Use New Attempt: active chunk disappears, target/history remain, recording starts.
10. Reopen History: the prior candidate plan, timing, playback, and graph return.

**One next step:** run this phone smoke and report any chunk-selection/playback discrepancy.
