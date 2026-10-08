# Repeated native/TTS capture robustness — continuation, October 4, 2026

**Phone capture robustness still blocks the checkpoint. No acoustic repair is promoted.** Three bounded rules fail to improve the latest critical-syllable repeatability; two add pitch to the known accidental-silence false accept, and local continuity changes protected low-F0 evidence. Two narrow reference corrections are implemented, independently of pitch. Direct digital native calibration is **still unverified due to missing trustworthy character timing**.

This continues the [native-control calibration audit](README.md), with its human, Google playback, native asset and silence identities retained. All existing uncommitted Tone Graph V2 work is preserved. No provider call, model download, new recording, database mutation, commit, push or deployment. Source labels for the latest captures are not inferred from timestamp order.

## Exact latest capture set

Read-only local inventory: **130 perceptions**, 32 since October 2; exactly three new successful matching perceptions after the prior inventory of 127. These are midnight **October 4 Eastern**, not noon. Target text is `我要一个苹果`; transcript is `我要一个苹果。` for all three. Their shared target is `8727db3e-65bb-4786-add4-ab7a19be6a05`. The user reports Native reference was played first, then repeated clean playback tests. Persistence does not link a capture to a playback event/provider; T1–T3 below are chronological labels only.

| Take | UTC (Eastern is −4 h) | Seconds | Perception ID | Utterance ID | Attempt ID |
| --- | --- | --- | --- | --- | --- |
| T1 | 04:01:21.640403 UTC | 3.87775 | `48c71bb4-913a-4a73-bf28-c76f958282bf` | `3e137d7d-6a25-434f-a617-d97fef57f893` | `0d674e5e-0091-4b0f-9f54-10f9f01abc8b` |
| T2 | 04:01:58.324853 UTC | 2.57744 | `cabf8d61-b782-497d-a00b-7f31636642d7` | `f764cc1a-e500-4589-be58-ded47bcb1122` | `91000d57-a25b-400b-8cbf-572944ffa087` |
| T3 | 04:02:20.367158 UTC | 4.73688 | `0cb79e67-aef4-4ea7-a90f-7c7568fd78a8` | `cfd89c61-ff48-4de7-a5c8-5af2327cb57c` | `e8ad386f-c89a-4035-8d62-6b1a1bcfc626` |


**T1 hashes:** original `41ae314e2ed7464b5001eca58f6962fc43e237fae0ed0dce1560e9fbc6638f86`; canonical `44d5c787f03cc42955575beb2d231c42ab0cf7c079d5c4e5b544087b855f0464`. Analysis `de3f9ee7-a9ac-4a2b-a85a-6401a9018550`.


**T2 hashes:** original `d6b13781b1a50fba0a60cb0967f732841f24d2b0facfa4e342ed509c623c0603`; canonical `93c60936ddedfa7cba1324ecf6be2f53a4c3eecd47460d3cd63dc6bd76df13e1`. Analysis `d2066b0a-7797-41c0-87b1-bb060d21e558`.


**T3 hashes:** original `b0bb8ad8ec9e2e2512070d4543d6f2910bb027a7d5fe867387345934396c34dc`; canonical `47cc17edd56f510676325270fed72a4b018c4eafad9d35c00b3b4a687f58b082`. Analysis `0419a990-f95e-428b-8c04-2acff1ed3919`.


Every local asset hash was recomputed. All six prior/new phone controls in the detailed audit re-canonicalize byte-for-byte; fresh acoustic results, classifications and graph evidence equal their saved versions (36 timed units). The replay matrix additionally covers 31 real recordings with saved complete/partial analyses and two synthetic negative controls. Partial T3 alignments retain only trustworthy character timing; no rain/umbrella word is divided artificially.

## Native reference timing and direct digital status

The sole matching native row remains `d1272f79-c791-4eb4-973c-3864cc1af03d`, created October 2 at 15:19:22.936924 UTC, Azure `zh-CN-Xiaochen:DragonHDLatestNeural`, 24 kHz mono, 1.05 s. Source SHA-256 `ec96b80ac58bab2941badf3401a135810eb8737b41816337af0f2a2d3b70e9c9`; normal 16-kHz derivative `88e6b9325b545a1c16e893f18b65b7645d2cfd7ccab7f35fb5df1b6788228fbe`.

`ReferenceSpeechService.get_or_create()` returns the existing cache row. `AzureSpeechSynthesisProvider` uses the audio-only REST response; `SpeechSynthesisResponse` has audio/MIME/version/status, and no timing/event fields. There is no captured transient word-boundary callback to recover, nor saved character alignment linked to these exact bytes. Restarting/replaying does not reconstruct it. Native-reference synthesis lacks the timing metadata needed for deterministic character-level self-calibration.

Fresh unchanged analysis again yields **73/100 raw and retained** frames at 24 kHz; the canonical 16-kHz derivative yields **74/100 raw, 70/100 retained**. These whole-file figures do not assign any gesture to a character. Exact character times, character coverage/ranges, gesture, confidence and comparison are **NA for all six characters**, including 要/一/苹. The untimed product fallback is uncertain. No timing was invented or transferred from a recapture, and the digital source is not treated as reference truth for the study.

## Required per-take critical results

