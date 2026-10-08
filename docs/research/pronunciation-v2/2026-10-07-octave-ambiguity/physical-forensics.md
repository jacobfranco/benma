# Physical forensics

## Exact production order before this pass (and still current)

1. Canonical mono PCM16 WAV enters `PraatAcousticAnalyzer.analyze`, without transcript/target/character inputs. Praat AC performs candidate generation and path selection: floor 50 Hz, ceiling 550 Hz, 10 ms step, up to 15 candidates, octave-jump cost 0.5, octave cost 0.01, voiced/unvoiced cost 0.14, silence threshold 0.03, voicing threshold 0.45, `very_accurate=False`. Its path-selected frequency and strength become `tracker_f0_hz` and `voicing_probability`; the latter is periodicity, not a calibrated probability of correct F0 or speech.
2. Existing RMS gating uses 40 ms windows and `max(0.003, min(3*q10_RMS, .15*peak_RMS))`. Raw tracker Hz survive; energy-gated `f0_hz` may become missing. There is no input-volume normalization in this pass.
3. The existing 70 Hz high-pass diagnostic runs the **same production Praat configuration**, not a new tracker. A 100 ms Hann power spectrum measures the 40–80 / 40–4000 Hz ratio. Quality rejects `(Hz<80 and low-band fraction>.7)` or raw-versus-filtered pitch disagreement `>6 st`. This existing conjunction is not a newly introduced low-F0 floor. The diagnostic never supplies replacement Hz.
4. Existing `reject_terminal_octave_ambiguity` may mark analyzer selection unavailable. It requires exactly one >6 st jump among voiced pairs separated by at most 30 ms; that jump must be downward −13…−11 st; five preceding usable frames; a coherent tail (within 1.5 st) spanning at most 80 ms; first-tail energy at most 80% of preceding energy; final-tail energy at most 1.2× energy threshold; no supported ~2× candidate (within 1 st, strength >=.45); and no later usable voicing. It preserves raw F0/candidates. These complex physical takes do not satisfy that narrowly terminal, unsupported-alternative pattern. A supported octave alternative actually prevents this old rule from rejecting.
5. `acoustic_result` adds raw utterance-median semitones and z-log-F0, full-resolution F0 and a separate mobile downsampled series. **Tone Graph V2 uses the full-resolution track, not that 240-point legacy downsample.**
6. `build_pitch_track` calls `display_contour` once over the whole raw result. Basic validity requires usable quality, finite nonnegative time, 40–1000 Hz and periodicity >=.45 (or absent). It then applies bracketed-island rejection and local Hampel rejection, in that order, over the same pre-rejection valid samples. Hampel does not first remove island-rejected values from its neighborhood.
7. After selection, the display baseline is recomputed from retained measured Hz. Missing/rejected points break segments, as do nonpositive time differences or gaps >45 ms. Within each retained segment, interior points receive a median-of-three in semitone space; endpoints remain measured. This is display-only smoothing, not a new selected frequency. Values round to four decimal places. Domain: `min(-3, min(display)-1)` to `max(3, max(display)+1)`.
8. The frozen `UtterancePitchTrack` stores raw, energy-gated, analyzer-selected and final-selected Hz separately, candidates/strengths, reasons, timestamps, display semitones, baseline and provenance/content digest. `load_pitch_track` replays an existing immutable snapshot; metadata changes cannot rebuild its selection. No acoustic extraction follows a changed character/reference.
9. `project_pitch` attributes original source indices with `[start,end)` and trusted timing; absent/synthetic timing remains unattributed. `display_from_track` reconstructs selected display segments. `classify_contour` uses that selected geometry when given a track; raw evidence remains available for attrition, discontinuity and instability diagnostics. Eligibility compares selected support against original raw voiced support; `gate_observation` withholds non-sufficient interpretations.
10. `tone_graph.sentence_pitch_evidence` splits segments at syllable/group boundaries, then simplifies Mine to <=.15 st vertex error without bridging gaps. Detail uses the **unsmoothed surviving measured Hz**, normalized to the same rounded baseline. Raw retains original selected tracker Hz, missingness, retained flags and exclusion reasons. Full candidate evidence stays in the acoustic track, not a newly expanded mobile raw-frame object.
11. `SentenceToneGraph` selects Mine by default and filtered real-time evidence in More Detail. `normalizedMine` changes X positions to equal character cells / trusted word groups, never Hz. `PitchPlot` takes the union of the supplied contour bounds and displayed vertex extrema ±1 st (floor −3/+3); it does not exclude outliers itself. Raw is a separate plot with its own extrema/domain; opening Raw does not enlarge Mine's scale. Neither observed labels nor lexical references set the Y-domain.

