# Luilui6666 T3 acoustic forensics — 2026-09-30

**Executive summary.** Benma sees several different failure modes in these valid T3 recordings. Eleven of 13 trigger tracker instability; one (`五`) has a dip/recovery across a dropout but fails the whole-clip coverage gate; one (`你`) has strong, continuous, predominantly falling F0 with a small late recovery that disappears from the five-bin gesture summary. The energy gate removes **zero** frames, evidence-region selection trims **zero** clips, and reliable-contour filtering removes only **2 of 336** voiced T3 frames. Thus those stages are not deleting a clean T3 contour wholesale.

T3 has more missing F0 during energy-active speech, larger tracker jumps, lower tracked register, lower periodicity, and lower recorded energy than T4 in this sample. These are descriptive differences with substantial overlap, not a validated tone detector or proof of creaky phonation. Whole-recording missing-F0 percentages are actually similar because both groups contain substantial padding. The two wav2vec-correct T3s are also tracker-unstable. **Multiple interacting issues are supported; the specific wav2vec representation-versus-head cause remains unresolved. Keep every clip, retain lexical labels, and change no production behavior.**

Start with the [visual gallery](index.html), [distribution plot](plots/comparison.svg), and [human audit index](human-audit-index.md). Every clip has a committed five-panel plot. The analysis also generates complete diagnostic JSON locally; those large generated payloads are intentionally excluded from Git. [Pipeline and measurement definitions](pipeline.md) explain the timing assumption, production imports, drawer transformations, and diagnostic limitations. [Environment and validation](environment.md) gives reproduction commands.

## Scope and truth boundary

All **13 T3 and all 21 T4** included primary-test recordings from `lingualibre:Q301531` are included, sorted by asset ID before joining predictions. T4 selection does not depend on classification. This is a complete within-speaker comparison, **not phonetic-segment-matched pairs**. No training, model execution, classifier fitting, threshold tuning, label changes, cloud calls, or new listening occurred. The previous human listening observations are accepted as perceptual notes; the measurements below do not directly identify laryngeal mechanism.

All 34 fresh acoustic results and complete observed-contour objects reproduce the saved frozen V1 evidence exactly. Frozen wav2vec probabilities are read from experiment #1. Those probabilities are classifier outputs, not confidence in the lexical truth.

## Descriptive comparison

Values are per-clip medians [25th–75th percentiles], except explicit counts. No significance tests, feature selection, or predictive evaluation were performed. Full means, extrema, and distributions are in [t3-vs-t4-summary.csv](t3-vs-t4-summary.csv); all measurements are in [per-clip.csv](per-clip.csv).

| Measure | T3, n=13 | T4, n=21 |
|---|---:|---:|
| Whole-clip tracker-frame F0 coverage | 33.7% [27.5–34.9] | 30.8% [28.9–36.1] |
| Whole-clip missing F0 | 66.3% [65.1–72.5] | 69.2% [63.9–71.1] |
| Missing F0 among energy-active frames | 16.7% [4.5–21.9] | 4.3% [0–9.7] |
| Clips with internal raw-F0 gaps | 12/13 | 13/21 |
| Internal raw gap count | 2 [1–2] | 1 [0–1] |
| Total internal missing-frame duration | 30 ms [20–70] | 10 ms [0–50] |
| Largest internal raw gap | 20 ms [10–60] | 10 ms [0–50] |
| Tracker-instability flag/reason | 11/13 (84.6%) | 11/21 (52.4%) |
| Maximum tracker jump, production definition | 18.26 st [13.01–21.09] | 6.00 st [0.99–16.57] |
| Clips with production octave-like jumps (9–15 st) | 6/13 | 5/21 |
| Median tracked F0 | 188.6 Hz [168.0–203.5] | 223.6 Hz [203.9–237.6] |
| Minimum tracked F0 | 100.4 Hz [64.4–147.3] | 162.5 Hz [96.3–167.0] |
| Retained semitone range | 21.55 st [17.90–22.43] | 9.04 st [8.10–17.21] |
| Retained minimum position within voiced span | .750 [.538–1.000] | .757 [.667–.963] |
| Retained middle→final third change | −1.42 st [−6.64–8.60] | −2.12 st [−5.95–.25] |
| Mean active-frame selected periodicity | .620 [.562–.750] | .702 [.670–.845] |
| Mean voiced-frame selected periodicity | .727 [.678–.786] | .776 [.742–.841] |
| Voiced frames below .65 periodicity | 25.0% [20.0–45.5] | 16.7% [8.3–26.5] |
| Competing octave candidate fraction | 28.6% [13.3–44.0] | 23.1% [16.7–45.8] |
| Retained voiced duration | .26 s [.21–.28] | .27 s [.24–.30] |
| Recording duration | .883 s [.883–.968] | .883 s [.883–.883] |
| Recording RMS | .0457 [.0415–.0537] | .0768 [.0578–.0899] |
| Ending/onset RMS over energy-active span | .467 [.386–.486] | .603 [.540–.813] |
| Frozen wav2vec outputs | T3: 2; T4: 8; T1: 3 | T4: 17; T1: 4 |

