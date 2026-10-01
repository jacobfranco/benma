# Experiment 2 post-hoc diagnostic error audit — 2026-09-30

**Recommendation: prediction-blind human realized-tone audit first. Cropping is not currently well justified as the next experiment.** The overall edge low-energy fractions are nearly identical for correct and wrong clips, and within-speaker directions disagree. Fresh T3 errors contain several distinct patterns; the severe tracker-jump pattern found in Luilui is not a universal explanation. The data raise representation/head questions but do not yet establish which correctly realized tones defeat A.

This directory analyzes **all 118 opened/inspected fresh-panel clips**, with the 13 already-inspected Luilui T3 clips as a separate stress comparison. These clips must never again be described as pristine for future model selection. A remains the learned baseline; temporal-thirds B is not promoted. B gained two T3 correct predictions but lost four T2 correct predictions in Experiment 2. This audit reads A's saved outputs and runs only the existing Benma/Praat diagnostic pipeline. No learned classifier was trained or executed, no hyperparameters were tuned, and no lexical labels, production thresholds, API behavior, or mobile behavior changed.

**Evidence language:** **FACT** denotes reproducible measurements or saved results; **DESCRIPTIVE ASSOCIATION** denotes a pattern within this small, selected, opened panel; **HYPOTHESIS** denotes an unverified mechanism. None of the comparisons below establishes causality, population generalization, phonation mechanism, or pronunciation correctness. No significance tests are used.

## Artifacts and measurement boundary

- [per-clip.csv](per-clip.csv): exactly 118 identities, immutable lexical labels, saved A probabilities/correctness/margin, and acoustic diagnostics.
- [error-groups.csv](error-groups.csv): count, missing count, median, quartiles, and range for overall, tone-error, speaker, and speaker × tone × correctness groups. Empty groups remain explicit.
- [speaker-summary.csv](speaker-summary.csv): speaker and per-tone counts/confusion, accuracy, and full text/pinyin composition.
- [t3-audit.csv](t3-audit.csv): all 29 fresh lexical-T3 clips, retaining the complete quality/geometry evidence and probabilities. A compact reading table appears below.
- [luilui-t3-comparison.csv](luilui-t3-comparison.csv): exactly 13 separate stress rows, measured with the same new waveform boundary rule. This additional file prevents mixing the stress set into the 118-row panel.
- [human-audit/index.html](human-audit/index.html) and [blank annotation template](human-audit/annotations-template.csv): prediction-blind local listening workflow.
- [provenance.json](provenance.json), [environment.md](environment.md): input/audio/source hashes, parameters, runtime, reproduction and validation.

No plots are added: the distributions, per-speaker controls, and identity-linked T3 table expose the relevant heterogeneity without implying fitted relationships. No raw audio or hidden-state arrays are copied into this directory.

**FACT — definitions.** Originals are hash-checked against the existing manifests, then decoded temporarily to mono 16-kHz PCM16 using FFmpeg. Acoustic extraction accepts only an audio path. Identity, lexical tone, and A output join after extraction. The current `PraatAcousticAnalyzer`, evidence-region selection, filtering, and contour classification are imported unchanged. V1 timing is the whole isolated clip, not a reproduced production alignment.

The additional waveform metric uses nonoverlapping 10-ms RMS blocks, including the partial final block. Its fixed threshold is `max(.003, min(3 × q10(block RMS), .15 × peak block RMS), .20 × peak block RMS)`. The `.20 × peak` term dominates the noise-floor cap, so this is equivalent to `max(.003, .20 × peak block RMS)`. Leading/trailing durations extend from the file edge to the first/last above-threshold block. Active duration counts **all** above-threshold samples; active-span duration includes intervening below-threshold blocks. Active RMS uses the actual retained waveform samples, not an average of frame RMS values. Fractions use full decoded duration. No smoothing, correctness-dependent choice, or fitted boundary parameter is used.

**Low energy is not verified silence.** This rule can remove quiet consonants or soft speech tails and can be dominated by a brief amplitude peak. For example, correctly classified Jouketou `等` has 86.1% edge low-energy by this rule despite substantial tracked voicing. These measurements do not authorize automatic cropping. No-active boundaries are blank; active coverage is zero. None of the 118 clips has zero active waveform blocks.