## Why the two relevant existing protections miss

**Bracketed island:** first partition valid samples on a missing predecessor, >45 ms gap or >6 st adjacent change. A middle region can be rejected only when its last-minus-first span is <=80 ms, preceding-last to middle-first and middle-last to following-first are each <=120 ms, the preceding last-five and following first-five semitone medians agree within 2 st, and the middle median is >6 st from both. This is an island-level rule; it neither requires an octave ratio nor reads candidates. Duration is endpoint span, so nine regular 10 ms samples can meet the 80 ms bound. Gaps can be crossed by the bracket test up to 120 ms, but they fragment the candidate middle into neighboring low regions that may support one another. True first/last regions cannot be middle regions. A longer wrong branch is outside the bound or lacks a following region.

**Hampel:** for each valid frame, collect up to three contiguous valid neighbors each way, stopping at any invalid/missing frame or time step outside `(0,45 ms]`. Require at least two on each side. Compare to the neighbors' semitone median and reject only if deviation is `>max(6, 3*1.4826*MAD)`. This is frame-level and candidate-blind. A gap/onset/offset disables the test; several consecutive wrong frames can supply their own median or inflate MAD. Syllable boundaries are not inputs: selection precedes linguistic projection, but acoustic onsets/offsets often coincide with missing neighbors.

These are specific coverage limits, not evidence that every surviving excursion is false. [Per-frame diagnostics](frame-forensics.csv) reproduce both rules and assert agreement with current production diagnostics.

## The six canonical files

All paths are under `services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/`. Full relative paths and SHA-256 hashes are in [replay.json](replay.json). Original M4A inspection was unnecessary; no canonicalization defect was established or assumed.

| Take | Canonical filename | Duration | Raw voiced / current selected |
| --- | --- | ---: | ---: |
| 1 | `40357072fc994a0ab052752ca119b2e6.wav` | 4.8994 s | 276 / 253 |
| 2 | `8d2522640da64860bd83c33b0b7b7e14.wav` | 4.6904 s | 197 / 189 |
| 3 | `d47274bcdb604380abbeac49930a5dad.wav` | 6.8731 s | 222 / 214 |
| 4 | `4b9dbd2bb17b434498fcbd16a7dd4b69.wav` | 6.7802 s | 226 / 224 |
| 5 | `8faf1a90f564479cac56a41aeab22177.wav` | 3.0186 s | 167 / 164 |
| 6 | `a5acd04c21b742fbbfd53741a2aed1dd.wav` | 2.6935 s | 140 / 140 |

## Every major reviewed excursion

Hz ranges below describe raw voiced frames within the event; the selected count excludes current periodicity/quality failures. Duration includes one 10 ms hop. Stable neighbors are the nearest five-sample selected branch medians; **their distance matters** and is recorded in the frame table. Distant medians describe context but are never permitted to drive the prototype.

