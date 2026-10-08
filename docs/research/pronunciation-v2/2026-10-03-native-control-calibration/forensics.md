# Full per-character forensics

Frozen audit of the existing working tree. All times are absolute canonical seconds. Each of the 18 rows in [the full CSV](per-character-forensics.csv) includes all requested fields, complete retained Hz/semitone sequences, full observed-contour features and Mine vertices. The tables below split those columns for readability. `NA` means unavailable, not zero.

Raw frame count is the current 10-ms tracker grid inside `[start,end)`. Finite raw means `tracker_f0_hz` before energy gating. Retained is the existing display filter’s full-resolution selection, before smoothing/simplification. Coverage is frame count divided by all frames in the provider character span; it is not a phonetic voicing rate. Hz triplets and semitone triplets are min/median/max. Semitones use `12*log2(F0 / rounded utterance baseline_hz)`. Mine has median smoothing and 0.15-st simplification; the CSV retains both measurements and Mine vertices.

A pitch island is a contiguous non-null run on the raw frame grid, or a retained display run. A long gap is an inter-island timestamp gap >0.045 s. Jumps count adjacent finite samples separated by at most 0.12 s; missing spans longer than that do not become jumps. Rejection reasons overlap and must not be summed. These are audit definitions, not new thresholds in production. Actual acoustic correctness of provider boundaries is not established by structural mapping checks alone.

The requested external context is 我 T3, 要 T4, 一 T2, 个 neutral, 苹 T2, 果 T3. The saved backend differs: 要 is unresolved (`yao4/yao1/yao3`); 个 remains lexical/contextual T4. Both are preserved below. A has generation text, but no perceived transcript or saved alignment; its per-character acoustic fields remain NA. A’s displayed dictionary derivation is explicitly separate from perceived evidence.

## DIRECT NATIVE

| Char | Perceived reading | Lexical | Backend surface | Audit surface | Word | Word start/end | Char start/end | Timing kind/source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | NA | NA | NA | 3 | NA | NA/NA | NA/NA | NA/NA |
| 要 | NA | NA | NA | 4 | NA | NA/NA | NA/NA | NA/NA |
| 一 | NA | NA | NA | 2 | NA | NA/NA | NA/NA | NA/NA |
| 个 | NA | NA | NA | 0 | NA | NA/NA | NA/NA | NA/NA |
| 苹 | NA | NA | NA | 2 | NA | NA/NA | NA/NA | NA/NA |
| 果 | NA | NA | NA | 3 | NA | NA/NA | NA/NA | NA/NA |

| Char | Raw frames | Finite raw | Post-energy finite | Retained | Raw % | Retained % | First/last retained | Raw Hz min/med/max | Retained Hz min/med/max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | NA | NA | NA | NA | NA | NA | NA/NA | NA/NA/NA | NA/NA/NA |
| 要 | NA | NA | NA | NA | NA | NA | NA/NA | NA/NA/NA | NA/NA/NA |
| 一 | NA | NA | NA | NA | NA | NA | NA/NA | NA/NA/NA | NA/NA/NA |
| 个 | NA | NA | NA | NA | NA | NA | NA/NA | NA/NA/NA | NA/NA/NA |
| 苹 | NA | NA | NA | NA | NA | NA | NA/NA | NA/NA/NA | NA/NA/NA |
| 果 | NA | NA | NA | NA | NA | NA | NA/NA | NA/NA/NA | NA/NA/NA |

| Char | Baseline Hz | Retained st min/med/max | Raw/retained islands | Long gaps | Raw >6/>12 st | Retained >6/>12 st | Rejections |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | 252.577 | NA/NA/NA | NA/NA | NA | NA/NA | NA/NA | NA |
| 要 | 252.577 | NA/NA/NA | NA/NA | NA | NA/NA | NA/NA | NA |
| 一 | 252.577 | NA/NA/NA | NA/NA | NA | NA/NA | NA/NA | NA |
| 个 | 252.577 | NA/NA/NA | NA/NA | NA | NA/NA | NA/NA | NA |
| 苹 | 252.577 | NA/NA/NA | NA/NA | NA | NA/NA | NA/NA | NA |
| 果 | 252.577 | NA/NA/NA | NA/NA | NA | NA/NA | NA/NA | NA |

| Char | Observed classification | Confidence | Reason | Comparison | Mine segment count |
| --- | --- | --- | --- | --- | --- |
| 我 | NA | NA | NA | uncertain | NA |
| 要 | NA | NA | NA | uncertain | NA |
| 一 | NA | NA | NA | uncertain | NA |
| 个 | NA | NA | NA | uncertain | NA |
| 苹 | NA | NA | NA | uncertain | NA |
| 果 | NA | NA | NA | uncertain | NA |

A’s `uncertain` comparison is the offline rendering fallback for absent timing, not a persisted native analysis result. There are zero owned Mine segments, but per-character segment counts stay NA because the boundaries are unknown. Seventy full-resolution measurements remain available on the elapsed-time view. Current dictionary derivation from generation text: wǒ / unresolved / yī / gè / píng / guǒ; lexical 3/NA/1/4/2/3; surface 3/NA/2/4/2/3. No ASR result was fabricated.