These tables are the **unchanged acoustic baseline and saved reference semantics**. “Direct” means exact provider Grapheme identity plus validated nonoverlapping in-audio timing, not independent phonetic annotation. Raw coverage counts finite original Praat decisions; selected coverage counts all retained frames before smoothing/simplification. The denominator is every 10-ms tracker frame in the character interval. All raw and selected min/max, strengths, islands, missing runs, jumps, interval RMS and exact rejection counts are in [the full syllable table](capture-robustness-syllables.csv).


### T1 — playback source unencoded


| Character | Timing s | Raw | Retained | Raw median Hz | Selected median Hz | Harmonic relation | Gesture | Confidence | Comparison | Primary failure/limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | Direct [1.16,1.57) | 75.6% | 75.6% | 279.11 | 279.11 | none established | Unclear | low | uncertain | Onset rise then fall; conservative shape abstention |
| 一 | Direct [1.58,1.91) | 51.5% | 51.5% | 245.83 | 245.83 | ~2× high branch | Unclear | low | uncertain | Raw ~2× onset branch and path dropouts |
| 苹 | Direct [2.33,2.91) | 48.3% | 36.2% | 212.77 | 212.46 | none established | Level-like | moderate | different | Raw tail dropouts + energy/disagreement attrition |


### T2 — playback source unencoded


| Character | Timing s | Raw | Retained | Raw median Hz | Selected median Hz | Harmonic relation | Gesture | Confidence | Comparison | Primary failure/limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | Direct [0.93,1.20) | 77.8% | 77.8% | 321.88 | 321.88 | none established | Unclear | low | uncertain | Supported nonmonotonic shape; ambiguous |
| 一 | Direct [1.21,1.40) | 57.9% | 57.9% | 250.76 | 250.76 | none established | Unclear | low | uncertain | Only 110 ms retained; insufficient support |
| 苹 | Direct [1.61,2.02) | 68.3% | 51.2% | 217.83 | 215.61 | none established | Rising | moderate | consistent | Usable rising portion; some energy attrition |


### T3 — playback source unencoded


| Character | Timing s | Raw | Retained | Raw median Hz | Selected median Hz | Harmonic relation | Gesture | Confidence | Comparison | Primary failure/limitation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | Direct [1.73,2.15) | 97.6% | 88.1% | 282.31 | 281.01 | none established | Unclear | low | uncertain | High raw terminal branch; tracker instability |
| 一 | Direct [2.16,2.50) | 55.9% | 47.1% | 238.62 | 240.50 | ~2× high branch | Unclear | low | uncertain | Raw ~2× onset branch + dropouts/energy loss |
| 苹 | Direct [2.89,3.46) | 45.6% | 36.8% | 212.72 | 211.79 | none established | Level-like | moderate | different | Raw tail dropouts + energy/disagreement attrition |


| Take | RMS | Peak | Clipped ≥.98 | Noise RMS q10 | q90/q10 dB proxy | Energy gate |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 0.02511 | 0.3001 | 0.0% | 0.001855 | 27.10 | 0.005564 |
| T2 | 0.02495 | 0.2628 | 0.0% | 0.001966 | 26.45 | 0.005899 |
| T3 | 0.02369 | 0.3012 | 0.0% | 0.002044 | 25.45 | 0.006132 |


The RMS quantile ratio is a dynamic-range/noise proxy, **not measured SNR**. No take clips. Subjective clean playback is consistent with usable speech in these files; nothing here demonstrates conditions outside ordinary phone use. Low-amplitude voiced tails remain a product responsibility. There is no same-source clean digital recording with alignment, so capture-only degradation in dB cannot be isolated.

## Candidate-level diagnosis: both candidate loss and path loss

Production already persists every positive-frequency Praat candidate up to 550 Hz and its strength. Research inspection additionally reads each original Praat frame intensity without changing configuration. Original selected strength is **zero when the chosen path is unvoiced**; that does not imply zero strength for the alternative candidates. Candidate strength measures periodicity, not probability that the fundamental is correct. Several harmonic candidates can be strong together.

- **Old Google 一:** all 28 finite raw decisions are 52.012–65.638 Hz; all fail the recording energy gate. At 2.2225 s the chosen 54.139 Hz has strength .7774; a 217.316-Hz candidate has strength .6906: ratio .2491, approximately a quarter-frequency branch. Eight frames have an alternative ≥.55 in an acoustically supported utterance range; only two alternatives exceed the selected branch strength. This is not a complete recoverable vowel trajectory.
- **Old Google 苹:** all 42 finite raw decisions are 52.481–62.122 Hz. At 2.9825 s: 52.481/.9060 selected versus 210.336/.7383 alternative (ratio .2495). The existing filtered track corroborates a ~210–219 Hz path at 24 shared timestamps (median ratio 3.9955). The low branch is sustained through the finite region; it does not recover a normal octave within 苹. Fifteen frames have an alternative ≥.55 in the supported range, none stronger than the chosen branch. The more periodic low branch is not automatically the correct speech fundamental.
- **T1 一:** four selected onset frames at 1.5839–1.6139 s are 405.750–429.440 Hz, followed by a gap and a coherent ~217–269 Hz trajectory. At 1.6039: 413.390/.6459 versus 214.586/.5613, ratio 1.9265. Both primary and high-pass select the high branch here. At 1.7239 the selected path is unvoiced although candidates include 226.632/.6838, 434.092/.7170 and 472.178/.6979. This is a real candidate/path ambiguity, not total absence of periodic structure.
- **T3 一:** four original high frames near the onset (one energy-rejected) include 427.578/.7313 versus 212.006/.5630 at 2.1734, ratio 2.0168. The raw jump is 12.149 st; primary later returns to ~215–269 Hz. This is short-lived upward branch selection, unlike the old sustained quarter-frequency selection.
- **T1/T3 苹:** no selected raw decision below 80 Hz, and no large raw jump in these intervals. Both track a plausible ~210–215 Hz beginning, then lose the rising tail. In T1 at 2.6339, 215.259 Hz remains raw but RMS .005504 is below gate .005564. In T3 at 3.2534, selected F0 is absent although candidates include 220.510/.7364, 440.286/.6578, 110.449/.6881, 73.556/.7138 and 55.220/.5865. Later, fundamental and half-frequency candidates compete; at 3.3334 raw 233.415/.6481 is both below energy gate and disagrees with high-pass 117.176. Automatically trusting the high-pass track would halve this plausible continuation.
- **T2 苹:** the retained later rise is substantial (robust-bin change +4.673 st), ending up to 299.464 Hz. Original raw reaches 308.449 Hz; seven raw frames are energy-rejected. Strong alternative support is not present throughout all missing intervals, and the acoustic profile differs from T1/T3.