`active_speech_missing_f0_fraction` and `active_periodicity_*_waveform` use Praat frames whose centers fall in active waveform blocks. Missing F0 includes unvoiced consonants and tracking failures; it does not identify which. `voiced_fraction` is the current Benma post-energy-gate voiced-frame count divided by all Praat frames, not sample coverage. Older `active_missing_fraction` and `active_periodicity_mean` columns are retained for compatibility with the prior Luilui audit and use its separate Praat-frame RMS gate; do not silently interchange the two definitions. For Luilui the old active missingness median is 16.7%, versus 7.4% with the new waveform-block definition.

Periodicity is selected-candidate Praat autocorrelation strength, not a calibrated probability or direct creak measurement. F0 minima/medians are tracked values; retained range is smoothed, filtered evidence in semitones. Broad thirds are equal elapsed-time thirds of the retained voiced span; gaps are not imputed. Bin dip/recovery requires an interior five-bin minimum and both limbs ≥1.5 st; thirds dip/recovery requires first→middle ≤−1 st and middle→final ≥1 st. These are geometry descriptors, not new classifiers or relabeling. V1's actual verdict remains separate.

Production maximum jump uses successive available voiced points separated by at most 120 ms; octave-like jumps are 9–15 st. Instability uses the unchanged production rejection flag. Raw internal gaps count missing 10-ms frame support between voiced observations, excluding edge loss. A zero maximum jump or false instability flag can mean **no usable F0**, not clean speech; consult coverage and missing-value counts. `孔`, for example, has a 32.70-st retained range but only a 3.25-st maximum production jump and 140 ms total internal missing support. Range and jump statistics need not agree: longer-gap transitions do not enter the latter. Absent numeric F0/shape fields remain blank; geometry flags are false when required evidence is unavailable.

All distribution cells below are per-clip **median [25th–75th percentile]**, using linear-interpolated quartiles. F0/range/shape denominators exclude unavailable values: 2/14 T3→T4 clips have no F0; their absence must not be interpreted as zero pitch. Small-group quartiles describe those observations only.

## A-correct versus A-wrong

**FACT.** Saved A is 81/118 (68.64% accuracy; 68.30% balanced accuracy; macro F1 .66769). B was 78/118 (66.10%; 65.75%; .64956). A's true-row/predicted-column matrix remains `[[26,0,0,4], [4,19,4,2], [2,4,9,14], [0,0,3,27]]`.

| Measure | A-correct, n=81 | A-wrong, n=37 |
|---|---:|---:|
| Duration (s) | 0.883 [0.808–0.960] | 0.883 [0.797–1.036] |
| Edge low-energy (%) | 66.9 [57.8–72.4] | 66.3 [62.6–71.7] |
| Estimated active samples (%) | 31.0 [25.8–38.6] | 29.5 [25.1–34.8] |
| Whole-clip RMS | 0.0478 [0.0351–0.0668] | 0.0532 [0.0421–0.0694] |
| Active-sample RMS | 0.0898 [0.0587–0.1258] | 0.1012 [0.0806–0.1260] |
| Benma/Praat voiced frames (%) | 36.0 [30.2–45.5] | 36.2 [21.1–40.8] |
| Missing F0 in active frames (%) | 7.7 [0.0–18.2] | 14.3 [0.0–45.0] |
| Mean active-frame periodicity | 0.776 [0.660–0.880] | 0.738 [0.424–0.873] |
| Maximum production tracker jump (st) | 0.96 [0.53–1.99] | 1.01 [0.67–2.51] |
| Median tracked F0 (Hz) | 100.8 [91.4–164.3] | 99.5 [86.6–160.9] |
| A maximum probability | 0.889 [0.761–0.950] | 0.778 [0.568–0.859] |
| A top-1 minus top-2 margin | 0.804 [0.617–0.928] | 0.627 [0.242–0.802] |

**DESCRIPTIVE ASSOCIATION.** Wrong clips have more active-frame missing F0 and a lower periodicity median, especially a worse lower tail. Whole-clip duration and voiced-fraction medians are almost identical. RMS is slightly higher among errors, and median register/jump magnitudes are similar. Instability flags occur in 7/37 wrong versus 10/81 correct clips; internal raw gaps occur in 16/37 versus 21/81. These variables overlap substantially and do not yield one acoustic explanation. A confidence/margin are lower among errors, but eight errors still have A probability ≥.9; uncalibrated model confidence does not establish realized-tone truth.

