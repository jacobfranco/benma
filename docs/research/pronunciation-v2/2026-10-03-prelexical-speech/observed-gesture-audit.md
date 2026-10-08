# Observed gesture audit — 2026-10-03

All 124 persisted perceptions were enumerated in a PostgreSQL read-only transaction. Latest matching successful perceptions were selected by exact alphanumeric transcript, UTC creation time and ID; the 贵州 case additionally requires a linked target 广州. Punctuation normalization is lookup-only. Nineteen matching recordings were retained, including both historical silence false accepts. All 19 canonical SHA-256 hashes matched storage. The local container was stopped; the existing `api-postgres-1` container was started without recreating its volume. No provider was called and no stored analysis/transcript was changed.

These four takes are newer than the October 2 Trust Pass. Learner descriptions are region-selection cues, not phonetic gold. The snapshot’s latest perception is 2026-10-03 04:20:31.197755 UTC. All dates below are UTC.

## Exact latest recording identity

### 我想买五把雨伞

- Perception: `02927481-5174-478d-a40a-6cece40b98df`; created `2026-10-03T04:13:39.779431+00:00`.
- Utterance: `f744082a-d401-4042-8060-2fd902a16aaf`.
- Attempt: `3ee1e8e1-b49c-48b6-b294-de39efe40c86`; created `2026-10-03T04:13:39.899221+00:00`; saved target `我想买五吧雨伞`.
- Analysis: `0b96165e-290e-4030-bdd2-49554fff5863`; acoustic run `268679aa-9a44-45e7-a3b9-5811155014ff`.
- Canonical asset: `c9af82dc-efda-486b-bfcb-a3f580517f6a`; SHA-256 `78103e205e43b62f973c18df9d104a3b07543dd960dd9a94d7d81cde1cf1f285`.

### 我要一个苹果

- Perception: `e0c56934-0bcb-47fd-aab3-a636f45092cb`; created `2026-10-03T04:16:49.895375+00:00`.
- Utterance: `0a169789-5e41-4026-8b64-6632d84ece05`.
- Attempt: `8d922514-e66a-4504-84f7-96664ef1156c`; created `2026-10-03T04:16:49.969858+00:00`; saved target `我要一个苹果`.
- Analysis: `91c60ddf-d0c0-4f4d-a686-1f5c9134d8dc`; acoustic run `c6b521b0-a2bb-46f1-a3a3-e18e49eaf4bc`.
- Canonical asset: `5bf3383c-4aa8-4592-877b-7ce84c4aea7e`; SHA-256 `db12a011c432f27c71fa7ec6a6e94c24c57220ddcaacf92a394649ed4339cdce`.

### 我们去吧

- Perception: `dccf8a63-0e0f-4458-82ce-facda812c8e3`; created `2026-10-03T04:18:44.285766+00:00`.
- Utterance: `4bd9f81e-a5b8-48c7-ad4d-d619c36c8fad`.
- Attempt: `8a92dd28-05ce-4b25-8dc0-2bebdd07324f`; created `2026-10-03T04:18:44.421660+00:00`; saved target `我们去吧`.
- Analysis: `a5536c4e-6679-4f61-b00b-de59d86b8ec7`; acoustic run `fdcb1a56-03b0-4e32-abb0-c74350005cf4`.
- Canonical asset: `3e4cd15f-3ff5-4229-b118-b30f1bd0af6f`; SHA-256 `d6c6abf9b5e57432033ccb57b9e763623ff68ab09056a01d69b908b331ce34d4`.

### 贵州

- Perception: `9b1d959a-f7ec-453a-8728-1a1c685606e7`; created `2026-10-03T04:20:31.197755+00:00`.
- Utterance: `dc078e94-3afa-4032-8780-cab2941617d0`.
- Attempt: `700a1662-f04b-4926-ae47-ea40b4f03592`; created `2026-10-03T04:20:31.359137+00:00`; saved target `广州`.
- Analysis: `8eed93d5-a363-49dc-a1f9-23defcecabfb`; acoustic run `14cf7146-1583-4af1-bf45-44bc8aee8b59`.
- Canonical asset: `577b29fb-9b9d-489a-9d49-630ec9ed7f94`; SHA-256 `e5ead05a19f091a0c7294087287d5c3e3b6b0c955fac1e19e034e9911de2b402`.