The local supported-range diagnostic (median of ≥.85-strength, retained, high-pass-agreeing frames, falling back to such utterance frames; ±6 st; candidate strength ≥.55) finds **10/30** T1 苹 and **8/31** T3 苹 unvoiced-path frames still containing a plausible strong candidate. Respectively 20 and 23 interval frames have no strong candidate in that range. This range is a diagnostic proxy, not ground-truth F0, and includes unvoiced onsets/offsets. It demonstrates both **A: plausible candidate exists but loses selection** and **B: no strong plausible candidate in parts of the interval**. A correction cannot safely recover the entire tail merely because several frames contain candidates.

All candidates for every critical interval, including human and prior Google controls, are preserved in the ignored `candidate-frames.csv`; representative intensities and complete per-frame candidate sets are in `candidate-examples.json`. Praat intensities near .03–.046 in lost tail regions show low local intensity alongside periodicity; no claim is made that strength alone overrides Praat's joint voicing/path objective. No fixed pitch-floor explanation or expected-tone criterion is used.

## Cross-take acoustic similarity

Each exact provider interval is resampled to 80 normalized time positions for analysis only. A 40-ms Hann spectrum is integrated into 32 logarithmic bands from 80–4000 Hz; centered log-power vectors compare spectral shape independently of level. Banded dynamic time warping allows ±20% local time deviation with a .025 insertion penalty. Active comparisons require RMS ≥max(.003, .2×each interval's maximum). No aligned samples enter production or the direct-native control.

| Pair | Character | Duration ratio B/A | Spectral cosine after alignment | Aligned log-energy correlation | Active energy B/A dB | Shared-finite F0 difference st | Voicing disagreement | Candidate agreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1/T2 | 要 | 0.659 | 0.945 | 0.732 | 0.77 | 3.166 | 2.1% | 9.8% |
| T1/T3 | 要 | 1.024 | 0.991 | 0.988 | -0.08 | 0.045 | 16.1% | 68.6% |
| T2/T3 | 要 | 1.556 | 0.944 | 0.806 | -1.05 | 3.221 | 0.0% | 12.1% |
| T1/T2 | 一 | 0.576 | 0.982 | 0.709 | 2.65 | 0.669 | 32.1% | 27.0% |
| T1/T3 | 一 | 1.030 | 0.990 | 0.925 | 0.30 | 0.102 | 17.6% | 72.1% |
| T2/T3 | 一 | 1.789 | 0.981 | 0.846 | -2.21 | 1.034 | 25.6% | 28.7% |
| T1/T2 | 苹 | 0.707 | 0.977 | 0.031 | 3.31 | 0.425 | 37.9% | 36.3% |
| T1/T3 | 苹 | 0.983 | 0.989 | 0.965 | 0.56 | 0.029 | 6.9% | 85.7% |
| T2/T3 | 苹 | 1.390 | 0.976 | 0.243 | -2.67 | 0.448 | 41.0% | 36.4% |


Candidate agreement is symmetric nearest-frequency matching within .5 st among candidates of strength ≥.45; it is a summary, not proof of identical sources. Coarse spectral similarity alone is insufficient for that claim.

**T1/T3 are very similar:** interval durations differ by only −1.7% to +3.0%, aligned energy correlations .925–.988, shared-finite F0 differences .029–.102 st. Nonetheless voicing decisions differ on 6.9–17.6% of matched active samples. Their gross 苹 error is repeatable: both lose the tail and become level-like. **T2 differs materially:** critical intervals are 29–42% shorter than T1; 要 has a 3.166-st shared-finite shift, and 苹 has a 3.31-dB active level difference and very different envelope timing (correlation .031). T2's positive 苹 versus the two level-like results cannot honestly be attributed solely to random path selection on identical speech. The recordings support a similar source family with timing/prosodic/capture differences and demonstrable path susceptibility; they do not establish exact same-source equivalence for all three. This does not excuse the phone-capture failure.

## Raw failure versus filtering

- **T1 一:** 16 tracker-missing frames; every one of 17 raw finite frames survives selection. The doubled path is already present in raw evidence. Filtering is not the cause.
- **T3 一:** 15 tracker-missing frames plus 3 of 19 raw finite frames removed by the energy gate. The doubled path remains; both raw instability and energy attrition contribute.
- **T2 一:** 8 raw-missing frames; all 11 finite frames retained. The classifier's 110-ms support is insufficient. No filtering loss explains it.
- **T1 苹:** 30 tracker-missing, 28 finite, 21 retained. All 7 finite losses fail energy; 3 also carry high-pass disagreement. The retained frequency range shrinks from raw 208.866–238.422 to 208.866–214.771 Hz. Missing candidates/path support and filtering both remove later motion.
- **T3 苹:** 31 tracker-missing, 26 finite, 21 retained. All 5 finite losses fail energy; 2 also carry disagreement. Raw 210.232–234.261 becomes retained 210.232–214.952 Hz. Again both contribute.
- **T2 苹:** 13 tracker-missing and 7 of 28 finite frames energy-rejected, yet a supported rise remains. Counts of overlapping reasons must not be summed as disjoint losses.

No Hampel or short-island rule removes any of these 苹 tails. Original Praat path loss, the recording RMS gate, and high-pass disagreement are the relevant stages. Restoring all raw finite tail frames would still leave missing regions and would not certify a clean rising gesture in every take.

## Three bounded acoustic hypotheses — all research-only

**A, high-pass corroboration:** only missing or >6-st-disagreeing raw frames may use an original candidate within .5 st of the already-existing 70-Hz-high-pass selection, strength ≥.65, original energy gate passed and low-band energy fraction <.7. Healthy agreeing primary frames remain untouched. It adds nine old Google 苹 frames but still yields insufficient support; old Google 一 remains empty. It cannot fix an upward branch chosen by both tracks and can mistake filtered half-frequency selection for corroboration.

**B, adaptive range:** seeds are retained primary frames with strength ≥.85, high-pass agreement ≤.5 st, low-band fraction <.25, and neighboring raw steps ≤1.5 st. At least 10 seeds are required; otherwise it returns the primary evidence unchanged. Median ±6 st is an utterance evidence range, not a fixed Hz floor. Repair also requires an original ≥.65 candidate within 3 st of a seed no more than 200 ms away, and the original energy gate. Healthy primary values within range, and strong existing primary values, are preserved. T1/T2/T3 have 114/63/106 seeds, medians 241.070/260.395/240.406 Hz. T1/T3 center difference is .048 st; T2 differs ~1.34 st, consistent with its rendition. The rule changes a few high-path frames but leaves decisive missing/weak tail regions unresolved. It cannot exclude every expressive-register risk from this small single-user corpus.

**C, local continuity:** use the same acoustic seeds; walk at most 150 ms each direction through actual candidates of strength ≥.65 and steps ≤1.5 st, RMS ≥max(.003, 1.5×recording noise floor), low-band fraction <.25. Preserve healthy primary frames; replace only an approximately 2×/3×/4× competing path or absent selected evidence. Conflicting proposals abstain. Stop when support fails. No interpolation or arithmetic frequency multiplication supplies a sample. It recovers too little tail evidence to change the critical gestures and can extend into ambiguous low-energy material.

Repairs accept only raw acoustic dictionaries; no text, character identity, boundaries, reference, tone or contour target enters any repair function. The existing classifier is applied afterward using original timing. Original tracker values/candidates remain immutable; research-derived selections carry explicit reasons. No production provenance/schema design is claimed. Each output was checked deterministic over repeated invocations. These are three fixed rules; no parameter sweep or extra tracker was introduced.

### Baseline stability summary

| Character | Usable takes | Gesture agreement | Verdict agreement | Primary instability |
| --- | --- | --- | --- | --- |
| 要 | 0/3 | 100% Unclear | 100% uncertain | Nonmonotonic shape / extra high branch; unresolved reference was a separate blocker |
| 一 | 0/3 | 100% Unclear | 100% uncertain | Doubled branch, raw dropouts and insufficient support |
| 苹 | 3/3 moderate classifications, only 1 rising | 66.7% | 66.7% | Smooth retained beginnings conceal excluded/missing tails; source-family timing/energy differ |

Agreement on abstention is not usable feedback; a moderate classification does not establish that the partial contour represents the whole syllable.

### Required before/after repeatability

A **usable take** below means a moderate, `acoustic_shape_only` gesture, not merely any retained samples. All three takes have some retained evidence for each character, which is not equivalent to usable learner feedback. Agreement is the modal category fraction including abstentions; 100% Unclear/uncertain is stable abstention, not success. Order is always T1 / T2 / T3. Comparison uses frozen original references to isolate acoustic effects; later reference corrections do not change these nine comparisons.


### Before


| Character | Usable | Gestures T1 / T2 / T3 | Gesture agreement | Verdicts T1 / T2 / T3 | Verdict agreement | Retained coverage min–max | Median Hz min–max | Selected jumps >6 / >12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 75.6–88.1% | 279.11–321.88 | 1 / 0 |
| 一 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 47.1–57.9% | 240.50–250.76 | 2 / 0 |
| 苹 | 3/3 | Level-like / Rising / Level-like | 66.7% | different / consistent / different | 66.7% | 36.2–51.2% | 211.79–215.61 | 0 / 0 |


| Take | Character | Raw coverage | Retained coverage | Selected median Hz | Islands | Gesture / confidence | Reason | Comparison |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 要 | 75.6% | 75.6% | 279.11 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T1 | 一 | 51.5% | 51.5% | 245.83 | 3 | Unclear / low | tracker_instability | uncertain |
| T1 | 苹 | 48.3% | 36.2% | 212.46 | 1 | Level-like / moderate | acoustic_shape_only | different |
| T2 | 要 | 77.8% | 77.8% | 321.88 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T2 | 一 | 57.9% | 57.9% | 250.76 | 2 | Unclear / low | insufficient_voicing | uncertain |
| T2 | 苹 | 68.3% | 51.2% | 215.61 | 2 | Rising / moderate | acoustic_shape_only | consistent |
| T3 | 要 | 97.6% | 88.1% | 281.01 | 4 | Unclear / low | tracker_instability | uncertain |
| T3 | 一 | 55.9% | 47.1% | 240.50 | 3 | Unclear / low | tracker_instability | uncertain |
| T3 | 苹 | 45.6% | 36.8% | 211.79 | 1 | Level-like / moderate | acoustic_shape_only | different |


### A: high-pass


| Character | Usable | Gestures T1 / T2 / T3 | Gesture agreement | Verdicts T1 / T2 / T3 | Verdict agreement | Retained coverage min–max | Median Hz min–max | Selected jumps >6 / >12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 75.6–88.1% | 279.11–321.88 | 1 / 0 |
| 一 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 47.1–57.9% | 240.50–250.76 | 2 / 0 |
| 苹 | 3/3 | Level-like / Rising / Level-like | 66.7% | different / consistent / different | 66.7% | 36.2–51.2% | 211.79–215.61 | 0 / 0 |


| Take | Character | Raw coverage | Retained coverage | Selected median Hz | Islands | Gesture / confidence | Reason | Comparison |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 要 | 75.6% | 75.6% | 279.11 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T1 | 一 | 51.5% | 54.5% | 244.55 | 3 | Unclear / low | tracker_instability | uncertain |
| T1 | 苹 | 48.3% | 36.2% | 212.46 | 1 | Level-like / moderate | acoustic_shape_only | different |
| T2 | 要 | 77.8% | 77.8% | 321.88 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T2 | 一 | 57.9% | 57.9% | 250.76 | 2 | Unclear / low | insufficient_voicing | uncertain |
| T2 | 苹 | 68.3% | 51.2% | 215.61 | 2 | Rising / moderate | acoustic_shape_only | consistent |
| T3 | 要 | 97.6% | 88.1% | 281.01 | 4 | Unclear / low | tracker_instability | uncertain |
| T3 | 一 | 55.9% | 47.1% | 240.50 | 3 | Unclear / low | tracker_instability | uncertain |
| T3 | 苹 | 45.6% | 36.8% | 211.79 | 1 | Level-like / moderate | acoustic_shape_only | different |


### B: adaptive range


| Character | Usable | Gestures T1 / T2 / T3 | Gesture agreement | Verdicts T1 / T2 / T3 | Verdict agreement | Retained coverage min–max | Median Hz min–max | Selected jumps >6 / >12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 75.6–88.1% | 279.11–321.88 | 1 / 0 |
| 一 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 47.1–57.9% | 240.50–250.76 | 2 / 0 |
| 苹 | 3/3 | Level-like / Rising / Level-like | 66.7% | different / consistent / different | 66.7% | 36.2–51.2% | 211.79–215.61 | 0 / 0 |


| Take | Character | Raw coverage | Retained coverage | Selected median Hz | Islands | Gesture / confidence | Reason | Comparison |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 要 | 75.6% | 75.6% | 279.11 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T1 | 一 | 51.5% | 54.5% | 244.55 | 3 | Unclear / low | tracker_instability | uncertain |
| T1 | 苹 | 48.3% | 36.2% | 212.46 | 1 | Level-like / moderate | acoustic_shape_only | different |
| T2 | 要 | 77.8% | 77.8% | 321.88 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T2 | 一 | 57.9% | 57.9% | 250.76 | 2 | Unclear / low | insufficient_voicing | uncertain |
| T2 | 苹 | 68.3% | 51.2% | 215.61 | 2 | Rising / moderate | acoustic_shape_only | consistent |
| T3 | 要 | 97.6% | 88.1% | 281.01 | 4 | Unclear / low | tracker_instability | uncertain |
| T3 | 一 | 55.9% | 47.1% | 240.50 | 3 | Unclear / low | tracker_instability | uncertain |
| T3 | 苹 | 45.6% | 36.8% | 211.79 | 1 | Level-like / moderate | acoustic_shape_only | different |


### C: continuity


| Character | Usable | Gestures T1 / T2 / T3 | Gesture agreement | Verdicts T1 / T2 / T3 | Verdict agreement | Retained coverage min–max | Median Hz min–max | Selected jumps >6 / >12 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 要 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 75.6–88.1% | 279.11–321.88 | 1 / 0 |
| 一 | 0/3 | Unclear / Unclear / Unclear | 100.0% | uncertain / uncertain / uncertain | 100.0% | 47.1–57.9% | 240.50–250.76 | 2 / 1 |
| 苹 | 3/3 | Level-like / Rising / Level-like | 66.7% | different / consistent / different | 66.7% | 37.9–58.5% | 212.52–216.96 | 0 / 0 |


| Take | Character | Raw coverage | Retained coverage | Selected median Hz | Islands | Gesture / confidence | Reason | Comparison |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 要 | 75.6% | 75.6% | 279.11 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T1 | 一 | 51.5% | 57.6% | 243.28 | 3 | Unclear / low | tracker_instability | uncertain |
| T1 | 苹 | 48.3% | 37.9% | 212.52 | 1 | Level-like / moderate | acoustic_shape_only | different |
| T2 | 要 | 77.8% | 77.8% | 321.88 | 1 | Unclear / low | ambiguous_shape | uncertain |
| T2 | 一 | 57.9% | 57.9% | 250.76 | 2 | Unclear / low | insufficient_voicing | uncertain |
| T2 | 苹 | 68.3% | 58.5% | 216.96 | 2 | Rising / moderate | acoustic_shape_only | consistent |
| T3 | 要 | 97.6% | 88.1% | 281.01 | 4 | Unclear / low | tracker_instability | uncertain |
| T3 | 一 | 55.9% | 47.1% | 240.50 | 3 | Unclear / low | tracker_instability | uncertain |
| T3 | 苹 | 45.6% | 42.1% | 212.56 | 1 | Level-like / moderate | acoustic_shape_only | different |


**No rule changes any of the nine broad gestures or verdicts.** 苹 remains Level-like / Rising / Level-like and different / consistent / different: 66.7% agreement. 要 and 一 remain Unclear / Unclear / Unclear, zero usable takes. Increasing coverage alone fails the primary acceptance metric.

## Replay matrix and safety

[Complete 132-row matrix](capture-robustness-replay.csv): all four methods on 31 real files plus digital silence and a transient click. Every row contains exact identity/hash, raw/retained coverage, islands, missing runs, jumps, protected low-F0 changes, unowned/quiet retention and runtime. [Repeatability CSV](capture-robustness-repeatability.csv) also provides exact coverage and median-F0 spreads and instability-take counts.

| Method | Raw finite / all | Retained / all | Islands | >6 / >12 st | Protected low changes | Unowned retained | Net median rule ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Before | 4453/9995 | 3317/9995 (33.19%) | 199 | 31/13 | 0 | 359 | 0.000 |
| A: high-pass | 4453/9995 | 3348/9995 (33.50%) | 203 | 33/13 | 0 | 361 | 0.171 |
| B: adaptive range | 4453/9995 | 3328/9995 (33.30%) | 199 | 30/12 | 0 | 359 | 0.252 |
| C: continuity | 4453/9995 | 3359/9995 (33.61%) | 198 | 31/14 | 2 | 363 | 1.576 |


This aggregate includes padding and negative controls; higher totals are not evidence of improved speech quality. Original raw coverage is deliberately invariant across candidate rules. “Unowned” includes pauses, untimed syllables and timing margins; it is not automatically silence. RMS <.003 intervals retain zero pitch under all rules, but that easy proxy does not certify unvoiced-material safety.

- **Healthy human 苹** (`422877d2`): unchanged 27/37 retained, 107.846–124.922 Hz, Rising/moderate/consistent for all four methods. Its healthy 要 remains Falling/moderate. Prior Google 要 also remains Falling/moderate; local continuity adds two frames there without changing the gesture.
- **Low-F0 safety:** 617 protected frames in 18 existing non-silence user recordings, inside trusted character intervals, below 100 Hz, strength ≥.8 and high-pass agreement ≤.5 st. This is a conservative acoustic proxy, not independent F0 gold. A/B preserve all 617. C changes two in `7787300e` 五: at 2.5024 s the 54.773-Hz/.8815 frame becomes excluded after downstream filtering; at 2.5124 s 54.610/.8415 becomes 108.620 Hz. There is no independent basis to declare this protected low voice an error. **C fails low-voice preservation.** This corpus does not certify diverse speakers or every expressive register.
- **Historical high 州** (`f5dc0cc1`): the ~476/467/463-Hz branch and its 21.876-st transition remain unchanged under every rule; none worsens or fixes it. **Latest 州** (`9b1d959a`): every rule increases retained frames 25→31 and changes Unclear/uncertain to Level-like/consistent. Without independent fundamental truth, this is unvalidated added confidence, not a certified improvement.
- **吧 cases** (`f3c642b5`, `e59a6350`, `209ef0c7`, `dccf8a63`): no rule recovers a usable gesture. The two original all-missing cases remain empty; later sparse cases remain conservative. Representative T3 sentences are included, including partial word timing; no words are divided to manufacture syllable evidence.

| Negative control | Current speech guard | Before retained | A | B | C |
| --- | --- | --- | --- | --- | --- |
| de4b999e | no_speech | 0 | 0 | 0 | 0 |
| ab6c16ab | no_speech | 46 | 46 | 46 | 46 |
| 7e489fd3 | accepted | 76 | 79 | 76 | 78 |
| digital_silence | not a product request | 0 | 0 | 0 | 0 |
| transient_click | not a product request | 0 | 0 | 0 | 0 |


The second periodic-background recording has 46 analyzer-retained frames, but its speech guard rejects the request, so these are **diagnostic false pitch, not a published graph**. The accidental recording `7e489fd3-c36d-41f6-a20b-300616ad1a42`, SHA `fcaf551459dc957c7544e396858395e4214c2447aa23cc577a2f9c5261b28eaf`, is still accepted. A raises its retained count 76→79; C raises it 76→78. Both fail the explicit no-more-credible-noise criterion. B preserves the negative counts but fails repeatability. The presence guard is untouched; the false accept remains a separate product blocker.

### Repair versus abstention

Existing tracker-instability and insufficient-support abstention correctly prevent confident judgments on all three 一 takes. They do **not** catch the misleading confident level-like 苹 decisions, because the retained beginning is smooth while plausible later candidates were excluded or unselected. Candidate presence in the discarded tail is evidence of incomplete/ambiguous coverage, not permission to fabricate a rise. A bounded completeness/ambiguity abstention check is better motivated than the tested repairs, but its precision and loss of useful human feedback have not been calibrated here. No fourth acoustic rule or new production abstention threshold is introduced. Current status is **NO SAFE CHANGE**, with feedback remaining experimental as a readiness recommendation.

## Reference resolution fixes, independent of acoustics

**要 root cause: dictionary ambiguity plus missing grammatical context handling.** `resolve_run()` finds no containing phrase for 要 in this exact sentence; `character_options()` returns `yao4`, `yao1`, `yao3`. The resolver correctly avoids choosing by dictionary order but has no ordinary quantity-object rule. That makes `reading_source=unresolved`, lexical tone null, `surface_rule=reading_unresolved`, surface null. Mobile then correctly returns uncertain. It is not punctuation mapping, timing, schema propagation or the acoustic classifier.

The minimal added rule resolves **要 followed by an explicit numeral + existing recognized classifier** to yào/lexical T4, after longest phrase lookup. It also handles 你要两本书 / 我们要三杯水 / 要十二张纸. 要求/要挟 keep yāo; bare 要, 我要, incomplete 要一 and punctuation-separated context keep abstaining. No generic first-reading fallback or acoustic/target input was added. Reading version advances to `exact-text-lexical-context-v3.2`.

**个 root cause: citation T4 was used as a fixed production expectation.** The phrase dictionary stores 一个 as yí gè; citation normalization stores 一 as yi1 and 个 as ge4. Previously surface rules produced 一=T2, 个=T4/unchanged. A falling 个 therefore became consistent (T1, T3 and prior Google), even though ordinary quantity-classifier reduction can remove a full T4 gesture requirement. That positive state was comparison against an over-specific reference, not proof of a correctly realized neutral syllable.

The bounded correction reuses the existing adjacent **一 quantity** rule. For following lexical-T4 个, the surface result becomes **null**, rule `quantity_ge_reduction_optional`; lexical gè/T4 stays intact. This explicitly withholds a fixed contour expectation because text does not choose neutral/reduced versus stressed realization. It does **not** assert obligatory neutral tone or rewrite lexical tone to 0. Neutral itself is already represented as 0 and has no fixed comparison shape. Ordinal 第一个, 个个, reduplicated 一个个 and punctuation-separated 一/个 are outside this correction. Surface version advances to `exact-text-surface-v1.1`.

Fresh sentence semantics are therefore lexical **[3,4,1,4,2,3]**, contextual **[3,4,2,null,2,3]**. In a local replay through the actual TypeScript policy, the prior human and Google Falling/moderate 要 become consistent; all three newest 要 remain uncertain because their acoustic classifications are unclear. Previously positive 个 becomes uncertain. All pitch arrays, observed contours, timing and graph geometry remain byte-equivalent as JSON values.

Versioned analyzer configuration prevents fresh analysis from reusing an older reference policy. Historical stored analyses/targets are not rewritten, and reading an old result still shows its saved reference semantics. The replay above overlays freshly computed reference fields locally; it does not pretend persisted historical outputs were migrated.

## Assignment and mobile rendering

Exact provider mapper output, persisted intervals, raw timestamps, graph ownership and current normalized geometry agree. New T1/T2/T3 map **47/47, 49/49 and 52/52** owned Mine vertices respectively, total **148/148**. Prior human/Google/silence add 114 checked vertices. Each retained point stays in `[start,end)`; no 一→个 or 果→苹 reassignment occurs. No canonicalization offset or index drift is present.

| Take | Cell | Backend seconds | Rendered normalized x | Mine vertices |
| --- | --- | --- | --- | --- |
| T1 | 一 | 1.5839 → 1.8239 | 2.128982 → 2.681709 | 10 |
| T1 | 苹 | 2.4239 → 2.6239 | 4.243041 → 4.505110 | 2 |
| T2 | 一 | 1.2537 → 1.3937 | 2.294800 → 2.854800 | 6 |
| T2 | 苹 | 1.7337 → 1.9737 | 4.349298 → 4.794176 | 9 |
| T3 | 一 | 2.1634 → 2.3834 | 2.127600 → 2.619365 | 9 |
| T3 | 苹 | 2.9934 → 3.1934 | 4.257867 → 4.524533 | 2 |


The current transform is `cell_start + .12 + .76*(timestamp-start)/(end-start)`; actual mobile geometry was executed and checked within plot bounds with unchanged y/timestamp values. Both the good T2 and bad T1/T3 苹 states faithfully display backend selected evidence. **DISPLAY IS NOT THE ROOT CAUSE.** Structurally correct provider timing is not phonetic gold; no new evidence supports timing/assignment as the dominant cause. Screenshots themselves were not supplied in this turn, so this is backend-to-render-function verification, not a new physical-device screenshot inspection. No UI redesign.

## Runtime and validation

No production acoustic pass, threshold or pitch function changed: **zero added acoustic work**. Research timing includes a defensive copy; paired subtraction of baseline-copy cost gives the net rule timings in the aggregate table. Across these ≤7.9-s files, raw rule-plus-copy medians have maxima below 12 ms locally. A/C iterate over bounded candidate/neighbor windows; this B prototype scans the seed list and is not a production-optimized long-utterance implementation. No end-to-end/mobile latency bound or multi-speaker calibration is claimed.


Fresh six-character reference construction (warm cache, 200 measurements) is 0.129 ms median / 0.133 ms p95; no provider or acoustic work is included.


| Validation | Result |
| --- | --- |
| Focused backend readings/contours/perception/graph/presence + new quantity tests | 218 passed |
| Bounded full API, including extraction/filtering/reference and presence regressions | 512 passed; 4 opt-in PostgreSQL skipped; 5 known streaming cases deselected |
| Connected-speech / connected replay | 69 passed |
| Full native/web mobile, including SentenceToneGraph, Practice, Free Practice and Conversation | 336 passed, 26 suites |
| New direct quantity/reference semantic cases | 20 passed, included above |
| Ruff / formatting of all 5 Python files touched in this pass / API mypy | Passed; mypy 76 source files |
| Saved/current detailed baseline / real mobile transform | Exact; 36 timed units and 262 owned vertices |
| Both old exact silence regressions | Passed with hash-checked local fixtures |
| New accidental no-speech expected rejection | **Still fails: accepted**, intentionally not hidden by passing automated tests |
| Schema/mobile code changes, generated exports | None; no export regeneration needed |
| Whitespace and baseline-work preservation | Checked at completion |

The first full run exposed two old tests asserting full-T4 个; their expectations were updated to the intended optional-reduction semantics and the full suite rerun. These were resolved changes to relevant tests, not unrelated failures. The same five historical streaming cases remain excluded (three parameterizations of authoritative-interpretation ordering plus generation-failure ownership and meaning-byte streaming). Four optional PostgreSQL concurrency cases were not enabled. Existing React test-renderer/act warnings remain. No unrelated debt was changed.

Commands: `BENMA_TRUST_RECORDINGS=.../var/native-control/prior-negative-controls.json .venv/bin/python -m pytest -q tests -k 'not test_stream_orders_authoritative_interpretation_before_committed_reply and not test_stream_generation_failure_keeps_perception_and_rejects_other_account and not test_meaning_bytes_leave_server_while_generation_is_still_running'`; `PYTHONPATH=. services/api/.venv/bin/python -m pytest -q benchmark/pronunciation_v2/test_connected_speech.py benchmark/pronunciation_v2/test_connected_replay.py`; mobile `npm test -- --watch=false`; API `ruff check .`, touched `ruff format --check`, `mypy src`.

## Six final decisions

1. **DIRECT DIGITAL NATIVE — STILL UNVERIFIED.** Missing trustworthy character timing prevents a character-level pass despite useful whole-file F0.
2. **PHONE CAPTURE ROBUSTNESS — NOT ROBUST ENOUGH.** 一 has no usable gesture in any new take; 苹 alternates positive/negative states with incomplete-tail evidence.
3. **DOMINANT ROOT CAUSE — MIXED.** Praat candidate/voicing-path and octave/subharmonic susceptibility plus recording-energy/filter attrition dominate acoustic failure. The old quarter-frequency path and new upward/missing-tail cases share candidate ambiguity but are not one identical mechanism. Reference resolution independently blocks/misstates comparisons. Assignment/display is closed as the dominant hypothesis.
4. **ACOUSTIC STRATEGY — NO SAFE CHANGE.** A/C add pitch to known no-speech; C also changes protected low F0. B preserves those controls but improves none of the critical gestures. No production pitch repair or new acoustic abstention rule ships.
5. **LEARNER FEEDBACK — KEEP DESCRIPTIVE/EXPERIMENTAL.** This is the readiness recommendation; existing comparison UI remains unchanged, with more conservative 个 reference semantics.
6. **CURRENT STACK READINESS — PITCH ROBUSTNESS STILL BLOCKS CHECKPOINT.** Fixing silence alone would not establish readiness. The only production changes from this pass are the independently supported, bounded reference fixes.

**One next step:** validate a single candidate-aware **incomplete-contour abstention gate** against this frozen replay set: it must withhold confident level/different judgments on truncated 苹 while preserving the healthy human rise and low-F0 cases. Use the existing audio; do not expand into another tracker bakeoff.

For the next physical-device check of the reference fixes, use only **我要一个苹果。**: in More detail, 要 should resolve to lexical/reference T4, 一 remain contextual T2, and 个 retain lexical T4 while showing unresolved reference/uncertain comparison. T3 stays conservative. Do not expect all-green cells or improved acoustic paths. No new recording is required to review this pass; historical saved results retain their old references.

## Artifacts and reproducibility

- [Per-syllable full metrics](capture-robustness-syllables.csv), [all-method replay matrix](capture-robustness-replay.csv), [repeatability/spreads](capture-robustness-repeatability.csv).
- Ignored persistent workspace: [`services/api/var/capture-robustness/absolute-time-audit.html`](/home/jacob/benma/services/api/var/capture-robustness/absolute-time-audit.html), with all absolute-time traces, frame ownership, mobile mappings, candidate frames/intensities, similarity paths and frozen inventories.
- Scripts `audit.py`, `replay.py`, `similarity.py`, `candidates.py`, `intensity.py`, `reference-replay.py`, `mobile-audit.cjs` and validation logs are in that workspace; original capture audio remains in the pre-existing ignored audio store. Research repair signatures take only acoustic dictionaries. No user audio is added to tracked files.
- Reproduce from repository root with `PYTHONPATH=services/api/src services/api/.venv/bin/python services/api/var/capture-robustness/replay.py`; the frozen inventory supplies absolute verified audio paths. Research results use original saved references to isolate acoustic effects.
