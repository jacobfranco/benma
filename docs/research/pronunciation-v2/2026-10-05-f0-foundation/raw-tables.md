# Raw, cleanup and production tables

Native coverage is finite frames / native frames, including silence and boundaries. It is not voiced-speech accuracy. CREPE raw has no unvoiced decision. Jump counts are discontinuity proxies, not measured real-speech octave-error rates.

| File | Tracker | View | F0 frames | Total | Median Hz | Islands | Adjacent >9 st | Near-gap >9 st |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| native_24k | praat_ac | raw | 73 | 100 | 257.634 | 6 | 0 | 4 |
| native_24k | praat_ac | minimal | 73 | 100 | 257.634 | 6 | 0 | 4 |
| native_24k | praat_cc | raw | 79 | 102 | 256.682 | 3 | 0 | 1 |
| native_24k | praat_cc | minimal | 78 | 102 | 256.101 | 4 | 0 | 1 |
| native_24k | pyin | raw | 67 | 106 | 253.444 | 2 | 0 | 0 |
| native_24k | pyin | minimal | 56 | 106 | 259.368 | 2 | 0 | 0 |
| native_24k | harvest | raw | 97 | 106 | 233.865 | 1 | 0 | 0 |
| native_24k | harvest | minimal | 97 | 106 | 233.865 | 1 | 0 | 0 |
| native_24k | crepe_full | raw | 106 | 106 | 235.431 | 1 | 0 | 0 |
| native_24k | crepe_full | minimal | 68 | 106 | 248.939 | 3 | 0 | 0 |
| native_24k | praat_ac | production | 73 | 100 | 257.634 | 6 | 0 | 4 |
| native_16k | praat_ac | raw | 74 | 100 | 256.472 | 5 | 0 | 3 |
| native_16k | praat_ac | minimal | 74 | 100 | 256.472 | 5 | 0 | 3 |
| native_16k | praat_cc | raw | 79 | 102 | 256.463 | 3 | 0 | 1 |
| native_16k | praat_cc | minimal | 78 | 102 | 256.001 | 4 | 0 | 1 |
| native_16k | pyin | raw | 67 | 106 | 253.444 | 2 | 0 | 0 |
| native_16k | pyin | minimal | 56 | 106 | 259.368 | 2 | 0 | 0 |
| native_16k | harvest | raw | 97 | 106 | 233.848 | 1 | 0 | 0 |
| native_16k | harvest | minimal | 97 | 106 | 233.848 | 1 | 0 | 0 |
| native_16k | crepe_full | raw | 106 | 106 | 235.431 | 1 | 0 | 0 |
| native_16k | crepe_full | minimal | 68 | 106 | 248.939 | 3 | 0 | 0 |
| native_16k | praat_ac | production | 70 | 100 | 252.576 | 5 | 0 | 2 |
| native_24k | rmvpe | raw | 78 | 106 | 246.119 | 2 | 0 | 0 |
| native_24k | rmvpe | minimal | 77 | 106 | 247.198 | 2 | 0 | 0 |
| native_16k | rmvpe | raw | 78 | 106 | 246.119 | 2 | 0 | 0 |
| native_16k | rmvpe | minimal | 77 | 106 | 247.191 | 2 | 0 | 0 |

## Whole-corpus safety and continuity

| Tracker | View | Speech islands | Speech adjacent >9 st | Negative emitted / total | Synthetic >9-st errors / voiced comparisons | Low proxy coverage | Low proxy doubled |
| --- | --- | --- | --- | --- | --- | --- | --- |
| praat_ac | raw | 254 | 5 | 427/1911 | 0/1404 | 1.000 | 0 |
| praat_ac | minimal | 256 | 5 | 418/1911 | 0/1404 | 1.000 | 0 |
| praat_ac | production | 184 | 1 | 122/1911 | 0/1259 | 1.000 | 0 |
| praat_cc | raw | 302 | 7 | 471/1923 | 0/1403 | 1.000 | 0 |
| praat_cc | minimal | 291 | 7 | 457/1923 | 0/1403 | 1.000 | 0 |
| pyin | raw | 154 | 0 | 670/1947 | 145/1404 | 0.982 | 1 |
| pyin | minimal | 131 | 0 | 39/1947 | 145/1404 | 0.729 | 0 |
| harvest | raw | 161 | 29 | 1075/1947 | 0/1404 | 0.995 | 3 |
| harvest | minimal | 161 | 29 | 1073/1947 | 0/1404 | 0.995 | 3 |
| crepe_full | raw | 30 | 0 | 1947/1947 | 145/1404 | 1.000 | 8 |
| crepe_full | minimal | 277 | 0 | 289/1947 | 145/1378 | 0.937 | 1 |
| rmvpe | raw | 147 | 22 | 374/1947 | 79/1404 | 1.000 | 3 |
| rmvpe | minimal | 140 | 17 | 326/1947 | 79/1404 | 1.000 | 3 |

