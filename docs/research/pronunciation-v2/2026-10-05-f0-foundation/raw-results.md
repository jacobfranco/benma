# Native output, difficult speech and filter ablation

## Final RMVPE extension

RMVPE adds 49 preserved native tracks to the original 245 without replaying the previous estimators or production filters. Native output already includes the upstream .03 voicing threshold; its optional .05 view uses confidence only. All 45 direct-native and all 329 frozen coarse harmonic-core frames are supported. The direct native has 78/106 raw frames, 77 gated, and no pitch in the eight annotated trailing nonvoiced frames. Ambiguous weak-tail continuity receives no correctness credit.

RMVPE avoids the old Google low/subharmonic branch, repeated doubled onset and historical high 州 branch. take_1/take_3 苹 retain 47/43 frames through 2.860/3.400 s, with +2.43/+2.06-st measured change. The four prior 吧 windows have 4/7/13/18 frames; the two sparsest still lack convincing general recovery. Whole-file Google spikes and 79 synthetic weak-fundamental doubled frames remain. [Full RMVPE analysis](rmvpe.md) and the updated [six-tracker tables](raw-tables.md) distinguish these improvements from the unresolved false-voicing blocker.

The following five-tracker narrative is the original result; its saved numerical evidence is reused unchanged. The final six-tracker decision is [NO TRACKER GOOD ENOUGH; stop search](decision.md).

All 245 whole-file outputs were measured before optional cleanup. Native times, Hz/nulls, confidence semantics, gap decisions and available candidates are preserved. CREPE raw supplies F0 everywhere; it has no native voiced/unvoiced decision. No text, alignment, expected tone, smoothing or cross-tracker repair enters extraction. [Detailed tables](raw-tables.md) and [per-recording CSV](per-recording-metrics.csv) retain raw, minimal and production results separately.

## Exact direct digital reference

All five trackers follow all **45/45 native frames** in the two conservatively selected clear harmonic cores, .05–.35 and .47–.62 seconds. Every estimate there falls in the broad 190–320-Hz support band. This is coverage/coarse harmonic agreement, not a measured cents-error rate. The entire 1.05-second file is available in the viewer; no character alignment is needed.

| Tracker | Raw finite frames | Raw islands | Clean finite frames / islands | Native confidence median, raw → retained |
| --- | --- | --- | --- | --- |
| Praat AC | 73/100 | 6 | 73 / 6 | .972 → .972 |
| Praat CC | 79/102 | 3 | 78 / 4 | .976 → .977 |
| pYIN | 67/106 | 2 | 56 / 2 | .549 → .686 |
| Harvest | 97/106 | 1 | 97 / 1 | Unavailable |
| CREPE | 106/106 | 1 | 68 / 3 | .598 → .866 |

Praat AC chooses isolated ~450–490-Hz values near .40–.43 seconds, ~520 Hz near .74–.76, and ~67 Hz near .78–.80. CC exposes irregular late branches too. pYIN preserves a gap at the first break and is more conservative at the end. Harvest bridges breaks and descends through the weak tail. CREPE follows the main harmonic band smoothly but extends an apparently stable path through weak/irregular phonation and trailing silence.

The .70–.90-second tail has insufficient regular harmonic evidence to declare one exact F0 correct from this overview. Filling it earns no quality credit. Confidence cleanup removes much of CREPE's unsupported extension; its raw continuity is therefore not evidence of superior native voicing. Production AC retains all 73 original native values here, including its questionable branches. The canonical 16-kHz version retains 70 of 74 raw AC frames; native sample-grid/edge differences remain visible.

## Real harmonic support

Coarse manually marked support windows are post-extraction checks on spectral plausibility. They were finalized after semi-blinded review; the assistant reviewer knew the candidate families and subsequently saw the key. These are not independent expert labels, and broad bands cannot distinguish every octave ambiguity. Their purpose is to prevent counting a smooth background path as correct speech. [Annotation source](../../../../benchmark/pronunciation_v2/f0_acoustic_windows.json) and [support CSV](acoustic-support.csv) contain the exact intervals.

On the selected old Google cores, raw in-band coverage is AC/CC **82/101**, pYIN **65/101**, Harvest **81/101**, CREPE **101/101**; CREPE retains **96/101** after cleanup. On the healthy human cores, all five raw outputs cover **48/48** in-band frames. On historical `f5dc0cc1`, CC/Harvest/CREPE cover **22/22**, AC **20/22**, pYIN **0/22**. Those small-core checks do not cover all boundary failures; whole-window diagnostics below expose them.

## Difficult windows, inspected only after extraction

