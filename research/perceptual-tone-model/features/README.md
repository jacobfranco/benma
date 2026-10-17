# Numeric feature groups

`perceptual_tone/features.py` defines the fixed `benma-numeric-v1` allowlist.
`export-features` replays the frozen evaluator, then writes a numeric NPZ matrix
and ordered column schema. Training also replays and rejects stale or changed
deterministic payloads before fitting anything.

- **Benma:** four family supports, winner/runner-up support and margins, clarity,
  probe counts/agreement, duration, existing contour geometry/pitch range,
  quantiles of existing normalized contours, retained/raw voiced evidence,
  discontinuities, gaps, structural reliability and categorical gesture/family.
- **Context:** one-hot lexical/surface/previous/next tones, acceptable family set,
  neutral target/context, syllable index and known phrase position. Unknown is
  explicit. No transcript embeddings or unconstrained text features.
- **Speech:** the selected frozen encoder embedding, with all provenance in its
  cache metadata. Audio/model content, not paths or filenames, determines it.

Benma-derived numeric summaries consume existing exported measurements. They do
not change production calculations. Model 1 and Model 3 omit explicit expectation
features; Model 4 adds them. Learner grade/color, coaching, raw annotations,
consensus, confidence, perceived-tone labels, names, IDs, filenames, free text and
collection intent are never model features. They are retained for auditing only.

Every numeric dimension has an explicit missingness indicator. Median imputation
and standardization fit **only the gradable consensus training rows**. A wholly
missing training column is retained and filled with zero. Validation/test values
never set medians, scales, class weights or feature selection. Fixed categorical
vocabularies avoid data-driven vocabulary leakage.
