# Region results (unblinded after extraction)

**MEASURED OBSERVATION:** saved timing/pitch plus independent waveform measurements. No target or phone label was an extraction input. All spans are provider evidence, not independently verified boundaries. No pronunciation correctness judgment is available.

These tables join the separately stored key only after verifying the sealed blind packet. See [method](method.md) for definitions and fixed guards and [feasibility](segmental-feasibility.md) for interpretation.

## Selection and exact timing

| ID | Region | Source unit | Span ms | Duration ms | Selection |
| --- | --- | --- | --- | --- | --- |
| R01 | S13 贵 | u3 | 2550-2900 | 350 | lexical_substitution_control_not_phonetic_gold |
| R02 | S03 果 | u6 | 3130-3590 | 460 | recovered_timing |
| R03 | S03 你 | u0 | 950-1230 | 280 | acoustic_evidence_control_not_gold |
| R04 | S01 说 | u11 | 5910-6000 | 90 | recovered_timing |
| R05 | S02 我 | u0 | 910-1330 | 420 | acoustic_evidence_control_not_gold |
| R06 | S01 气 | u3 | 3210-3460 | 250 | recovered_timing |
| R07 | S01 说 | u10 | 5810-5900 | 90 | recovered_timing |
| R08 | S02 饭 | u10 | 4820-5250 | 430 | user_reported_possible_issue_not_gold |
| R09 | S02 上 | u4 | 2200-2550 | 350 | recovered_timing |
| R10 | S02 吃 | u9 | 4430-4810 | 380 | recovered_timing |
| R11 | S03 想 | u1 | 1240-1580 | 340 | acoustic_evidence_control_not_gold |
| R12 | S13 州 | u4 | 2910-3370 | 460 | lexical_substitution_control_not_phonetic_gold |

## Saved pitch and voicing evidence

Raw missingness uses existing raw gated F0; selected counts use exactly the saved selection and quality flag. Runs are contiguous selected-frame supports, not independent voicing duration. Candidate strength is not a calibrated probability.

| ID | Usable/total | Raw voiced fraction | Raw missing % | Selected missing % | Median Hz | Min-max Hz | Longest run ms | Existing instability frames |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | 14/35 | 0.400 | 60.0 | 60.0 | 126.9 | 101.8-140.8 | 140.0 | 0 |
| R02 | 0/46 | 0.000 | 100.0 | 100.0 | — | —-— | 0.0 | 0 |
| R03 | 20/28 | 0.714 | 28.6 | 28.6 | 130.1 | 128.0-508.8 | 190.0 | 0 |
| R04 | 2/9 | 0.222 | 77.8 | 77.8 | 105.0 | 104.3-105.6 | 20.0 | 0 |
| R05 | 32/42 | 0.762 | 23.8 | 23.8 | 116.0 | 105.2-430.9 | 300.0 | 0 |
| R06 | 0/25 | 0.000 | 100.0 | 100.0 | — | —-— | 0.0 | 0 |
| R07 | 5/9 | 0.556 | 44.4 | 44.4 | 106.5 | 106.0-106.9 | 50.0 | 0 |
| R08 | 11/43 | 0.302 | 69.8 | 74.4 | 108.9 | 103.0-109.6 | 110.0 | 5 |
| R09 | 3/35 | 0.086 | 91.4 | 91.4 | 120.8 | 114.6-122.4 | 20.0 | 0 |
| R10 | 0/38 | 0.000 | 100.0 | 100.0 | — | —-— | 0.0 | 0 |
| R11 | 19/34 | 0.559 | 44.1 | 44.1 | 114.8 | 110.9-126.0 | 170.0 | 0 |
| R12 | 15/46 | 0.326 | 67.4 | 67.4 | 475.0 | 130.7-504.6 | 70.0 | 0 |

| ID | First usable (ms:Hz) | Midpoint ±10 ms (ms:Hz) | Last usable (ms:Hz) | Longest-run slope Hz/s | Mean saved strength |
| --- | --- | --- | --- | --- | --- |
| R01 | 131.3:140.1 | 171.3:134.5 | 261.3:101.8 | -344.5 | 0.327 |
| R02 | — | — | — | — | 0.000 |
| R03 | 4.0:508.8 | 144.0:131.6 | 214.0:134.1 | 53.7 | 0.607 |
| R04 | 1.7:105.6 | — | 11.7:104.3 | — | 0.150 |
| R05 | 4.7:430.9 | 214.7:116.6 | 384.7:105.5 | -80.9 | 0.607 |
| R06 | — | — | — | — | 0.000 |
| R07 | 41.7:106.0 | 41.7:106.0 | 81.7:106.9 | 18.8 | 0.354 |
| R08 | 164.7:109.1 | 214.7:109.6 | 264.7:103.0 | -54.6 | 0.292 |
| R09 | 94.7:122.4 | — | 214.7:114.6 | — | 0.286 |
| R10 | — | — | — | — | 0.000 |
| R11 | 84.0:115.5 | 174.0:111.5 | 304.0:125.6 | 69.0 | 0.449 |
| R12 | 81.3:145.9 | — | 451.3:481.0 | -262.1 | 0.264 |

