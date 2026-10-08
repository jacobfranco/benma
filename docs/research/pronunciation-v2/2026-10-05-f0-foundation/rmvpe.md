# BENMA — RMVPE F0 FOUNDATION FINAL BAKEOFF

**RMVPE does not win. STOP TRACKER SEARCH — DESIGN AROUND EVIDENCE LIMITS.**

RMVPE makes substantial local improvements: it follows the old Google speech band, avoids the doubled onset and historical high 州 branch, preserves later rising material, and slightly improves the closest repeat while retaining more shared speech. It tracks the known 70-Hz signal and preserves far more low-register evidence than cleaned CREPE. CPU latency is credible: **0.286 s for the same 2.856-s clip**, versus CREPE's saved 29.059 s.

The decisive weakness is false vocal evidence in known negatives: **374/1947 native frames**, or **326/1947** with the predeclared stronger 0.05 gate. Smooth, high-confidence background survives. There are also **79 actual doubled-frequency error frames** in the weak-fundamental synthetic and **3/11 lowest-proxy upward octave disagreements** in real speech. These prevent a safe foundation migration despite the improvements. No production integration is recommended or performed.

## Five final decisions

1. **RMVPE DOES NOT CLEARLY IMPROVE THE FOUNDATION** — understood as a dependable product foundation across the joint criteria; several individual quality dimensions improve substantially.
2. **NOT SAFE ENOUGH**.
3. **NO TRACKER GOOD ENOUGH**.
4. **STOP TRACKER SEARCH — DESIGN AROUND EVIDENCE LIMITS**.
5. **DESIGN TRUSTWORTHY PRODUCT BEHAVIOR AROUND PARTIAL/UNCERTAIN ACOUSTIC EVIDENCE**.

There is no seventh-tracker recommendation, new broad bakeoff, per-character switching, tone-informed repair, or ensemble proposal.

## Implementation, checkpoint and exact configuration

The implementation is [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/tree/81eed5e8f68b6bed1789f682fe78cdd324495afc), fixed commit **`81eed5e8f68b6bed1789f682fe78cdd324495afc`**. The unmodified files used are [`infer/rmvpe.py`](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/infer/rmvpe.py) and its `tools/cuda_graph.py` helper. CPU execution uses the helper's eager path, without CUDA. This is the RVC implementation/checkpoint, not a claim to have evaluated every RMVPE training or implementation variant.

The RVC README links the pretrained `rmvpe.pt` distributed by `lj1995/VoiceConversionWebUI` and credits yxlllc and RVC-Boss. Exactly one checkpoint was downloaded from [the pinned model revision](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e6d0c1a17da07c33557852f9dfa2bd44cc75737d/rmvpe.pt). It is **181,184,272 bytes / 172.79 MiB**, SHA-256:

```text
6d62215f4306e3ca278246188607209f09af3dc77ed4232efdd069798c4ec193
```