The very large pitch ranges and recoveries are **tracker estimates with branch ambiguity**, not verified physiological pitch excursions. The candidate ambiguity distributions overlap strongly. The median adjacent-frame pitch change is actually smaller in T3 (.231 st) than T4 (.362 st); smooth T4 falling motion can drive this measure. It is not cycle-to-cycle jitter.

## Answers to the research questions

**1. What does the tracker see?** Predominantly falling stretches mixed with missing frames, very low branches, and abrupt changes to higher branches. It does not consistently recover one clean dipping contour. `你` is the high-quality falling exception: 38 consecutive voiced frames, mean voiced periodicity .948, no internal gaps, and maximum production jump 1.286 st. `早` has only 11 voiced frames out of 91 (12.1%), 100 ms total internal gaps, and 59.3% missing F0 during energy-active frames. `纸`, `笔`, and `等` have maximum jumps of 17.25, 21.09, and 21.31 st respectively. Those observations preserve the user-identified anomaly rather than correcting it.

**2. Are recognizable T3 contours present in measured F0?** Some tracks contain falling and recovering portions, but no T3 receives a reliable `3-like` judgment. Four T3s (`晚`, `五`, `买`, `狗`) have at least a 1-st fall and recovery in equal-time third means. Eight (`晚`, `五`, `想`, `表`, `纸`, `买`, `笔`, `狗`) meet the classifier's interior-trough and ≥1.5-st limb geometry before considering quality. These are descriptive geometry counts, not relabeling or a rerun with relaxed gates. Five T4s also meet that latter geometry condition, illustrating why ambiguous branch changes cannot certify a T3 dip. `五` has a clear broad fall and a later higher segment, but the recovery crosses missing F0. A continuous physiological recovery is not measured there.

**3. If a clean dip is absent, why?** In most T3s the selected pitch path is discontinuous or switches frequency branches. A low branch may reflect real irregular vibration, a subharmonic choice, or another tracker ambiguity; no independent F0 ground truth identifies which. `你` is different: F0 starts at 258.7 Hz, reaches 148.3 Hz at 86.5% of its voiced span, and ends at 166.8 Hz, approximately a 2.04-st late rebound. Five equal-count median bins are `[3.586, 1.955, .203, −1.492, −2.556]` st, so that small late rebound does not survive as a bin-level recovery. The median smoothing still shows the rebound; bin summarization and broad-shape rules are the specific further loss here. The human's T3 judgment remains valid.

**4. How often is F0 missing or unstable?** See the table. The meaningful distinction is active-speech missing F0 and instability, not the whole-file missing fraction. Production `f0` exactly equals pre-energy-gate tracker F0 wherever either is present in these 34 clips: there are zero energy-gated frames. The missing samples arise at the tracker stage, including expected unvoiced consonants and padding; they cannot all be assigned to phonation difficulty. No evidence-region trimming occurred. T3 retains 334/336 gated voiced frames; T4 retains 553/560. Most questionable branches therefore remain inspectable.

**5. Is irregular phonation plausibly associated with tracking difficulty?** Yes, as a hypothesis consistent with the human notes and the group-level lower periodicity, active-frame dropouts, low branches, and large jumps. It is not established causation. The saved `voicing_probability` is Praat selected-candidate autocorrelation strength, not a calibrated probability or direct measure of creak. Octave competitors are common in both groups, and some errors have high periodicity (`我`: .891 voiced mean). No calibrated creak score, pulse-level jitter, electroglottography, or independent manual pitch annotation was collected.