## Edge low energy and the cropping decision

**FACT.** Overall edge low-energy fraction is **66.9% correct versus 66.3% wrong**. Leading duration is .250 versus .280 s; trailing duration is .337 versus .343 s. These small shifts do not add up to a higher overall error-group edge fraction. The conditional directions matter:

| Group | Correct edge fraction median | Wrong edge fraction median | Correct / wrong n |
|---|---:|---:|---:|
| Jouketou, all tones | 56.2% | 64.5% | 33 / 7 |
| 雲角, all tones | 68.1% | 66.7% | 24 / 16 |
| Fake estate, all tones | 72.3% | 69.4% | 24 / 14 |
| Jouketou, T2 | 51.9% | 32.4% | 9 / 1 |
| 雲角, T2 | 61.4% | 66.2% | 5 / 5 |
| Fake estate, T2 | 69.0% | 63.1% | 5 / 4 |

| Measure | T2 correct, n=19 | T2 errors, n=10 |
|---|---:|---:|
| Duration (s) | 0.894 [0.844–0.960] | 1.036 [0.904–1.036] |
| Edge low-energy (%) | 57.8 [52.6–63.2] | 64.4 [59.4–66.1] |
| Estimated active samples (%) | 39.3 [34.8–45.5] | 34.9 [32.3–38.0] |
| Missing F0 in active frames (%) | 5.8 [0.0–13.8] | 1.1 [0.0–9.5] |
| Mean active-frame periodicity | 0.833 [0.675–0.898] | 0.820 [0.743–0.903] |

**DESCRIPTIVE ASSOCIATION.** Aggregate T2 errors have more edge low energy (64.4% versus 57.8%) and less active coverage (34.9% versus 39.3%), but this is not consistently reproduced within speakers. T2 errors actually have less median active missing F0 (1.1% versus 5.8%), so a universal tracking-quality account also fails. T3→T4 has more edge low energy in aggregate (71.7% versus 55.4% for correct T3), but its composition is predominantly Fake estate, with no correct T3 control for that speaker. Among 雲角's T3s, all errors have *less* edge low energy than its two correct T3s (68.1% versus 72.5%); even its three T3→T4s have a lower median (71.8%).

**Conclusion: edge silence is not consistently implicated, and cropping is NOT currently well justified as the immediate next experiment.** This proxy cannot rule out individual boundary problems or show how an encoder treats padding. More padding in a selected aggregate subgroup is insufficient evidence for a primary crop ablation.

**HYPOTHESIS / deferred option.** If independent listening and boundary inspection later establish material excess padding, a low-priority controlled ablation could use this fixed waveform rule, keep the envelope from first to last active block with 100-ms context on both sides clipped to the file, retain internal gaps, and preserve the full waveform when no block is active. It would depend only on waveform evidence, never expected tone, lexical tone, or model correctness. The rule is a candidate, not validated segmentation: freeze it before future sealed evaluation and verify that it preserves quiet speech on separate development material. Do not run it now or select among crop settings on this opened panel.

## Speaker comparison

**FACT.** A accuracy/error rate is Jouketou 33/40 = 82.5% / 17.5%; 雲角 24/40 = 60.0% / 40.0%; Fake estate 24/38 = 63.2% / 36.8%.

