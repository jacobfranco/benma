# Native-tone weak-label policy v2

This experiment asks about audio tone recognition, not tutor acceptability.
Classes are `T1`, `T2`, `T3`, `T4`, `NEUTRAL`; unresolved examples have a null
label and an explicit exclusion. Derived surface labels remain hypotheses about
ordinary speech. A transcript alone cannot establish the realized acoustic tone.

`perceptual_tone/native_labels.py` imports the frozen Benma lexical resolver
`exact-text-lexical-context-v3.2` and surface resolver `exact-text-surface-v1.1`
read-only. It uses pypinyin **0.55.0**, preserving reading alternatives, rule IDs,
character offsets, lexical tone and surface label separately. Research exclusions
are added after these calls; no production rule is changed.

| Case | Training-label policy |
| --- | --- |
| Unambiguous T1/T2/T3/T4 reading | Retain resolved surface class; reduced low T3 remains T3, without requiring a full dip/rise. |
| Neutral | Explicit contextual dictionary/grammar tone 5 maps to `NEUTRAL` (internal numeric 0). Do not infer neutral from duration, lack of pitch, or Benma abstention. |
| Recognized T3 pair | First syllable becomes T2 only when frozen logic resolves the pair; e.g. 你好 → T2,T3. Keep lexical T3 provenance for sandhi breakdown. |
| Long/uncertain T3 chain | Exclude every unresolved member. 我想买 is not three trustworthy lexical-T3 training labels. |
| T3 followed by unresolved reading | Exclude: potential sandhi cannot be resolved. |
| 不 | Before known T4 → T2; otherwise retain resolved T4. A不A remains excluded. |
| 一 | Quantity context: before T4 → T2, before T1/T2/T3 → T4. Explicit ordinal 第 一 and isolated/final 一 may retain T1. Unresolved grammatical contexts excluded. |
| 一 in cardinal strings | Extra research exclusion. The production number fallback is not sufficient evidence of actual surface realization. |
| Optional neutralization | Quantity 个 after 一 is excluded when frozen logic marks reduction optional. Repeated numbered-tone characters are additionally excluded where reduplication can reduce the second tone; explicit lexical-neutral 妈妈 remains supported. |
| Ambiguous polyphone | No first-dictionary-choice fallback. Keep null label and all alternatives. |
| Erhua | Exclude 儿 and the immediately preceding syllable pending proven ownership. This deliberately also rejects some ordinary 儿 readings. |
| Punctuation | Generic label function respects explicit character gaps. THCHS derived punctuation was added by the alignment author, so it is removed for labeling and cannot establish a prosodic boundary. |
| Unknown transcript content | Quarantine utterance candidates rather than silently dropping spoken Latin/numeric content. |

The first packet's pronounced class imbalance is partly a **label-selection
artifact**. For example, isolated 的 may remain polyphonically unresolved even
though many real occurrences are neutral. This pass does not “fix” that by
assuming every 的 is de5. Native optional reduction, emphasis, word segmentation,
and dictionary errors remain unmeasured sources of weak-label noise.

## Alignment and split policy

Only a word interval containing exactly one Han character can be a candidate in
this adapter. Multi-character word durations are never equally divided. Candidate
durations must be 60–800 ms, finite, monotonic, nonoverlapping and within the WAV.
These are structural filters, **not calibrated alignment confidence**; confidence
is recorded as null. Every retained and excluded row preserves transcript, source,
speaker identifiers, label/reading provenance, original word span, and reasons.

Seed `20261015` hashes conservative speaker groups into approximately 60/20/20
train/validation/test. All windows of a source recording remain in one partition.
Repeated prompt readings across partitions are quarantined using label-independent
prompt ownership. Cross-partition speaker groups, utterance IDs, decoded PCM
hashes and prompt IDs are rejected. This verifies mechanical separation under the
registry; uncertain real speaker identity still prevents a speaker-generalization
claim. The current manifest is **not training-ready**.

T3 before T1/T2/T3/T4/neutral, non-sandhi, and sandhi are retained as audit groups.
For this corpus, utterance-medial/final fields are position proxies; true prosodic
phrase positions and isolated T3 have not been established. Excluded hard T3
contexts must stay visible in reporting.

## Input boundary and future model comparison

Model A takes only finite frozen speech embeddings. No lexical/surface tone,
Hanzi, expected-family vector, IDs, text or coaching fields enter the input schema.
The old acceptability experiment's `context` feature block **must not be reused**.
For an F0 baseline only the existing `benma` acoustic feature block is eligible;
tests poison all expected-tone/grading fields and require identical features.

Model B is optional. `mǎi`/`mai3` → `mai`, `lǜ` → `lv`; marked/numeric pinyin and
Hanzi are rejected at the model boundary. Stripping tone is insufficient on its
own: a training-only vocabulary must retain bases seen at least five times in
each of at least two classes. A future run must compare identity-only and
audio-only controls on the same ambiguity subset, fit all encodings on training
data, and report unseen-base performance. No Model B was fitted in this pass.

Even Model A can learn segment identity from audio. A future claim of tone
perception therefore also needs a tone-stripped-identity majority control and
within-base contrasts; good speaker-disjoint accuracy alone cannot rule out
lexical shortcuts. This issue is separate from direct label-feature leakage.

Audio views are target-only and target ±200 ms, clipped to the source recording.
Existing caches address PCM content, target span, encoder revision/weight hashes,
layer/pooling and runtime. Pooling is target mean or context mean. The tested
encoder layers are 6, 9 and 12. Probabilities must retain fixed ordering
`T1,T2,T3,T4,NEUTRAL`; deterministic family supports are not probabilities.

Before meaningful training, the small developer review must verify audio/text,
syllable ownership, linguistic labels, sandhi and neutral cases. The generated
15-item training-only packet is unreviewed; no review was fabricated. No recruited
listeners, new wrong-tone speech, or acceptability annotations are required.