The published Git-LFS pointer and downloaded bytes agree. [Download receipt](rmvpe-download-receipt.json) records the full model revision, URL, bytes and source hash. RVC source is [MIT licensed](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/LICENSE); the [checkpoint repository](https://huggingface.co/lj1995/VoiceConversionWebUI) declares MIT in model-card metadata. That declaration is recorded as such, not invented as a separate checkpoint-specific license grant. The original Dream-High research repository has Apache-2.0 licensing; its code/checkpoint was not substituted for this RVC path.

No packages were installed for this extension. It reuses the previous isolated research environment: Python 3.12.13, Torch 2.8.0+cpu, librosa 0.11.0, NumPy 2.5.3, SciPy 1.18.1 and the existing resampler. Source and model are under ignored `services/api/var/f0-foundation/rmvpe/vendor/`. No production dependency manifest or lockfile changed. The model has 90,423,165 parameters, loaded as float32 on CPU. The checkpoint's compact tensor storage does not imply 173-MiB process RAM.

Exact fixed inference settings:

- Whole utterance, CPU, float32, `eval()`, deterministic Torch algorithms, one intra-op and one inter-op thread.
- 16-kHz mono float input. The existing 24-kHz sources are resampled with librosa `soxr_hq`, matching the upstream example's default resampler. PCM16 scaling only; no gain normalization, high-pass filter or augmentation.
- Native 128-channel HTK mel representation, 30–8000-Hz mel range, 1024-sample Hann window, 160-sample hop, centered reflection padding, log clamp `1e-5`.
- Native network padding to a multiple of 32 time frames, then trim. The network sees the whole utterance; no chunk boundary or syllable crop is introduced.
- All 360 pitch bins, 20-cent spacing, centers **31.7–2005.497 Hz**. No imposed 50-, 70- or 550-Hz mask, octave correction, smoothing or Viterbi replacement.
- Native argmax and salience-weighted local average over the winning bin ±4 bins, then Hz conversion. `infer_from_audio`/`decode` default threshold **0.03**. The lower-level local-average function's signature default is 0.05, but the public inference method explicitly passes 0.03.

The 30-Hz mel lower edge is not a 30-Hz F0 guarantee. Pitch-bin support includes 54–70 Hz; it cannot reliably represent fundamentals below its lowest bin, and support in range does not establish real low-register accuracy. No below-range signal was added to the benchmark.

## Raw output and confidence semantics

Each native frame has 360 sigmoid salience values, not a normalized categorical distribution or calibrated probability that the learner is speaking. The decoder takes their maximum as its threshold evidence. **Maximum ≤0.03 produces native F0 zero**, which the research track represents as null with `native_voiced=false`; values above the threshold yield positive F0. Confidence remains available even when pitch is null.

The immutable research frame tuple preserves native times (`i × .01 s`), F0/null, max salience, native voicing and five leading candidate bins. Forty-nine NPZ files additionally preserve every **13,318 × 360** salience value, exact native F0 including zero, confidence, bin centers, and the native decode with threshold zero. The latter is auxiliary evidence for the bounded sweep, **not** the primary raw result or a new tracker. NPZ ZIP timestamps need not be byte-identical; numeric arrays are deterministic.

There is no inference dithering or sampling. Dropout is disabled by `eval()`. Model construction initially draws random weights before loading the complete checkpoint; the adapter preserves the caller's Torch RNG state during that construction. Four real-waveform metadata contexts, repeated warm calls, cold-versus-warm evidence and a repeated full salience extraction are identical. The adapter's default native output also exactly matches upstream `infer_from_audio` on the same 16-kHz input. See [verification-rmvpe.json](verification-rmvpe.json).

## Corpus and character-free invariant

**49 completed, zero failed, zero skipped.** The exact prior 32 real captures, direct digital reference, three benign derivatives, ten known-F0 signals and three synthetic negatives were reused. All audio hashes were verified before inference; no corpus synthesis, regeneration, new recording, removal or relabeling occurred for extraction. Existing raw tracks, production ablations, 36 audio-only alignment paths, diagnostic windows, support annotations and protected-proxy timestamps were reused. The research regression suite separately checks deterministic synthetic generation in temporary test directories; these files do not enter the benchmark.

The actual historical `f5dc0cc1` waveform was independently extracted with **贵州, 鬼粥, empty text, and arbitrary nonsense**, including conflicting tone/target metadata. All canonical evidence bytes match, SHA-256 `e94598db41811cacd91b70d6df21aa9bf1a96e1dc8a765b73e72d247a10717fa`. The metadata adapter forwards only `audio_path`. No transcript, tone, pinyin, target or alignment reaches RMVPE.

## Direct native, difficult speech and octave behavior

All **45/45** previously marked direct-native harmonic-core frames lie in their existing 190–320-Hz band, raw and gated. The full source has **78/106** emitted raw frames in two islands, versus 73/100 for AC. RMVPE produces no pitch in the eight annotated trailing nonvoiced frames. It leaves a gap near .4 s, avoids AC's isolated high branches, and follows an irregular descending tail to about .85 s. The previously marked .66–.92 s ambiguous region is not exact-F0 truth; filling it earns no accuracy credit. Gate 0.05 removes one native frame (77/106), not the tail's uncertainty.

Coarse in-band support is **329/329** across the five frozen annotated files at every tested threshold: direct native 45, Google 101, human 48, historical `f5dc0cc1` 22, low-register `7787300e` 113. AC raw covers 304/329 within these bands; CREPE raw also covers all 329. This is a coarse, post-hoc spectral check inherited unchanged from the previous pass, not an independent cents-error benchmark.

| Frozen diagnostic | RMVPE native result | Assessment versus saved baseline |
| --- | --- | --- |
| Old Google 一 | 35 frames, median 229.21 Hz, range 202.38–296.76 | Avoids AC/CC's sustained ~55–57-Hz path; follows visible speech band |
| Old Google 苹 | 41 frames, median 215.17 Hz, +1.63-st first/last-quintile change | Avoids baseline's low branch; retains speech evidence |
| take_1 / take_3 一 | 30 / 29 frames, median 226.45 / 228.03 Hz, +3.97 / +4.07 st | Avoids AC/CC doubled onset; no >9-st jump inside these windows |
| take_1 苹 | 47 frames, +2.43 st, last finite 2.860 s | More later rise than raw AC's 28 frames/+1.30 st/2.784 s and production's 21/+.42/2.624 s |
| take_3 苹 | 43 frames, +2.06 st, last finite 3.400 s | More late support than raw AC's 26 frames/+.55 st/3.343 s and production's 21/+.34/3.193 s |
| take_2 苹 | 32 frames, +4.74 st | Preserves the stronger rise; genuine performance differences remain |
| Human 苹 | 33 frames, +1.75 st | Healthy low-voice trajectory preserved; extra boundary coverage is not automatically correct |
| Historical 州 | 17 frames, median 140.95 Hz, maximum 149.87 Hz | Avoids ~462–476-Hz branch and baseline ~21.9-st jump; irregular terminal descent remains uncertain |
| Four prior 吧 windows | `f3c642b5` 4, `e59a6350` 7, `209ef0c7` 13, `dccf8a63` 18 frames | Some plausible fragments recovered, but no robust general recovery of the sparsest cases |

These are post-extraction windows only. First/last-quintile changes describe retained acoustics, not expected tone correctness. Whole-file inspection also finds two brief doubled spikes in Google around 3.5–3.6 s, a brief low glitch in take_3, and stationary pre-roll fragments in take_1. RMVPE has **22 adjacent >9-st jumps** across the 30 speech/direct files, falling to 17 at gate 0.05; nearby-gap counts are 32→27. These are discontinuity proxies, not an independently measured real-speech error rate. Its better important trajectories do not establish general octave safety.

## Repeated-capture consistency and perturbations

All **36 saved DTW paths** are reused unchanged. No new alignment, linguistic timing or F0-conditioned path is computed. Metrics retain the prior mutual-voicing, active-mask, half-hop matching, 50-ms median correlation and fragmentation definitions.

| Pair / RMVPE view | Mutual seconds | Median / p90 absolute st | Broad correlation | V/UV agreement | >9-st count | Island difference |
| --- | --- | --- | --- | --- | --- | --- |
| take_1 / take_3 raw | 2.07 | .027 / .096 | 1.000 | .996 | 0/207 | 3 |
| take_1 / take_3 gate .05 | 2.02 | .027 / .093 | 1.000 | .983 | 0/202 | 0 |
| take_1 / take_2 raw | 2.09 | .520 / 2.717 | .832 | .957 | 4/209 | 4 |
| take_2 / take_3 raw | 1.32 | .651 / 2.432 | .799 | .953 | 5/132 | 1 |

The closest repeat improves on AC raw's **1.82 s, .030/.102 st, .904 V/UV agreement** while avoiding its repeated wrong onset and weak late rise. CREPE clean gives 1.68 s, .109/.263 st and .970 V/UV agreement. This is meaningful local evidence, with a very small conditional pitch-error advantage over AC. Pairs involving take_2 contain genuine source/prosodic differences; their remaining 4–5 large disagreements and weaker correlation rule out a claim of uniformly superior consistency. All six trackers' existing/new rows appear together in [repeatability-tables.md](repeatability-tables.md).

Perturbations use the exact prior .03–.99-s query grid, without DTW:

| Native derivative / raw RMVPE | Median / p90 st | Correlation | V/UV agreement | >9-st count |
| --- | --- | --- | --- | --- |
| App 16-kHz canonicalization | .000 / .002 | 1.000 | 1.000 | 0 |
| Quarter gain | .009 / .069 | .998 | .969 | 1 |
| 100–3500-Hz bandpass | .005 / .091 | .991 | 1.000 | 0 |

The one gain-related octave disagreement occurs in the uncertain tail and disappears with gate .05, at lower mutual coverage/V/UV agreement (.948). This is strong conditional stability on one short source, not perfect invariance or proof that the tail's pitch is valid.

## All ten known-F0 controls

Every evaluated known-voiced core is retained: **1404/1404**, zero false gaps raw and at gate .05. No halving events occur. The weak-fundamental control contains one core doubling event, **79/145 frames**; all other nine controls have zero octave errors. Overall 79/1404 exceed 9 st. Accuracy uses the unchanged ±80-ms boundary exclusion and native time grids.

| Signal | Coverage | Median abs Hz | Median cents | p95 st | Maximum st | Halved / doubled frames | False gaps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 70 Hz | 145/145 | .230 | 5.705 | .116 | .119 | 0 / 0 | 0 |
| 110 Hz | 145/145 | .102 | 1.599 | .018 | .020 | 0 / 0 | 0 |
| 180 Hz | 145/145 | .192 | 1.848 | .029 | .031 | 0 / 0 | 0 |
| 260 Hz | 145/145 | .079 | .524 | .008 | .010 | 0 / 0 | 0 |
| Rising sweep | 145/145 | .085 | .955 | .026 | .037 | 0 / 0 | 0 |
| Falling sweep | 145/145 | .083 | .876 | .026 | .037 | 0 / 0 | 0 |
| Valley | 145/145 | .066 | .807 | .021 | .029 | 0 / 0 | 0 |
| Octave-risk mixture | 145/145 | .069 | 1.082 | .050 | .062 | 0 / 0 | 0 |
| Weak fundamental / strong second | 145/145 | 109.202 | 1193.711 | 11.949 | 11.955 | 0 / 79 | 0 |
| Voice interrupted by noise | 99/99 | .116 | 1.820 | .030 | .033 | 0 / 0 | 0 |

The **70-Hz control passes**: every core frame remains, median error .057 st. This is a substantial contrast with production AC's removal of all 145 correct frames. RMVPE also leaves all 40 evaluated negative frames of the interrupted-voice control unvoiced. The weak-fundamental octave switch survives every threshold in the bounded sweep; native confidence is not a reliable octave-error detector. [Synthetic tables](synthetic-tables.md) include all six trackers, event counts, maximum Hz error in the CSV, and raw/gated views.

## Real low-F0 safety

RMVPE retains **617/617** previously protected samples in all 18 recordings at both native and .05 thresholds, with no missing samples and three upward >9-st disagreements. This is better retention than CREPE clean's 578/617 and much better lowest-register preservation. The baseline selection remains biased toward AC and production; these are safety proxies, not independent F0 truth.

| Lowest proxy file | Baseline median Hz | RMVPE covered | RMVPE median Hz | Upward octave disagreement | Median max salience |
| --- | --- | --- | --- | --- | --- |
| `7787300e` | 54.773 | 3/3 | 111.422 | 3/3 | .397 |
| `c95673d3` | 55.576 | 5/5 | 55.401 | 0/5 | .225 |
| `27ea3b92` | 58.329 | 3/3 | 58.249 | 0/3 | .258 |

All eleven samples remain, but only **8/11 agree without an upward octave disagreement**. AC/CC and production retain 11/11 without those disagreements; CREPE raw has eight disagreements and its cleaned sole retained frame is itself doubled. The three discrepant real samples could involve irregular phonation/subharmonics; this pass cannot certify which path is true. They withhold a complete low-F0 safety claim. The synthetic weak-fundamental error is independently known and does not depend on that uncertainty.

RMVPE preserves all **113/113** previously marked clear low-voice harmonic frames in long `7787300e`, versus raw/production AC 109 and cleaned CREPE 105. In the broader protected cohorts it covers 58/58 `7787300e` samples (median 93.071 Hz, seven proxy islands, longest .21 s), 85/85 `c95673d3` (92.923 Hz, seven islands, .36 s), and 19/19 `27ea3b92` (91.937 Hz, four islands, .14 s). The user-identified human control retains all 48 clear-core frames and its one protected <100-Hz sample (98.398 Hz, salience .750). All per-recording coverage, confidence, continuity and disagreement rows are in [low-f0-proxy.csv](low-f0-proxy.csv).

## Silence/noise and the single bounded gate sweep

The negative labels remain frozen, including the accidental-silence false accept. Harmonic background or another audible voice may have real physical F0; it is still unsafe evidence for the learner's own vocal graph. An estimator cannot establish source ownership from F0 alone. No negative was removed or relabeled after inspection.

| Negative | Raw emitted / total | Raw fraction | Longest raw run | Raw confidence median / max | Gate .05 emitted / longest run |
| --- | --- | --- | --- | --- | --- |
| Original silence | 103/679 | 15.2% | .87 s | .688 / .842 | 98 / .85 s |
| Periodic silence | 111/351 | 31.6% | .70 s | .065 / .174 | 75 / .33 s |
| Accidental silence | 160/314 | 51.0% | .93 s | .701 / .947 | 153 / .90 s |
| Digital silence | 0/201 | 0% | 0 | No emitted F0 | 0 / 0 |
| Stationary noise | 0/201 | 0% | 0 | No emitted F0 | 0 / 0 |
| Clicks/transients | 0/201 | 0% | 0 | No emitted F0 | 0 / 0 |

The long, high-confidence runs can plausibly look like voice. Across full negatives, **374/1947 = 19.2%** raw and **326/1947 = 16.7%** gated remain. The comparable saved counts are AC 427 raw / 418 minimal / 122 production, CREPE 1947 raw / 289 minimal, and pYIN 670 raw / 39 minimal. The five prior minimal views also used energy and island removal; RMVPE's optional view is native confidence only, so these are explicitly different fixed operating points.

The long low-register recording's **305 annotated pause frames** contain 34 raw RMVPE pitch frames and 23 gated, confidence reaching .278. Other annotated nonvoiced masks in direct native, Google, human and `f5dc0cc1` are fully unvoiced. Good results on those masks and synthetic negatives do not erase the whole-file real-background failures.

The five values were declared before inference: **.01, .02, .03, .04, .05**. Only native maximum salience is tested; no energy gate, minimum island, extra pitch range, smoothing, repair or per-file threshold is introduced. The .05 endpoint is shown in the viewer for inspection, not recommended for production.

| Threshold | Negative emitted /1947 | Whole speech-file emitted /9043 | Protected low /617 | Lowest /11 (upward disagreements) | Frozen harmonic support /329 |
| --- | --- | --- | --- | --- | --- |
| .01 | 496 | 5112 | 617 | 11 (3) | 329 |
| .02 | 424 | 4670 | 617 | 11 (3) | 329 |
| .03 native | 374 | 4426 | 617 | 11 (3) | 329 |
| .04 | 358 | 4262 | 617 | 11 (3) | 329 |
| .05 optional view | 326 | 4151 | 617 | 11 (3) | 329 |

Whole speech-file counts include pauses and are not a real-voice recall metric. All five thresholds retain the existing clear harmonic cores, but none suppresses the real negatives acceptably. Some negative salience exceeds protected low-voice salience by a large margin. **Reject this gating strategy as a sufficient production safety solution.** No wider sweep or unmeasured tuned threshold is proposed. [Summary](rmvpe-threshold-summary.csv) and [all 245 recording/threshold rows](rmvpe-threshold-sweep.csv) preserve the results.

## CPU runtime and resource burden

Same desktop as the prior pass: Intel Core i7-10700F @2.90 GHz, CPU float32, one Torch/BLAS thread, serial timing without plotting or other tracker inference running. Model initialization is timed separately and includes imports, source/checkpoint hash verification, construction and loading. Warm extraction includes reading/resampling, native inference and research frame packaging; no activation-file compression or output JSON serialization.

| Measurement | RMVPE | Saved CREPE full |
| --- | --- | --- |
| Explicit model import/load | 2.629 s | 1.270 s |
| Cold first 1.05-s native extraction | .222 s | 11.969 s |
| Warm 1.05-s native median, three calls | .125 s | 10.799 s |
| Warm 2.856-s human median, three calls | **.286 s** | **29.059 s** |
| Human-only wall RTF | .100 | 10.174 |
| Median wall / CPU RTF, all six warm calls | .113 / .112 | 10.237 / 10.206 |
| Verification-process peak RSS | 923.2 MiB | 933.8 MiB |
| Checkpoint | 172.79 MiB | 84.87 MiB |

The warm human path is approximately **101.5× faster** than the saved CREPE measurement. GPU is **not required** for practical extraction on this CPU. A persistent server worker is a credible latency path; cold import/load still costs seconds, RSS is substantial, and target-server concurrency/mobile deployments are unmeasured. Quality, not CPU speed, blocks migration. All 49 extraction timings (including activation compression) are in [rmvpe-per-file-runtime.csv](rmvpe-per-file-runtime.csv); they are not substituted for the controlled warm benchmark.

## Viewer, review and verification

The [existing local viewer](/home/jacob/benma/services/api/var/f0-foundation/viewer.html) now has six independent tracker toggles, raw and optional minimal views, original production-AC overlay, waveform/spectrogram/confidence against actual utterance time, and local audio. It is offline. The implementation reuses the previous viewer; no product UI changed. Source numeric evidence remains intact, and the original five-tracker figures and `/tmp/benma-f0-bakeoff/viewer.html` remain available.

A fresh A–F permutation was generated; 13 representative raw panels were reviewed before opening the key or the numeric RMVPE comparison. [Initial notes](rmvpe-blind-review-before-reveal.md) and [hash receipt](rmvpe-blind-review-receipt.json) precede reveal. Key: **A RMVPE, B Harvest, C pYIN, D CREPE, E AC, F CC**. The reviewer knew candidate families and prior trajectories and could infer identities from familiar shapes. This is explicitly **semi-blinded**, not an independent listening panel. The notes found A's improved difficult trajectories alongside its negative runs and weak-fundamental octave switch; no lexical tone expectation entered the assessment.

Research tests verify actual deterministic F0 and salience, four-context real-waveform invariance, exact 49-file coverage/hashes, native null/confidence semantics, known-F0 accounting, negative-control/sweep accounting, removal-only gate behavior, unchanged previous artifacts, and six-tracker viewer data. Chromium verifies all 49 cards, six raw/minimal/confidence groups per card, all six toggles, view switching, production overlay and local audio decoding/playback. See [validation.md](validation.md) for final test, hash and preservation receipts.

## Architecture and next product pass

Raw pitch extraction was already character-free and remains so. Preserve **canonical audio → character-free estimator → immutable UtterancePitchTrack → acoustic truth boundary → optional ASR/timing projections → character/group views → gesture/reference comparison**. Future orchestration can compute/persist acoustics concurrently with ASR using the existing audio-only service. No per-character tracker choice or tone-informed F0 correction follows from this result.

The next pass must design trustworthy behavior around incomplete or uncertain acoustic evidence: distinguish observed acoustic pitch from confidence that it belongs to the learner, retain gaps and ambiguous paths without inventing a contour, and decide what the product can responsibly show or decline to judge. That is a product/evidence-design pass using the available foundation limits, not another tracker search. Production extraction, filters, classification, learner verdicts, UI and silence guard remain unchanged by this evaluation.
