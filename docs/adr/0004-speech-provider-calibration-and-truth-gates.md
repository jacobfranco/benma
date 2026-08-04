# ADR 0004: Speech-provider calibration and truth gates

- Status: Accepted
- Date: 2026-08-03

## Decision

1. No provider was live validated in Pass 4. The same-audio smoke reached configuration validation
   and returned `BLOCKED_EXTERNAL` for Azure, Tencent sentence, Tencent pinyin, and iFlytek because
   credentials were absent. No live fixture was created.
2. Tencent integration targets only SOE-N / Smart Oral Evaluation-New Age, product 1774, current
   WSS endpoint. Legacy Basic product 884 has no code path. Sentence `eval_mode=1` and pinyin
   `eval_mode=8` both enable `F_TDET`; mode is provider identity. Fixture/docs show sentence mode can
   provide a valid hypothesis while the pinyin example can return invalid `-1` tones. No real mode
   is preferred until identical real audio is run.
3. iFlytek uses current streaming `/v2/open-ise`, `cn_vip`, `rst=entirety`, `ise_unite=1`, and
   full-dimension abilities. Its parser preserves tone/phone scores and detailed DP/initial/final/
   tone/error-confidence fields. Whether it adds useful independent evidence is unknown without a
   real entitled response and human-supported pilot.
4. Azure remains the mainstream commercial baseline. Its zh-CN phone/word evidence is useful, but
   Benma does not invent Mandarin tone hypotheses from its scores. It was not rerun live.
5. Alibaba SSECP and SpeechSuper remain documentation-only. Alibaba needs purchased/provisioned
   warrant/SDK access; SpeechSuper needs a usable trial/API contract. Neither was tested.
6. Production retains normalized autocorrelation v2. Torchcrepe and Parselmouth comparison tooling
   exists, but zero real recordings were available. This is `keep autocorrelation because real
   evidence is insufficient`, not an accuracy victory.
7. MFA remains disabled and research-only. Provider timings and MFA timings retain separate
   provenance. User-facing syllable boundaries require quality/confidence suppression. Zero real
   provider/MFA/manual comparisons exist, so neither is promoted or removed.
8. The corpus has 174 planned prompts and zero recordings. All real sample/rater/annotation/provider
   counts are zero. Calibration maturity is `RAW_EVIDENCE`; scope is `NONE`. Personal scope becomes
   possible only after a single-speaker rule passes its persisted held-out gate; it never transfers
   globally.
9. Categorical tone judgment remains disabled. No threshold was explored on real data, selected,
   held-out validated, or promoted. The server rejects the categorical flag.
10. Interpretation stays versioned and append-only. Every new run records configuration; the replay
    command reuses immutable evidence IDs/raw hashes and emits an observation diff without provider
    calls. User wording remains centralized by capability: raw factual evidence, explicitly
    experimental detection/conflict wording, and no calibrated wording yet.

## Evidence that would change the decision

- successful consented real captures for both Tencent modes, iFlytek full dimension, and Azure;
- at least 30 human-reviewed learner error recordings (10 each tone/initial/final), 10 native and
  10 negative controls, plus the stronger 12 paired learner-correct controls;
- at least three independent native listeners per critical sample and audio-quality exclusions;
- at least 20 human-supported error and 20 acceptable tone syllables;
- an immutable stratified split, calibration-only threshold selection, predeclared risk limits,
  acceptable held-out FAR/FRR across confusion/surface-tone classes, and explicit scope;
- real side-by-side F0 runtime/contour/voicing review and provider/MFA/manual boundary review.

Those facts could promote a narrow provider role or `CALIBRATED/PERSONAL` policy. They would not by
themselves establish `GENERAL`, native intelligibility, or a multi-provider production ensemble.

## Consequences

Benchmarking may call many vendors; production should call the smallest evidence set justified by
held-out risk, latency, cost, access, and privacy. Current provider ranking is unknown. Fixtures
validate parsers only. Synthetic acoustic tests validate tooling only. The manual action kit is the
source of truth for the remaining external campaign.