## Reproduction and denominators

Every stored timed classification was recomputed from its saved full acoustic frame list with the unchanged `classify_contour()` and compared exactly, including every feature: **77/77 timed units, 19 recordings, identical**. This includes historical false accepts only as negative diagnostic controls; the no-speech gate prevents their product use. Raw coverage below means finite original tracker F0, falling back to stored F0 only when no tracker field exists. Retained coverage means full filtered measurements, not simplified Mine vertices. Counts use `[start,end)` and the original 10-ms frame grid. The classifier’s `raw_voiced_frames` instead counts post-energy-gate F0; that denominator can differ. Untimed characters have **unidentifiable**, not zero, individual coverage.

Actual TypeScript `learnerVerdict` and `toneGestureMatch` were transpiled with the installed TypeScript compiler and run over the saved/new typed DTOs. No Python reimplementation of either policy was substituted. Source inputs were never targets. Full private rows, features and both traces are in `/tmp/benma-observed-gesture/{recordings,audit,presentation,verdicts}.json`; local measured plots are `critical-traces.svg`/`.png`. No user audio is added to Git.

## 我想买五把雨伞: every character

| Character / reading | Lexical / surface | Timing s | Raw / retained / frames | Classification · confidence · reason | Legacy / product |
|---|---|---|---|---|---|
| 我 / wǒ | T3 / unresolved | 0.74–1.07 | 25 / 22 / 33 (75.8% / 66.7%) | 2-like · moderate · `acoustic_shape_only` | unclear / uncertain |
| 想 / xiǎng | T3 / unresolved | 1.08–1.53 | 35 / 35 / 45 (77.8% / 77.8%) | unclear · low · `ambiguous_shape` | unclear / uncertain |
| 买 / mǎi | T3 / unresolved | 1.54–1.97 | 43 / 43 / 43 (100.0% / 100.0%) | 2-like · moderate · `acoustic_shape_only` | unclear / uncertain |
| 五 / wǔ | T3 / unresolved | 1.98–2.47 | 47 / 47 / 49 (95.9% / 95.9%) | unclear · low · `ambiguous_shape` | unclear / uncertain |
| 把 / unresolved | unresolved / unresolved | 2.48–2.87 | 18 / 18 / 39 (46.2% / 46.2%) | 2-like · moderate · `acoustic_shape_only` | unclear / uncertain |
| 雨 / yǔ | T3 / unresolved | unavailable | unidentifiable | unclear · low · `timing_unavailable` | unclear / uncertain |
| 伞 / sǎn | T3 / unresolved | unavailable | unidentifiable | unclear · low · `timing_unavailable` | unclear / uncertain |

| Character | Classifier coverage | Voiced s / boundary-tolerant coverage | Five robust bins, st | Change / range, st | Contamination / rejected instability / discontinuous gaps |
|---|---|---|---|---|---|
| 我 | 0.667 | 0.220 / 1.000 | -0.949, -1.000, 0.875, 1.372, 1.131 | 2.081 / 2.372 | 0.0000 / 0 / 0 |
| 想 | 0.778 | 0.350 / 1.000 | 2.290, 2.189, 4.516, 4.631, 1.819 | -0.471 / 2.812 | 0.0000 / 0 / 0 |
| 买 | 1.000 | 0.430 / 1.000 | -2.093, -1.854, -1.621, -0.868, 0.643 | 2.736 / 2.736 | 0.0000 / 0 / 0 |
| 五 | 0.959 | 0.470 / 1.000 | 1.603, 0.358, -0.103, 0.151, 0.700 | -0.903 / 1.706 | 0.0000 / 0 / 0 |
| 把 | 0.462 | 0.180 / 0.750 | -4.013, -3.029, -1.339, -1.210, -1.343 | 2.670 / 2.803 | 0.0000 / 0 / 0 |

