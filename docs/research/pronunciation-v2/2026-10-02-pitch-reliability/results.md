# Results

> **Superseded by the [Trust Pass](trust-pass.md).** The second real silence case exposed a periodic-background false accept. Current behavior adds post-ASR acoustic corroboration, removes default reference-tone labels, and keeps the primary pitch tracker. The content below records the earlier pass.

## Exact local inventory

All timestamps UTC on 2026-10-02. All ten canonical WAVs exist and match their database SHA-256. No other take identity is inferred.

| Case | Heard text | UTC | Perception ID |
|---|---|---|---|
| R0 | 我想买五把雨伞。 | 14:51:20 | `7787300e-d43a-48d2-bf1d-121e11761af9` |
| R1 | 我想买五把雨伞 | 14:52:03 | `c95673d3-ab32-443c-b2cd-49c5f95c8a45` |
| R2 | 我要一个苹果。 | 15:19:32 | `0f4107fe-5c8f-49ac-8302-63070cbadfca` |
| R3 | 我们去吧 | 15:21:11 | `f3c642b5-ef7b-451a-8e96-ec7e143338d9` |
| R4 | 我们要去贵州。 | 15:25:32 | `f47fadb3-63a6-4445-9c11-3b2170de9343` |
| R5 | 我想买五把雨伞。 | 19:19:29 | `a0270cee-2e62-41b3-b266-cec08c185226` |
| R6 | 现在是下午两点半。 | 19:20:07 | `de4b999e-a527-4613-8709-618c68716477` |
| R7 | 我要一个苹果。 | 19:23:25 | `484e80c0-cc41-49ab-9623-ba09d71a7458` |
| R8 | 我们去吧。 | 19:24:09 | `e59a6350-6631-43bd-ab64-7f02a6ed377a` |
| R9 | 贵州。 | 19:24:53 | `f5dc0cc1-cd1f-4721-918b-9357f33774e1` |

Exact canonical provenance:

- R0: utterance `d357de4a-a8e7-4290-af23-dbc8eabadc6b`; SHA-256 `0dd0e4a9dd5ca6bd87a83077ad69f2f8193fbe8b73bbfee49290055630baf3fe`.
- R1: utterance `d3cc24ce-88fc-4846-bddb-5a819837e404`; SHA-256 `2cbbdf2874d68e478891309fc69ce2f814ba393003324cd933a5c244ed951c8d`.
- R2: utterance `8a006ed3-8e45-4fd2-b35c-675a86d073c0`; SHA-256 `d76f1adcaa80df3bff443bb4f3534bd97d3c51d0d7586d813bff3a5fd2e4bb4a`.
- R3: utterance `56a5ecec-5f46-4b32-af60-026439c64ac0`; SHA-256 `6dc1af68387a1ca93096567233d01ab918c40493e49b2c9c6cfcfb7687c1ad8f`.
- R4: utterance `e3cee950-d217-4653-b3d4-c206668c81aa`; SHA-256 `978db669aa6dfeb1fdf25dc07f2de89034d2c3736d34d4c04b3f8b096a9db1e2`.
- R5: utterance `adab4e2b-8b2a-4206-8406-0ce1e25cf501`; SHA-256 `b50de95b98256488786e9f146ce08afc70cb3c3d5d2629c45cc92057fdfa1fa5`.
- R6: utterance `4e48d583-ff3f-4a53-8a60-a5f01877aa14`; SHA-256 `c95cc5554d4f682bb899d12e17509468dc870ade24ea896eb3d98755d05087e4`.
- R7: utterance `17ac23f5-5812-4704-8cb0-451f2c9eb12e`; SHA-256 `901ce949f0df0426e89b1e4cf91d7a2d33e26455146527de0968f336b295dd22`.
- R8: utterance `03c70bf4-996b-4ce3-8657-43aaef97f8bf`; SHA-256 `8e1a5cd68783e51ba012233b3df32854296102f523b67207c8702868afa4ef0e`.
- R9: utterance `3105301c-dc5c-4487-94f4-5386154e638c`; SHA-256 `a5917bbbb3f969a001f88da190c204dbc19e21089e7fc3eb0c1616229f7819ef`.

R4 target: `我们要去广州`; R9 target: `广州`. T3 targets were saved as `我想买五吧雨伞`; graph identity correctly retains perceived 把. R6 is the unique saved hallucination matching `现在是下午两点半。`.

## Generic audio quality

