# Latency and orchestration

Pitch warmup **already ran concurrently with ASR before this pass**. `create_perception` starts the existing bounded optional worker; that worker owns its SQL session. Perceived analysis retains its existing prepared acoustic/alignment closures and request-owned persistence. No second concurrency mechanism was added. PostgreSQL `NO KEY UPDATE` keeps duplicate acoustic computation single-flight while permitting ASR/perception FK insertion.

If warmup capacity is occupied, initialization fails, or the process loses its optional work, final analysis uses the existing locked acoustic path. No polling protocol, persistent job queue or ASR join was introduced. Tests disable automatic route warmup unless explicitly testing it.

A focused local timing sample used **one existing human-control waveform**, six repetitions of the unchanged production Praat analyzer (first cold, five warm). This was not a 49-file benchmark or alternative-tracker evaluation. Measurements are in `extraction-latency.json`:

| Work | Warm median |
|---|---:|
| Existing foundational extraction including existing high-pass diagnostic | 41.56 ms |
| New frozen-track construction, selection snapshot and content digest | 7.54 ms |
| New track JSON serialization | 0.59 ms |
| Typed saved-track replay, with no extraction/filtering | 1.25 ms |

Thus the measured new fresh-result construction/serialization cost is about **8.12 ms once per utterance**; cached downstream views pay validation/projection instead of extraction. There is no claimed ASR/turn speedup: live ASR and end-to-end device latency were not measured, and no provider was called. Do not compare the summed work with wall-clock turn latency when branches overlap.

`processing-timings.json` records all 152 saved-region derivations separately: projection, eligibility, gesture/classifier, and utterance construction. The generated summary in README/validation gives the final run's medians and maxima. Each projection and eligibility operation is well below 1 ms locally. Character comparison is disabled and a constant presentation policy, with no second mobile acoustic classifier.

The acoustic run's `latency_ms` includes fresh track construction. Perceived analysis additionally records `pitch_projection` and `pitch_eligibility` timing counters. Saved-region timings include grouped/diagnostic windows explicitly; they are local computation timings, not a provider latency claim.

Final saved-region medians/maxima: projection **0.0261/0.0825 ms**, eligibility **0.0525/0.3288 ms**, gesture/classifier plus gate **0.5642/1.0412 ms**. Local Node comparison-policy execution is **0.0000235 ms/call** median over 100,000 calls (`comparison-latency.json`), not a physical mobile-device measurement.