## 我要一个苹果: every character

| Character / reading | Lexical / surface | Timing s | Raw / retained / frames | Classification · confidence · reason | Legacy / product |
|---|---|---|---|---|---|
| 我 / wǒ | T3 / T3 | 0.52–0.81 | 21 / 21 / 29 (72.4% / 72.4%) | 4-like · moderate · `acoustic_shape_only` | different / uncertain |
| 要 / unresolved | unresolved / unresolved | 0.82–1.09 | 27 / 27 / 27 (100.0% / 100.0%) | unclear · low · `ambiguous_shape` | unclear / uncertain |
| 一 / yī | T1 / T2 | 1.10–1.51 | 24 / 24 / 41 (58.5% / 58.5%) | unclear · low · `insufficient_voicing` | unclear / uncertain |
| 个 / gè | T4 / T4 | 1.52–1.79 | 27 / 24 / 27 (100.0% / 88.9%) | 1-like · low · `sustained_level_after_onset` | unclear / uncertain |
| 苹 / píng | T2 / T2 | 1.80–2.17 | 21 / 21 / 37 (56.8% / 56.8%) | 4-like · moderate · `acoustic_shape_only` | different / different |
| 果 / guǒ | T3 / T3 | 2.18–2.69 | 21 / 21 / 51 (41.2% / 41.2%) | 2-like · moderate · `acoustic_shape_only` | different / uncertain |

| Character | Classifier coverage | Voiced s / boundary-tolerant coverage | Five robust bins, st | Change / range, st | Contamination / rejected instability / discontinuous gaps |
|---|---|---|---|---|---|
| 我 | 0.724 | 0.210 / 1.000 | 2.354, 1.646, 0.790, 0.004, -0.348 | -2.703 / 2.703 | 0.0000 / 0 / 0 |
| 要 | 1.000 | 0.270 / 1.000 | 0.004, 0.073, -0.156, -0.242, -1.165 | -1.168 / 1.238 | 0.0000 / 0 / 0 |
| 一 | 0.585 | 0.240 / 0.588 | -4.636, 2.657, 1.555, 0.948, 1.061 | 5.697 / 7.293 | 0.0000 / 0 / 1 |
| 个 | 0.889 | 0.240 / 1.000 | 0.986, 0.073, -0.474, -0.848, -0.853 | -1.838 / 1.838 | 0.0000 / 0 / 0 |
| 苹 | 0.568 | 0.210 / 0.992 | 4.374, 4.049, 3.179, 2.397, -0.673 | -5.047 / 5.047 | 0.0000 / 0 / 0 |
| 果 | 0.412 | 0.210 / 0.845 | -2.821, -2.598, -2.139, -1.509, 0.599 | 3.420 / 3.420 | 0.0000 / 0 / 0 |

## 我们去吧: every character

| Character / reading | Lexical / surface | Timing s | Raw / retained / frames | Classification · confidence · reason | Legacy / product |
|---|---|---|---|---|---|
| 我 / wǒ | T3 / T3 | 0.39–0.80 | 8 / 8 / 41 (19.5% / 19.5%) | unclear · low · `insufficient_voicing` | unclear / uncertain |
| 们 / men | Neutral / Neutral | 0.81–0.98 | 16 / 16 / 17 (94.1% / 94.1%) | 1-like · moderate · `acoustic_shape_only` | unclear / uncertain |
| 去 / qù | T4 / T4 | 0.99–1.12 | 7 / 7 / 13 (53.8% / 53.8%) | unclear · low · `insufficient_voicing` | unclear / uncertain |
| 吧 / ba | Neutral / Neutral | 1.13–1.44 | 6 / 6 / 31 (19.4% / 19.4%) | unclear · low · `insufficient_voicing` | unclear / uncertain |