| Case | Praat AC / production | Praat CC | pYIN raw / clean | Harvest | CREPE raw / clean |
| --- | --- | --- | --- | --- | --- |
| Healthy human 苹 | Preserves later rise: +2.06 st; all 27 frames retained | Similar +1.94 st | +2.05 / +2.20 st | Boundary excursions make full-window trend −.36 st | +1.94 / +2.06 st |
| Old Google 一 and 苹 | Sustained ~55–57-Hz branch; production removes both windows | Same low branch | ~57–64 Hz then no retained evidence | Often ~60-Hz background with excursions | Follows ~215–255-Hz speech band; also fills surrounding background raw |
| New take_1 一 | Doubled ~405–429-Hz onset already raw; production retains it | Similar doubled onset | No raw evidence | Boundary/background confusion | Avoids doubled onset; clean +3.33-st trajectory |
| New take_3 一 | Same onset problem, 19 raw → 16 production frames | Similar | 16 raw → 0 clean | Unstable boundary | Avoids doubled onset; clean +3.49 st |
| New take_1 苹 | 28 frames, +1.30 st → 21 frames, +.42 st; end 2.784 → 2.624 s | Does not establish a general solution | 37 frames, +1.80 → 20, +.35 st | Drops toward low background; −15.84-st window trend | 58 raw → 43 clean; clean +3.01 st, end 2.85 s |
| New take_3 苹 | 26 frames, +.55 → 21, +.34 st; end 3.343 → 3.193 s | Similar weak late support | 31 frames, +.90 → 20, +.35 st | Only 24 frames, +.44 st | 57 raw → 35 clean; clean +2.06 st, end 3.37 s |
| New take_2 苹 | Stronger rise survives: +5.24 → +4.79 st | Stronger surviving rise | Conditional support varies | Boundary errors remain | Clean +4.64 st; raw onset contamination obscures whole-window trend |
| Historical 州 `f5dc0cc1` | ~462–476-Hz terminal branch gives **21.876-st** nearby jump, retained by production | Avoids this high branch | Misses the clear speech; six late ~57-Hz raw frames → none | Mostly low background over the broad window | Avoids high branch; clean 21 frames near 147 Hz, but some weak/background extension |
| Prior 吧 `f3c642b5`, `e59a6350` | No raw or retained frames | At most four raw, two retained boundary frames | Sparse low raw path, none after cleanup | Low ~60-Hz background is not demonstrated recovered voice | Four retained frames per case; insufficient for confident recovery |

Changes are first-versus-last finite quintile median Hz ratios in semitones, not lexical tone scores. Different algorithms retain different portions, so a bigger positive number alone is not better. The spectrogram and temporal endpoints are essential. All four prior 吧 cases and the remaining diagnostic windows are included in [diagnostic-windows.csv](diagnostic-windows.csv). None establishes robust recovery of prior weak 吧 evidence.

## Minimal cleanup

One fixed concept: retain native voiced decisions, reject native confidence below the declared threshold, require 64-ms local RMS ≥.001 (−60 dBFS), and drop islands shorter than 30 ms. Thresholds are AC/CC .45, pYIN .1, CREPE .21; Harvest has no confidence field. These scales are not comparable calibrated speech probabilities. The CREPE threshold follows its implementation's example; the pYIN threshold is a declared research operating point, not a claimed optimum. No threshold sweep or case-specific tuning was used.

Cleanup can only remove native measurements. It never interpolates, smooths, repairs octaves or conditions on expected tone. It reduces pYIN negatives from 670 to 39 frames but discards much real low/weak voice and late-rise evidence. It reduces CREPE negatives from 1947 to 289 yet leaves confident background. Harvest offers no native-confidence separation to exploit in this experiment.

## Current Praat production-filter ablation

The unchanged production analyzer and `display_contour` run separately on each frozen file. Raw AC equivalence was checked against `tracker_f0_hz`, allowing only production serialization rounding. Production retention is then applied to the original unrounded native Hz for comparisons. This isolates removal and gaps; display normalization/smoothing cannot be mistaken for changed raw F0. Diagnostics and the actual production result are preserved separately.

| Metric | Raw AC | AC with production retention | Interpretation |
| --- | --- | --- | --- |
| Finite frames over whole speech files, including pauses | 4191/8863 (47.3%) | 3274/8863 (36.9%) | 917 raw measurements removed; not a voiced-truth accuracy rate |
| Speech islands | 254 | 184 | Fewer islands partly means removed evidence |
| Adjacent >9-st jumps | 5 | 1 | Discontinuity proxy; no real-speech gold error rate |
| Nearby >9-st jumps across ≤120-ms gaps | 60 | 30 | Specific onset/州 errors remain |
| Known-negative pitch frames | 427/1911 | 122/1911 | Large reduction, incomplete vocal/background separation |
| Synthetic correct-core coverage | 1404/1404 | 1259/1404 | All 145 lost frames are the correct steady 70-Hz signal |
| Synthetic >9-st error frames | 0 | 0 | Removal cannot improve an already zero error count |
| Protected real low-F0 proxy | 617/617 | 617/617 | Selection favors the baseline by construction |
| Closest repeat mutual duration | 1.82 s | 1.73 s | Median/p90 .030/.102 → .029/.102 st |

On synthetic 70 Hz, periodicity is ~.9999 and high-pass F0 agrees, yet low-frequency energy fraction ~.728 triggers `low_frequency_contamination`, removing every evaluated frame. This is a filter-created false rejection of known-valid F0. It is distinct from the baseline-selected real proxy, which necessarily survives its own selection procedure.

**Root causes are mixed.** Google low paths, doubled 一 onset and the historical 州 jump originate before filtering; filtering does not recover the right branch. Newest 苹 already has incomplete raw support, and production filtering further shortens the useful rise. Prior 吧 has missing raw evidence, so changing display retention alone cannot recover it. Real accidental/periodic background is voiced raw and remains partly voiced after filtering. Source/capture changes matter, but unlinked playback sources and genuine prosodic differences prevent assigning all cross-recording variation to the capture device.
