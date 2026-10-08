# Sustained high branch: acoustic forensics and rejected implementation gate

**Outcome D — the entire high run remains acoustically ambiguous. Production unchanged. GRAPH QUALITY STILL BLOCKS CHECKPOINT.**

The premise of a sustained, well-supported half-frequency alternative is not established. The high branch is not trustworthy as a demonstrated continuous fundamental either: its central portion contains a roughly **94 Hz harmonic series**, including odd harmonics that a simple 187 Hz fundamental does not explain. Early and late portions have less regular structure, often stronger short-lag repetition, missing/weak half candidates, and no following trusted F0. This is evidence against treating the whole 353–434 Hz curve as established F0; it is **not** evidence for writing a continuous lower curve into Mine.

This report supersedes the previous pass's proposed next-step premise, without changing that pass's results. It uses no tone expectations, transcript, target, reference contour, new tracker or VAD. No frequency repair, learner grading, UI or graph-scale policy changed.

## Exact reproduction before code changes

The unchanged `PraatAcousticAnalyzer.analyze` was run first, before adding research code. Its complete result is value-identical to the previous frozen baseline. Version: `1.2.0-parselmouth-0.4.7-praat-6.1.38`. Configuration: 50–550 Hz, 10 ms step, octave-jump cost .5, octave cost .01, voicing threshold .45, 15 candidates, existing production energy/quality gates. Full provenance and source hashes are in the [structured evidence](sustained-high-evidence.json).

- Canonical: `services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/8d2522640da64860bd83c33b0b7b7e14.wav`.
- Original: `services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/original/38fdbad3dc624c0997c2eac2bf802d80.m4a`.
- Critical interval: **4.1002–4.3402 s**, inclusive; source indices **407–431**. This is 240 ms between first/last sample centers, **25 frames / 250 ms of hop support**, not 24 frames.
- All 25 raw tracker selections and analyzer selections are high. Frame **4.1302 / 355.918 Hz / .3718 strength** fails the existing display periodicity gate. **24/25 reach selected evidence and Mine source geometry**, in two segments of 3 and 21 frames. Mine simplifies these to **11 vertices**; it does not transmit every source frame as a separate vertex. Exact vertex flags are in the CSV/JSON. This is real-time evidence projection; no character timing was invented.
- All frame energy RMS values exceed the recording's .0098201 gate. Filter-disagreement values do not reject this run. Analyzer reason is `praat_selected` throughout. Only the frame above has `weak_periodicity` in final exclusions.
- The first three-frame display segment fails the old short-island rule's flank conditions; the later segment has no following selected flank. Local Hampel checks have insufficient neighbors at segment edges or deviation below the existing 6 st threshold inside the sustained branch. Every frame's exact guard explanation is preserved.

## Original versus canonical

The original is AAC, stereo, **44.1 kHz**. Both decoded stereo channels are **sample-identical**, ruling out cancellation or changed structure from mono mixing. The direct comparison uses native-rate mono PCM16 decoded from this original and the existing canonical **16 kHz** PCM16, with identical production Praat settings. There is no gain/normalization experiment. Full-recording extraction preserves the path context; it does not extract a small crop and create new path edges.

Reapplying the repository's canonicalization command produces **sample-identical PCM** to the saved canonical WAV. Native/canonical waveform correlation over the exact critical interval is **.9999193**; relative RMS difference is **1.2706%** when comparing the native waveform by linear interpolation at canonical sample times. That includes interpolation, resampling and quantization effects, not a measured vocal difference. Timestamp grids agree to their stored 0.1 ms precision.

All 25 native original high selections agree with canonical within **.013809 st**. Maximum selected-strength difference is **.0007**; the same 24 timestamps survive production selection. Of 135 canonical candidates, 134 match native candidates within 1 Hz; their maximum frequency/strength changes are **.295 Hz / .0015**. The exception is a weak near-floor **49.949 Hz / .3775** canonical candidate at 4.2402, absent in native extraction. This difference is retained in the report; it neither establishes nor strengthens the high/half path.

Spectral overlays at six representative centers show the same harmonic/resonance structure. At 4.2102 the dominant spectral peak is 373.54 Hz canonical versus 373.47 Hz native, and the roughly 279.8/464.4/651.9 Hz peaks also persist. The branch exists equivalently in the original. **Canonicalization is exonerated for this issue.**

## Every frame and candidate evidence

