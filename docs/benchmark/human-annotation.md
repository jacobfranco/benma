# Native-listener annotation protocol

Human perception agreement is a primary benchmark signal, not decorative validation. Use at least
three native Standard Mandarin listeners per evaluated sample; five is preferred for ambiguous or
adversarial cases. Preserve disagreement.

## Preparation

1. Confirm consent covers research processing and each cloud provider under test.
2. Assign a pseudonymous listener ID. Store identity/consent mapping outside this repository.
3. Use headphones in a quiet room at a comfortable fixed level.
4. Randomize samples per listener with a seeded order; do not group error types.
5. Tell listeners to transcribe what they heard, not repair it into the likely lesson target.

## Stage 1 — blind

Run `python -m benchmark annotate-blind ...`. The utility plays audio without target text and asks:

1. What did you hear? Characters are preferred; pinyin is optional.
2. Did you understand on the first listen?
3. Would you ask for repetition?
4. Confidence from 0 to 1.
5. Optional perceptual notes.

The resulting JSON includes a SHA-256 commit over sample ID, listener ID, order, and response. The
file is create-only. The reveal command recomputes the hash; changed blind content is rejected.
Corrections require a new annotation ID with an explicit note—never silent editing.

## Stage 2 — reveal

Only after Stage 1 exists, run `annotate-reveal`. It then displays target text/pinyin and asks:

- whether a tone was problematic and which zero-based syllable indices;
- initial/final problems;
- rhythm/prosody issues;
- whether speech remains understandable;
- severity: none, minor, moderate, severe;
- notes distinguishing “understandable” from “technically correct.”

The reveal commit references the blind hash. It cannot overwrite the original perception.

## Analysis

Report raw per-listener responses plus pairwise inter-rater CER. Do not majority-vote away minority
perceptions before inspecting them. For Benma, “two listeners heard the wrong word and one repaired
it” is often more important than the modal transcript.

If listeners disagree because of script choice, synonyms, or punctuation, normalize only those
orthographic differences in metrics and retain originals. Do not normalize a tone-changed word to
the intended word.

## Quality controls

- Include repeat native-control items to estimate within-listener consistency.
- Include silence/nonsense to detect forced guessing.
- Flag hearing impairment, playback failure, known target exposure, or Mandarin dialect effects.
- Do not use fixture annotations in scientific results. Files under `reports/fixtures` are synthetic
  workflow tests and say so in their notes.

