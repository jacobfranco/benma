# Character-free F0 foundation — final six-tracker result

**NO TRACKER GOOD ENOUGH. RMVPE does not earn migration. STOP TRACKER SEARCH — DESIGN AROUND EVIDENCE LIMITS.**

The final bounded RMVPE experiment completed the exact frozen **49 files**, bringing saved native evidence to **294 tracks across six estimators**, zero failures/skips. All prior tracker outputs and audio-only alignments were reused.

RMVPE improves the old Google low branch, doubled onset, later rises, historical high 州 branch and closest-repeat coverage. It tracks every known 70-Hz core frame and keeps all 617 low-F0 proxy samples, although three of eleven lowest samples are doubled relative to the baseline. CPU inference is practical: **0.286 s / 2.856 s**, versus saved CREPE **29.059 s**.

It still emits **374/1947 known-negative frames**, and **326** survive the strongest permitted confidence gate. Its weak-fundamental synthetic has **79 doubled frames**. These failures block migration. The next pass is **DESIGN TRUSTWORTHY PRODUCT BEHAVIOR AROUND PARTIAL/UNCERTAIN ACOUSTIC EVIDENCE**. No further tracker search is recommended.

Read [the complete RMVPE summary](rmvpe.md), [five final decisions](decision.md), and [validation](validation.md). Raw extraction remains character-free; production behavior and the pre-existing working tree are preserved.

## Product-weighted comparison

Highest weight: real harmonic support, repeat consistency, octave/subharmonic behavior, low-F0 safety and background rejection. Coverage, fragmentation, synthetic accuracy and perturbation stability are secondary. Runtime is a constraint, not a substitute for quality. No aggregate quality score hides these tradeoffs.

“Clean” for the original five means the previous fixed minimal acoustic cleanup. RMVPE uses only native max salience >.05; its raw output already uses the upstream >.03 voicing threshold. No RMVPE production filtering is applied. Negative counts use each estimator's native grid. The low proxy is 617 frames from 18 recordings; it is baseline-selected, not independent F0 truth. The 11-frame lowest subset is particularly small. Repeat values below are take_1/take_3 **raw p90 absolute semitone disagreement**, conditional on mutual voicing.

| Tracker | Direct-native quality | Repeated-capture consistency | Synthetic accuracy | Low-F0 safety | Silence false pitch, raw → clean | Octave/subharmonic robustness | Fragmentation, raw → clean | Benign-perturbation stability | Warm CPU latency / wall RTF | Model/dependency size | Overall verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Praat AC | All 45 clear core frames supported; high/low branches in irregular tail | p90 .102 st; repeats some wrong branches | 0/1404 octave-error frames, full core coverage | 617/617 protected; 11/11 lowest; production rejects synthetic 70 Hz | 427 → 418 /1911; production 122 | Doubled onset, Google low path, ~21.9-st 州 branch remain | 254 → 256 speech islands; production 184 | Stable gain/resample; small conditional bandpass error | 4.47 ms / .00226 | No model; Parselmouth 35.4 MiB | Inadequate despite strong speed/low-register baseline |
| Praat CC | All clear core; irregular late paths | p90 .161 st | 0/1403 octave errors, full coverage | 617/617 and 11/11 lowest | 471 → 457 /1923 | Avoids specific 州 branch; still doubled onset/Google path | 302 → 291 islands | Bandpass causes 4 octave disagreements; correlation −.503 | 6.05 ms / .00336 | Shared Praat package | No general improvement |
| pYIN | Conservative gaps; all clear core supported | p90 .100 st; cleanup cuts shared frames 140 → 87 | 145/1404 octave errors: weak fundamental doubles | 606 → 450 /617; lowest 1 → 0 /11 | 670 → 39 /1947 | Smooth paths can be wrong; misses difficult voiced patches | 154 → 131 islands, with substantial missing speech | Stable on these three transformations | 543 ms / .200 | No model; librosa .95 MiB plus NumPy/SciPy/Numba | Cleaner negatives cost too much real voice |
| WORLD Harvest | Core supported; weak-tail/boundary excursions | p90 7.394 st | 0/1404 octave errors, full coverage | 614/617, 3 doubled; lowest 8/11 | 1075 → 1073 /1947 | Frequent real onset/offset and background excursions | 161 → 161 islands | Bandpass p90 16.48 st, 20 octave disagreements | 731 ms / .226 | No model; pyworld 2.78 MiB plus NumPy | Background behavior disqualifies |
| CREPE full | Core supported; raw fills irregular tail and silence | p90 .378 st; clean .263 st with 168 shared frames | 145/1404 octave errors; clean also removes 26 correct frames | 617 → 578 /617; lowest 11 → 1 /11, retained one doubled | 1947 → 289 /1947 | Best difficult speech paths; weak-fundamental/lowest-register doubling | 30 → 277 islands; raw continuity includes background | Stable conditional pitch; voicing changes slightly | 29.06 s / 10.24 | 84.87-MiB weights; reused Torch ~646.5 MiB | Promising local improvements, unsafe overall |
| RMVPE | 45/45 clear core; gap at break; ambiguous weak tail, trailing nonvoice absent | p90 .096 st; 2.07 s shared; V/UV .996; take_2 pairs still disagree | 79/1404 doubled frames in weak fundamental; full coverage otherwise | 617/617 and 11/11 retained; 3 lowest upward octave disagreements; synthetic 70 Hz passes | 374 → 326 /1947 with native-confidence gate | Fixes important Google/onset/州 paths; retains late rises; brief real glitches and weak-fundamental doubling remain | 147 → 140 speech islands; 22 → 17 adjacent >9-st jumps | Canonical p90 .002 st; bandpass .091; gain one raw octave disagreement | .286 s / .113 | 172.79-MiB weights; reused Torch/scientific stack; ~923-MiB RSS | Best new local gains, still unsafe; no migration |

