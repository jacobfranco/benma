# Grouping audit and architecture

## Existing representations

| Layer | Current representation and authority |
| --- | --- |
| Perceived text | Persisted `PerceptionRun.transcript` / analysis `alignment_reference_text`; target and contextual interpretation are separate |
| Perceived characters | `PerceivedSyllable`: index, exact character offsets, characters, saved readings, surface expectations, optional timing/projection/eligibility |
| Reading resolution | `readings.resolve_run`: longest pypinyin phrase matches, reviewed supplement, narrow grammar rules, dictionary options or unresolved; phrase span boundaries are not serialized |
| Expected surface tone | `surface_expectations`: exact perceived text and citation tones; separate lexical vs contextual fields, including 一/不 and unresolved cases |
| Individual timing | Accepted aligned/partial recorded-audio span with timing evidence ID; no source evidence supplied by target text |
| Grouped timing | `PerceivedTimingGroup`, currently `azure_word`: exact provider word span without trustworthy character boundaries |
| Workspace timing unit | `pronunciationUnits`: original evidence/span ID, members, start/end, grouped flag, original eligibility and abstaining agreement |
| Playback | `ExactPlaybackButton` + `exactRecording`: shared canonical PCM download and exact zero-padding sample crop |
| Selected graph | `unitPitch`: immutable filtered source points, half-open spans, later-start ownership for accepted tiny overlap, saved source gaps, common attempt scale |

The saved 雨伞 group exists because Azure supplied a trustworthy exact **word span**, but
not attributable per-character Grapheme spans. Anonymous syllable positions or provider
phonetic labels cannot be substituted for character timing. `azure_word_timing_groups`
requires exact sequential text identity, contiguous Han offsets, valid duration-bounded
timing, no omission/insertion, no pre-existing individual timings, and no overlapping
individual span. Reading the letters 雨/伞 does not earn a boundary between them.

For the saved `40357072` recording, individual 雨 and 伞 timings are null and the group
is 3.56–4.87 s. Both characters have phrase-resolved readings, but **that is not why
they were acoustically grouped**. V1 can additionally label the exact 雨伞 expression
as a reviewed linguistic candidate; its learner chunk still contains one timing unit.

## Linguistic metadata audit

There is no POS parser, general word tokenizer, or serialized lexical word-edge contract
in the perceived-speech DTO. ASR/logprob tokens are not reliable lexical units. Explicit
pronunciation tokens may resolve a reading only at exact matching offsets.

The reading dictionary's longest matches include words, names, idioms, and constructions:
雨伞, 一个, 不是, 今天, 我们; the supplement also includes 很好 and 聊聊. A bounded
check showed 三个人 resolves as reading spans 三 / 个人, while 两本书 leaves 本's reading
unresolved. Therefore neither “phrase” sources nor all dictionary matches can define UX
chunks. No broad dictionary segmentation is exposed.

`surface.YI_QUANTITY_FOLLOWERS` is a conservative surface-rule follower set (including
time/quantity characters), not a full classifier/POS lexicon. It cannot justify general
measure-word grouping. `yi_quantity` is sufficient for the already reviewed 一个 case.
The lexical-neutral supplement and narrow 们/吧 rules establish readings, not arbitrary
left attachment. Reference TTS consumes target/readings and supplies no independent
perceived chunk structure. Sandhi groups are tone contexts, not practice-unit boundaries.

## Additive API candidates

`pronunciation/chunks.py` owns the deterministic linguistic whitelist. Inputs are only
exact perceived text and saved `PerceivedSyllable` values. Output:

```text
PronunciationChunkCandidate {
  text, character_start, character_end, syllable_indices,
  reason: lexical_word | demonstrative_classifier | numeral_classifier
}
PerceivedAnalysisData {
  ...existing fields,
  pronunciation_chunk_policy: string | null,
  pronunciation_chunk_candidates: PronunciationChunkCandidate[]
}
```

`analysis_response` enriches both new responses and reopened historical analyses after
the existing grouped-timing enrichment. It operates on a validated copy. No saved JSON,
analysis configuration hash, database schema, timing record, or immutable evidence is
rewritten. No reanalysis/provider call occurs. Old DTOs default to no candidates.
OpenAPI and dependency-free mobile types are regenerated with the existing exporter.

This is deliberately a candidate API, not a second authoritative timing plan. The API
already owns Mandarin interpretation; the mobile workspace already owns accepted-unit
navigation and exact playback. This division avoids copying Mandarin rules into mobile
or duplicating the workspace's acoustic ownership implementation on the server.

## Learner chunk projection

`pronunciationChunks.ts` leaves `pronunciationWorkspace.ts` and `unitPitch` unchanged.

```text
PronunciationChunk {
  id, text,
  members: saved perceived syllable references,
  constituents: existing PronunciationUnit references,
  constituentUnitIds, characterIndices,
  reason: candidate reason | single_unit | existing_timing_group | untimed,
  linguisticReason?: candidate reason,
  timingStatus: timed | unavailable,
  start: number | null, end: number | null
}
```

IDs serialize the complete ordered constituent IDs, not the displayed text. Untimed
IDs use syllable index/offsets; workspace selection is scoped to an analysis. The pure
planner is an ordered non-overlapping partition, including untimed singleton members.
It accepts only whole atoms. A candidate crossing half of [买这], or missing 个 timing,
fails closed without splitting or discarding those original identities.

`chunkEvidence` retains each unit's independent projection/availability/eligibility.
`chunkPitch` unions the original `unitPitch` segments in time order without joining lines
at constituent boundaries. Source point objects, pitch values, timestamps, raw indices,
and whole-attempt Y scale survive. A point in an unowned inter-unit gap remains unowned
even though the chunk's audio window includes the gap. Missing selected pitch is never
filled. An empty constituent does not erase a measured neighbor.

Chunk playback simply supplies first accepted start and last accepted end to the existing
canonical PCM crop. Exact constituent controls still receive their original spans.
It adds no new media backend, padding, synthesis, smoothing, or resampling.

## Workspace and lifecycle

Default navigation now selects one compact chunk button and one reusable panel. The same
wrapping styles, 44×48 minimum selection targets, neutral styling, optional-target controls,
and fixed Record/New Attempt footer remain. Citation pinyin is composed from saved perceived
readings; detailed contextual references remain separate. Missing readings stay explicit.

A multiple-unit chunk has no aggregate eligibility, gesture, or agreement score. Its
combined graph remains available even when one constituent is pitch-unavailable. Only
the necessary partial-coverage sentence is added to the default panel. Single timing
units/groups retain the previous measurement and gesture semantics.

More Details keeps the full-utterance graph and adds a compact constituent selector with
**one** constituent inspection panel. It exposes reading, original timing, exact playback,
pitch availability, selected graph, existing quality labels/reasons, and contextual tone
references. Existing indivisible groups expose no separate per-character exact playback.

Playback retains product voice: “Play my recording for 这个”, “Play my recording for 这”,
and “Play my recording for 个”. Selection buttons expose native selected state and explicit
web `aria-pressed`, because the installed React Native Web does not translate the native
`accessibilityState.selected` into DOM state. Enter/Space selection, touch, dialog focus
containment, and Escape are exercised in Chromium. No invisible character buttons sit
inside a chunk.

Practice with/without a target and expanded Conversation share this projection. Conversation
still starts collapsed; no assistant behavior changes. History is still session-local and
reconstructs the same plan from the saved response, resetting the selected panel on remount.
New Attempt clears active evidence/selection, stops playback, retains target/history, and
starts capture. Clear target keeps the existing exercise reset. No persistent chunk state
or migration is introduced.
