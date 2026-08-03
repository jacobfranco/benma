# ADR 0001: Provisional speech foundation

- Status: provisional research decision
- Date: 2026-08-03
- Evidence level: architecture + documentation + synthetic replay only; **no live vendor winner**

## Context

Benma's largest product risk is semantic repair: a recognizer reconstructs intended Mandarin and
the product presents it as acoustic truth. Known-target assessment and unknown-target perception
therefore require structurally different contracts and separately persisted evidence.

## Decision

### Unknown-target perception

No provider is selected. The first falsification bake-off will compare:

1. FunASR `paraformer-zh` (Mandarin-specific, local, timestamped);
2. Google Chirp 3 `cmn-Hans-CN` (current GA cloud/multilingual contestant);
3. OpenAI `gpt-4o-transcribe` (current dedicated transcription contestant, prompt omitted);
4. local OpenAI Whisper turbo and API `whisper-1` as baselines.

FunASR is the provisional **local candidate**, not the quality leader. Google and OpenAI are the
provisional **cloud contestants**, not trusted literal listeners. Thirty exact-one-error sentences,
20 nonsense/clipped controls, and three blind native listeners each are the minimum evidence before
calling a leader. Selection emphasizes human agreement, error preservation, semantic repair, and
misleading-context behavior ahead of intended-target CER.

### Known-target pronunciation

Tencent SOE-N is the first candidate to test because its current documentation explicitly exposes
Chinese sentence tone detection and short pinyin tone assessment, plus phone/timing detail. iFlytek
ISE streaming is the fallback contestant because it documents Mandarin phone and tone scores.
Azure is a globally accessible comparison baseline, but current docs do not show an explicit
detected Mandarin lexical-tone field and say several detailed pronunciation features are English-
only. None is selected until tone false acceptance and native false rejection are measured.

Minimum decision data: every directed tone substitution represented at least ten times across
speakers; at least 30 native controls; segmental substitutions across each priority contrast;
sandhi subsets analyzed independently.

### F0

Use torchcrepe as the first neural pitch contestant, Praat/Parselmouth as the scientific reference,
and the dependency-free autocorrelation analyzer as a reproducibility/sanity baseline. F0 is
initially **visualization and diagnostic evidence only**. Promote it to grading evidence only after
speaker-relative normalization, hand-checked boundaries, tracker disagreement, and held-out human
labels establish false-accept behavior.

### Forced alignment

MFA Mandarin is suitable for a hand-inspected experiment, not yet trustworthy for user-facing
syllable highlighting. Its model documentation warns about read/clean-speech training mismatch and
alignment has no automatic gold standard. Until the pilot quantifies boundary error on bad learner
speech, prefer provider timestamps with uncertainty or coarse utterance/word highlighting. Never
show a precise red syllable boundary merely because MFA returned one.

### Vendor strategy

> Provider choice is provisional and replaceable.

Vendor response structures stay in adapter raw evidence. Product-domain models receive normalized
results with explicit missing/unsupported fields. Replacement requires the same frozen benchmark,
adapter contract tests, raw preservation, no regression in semantic repair/tone false acceptance,
acceptable native false rejection, and documented cost/privacy/operations.

## Consequences

- Unknown-target request types cannot contain a target or context; Pydantic rejects extras.
- Context prompts live only in a research-only probe contract and are excluded from production.
- User corrections and later interpretations append evidence; they do not overwrite perception.
- The initial backend remains a modular monolith around ports documented in
  `docs/architecture/evidence-model.md`.
- Replay fixtures prove plumbing only. Reports visibly refuse to declare a winner from them.

## Unresolved questions and Pass 2 recommendation

| Unknown | Evidence needed | Blocks Pass 2 product skeleton? |
|---|---|---|
| Which ASR best matches blind listeners on learner errors? | 30 corrupted sentences × 3 listeners × four providers | Blocks feedback claims, not corpus tools |
| Does SOE-N accept wrong tones under sandhi? | full directed tone confusion set plus T3/一/不 cases | Blocks tone grading |
| Are iFlytek symbols stable/mappable? | contracted access and 20 raw responses | Blocks iFlytek normalization only |
| Does F0 add value beyond evaluators? | disagreement cases with hand boundaries | Does not block; keep diagnostic |
| Can MFA bound learner syllables safely? | 50 hand-labeled utterances including bad speech | Blocks precise UI highlighting |
| Cloud audio regions/retention acceptable? | legal/privacy review of selected accounts/contracts | Blocks human production upload |

Recommended next experiment: record 30 exact-one-error learner utterances (balanced tone, initial,
final), 10 native controls, and 10 nonsense/low-confidence controls; obtain three blinded native
annotations per item; then run FunASR, Chirp 3, GPT-4o Transcribe, Whisper, SOE-N, iFlytek, and Azure
on identical audio. This most directly reduces the decision uncertainty.