**6. Are T3 and T4 distinguishable with existing acoustic information?** Descriptively, partly: their distributions differ in register, active-frame coverage, instability, periodicity, and energy. This does not establish accurate per-clip discrimination, speaker-independent generalization, or benefit to learner evaluation. Labels, consonants/vowels, speaking style, and recording level are not experimentally controlled. No classifier was fitted to these features.

**7. Which features separate them most visibly?** Large tracker jumps/expanded estimated range, active-frame missingness, tracked register, and RMS are the clearest plots. Periodicity and the relative ending-energy pattern offer supporting differences. Minimum-pitch location is nearly identical at the group median; retained voiced duration is also similar. Those are weak separators here. Absolute low register is partly removed by utterance-relative normalization: the baseline remains stored, but the gesture classifier operates on relative pitch. Energy and periodicity mainly support quality decisions rather than a learned phonation-sensitive tone category.

**8–9. What does V1 call each T3, and what would the drawer show?** Under the same whole-isolated-clip timing assumption used by frozen V1, the exact backend classification and frontend projection are:

| Clip / asset suffix | wav2vec output, probability | V1 observed / confidence | Reason | Primary drawer |
|---|---|---|---|---|
| 你 ni3 / 113935451 | T4 .969 | 4-like / moderate | acoustic_shape_only | “Tone 4”; falling five-bin Mine; “Expected Tone 3. Yours sounded more like Tone 4” |
| 我 wo3 / 113935452 | T1 .479 | unclear / low | tracker_instability | Unclear; segmented measured-derived contour; “Pitch tracking was unstable” |
| 早 zao3 / 113935453 | T4 .963 | unclear / low | tracker_instability | Unclear; sparse falling fragments; tracker-unstable note; recording also flagged low voiced fraction |
| 晚 wan3 / 113935472 | **T3 .887** | unclear / low | tracker_instability | Unclear; low middle branch with gaps; tracker-unstable note |
| 五 wu3 / 113935506 | T4 .832 | unclear / low | insufficient_voicing | Unclear; fall then higher ending segment; “Not enough clear voice” |
| 想 xiang3 / 113935518 | T1 .503 | unclear / low | tracker_instability | Unclear; fragmented low branch/recovery; tracker-unstable note |
| 表 biao3 / 113935548 | **T3 .755** | unclear / low | tracker_instability | Unclear; early fall then high branch; tracker-unstable note |
| 纸 zhi3 / 113935556 | T1 .954 | unclear / low | tracker_instability | Unclear; fall then high branch and lower ending; tracker-unstable note |
| 买 mai3 / 113935561 | T4 .859 | unclear / low | tracker_instability | Unclear; large dropout and later high branch; tracker-unstable note |
| 笔 bi3 / 113935564 | T4 .949 | unclear / low | tracker_instability | Unclear; long gap/low branch/return; tracker-unstable note |
| 等 deng3 / 113935570 | T4 .989 | unclear / low | tracker_instability | Unclear; short, conflicting branches; tracker-unstable note |
| 狗 gou3 / 113935580 | T4 .846 | unclear / low | tracker_instability | Unclear; multiple branches including high ending; tracker-unstable note |
| 碗 wan3 / 113935595 | T4 .738 | unclear / low | tracker_instability | Unclear; high interior and low ending branches; tracker-unstable note |

All 12 unclear T3s retain separate display segments; none receives frontend gap bridging or a five-bin primary gesture. `你` alone receives the five-bin gesture. More detail preserves every server-retained frame and the raw measured track, including its late rebound. Expected T3 is a separate teaching shape in the real drawer; the research plot overlays it explicitly as a reference, never as measured data. The plots use full elapsed time; the mobile primary thumbnail fits its own retained/gesture span horizontally.

This is an **acoustic drawer reproduction conditional on whole-clip timing**, not a claim about a live request. Live production requires validated provider timing; that was neither requested nor fabricated. With no accepted timing, live production would not produce these syllable classifications. `五` illustrates the sensitivity: its boundary-tolerant coverage is .4977, just below the fixed .5 gate despite .29 s retained voiced evidence and a .9355 active-core coverage. Its gap also means relaxing that first gate would not establish a reliable dip. This is a research timing limitation to investigate, not authorization to trim or tune.

