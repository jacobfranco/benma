# Validation

Branch: `pronunciation-v2-research`. All implementation changes are confined to connected-speech research modules, tests, schema and documentation. Production source is unchanged. No live OpenAI/Azure calls, other network inference, user rerecording, training, model experiment, F0/threshold tuning, UI change, deployment, commit or push.

## Completed checks

| Check | Result |
| --- | --- |
| Focused connected speech + replay tests | **69 passed** (final run after Markdown separation) |
| Existing pronunciation/perceived/reading/evidence API tests | **181 passed** |
| Additional bounded recon API selection | **104 passed, 5 deselected** |
| Existing pronunciation calibration report tests | **2 passed** |
| Completed test total | **356 passed; 0 failed** |
| Ruff check: six touched/new Python files + unchanged production pronunciation package | passed |
| Ruff format check: same scope | **25 files already formatted** |
| Generated schema equals `Record.model_json_schema()` | passed |
| Archived v1 schema byte-equal to HEAD's original schema | passed |
| All four final reports equal `markdown(saved_v2_record)` | passed |
| Coverage tables/JSON recomputed from original and final record units | passed |
| Original recording IDs/audio/perception/raw Azure/intended text/acoustics preserved | passed for all four |
| `git diff --check` + untracked text whitespace check | passed |
| Staged files / staged audio | **none** |

There are **no newly failing or observed unrelated failing tests** in the completed selections. Five unrelated conversation-streaming cases were deliberately excluded from the additional bounded command because the prior [recon validation](../2026-10-01-connected-speech-recon/validation.md#existing-streaming-test-limitation) records a reproducible timeout there. That historical limitation remains unverified in this pass; it is not reported as a new failure or as fixed. No unrelated streaming code was changed. This is not a claim that the entire repository suite is green.

## Commands

Use the existing API environment, without syncing dependencies or contacting providers:

```sh
services/api/.venv/bin/python -m pytest \
  benchmark/pronunciation_v2/test_connected_speech.py \
  benchmark/pronunciation_v2/test_connected_replay.py -q

services/api/.venv/bin/python -m pytest \
  services/api/tests/test_pronunciation_corrections_ownership.py \
  services/api/tests/test_pronunciation_diagnostic.py \
  services/api/tests/test_pronunciation_laboratory.py \
  services/api/tests/test_live_pronunciation.py \
  services/api/tests/test_perceived_speech.py \
  services/api/tests/test_readings_contours.py \
  services/api/tests/test_tone_evidence_region.py -q

# Additional files from the established recon validation command, excluding
# the five previously documented streaming stalls; no duplicate test files.
timeout 60s services/api/.venv/bin/python -m pytest \
  services/api/tests/test_perception_truth.py \
  services/api/tests/test_acoustic_frontend.py \
  services/api/tests/test_upstream_evidence.py \
  services/api/tests/test_speech_concurrency.py \
  services/api/tests/test_provider_adapters.py \
  services/api/tests/test_final_acoustic_calibration.py \
  -q -k 'not test_stream and not test_meaning_bytes'

services/api/.venv/bin/python -m pytest tests/test_pronunciation_calibration_report.py -q

services/api/.venv/bin/ruff check \
  benchmark/pronunciation_v2/connected*.py \
  benchmark/pronunciation_v2/test_connected*.py \
  services/api/src/benma_api/pronunciation
services/api/.venv/bin/ruff format --check \
  benchmark/pronunciation_v2/connected*.py \
  benchmark/pronunciation_v2/test_connected*.py \
  services/api/src/benma_api/pronunciation

git diff --check
git diff --cached --name-only
git diff --stat
git status --short
```

Local test logs are `/tmp/benma-mapping-focused-tests.log`, `benma-mapping-api-tests.log`, `benma-mapping-broader-tests.log` and `benma-mapping-pronunciation-tests.log`. The initial focused run caught expectations tied to the old phone-only mapping and an annotation-application omission; both were corrected before the final passing run. These were development failures, not suppressed pre-existing failures.

## Regression coverage

Tests exercise explicit timing with unresolved pinyin; exact grapheme/word identity; no pinyin-based identity substitution; no search-forward mapping of repeated words; missing intervals despite available phone spans; no equal splitting or phone-count segmentation; missing/extra/mismatched graphemes; invalid numeric values, containment, order and overlap; omitted/inserted provider words; exact multiple-character mapping of real excerpt structures; stricter phone attachment and retained raw scores; perceived phrase context independent of target; all requested phrase timing cases with dictionary gaps retained; S13 贵州/广州; saved-frame slicing; Markdown showing timing with unresolved reading; schema snapshot/v1 compatibility; preserved source hashes/provenance and overwrite refusal.

The offline replay test blocks socket connections and mocks provider/audio/Praat entry points to fail if called. It supplies a nonexistent audio path: successful replay therefore cannot depend on re-reading a recording. Existing production acoustic plumbing tests may generate temporary test signals; they do not re-extract these four recordings or provide learner phonetic evidence. No trained isolated-tone model is run.

## Artifact review

Only derived reports, summaries, notes and a **25,573-byte** mapping excerpt fixture are included as new source-tree candidates; full real records remain ignored local data. The excerpt is labeled derived real provider evidence with source hashes. It contains no audio, raw ASR confidence/logprob payload or whole-recording F0 trace. The archived machine schema is not a new raw study record. `git diff --stat` naturally omits untracked new files, which are separately listed by `git status --short`; no staging was used to change that display.

This pass validates evidence mapping/replay and provenance, not acoustic boundary gold, segment detection, Mandarin tone accuracy or pronunciation grading.
