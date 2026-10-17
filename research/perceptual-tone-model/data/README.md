# Canonical research manifest

[`dataset.schema.json`](dataset.schema.json) defines one v2 JSON object per syllable
in a UTF-8 JSONL dataset. The root-level **v1** schema and Stage-0 files are immutable
baseline archives, consumed only through the adapter; new experiments use v2.
Do not edit the pinned v1 schema, evaluator, inputs or baseline manifest.

| Object / fields | Meaning |
| --- | --- |
| `schema_version`, `dataset_version` | Contract version `2.0.0` and collection/version identifier. Every row in one manifest has the same dataset version. |
| `example_id`, `recording_id`, `utterance_id`, `speaker_id`, `partition` | Persistent identities. A speaker pseudonym spans all sessions/recordings. Unknown is null. No account/recording ID is evidence of speaker identity. |
| `utterance`, `target` | Full text; target Hanzi, nullable pinyin, zero-based syllable index/member indices, unit kind, original start/end seconds. Repeated characters are located by index and time. |
| `expected` | Lexical/surface tone, acceptable family set, surface rule, previous/next tone and syllable, neutral context, nullable phrase position. Lexical tone 0 identifies a neutral target; `neutral_context` can describe a neighboring dependency. |
| `audio`, `source` | Canonical source WAV reference/hash/sample rate and frozen analysis reference/hash/ID. Relative references resolve from repository root. |
| `context_window` | Preserved original context timing, never overwritten by a different window experiment. |
| `windows.target/local/wide` | Generated WAV reference, file/PCM SHA-256, exact original start/end samples and seconds, sample rate. `{}` before preflight. |
| `deterministic` | Complete unchanged output of the frozen evaluator, including reliability, supports/margins, family, clarity, probes, gesture, learner grade, coaching, contours and structural/prosodic evidence. Nullable before replay. |
| `annotations` | Append-only raw judgments, optional perceived family/confidence/notes, annotator and judgment IDs, timestamp with timezone, rubric version, revision number and explicit `supersedes`. |
| `aggregate` | Nullable derived consensus, counts, active/raw judgment counts, disagreement count, normalized entropy, unanimity, exclusion reason, aggregation config hash. Training always recomputes this from raw judgments. |
| `provenance` | `stage0`/`pilot`, verified/unknown/temporary-fixture speaker identity, none/human/mock-test label provenance, notes. Scientific runs reject fixture identities and mock judgments. |

Times are half-open `[start,end)` in the original canonical recording. Crops use
floor(start × rate), ceil(end × rate), then clamp context at recording bounds.
No alignment, F0 or segmentation is recomputed. Inputs must be mono PCM16 WAV;
the initial encoder recipes require 16 kHz. Preflight rejects missing/truncated
audio, checksum/sample-rate mismatches and invalid bounds. Use the frozen upstream
pipeline's canonical audio, rather than silently converting a mismatched source.

`init` imports a v1 frozen analysis-backed dataset and an explicit JSON
`{recording_id: persistent_speaker_pseudonym}` registry. It does not infer speaker
identity. It preserves unknown pinyin/phrase-position fields as null. Fill these
from verified transcript/context metadata when available; do not infer them from
the listener's answer. The baseline exporter checks ownership, utterance, timing,
analysis hash and lexical/acceptable-family expectations against saved evidence.
Context-only enrichment is researcher-supplied inference-time metadata: audit it
before freezing the dataset. This pass does not invent an ASR/export endpoint.

One recording must have one identified speaker in this pilot. Resolve duplicate
aliases and prior-corpus overlap before assigning pseudonyms. Timing groups are
preserved in archives but cannot enter syllable training partitions. New collections
should use complete saved analyses, not the historical-row compatibility adapter.

The executable schema check uses the existing, pinned mobile AJV installation.
Additional Python checks enforce timing, global judgment IDs, revision chains and
provenance relationships. Schemas reject unknown fields. Large/generated datasets
and WAVs go in ignored `data/generated/`; never distribute private source paths or
the private packet mapping to listeners.
