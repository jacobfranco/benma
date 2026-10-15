# Bounded fixture review

The saved sample comprises the existing six-take viewer, the physical `89cee47e`
projection fixture, and four saved analysis extracts for neutral particles, ordinary
adjacency, perceived 贵州, and mixed script. These are **11 saved attempts**, not a
segmentation benchmark. Reading-resolver probes and clearly labelled deterministic design
fixtures cover cases absent from this sample. No audio/timing was synthesized for a saved
case and no acoustic model was rerun. Confidence below refers to policy/identity, not tones.

| Perceived text / source | Existing timing structure | Linguistic candidate | Final learner chunks | Reason / confidence / concern |
| --- | --- | --- | --- | --- |
| 我想买这个。 / `89cee47e` | 我 / 想 / 买 / 这 2.34–2.73 / 个 2.74–3.04 | 这个 | 我 / 想 / 买 / 这个 | Reviewed demonstrative; high; 个 has no selected pitch |
| 我想买五把雨伞。 / `40357072` | Five individual spans; grouped 雨伞 3.56–4.87 | 雨伞 | 我 / 想 / 买 / 五 / 把 / 雨伞 | Existing group plus reviewed word; high; no internal 雨/伞 timing |
| 我要一个苹果。 / `8d252264` | All individual; 一 1.68–2.46, 个 2.47–2.94 | 一个 (`yi_quantity`) | 我 / 要 / 一个 / 苹 / 果 | Reviewed quantity; high; 苹果 is a reading phrase, not a V1 chunk |
| 我有一个苹果。 / `d47274bc` | All timing unavailable | 一个 | Readable 我 / 有 / 一 / 个 / 苹 / 果; no bounded controls | Timing veto; high confidence abstention |
| 我要一个苹果。 / `4b9dbd2b` | 一 2.86–3.25, 个 3.26–3.85 | 一个 | 我 / 要 / 一个 / 苹 / 果 | Complete timing, 10 ms gap; high; missing selected pitch stays missing |
| 我要一个苹果。 / `8faf1a90` | 一 1.24–1.49, 个 1.50–1.89 | 一个 | 我 / 要 / 一个 / 苹 / 果 | Same policy for shorter durations; high |
| 我有一个苹果。 / `a5acd04c` | 一 1.26–1.47, 个 1.48–1.67 | 一个 | 我 / 有 / 一个 / 苹 / 果 | Same quantity rule despite unresolved 有 reading; high |
| 我们去吧 / analysis `a5536c4e` | 我 .39–.80 / 们 .81–.98 / 去 .99–1.12 / 吧 1.13–1.44 | None | 我 / 们 / 去 / 吧 | Reading phrase 我们 and neutral/grammar 吧 do not earn grouping; intentional abstention |
| 我想买 / analysis `44075f37` | Three individual spans | None | 我 / 想 / 买 | Ordinary phrase adjacency is insufficient |
| 贵州。 / analysis `8eed93d5` | 贵 .63–1.06 / 州 1.07–1.67 | None | 贵 / 州 | Perceived identity, independent of target 广州; high |
| 我上马523 / analysis `81925693` | Three Han timings; digits remain transcript content | None | 我 / 上 / 马; full transcript retained | No new grouping across mixed content; no number normalization |
| 那个 / design | Two deterministic test spans | 那个 | 那个 | Same reviewed demonstrative rule; no physical take claimed |
| 不是 / reading + design | Two deterministic test spans | None | 不 / 是 | `phrase` readings and `bu_before_fourth` are not chunk boundaries |
| 三个人, 两本书 / reading + design | Individual design spans | None | 三 / 个 / 人; 两 / 本 / 书 | General classifier/POS structure unavailable; defer |
| 第一个, 十一个, 一个个 / design | Individual design spans | None | Singletons | Not the reviewed quantity rule; never override context |
| 这，个 / design | Separate offsets around punctuation | None | 这 / 个 | No candidate crosses a punctuation boundary |
| 那……个 / timing counterfactual for 那个 | Candidate text 那个; gap ≥ .30 s | 那个 | 那 / 个 | Existing visible-pause veto; no new acoustic inference |
| 这个……这个 / design | Two individually timed pairs at distinct offsets | Two 这个 spans | 这个 / 这个 | Distinct IDs; punctuation separates occurrences |
| 我想 / clean-F0 counterfactual | Touching spans, clean selected points | None | 我 / 想 | Proximity and F0 do not create candidates |
| 我想买这个雨伞和那个雨伞再要一个苹果 / layout only | Deterministic individual spans | 这个, 雨伞, 那个, 雨伞, 一个 | 我 / 想 / 买 / 这个 / 雨伞 / 和 / 那个 / 雨伞 / 再 / 要 / 一个 / 苹 / 果 | Long wrapping/selection review; no physical audio claim |

## Audit conclusions

Broad phrase grouping was rejected. Existing reading matches include 不是/我们 and a
三 / 个人 segmentation of 三个人; phrase metadata does not mean one pedagogical word.
The broad surface follower set does not resolve classifier readings (e.g. 本 in 两本书).
Neutral tone and sandhi are contextual references, not permission to merge neighbors.

The four approved expressions are short, deterministic, and useful without these broader
assumptions. All multi-unit merges need complete accepted timing, exact offsets, and no
visible-pause veto. A grouped 雨伞 remains one chunk even if the API candidate is absent.

The shared checked-in `pronunciationChunkCases.json` contains **linguistic/design data
only**. Backend tests compare its fields/candidates with the actual API generator; mobile
tests add explicitly synthetic layout spans. The saved physical pitch fixture and timing
controls remain their existing files. Browser audio uses the private canonical physical
file after a SHA-256 check, and existing private viewer audio for 一个/雨伞. No recording
bytes are added to tracked fixtures or screenshots.