| Character | Classifier coverage | Voiced s / boundary-tolerant coverage | Five robust bins, st | Change / range, st | Contamination / rejected instability / discontinuous gaps |
|---|---|---|---|---|---|
| 我 | 0.195 | 0.080 / 0.308 | 0.300, 0.174, 0.275, 0.268, 0.226 | -0.074 / 0.126 | 0.0000 / 0 / 0 |
| 们 | 0.941 | 0.160 / 1.000 | 0.145, -0.285, -0.437, -0.466, -0.207 | -0.352 / 0.611 | 0.0000 / 0 / 0 |
| 去 | 0.538 | 0.070 / 1.000 | 4.376, 3.947, 3.182, 2.897, 2.510 | -1.866 / 1.866 | 0.0000 / 0 / 0 |
| 吧 | 0.194 | 0.060 / 0.630 | -1.979, -1.918, -1.559, -1.491, -1.321 | 0.658 / 0.658 | 0.0000 / 0 / 0 |

## 贵州: every character

| Character / reading | Lexical / surface | Timing s | Raw / retained / frames | Classification · confidence · reason | Legacy / product |
|---|---|---|---|---|---|
| 贵 / guì | T4 / T4 | 0.63–1.06 | 25 / 25 / 43 (58.1% / 58.1%) | 1-like · moderate · `acoustic_shape_only` | different / different |
| 州 / zhōu | T1 / T1 | 1.07–1.67 | 38 / 25 / 60 (63.3% / 41.7%) | unclear · low · `low_frequency_contamination` | unclear / uncertain |

| Character | Classifier coverage | Voiced s / boundary-tolerant coverage | Five robust bins, st | Change / range, st | Contamination / rejected instability / discontinuous gaps |
|---|---|---|---|---|---|
| 贵 | 0.581 | 0.250 / 0.893 | -0.622, -1.138, -1.500, -1.675, -0.709 | -0.086 / 1.052 | 0.0000 / 0 / 0 |
| 州 | 0.417 | 0.250 / 0.662 | 2.276, 2.382, 3.083, 3.071, 2.701 | 0.424 / 0.807 | 0.2188 / 1 / 0 |

## Critical conclusions

**苹: outcome A, missing product integration.** Timing [1.80,2.17), 21/37 raw and retained frames. Mine has one visibly falling measured segment; the unsmoothed full selected trace has the same direction, from +4.6350 st at 1.9516 s to −1.0536 st at 2.1516 s (−5.6886 st endpoints). Five-bin change is −5.0471 st. `classify_contour`: **4-like / moderate / acoustic_shape_only**, coverage .568, 210 ms continuous support, boundary-tolerant coverage .9924, no contamination or rejected instability. `learnerVerdict(T2, observed)` is **different**; new policy also **different**. Both agree with the visually falling curve. No self-report-driven adjustment is needed.

**贵: shallow valley inside a level-like coarse category.** Timing [0.63,1.06), 25/43 retained, 250 ms contiguous support. Full selected range 1.8261 st, with a late recovery; robust five-bin range 1.0524 st and change −.0862 st. The existing level rule requires robust range ≤1.5 st and |change|≤1 st, so **1-like / moderate / acoustic_shape_only** follows its actual rules. It is not evidence of a full T3 valley: robust fall/recovery are only 1.0524/.9662 st. User-facing **level-like** deliberately does not mean perfectly flat. Against reference guì/T4: legacy **different**, product **different**. Character remains 贵. No invented dipping classification is substituted.

**州: uncertainty is required.** Timing [1.07,1.67), 38/60 raw tracker frames, 32 post-energy F0, 25 retained. The visible selected region rises mildly, levels and undulates; its robust change is +.4244 st. Raw evidence has a maximum 11.8818-st jump and contamination fraction .2188 (7/32); `tracker_instability_rejected=1`. Result **unclear / low / low_frequency_contamination**. Both policies abstain against zhōu/T1. The mild retained line cannot override suspicious original evidence. Perceived 州 and reference T1 remain intact.