| Measure | Jouketou | 雲角 | Fake estate |
|---|---:|---:|---:|
| Duration (s) | 0.824 [0.759–0.879] | 1.036 [0.943–1.059] | 0.883 [0.797–0.883] |
| Edge low-energy (%) | 57.3 [52.8–65.4] | 67.2 [63.6–71.5] | 71.9 [65.9–78.2] |
| Estimated active samples (%) | 37.2 [29.7–44.3] | 32.4 [27.0–35.2] | 25.1 [21.5–30.3] |
| Whole-clip RMS | 0.0416 [0.0347–0.0503] | 0.0745 [0.0682–0.0892] | 0.0420 [0.0330–0.0485] |
| Active-sample RMS | 0.0678 [0.0513–0.0903] | 0.1335 [0.1204–0.1635] | 0.0808 [0.0567–0.0990] |
| Benma/Praat voiced frames (%) | 45.1 [34.6–53.5] | 37.3 [31.8–41.6] | 30.1 [20.6–32.5] |
| Missing F0 in active frames (%) | 8.2 [3.6–16.7] | 0.0 [0.0–11.8] | 24.5 [6.9–43.9] |
| Mean active-frame periodicity | 0.791 [0.657–0.876] | 0.862 [0.755–0.913] | 0.626 [0.413–0.756] |
| Maximum production tracker jump (st) | 1.56 [0.66–6.35] | 0.92 [0.61–1.51] | 0.87 [0.58–1.43] |
| Median tracked F0 (Hz) | 86.4 [80.1–98.9] | 172.6 [163.4–193.3] | 94.1 [88.9–104.4] |
| A maximum probability | 0.876 [0.716–0.937] | 0.826 [0.673–0.909] | 0.854 [0.694–0.962] |
| A top-1 minus top-2 margin | 0.798 [0.531–0.888] | 0.744 [0.430–0.855] | 0.760 [0.481–0.933] |
| Minimum tracked F0 (Hz) | 72.1 [68.7–86.2] | 151.2 [138.9–164.3] | 86.1 [80.9–92.4] |
| Retained pitch range (st) | 7.39 [5.06–8.95] | 6.45 [3.11–9.23] | 3.70 [2.06–5.50] |

Jouketou / 雲角 / Fake estate instability counts are **11/40, 5/40, 1/38** respectively. The low Fake estate count is not proof of good tracking: two clips have no F0, and its active missingness is highest. Jouketou is the most accurate despite having the most instability flags. 雲角 has the strongest median periodicity and zero median active-frame missingness, yet the lowest overall learned accuracy. These counterexamples rule out treating one tracker-quality scalar as a sufficient speaker explanation.

**FACT — per-tone predicted counts (T1,T2,T3,T4):**

| Speaker | True T1 | True T2 | True T3 | True T4 |
|---|---|---|---|---|
| Jouketou | [10,0,0,0] | [0,9,1,0] | [0,0,7,3] | [0,0,3,7] |
| 雲角 | [7,0,0,3] | [1,5,3,1] | [1,4,2,3] | [0,0,0,10] |
| Fake estate | [9,0,0,1] | [3,5,0,1] | [1,0,0,8] | [0,0,0,10] |

Lexical composition is nearly tone-balanced: 10 of each tone for Jouketou and 雲角, and [10,9,9,10] for Fake estate. However, **the words are almost entirely unmatched**: Jouketou/雲角 share only `腿`; Jouketou/Fake estate share only `州` and `砸`; 雲角/Fake estate share none. Unique pinyin counts are 39/40, 39/40, and 35/38. The full inventory is in speaker-summary.csv. Tone balance does not control syllable, consonant, vowel, lexical selection, recording style, or capture conditions.

**DESCRIPTIVE ASSOCIATION.** Jouketou has shorter files, less edge low energy, more active/voiced coverage, lower recorded level and lower tracked register than 雲角; Fake estate has the smallest active fraction and weakest active-frame tracking. Their learned confusion patterns differ substantially: Fake estate never receives T3 anywhere, whereas 雲角 spreads T3 across all outputs and misses many cleanly tracked T2s. Confidence medians differ only moderately and overlap.

**HYPOTHESIS.** Speaker-associated distribution shift, syllable composition, capture conditions, and a mismatch between frozen features and the linear decision boundary are plausible contributors. This audit does not separate them or measure feature-distribution distance to training speakers. It does not infer gender, age, ethnicity, accent identity, native status, or physiology from pitch or other measurements.

## All 29 fresh lexical-T3 cases

**FACT — outcome partitions:** correct T3 **9** (Jouketou 7, 雲角 2); T3→T4 **14** (Jouketou 3, 雲角 3, Fake estate 8); T3→T1 **2** (雲角 1, Fake estate 1); T3→T2 **4**, all 雲角. These partitions exhaust all 29 and preserve lexical T3 throughout.