The table reports raw tracker selection, which remains unchanged. `S` is selected candidate strength/periodicity, not a calibrated probability. `A` is the nearest **measured** near-half candidate within 2 st, shown permissively so inconvenient off-octave/weak candidates remain visible. Diagnostic octave support uses the unchanged **1 st** tolerance and **.45** strength floor. `Δ = S − A strength`; negative means the alternative is stronger. `ε` is absolute octave-ratio error in semitones. A dash means no such candidate, never an interpolated half frequency. Other strong candidates are listed as Hz/strength.

Pre distances are absolute semitone distances `selected / alternate` to the last five selected pre-run frames' median, **119.767 Hz** (3.9702–4.0102). This fixed, measured anchor avoids extrapolating a declining trajectory through 250 ms. Following distances are unavailable for **every frame**, since no following selected F0 exists. The separate boundary-only slope comparison appears below. All candidates, including weaker ones, exact reasons, RMS, comparison F0 and Mine membership are in the [29-row CSV](sustained-high-frames.csv) and JSON; four rows are the protected comparison.

| Time s | Raw selected Hz | S | A Hz | A strength | Δ | ε st | Other candidates ≥ .45 (Hz/strength) | Pre distance S/A st | Following S/A st | Production |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 4.1002 | 353.147 | 0.5392 | 180.730 | 0.2989 | 0.2403 | 0.403 | — | 18.720/7.123 | —/— | retained |
| 4.1102 | 356.948 | 0.6115 | 180.248 | 0.4260 | 0.1855 | 0.171 | — | 18.906/7.077 | —/— | retained |
| 4.1202 | 359.970 | 0.6234 | 179.981 | 0.5106 | 0.1128 | 0.000 | — | 19.052/7.051 | —/— | retained |
| 4.1302 | 355.918 | 0.3718 | 176.468 | 0.3536 | 0.0182 | 0.146 | 50.408/0.4596 | 18.856/6.710 | —/— | weak periodicity |
| 4.1402 | 354.440 | 0.5728 | 173.782 | 0.4400 | 0.1328 | 0.339 | 87.939/0.4587 | 18.784/6.445 | —/— | retained |
| 4.1502 | 360.607 | 0.6249 | 176.442 | 0.4057 | 0.2192 | 0.375 | — | 19.082/6.708 | —/— | retained |
| 4.1602 | 369.455 | 0.5385 | 192.963 | 0.3153 | 0.2232 | 0.755 | 54.438/0.4845 | 19.502/8.257 | —/— | retained |
| 4.1702 | 371.528 | 0.5005 | 201.371 | 0.5081 | -0.0076 | 1.397 | — | 19.599/8.996 | —/— | retained |
| 4.1802 | 368.339 | 0.4955 | 200.290 | 0.4749 | 0.0206 | 1.453 | — | 19.450/8.902 | —/— | retained |
| 4.1902 | 359.920 | 0.5396 | 191.635 | 0.3612 | 0.1784 | 1.088 | 52.413/0.4818 | 19.049/8.138 | —/— | retained |
| 4.2002 | 360.152 | 0.6545 | 186.263 | 0.5104 | 0.1441 | 0.585 | 124.419/0.5383, 92.303/0.7467, 73.338/0.5021 | 19.061/7.645 | —/— | retained |
| 4.2102 | 363.351 | 0.7291 | 187.361 | 0.6213 | 0.1078 | 0.533 | 125.739/0.6939, 93.351/0.9026, 74.257/0.6267, 62.424/0.5245, 53.601/0.5894 | 19.214/7.747 | —/— | retained |
| 4.2202 | 363.981 | 0.7452 | 189.017 | 0.6164 | 0.1288 | 0.656 | 127.082/0.7215, 94.041/0.9085, 74.806/0.6308, 62.955/0.5139, 54.025/0.5882 | 19.244/7.899 | —/— | retained |
| 4.2302 | 361.539 | 0.7161 | 190.023 | 0.5331 | 0.1830 | 0.864 | 127.982/0.6414, 94.254/0.7598 | 19.127/7.991 | —/— | retained |
| 4.2402 | 364.336 | 0.6191 | 196.304 | 0.3984 | 0.2207 | 1.294 | — | 19.260/8.554 | —/— | retained |
| 4.2502 | 394.684 | 0.6242 | 204.861 | 0.4762 | 0.1480 | 0.647 | 80.487/0.4609, 67.653/0.5010, 57.556/0.4537 | 20.646/9.293 | —/— | retained |
| 4.2602 | 399.357 | 0.6864 | 202.162 | 0.5207 | 0.1657 | 0.214 | 100.504/0.4741, 80.382/0.5576 | 20.849/9.063 | —/— | retained |
| 4.2702 | 398.212 | 0.6274 | 203.131 | 0.4625 | 0.1649 | 0.346 | — | 20.800/9.146 | —/— | retained |
| 4.2802 | 404.348 | 0.5113 | 211.168 | 0.3925 | 0.1188 | 0.754 | — | 21.064/9.818 | —/— | retained |
| 4.2902 | 407.603 | 0.4713 | 220.939 | 0.3011 | 0.1702 | 1.398 | 56.410/0.7458 | 21.203/10.601 | —/— | retained |
| 4.3002 | 405.531 | 0.5144 | — | — | — | — | 75.701/0.6637, 56.484/0.4500 | 21.115/— | —/— | retained |
| 4.3102 | 413.897 | 0.4871 | — | — | — | — | — | 21.468/— | —/— | retained |
| 4.3202 | 426.216 | 0.5059 | — | — | — | — | — | 21.976/— | —/— | retained |
| 4.3302 | 431.453 | 0.5367 | 207.625 | 0.2508 | 0.2859 | 0.663 | — | 22.188/9.525 | —/— | retained |
| 4.3402 | 433.946 | 0.4882 | — | — | — | — | 102.475/0.5746, 83.699/0.5097 | 22.287/— | —/— | retained |

