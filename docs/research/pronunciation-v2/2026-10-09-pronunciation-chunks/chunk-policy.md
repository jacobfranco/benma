# Exact production policy

Policy identifier: `perceived-pronunciation-chunks-v1`.

| Case | API candidate requirement | Workspace outcome |
| --- | --- | --- |
| 雨伞 | Exact adjacent perceived 雨/伞 with saved resolved `yu3`, `san3` | Wrap existing timing group, or join two complete timed units |
| 这个 | Exact adjacent perceived 这/个 with saved `zhe4`, `ge4` or `ge5` | Join only whole accepted timing units |
| 那个 | Exact adjacent perceived 那/个 with saved `na4`, `ge4` or `ge5` | Same as 这个 |
| 一个 | Saved `yi1`, `ge4`, and 一's existing `surface_rule == yi_quantity` | Join only the reviewed quantity use |
| Existing accepted timing group | No linguistic candidate required | One wrapper, keeping its full original extent |
| Everything else | No candidate | Singletons, including readable untimed syllables |

Candidate text, character offsets, and syllable indices must match exactly. Readings must
be resolved and in the reviewed set; missing or different saved overrides cause abstention,
not reading correction. The API normalizes a saved reading's notation only for membership
checking. It neither reruns the reading resolver on historical data nor edits pinyin.
An immediately following 个 vetoes any reviewed `…个` candidate, avoiding partial grouping
of unreviewed reduplication. These are closed reviewed expressions, not a new general
classifier dictionary. No new language dependency or network call is introduced.

## 一, 不, and neutral tones

The 一个 quantity check reuses the existing exact-text surface engine's grammatical
distinction. 第一个, 十一个, 一个个, arbitrary 一 constructions, and old data without the
quantity rule do not qualify. The rule is linguistic metadata, not a tone grade.
Existing unresolved/reduplication contexts remain unresolved even if substring spelling
contains 一个. For example, a constructed `那个一个` sequence triggers the existing
reduplication guard around 一; this pass does not override it.

The display composes **saved citation readings**: `zhège`, `nàge`, and `yīgè` in the
reviewed fixtures. 一 remains lexical T1 with existing expected T2 in quantity use;
个's optional reduction stays unresolved in that fixture. We do not silently display
surface `yí` as lexical `yī`, force neutral 个, or borrow target pinyin.

不是 stays [不] [是] despite the existing `bu_before_fourth` expectation. A reading
phrase match is not chunk permission. 我们, 妈妈, 今天, and lexical 苹果 are deliberately
not automatically joined. General neutral suffixes and particles 吗/呢/吧/的/们 stay
separate. A lexical neutral reading alone does not establish safe attachment.

## Partition and timing gates

1. Start with all perceived syllables in order, wrapping each accepted timing group once.
   Untimed syllables have one noninteractive singleton each. Never split a timing group.
2. Accept only candidates from the recognized V1 API policy. An older server or unknown
   future policy falls back to the existing timing units/groups.
3. Require an exact match to the **entire** candidate span, its text, and its ordered
   syllable indices. No member of an atom can be partially consumed.
4. Require every atom in a proposed join to be accepted and timed. No partial/missing
   timing, synthetic alignment, or invented playback window can authorize a join.
5. Require ordered constituent starts/ends and apply the existing visible-pause veto.
6. Consume the successful candidate once; otherwise emit the current atom unchanged.

The result partitions every perceived syllable exactly once. Repeated text gets distinct
IDs from the constituent identities and offsets. Punctuation and non-Han gaps cannot be
crossed because the perceived code-point offsets must be consecutive. Mixed Latin,
numeric, and unknown content retains the existing full-transcript display; the planner
does not tokenize it or invent hidden learner buttons.

New linguistic joins contain exactly **two Han characters**: this follows the four
reviewed expressions, not a general UX length heuristic. Existing acoustic groups can
be longer and remain indivisible. No six-character lexical expression is newly merged.

## Existing visible-pause veto

`sentenceToneGraph.ts` defines `PAUSE_SECONDS = .3`. Its production normalized timeline
marks a pause for adjacent timed syllables when:

```text
next.start - previous.end + 1e-9 >= PAUSE_SECONDS
```

The nanosecond tolerance prevents floating-point arithmetic from hiding a mathematical
0.30-second gap. Existing tests cover short gaps, exactly 0.30 s, a just-shorter gap,
and missing/synthetic timing. The chunk planner imports the same constant and semantics.
This is a conservative **presentation veto**, not a claim of a validated new prosodic
boundary detector. A visible pause should not disappear inside a new seamless chunk.
It never creates a chunk: touching ordinary syllables remain separate.

There is no available internal boundary for an existing timing group, so no internal
pause is inferred. Its accepted whole-span playback remains unchanged.

## Explicitly deferred

Broad lexical/dictionary grouping; ASR word grouping beyond existing accepted timing
groups; general demonstrative/classifier or numeral/classifier grammar; 三个/两本/五把;
question/quantity forms 几个/多少个; neutral suffix attachment; broad 一/不 constructions;
whole noun phrases; segmentation based on proximity/F0/TTS/target text; LLM segmentation;
new pause detection; chunk-level scoring, gesture classification, or tone colors.
