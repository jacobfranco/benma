# Benma speech benchmark report

Data status: **replay_fixture_only**.

> Replay fixtures validate the harness; they are not experimental evidence and must not be used 
> to select a production vendor.

## Benchmark status

- Corpus: 174 defined / 384 desired; 0 recorded
- Provider runs: 25 total, 25 succeeded, 0 failed
- Blind listener commits: 6
- Inter-rater pairwise CER: 50.3%

## Unknown-target perception

| Provider/product | Success | Target CER / WER | Human CER | Error preservation | Semantic repair |
|---|---:|---:|---:|---:|---:|
| funasr/paraformer-zh | 4/4 | 9.5% / n/a | 12.7% | 50.0% | 50.0% |
| google_cloud/chirp_3 | 4/4 | 0.0% / n/a | 12.7% | 0.0% | 100.0% |
| openai/gpt-4o-transcribe | 4/4 | 0.0% / n/a | 12.7% | 0.0% | 100.0% |
| openai/gpt-4o-transcribe/context_probe | 3/3 | 19.0% / n/a | 19.0% | 66.7% | 33.3% |

Target CER is conventional accuracy and is intentionally not the primary selection metric.

### Confidence, context, latency, and fixture cost

| Provider/product | Confidence n / mean | High-confidence repair | Context delta | p50 / p95 | Estimated run cost |
|---|---:|---:|---:|---:|---:|
| funasr/paraformer-zh | 4 / 93.0% | 50.0% | n/a | 0.270s / 0.324s | $0.002400 |
| google_cloud/chirp_3 | 4 / 89.0% | 100.0% | n/a | 0.300s / 0.354s | $0.003200 |
| openai/gpt-4o-transcribe | 4 / 85.0% | 100.0% | n/a | 0.330s / 0.384s | $0.004000 |
| openai/gpt-4o-transcribe/context_probe | 0 / n/a | n/a | 50.0% | 0.300s / 0.300s | n/a |

Confidence summaries describe field availability and synthetic-fixture behavior; they are not calibration evidence.

## Known-target pronunciation

| Provider/product | Success | Tone observations | Tone false accept | Native false reject | Phone / initial / final recall |
|---|---:|---:|---:|---:|---:|
| azure_speech/pronunciation_assessment_zh-CN | 5/5 | 0 | n/a | n/a | 0.0% / 0.0% / n/a |
| tencent/SOE-N | 5/5 | 4 | n/a | n/a | 100.0% / 100.0% / n/a |

### Known-target operations and unavailable capabilities

| Provider/product | p50 / p95 | Estimated run cost | Explicitly unavailable |
|---|---:|---:|---|
| azure_speech/pronunciation_assessment_zh-CN | 0.500s / 0.590s | n/a | explicit detected tone |
| tencent/SOE-N | 0.500s / 0.590s | n/a | none declared |

### Tone confusion matrices

| Provider/product | Expected | Detected | Count |
|---|---:|---:|---:|
| tencent/SOE-N | T1 | T1 | 1 |
| tencent/SOE-N | T2 | T3 | 1 |
| tencent/SOE-N | T3 | T2 | 1 |
| tencent/SOE-N | T3 | T3 | 1 |

### Tone evidence examples

| Sample | Provider/product | Unit | Expected | Detected | Score | Human |
|---|---|---:|---:|---:|---:|---|
| isolated_ma1_correct_r1 | tencent/SOE-N | 0 | T1 | T1 | 94.0 | n/a |
| isolated_ma2_wrong_as_t3 | tencent/SOE-N | 0 | T2 | T3 | 42.0 | n/a |
| sentence_beijing_wrong_tone | tencent/SOE-N | 3 | T3 | T2 | 82.0 | n/a |
| tone_pair_33 | tencent/SOE-N | 0 | T3 | T3 | 90.0 | n/a |

## Negative/control behavior

| Sample | Provider/product | Transcript | Confidence |
|---|---|---|---:|
| control_nonsense_1 | funasr/paraformer-zh | 嘎咯咪 | 93.0% |
| control_nonsense_1 | google_cloud/chirp_3 | 咖喱米 | 89.0% |
| control_nonsense_1 | openai/gpt-4o-transcribe | 咖喱米 | 85.0% |

## Failure gallery

### sentence_shuijiao_wrong_initial — funasr/paraformer-zh

- Target: 他吃完饭以后想睡觉。
- Provider: 他吃完饭以后想睡觉
- Blind listeners: 他吃完饭以后想睡觉, 他吃完饭以后想水饺
- Observation: Provider returned the target while at least one blind listener did not.

### sentence_beijing_wrong_tone — google_cloud/chirp_3

- Target: 我明天想去北京。
- Provider: 我明天想去北京
- Blind listeners: 我明天想去背景, 我明天想去北京
- Observation: Provider returned the target while at least one blind listener did not.

### sentence_shuijiao_wrong_initial — google_cloud/chirp_3

- Target: 他吃完饭以后想睡觉。
- Provider: 他吃完饭以后想睡觉
- Blind listeners: 他吃完饭以后想睡觉, 他吃完饭以后想水饺
- Observation: Provider returned the target while at least one blind listener did not.

### sentence_beijing_wrong_tone — openai/gpt-4o-transcribe

- Target: 我明天想去北京。
- Provider: 我明天想去北京
- Blind listeners: 我明天想去背景, 我明天想去北京
- Observation: Provider returned the target while at least one blind listener did not.

### sentence_shuijiao_wrong_initial — openai/gpt-4o-transcribe

- Target: 他吃完饭以后想睡觉。
- Provider: 他吃完饭以后想睡觉
- Blind listeners: 他吃完饭以后想睡觉, 他吃完饭以后想水饺
- Observation: Provider returned the target while at least one blind listener did not.

## Interpretation

No provider winner is declared from replay data. Use this report shape only after collecting native/learner recordings and blinded native-listener annotations.