| Case | Duration s | RMS | Peak | RMS p10 / p50 / p90 | Frames RMS <.003 |
|---|---:|---:|---:|---|---:|
| R0 | 7.895 | 0.02023 | 0.164 | 0.0021 / 0.0029 / 0.0394 | 51.7% |
| R1 | 3.924 | 0.07678 | 0.528 | 0.0033 / 0.0463 / 0.1243 | 9.0% |
| R2 | 2.276 | 0.04202 | 0.232 | 0.0023 / 0.0266 / 0.0766 | 20.7% |
| R3 | 2.206 | 0.02041 | 0.152 | 0.0023 / 0.0031 / 0.0396 | 46.5% |
| R4 | 3.088 | 0.02417 | 0.168 | 0.0022 / 0.0086 / 0.0442 | 29.0% |
| R5 | 3.831 | 0.02713 | 0.173 | 0.0031 / 0.0199 / 0.0438 | 9.5% |
| R6 | 6.780 | 0.00613 | 0.536 | 0.0031 / 0.0038 / 0.0053 | 7.4% |
| R7 | 2.067 | 0.04150 | 0.227 | 0.0047 / 0.0166 / 0.0761 | 3.5% |
| R8 | 2.392 | 0.03353 | 0.319 | 0.0030 / 0.0040 / 0.0670 | 12.0% |
| R9 | 1.625 | 0.05103 | 0.525 | 0.0032 / 0.0055 / 0.0855 | 7.0% |

All canonical audio is mono PCM16 at 16 kHz; clipping fraction is zero for every recording. Nine speech recordings have ordinary usable levels, not broadly weak/clipped input. This does not establish microphone quality, SNR, or periodic phonation throughout every vowel. Pauses dominate some whole-recording coverage denominators.

R6 is not digital silence: RMS .00613 and peak .536 reflect low background plus a click. The presence guard measures background RMS .00303; the longest elevated-activity run is three 10-ms hops (~40 ms including the 20-ms window), and broad AC produces no finite voiced frames. Saved ASR evidence contains token logprobs but no no-speech probability. The guard does not use token meaning or confidence to make its decision.

## Tracker comparison

Each cell is **finite frames / islands / median runtime ms**. AC50 control equals production raw frequencies; native grids differ when floor/method changes.

| Case | Production raw | AC50 control | CC50 | AC40 | CC40 | Final production retained |
|---|---|---|---|---|---|---|
| R0 | 214/17/106.41 | 214/17/4.80 | 245/24/10.59 | 214/17/5.12 | 251/24/12.42 | 189/14 |
| R1 | 233/10/55.73 | 233/10/2.87 | 233/11/4.74 | 236/8/3.23 | 244/9/6.69 | 226/10 |
| R2 | 112/5/32.04 | 112/5/1.43 | 113/5/3.00 | 114/6/1.57 | 122/7/4.35 | 107/5 |
| R3 | 58/5/31.08 | 58/5/1.81 | 84/10/3.20 | 57/5/1.71 | 80/7/4.56 | 27/2 |
| R4 | 139/6/43.40 | 139/6/2.25 | 144/7/3.85 | 137/6/2.36 | 147/8/5.03 | 122/4 |
| R5 | 262/14/52.89 | 262/14/2.50 | 272/13/4.19 | 265/12/2.64 | 269/12/6.07 | 175/7 |
| R6 | 0/0/91.88 | 0/0/3.75 | 0/0/7.19 | 0/0/3.82 | 0/0/10.51 | 0/0 |
| R7 | 94/6/31.92 | 94/6/2.36 | 106/8/3.60 | 96/6/2.54 | 111/9/5.55 | 80/4 |
| R8 | 45/4/33.18 | 45/4/1.42 | 57/6/3.18 | 52/5/1.52 | 56/5/4.55 | 38/2 |
| R9 | 28/3/23.44 | 28/3/1.60 | 27/2/2.46 | 29/3/1.83 | 28/3/3.35 | 28/3 |

Aggregate counts include the no-speech negative control. All methods returned zero F0 on that control.

| Method | Finite/total (%) | Islands | Singletons / short | >6 st / octave jumps | Isolated octave excursions | Periodic-looking missing/total | Aperiodic pitch/total | Median runtime ms |
|---|---|---:|---|---|---:|---|---|---:|
| production | 1185/3554 (33.3%) | 70 | 0 / 10 | 1 / 1 | 1 | 298/1268 | 0/346 | 38.29 |
| ac50 | 1185/3554 (33.3%) | 70 | 0 / 10 | 1 / 1 | 1 | 296/1266 | 0/348 | 2.31 |
| cc50 | 1281/3574 (35.8%) | 86 | 2 / 18 | 2 / 2 | 0 | 287/1267 | 0/351 | 3.73 |
| ac40 | 1200/3539 (33.9%) | 68 | 0 / 10 | 2 / 2 | 2 | 276/1268 | 0/351 | 2.45 |
| cc40 | 1308/3564 (36.7%) | 84 | 0 / 18 | 3 / 3 | 1 | 292/1289 | 1/345 | 5.29 |
| production_selected | 992/3554 (27.9%) | 51 | 1 / 11 | 1 / 1 | 1 | 377/1268 | 0/346 | included above |