## PHONE TTS

| Char | Perceived reading | Lexical | Backend surface | Audit surface | Word | Word start/end | Char start/end | Timing kind/source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | wǒ | 3 | 3 | 3 | 我 | 1.31/1.69 | 1.31/1.69 | direct_grapheme/azure_provider_grapheme |
| 要 | NA | NA | NA | 4 | 要 | 1.7/2.09 | 1.7/2.09 | direct_grapheme/azure_provider_grapheme |
| 一 | yī | 1 | 2 | 2 | 一个 | 2.1/2.75 | 2.1/2.47 | direct_grapheme/azure_provider_grapheme |
| 个 | gè | 4 | 4 | 0 | 一个 | 2.1/2.75 | 2.48/2.75 | direct_grapheme/azure_provider_grapheme |
| 苹 | píng | 2 | 2 | 2 | 苹果 | 2.76/4.41 | 2.76/3.45 | direct_grapheme/azure_provider_grapheme |
| 果 | guǒ | 3 | 3 | 3 | 苹果 | 2.76/4.41 | 3.46/4.41 | direct_grapheme/azure_provider_grapheme |

| Char | Raw frames | Finite raw | Post-energy finite | Retained | Raw % | Retained % | First/last retained | Raw Hz min/med/max | Retained Hz min/med/max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | 38 | 28 | 22 | 22 | 73.6842 | 57.8947 | 1.4325/1.6425 | 235.505/243.647/255.803 | 235.505/245.7265/255.027 |
| 要 | 39 | 38 | 35 | 31 | 97.4359 | 79.4872 | 1.7125/2.0725 | 217.679/275.097/306.274 | 217.679/276.079/306.274 |
| 一 | 37 | 28 | 0 | 0 | 75.6757 | 0 | NA/NA | 52.012/56.7315/65.638 | NA/NA/NA |
| 个 | 27 | 20 | 19 | 19 | 74.0741 | 70.3704 | 2.4925/2.6725 | 221.987/245.9785/286.445 | 221.987/244.095/282.134 |
| 苹 | 69 | 42 | 9 | 0 | 60.8696 | 0 | NA/NA | 52.481/54.4875/62.122 | NA/NA/NA |
| 果 | 95 | 89 | 80 | 74 | 93.6842 | 77.8947 | 3.4925/4.3325 | 58.016/186.338/398.009 | 162.065/185.032/228.472 |

| Char | Baseline Hz | Retained st min/med/max | Raw/retained islands | Long gaps | Raw >6/>12 st | Retained >6/>12 st | Rejections |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | 221.853 | 1.0338/1.7692/2.4126 | 1/1 | 0 | 0/0 | 0/0 | {"tracker_missing":10,"missing_or_out_of_range_f0":16,"weak_periodicity":10,"below_energy_gate":6} |
| 要 | 221.853 | -0.3288/3.7857/5.5826 | 1/4 | 0 | 0/0 | 0/0 | {"below_energy_gate":3,"missing_or_out_of_range_f0":4,"weak_periodicity":5,"tracker_missing":1} |
| 一 | 221.853 | NA/NA/NA | 1/0 | 0 | 0/0 | 0/0 | {"tracker_missing":9,"missing_or_out_of_range_f0":37,"weak_periodicity":9,"below_energy_gate":28,"low_frequency_contamination":4} |
| 个 | 221.853 | 0.0105/1.6541/4.1613 | 1/1 | 0 | 0/0 | 0/0 | {"below_energy_gate":1,"missing_or_out_of_range_f0":8,"tracker_missing":7,"weak_periodicity":7} |
| 苹 | 221.853 | NA/NA/NA | 4/0 | 0 | 0/0 | 0/0 | {"tracker_missing":27,"missing_or_out_of_range_f0":60,"weak_periodicity":27,"below_energy_gate":33,"low_frequency_contamination":38} |
| 果 | 221.853 | -5.4364/-3.142/0.509 | 5/3 | 1 | 3/3 | 0/0 | {"tracker_missing":6,"missing_or_out_of_range_f0":15,"weak_periodicity":6,"below_energy_gate":9,"bracketed_short_pitch_island":4,"low_frequency_contamination":5} |

| Char | Observed classification | Confidence | Reason | Comparison | Mine segment count |
| --- | --- | --- | --- | --- | --- |
| 我 | unclear | low | ambiguous_shape | uncertain | 1 |
| 要 | 4-like | moderate | acoustic_shape_only | uncertain | 4 |
| 一 | unclear | low | insufficient_voicing | uncertain | 0 |
| 个 | 4-like | moderate | acoustic_shape_only | consistent | 1 |
| 苹 | unclear | low | low_frequency_contamination | uncertain | 0 |
| 果 | unclear | low | tracker_instability | uncertain | 3 |

Timing evidence ID: `f7a0ee97-827a-4187-9c92-07d8e0f259fe`. Provider source is `azure_speech_alignment_only`, version `zh-CN-exact-grapheme-v2-target-sapi-v1`. All six are direct `Grapheme` entries. Anonymous syllables, inferred intervals and grouped word regions: **none**.