## Production filter ablation

| Recording | Raw frames | Retained | Removed | Raw/retained islands | Raw/retained nearby >9-st jumps |
| --- | --- | --- | --- | --- | --- |
| native_24k | 73 | 73 | 0 | 6/6 | 4/4 |
| 6f56aef1 | 243 | 211 | 32 | 15/12 | 4/1 |
| 5b995fff | 83 | 80 | 3 | 6/7 | 3/3 |
| 7787300e | 214 | 189 | 25 | 17/14 | 4/4 |
| c95673d3 | 233 | 226 | 7 | 10/10 | 3/3 |
| c5188fc3 | 83 | 76 | 7 | 8/10 | 4/4 |
| 27ea3b92 | 96 | 91 | 5 | 8/9 | 1/1 |
| 0f4107fe | 112 | 107 | 5 | 5/5 | 1/1 |
| f3c642b5 | 58 | 27 | 31 | 5/2 | 0/0 |
| f47fadb3 | 139 | 122 | 17 | 6/4 | 1/0 |
| a0270cee | 262 | 175 | 87 | 14/7 | 2/0 |
| silence_original | 0 | 0 | 0 | 0/0 | 0/0 |
| 484e80c0 | 94 | 80 | 14 | 6/4 | 0/0 |
| e59a6350 | 45 | 38 | 7 | 4/2 | 0/0 |
| f5dc0cc1 | 28 | 28 | 0 | 3/3 | 1/1 |
| silence_periodic | 148 | 46 | 102 | 18/19 | 0/0 |
| 370aa8f4 | 228 | 153 | 75 | 11/3 | 3/0 |
| 1a927887 | 214 | 184 | 30 | 15/10 | 3/1 |
| 5ca771a7 | 140 | 116 | 24 | 9/6 | 2/0 |
| 209ef0c7 | 139 | 42 | 97 | 10/3 | 2/0 |
| 87ac7dd1 | 67 | 25 | 42 | 10/2 | 1/0 |
| 277e9941 | 92 | 6 | 86 | 11/4 | 0/0 |
| 02927481 | 264 | 217 | 47 | 10/7 | 1/0 |
| 90aa0d8d | 39 | 38 | 1 | 2/2 | 0/0 |
| e0c56934 | 159 | 140 | 19 | 7/5 | 0/0 |
| dccf8a63 | 38 | 38 | 0 | 3/3 | 0/0 |
| 9b1d959a | 64 | 51 | 13 | 2/2 | 1/0 |
| human_control | 204 | 102 | 102 | 14/5 | 5/0 |
| google_old | 253 | 146 | 107 | 14/9 | 7/0 |
| silence_accidental | 279 | 76 | 203 | 12/6 | 9/1 |
| take_1 | 185 | 177 | 8 | 9/8 | 3/3 |
| take_2 | 143 | 131 | 12 | 6/8 | 1/1 |
| take_3 | 199 | 185 | 14 | 8/12 | 3/3 |
| native_16k | 74 | 70 | 4 | 5/5 | 3/2 |
| native_gain | 73 | 72 | 1 | 6/6 | 4/4 |
| native_bandlimit | 70 | 70 | 0 | 5/5 | 2/2 |
| syn_steady_70 | 159 | 2 | 157 | 1/2 | 0/0 |
| syn_steady_110 | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_steady_180 | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_steady_260 | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_rise | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_fall | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_valley | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_octave_risk | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_weak_fundamental | 161 | 161 | 0 | 1/1 | 0/0 |
| syn_noise_gap | 132 | 132 | 0 | 2/2 | 0/0 |
| neg_digital_silence | 0 | 0 | 0 | 0/0 | 0/0 |
| neg_stationary_noise | 0 | 0 | 0 | 0/0 | 0/0 |
| neg_clicks | 0 | 0 | 0 | 0/0 | 0/0 |