Every tracker is exactly repeatable across three runs. All have zero pitch in the RMS <.0003 frames. CC50 raises coverage from 33.3% to 35.8% while islands rise 70→86, short islands 10→18 and adjacent large jumps 1→2. AC40 adds little coverage and doubles the octave-excursion proxy; CC40 adds an aperiodic-frame pitch. No candidate qualifies. Production selected retains 992/1185 raw-finite frames; application gates are responsible for 193 losses, separately from 2369 tracker-missing frames.

## Key per-unit attrition

Each row uses its saved provider interval, not a phonetic gold boundary. E = finite after energy gate; S = acoustic selection; retained = final display selection before simplification.

| Case / unit | Interval s | Frames | Raw finite | E / S / retained | Mine points / segments | Cause |
|---|---|---:|---:|---|---|---|
| R0 我 | [0.35, 0.96) | 61 | 19 | 19 / 19 / 19 | 6 / 1 | 42 tracker missing |
| R0 想 | [0.97, 1.38) | 41 | 31 | 31 / 31 / 31 | 7 / 1 | 10 tracker missing |
| R0 买 | [1.39, 1.9) | 51 | 20 | 20 / 20 / 20 | 14 / 4 | 31 tracker missing |
| R0 五 | [2.31, 2.84) | 53 | 33 | 33 / 33 / 33 | 12 / 1 | 20 tracker missing |
| R0 把 | [2.85, 3.37) | 52 | 30 | 29 / 29 / 29 | 19 / 2 | 22 tracker missing; 1 energy rejected |
| R0 雨 | unavailable | — | — | — | 0 / 0 in Mine cell | No timing; identity/reference remain |
| R0 伞 | unavailable | — | — | — | 0 / 0 in Mine cell | No timing; identity/reference remain |
| R2 一 | [0.94, 1.14) | 20 | 18 | 18 / 18 / 18 | 8 / 1 | 2 tracker missing |
| R3 去 | [0.66, 0.78) | 12 | 8 | 8 / 8 / 8 | 6 / 1 | 4 tracker missing |
| R3 吧 | [0.79, 1.07) | 28 | 0 | 0 / 0 / 0 | 0 / 0 | 28 tracker missing |
| R4 贵 | [1.76, 2.57) | 81 | 28 | 22 / 22 / 22 | 8 / 1 | 53 tracker missing; 6 energy rejected |
| R4 州 | [2.58, 2.88) | 30 | 18 | 11 / 11 / 11 | 8 / 1 | 12 tracker missing; 7 energy rejected |
| R5 买 | [1.04, 1.5) | 46 | 45 | 29 / 29 / 29 | 10 / 1 | 1 tracker missing; 16 energy rejected |
| R5 五 | [1.53, 1.91) | 38 | 35 | 27 / 27 / 27 | 9 / 1 | 3 tracker missing; 8 energy rejected |
| R7 一 | [1.01, 1.14) | 13 | 13 | 13 / 13 / 13 | 5 / 1 | retained |
| R8 去 | [0.78, 0.91) | 13 | 9 | 9 / 9 / 9 | 4 / 1 | 4 tracker missing |
| R8 吧 | [0.92, 1.24) | 32 | 0 | 0 / 0 / 0 | 0 / 0 | 32 tracker missing |
| R9 贵 | [0.69, 1.05) | 36 | 15 | 15 / 15 / 15 | 8 / 1 | 21 tracker missing |
| R9 州 | [1.06, 1.6) | 54 | 13 | 13 / 13 / 13 | 6 / 2 | 41 tracker missing |

The complete local CSV includes every timed syllable, every untimed identity, each
candidate's finite count, and overlapping diagnostic reasons. In the T3 third take,
83 whole-recording raw-finite frames fail the energy gate; 48 also have contamination
flags. The gated portions include weak ~50–70 Hz branches. This is evidence that filters
matter, but does not establish those branches as valid voice. Removing the gates would
revive the periodic-background failure documented in earlier research. No onset or
classifier abstention gate drives the V2 graph; its selected timestamps come from the
display filter. Simplification removes vertices, not evidence regions.

## Missing 吧

R3 reproduces the exact historical analysis: 去 [0.66,.78) retains eight samples at
.703–.773; 吧 [.79,1.07) has 28 frames, all raw F0 missing. No selected point leaks from
去. AC40 also returns zero; CC50 supplies only four frames, CC40 two. R8 independently
has 32 missing raw frames for 吧; AC40/CC40 return zero and CC50 only one.

