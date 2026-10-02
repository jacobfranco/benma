# Architecture update: connected speech v2

**TIMING TRUTH ≠ READING TRUTH ≠ REFERENCE PHONE EVIDENCE ≠ OBSERVED ACOUSTICS ≠ TARGET EXPECTATION.** Here “timing truth” means faithfully mapped provider evidence, not independently validated gold acoustic boundaries.

The change is confined to the research harness. Production Azure parsing, grading, reading rules, F0 extraction/selection thresholds, UI and deployment are unchanged.

| Concept | v2 representation | Permitted inputs |
| --- | --- | --- |
| Perceived identity | immutable `perception`; `unit.perceived_text`, character offsets | saved unknown-target perception |
| Provider timing | nullable `timing`, `timing_source`, `provider_timing` | exact perceived character sequence + provider grapheme and offsets |
| Reading | nullable pinyin/tone, status, alternatives, ambiguity, `context_text` | perceived clause, exact perceived word, existing phrase/grammar dictionary |
| Reference phones | `phones`, exact provider label/score/raw entry; mandatory `reference_label_not_observed_phone` semantics | accepted interval + independent resolved reading-base check |
| Observed acoustics | unchanged whole-recording `acoustics`; `unit.pitch` slices | saved timestamped measurements, accepted interval |
| Target expectation | `text_comparison`, optional `unit.target_comparison.expectation` | intended text, perceived text correspondence; only after perceived analysis |

## Timing acceptance

`grapheme_candidates(raw, perceived_text)` accepts no reading or target argument. It requires the full ordered provider-word lexical sequence to match the perceived alphanumeric sequence. Punctuation/space are ignored only for correspondence; original text and character offsets remain intact. It never searches forward to force a repeated word to fit.

For each word, it requires a finite positive nonnegative-start word interval and rejects Omission/Insertion. An explicit grapheme tier must have exactly one single Han grapheme per matched character, in exactly that order; extra, missing, duplicated/mismatched entries reject the word. Each interval comes directly from Azure ticks (10,000 ticks/ms), with the raw entry and JSON pointer preserved. Missing/invalid numeric timing leaves that character untimed. Nonmonotonic/overlapping spans or spans outside the word reject its entire tier. The only containment allowance is the **existing 1 ms word-boundary tolerance**; no interval is extended, clipped or interpolated.

The harness additionally requires positive unit durations ≤3 seconds, strict nonoverlap across accepted units, monotonically increasing unit indices, intervals within audio and nonoverlapping provider words. A cross-unit or word-order conflict conservatively clears accepted unit timing. Word evidence and complete raw response remain available even if units abstain. No confidence score or AccuracyScore is used to accept timing.

If no grapheme tier exists, an exact **single-character** provider word may retain its own interval, with source `azure_character_word`. A multi-character word is never split, nor segmented from phone counts or pinyin. This intentionally removes the research v1 phone-only multi-character fallback. Valid timing can coexist with unresolved reading and absent attached phones.

## Reference phone attachment

A phone can attach only when its full SAPI base matches an independently resolved perceived reading and its own interval exactly matches that accepted character interval. Multiple matches abstain. Tone digits are retained as provider reference labels, not independently measured tones or a lexical correction. Scores (nested or top-level provider shape) and the exact phone entry are retained. Unattached raw phones remain in `alignment.raw_response` and raw word evidence. Reading ambiguity never removes timing, and phone evidence never resolves a reading.

## Schema and compatibility

New output uses `connected-speech-v2` / `connected-probe-v2`, mapping `azure-exact-grapheme-v2`, context policy `perceived-word-context-v1`. The executable schema reader accepts explicitly labeled v1 and v2 and rejects mismatched schema/analysis versions. The original machine schema is archived as [connected-speech-schema-v1.json](../../../../benchmark/pronunciation_v2/connected-speech-schema-v1.json); [connected-speech-schema.json](../../../../benchmark/pronunciation_v2/connected-speech-schema.json) describes the current compatibility reader.

Additions: `unit.provider_timing` (provider word/grapheme, indices, raw JSON pointer, raw entry, validity), `reading.context_text`, `phone.raw_entry`, `replay` metadata and `study_annotations`. `Reading.status` remains its existing source, not confidence or truth. In v1 `alignment.words[].raw_provider_word` held the normalized whitelist; in v2 it holds the exact raw Azure word. This difference is explicit and versioned. Global `alignment.raw_response` is complete in both. V1 stored units are never silently rewritten in place; replay produces a new versioned artifact and keeps original schema/configuration/issues in its provenance metadata.

`replay_record` preserves recording ID, audio path/hashes/duration/provenance, perception including raw response and request configuration, Azure raw response/status, intended text and full acoustics. The CLI records SHA-256 of the original record bytes and pypinyin version. It creates a new directory and refuses overwrite. It cannot accept a new target or audio path. Study notes are separate user-report annotations, never labels used by mapping or acoustics.

All unit judgments remain **INSUFFICIENT EVIDENCE**. The model slot remains null. S13's target 广州 produces only a 广→贵 text substitution/expected target guǎng; perceived 贵州, its guì/zhōu readings, timing and reference phones remain independent of that target.