| Measure | T3 correct, n=9 | T3→T4, n=14 | Luilui T3, n=13 |
|---|---:|---:|---:|
| Edge low-energy (%) | 55.4 [54.5–72.0] | 71.7 [67.1–77.7] | 74.2 [69.4–76.2] |
| Estimated active samples (%) | 29.7 [25.4–40.2] | 24.9 [18.6–27.4] | 24.8 [22.7–29.5] |
| Benma/Praat voiced frames (%) | 45.5 [33.3–51.9] | 18.6 [8.0–32.5] | 33.7 [27.5–34.9] |
| Missing F0 in active frames (%) | 7.7 [2.8–35.9] | 39.2 [14.9–76.2] | 7.4 [3.8–14.3] |
| Mean active-frame periodicity | 0.713 [0.498–0.789] | 0.426 [0.151–0.652] | 0.671 [0.622–0.769] |
| Maximum production tracker jump (st) | 2.15 [1.39–4.75] | 2.10 [0.95–6.91] | 18.26 [13.01–21.09] |
| Median tracked F0 (Hz) | 77.6 [73.5–91.4] | 86.6 [82.3–102.5] | 188.6 [168.0–203.5] |
| Minimum tracked F0 (Hz) | 69.5 [66.1–72.8] | 76.6 [68.3–80.7] | 100.4 [64.4–147.3] |
| Retained range (st) | 5.81 [5.79–7.62] | 3.63 [2.73–8.65] | 21.55 [17.90–22.43] |
| Middle→final third (st) | 2.11 [-0.73–3.16] | 0.02 [-0.63–3.30] | -1.42 [-6.64–8.60] |
| Five-bin post-minimum recovery (st) | 3.19 [2.13–4.45] | 0.64 [0.16–3.72] | 4.87 [0.00–15.51] |

Correct T3s have 2/9 instability flags, versus 4/14 T3→T4. Internal raw gaps occur in 4/9 versus 9/14; median internal missing support is 0 versus 40 ms. Bin dip/recovery occurs in 7/9 versus 3/14, and broad thirds dip/recovery in 4/9 versus 3/14. V1 recognizes `3-like` in 3/9 correct T3s. All 14 T3→T4s are V1-unclear: nine insufficient voicing, four tracker instability, one fragmented voicing. This is a description of the current whole-clip acoustic gates, not proof all fourteen are badly pronounced.

The table below is diagnostic and must **not** be given to a blind auditor. Full T1–T4 probabilities, leading/trailing durations, F0 minima/range/gaps and contour values are in t3-audit.csv. “Dip” is the bin/thirds geometry flag pair; these are apparent tracked shapes, not human judgments. Missing F0 is measured only among active waveform-frame centers. “Unstable” is the production flag, not absence/presence of every tracking problem.

