# Final corpus metrics

All quality/coverage/label counts below use the 95 timing-authorized spans. Timing-rejected spans remain unclear. Gap durations count missing 10-ms frame slots; octave events here use 10–14 st, while the frozen classifier diagnostic uses 9–15 st.

| Method | Sufficient quality | Classified | Severe fragmentation | Unstable reason | Internal gaps | Missing s | Median coverage | Core p10 / p50 | >6 st jumps | Octave events | Category / tuple changes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| production | 63 | 49 | 10 | 12 | 37 | 1.26 | 0.589 | 0.797 / 1.000 | 21 | 6 | 0 / 0 |
| dp_balanced | 64 | 50 | 10 | 12 | 35 | 1.03 | 0.571 | 0.803 / 1.000 | 22 | 6 | 1 / 2 |
| dp_continuity | 63 | 49 | 4 | 12 | 26 | 0.82 | 0.569 | 0.803 / 1.000 | 19 | 5 | 2 / 3 |
| cc | 56 | 47 | 12 | 14 | 42 | 1.12 | 0.590 | 0.819 / 1.000 | 25 | 7 | 20 / 31 |
| legacy_nac | 27 | 23 | 28 | 56 | 116 | 2.77 | 0.587 | 0.682 / 1.000 | 224 | 77 | 32 / 58 |
| fallback_cc | 63 | 48 | 10 | 11 | 34 | 0.95 | 0.590 | 0.862 / 1.000 | 21 | 6 | 6 / 9 |

Sufficient quality includes ambiguous_shape (adequate F0, no supported category) and all existing certified quality exceptions. Severe fragmentation means ≥2 internal gaps or >80-ms missing run; it is an analysis statistic, not a new production gate.

| Method | Recording median / p95 ms | Single-span WAV median / p95 ms | Amortized per-span median / p95 ms | Confidence changes |
|---|---:|---:|---:|---:|
| production | 25.93 / 77.56 | 24.20 / 38.39 | 23.73 / 34.47 | 0 |
| dp_balanced | 43.34 / 134.40 | 40.12 / 62.79 | 39.45 / 56.93 | 2 |
| dp_continuity | 43.92 / 130.57 | 39.36 / 62.85 | 38.73 / 56.26 | 2 |
| cc | 28.70 / 82.41 | 26.39 / 41.28 | 25.54 / 38.47 | 19 |
| legacy_nac | 535.74 / 1705.36 | 484.22 / 745.03 | 472.57 / 723.63 | 26 |
| fallback_cc | 30.33 / 120.72 | 25.52 / 56.56 | 24.74 / 51.63 | 4 |

Whole-recording times include decoding, both primary/comparison paths and acoustic post-processing, but exclude classifier time. Three rotated repetitions per Praat method; independent estimator once. Single-span WAVs are recordings with exactly one numerical span; no audio was cropped, which could change path selection. Amortized values divide each whole-recording time by its numerical span count. Fallback values are the estimated sum of already-measured primary plus CC cost, excluding trigger overhead.

| Method | Region coverage p10 / p50 / p90 | Fixed production-core coverage p10 / p50 | Gap duration p50 / p95 s | Strong-frame agreements ≤1 st / matched / baseline |
|---|---:|---:|---:|---:|
| production | 0.297 / 0.589 / 0.798 | 0.797 / 1.000 | 0.020 / 0.082 | 1861 / 1861 / 1861 |
| dp_balanced | 0.300 / 0.571 / 0.798 | 0.794 / 1.000 | 0.020 / 0.080 | 1861 / 1861 / 1861 |
| dp_continuity | 0.240 / 0.569 / 0.798 | 0.769 / 1.000 | 0.020 / 0.077 | 1819 / 1819 / 1861 |
| cc | 0.291 / 0.590 / 0.813 | 0.749 / 0.971 | 0.015 / 0.060 | 1811 / 1815 / 1861 |
| legacy_nac | 0.276 / 0.587 / 0.788 | 0.676 / 0.938 | 0.020 / 0.070 | 1838 / 1840 / 1861 |
| fallback_cc | 0.275 / 0.590 / 0.803 | 0.806 / 1.000 | 0.020 / 0.067 | 1859 / 1860 / 1861 |

| Method | 1-like | 2-like | 3-like | 4-like | Unclear |
|---|---:|---:|---:|---:|---:|
| production | 26 | 6 | 7 | 10 | 46 |
| dp_balanced | 26 | 6 | 7 | 11 | 45 |
| dp_continuity | 25 | 6 | 7 | 11 | 46 |
| cc | 19 | 6 | 9 | 13 | 48 |
| legacy_nac | 17 | 2 | 3 | 1 | 72 |
| fallback_cc | 25 | 6 | 9 | 8 | 47 |

| Method | Contaminated spans | Raw/high-pass disagreements >6 st (frames) | Learner verdicts |
|---|---:|---:|---|
| production | 5 | 86 | {'different': 12, 'unclear': 62, 'matches': 14, 'close': 7} |
| dp_balanced | 5 | 86 | {'different': 12, 'unclear': 61, 'matches': 15, 'close': 7} |
| dp_continuity | 6 | 137 | {'different': 12, 'unclear': 62, 'matches': 15, 'close': 6} |
| cc | 8 | 147 | {'different': 13, 'unclear': 64, 'close': 4, 'matches': 14} |
| legacy_nac | 32 | 74 | {'different': 8, 'unclear': 78, 'close': 3, 'matches': 6} |
| fallback_cc | 6 | 89 | {'different': 10, 'unclear': 64, 'matches': 14, 'close': 7} |