**去/吧:** latest 去 visibly falls about 1.98 st at selected endpoints, but only 7 frames / 70 ms survive; classifier **unclear / low / insufficient_voicing**. Latest 吧 has 6 frames / 60 ms and the same abstention. Latest 们 is **1-like / moderate / acoustic_shape_only**, but its neutral reference still receives no comparison. Consequently this latest 我们去吧 take has no positive cells; the request for positive feedback does not justify inventing reliable evidence.

**T3:** latest heavy-sentence 我/买/把 have rising categories; 想/五 are ambiguous; 雨/伞 have no character timing. All comparisons remain uncertain. In the apple take, 我 is falling and 果 rising, both moderate. The historical verdict calls both different from T3; this is an unsuitable production assumption when half-third/prosodic realization is unresolved. The new policy abstains for all surface T3, even when a categorical T3 reference exists. Existing explicitly resolved T3→T2 sandhi may enter the T2 policy; no surface-rule change was made.

**Failure assessment:** no confidently reversed rise/fall classification was discovered in the latest real cases. Coarse level-like labeling suppresses the small 贵 valley and binning differs from full endpoint extrema; this limitation is explicit. Short clear-looking motion (去) can correctly remain insufficient. The concrete product-policy failure is naïve historical T3 shape mismatch, not a demonstrated lexical-tone detector failure. No classification, pitch extraction, selection, threshold, region-selection or smoothing code was changed in this pass. The pre-existing `contours.py` diff belongs to earlier uncommitted work and is preserved.

**Decision 1: TRUSTWORTHY ENOUGH FOR CONSERVATIVE CONNECTED-SPEECH PRODUCT USE.** This means bounded acoustic shape descriptions and abstentions on these cases, not independently validated Mandarin-tone accuracy. There is no gold phonetic labeling or population accuracy estimate.

**Decision 2: SHIP CONSERVATIVE MATCH/DIFFERENT/UNCERTAIN**, exposed as consistent/different/uncertain under the explicit policy in the architecture document. Do not revive the legacy T3/low-confidence grading.

## Latest grouped 雨伞 evidence

Word [2.88,3.87), source character offsets **[5,7)**, text 雨伞, source `azure_word`, timing evidence ID `23be3b12-b6eb-4a0e-b0a0-5eb9ba61a22f`. Anonymous provider syllables are [2.88,3.23) and [3.24,3.87), with no Grapheme labels. They are deliberately unused. Raw tracker **59/99 (59.60%)**, retained **49/99 (49.49%)**: this is substantial word evidence, not absent pitch. No per-character F0 denominator or boundary can be justified.

The group maps its entire elapsed interval across both equal-width character cells with one shared plot region. No line or classification is split at their visual midpoint. Actual evidence gaps survive. Each character remains visible; both taps explain word-only attribution and uncertain comparison. More detail keeps the original elapsed timestamps and word span; Raw is unchanged. Partial character-timed words retain their known character intervals and are not overlaid by this initial whole-word grouping policy.

**Decision 3: SHIP GROUPED WORD-LEVEL PITCH.** Keeping this measured word blank hides usable evidence. Grouping preserves it without claiming an internal alignment or character grade.

## Previous positive control

Prior 贵州 perception `f5dc0cc1-cd1f-4721-918b-9357f33774e1` supplies a real consistent case: 贵 [0.69,1.05), 15/36 raw and retained frames, 150 ms continuous support, robust change −5.0273 st, no contamination/instability. Existing classification **4-like / moderate / acoustic_shape_only**, contextual T4, legacy **matches**, new **consistent**. The latest four recordings do not contain an eligible consistent character; the UI does not force one.

## Previous useful recordings retained

The 15 earlier takes remain independently addressable; the former Trust Pass's “latest” labels are historical, not this pass's selection.