| Asset suffix | Speaker | Character / pinyin | A output (max p) | Active missing F0 | Edge low energy | Max jump st | Unstable | Dip bins/thirds | Current V1 evidence |
|---|---|---|---:|---:|---:|---:|---|---|---|
| 124566721 | Fake estate | 耍 shua3 | T4 (0.694) | 100.0% | 67.1% | 0.00 | no | no/no | unclear: insufficient_voicing |
| 124567108 | Fake estate | 宰 zai3 | T4 (0.602) | 86.7% | 79.6% | 2.51 | no | no/no | unclear: insufficient_voicing |
| 124567179 | Fake estate | 吼 hou3 | T4 (0.892) | 100.0% | 81.7% | 0.00 | no | no/no | unclear: insufficient_voicing |
| 124568191 | Fake estate | 党 dang3 | T4 (0.902) | 14.3% | 79.9% | 0.79 | no | no/no | unclear: insufficient_voicing |
| 124568202 | Fake estate | 犬 quan3 | T4 (0.446) | 76.9% | 67.1% | 1.42 | no | no/no | unclear: insufficient_voicing |
| 124568239 | Fake estate | 染 ran3 | T4 (0.778) | 52.6% | 78.5% | 1.70 | no | no/no | unclear: insufficient_voicing |
| 124600312 | Fake estate | 孔 kong3 | T4 (0.972) | 45.0% | 62.4% | 3.25 | no | no/no | unclear: insufficient_voicing |
| 124684589 | Fake estate | 啃 ken3 | T4 (0.840) | 33.3% | 71.7% | 1.41 | no | no/no | unclear: insufficient_voicing |
| 124684682 | Fake estate | 眨 zha3 | T1 (0.511) | 78.9% | 76.2% | 0.17 | no | no/no | unclear: insufficient_voicing |
| 147755085 | Jouketou | 等 deng3 | T3 (0.852) | 9.1% | 86.1% | 2.15 | no | yes/yes | 3-like: acoustic_shape_only |
| 147755199 | Jouketou | 敢 gan3 | T3 (0.589) | 37.5% | 72.0% | 7.37 | yes | yes/no | unclear: tracker_instability |
| 147778624 | Jouketou | 老 lao3 | T3 (0.494) | 7.7% | 55.4% | 6.01 | yes | yes/no | unclear: tracker_instability |
| 147778695 | Jouketou | 嘴 zui3 | T4 (0.501) | 26.1% | 61.2% | 8.13 | yes | yes/yes | unclear: tracker_instability |
| 147778719 | Jouketou | 马 ma3 | T3 (0.380) | 35.9% | 54.5% | 2.28 | no | no/no | unclear: insufficient_voicing |
| 147779345 | Jouketou | 腿 tui3 | T4 (0.823) | 16.7% | 72.3% | 10.30 | yes | yes/yes | unclear: tracker_instability |
| 147779367 | Jouketou | 米 mi3 | T4 (0.919) | 8.0% | 66.3% | 8.73 | yes | yes/yes | unclear: tracker_instability |
| 147794898 | Jouketou | 雪 xue3 | T3 (0.750) | 2.8% | 55.4% | 2.10 | no | yes/yes | 3-like: acoustic_shape_only |
| 147795021 | Jouketou | 左 zuo3 | T3 (0.981) | 0.0% | 53.7% | 1.22 | no | yes/yes | 3-like: acoustic_shape_only |
| 147795048 | Jouketou | 鼠 shu3 | T3 (0.547) | 3.7% | 39.2% | 4.75 | no | yes/yes | unclear: insufficient_voicing |
| 71028935 | 雲角 | 小 xiao3 | T3 (0.865) | 51.9% | 70.3% | 1.10 | no | no/no | unclear: insufficient_voicing |
| 71028938 | 雲角 | 短 duan3 | T2 (0.677) | 0.0% | 67.2% | 1.60 | no | no/no | unclear: insufficient_voicing |
| 71028939 | 雲角 | 窄 zhai3 | T4 (0.921) | 73.9% | 71.8% | 0.63 | no | no/no | unclear: insufficient_voicing |
| 71029001 | 雲角 | 口 kou3 | T1 (0.568) | 3.7% | 68.1% | 0.91 | no | no/no | 4-like: acoustic_shape_only |
| 71029011 | 雲角 | 腿 tui3 | T4 (0.980) | 0.0% | 75.3% | 3.03 | no | no/no | unclear: fragmented_voicing |
| 71029015 | 雲角 | 手 shou3 | T2 (0.971) | 25.5% | 56.6% | 21.07 | yes | yes/yes | unclear: tracker_instability |
| 71029034 | 雲角 | 乳 ru3 | T4 (0.667) | 0.0% | 71.4% | 13.60 | yes | no/no | unclear: tracker_instability |
| 71029061 | 雲角 | 死 si3 | T3 (0.496) | 0.0% | 74.6% | 1.39 | no | yes/no | unclear: insufficient_voicing |
| 71029076 | 雲角 | 走 zou3 | T2 (0.675) | 0.0% | 68.1% | 1.01 | no | yes/yes | 3-like: acoustic_shape_only |
| 71029085 | 雲角 | 挤 ji3 | T2 (0.831) | 12.8% | 57.5% | 0.83 | no | yes/yes | 3-like: acoustic_shape_only |

**DESCRIPTIVE ASSOCIATION — multiple T3→T4 patterns, not one coherent mechanism.**

- **Little or no tracked F0:** Fake estate `耍` (124566721) and `吼` (124567179) have no F0 at all; `宰` and `犬` have 86.7% and 76.9% active missingness. 雲角 `窄` has 73.9%. Across the 14, six have ≥50% active missing F0, while two have zero. A missingness threshold therefore cannot summarize all failures.
- **Jump/recovery ambiguity:** Jouketou `嘴`, `腿`, `米` all contain apparent bin and thirds fall/recovery while A predicts T4. Their maximum jumps are 8.13, 10.30, and 8.73 st and V1 flags instability. 雲角 `乳` has a 13.60-st jump with zero active missingness. Recovery geometry can coexist with dubious branch selection.
- **Falling/limited or fragmented evidence without severe production jumps:** Fake estate `党` has a shallow falling retained trajectory, .79-st maximum jump, one 40-ms gap and 14.3% active missingness, but low whole-clip voiced coverage. 雲角 `腿` has zero active missingness, .870 active periodicity, one 10-ms raw gap and a 3.03-st maximum jump; V1 calls it fragmented. These are different from either total pitch loss or Luilui-scale repeated octave ambiguity. Neither constitutes independently verified “clean pronunciation.”

