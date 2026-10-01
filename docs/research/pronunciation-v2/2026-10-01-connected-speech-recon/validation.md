# Validation — 2026-10-01

Scope: research-only new files; production application modules, existing model code and Experiment #3 artifacts are unchanged. No raw recording was requested, fabricated as learner evidence, staged, or committed. No provider credentials were used and no live request was sent. No training, tuning, deployment, commit or push.

## Results

| Check | Result |
| --- | --- |
| New connected-speech tests | **31 passed** |
| Relevant existing API pronunciation/perception tests | **279 passed** across completed runs; five unrelated conversation-streaming cases remain unverified (see below) |
| Selected mobile workflow/Practice/transcript/verdict suites | **4 suites, 59 tests passed** |
| Ruff check on all three new Python files | passed |
| Ruff format check on all three new Python files | passed |
| Pydantic record serialization/read validation + generated JSON schema snapshot | passed in focused tests |
| Fixture CLI JSON/Markdown equivalence and refusal to overwrite | passed in focused tests |
| Production canonicalization + Praat signal plumbing | passed with temporary generated sinusoid and mocked provider transports |
| `git diff --check` and additional untracked-file whitespace checks | passed |
| Staged paths / staged audio | none |

The waveform in the plumbing test is generated under pytest's temporary directory, not saved as a study recording. It verifies ffmpeg/Praat availability, timestamps, hashes and port inputs. It cannot validate Mandarin perception or connected-speech accuracy. The fixture contains invented **structural provider JSON**, explicitly labeled synthetic and without an audio hash; it is not a fabricated live provider capture.

## Commands

From repository root:

```sh
services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_connected_speech.py -q
services/api/.venv/bin/ruff check \
  benchmark/pronunciation_v2/connected_schema.py \
  benchmark/pronunciation_v2/connected_speech_probe.py \
  benchmark/pronunciation_v2/test_connected_speech.py
services/api/.venv/bin/ruff format --check \
  benchmark/pronunciation_v2/connected_schema.py \
  benchmark/pronunciation_v2/connected_speech_probe.py \
  benchmark/pronunciation_v2/test_connected_speech.py
git diff --check
git diff --cached --name-only
```

Existing API selection:

```sh
timeout 90s services/api/.venv/bin/python -m pytest \
  services/api/tests/test_perception_truth.py \
  services/api/tests/test_perceived_speech.py \
  services/api/tests/test_readings_contours.py \
  services/api/tests/test_tone_evidence_region.py \
  services/api/tests/test_acoustic_frontend.py \
  services/api/tests/test_upstream_evidence.py \
  services/api/tests/test_pronunciation_diagnostic.py \
  services/api/tests/test_pronunciation_laboratory.py \
  services/api/tests/test_speech_concurrency.py \
  services/api/tests/test_provider_adapters.py \
  services/api/tests/test_final_acoustic_calibration.py \
  services/api/tests/test_live_pronunciation.py \
  -q -k 'not stream and not meaning_bytes'
# 264 passed, 20 deselected. "stream" also matches "upstream": run those separately.
timeout 60s services/api/.venv/bin/python -m pytest \
  services/api/tests/test_upstream_evidence.py -q
# 15 passed; combined completed coverage: 279 of the original 284 selected cases.
```

From `apps/mobile`:

```sh
npm test -- --watch=false --runTestsByPath \
  src/__tests__/sharedWorkflows.web.test.ts \
  src/__tests__/practiceScreen.test.ts \
  src/__tests__/transcriptFeedback.test.ts \
  src/__tests__/learnerVerdict.test.ts
```

No mobile/API source was modified. These suites check the recon's relevant existing paths as regression evidence; there was no need to regenerate app/API contracts or run repository-wide lint. No claim is made that broader repository lint is clean.

## Existing streaming test limitation

The initial full selected API run stalled at conversation streaming and was interrupted. A bounded diagnostic rerun of `test_pronunciation_laboratory.py` and `test_speech_concurrency.py` with `-vv -o faulthandler_timeout=20` reproduced the stall at:

`test_stream_orders_authoritative_interpretation_before_committed_reply[preserve]`

The dump showed the main thread waiting in asyncio/select during the test client's POST; provider executor threads were idle. The diagnostic process reached the external 90-second timeout (exit 124), after the first 21 tests passed. This is in unchanged production/test code; this pass has not established the underlying cause, so it is reported as unresolved, not dismissed as a proven environment defect.

The completed API run excludes that test's preserve/infer/clarify variants, `test_stream_generation_failure_keeps_perception_and_rejects_other_account`, and `test_meaning_bytes_leave_server_while_generation_is_still_running`: **five cases**. Only the preserve case's timeout was individually reproduced. All other cases in the 284-case selection completed in the two runs above. No unrelated streaming code was changed to make the suite pass.

## Focused assertions

The new tests cover immutable/detached perception snapshots; optional target; 广州/贵州; deterministic substitution/insertion/deletion and punctuation-aware offsets; ambiguous repeated-text correspondences; absent/invalid/overlapping/out-of-audio timing; exact native tokens; retained multi-character word spans; no equal splits; full-pinyin SAPI mapping and rejection of partial/mismatched labels; ambiguous readings; neutral 0; existing third-tone/不/一 rules; target-independent raw pitch/reading/quality/phones; F0 missingness/instability; configurable clipped context; no unlabeled model evidence; abstention; malformed provider evidence; fixture-reference mismatch; schema stability; JSON/Markdown consistency; no audio output or staged audio.

## Unperformed empirical validation

No live sentence ASR/Azure run, natural-speech boundary audit, native annotation or model inference. The manual packet is the next pass. No accuracy metric is computed from these synthetic tests. Timing and F0 plumbing work does not imply correct Mandarin tone or segment diagnosis.
