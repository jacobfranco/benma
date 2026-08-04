# Metric definitions

All aggregates are reported per provider/product/model/adapter and corpus version. Missing vendor
fields remain missing. A provider returning no confidence is not assigned zero confidence.

## Recognition and human agreement

- **CER**: Levenshtein distance over NFKC-normalized characters after removing Unicode punctuation
  and whitespace, divided by reference length. Intended-target CER is conventional accuracy only.
- **WER**: whitespace-token Levenshtein rate; omitted for unsegmented Mandarin strings.
- **Human-perception CER**: provider transcript CER against every blind listener transcript, then
  arithmetic mean. Original transcriptions remain available for inspection.
- **Inter-rater disagreement**: mean symmetric pairwise CER for samples with 2+ blind listeners.

## Truthfulness metrics

An error case is eligible for error-preservation/repair metrics only when it has a declared
non-`none` deliberate error **and** at least one blind listener produced a noncanonical transcript.
This avoids treating the curator's intent alone as acoustic proof.

- **Error preservation recall**: eligible cases where provider output is not exactly the normalized
  intended target / all eligible cases. This conservative first metric detects that evidence of an
  error survived; the failure gallery and future unit alignment determine whether it preserved the
  *right* error.
- **Semantic repair rate**: eligible cases where provider output exactly equals intended target /
  all eligible cases. A high value is dangerous even if target CER improves.
- **Context leakage delta**: among matched context-probe pairs whose A transcript is noncanonical,
  fraction of B/C transcripts shifted exactly to the intended target. Reports must also show
  congruent and misleading changes separately when real data exists.
- **Nonsense hallucination**: per negative-control sample, retain transcript, confidence, and empty-
  output behavior. No single numeric score is used until native listeners label word-likeness.

The current preservation metric is deliberately auditable and incomplete. Pass 2 should add
corrupted-unit span matching once human-produced pinyin and alignment are reliable.

## Human-supported known-target metrics

- **Tone confusion matrix**: count explicit `(reference_tone, detected_tone)` pairs only. Providers
  without detected tones are labeled unavailable, never inferred from a score.
- **Tone detection FAR**: human-supported tone-error syllables where explicit valid provider
  evidence fails to flag a concern / human-supported tone-error syllables with a provider decision.
- **Tone diagnosis FAR**: human-supported known tone substitutions where the provider identifies
  the expected tone / substitutions with a valid provider tone hypothesis. Missing/invalid tone is
  an abstention, not a pass or a tone.
- **Native FRR**: native-control decisions that flag a concern / native controls with a provider
  decision.
- **Learner-correct/acceptable FRR**: flagged syllables / human-supported acceptable learner
  syllables with a decision. Surface tone, not dictionary tone, supplies the expectation.
- **Severe FAR**: likely-unintelligible/repetition samples shown reassuring evidence / severe
  samples eligible under a predeclared reassurance policy. It remains undefined until such a policy
  is selected; the report does not fabricate a zero rate.
- **Phone error recall**: deliberate initial/final substitutions whose affected syllable has a
  provider error classification or a phone score below threshold / eligible substitutions.
- **Omission/substitution recall**: provider miscue/absence classification at the declared unit;
  add after live schemas are mapped.

## Confidence, latency, and cost

- Confidence calibration compares vendor confidence with blind first-pass understanding using
  reliability bins and Brier score once at least 100 labeled outcomes exist. Current small fixtures
  do not report calibration. They report only confidence availability, mean confidence, and the
  share of confidence-bearing eligible cases that both semantically repair and exceed the explicit
  0.8 high-confidence threshold.
- Latency uses wall-clock request start to final response, plus audio duration. Report p50/p95 and
  real-time factor; streaming first-token latency should be a separate field in Pass 2.
- Costs come only from dated configuration. Per-request services state assumed utterances/minute.
  Token-priced services stay unknown until run usage exists. Report p50/p95 failures/timeouts
  alongside successful latency; never exclude a provider's failures silently.

Every rate reports numerator, denominator, fraction, and Wilson interval when the denominator is
nonzero. Thresholds are explored on a persisted calibration partition and reported on held-out data
separately. Small samples remain exploratory.
