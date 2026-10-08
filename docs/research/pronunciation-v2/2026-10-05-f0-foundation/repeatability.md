# Audio-only repeatability and benign perturbations

## Final RMVPE extension

The 36 prior audio-only DTW paths are reused byte-for-byte. On the closest take_1/take_3 repeat, RMVPE raw has **2.07 s mutual voice, .027/.096-st median/p90 disagreement, 1.000 broad correlation, .996 V/UV agreement, 0/207 octave disagreements and island difference 3**. Gate .05 gives 2.02 s, .027/.093 st, .983 V/UV agreement and island difference 0. This improves shared speech over AC's 1.82 s and CREPE clean's 1.68 s while avoiding baseline's doubled onset/weak late rise.

For take_1/take_2 and take_2/take_3, raw median/p90 is .520/2.717 and .651/2.432 st, correlation .832/.799, octave disagreements 4/209 and 5/132. These pairs include genuine performance differences. RMVPE is not uniformly superior on every repeat dimension.

Native canonicalization/gain/bandpass raw p90 disagreement is .002/.069/.091 st; correlations 1.000/.998/.991; V/UV agreement 1.000/.969/1.000. Gain produces one raw octave disagreement in the uncertain tail, removed by gate .05 with reduced coverage. Updated [tables](repeatability-tables.md) and CSVs contain all six trackers. The original five-tracker interpretation below is historical; the final result remains unsafe because of separate negative/synthetic failures.

**No candidate unambiguously beats Praat AC on repeated pitch agreement while also fixing its systematic errors.** CREPE better preserves the difficult onset/late-rise trajectories, but its smoother raw path includes background. pYIN's excellent conditional agreement comes with substantial missing voice. Harvest is least stable around real boundaries.

## Alignment and interpretation

Whole-waveform F0 extraction precedes alignment. A shared acoustic-only DTW path is built from 32 log-spectral bands spanning 80–4000 Hz, 40-ms Hann windows and 10-ms hops, with per-frame centering/L2 normalization. Analysis support uses RMS ≥max(.0015, .08×95th-percentile RMS), with 150-ms margins. DTW uses cosine distance, a 25% normalized-time band and .025 cost for horizontal/vertical steps. No transcript, character boundary, tracker F0 or expected pitch enters that path.

Each A frame maps to the median B index along its DTW matches, avoiding duplicate weighting during long holds. Pitch comparison uses nearest native frames within half a native hop; it never fills missing values. Mutual duration is 10 ms times the mutually voiced count on A's aligned grid, not a claim about identical physical duration in both captures. The broad correlation uses local 50-ms medians on existing mutual samples, leaving gaps absent. V/UV agreement is over acoustic-active aligned pairs. Octave disagreement is >9 st; fragmentation difference is the absolute whole-track island-count difference.

All 36 pairs of the nine sentence-family files are exported, but only the newest trio is the main repeat comparison. Old human/Google/unlinked captures are not assumed to share one playback source. Even the newest takes are not byte-identical inputs, and take_2 differs in timing/prosody. A difference can be real, alignment-related or an estimator error; these metrics alone cannot assign causality.

| Pair | Aligned spectral cosine | Log-energy correlation | Interpretation |
| --- | --- | --- | --- |
| take_1 / take_3 | .969 | .987 | Strongest acoustic repeat |
| take_1 / take_2 | .936 | .962 | Less similar source/timing/prosody |
| take_2 / take_3 | .931 | .939 | Less similar source/timing/prosody |

## Strongest repeat: take_1 / take_3

230 active aligned frames; raw and clean columns below must be read together.

| Tracker/view | Mutual duration | Median / p90 abs st | Broad correlation | V/UV agreement | >9-st disagreements | Island difference |
| --- | --- | --- | --- | --- | --- | --- |
| AC raw | 1.82 s | .030 / .102 | 1.000 | .904 | 0/182 | 1 |
| AC production | 1.73 s | .029 / .102 | 1.000 | .926 | 0/173 | 4 |
| CC raw | 1.90 s | .044 / .161 | .956 | .913 | 2/190 | 1 |
| CC clean | 1.86 s | .043 / .147 | 1.000 | .909 | 0/186 | 1 |
| pYIN raw | 1.40 s | .000 / .100 | .999 | .822 | 0/140 | 1 |
| pYIN clean | .87 s | .000 / .100 | 1.000 | .939 | 0/87 | 1 |
| Harvest raw/clean | 1.48 s | .094 / 7.394 | .810 | .787 | 11/148 (7.4%) | 2 |
| CREPE raw | 2.30 s | .129 / .378 | .980 | 1.000 | 0/230 | 0 |
| CREPE clean | 1.68 s | .109 / .263 | .999 | .970 | 0/168 | 3 |

AC strongly repeats its melody **and its wrong doubled onset/weak late-rise shape**. Consistency does not prove correctness. CREPE clean retains the broad rise more faithfully in the spectral review and provides the best V/UV repeat agreement here, but its .263-st p90 is worse than AC's .102, and it fails separate negative/low-register tests. Raw CREPE's perfect V/UV agreement is automatic because every frame has pitch.

pYIN's .100-st p90 reflects quantized native estimates and a shrinking common subset: cleanup retains only 87/230 active pairs. It is not evidence of a complete, superior utterance foundation. Harvest's 11 octave-disagreement frames explain the large p90 despite its small median.

For pairs involving take_2, AC raw p90 is 2.94/2.76 st, pYIN 2.75/2.60, Harvest 6.81/2.82, CREPE 3.72/3.72. CREPE cleanup improves its p90 to 2.83/2.48 with 1.50/1.04 seconds shared; its broad correlations are .910/.961. These differences include real source/prosodic variation. A tracker cannot be rewarded for forcing different performances to match.

Production AC changes take_1/take_2 median/p90 .389/2.937 to .400/2.925 and take_2/take_3 .441/2.760 to .409/2.710, while removing shared frames. It does not resolve a foundation problem through repeatability alone. [Full tables](repeatability-tables.md) include all raw/clean/production newest comparisons, durations, disagreement counts/rates and fragmentation; [CSV](pairwise-repeatability.csv) includes all 396 rows and acoustic alignment diagnostics.

## Three already-frozen source transformations

The exact digital reference is compared at identical times to its app-normal 16-kHz canonicalization, quarter-gain PCM16 copy, and 100–3500-Hz bandpass copy. There is no DTW for these transformations. All statistics cover .03–.99 seconds, so ambiguous tail changes remain visible instead of being excluded after seeing results.

Gain changes barely affect conditional F0 for every tracker. Canonicalization has raw p90 disagreement below .057 st for every tracker, with no >9-st disagreement. This is encouraging but covers one short source only.

| Tracker | Bandpass raw median / p90 st | Broad correlation | V/UV agreement | >9-st disagreements |
| --- | --- | --- | --- | --- |
| AC | .002 / .019 | 1.000 | .948 | 0 |
| CC | .003 / .043 | −.503 | .896 | 4 |
| pYIN | .000 / .100 | 1.000 | 1.000 | 0 |
| Harvest | .007 / 16.481 | .293 | .979 | 20 |
| CREPE | .000 / .000 | .997 | 1.000 | 0 |

CC illustrates why median/p90 alone is inadequate: a few severe tail changes invert broad correlation. Harvest changes much more in the weak tail. CREPE's quantized/Viterbi pitch path is very stable here; this does not certify its continuous raw tail as vocal. Cleanup changes its bandpass V/UV agreement to .969, with unchanged conditional median/p90 pitch. Full raw/clean correlation, coverage and octave counts are in [source-perturbations.csv](source-perturbations.csv).