**Other T3 errors are informative controls.** T3→T1 includes Fake estate `眨` (78.9% active missingness) and 雲角 `口` (3.7%, no internal gaps, .91-st maximum jump, .878 voiced periodicity). `口` is V1 `4-like`, a relatively clean predominantly falling track resembling the *measurement pattern* of Luilui `你`; A actually chooses T1, not T4. No fresh T3→T4 receives a reliable V1 `4-like` verdict under the unchanged whole-clip gates. Thus the clean-falling `你` analogy exists in the broader T3 error set but should not be asserted for all fourteen T3→T4s.

T3→T2 comprises 雲角 `短`, `手`, `走`, `挤`. Median active missingness is 6.4%, active periodicity .838 and maximum jump 1.31 st. `手` is the unstable exception (21.07 st); `走` and `挤` have no raw internal gaps, small jumps (1.01/.83 st), and V1-recognized `3-like` dip/recovery even though A chooses T2. `短` has an apparent later rise with zero active missingness but an insufficient-whole-clip-voicing verdict. These observations warrant human confirmation before claiming a learned representation failure on correctly realized speech.

**FACT — Luilui comparison.** Large-jump instability is **11/13 Luilui T3s**, versus **4/14 fresh T3→T4s**, or **5/20 all fresh T3 errors**. Luilui's median production maximum jump is 18.26 st and retained range 21.55 st, versus 2.10 st and 3.63 st for fresh T3→T4. The latter jump median includes production zero values for the two absent tracks; those zeroes are not evidence of clean pitch. Luilui remains A-correct 2/13, with 8→T4 and 3→T1, including the previously human-inspected `你`. Its median tracked register (188.6 Hz) is much higher than fresh T3→T4 (86.6 Hz), despite low branches within its own trajectories; “low” is not a universal absolute-Hz phenotype. Median edge low energy is 74.2%, similar to the padded fresh T3→T4 group, while active missingness under the same waveform rule is only 7.4% versus 39.2%.

**Conclusion.** Some fresh cases resemble Luilui's tracker-jump ambiguity, others have far less F0 evidence, and some broader T3 failures have relatively clean falling or dipping tracks. No single acoustic-quality variable establishes an explanation for most T3→T4 mistakes. Insufficient whole-clip voicing is a frequent V1 reason, but that composite gate does not distinguish padding, unvoiced segments, and tracker loss. The independent wav2vec model never consumes Benma F0 or its quality flags, so these cannot mechanically cause its learned errors.

## What remains unknown, and the next experiment decision

**FACT:** lexical labels come from the frozen metadata; no new human realized-tone annotations exist. Current F0 evidence can describe a fall, recovery, dropout, or ambiguous branch without identifying the speaker's realized tone. Acoustic “cleanliness” is also only partially measured.

**HYPOTHESES still unresolved:** target/realization mismatch; quiet or unvoiced segments versus tracker failure; actual pitch irregularity versus subharmonic/octave selection; acoustic/syllable/capture distribution shift; encoder information loss versus linear-head limitations. The present study cannot apportion errors to these mechanisms. Confidence is not correctness, a V1 match is not human gold, and temporal thirds losing does not establish that all temporal information is useless.

**Exact immediate next step:** a Mandarin-speaking auditor should annotate **all 118 clips** using only the blind page and save a complete ID-keyed file, leaving uncertain realizations explicitly unclear. Preserve lexical targets. Have disagreements/unclear examples reviewed independently where feasible. Freeze annotations before joining them to A or reading this diagnostic table. Then report lexical-target and audited-realization agreement separately, retaining unclear/other/wrong-syllable outcomes and coverage rather than silently dropping hard clips. This is annotation work, not Experiment 3 model evaluation.