## Waveform and spectrum

RMS is digital amplitude, not SPL. Spectra are whole-span frame medians except the explicitly labeled RMS envelope mean. **All twelve near-full-scale sample fractions are zero.** No SNR was measured.

| ID | Whole RMS | RMS envelope mean/median | Centroid Hz | Bandwidth Hz | 85% rolloff Hz | ≥4 kHz fraction | ZCR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | 0.0809 | 0.0699/0.0515 | 715 | 1038 | 844 | 0.0154 | 0.1153 |
| R02 | 0.0413 | 0.0392/0.0359 | 764 | 1072 | 969 | 0.0308 | 0.1529 |
| R03 | 0.2736 | 0.2635/0.2702 | 381 | 883 | 375 | 0.0140 | 0.0777 |
| R04 | 0.0355 | 0.0296/0.0256 | 875 | 1455 | 1969 | 0.0592 | 0.1629 |
| R05 | 0.2687 | 0.2439/0.2161 | 590 | 726 | 766 | 0.0124 | 0.0927 |
| R06 | 0.0314 | 0.0296/0.0240 | 2139 | 1851 | 4250 | 0.2024 | 0.3158 |
| R07 | 0.0570 | 0.0555/0.0604 | 565 | 878 | 656 | 0.0169 | 0.0902 |
| R08 | 0.0526 | 0.0481/0.0448 | 696 | 1022 | 969 | 0.0297 | 0.1228 |
| R09 | 0.0444 | 0.0419/0.0394 | 743 | 1324 | 1469 | 0.0444 | 0.1554 |
| R10 | 0.0387 | 0.0356/0.0291 | 1775 | 1504 | 3781 | 0.1377 | 0.2494 |
| R11 | 0.1034 | 0.0957/0.0885 | 685 | 953 | 1109 | 0.0198 | 0.1165 |
| R12 | 0.0734 | 0.0610/0.0430 | 778 | 1148 | 1109 | 0.0384 | 0.1353 |

## Formant feasibility

All values below describe the fixed Burg attempt. `Passing` means joint frame sanity only, not accepted vowel evidence. Support span is the first-to-last passing center and may contain gaps. F1/F2/F3 availability counts finite raw estimates before bandwidth/bounds checks. All accepted summaries remain **null**.

| ID | Candidate relative ms | Attempted | Raw F1/F2/F3 available | Passing | Passing-center span ms | Rejected | Adjacent jumps | Outcome / reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | 126.3-266.3 | 9 | 9/9/9 | 6 | 80.0 | 3 | 0 | quality_abstention; insufficient_sanity_pass_fraction |
| R02 | absent | 0 | 0/0/0 | 0 | 0.0 | 0 | 0 | no_candidate; — |
| R03 | 29.0-219.0 | 14 | 14/14/14 | 2 | 10.0 | 12 | 0 | quality_abstention; insufficient_passing_frames, insufficient_sanity_pass_fraction |
| R04 | absent | 0 | 0/0/0 | 0 | 0.0 | 0 | 0 | no_candidate; — |
| R05 | 89.7-389.7 | 25 | 25/25/25 | 6 | 110.0 | 19 | 0 | quality_abstention; insufficient_sanity_pass_fraction |
| R06 | absent | 0 | 0/0/0 | 0 | 0.0 | 0 | 0 | no_candidate; — |
| R07 | 36.7-86.7 | 0 | 0/0/0 | 0 | 0.0 | 0 | 0 | insufficient_support; — |
| R08 | 159.7-269.7 | 6 | 6/6/6 | 1 | 0.0 | 5 | 0 | quality_abstention; insufficient_passing_frames, insufficient_sanity_pass_fraction |
| R09 | absent | 0 | 0/0/0 | 0 | 0.0 | 0 | 0 | no_candidate; — |
| R10 | absent | 0 | 0/0/0 | 0 | 0.0 | 0 | 0 | no_candidate; — |
| R11 | 79.0-249.0 | 12 | 12/12/12 | 8 | 100.0 | 4 | 0 | quality_abstention; insufficient_sanity_pass_fraction |
| R12 | 76.3-146.3 | 2 | 2/2/2 | 2 | 10.0 | 0 | 0 | quality_abstention; insufficient_passing_frames |

## Prefix / onset feasibility