| Event | Time / duration | Raw Hz; selected frames | Previous / following stable Hz | Why current rules leave selected evidence |
| --- | --- | --- | --- | --- |
| A1, take 1 | 2.0747–2.1647 / 100 ms | 53.02–60.10; 7 | 102.51 / 101.71 | Missing/weak frames split the low branch into mutually low neighbors. Brackets disagree or middle is not >6 st from both. Hampel is missing neighbors or sees a low local median. |
| A2, take 1 | 2.3847 / 10 ms | 66.35; 1 | 121.28 / 117.80 | Following usable branch is >120 ms away; right-side Hampel support is missing. |
| A3, take 1 | 4.2847–4.3147 / 40 ms | 51.68–51.98; 4 | 115.43 / 112.79 | Both bracket gaps exceed 120 ms; no frame has two valid neighbors on both sides. |
| A4, take 1 | 4.7147–4.7447 / 40 ms | 65.84–66.11; 4 | 129.18 / unavailable | Last valid region lacks a following bracket. Hampel skips edges or sees the internally stable low tail. |
| B1, take 2, low-dip control | 1.1102–1.2102 / 110 ms | 66.38–92.87; 8 | 107.60 / 128.08 | Mostly gradual descent with irregular voicing; not an isolated octave jump. Brackets disagree or do not identify an outlier; sparse Hampel support/local median. Retention is appropriate absent contrary evidence. |
| B2, take 2 | 2.5102 / 10 ms | 50.86; 1 | 130.02 / 114.72 | Immediate following branch is also ~51 Hz, so brackets disagree; Hampel has no contiguous support. |
| B3, take 2 | 2.5602–2.5902 / 40 ms | 49.95–51.18; 4 | 130.02 / 114.72 | Previous isolated low region supports it; following gap >120 ms. Hampel cannot get two neighbors on both sides. |
| B4, take 2 | 4.1002–4.3402 / 250 ms | 353.15–433.95; 24 | 119.77 / unavailable | A weak frame splits 3 and 21 selected frames. First region's flanks disagree; final region has no following flank and spans 200 ms. Hampel sees the coherent high branch. |
| C1, take 3, low-dip control | 1.1516–1.3616 / 220 ms | 69.61–105.29; 18 | 98.11 / 113.28 | A broad low dip/recovery with matching harmonic motion, not one isolated deviation. Existing guards appropriately do not erase it. |
| C2, take 3 | 6.0516–6.0716 / 30 ms | 51.52–51.76; 3 | 185.66 / 109.49 | Previous selected branch ends 540 ms before onset and differs from the following branch. Gap then ~111 Hz; Hampel lacks both sides. |
| F1, take 6 | 1.2217–1.2417 / 30 ms | 353.90–380.12; 3 | 104.73 / 126.94 | Bracket medians differ by ~3.33 st, exceeding 2 st. Missing frames on both sides defeat Hampel. |
| F2, take 6 | 1.6518–1.6718 / 30 ms | 208.72–210.30; 3 | 105.01 / 163.99 | Brackets differ by ~7.7 st and the following branch is within 6 st of the island. Missing neighbors defeat Hampel. |

Takes 4 and 5 have no comparable isolated extreme branch in the full raw/selected/spectral review. Their low and high extrema, including the conspicuous broad downward/recovery movement in take 5, remain untouched. The 12-window table intentionally includes B1/C1 as alternatives to a simplistic “low means bad” diagnosis. The other ten windows contain **54 currently selected suspicious frames**, without treating all 54 as proven errors.

All 54 supply selected evidence to Mine and Detail. Mine's smoothing and <=.15 st simplification can omit individual vertices; the frame table separately reports selected support, Detail membership and timestamp membership in the simplified server Mine with no linguistic splits. Real timing splits can preserve additional endpoints. The client still needs trusted timing to place a point inside a character cell, but the contour's supplied global Y bounds affect Mine even if a point is unattributed. No provider alignment was requested for this acoustic audit.

## Candidate and spectral evidence

`margin = selected strength − alternative strength`; a negative margin means the alternative has higher frame strength. Praat's global path selection need not choose the strongest candidate in one frame. Ratios are alternative / selected. The table is illustrative; every stored candidate is in the 92-row export, including non-octave alternatives and the nearest octave candidate even when it fails tolerance.