## HUMAN

| Char | Perceived reading | Lexical | Backend surface | Audit surface | Word | Word start/end | Char start/end | Timing kind/source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | wǒ | 3 | 3 | 3 | 我 | 0.5/1.05 | 0.5/1.05 | direct_grapheme/azure_provider_grapheme |
| 要 | NA | NA | NA | 4 | 要 | 1.06/1.39 | 1.06/1.39 | direct_grapheme/azure_provider_grapheme |
| 一 | yī | 1 | 2 | 2 | 一个 | 1.42/1.85 | 1.42/1.63 | direct_grapheme/azure_provider_grapheme |
| 个 | gè | 4 | 4 | 0 | 一个 | 1.42/1.85 | 1.64/1.85 | direct_grapheme/azure_provider_grapheme |
| 苹 | píng | 2 | 2 | 2 | 苹果 | 1.88/2.73 | 1.88/2.25 | direct_grapheme/azure_provider_grapheme |
| 果 | guǒ | 3 | 3 | 3 | 苹果 | 1.88/2.73 | 2.26/2.73 | direct_grapheme/azure_provider_grapheme |

| Char | Raw frames | Finite raw | Post-energy finite | Retained | Raw % | Retained % | First/last retained | Raw Hz min/med/max | Retained Hz min/med/max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | 55 | 41 | 21 | 21 | 74.5455 | 38.1818 | 0.843/1.043 | 53.035/97.485/122.345 | 97.485/111.24/122.345 |
| 要 | 33 | 31 | 20 | 20 | 93.9394 | 60.6061 | 1.063/1.253 | 57.816/93.394/121.06 | 92.077/102.1455/121.06 |
| 一 | 21 | 16 | 15 | 15 | 76.1905 | 71.4286 | 1.453/1.593 | 60.254/106.8465/117.778 | 103.722/107.275/117.778 |
| 个 | 21 | 18 | 12 | 11 | 85.7143 | 52.381 | 1.673/1.773 | 50.31/101.2345/109.371 | 100.015/103.533/109.371 |
| 苹 | 37 | 27 | 27 | 27 | 72.973 | 72.973 | 1.983/2.243 | 107.846/115.45/124.922 | 107.846/115.45/124.922 |
| 果 | 47 | 34 | 9 | 7 | 72.3404 | 14.8936 | 2.273/2.333 | 52.032/59.4785/100.625 | 86.097/93.635/100.625 |

| Char | Baseline Hz | Retained st min/med/max | Raw/retained islands | Long gaps | Raw >6/>12 st | Retained >6/>12 st | Rejections |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 我 | 108.923 | -1.9207/0.3644/2.0118 | 4/1 | 0 | 1/0 | 0/0 | {"below_energy_gate":20,"missing_or_out_of_range_f0":34,"tracker_missing":14,"weak_periodicity":14,"low_frequency_contamination":11} |
| 要 | 108.923 | -2.9088/-1.1123/1.829 | 3/1 | 0 | 1/0 | 0/0 | {"tracker_missing":2,"missing_or_out_of_range_f0":13,"weak_periodicity":2,"below_energy_gate":11,"low_frequency_contamination":2} |
| 一 | 108.923 | -0.847/-0.2639/1.3531 | 2/1 | 0 | 1/0 | 0/0 | {"below_energy_gate":1,"missing_or_out_of_range_f0":6,"tracker_missing":5,"weak_periodicity":5} |
| 个 | 108.923 | -1.4771/-0.8786/0.0711 | 1/1 | 0 | 1/0 | 0/0 | {"tracker_missing":3,"missing_or_out_of_range_f0":9,"weak_periodicity":3,"low_frequency_contamination":5,"below_energy_gate":6} |
| 苹 | 108.923 | -0.172/1.0075/2.3726 | 1/1 | 0 | 0/0 | 0/0 | {"tracker_missing":10,"missing_or_out_of_range_f0":10,"weak_periodicity":10} |
| 果 | 108.923 | -4.0713/-2.6183/-1.3718 | 3/1 | 0 | 1/0 | 0/0 | {"tracker_missing":13,"missing_or_out_of_range_f0":38,"weak_periodicity":13,"low_frequency_contamination":25,"below_energy_gate":25} |

| Char | Observed classification | Confidence | Reason | Comparison | Mine segment count |
| --- | --- | --- | --- | --- | --- |
| 我 | 2-like | moderate | acoustic_shape_only | uncertain | 1 |
| 要 | 4-like | moderate | acoustic_shape_only | uncertain | 1 |
| 一 | unclear | low | ambiguous_shape | uncertain | 1 |
| 个 | unclear | low | tracker_instability | uncertain | 1 |
| 苹 | 2-like | moderate | acoustic_shape_only | consistent | 1 |
| 果 | unclear | low | low_frequency_contamination | uncertain | 1 |

Timing evidence ID: `fe854833-8a7c-4340-9141-27de407f50b9`. Provider source is `azure_speech_alignment_only`, version `zh-CN-exact-grapheme-v2-target-sapi-v1`. All six are direct `Grapheme` entries. Anonymous syllables, inferred intervals and grouped word regions: **none**.