Latency is median warm `human_control` extraction; RTF is the median over six warm runs on two durations. See [runtime.md](runtime.md) for CPU time, cold timing, process memory and thread caveats. Island counts cover the 30 direct/capture speech or unlabeled cases, excluding negatives and deterministic derivatives; fewer islands alone is not better.

## Five final decisions

1. **RMVPE DOES NOT CLEARLY IMPROVE THE FOUNDATION** — joint product acceptance, despite local improvements.
2. **NOT SAFE ENOUGH**.
3. **NO TRACKER GOOD ENOUGH**.
4. **STOP TRACKER SEARCH — DESIGN AROUND EVIDENCE LIMITS**.
5. **DESIGN TRUSTWORTHY PRODUCT BEHAVIOR AROUND PARTIAL/UNCERTAIN ACOUSTIC EVIDENCE**.

[decision.md](decision.md) explains the final boundary. The [historical five-tracker decision](five-tracker-decision.md) is preserved as provenance and superseded by this final result.

## Evidence and artifacts

- [Frozen corpus and provenance](benchmark-corpus.md), [49-file hashes](corpus.csv), [exact tracker configurations and licenses](tracker-inventory.md).
- [Raw/direct-native results and production ablation](raw-results.md), [all native/aggregate/ablation tables](raw-tables.md), [post-hoc difficult-window measurements](diagnostic-windows.csv).
- [Repeatability and perturbations](repeatability.md), [detailed repeat tables](repeatability-tables.md), [all 36 pair comparisons](pairwise-repeatability.csv).
- [Known-F0 results](synthetic-results.md), [full synthetic tables](synthetic-tables.md).
- [Low-F0 and silence findings](low-f0-and-silence.md), [full safety tables](safety-tables.md), [per-recording metrics](per-recording-metrics.csv).
- [Semi-blinded review](blinded-review.md), [runtime/deployment](runtime.md), [architecture and invariant](architecture.md), [validation/reproduction](validation.md).

Open the [local interactive overlay viewer](/home/jacob/benma/services/api/var/f0-foundation/viewer.html): all 49 recordings, actual-time waveform/spectrogram/F0/confidence, independent tracker toggles, raw/clean selection, production AC overlay and local audio playback. The final fresh identity labels remain A–F until explicitly revealed; raw/minimal toggles now include RMVPE. This is an offline artifact, not a deployed site.

Original working artifacts remain in `/tmp/benma-f0-bakeoff/`. A durable ignored copy of outputs is in `services/api/var/f0-foundation/`; no audio, frame arrays or model enters the tracked report. No production file, lockfile, narrow 要/个 fix, downstream tone/gesture logic or UI was changed by this bakeoff. No inference-provider call, commit, push or deployment occurred.

The actual estimator regression and historical 州 audio verification establish:

`F0(audio, 贵州 metadata) == F0(audio, 鬼粥 metadata) == F0(audio, empty text and nonsense metadata)`

for all six estimators, byte for byte. RMVPE explicitly tests four separate contexts, including arbitrary nonsense. The estimator contract has no linguistic fields; arbitrary metadata cannot enter it. Acoustic uncertainty remains acoustic uncertainty regardless of the character label.

The new raw RMVPE tracks, complete salience arrays, checkpoint/source, timings and validation logs are in `services/api/var/f0-foundation/rmvpe/`. The original five-tracker `/tmp/benma-f0-bakeoff/` artifacts are unchanged. [rmvpe.md](rmvpe.md) covers all 26 required summary items and the one five-value native-confidence sweep.