There are **no near-half candidates even within 2 st** at 4.3002, 4.3102, 4.3202 or 4.3402. The 4.3302 candidate exists but has only .2508 strength. At 4.1702, 4.1802, 4.1902, 4.2402 and 4.2902, the apparent alternate is more than 1 st from an octave relation. Those frames must not be silently counted as exact half-path support.

## Spectral spacing and direct period evidence

Every high-run frame and all four protected low frames have **60 and 100 ms Hann spectra**, with all local peaks above −45 dB up to 2 kHz and energy maxima around selected/half/quarter harmonic hypotheses. The native FFT resolutions are **16.7 and 10 Hz**; the zero-padded grids interpolate peaks and do not add resolution. The spectrogram uses 60 ms windows and 2.5 ms hops. Long windows trade time localization for frequency resolution, so transitions are also checked with **40, 60 and 80 ms unfiltered waveform lag curves**. These are forensic self-similarity measurements, not another F0 tracker or a production estimator.

Representative 60 ms spectral findings (dB relative to each frame's strongest 40–2000 Hz peak):

| Center | Representative peaks Hz (relative dB) | Interpretation |
| --- | --- | --- |
| 4.1002 | 129 (−9), 208 (−7), 249 (−7), 362 (0), 398 (−3); energy near 689/727 is much weaker | Strong high-band oscillation; neither a clean 353-spaced nor 177-spaced harmonic ladder. The weaker near-half candidate alone is insufficient. |
| 4.1702 | 171 (−11), 209 (−8), 341 (−5), 383 (0), 421 (−3), 673 (−8) | Irregular/split peaks and a strong broad high-band component. 201 Hz candidate is not half of 371.5 within 1 st. |
| **4.2102** | **94.5 (−24), 189 (−13), 280 (−11), 373.5 (0), 464 (−13), 559 (−17), 652 (−9), 745 (−29)** | **Approximately 93–94 Hz spacing.** Strong odd harmonics near 280/464/652 support a longer period and cannot be explained by a clean 187 Hz ladder alone. The fourth harmonic is strongest. |
| 4.2602 | 152 (−16), 190 (−14), 298 (−13), 338 (−10), 406 (0), 462 (−9), 562 (−15), 718 (−12) | No stable single 200 Hz or 400 Hz ladder across the window. Returning to a clean half path here would be an inference beyond the measurements. |
| 4.3102 | 169 (−12), 222 (−14), 302 (−6), 388 (0), 430 (−4), 465 (−.1), 509 (−4), 598 (−8), 773 (−7) | Multiple nonmatching components; half candidate absent despite energy around the half-frequency band. Spectral energy is not a measured pitch candidate. |
| 4.3402 | 93 (−17), 183 (−12), 324 (−6), 415 (0), 511 (−2), 601 (−8), 783 (−12), 827 (−7) | Late structure remains irregular. Neither a clean 434 Hz fundamental nor a continuous 217 Hz path is established. |

The roughly 94 Hz central spacing is not inferred from the tallest FFT bin. It follows the **whole ladder, including odd harmonics**, candidate structure and waveform repetition. Conversely, early/late short-lag oscillations are real acoustic energy; they cannot simply be declared impossible high pitch. Intermittent longer-period structure does not license assigning 94 Hz across the whole run.

Waveform self-similarity uses DC-centered, overlap-normalized unfiltered samples. It records all local maxima over 1.5–23 ms, with ±8% neighborhoods around the hypotheses. Representative 60 ms results:

| Center s | Selected-period neighborhood: ms / correlation | Half-frequency period: ms / correlation | Quarter-frequency period: ms / correlation |
| --- | --- | --- | --- |
| 4.1002 | 2.688 / .523 | 5.375 / .307 | 11.375 / ~0 |
| 4.1702 | 2.750 / .528 | 5.000 / .310 | 10.563 / .092 |
| **4.2102** | **2.750 / .700** | **5.313 / .552** | **10.688 / .833** |
| 4.2202 | 2.750 / .690 | 5.313 / .538 | 10.688 / .802 |
| 4.2602 | 2.563 / .575 | 4.875 / .429 | 9.813 / .263 |
| 4.3102 | 2.375 / .503 | 4.750 / .196 | 10.250 / .076 |
| 4.3402 | 2.313 / .435 | 4.750 / .178 | 9.750 / .432 |

At 4.2102, the 10.688 ms correlation exceeds the short-period correlation in **40/60/80 ms** windows: .921/.833/.718 versus .701/.700/.680. At 4.2202 and 4.2302 that advantage becomes less clear in the longest window, as surrounding nonstationarity enters. Early/late frames often favor the short lag over the half lag. The evidence establishes **local longer-period harmonic structure**, not an uninterrupted lower fundamental. Repetition at twice a period alone is never proof of a lower F0: even a perfectly periodic high-F0 signal repeats after two cycles.

## Pre/post trajectory, energy and timbre

At least 300 ms before and after the run are retained in the structured transition evidence. Before: 3.8002–3.9402 is coherent **131.686 → peak 135.316 → 131.208 Hz** with periodicity about .986–.998. It then descends through 129.765, 127.451, 124.830, 122.163, 119.767, 117.433 to **113.531 Hz at 4.0102**; strength falls to .6351. There are **eight unvoiced tracker frames, 4.0202–4.0902**, before 353.147 Hz starts at 4.1002. The endpoint-to-endpoint jump is **+19.646 st**, across 90 ms between voiced sample centers; it is not a measured instantaneous +12 st switch.

After 433.946 Hz at 4.3402, the tracker is unvoiced through the available tail, including the next 300 ms. **There is no octave-scale return and no post-run trusted trajectory.** Filling one from candidates or terminal noise would manufacture context.

There is a substantial energy/envelope change rather than smooth ordinary periodic structure continuing through a doubled tracker number. RMS drops from .1078 at 3.9002 to .0323 at 4.0202, reaches .0185 at 4.1302, rebounds to .0798 near 4.2202, then decays. A 40 ms energy-weighted spectral centroid over 40–4000 Hz changes from about **187 Hz at 3.9002** to **323 at 4.1002**, **388 at 4.2102**, and **485 at 4.3402**. The 300–500 Hz band changes from about **12.5%** to **68.2%, 82.3%, and 56.9%** of that band-limited energy. These are descriptive envelope features, not a register classifier; phonetic change, irregular phonation, resonance or other sound can also change them.

Thus the “no timbre/energy/onset change” prerequisite is **not established**. The recordings do not prove an intentional high-register/falsetto event, but this pass cannot veto one solely from continuity. No physiological source/register claim is made.

The private **3.8–4.6 s** WAV crop is available in the [local viewer](../../../../services/api/var/octave-ambiguity/sustained-high/viewer.html). It is ignored, not committed. No human listening verdict or usable auditory inspection channel was available to this agent; **perceptual category is unassessed**, not claimed to be “ordinary speech” or “falsetto.” The acoustic ambiguity finding is based on waveform and spectral evidence. A browser audio control permits subsequent human audition.

## Run-level alternate path and local connection

With the prior fixed 1 st octave tolerance, measured half-frequency support covers **16/25 = 64%**. Only **8/25 = 32%** meet strength ≥ .45 and deficit ≤ .25. The longest consecutive credible half-path segment is **4 frames / 40 ms support**. Among all 16 measured octave candidates the median selected-minus-alternate strength deficit is **.15645**, maximum **.2859**. On the 24 production-selected frames alone, support is **15/24 present and 8/24 credible**. The weak raw frame is never dropped from the primary denominator to inflate coverage.

For consecutive source frames with supported octave candidates, median absolute step is **.191 st**, maximum **1.550 st**, RMS step **.517 st**, and RMS second difference **.526 st**. These statistics describe local fragments; they do not turn gaps into a continuous path. A permissive 2 st inspection band finds 21/25 near-half candidates, including a 20-frame segment through 4.2902, but several are weak/off-octave and the tail breaks. This is a **partial near-half trajectory**, not a coherent supported alternate through most/all of the run. No path optimizer could supply measured half candidates at the four genuinely missing frames.

Boundary comparison uses only the nearest coherent five-frame pre-run slope and at most 120 ms extrapolation, not prediction through the entire sustained run. The extrapolated pre-run boundary is **95.376 Hz**. Selected onset residual: **22.663 st**; measured 180.730 Hz alternate residual: **11.066 st**; improvement **11.597 st**. The alternate is closer but still nearly an octave from that local continuation. Against the last actual sample, 113.531 Hz, the high jump is +19.646 st and the half candidate jump is +8.049 st. **Closer is not connected.** Post connection is unavailable.

Quarter-frequency candidate support is also intermittent: **14/25 present, 7/25 credible**, median deficit .1350, maximum .3363; longest credible segment four frames. The strong 92.303 → 93.351 → 94.041 → 94.254 Hz segment has strengths .7467/.9026/.9085/.7598 at 4.2002–4.2302. It explains the central spectral/period evidence but does not establish a whole-run quarter path. This was inspected only because it is in the same run's acoustic evidence, not as a new tracker or a separate threshold search.

## Protected 54.610 Hz: the primary counterexample

The four-frame region around the protected sample, **2.4824–2.5124 s**, is 55.853, 55.288, 54.773, **54.610 Hz**. Sample span 30 ms; hop support **40 ms**. Following selected F0 is 107.282 → 105.687 → 103.845 → 101.830 → 99.965 Hz, a **+11.690 st** immediate boundary jump. The preceding selected branch ends at 1.7424, **740 ms** before this low run; it is not usable local context.

| Time s | Selected Hz / strength | All near-double candidates Hz / strength | Closest octave error st | Selected−candidate deficit |
| --- | --- | --- | ---: | ---: |
| 2.4824 | 55.853 / .7467 | 103.586 / .5588 | 1.307 | .1879 |
| 2.4924 | 55.288 / .8239 | **102.477 / .4597; 118.245 / .3704** | 1.161 (118.245) | .4535 (118.245) |
| 2.5024 | 54.773 / .8815 | 109.068 / .5466 | .076 | .3349 |
| 2.5124 | 54.610 / .8415 | 108.620 / .7776 | .095 | .0639 |

At 2.4924 the 118.245 Hz candidate is numerically nearer exact doubling, but the **102.477 Hz candidate makes the smoother measured sequence** 103.586 → 102.477 → 109.068 → 108.620. Both are preserved, rather than selecting the candidate that makes the proposed rule look safest. That smoother permissive sequence has 4/4 strength ≥ .45, median deficit **.2614**, maximum **.3642**; its first two points fall outside the fixed 1 st octave tolerance. With the same strict diagnostic as the high run, only **2/4 = 50%** have a measured/credible double candidate, and **1/4** passes deficit ≤ .25. The final boundary connects extremely well to the post-run predictor: .131 st alternate residual versus 12.036 st selected residual, advantage **11.905 st**. This is the same strong misleading feature that caused the previous false rejection.

The independent acoustic difference is important. Around 2.5024 the spectral peaks are roughly **55.7, 110.6, 164.1, 218.0, 278.1, 330.6, 387.0 Hz**. The **110.6 Hz peak is strongest**, but odd harmonics support roughly 55 Hz spacing. At 2.5124 the roughly 109/217 Hz components dominate, while ~56/160/329 Hz structure persists. A strongest-harmonic rule would again be wrong.

At 2.5024 the unfiltered waveform's **18.25 ms** repetition has correlation **.851**, versus **.702** near 9.25 ms; the 40 ms window gives **.873 versus .529**. At 2.5124, 18.5 ms gives **.868 versus .768** at 9.375 ms. An 80 ms window includes more of the following doubled region and reverses the last comparison (.792 versus .805), explicitly demonstrating the time-resolution limitation. The low run contains only a few long cycles; longer analysis windows overlap its transition. The waveform nevertheless supplies positive low-period evidence that cannot be dismissed because a doubled candidate better connects to later F0.

Energy grows through this onset; the centroid remains approximately 194–211 Hz, rather than demonstrating that the selected octave jump is a known artifact. Duration and strength differences alone are **not** a principled general separator. The protected label remains binding. These two excerpts have distinguishable acoustic structure, but no validated automatic run-level rule safely captures that distinction across irregular speech.

## Concept evaluation, controls and historical failures

The research feature extractor reports run duration, every measured octave path (¼/½/2/4), candidate coverage/deficits, consecutive-frame smoothness and bounded pre/post connections. It is not imported by production. An illustrative **fixed screening conjunction** requires ≥120 ms support, ≥80% credible candidate coverage with deficit ≤.25, maximum measured alternate step ≤3 st, and supported connections on **both** available local sides: advantage ≥6 st and residual ≤3 st. A missing side fails this screen; it is never silently assumed to agree. These fixed context/ratio/strength definitions come from the prior pass and a conservative run-level interpretation; they are not a fitted winning rule.

The target fails coverage, pre-run residual and missing post context. The protected low run fails duration, coverage and missing pre context. Dropping duration would not solve the target; adding a duration cutoff merely avoids one brief control. Even a synthetic, genuinely periodic **110 → 220 → 110 Hz** register-jump candidate example passes this candidate-only screen: true 220 Hz waveforms also repeat at twice their period. A focused test demonstrates both correlations >.99 and absent 110 Hz spectral fundamental in a known 220 Hz signal. Those candidate strengths are an **analytical counterexample**, not a claimed Praat extraction or a new recording. An independently validated acoustic veto would still be necessary.

**No generic criterion emerged. No parameter neighborhood was run.** In particular, octave tolerance was not widened to make 21 near-half candidates count, weak periodicity was not lowered, missing tail candidates were not invented, and the full run was not fragmented to manufacture successful short runs. The user authorized a small neighborhood only if a generic criterion emerged; adjusting four cutoffs cannot supply absent context or fundamental-period evidence. This is the implementation gate failing before parameter sensitivity could establish safety.

Replay results (current production snapshots, no other inference):

| Control | Result |
| --- | --- |
| All 49 saved production controls | Current selected timestamps exactly match frozen snapshots; no screen flags across all 49. Zero recall is explicitly not rule acceptance. |
| All **617 protected samples** across 18 recordings | **617/617 retained**, zero screened. This includes **all 11 explicitly listed protected <70 Hz samples, 54.610–66.615 Hz**. The saved list and its intersection with the 617 proxy samples contain 11 entries; the previous report's prose count of ten was incorrect. Every containing run's features are exported. |
| Coherent 54.610/60/70 Hz numerical controls, including stronger doubled candidates | Retained by the diagnostic; positive low-period evidence is not replaced. |
| Existing synthetic 70 Hz | No new loss; **2 selected / 159 raw voiced** remain. The existing production quality gate already rejects most of this synthetic signal; no claim of 159/159 production retention. |
| Existing synthetic rise/fall and steady 260 Hz | 161 selected each, zero screened. Existing deterministic 55→220 Hz two-octave sweep and reverse also survive the new run diagnostic. |
| Existing coherent high/large local runs | Search found native reference 228–278 Hz, clean `take_2` 240–342 Hz, other coherent playback runs up to ~326 Hz, and smooth synthetic motion. Same features were evaluated; zero flags. Capture identities are not ground truth. The search provides **no independently confirmed human >350 Hz register event**. |
| Genuine coherent 380 Hz numerical case | Survives even with a strong lower candidate. The analytical abrupt 220 Hz counterexample above falsifies candidate-only register-jump safety. |
| Old Google low/subharmonic failure | Raw runs **2.1325–2.4025 (52–66 Hz)** and **2.9525–3.2125 (52–61 Hz)** are already excluded by production. Same diagnostic on raw runs gives double-candidate credible coverage **7.1% / 48.1%**, quadruple coverage **32.1% / 59.3%**; context/coverage fail. Candidate-poor other low runs also fail. No successful generalization. Raw-run features are exported so already-rejected history is not hidden by selected-only replay. |
| Suspicious 州 `f5dc0cc1` | 134.6–152.4 Hz at 1.1127–1.2027 has 9/10 credible half candidates, but lasts 100 ms and lacks qualifying context/deficit coverage. The 462.8–476.3 Hz run at 1.2227–1.2427 has **0/3 credible half candidates** (two weak ones). Nothing safely removed. |
| Latest six physical recordings | Zero diagnostic flags; latest low excursions do not gain the sustained supported alternate/context needed by this concept. All their run features are exported. This is failure to generalize, not exoneration of those excursions. |

Only high/large runs already in the frozen local corpus were inspected; negative `silence_accidental` runs found by the numerical search are explicitly marked negative, not counted as legitimate high-F0 controls. No external corpus, new recording, tracker comparison, VAD evaluation or model download was used.

## Graph contribution, raw preservation and eligibility

Actual before **equals actual after**: baseline **119.767 Hz**, 189 selected whole-recording frames, selected display range **−15.1387…22.2874 st**, Mine domain **−16.1387…23.2874 st**, span **39.4261 st**. The high branch supplies the upper extreme; it is not removed. The three long coherent sections (0.6002–1.1002, 2.0302–2.4302, 3.5102–4.0102) contain 143 samples at **100.206–135.316 Hz**, displayed over **5.1939 st**, only **13.2%** of this domain's height. This is a descriptive useful-motion range, not a new selection/scale heuristic.

A clearly labeled **deletion-only illustration**, not a proposed accepted rule, removes the 24 selected high frames while retaining all raw fields/candidates/timestamps. It yields 165 selected frames, baseline 116.997 Hz, display range **−14.7336…2.6293**, and domain **−15.7336…3.6293**, span **19.3629 st**. The same broad-motion range would occupy **26.8%** of that height. Thus removal could improve readability but would not eliminate the remaining low excursions' contribution. Nothing was changed to obtain the counterfactual scale; it is the existing projection/median/scale arithmetic on a research copy.

Current six physical Mine domains, all unchanged by this pass:

| Canonical prefix | Before st | Actual after st |
| --- | --- | --- |
| 40357072 | −14.2543…5.2661 | identical |
| 8d252264 | −16.1387…23.2874 | identical |
| d47274bc | −14.0217…10.3005 | identical |
| 4b9dbd2b | −3.6776…7.2912 | identical |
| 8faf1a90 | −4.5798…6.2201 | identical |
| a5acd04c | −4.6170…21.4683 | identical |

Actual raw evidence and selection remain unchanged. Research copies preserve raw tracker, energy-gated, analyzer-selected, candidate, periodicity and timestamp fields; only their counterfactual selected/display fields can differ. No half or quarter frequency is inserted. The copied track remains explicitly versioned as a rejected research experiment; its inherited reason is `octave_candidate_ambiguous`, **not a new production reason code**.

Eligibility uses raw support as its denominator and retains the original discontinuities. On the acoustic **3.8–4.6** window, current **unstable** (46/47 raw frames retained, +19.646 st discontinuity) would become **incomplete** (22/47, lost tail). On **4.1–4.35**, current **sufficient** (24/25) would become **insufficient** (0/25). Removing suspect material does not manufacture sufficient evidence. These are acoustic windows, not asserted character/word timings; production character eligibility is unchanged. The isolated high-run `sufficient` result describes completeness and continuity, **not proof of correct fundamental selection**, which is precisely the unresolved reliability issue.

## Review artifacts and validation

- [Focused local viewer with private listening crop](../../../../services/api/var/octave-ambiguity/sustained-high/viewer.html).
- [Target beside protected control, PNG](../../../../services/api/var/octave-ambiguity/sustained-high/comparison.png) / [PDF](../../../../services/api/var/octave-ambiguity/sustained-high/comparison.pdf): waveform, spectrogram, candidates/near-half path, raw/production-selected F0, unchanged domains, and deletion-only geometry.
- [Spectral/periodicity plates, PNG](../../../../services/api/var/octave-ambiguity/sustained-high/spectral-periodicity.png) / [PDF](../../../../services/api/var/octave-ambiguity/sustained-high/spectral-periodicity.pdf): eight representative frames, including the candidate-poor tail and protected low period.
- [Original/canonical overlay](../../../../services/api/var/octave-ambiguity/sustained-high/original-comparison.png).
- [Complete frame table](sustained-high-frames.csv) and [structured replay/features](sustained-high-evidence.json). Full lag arrays, exact unchanged extraction, native extraction, decoded audio, figures and validation logs remain private under ignored `services/api/var/octave-ambiguity/sustained-high/`.

The plots were visually inspected. The viewer is a local static forensic artifact using local images/audio only, with all 29 frame rows and no external assets. No mobile interface was changed.

The attempted Chromium runtime smoke could not start in this sandbox: Crashpad reported `setsockopt: Operation not permitted`, followed by a pipe reset. Static HTML checks verified all 31 table rows (29 data plus two headers), all four local image/audio assets, and report links; the standalone plots were inspected directly. Browser playback/rendering is not reported as a passed runtime check, and the listening verdict remains unavailable. The private failure log is `services/api/var/octave-ambiguity/sustained-high/browser-check.log`.

Validation: **30 research tests passed** (14 new forensic checks plus the previous 16 octave-research checks). Tests cover exact run/frame inventory, direct original comparison including the weak near-floor discrepancy, missing path candidates, full denominators, protected replay, smooth sweeps, genuine high/low continuity, the explicit register-jump false positive, harmonic-vs-fundamental waveform evidence, metadata independence and honest counterfactual eligibility. These passing tests record a rejected concept; they do not certify a production rule. API source/tests Ruff, new research Ruff, touched Python formatting, local artifact links and `git diff --check` pass. Production source hashes remain unchanged from the pre-research snapshot. No backend production suite, mobile suite, tracker/VAD bakeoff or unrelated inference was rerun because production did not change.

Reproduce with installed local dependencies (no installs/network):

```sh
# Optional exact production re-extraction of this canonical and native original only:
PYTHONPATH=.:services/api/src services/api/.venv/bin/python -m \
  benchmark.pronunciation_v2.sustained_high_branch_report --extract

# Saved evidence replay plus plots; Matplotlib already exists in this ignored local deps dir:
MPLCONFIGDIR=/tmp/benma-sustained-mpl \
PYTHONPATH=.:services/api/src:services/api/var/silero-vad/deps \
services/api/.venv/bin/python -m \
  benchmark.pronunciation_v2.sustained_high_branch_report --plots

PYTHONPATH=.:services/api/src services/api/.venv/bin/pytest -q \
  benchmark/pronunciation_v2/test_sustained_high_branch.py \
  benchmark/pronunciation_v2/test_octave_ambiguity.py

services/api/.venv/bin/ruff check --config services/api/pyproject.toml \
  benchmark/pronunciation_v2/sustained_high_branch.py \
  benchmark/pronunciation_v2/sustained_high_branch_report.py \
  benchmark/pronunciation_v2/test_sustained_high_branch.py
services/api/.venv/bin/ruff format --check --config services/api/pyproject.toml \
  benchmark/pronunciation_v2/sustained_high_branch.py \
  benchmark/pronunciation_v2/sustained_high_branch_report.py \
  benchmark/pronunciation_v2/test_sustained_high_branch.py
services/api/.venv/bin/ruff check services/api/src services/api/tests
git diff --check
git diff --stat
git status --short
```

## Seven final decisions

| Decision | Result |
| --- | --- |
| **1 — 8d252264 high branch** | **ACOUSTICALLY AMBIGUOUS.** Local ~94 Hz structure contradicts treating the entire curve as established high F0; neither a continuous half-frequency fundamental nor a genuine high-register gesture is proven. |
| **2 — half-frequency path** | **NO COHERENT ALTERNATE PATH** through most/all of the complete run under the stated supported-octave definition. A partial near-half trajectory exists; only 8/25 frames have credible octave-related support, and four tail frames have no near-half candidate at all. |
| **3 — low-F0 separability** | **LOW-F0 CONFOUND REMAINS.** Independent waveform evidence explains why protected low F0 can coexist with stronger doubled harmonics and better doubled continuity; safe generic automatic separation is unproven. |
| **4 — generic rule** | **NO SAFE GENERIC RULE.** Target prerequisites fail, historical generalization fails, and candidate-only register-jump safety has a counterexample. |
| **5 — graph domain** | **GRAPH DOMAIN STILL DISTORTED.** Actual selected evidence/domain unchanged; an attractive deletion-only picture is not an implementation gate. |
| **6 — checkpoint** | **GRAPH QUALITY STILL BLOCKS CHECKPOINT.** Four-case physical re-smoke is not ready. |
| **7 — exactly one remaining issue** | **Trustworthiness of the irregular terminal 353–434 Hz selected run at 4.1002–4.3402 s in 8d252264, especially its candidate-poor 4.3002–4.3402 tail.** The sustained-half-path hypothesis does not solve this issue. |

The existing uncommitted V2 stack and `pronunciation-v2-research` branch were preserved. No production implementation, new reason taxonomy, commit, push, deployment, provider/API call, model download, new recording or broad parameter search occurred. [Final full-tree diff/stat and status](../../../../services/api/var/octave-ambiguity/sustained-high/final-git-state.txt) include the pre-existing stack; `git diff --stat` omits untracked research files.