Prefix ends at the longest saved voiced-run candidate, so it may contain earlier voicing, transitions, neighboring sound, or missed pitch. It is **not an isolated initial**. No confirmed aperiodic duration is available for any region. Large centroid IQRs indicate changing spectral content; no stability classifier is used.

| ID | Prefix ms | Full FFT frames | Saved raw voiced frames in prefix | Centroid median/IQR Hz | ≥4 kHz fraction median | Result |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | 126.3 | 11 | 0 | 888/259 | 0.0482 | generic_prefix_available |
| R02 | — | 0 | — | — | — | unresolved |
| R03 | 29.0 | 1 | 1 | — | — | insufficient_support |
| R04 | — | 0 | — | — | — | unresolved |
| R05 | 89.7 | 7 | 2 | 806/184 | 0.0543 | generic_prefix_available |
| R06 | — | 0 | — | — | — | unresolved |
| R07 | 36.7 | 2 | 0 | — | — | insufficient_support |
| R08 | 159.7 | 14 | 0 | 2316/2518 | 0.3004 | generic_prefix_available |
| R09 | — | 0 | — | — | — | unresolved |
| R10 | — | 0 | — | — | — | unresolved |
| R11 | 79.0 | 6 | 0 | 3784/703 | 0.3855 | generic_prefix_available |
| R12 | 76.3 | 6 | 0 | 3870/1280 | 0.4106 | generic_prefix_available |

## Evidence-quality representation

No overall score. Every region is waveform/spectrum-analyzable under the supplied span, and every boundary remains unvalidated. The full independent flags are:

- **R01**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, heavy_raw_F0_missingness, nucleus_candidate_available, formants_unavailable, formant_summary_abstained, prefix_spectrum_available; embedding_available.
- **R02**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, F0_missing, heavy_raw_F0_missingness, insufficient_saved_voicing, formants_unavailable, onset_window_unresolved; embedding_available.
- **R03**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, nucleus_candidate_available, formants_unavailable, formant_summary_abstained, onset_window_unresolved; embedding_available.
- **R04**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, insufficient_saved_pitch, heavy_raw_F0_missingness, insufficient_saved_voicing, formants_unavailable, onset_window_unresolved; embedding_available.
- **R05**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, nucleus_candidate_available, formants_unavailable, formant_summary_abstained, prefix_spectrum_available; embedding_available.
- **R06**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, F0_missing, heavy_raw_F0_missingness, insufficient_saved_voicing, formants_unavailable, onset_window_unresolved; embedding_available.
- **R07**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, nucleus_candidate_available, formants_unavailable, onset_window_unresolved; embedding_available.
- **R08**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, heavy_raw_F0_missingness, tracker_instability, nucleus_candidate_available, formants_unavailable, formant_summary_abstained, prefix_spectrum_available; embedding_available.
- **R09**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, insufficient_saved_pitch, heavy_raw_F0_missingness, insufficient_saved_voicing, formants_unavailable, onset_window_unresolved; embedding_available.
- **R10**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, F0_missing, heavy_raw_F0_missingness, insufficient_saved_voicing, formants_unavailable, onset_window_unresolved; embedding_available.
- **R11**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, nucleus_candidate_available, formants_unavailable, formant_summary_abstained, prefix_spectrum_available; embedding_available.
- **R12**: timing_valid, enough_audio_duration, boundary_not_independently_validated, spectral_measurement_available, saved_pitch_available, heavy_raw_F0_missingness, nucleus_candidate_available, formants_unavailable, formant_summary_abstained, prefix_spectrum_available; embedding_available.

## Frozen representation

Twelve 768-dimensional block-6 mean-pooled vectors; unchanged frozen CPU encoder; all per-crop repeats bitwise equal. No labels, distances, head or classification.

| ID | Hidden frames pooled |
| --- | --- |
| R01 | 17 |
| R02 | 22 |
| R03 | 13 |
| R04 | 4 |
| R05 | 20 |
| R06 | 12 |
| R07 | 4 |
| R08 | 21 |
| R09 | 17 |
| R10 | 18 |
| R11 | 16 |
| R12 | 22 |

## Control ranking

Eligible nonfocal S02/S03 regions, descending selected-frame fraction then count. The first three were selected. Source unit labels are revealed only here.

| Study | Unit | Usable fraction | Usable frames | Selected |
| --- | --- | --- | --- | --- |
| S02 | u0 | 0.762 | 32 | yes |
| S03 | u0 | 0.714 | 20 | yes |
| S03 | u1 | 0.559 | 19 | yes |
| S02 | u1 | 0.452 | 14 | no |
| S03 | u3 | 0.333 | 10 | no |
| S03 | u5 | 0.207 | 6 | no |
