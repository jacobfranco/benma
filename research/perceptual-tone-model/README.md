# Perceptual tone model — frozen deterministic baseline

Checkpoint date: 2026-10-15. This directory is offline research only. No learned
model is integrated or trained, and no production files are changed by this pass.
The existing uncommitted pronunciation implementation is the baseline.

- [ARCHITECTURE.md](ARCHITECTURE.md): complete pipeline, stage ownership, invariants,
  grading philosophy and the remaining perceptual diagnosis failure.
- [EXPERIMENT.md](EXPERIMENT.md): labels, annotation rubric, input groups, four
  comparison models, speaker-disjoint metrics and staged collection plan.
- [dataset.schema.json](dataset.schema.json): JSON Schema draft-07 for each JSONL
  record before annotation, after annotation and after deterministic replay.
- [evaluate.cjs](evaluate.cjs): source-verified production replay and JSONL exporter.
- [baseline-manifest.json](baseline-manifest.json): working-tree file SHA-256s,
  dependency/runtime provenance and baseline scope. Its own SHA-256 identifies
  each exported deterministic result.
- [stage0.dataset.jsonl](stage0.dataset.jsonl): 53 historical units plus 10 newest
  physical units, with audio hashes/references and empty listener annotations.
- [stage0.baseline.jsonl](stage0.baseline.jsonl): frozen deterministic outputs for
  those 63 units. This is an engineering replay, not perceptual ground truth.
- [verify_measurements.py](verify_measurements.py): existing historical/physical
  replay with writes redirected to temporary files; canonical WAV verification.
- [test_evaluate.cjs](test_evaluate.cjs): export parity, evidence/identity rejection,
  raw disagreement preservation and speaker-leakage checks.
- [validation.json](validation.json): commands, results, output hashes and scope.

## Reproduce

Run from the repository root with the existing mobile dependencies installed.
The exporter uses the existing TypeScript replay adapter and local AJV dependency;
it needs no provider calls, database, Python environment or model downloads.

```sh
node research/perceptual-tone-model/evaluate.cjs \
  research/perceptual-tone-model/stage0.dataset.jsonl \
  /tmp/benma-stage0-replay.jsonl
cmp research/perceptual-tone-model/stage0.baseline.jsonl /tmp/benma-stage0-replay.jsonl
node --test research/perceptual-tone-model/test_evaluate.cjs
node --test benchmark/pronunciation_v2/test_conservative_grading_audit.cjs \
  benchmark/pronunciation_v2/test_natural_acceptance_audit.cjs \
  benchmark/pronunciation_v2/test_natural_family_audit.cjs \
  benchmark/pronunciation_v2/test_measurement_audit.cjs \
  benchmark/pronunciation_v2/test_tone_feedback.cjs
PYTHONPATH=. services/api/.venv/bin/python research/perceptual-tone-model/verify_measurements.py
git diff --check
```

For the six focused mobile suites, run in `apps/mobile`:

```sh
npm test -- --runTestsByPath \
  src/__tests__/conservativeLearnerGrade.test.ts \
  src/__tests__/learnerPitchGrade.test.ts \
  src/__tests__/chunkPitchGrade.test.ts \
  src/__tests__/toneClassification.test.ts \
  src/__tests__/pitchRobustness.test.ts \
  src/__tests__/toneFeedbackWorkspace.test.ts
```

Output paths must be new: the exporter refuses overwriting any existing file.
The measurement check needs the already-local private WAVs and saved snapshots
under `services/api/var`; these are not copied or published by the checkpoint.
Without private audio, JSONL replay still works, but it is not a fresh F0 extraction.
No broad backend/browser suite is required for this documentation/research pass.

## Baseline identity and future datasets

The manifest pins production source, dependency locks, prior frozen inputs,
offline replay helpers, schema and this exporter. Startup verifies every pinned
file and fails on any changed/missing file. Preserve this working tree and its
private audio separately before future production edits; hashes detect drift
but are not a source-code backup. **Checking out HEAD alone is insufficient**,
because the frozen implementation includes existing uncommitted/untracked files.
Do not regenerate the manifest to make a changed grader appear to be this baseline.