| UTC timestamp | Transcript | Perception ID | Canonical SHA-256 |
|---|---|---|---|
| 2026-10-02T14:51:20.001932+00:00 | 我想买五把雨伞。 | `7787300e-d43a-48d2-bf1d-121e11761af9` | `0dd0e4a9dd5ca6bd87a83077ad69f2f8193fbe8b73bbfee49290055630baf3fe` |
| 2026-10-02T14:52:03.084658+00:00 | 我想买五把雨伞 | `c95673d3-ab32-443c-b2cd-49c5f95c8a45` | `2cbbdf2874d68e478891309fc69ce2f814ba393003324cd933a5c244ed951c8d` |
| 2026-10-02T15:19:32.327506+00:00 | 我要一个苹果。 | `0f4107fe-5c8f-49ac-8302-63070cbadfca` | `d76f1adcaa80df3bff443bb4f3534bd97d3c51d0d7586d813bff3a5fd2e4bb4a` |
| 2026-10-02T15:21:11.403659+00:00 | 我们去吧 | `f3c642b5-ef7b-451a-8e96-ec7e143338d9` | `6dc1af68387a1ca93096567233d01ab918c40493e49b2c9c6cfcfb7687c1ad8f` |
| 2026-10-02T15:25:32.507541+00:00 | 我们要去贵州。 | `f47fadb3-63a6-4445-9c11-3b2170de9343` | `978db669aa6dfeb1fdf25dc07f2de89034d2c3736d34d4c04b3f8b096a9db1e2` |
| 2026-10-02T19:19:29.518506+00:00 | 我想买五把雨伞。 | `a0270cee-2e62-41b3-b266-cec08c185226` | `b50de95b98256488786e9f146ce08afc70cb3c3d5d2629c45cc92057fdfa1fa5` |
| 2026-10-02T19:20:07.268747+00:00 | 现在是下午两点半。 | `de4b999e-a527-4613-8709-618c68716477` | `c95cc5554d4f682bb899d12e17509468dc870ade24ea896eb3d98755d05087e4` |
| 2026-10-02T19:23:25.955471+00:00 | 我要一个苹果。 | `484e80c0-cc41-49ab-9623-ba09d71a7458` | `901ce949f0df0426e89b1e4cf91d7a2d33e26455146527de0968f336b295dd22` |
| 2026-10-02T19:24:09.462939+00:00 | 我们去吧。 | `e59a6350-6631-43bd-ab64-7f02a6ed377a` | `8e1a5cd68783e51ba012233b3df32854296102f523b67207c8702868afa4ef0e` |
| 2026-10-02T19:24:53.758159+00:00 | 贵州。 | `f5dc0cc1-cd1f-4721-918b-9357f33774e1` | `a5917bbbb3f969a001f88da190c204dbc19e21089e7fc3eb0c1616229f7819ef` |
| 2026-10-02T23:32:46.556503+00:00 | 其实我不行 | `ab6c16ab-ece9-4d00-a3f9-ca693d103624` | `6f8c2f58de72ce69fce08125091c12b6194d517f5e6752fdba556b9f25e789d1` |
| 2026-10-02T23:34:52.005699+00:00 | 我想买五把雨伞。 | `1a927887-320c-4f15-876e-60648b472c8c` | `66b6ec23a83c8e96417e1832df7bebb0692f204c1f7ef80208bcc59723eccafc` |
| 2026-10-02T23:36:05.974350+00:00 | 我要一个苹果。 | `5ca771a7-ad1f-42a0-b7ee-20babc4a1385` | `bdfea0fa05fbda85a29f595e9261debfd31d34754d85d918e3a32c0b9a8f8248` |
| 2026-10-02T23:37:43.979291+00:00 | 我们去吧。 | `209ef0c7-c22b-4e74-af1c-391892040d29` | `0ed2c58291c4acbe98b56eec67027b8027f9e9ba3995b62ae772695a5771a794` |
| 2026-10-02T23:38:29.504301+00:00 | 贵州 | `87ac7dd1-702e-46af-92f5-652507487d51` | `9c2c3828fa4362188ff5e1e87f00747f42adda3dba76399e1595191d0bfc48d3` |

Earlier exact utterance/attempt provenance is also retained in the local inventory and [Trust Pass](../2026-10-02-pitch-reliability/trust-pass.md#exact-recording-identity). Both silence controls remain rejected: no product contour or comparison is emitted for them.