The next **model** experiment is conditional; there is no scientifically justified unconditional variant to launch now:

| Later audit result | Next action |
|---|---|
| Important errors reflect target/realization mismatch | Prioritize adjudicated evaluation labels and collection quality; do not change the model to fit misleading labels. Keep the frozen lexical column and audited realization as separate fields. |
| A substantial subset is independently confirmed as correctly realized and reasonably tracked, but A still fails | Design one controlled representation/head ablation. A useful first question is head capacity: hold encoder, layer-8 full-clip mean pooling, training rows, preprocessing and evaluation protocol fixed, and compare the frozen linear-head baseline against one preregistered low-capacity nonlinear head. Freeze its exact capacity/training/stopping settings using development material before sealing new evaluation; no grid on these 118 clips. This tests linear-head limitation, not whether the encoder itself is better. |
| Audited failure is concentrated in acoustic difficulty | Retain these stress cases and investigate independent pitch/boundary annotation and additional matched recordings before assuming a head change can solve them. Do not discard valid difficult tones. |
| Independent boundary evidence later contradicts this weak/inconsistent edge association | Consider the deferred waveform-only crop ablation, changing only cropping with the same frozen encoder/full-mean scheme. It is not the immediate recommendation. |

No representation/head experiment is warranted **yet as the next action** solely because B lost. It becomes justified after the clean/correctly-realized condition is established. Do not stack crop, temporal pooling, encoder and head changes. Do not repeat temporal thirds without materially new evidence. Any future comparison uses these opened clips only as descriptive development/stress diagnostics and requires newly collected, speaker-separated, sealed evaluation for fresh model-selection claims. A remains the baseline until a controlled experiment earns a change.

## Prediction-blind human audit: local workflow

The page's clip payload contains only source ID, speaker ID/pseudonym, character, lexical pinyin/tone, and local audio filename. IDs support deterministic joins but are not presented as pronunciation evidence. No A/B prediction, probability, correctness, learned confidence, or acoustic verdict is present in the HTML, JavaScript data, or attributes. Displayed target text can still prime a listener: this is prediction-blind, **not target-blind**.

1. Open `human-audit/index.html` directly in a browser (tested in Chromium). No web server or network is required.
2. Select `/home/jacob/benma/benchmark/corpus/recordings/original/experiment-2-preflight/commons` with **Audio folder**, or select its WAV files with the fallback picker. The page resolves the exact existing filenames to browser-local Blob URLs; it neither downloads nor copies audio into the report. Selecting the folder grants the browser access to those files for this session.
3. Listen and select T1/T2/T3/T4, neutral/other, unclear, or wrong syllable / target mismatch. Optional listening certainty is low/medium/high and is an **auditor annotation**, not model confidence. Notes are optional. Initially all annotations are blank. Previous/Next or Go to item navigates all 118 in deterministic source-ID order.
4. Each input updates localStorage under `benma-exp2-realized-audit-v1` if available. Storage is specific to this browser/profile/origin, can be disabled for local files, and may be cleared. It is convenience persistence, not a durable backup.
5. **Save annotations (JSON)** downloads the ID-keyed state and schema. Save regularly and before closing. **Restore saved JSON** replaces the current state after validating IDs and allowed values; save current work before restoring. Reselect audio after reopening; browser Blob URLs do not persist.
6. **Export CSV** downloads all 118 rows, including blank unannotated rows and properly quoted notes. Join uniquely on `source_asset_id`, never row number or character. The supplied blank `annotations-template.csv` supports a spreadsheet-only annotation workflow; copy it to a separate working file and keep IDs/targets unchanged. CSV is an export, while JSON is the supported browser restore format.

Give the auditor the blind page/template and local audio, **not review.md, t3-audit.csv, or per-clip.csv** before saving their annotations. No human annotations were fabricated. Browser tests used clearly marked synthetic responses solely in temporary files/profile and removed them afterward.

## Validation

See [environment.md](environment.md) for exact commands, final checks and the distinction between full extraction replay and artifact-only verification. Full deterministic replays already matched every generated CSV/HTML/provenance byte. Final browser validation covers rendering, navigation, browser persistence, CSV quoting/unique joins, JSON save/restore, invalid import rejection, and decoding/playing an existing local WAV. No staged files, commits, pushes, production edits, or label changes are part of this audit.