For later labeled research, create one schema-valid JSONL record per syllable
using `source.kind: "analysis"`, a saved `PerceivedSpeechAnalysis` JSON object
(or array), its SHA-256 and analysis ID. Supply recording/utterance/speaker IDs,
audio reference/hash, original syllable index, exact span, context window and
lexical/surface information. `source.path` and local `audio.reference` are relative
to repository root (absolute local paths also work for source files). IDs are
opaque; an analysis ID is not a recording or speaker ID. The adapter locates units
by index, not character text, so repeated syllables are unambiguous.

Run the same exporter command with the new dataset path. It calls existing
`pronunciationChunks`/`gradeChunkPitch` and the production family/grading code,
overwrites only the in-memory `deterministic` field, preserves raw annotations,
and writes a new output file. Source analysis hashes, utterance, timing, ownership,
lexical/surface tones and contextual acceptable families must match; inconsistent
inputs fail. The adapter does not call ASR/alignment/F0 extraction for new audio.
Capture those as a saved analysis using the pinned upstream implementation first,
record the provider/model/configuration and audio provenance, then replay. External
ASR/provider responses are not guaranteed repeatable; saved evidence is the exact
reproduction boundary. No production export endpoint or DB mutation is introduced.

`historical_row` is only the compatibility adapter for the saved 53-unit corpus.
It preserves the historical context fields exactly, including absent index data;
it must not be silently upgraded to newer full-analysis contextual behavior.
Historical grouped timing is exported as `timing_group` with member indices and
GRAY; it is excluded from syllable-level learning. Historical `chunk` is null
because that legacy replay did not evaluate chunk aggregation. For new data use
full analyses. The schema allows grouped records only outside training partitions.

## Record contract

Each record contains example/recording/utterance/speaker IDs; utterance text;
target syllable and zero-based index/members; canonical timing span in seconds;
audio reference/hash and `span_id`; context window; lexical/surface tones and
acceptable families; previous/next tones and neutral/position context; source
analysis provenance; raw annotator judgments; disagreement counts and optional
adjudication; and current deterministic outputs. Null means unknown/not available,
not zero or an inferred annotation. All time spans are half-open `[start, end)`.
Stage 0 windows are clipped target ±0.5 seconds; they are an extraction proposal,
not labels. No cropped audio is written here.

`deterministic` includes evidence reliability and saved eligibility, structural
reliability, observed family and numbered/unclear/unavailable decision, all four
family supports, winner/runner-up supports, acoustic/acceptable/runner-up margins,
clarity, probe votes/count/agreement, gesture strength, learner grade/reason/message,
coaching, chunk grade and constituent role when applicable. It also keeps the
complete shape/acoustic/expectation objects, duration, retained normalized F0
segments and projection/frame references. Historical points use `{index,t,st}`;
full-analysis points retain production `{timestamp_seconds,normalized_semitones}`.
There is no measurement rounding or new normalization in the exporter. Original
raw/candidate data remains in the linked saved analysis/track rather than being
rewritten into a production schema.

Speaker identity is unknown for these Stage 0 fixtures; recording/account IDs are
not substituted for speakers. The schema rejects unknown speakers, missing
judgments and timing groups in train/validation/test. The evaluator rejects
cross-partition speaker overlap within its input, inconsistent identities for an
audio hash, duplicate example IDs and mismatched vote counts. Run it on the full
split dataset together. Cross-file/session alias resolution and local audio hash/
sample validation for new collections belong to the next preflight command.

The acceptability choices are `acceptable`, `borderline`, `incorrect`, `ungradable`;
optional perceived tone is `T1/T2/T3/T4/unclear` or null. Neither the deterministic
grade nor collection intent supplies native-listener labels. Stage 0 has zero
listener judgments and must not be reported as 63 labeled training examples.

The exact next implementation step is the offline annotation-packet/preflight
command described in [EXPERIMENT.md](EXPERIMENT.md), followed by pilot annotation,
a speaker split, frozen embedding extraction and small classifier comparisons.