Within R3's 吧 interval, RMS spans .00214–.04803 (median .00401). Early candidates include
118 Hz at strength .6354 (.793 s), then .4561 (.803 s); subsequent speech-level frames
have weak/inconsistent candidates and .843–.883 s have none. Later energy approaches
background and candidates concentrate near 50–70 Hz. Praat's selected **unvoiced path**
has strength zero, which must not be confused with all candidate strengths being zero.
The strongest supported explanation is tracker candidate/path instability and declining
acoustic support within this provider window, not downstream display filtering or a
50-Hz floor cutoff. Exact phonation, actual syllable boundaries, and whether some missing
frames are genuinely unvoiced cannot be established from these measurements. No learner
pronunciation judgment is made.

## Suspicious 州 island

R9 raw/retained F0 falls to 134.611 Hz at 1.2027 s, is missing at 1.2127, then tracks
476.266, 467.038 and 462.807 Hz at 1.2227–1.2427. The first transition is **21.876 st**,
not 12 st. The three raw strengths are .5855/.614/.4906 and energy is .112/.101/.088:
they pass energy and periodicity checks. Raw candidates around half that high branch
are weaker, and a coherent lower continuation is not supported on both sides.

It survives existing rules because: the Hampel filter needs contiguous bilateral support;
the short-island rejection needs agreeing preceding **and following** regions; there is
no subsequent finite lower region. The terminal rule only rejects a single downward
11–13 st octave branch during fading energy; this is an upward ~22 st branch. It is a
plausible tracker branch/artifact, already present in raw evidence, not a mobile invention
and not proven genuine vocal F0. CC50 avoids this particular branch (133.6→123.8 Hz), but
CC40 retains a ~491–466 Hz branch and the aggregate CC50 regressions prevent promotion.
There is no justified general multi-recording rule to remove this event without risking
legitimate large pitch movements; no special case for 州 or expected T1 was added.

## Final production choice and display choice

**KEEP CURRENT** `PraatAcousticAnalyzer`, version
`1.2.0-parselmouth-0.4.7-praat-6.1.38`: AC 50–550 Hz, 10 ms step, octave jump .5,
octave cost .01, voiced/unvoiced .14, silence .03, 15 candidates, voicing .45,
very-accurate false. RMS gate `max(.003, min(3*p10_RMS, .15*peak_frame_RMS))`;
70-Hz Hann high-pass comparison, 40–80 Hz spectral dominance / >6 st disagreement
quality guard, and existing bounded downward terminal-octave ambiguity exclusion.
Display: existing 40–1000 Hz/.45 validity checks, bilateral short-island and Hampel
rejection, retained median baseline, within-segment median-of-three, 0.15-st simplification.
No new octave/continuity repair, range adaptation or changed filter thresholds.

No Mine-only bridge: the saved raw transport lacks independent pause/voicing certification
at a missing frame. Compatible endpoints alone do not prove a gap is not unvoiced speech.
The important all-missing syllables and ~22-st branch would not qualify anyway. Every gap,
pause and syllable boundary remains unbridged in Mine, More detail and Raw.

## Robustness and no-speech limits

Ordinary-level, unclipped audio can still yield sparse pitch: the two 吧 windows and the
州 branch are concrete remaining limitations. The comparison does **not** establish
robustness on worse microphones or diverse speakers. It does establish that blindly
lowering thresholds, returning more F0 or joining gaps would weaken evidence quality.
Useful portions remain visible; zero-evidence regions remain blank with their characters.
The selected pitch path is retained because no tested alternative wins, not because it
is proven universally good enough.

The no-speech guard rejects only confident absence: <=1 PCM16 quantization step, or
low stationary background (<.01 centered RMS), no five-frame activity run above
`max(3*background, 3/32768)`, and no broad AC40 voiced frame. Frames for activity are
20 ms with 10 ms hop; background is p20 of frames above one quantization step. An
activity run of five hops corresponds to 60 ms covered audio. Nonzero recordings under
80 ms, any periodic evidence, sustained nonperiodic activity, and louder uncertain audio
continue. The periodicity track has no production energy/quality filter. This separate
guard changes neither raw F0 nor selected pitch. A quiet 90-ms regression motivated
allowing **any** voiced frame rather than requiring three; the exact noise case still
has none. A direct ACF maximum was rejected during guard development because colored
background falsely looked periodic.

No local neural VAD is available; stationary whisper indistinguishable from low noise,
non-speech tonal sound, and complex noise remain limits. No claim to block all ASR
hallucinations is made. Local replay: R6 rejected, other nine accepted; all nine at
0.1× and 0.01× amplitude accepted; nine provider-timed single-character excerpts accepted.
Those excerpts are real audio with provider timing, not independently verified phonetic
gold. All 37 checks passed. Original-record guard time was 3.0–15.8 ms locally.