**10. Why does the listener hear T3 while wav2vec often predicts T4?** The exact explanation remains unknown. Human listeners can combine temporal, register, phonation, segmental, and lexical information; this pass does not isolate their cue weights. Crucially, frozen wav2vec does **not** consume Benma's F0, quality gates, or drawer. V1 extraction difficulties cannot mechanically cause the independent model's errors. Mean pooling eliminates explicit ordering of the final frame vectors, although contextual wav2vec vectors can already encode temporal information. This motivates an ablation; it does not prove that the encoder, pooling operation, or linear head is solely responsible. Speaker distribution shift and the small source-group training corpus remain alternatives.

**11. Which failure explanations are supported?** **D, multiple interacting issues**, with **E for unresolved causal attribution**. A: many selected F0 paths provide unreliable evidence, but true pitch errors versus actual irregular vibration cannot be separated without independent annotation. B: `你` demonstrates a broad-shape/summary mismatch with a valid lexical T3, and `五` exposes sensitivity to supplied timing/coverage. The conservative abstentions are not themselves evidence that loosening thresholds would be correct. C: the frozen representation/pooling/head system empirically fails this speaker's T3s; the specific failing substage is unidentified. Evidence-region deletion and energy gating are not supported as primary causes here. No production thresholds changed.

**12. How do the two correct T3s differ from the eleven misses?** The correct clips are **晚 wan3 (113935472)** and **表 biao3 (113935548)**. Both have an interior measured minimum and a strong apparent later rise, but both have ~18-st branch changes and V1 abstains. They are not two clean textbook controls. `晚` has a low middle branch (minimum 68.9 Hz) and a return to ~171 Hz; `表` has a minimum 156.5 Hz and a high ending ~386 Hz. Their middle→final raw third changes are +11.11 and +11.44 st. For misses the median is −2.07 st, but several misses also recover sharply.

Their active missingness is 3.4% and 7.1% (misses: median 16.7%), retained voiced duration .40 and .26 s (misses .25 s), and recording RMS .0366 and .0427 (misses .0488). They are longer on average but overlap the misses. Their low-confidence voiced fractions are 25.0% and 46.2% (misses median 25.0%): they are **not uniformly less irregular by the available proxies**. Their 1.5 median internal-gap count and 30-ms median total gap duration do not form a strong distinction either. With n=2, quartiles in [t3-correct-vs-wrong.csv](t3-correct-vs-wrong.csv) are interpolations between two observations, not reliable population estimates. Nothing here establishes causality.

**13. Does “collapses in the throat” versus “expelled outward” correspond to measurements?** The descriptions have compatible correlates: T3's active periodicity is lower; active dropouts and abrupt branch changes are more frequent; tracked minima are lower; energy is lower and decays more relative to onset. Median onset/middle/ending RMS is `.109/.096/.046` for T3 versus `.145/.176/.083` for T4. T4 is more middle-peaked in these group summaries. These are **possible correlates of irregular phonation and temporal energy differences**. RMS measures recorded amplitude, not air pressure, force, mouth radiation, glottal closure, or laryngeal location. Different segments, gain, and recording conditions could contribute. The metaphor cannot be converted into a physical mechanism from these measurements.

**14. What should experiment #2 prioritize?** Prioritize **more independent speakers plus a controlled temporal-pooling ablation**, with this now-inspected speaker retained as a known stress case. New evaluation material is needed for fresh generalization claims. Compare explicit temporal summaries against the already-frozen mean-pooling result; do not present reuse of this test set as a pristine test. In parallel, manually annotate a small stratified set of problematic pitch regions and compare an independent/neural F0 system as a diagnostic; agreement alone would not establish truth. Retain periodicity/energy features as exploratory voice-quality proxies, and validate any direct creak measure before relying on it. Add learner recordings before deciding production usefulness. This pass implements none of those experiments.

**15. Exclude any valid T3?** **No.** All source audio hashes match the frozen manifest; all decode; measured clipping is zero. `早`'s low voiced-fraction flag is a tracker/evidence limitation, not evidence of corruption or an incorrect lexical label. The user confirmed valid T3 by listening. Preserve the difficult examples.

**16. Change production now?** **No.** There is evidence for further research, not a validated replacement or threshold adjustment. Production/API/mobile source, model, head, split, labels, and the prior experiment artifacts remain unchanged. Nothing was committed or pushed.
