# Validation and reproducibility

**This is a completed bounded audit with an unresolved product blocker, not a passing fix.** New regression tests explicitly expect the current known failures. Their XFAIL status must not be interpreted as acceptance of the shipping requirement.

## Executed checks

| Check | Result |
| --- | --- |
| Focused presence suite, all private corpus cases enabled, including streamed preflight | **72 passed, 11 strict xfailed**, 6.87 s |
| Bounded backend API suite, including acoustics/audio, perception, tone graph, pronunciation/Practice, Conversation, concurrency and presence | **573 passed, 4 opt-in PostgreSQL skipped, 25 deselected, 10 strict xfailed**, 36.36 s |
| Actual local PostgreSQL duplicate/concurrent perceived and target analysis, warmup on/off | **4 passed**, 1.20 s; isolated temporary schemas |
| Connected-speech and connected replay | **69 passed**, 1.04 s |
| API-tree Ruff | Passed |
| New audit script + corpus tests Ruff | Passed |
| New Python files format check | **2 passed** |
| Broad API source/tests Python format check | **25 pre-existing files would reformat**, 87 already formatted; unchanged failures left alone |
| Backend strict mypy | **78 source files passed** |
| JSON report artifacts parse | Passed |
| `git diff --check` | Passed |
| Mobile generated schema/typecheck | Not applicable: no API semantics, schemas, mobile, or production changes |

The bounded selection excludes `stream` and `meaning_bytes`, matching the prior pass's documented streaming-hang boundary. It is not a full unbounded suite claim. The new focused suite separately executes **all four presence-gate paths**, including stream preflight, for the three persisted negatives. PostgreSQL initially could not connect from the network sandbox; the same authorized local-only tests passed outside it. No live provider was used.

The broad format failures occur in unchanged assistant-generation/speech, auth/config, contextual interpretation, database models, speech-provider/synthesis files and existing tests. No formatting churn was applied. This pass added only research artifacts and focused private-corpus tests; it did not alter those files.

## Eleven explicit remaining failures

- Six negative rejection requirements: accidental silence, stored clicks, and the four saved non-speech padding excerpts.
- One language-independence requirement: the existing periodic-negative result changes when Han-count metadata is removed/shortened.
- Four integration requirements: accidental silence escapes Practice target creation, Free Practice speech analysis, Conversation, and streamed Conversation preflight.

The negative assertions use **strict XFAIL limited to assertion failure**; the integration cases use **strict XFAIL limited to a named gate-escape sentinel**. The sentinel runs immediately **after the real existing guard accepts**, stopping optional downstream work. Unexpected exceptions are not swallowed as expected failures. When a future guard correctly returns 422/no_speech, these tests become XPASS failures until the marker is removed. No test silently accepts the newest recording as correct speech.

Historical original and periodic negatives are tested through all four paths. They produce 422/no_speech, no attempt, no perceived graph, no Conversation turn, and no interpreter/generator call; saved transcript evidence survives. Two different intended targets yield the same rejection. Existing normal-flow API tests continue passing. Real-positive corpus checks exercise the production guard on all 37 waveforms/excerpts with absent, empty, nonsense and changed-Chinese transcript metadata; the normal-flow suite's downstream providers remain fixtures/mocks, not paid/live services.

The immutable-evidence regression loads frozen production acoustic JSON, checks **all 61 locally sufficient accidental-negative windows**, calls presence independently, and compares typed pitch JSON before/after. It also checks a separately loaded original-silence pitch track survives an actual presence rejection unchanged. No rerun of another tracker or acoustic eligibility edit was used.

## Reproduce

From `/home/jacob/benma`, using the existing API environment and existing private waveforms:

```sh
PYTHONPATH=.:services/api/src services/api/.venv/bin/python benchmark/pronunciation_v2/speech_presence_audit.py
BENMA_PRESENCE_CORPUS=1 BENMA_TRUST_RECORDINGS=/home/jacob/benma/services/api/var/utterance-evidence/presence-inventory.json services/api/.venv/bin/pytest -q services/api/tests/test_speech_presence.py services/api/tests/test_presence_regression_corpus.py --tb=short
BENMA_PRESENCE_CORPUS=1 BENMA_TRUST_RECORDINGS=/home/jacob/benma/services/api/var/utterance-evidence/presence-inventory.json timeout 120 services/api/.venv/bin/pytest -q services/api/tests -k 'not stream and not meaning_bytes' --tb=short
PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q benchmark/pronunciation_v2/test_connected_speech.py benchmark/pronunciation_v2/test_connected_replay.py
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/speech_presence_audit.py services/api/tests/test_presence_regression_corpus.py
services/api/.venv/bin/ruff format --check benchmark/pronunciation_v2/speech_presence_audit.py services/api/tests/test_presence_regression_corpus.py
git diff --check
```

In `services/api`:

```sh
BENMA_TEST_POSTGRES=1 timeout 35 .venv/bin/pytest -q tests/test_perceived_postgres.py --tb=short
.venv/bin/ruff check .
.venv/bin/ruff format --check src tests
.venv/bin/mypy src
```

The broad format command intentionally reports the existing failures. Logs are in `services/api/var/speech-presence/`; [portable summaries](validation-output.txt) record the observed outputs. The audit does not silently download missing inputs; it verifies manifest hashes. Exact excerpts are reconstructed in memory from their hashed parent waveforms, so no new recording or synthetic speech is needed. Without `BENMA_PRESENCE_CORPUS=1`, private-audio tests are explicitly skipped.

The comparison figures use existing FFmpeg filters, not a neural image generator or another F0 tracker. Example (repeat for the five labelled identities in `figures/`):

```sh
ffmpeg -v error -i services/api/var/f0-foundation/audio-links/silence_accidental.wav -lavfi 'showspectrumpic=s=1200x600:legend=1:scale=log:color=intensity:win_func=hann:fscale=lin:start=0:stop=4000' -frames:v 1 /tmp/silence-spectrum.png
ffmpeg -v error -i services/api/var/f0-foundation/audio-links/silence_accidental.wav -lavfi 'showwavespic=s=1200x180:colors=0x216a94:scale=lin' -frames:v 1 /tmp/silence-waveform.png
```

Waveform plots use each recording's display normalization; spectral images support qualitative temporal/harmonic inspection. Numerical comparisons come from the explicitly defined DSP measurements, not image-color or waveform-height comparisons.

## Preservation and scope

[Preservation receipt](preservation.json): all **162 snapshotted production/mobile source files** and **893 prior evidence files** are unchanged, with none missing. This includes presence, its callers, pitch types/evidence/eligibility, reference logic, audio assets and saved F0/alignment/provider evidence. There was no database migration or application-data mutation. PostgreSQL checks create/drop their isolated test schemas only.

The current branch remains `pronunciation-v2-research`. The large initial uncommitted working tree, including the pre-existing mobile file deletion, is preserved. The only pass additions are:

- `benchmark/pronunciation_v2/speech_presence_audit.py`
- `services/api/tests/test_presence_regression_corpus.py`
- this research directory, containing the requested five reports, hashes, measurements, plots and validation records

Ignored local scratch/log/crop files live under `services/api/var/speech-presence/`. No production implementation was promoted. No commit, push or deployment occurred.

[Full final Git outputs](git-state.txt) include the pre-existing work. Ordinary `git diff --stat` omits untracked additions; `git status --short` shows this pass's new files and report directory.
