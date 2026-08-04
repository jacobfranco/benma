# Pronunciation calibration

**NOT READY**

Synthetic replay, constructed fixtures, documentation examples, and TTS are excluded from every headline count and metric. Requested learner error is not ground truth.

Maturity: `raw_evidence`. Scope: `none`.

## Real corpus and human evidence

| Evidence | Count |
|---|---:|
| real recordings | 0 |
| learner correct | 0 |
| tone errors | 0 |
| initial errors | 0 |
| final errors | 0 |
| native controls | 0 |
| negative controls | 0 |
| spontaneous samples | 0 |
| unique native raters | 0 |
| stage a annotations | 0 |
| stage b annotations | 0 |
| samples with three native raters | 0 |
| known target provider runs | 0 |

## Readiness gates

### Minimum Existing Pilot

| Gate | Actual | Required | State |
|---|---:|---:|---|
| learner deliberate errors | 0 | 30 | NOT READY |
| tone errors | 0 | 10 | NOT READY |
| initial errors | 0 | 10 | NOT READY |
| final errors | 0 | 10 | NOT READY |
| native controls | 0 | 10 | NOT READY |
| negative controls | 0 | 10 | NOT READY |
| three native listeners per critical sample | 0 | 30 | NOT READY |

### Stronger Paired Pilot

| Gate | Actual | Required | State |
|---|---:|---:|---|
| learner deliberate errors | 0 | 30 | NOT READY |
| tone errors | 0 | 10 | NOT READY |
| initial errors | 0 | 10 | NOT READY |
| final errors | 0 | 10 | NOT READY |
| native controls | 0 | 10 | NOT READY |
| negative controls | 0 | 10 | NOT READY |
| three native listeners per critical sample | 0 | 30 | NOT READY |
| learner correct controls | 0 | 12 | NOT READY |

### Categorical Tone

| Gate | Actual | Required | State |
|---|---:|---:|---|
| human supported tone error syllables | 0 | 20 | NOT READY |
| human supported acceptable tone syllables | 0 | 20 | NOT READY |
| critical rater coverage | 0 | 30 | NOT READY |
| held out evaluation | 0 | >=1 persisted held-out partition | NOT READY |
| held out validated threshold | 0 | explicit promotion decision after holdout review | NOT READY |

## Provider evidence

No qualifying real provider runs exist. Fixture parsing is not live validation.

| Provider/mode | Lifecycle | Live runs | Calibration |
|---|---|---:|---|
| tencent_soe_n / sentence / eval_mode=1 / F_TDET=true | fixture_validated | 0 | raw_evidence / none |
| tencent_soe_n / pinyin / eval_mode=8 / F_TDET=true | fixture_validated | 0 | raw_evidence / none |
| iflytek_ise / cn_vip read_sentence full dimension | fixture_validated | 0 | raw_evidence / none |
| azure_speech / scripted phoneme assessment | fixture_validated | 0 | raw_evidence / none |
| alibaba_ssecp / cn.raw.score / cn.word.score | documented | 0 | raw_evidence / none |
| speechsuper / character/sentence evaluation | documented | 0 | raw_evidence / none |

## Decision

Categorical pronunciation calibration remains incomplete.

Categorical tone judgment remains disabled. No threshold has satisfied real-data, three-rater, calibration-selection, and held-out promotion gates.