| Event / timestamp | Selected Hz / strength | Measured alternative Hz / strength | Margin | Ratio; nearest power | Acoustic reading |
| --- | --- | --- | ---: | --- | --- |
| A1 / 2.0747 | 55.314 / .6139 | 107.647 / .4572 | .1567 | 1.946; 2× | 109.38 Hz is the strongest spectral peak; doubled branch is plausible. |
| A1 / 2.0847 | 56.147 / .6195 | 113.337 / .5032 | .1163 | 2.019; 2× | Near-octave alternative follows the neighboring ~100–110 Hz trajectory. |
| A1 / 2.1447 | 60.104 / .7732 | no credible ~120 Hz candidate | — | — | Remaining low branch cannot be removed by pretending that an alternative was measured. |
| A2 / 2.3847 | 66.354 / .6836 | 122.813 / .4831 | .2005 | 1.851; 2×, ~1.34 st error | Broadly subharmonic-like, outside the tested tight octave tolerance. Peak ~128.91 Hz; this is not a clean exact octave test. |
| A3 / 4.3047 | 51.816 / .6031 | 108.078 / .2643; 99.497 / .3249 | .3388; .2782 | 2.086; 1.920 (2×) | Alternatives fail credibility. Peaks ~152.34 and 204.10 Hz can also be higher harmonics of a low periodicity; F0 remains unresolved. |
| A4 / 4.7347 | 65.836 / .9366 | 129.715 / .7979 | .1387 | 1.970; 2× | Peak 130.86 Hz; selected-frequency band ~−25.31 dB relative to peak. Strong ambiguity evidence, not a frequency correction. |
| B2 / 2.5102 | 50.864 / .8195 | no ~102 Hz candidate | — | — | Broad high-frequency/transient structure; no credible measured octave alternative. |
| B3 / 2.5802 | 50.239 / .8676 | 113.655 / .5126 | .3550 | 2.262; 2×, ~2.13 st error | Spectrum has ~99.61/200.20 Hz support, but the available candidate is not a close, strong-enough octave. |
| B4 / 4.2202 | 363.981 / .7452 | 189.017 / .6164; 94.041 / .9085 | .1288; −.1633 | .519; ½× / .258; ¼× | Peaks ~187.50, 280.27, 373.05, 469.73 and 654.30 Hz support harmonic spacing near 94 Hz. Selected ~364 Hz is not uniquely supported as F0. |
| C2 / 6.0616 | 51.743 / .8034 | no credible ~103 Hz candidate | — | — | Main peaks ~414.06/218.75/307.62 Hz; selected band ~−26.29 dB. Candidate support cannot justify the desired exclusion through A+B+C. |
| F1 / 1.2317 | 365.159 / .7151 | 183.370 / .7014; 90.906 / .4843 | .0137; .2308 | .502; ½× / .249; ¼× | Peaks ~365–397, 200, 291–305 Hz; alternatives are credible, but the two local trajectories do not agree closely enough for this conservative model. |
| F2 / 1.6618 | 210.299 / .8416 | 104.805 / .6709 | .1707 | .498; ½× | ~207/428 Hz dominates; half candidate is credible. Before/after branches genuinely differ, so choosing one side loses safety. |
| Protected / 2.5124 | **54.610 / .8415** | **108.620 / .7776** | **.0639** | **1.989; 2×** | The alternative is closer and stronger relative to selected than many physical examples. This is protected valid evidence and must remain valid. |

Spectra use a centered 100 ms Hann window and 16,384-point zero padding for peak readout. Band measurements are maxima within ±8 Hz, normalized to the strongest 40–1000 Hz peak. Zero padding does not improve the underlying ~10 Hz resolution. Adjacent acoustic states can share one spectral window. Dominant energy at 2× alone is not proof of an octave mistake: **the protected low-F0 counterexample also has dominant peaks near 109/216 Hz**, plus support near 160 Hz. Stronger harmonics, creak and period doubling make spectral/candidate evidence non-unique. No spectral peak is substituted for selected Hz.

## Input conditioning

The user-supplied normalization experiment already covered these exact six takes: ordinary RMS normalization left Praat effectively unchanged (maximum differences about .003 st) and preserved the same energy-gated frames. This pass accepts that finding and did not repeat it. No new claim about original-versus-canonical audio equivalence is made; canonicalization comparison was optional and not needed to expose these path/candidate ambiguities.
