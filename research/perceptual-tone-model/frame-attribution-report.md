# Frozen frame-level attribution audit

**Decision: REPRESENTATION AND HEAD BOTH CONTRIBUTE. Ownership-selector integration: NOT READY.**

Exactly four previously identified cases were audited. Their frozen embeddings are
temporally heterogeneous, and expanding a uniform mean changes their composition.
The expanded and pilot heads then project those changes differently. The evidence
does **not** establish one generic pooling defect, a preferred span, or a correct
tone. No selector, threshold, pooling implementation, model, F0, grading, UI or
Practice behavior was changed. No recording, fitting, calibration, corpus benchmark,
commit, push or deployment was performed.

The two 这 cases share an early-frame mechanism, but the influential acoustic
material is not identical. 想 adds strong frication; 买 adds a quieter tail. Calling
all these frames either “bad noise” or “legitimate tone evidence” would overstate
the evidence. This is exact attribution of **contextual encoder features to the
head**, not causal attribution of individual waveform samples or perceptual truth.

## Exact inference path and additive mathematics

The inspected path is `ownership_replay.run` → exact persisted contract reuse from
`f0_independent_replay` → `aishell3_embeddings.Encoder.extract(..., "context")` →
`learner_transfer.probabilities` and the pinned sklearn pipelines.

1. Verify the frozen waveform hash. Existing canonicalization resamples the whole
   utterance to 16 kHz with `scipy.signal.resample_poly` if needed, then quantizes to
   PCM16. All four consumed waveforms are the existing canonical recordings.
2. Read the **same original Azure ±250 ms context** for each comparison, using
   nearest-sample `ROUND_HALF_UP` endpoints. Add 200 zero samples on each side.
   Both contexts and input arrays are asserted identical across current/new pools.
3. The installed `Wav2Vec2FeatureExtractor` applies
   `(x - mean(x)) / sqrt(var(x) + 1e-7)` over this padded context. There is no
   attention mask in this single-example path. This waveform normalization is
   nonlinear in audio but **unchanged across the two frame sets**.
4. Frozen `TencentGameMate/chinese-hubert-base`, revision
   `fce0375452b1dd6c080ac3248d423d4d037bc831`; eval mode, gradients disabled,
   deterministic CPU operations, four Torch threads. The model returns 13 hidden
   states, each `[1, T, 768]`; the selected transformer state is **layer 9**.
   T is **36, 37, 42, 49**, respectively. The original cache stacks layer 6/9/12
   pooled vectors into `(3,768)` and the head consumes row 1, layer 9.
5. Conv kernels `[10,3,3,3,3,2,2]`, strides `[5,2,2,2,2,2,2]` imply a 400-sample
   receptive field and 320-sample stride. In padded coordinates the centers are
   `199.5 + 320*j`, with zero-based frame j. If context starts at sample a,
   absolute time is `(a - 200 + 199.5 + 320*j)/16000`.
6. Frame membership is half-open: select centers `>= p` and `< q`, where
   `p,q = round_half_up(pool_seconds*16000) - a + 200`. The production operation
   is `hidden[9][0, mask].mean(0)` in float32. No embedding L2 normalization,
   weighting, attention pooling, or context-vector concatenation follows.
7. Both heads are `SimpleImputer(median, keep_empty_features=True)` →
   `StandardScaler` → balanced multinomial `LogisticRegression(C=.1)`.
   All inspected embeddings are finite; the imputer is an identity here. The
   scaler is fixed affine, not per-example normalization. Each head has its own
   frozen mean μ, scale σ, weights W and intercept b. Its four logits and
   probabilities are

   ```text
   h̄ = (1/N) Σ h_i
   z_c = W_c · ((h̄ - μ)/σ) + b_c
       = b_c + (1/N) Σ [W_c · ((h_i - μ)/σ)]
   P(c) = exp(z_c) / Σ_k exp(z_k); prediction = argmax_c z_c
   ```

**Exact additive frame attribution is possible for logits and margins**, not for
softmax probabilities. We report standardized frame score
`s_ic = W_c·((h_i-μ)/σ)` and contribution `s_ic/N`, with b separate.
The requested raw-embedding form is also saved:
`w_eff=W/σ`, `b_eff=b-w_eff·μ`, `z=b_eff+Σ(w_eff·h_i)/N`.
No SHAP or other approximate explanation framework is involved.

Attribution calculations use float64 over the identical saved float32 frames.
The production Torch mean reproduces **all eight original pooled layer-9 vectors
bit-for-bit**. Float64 mean versus those caches differs by at most **2.710e-7**
per coordinate; reproduced probability vectors differ by at most **1.247e-7**.
This small arithmetic distinction is documented rather than called a model change.
All subset logits are checked against both affine decompositions.

Final reconstruction on persisted vectors covers **344 head/subset comparisons**
and all six class pairs per comparison. Maximum absolute residuals are
**5.3291e-15** for standardized logits, **6.2173e-15** for raw-origin logits,
**6.6614e-15** for pairwise margins, and **1.3323e-15** for reconstructed
logit changes. These concern exact linear accounting; the separate float32-production
versus float64 difference above is larger but negligible.

## Exact frame sets

All indices below are zero-based within their fixed context, not global utterance
indices. Ranges are inclusive; every adjacent center is exactly 20 ms apart.
In **every case the intersection equals the current set and removed frames = ∅**.
The new span is the persisted GAP_AWARE_AZURE span; no selector is rerun or edited.

| Case | Current span (s); duration | New span (s); duration | Current = shared IDs | New IDs | Added IDs | N current→new |
|---|---|---|---|---|---|---|
| take-1 这 | 2.1467–2.2167; 70 ms | 2.0100–2.2200; 210 ms | 20–22 | 13–23 | 13–19, 23 | 3→11 |
| take-2 这 | 2.6670–2.7570; 90 ms | 2.5400–2.7600; 220 ms | 19–23 | 13–23 | 13–18 | 5→11 |
| take-3 想 | 1.5353–1.7553; 220 ms | 1.4300–1.7600; 330 ms | 18–28 | 13–29 | 13–17, 29 | 11→17 |
| take-3 买 | 1.7700–2.0853; 315.3 ms | 1.7700–2.2300; 460 ms | 13–28 | 13–35 | 29–35 | 16→23 |

| Case | Fixed context (s) | Current/shared centers (s, inclusive 20-ms progression) | Added centers (s) |
|---|---|---|---|
| take-1 这 | 1.76–2.47 | 2.15996875, 2.17996875, 2.19996875 | 2.01996875, 2.03996875, 2.05996875, 2.07996875, 2.09996875, 2.11996875, 2.13996875, 2.21996875 |
| take-2 这 | 2.29–3.01 | 2.66996875 through 2.74996875 | 2.54996875, 2.56996875, 2.58996875, 2.60996875, 2.62996875, 2.64996875 |
| take-3 想 | 1.18–2.01 | 1.53996875 through 1.73996875 | 1.43996875, 1.45996875, 1.47996875, 1.49996875, 1.51996875, 1.75996875 |
| take-3 买 | 1.52–2.48 | 1.77996875 through 2.07996875 | 2.09996875, 2.11996875, 2.13996875, 2.15996875, 2.17996875, 2.19996875, 2.21996875 |

Added counts are **8, 6, 6, 7**, respectively. The compact
[per-case summary CSV](data/generated/frame-attribution-v1/per-case-summary.csv)
combines counts, both predictions, top-two gaps, competing pairs, shared/direct/
dilution terms, total margin changes and embedding/output distances for both heads.

`plan-before-inference.json` includes **every context center**, both contracts,
all selected IDs, all five region sets and every prefix/suffix subset. It was
sealed before either head was loaded. Duration of the pooling interval, extent
between selected centers, and N×20-ms cell support are distinct quantities;
the latter two appear separately in the subset tables. Arbitrary subsets can be
discontinuous, so their center extent is not a contiguous owned duration.

## Shared, added and dilution accounting

For any class or pairwise margin, with shared S, added A, removed R, old count n
and new count m:

```text
Δz = (1/m - 1/n) Σ_S s_i + (1/m) Σ_A s_i - (1/n) Σ_R s_i
     shared rescaling        added direct       removed old
```

All four real R sets are empty. Intercepts do not change. In the table, the margin
is **new expanded class minus old expanded class**. The same pair is used for pilot
so orientation is directly comparable; take-1 pilot's own flip is the reverse pair.
All four class components are preserved in JSON/CSV, not just this margin.

| Case/head; pair | Shared / n | Shared / m | Added / m | Dilution Δ | Bias | Old margin→new margin | Total Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| take-1 expanded; T2−T3 | -3.698827 | -1.008771 | +1.056632 | +2.690056 | +.447111 | -3.251716→+.494972 | +3.746688 |
| take-1 pilot; T2−T3 | +1.040344 | +.283730 | -.818214 | -.756614 | +.247658 | +1.288002→-.286826 | -1.574828 |
| take-2 expanded; T4−T3 | -3.499693 | -1.590770 | +1.237521 | +1.908924 | +1.175634 | -2.324060→+.822385 | +3.146445 |
| take-2 pilot; T4−T3 | -.901450 | -.409750 | -.880896 | +.491700 | +.532189 | -.369260→-.758457 | -.389196 |
| take-3 想 expanded; T2−T3 | -.782951 | -.506616 | +.446784 | +.276336 | +.447111 | -.335840→+.387280 | +.723120 |
| take-3 想 pilot; T2−T3 | -1.776007 | -1.149181 | +.298672 | +.626826 | +.247658 | -1.528349→-.602851 | +.925498 |
| take-3 买 expanded; T2−T3 | -1.515406 | -1.054196 | +.969492 | +.461211 | +.447111 | -1.068295→+.362408 | +1.430702 |
| take-3 买 pilot; T2−T3 | -2.428975 | -1.689722 | -.690120 | +.739253 | +.247658 | -2.181317→-2.132184 | +.049133 |

Relative to the frozen **training-mean reference**, dilution supplies 71.8%, 60.7%,
38.2% and 32.2% of the expanded pair-margin changes. Nevertheless, setting all
added standardized scores to zero leaves expanded competing-pair margins
**−.561660, −.415136, −.059504, −.607084**. Thus dilution alone does **not** give
any of the observed destination-class victories. On take-1 this hypothetical
neutral-addition vector makes T4 top rather than T2; multiclass effects matter.

“Direct versus dilution” is reference-dependent. Under raw hidden-vector zero,
the corresponding direct/dilution terms are `.380617/3.366072`,
`.752376/2.394069`, `.118718/.604402`, `.686594/.744108`; total Δ is identical.
These percentages are therefore **not causal fractions of acoustic information**.
The invariant result is that the added frames differ from the old mean along the
head's discriminant. The standardized-zero counterfactual is an algebraic diagnostic,
not a realizable waveform or an implemented pooling candidate.

Approximate classifications **only under the training-mean reference**:

| Case | Direct / dilution share of expanded margin change | Classification | Interpretation |
|---|---|---|---|
| take-1 这 | 28.2% / 71.8% | DILUTION_DOMINANT | Active added T2 evidence is still needed for the observed T2 victory. |
| take-2 这 | 39.3% / 60.7% | DILUTION_DOMINANT | Strong peripheral T4 projections accompany the larger rescaling term. |
| take-3 想 | 61.8% / 38.2% | MIXED | Frication supplies direct T2 evidence; dilution is substantial. |
| take-3 买 | 67.8% / 32.2% | DIRECT_ADDED_EVIDENCE_DOMINANT | Every added tail frame projects toward expanded T2; dilution assists. |

These are descriptive labels, not fitted cutoffs. None is a pure neutral-filler case.

## Per-case mechanism and acoustic evidence

Waveform, spectrogram, old/new centers, Azure owner and immediate neighbors,
per-frame margins, existing energy/ZCR and saved F0 are aligned in each timeline.
Spectral diagnostics come from the previous experiment's 20-ms windows/5-ms hop;
saved RMS/F0 use their original timestamps. Numeric frame diagnostics join to
the nearest acoustic timestamp **for interpretation only**, recording both times.
No F0 was computed or used for frame selection. The two 这 units retain
“unavailable” pitch eligibility despite a few saved measurements.

### take-1 这: early material changes both heads, in opposite directions

Expanded changes **T3→T2**; pilot changes **T2→T3**. The seven recovered early
frames 13–19 are sufficient: shared+early gives expanded T2 margin **+.756574**;
the final frame 23 alone leaves T3 at **−2.969049**. The added tail actually
opposes the T2 flip. Earliest frames **13,14,15** contribute **+1.037070** at the
new denominator, almost the entire net added contribution +1.056632. Frame 15
(2.05996875 s) is strongest, score **+6.9497**, contribution **+.6318**.

Frames 13–14 are lower-amplitude leading material (RMS 8.04–8.56× the saved gate,
20-ms energy −32.9/−31.6 dBFS), before the clear frication in frames 16–18
(high-band fraction .656–.846). Frame 15 bridges into the onset. The early frames
are inside Azure ownership; some resemble surrounding low-level background in this
recording. The evidence supports **pre-vowel/peripheral and onset-transition
sensitivity**, not proof that each frame belongs to a tone-bearing nucleus or is
random noise. The late voiced body supplies the old T3 preference for expanded.

Removing the earliest positional region gives expanded T3, margin **−.913051**.
Removing the central region gives T4, demonstrating additional multiclass
competition. Expanded top-two gaps are only **.277811→.261083** even though its
T2−T3 change is large. Pilot interprets the early body oppositely: early-only
addition yields T3; its margin T2−T3 changes +1.288002→−.286826.

Classification: **A PERIPHERAL_FRAME_DOMINANCE, B ONSET_SENSITIVITY,
D MEAN_POOL_DILUTION, F LOW_CLASS_MARGIN_INSTABILITY**. Noise versus legitimate
pre-onset material is inconclusive. This case is not evidence for pilot stability.

### take-2 这: below-gate leading frames dominate the expanded head

Expanded changes **T3→T4**; pilot remains **T3**. All six additions are early,
13–18. Frames **13 and 14**, at 2.54996875 and 2.56996875 s, have expanded T4−T3
scores **+8.7586 and +5.5229**. Their direct contribution is **+1.298322**,
larger than all six additions' net +1.237521. They lie in low-energy material
before the visible frication: saved RMS **.31/.35× gate**, 20-ms energy
**−56.0/−54.7 dBFS**. Frame 15 is the onset transition; frames 16–18 have
high-band fractions .820–.885 and substantially weaker or negative T4−T3 scores.

The 10-frame suffix excluding frame 13 is T3 at **−.088803**; adding frame 13
makes T4 at **+.822385**. This is an exact single-frame completion flip, not
a claim that other frames have no influence. Removing the whole earliest region
(13–15) yields T3 at **−1.288170**. The old expanded gap **2.324060** was not
small; this is a substantial representation shift, not merely a pre-existing tie.

Pilot's added aggregate favors T3 (direct **−.880896**), overcoming its positive
dilution term. Its T4−T3 margin becomes more negative, **−.369260→−.758457**.
The first two pilot prefixes do predict T4; stability of the complete span does
not mean every pilot subspan is stable.

Classification: **A PERIPHERAL_FRAME_DOMINANCE, D MEAN_POOL_DILUTION**;
**B ONSET_SENSITIVITY** in the temporal/pre-onset sense. The dominant frames
are not convincing local tone-bearing material. Their contextual encoder vectors
can still carry neighboring/whole-context information. **G context contamination
is unproven**, because context was held fixed, not ablated.

### Do the two 这 cases share a mechanism?

**Yes at the structural level:** full pooling recovers an early, pre-vowel region
whose expanded discriminant projection differs sharply from the small late pool;
the earliest three-frame ablation reverses both expanded flips. Both also have
large dilution terms. **No at the level of identical acoustics or head response:**
take-2's decisive pair is below-gate pre-frication material, whereas take-1 has
background/onset-transition support above the gate; their destination classes
differ, and pilot flips only on take-1. A common phonetic or noise diagnosis is
not established.

### take-3 想: strong frication meets a small expanded margin

Expanded changes **T3→T2**; pilot stays **T1**. Added early frames 13–17 occupy
1.43996875–1.51996875 s. Frames 13–16 have high energy (55.6–84.0× saved gate)
and high ZCR .458–.539, with high-band fraction .454–.669: strong fricative-like
speech onset, not low-energy filler. Frame 17 transitions toward the voiced body.
The exact phonetic boundary is not annotated. These are legitimate syllable-onset
candidates, but not direct evidence of a particular perceived tone.

Expanded positive scores occur at 13,14,16,17 and also **shared central frame 23**
(1.63996875 s, score +3.6672). Several central and most late frames oppose T2.
Shared+early gives T2 at **+.561836**. Added final frame 29 has score **−2.8527**;
shared+tail instead gives T3 at **−.508322**. Removing earliest frames 13–16 gives
T3 at **−.135920**. The initial/final expanded top-two margins are
**.335840/.387280**; a modest shift is sufficient.

This establishes **heterogeneous model projections** within the syllable, not
genuine heterogeneous tone perception. The available F0 begins in the later body
and does not validate the early frames' T2 projection. Pilot's T2−T3 margin moves
**more** than expanded's (.925498 versus .723120), but T1 remains the winner,
with top-two gaps **2.398117→1.799682**. This is especially clear evidence that
argmax stability alone is not a measure of feature sensitivity or quality.

Classification: **B ONSET_SENSITIVITY, D MEAN_POOL_DILUTION,
F LOW_CLASS_MARGIN_INSTABILITY**. **E** applies only to internally heterogeneous
*model evidence*; the stronger claim about acoustic tone evidence is **J INCONCLUSIVE**.

### take-3 买: sustained added-tail projection, not one outlier

Expanded changes **T3→T2**; pilot remains **T3**. All seven added tail frames,
29–35 at 2.09996875–2.21996875 s, have positive expanded T2−T3 scores
**[2.5151, 2.6937, 2.6882, 2.6177, 4.7175, 4.8831, 2.1831]**. Together they add
**+.969492**, with +.461211 from shared dilution. The corresponding pilot scores
are **all negative**; its added contribution −.690120 nearly cancels dilution
+.739253. Pilot's full margin changes only +.049133.

The tail is quieter than the body: RMS 8.61–11.16× the existing gate, 20-ms energy
−28.8 to −32.3 dBFS, increased ZCR .169–.266, and no retained selected F0 there.
It lies within the Azure owner and before the following owner starts at 2.26 s.
The waveform/spectrum support a decaying/noisier tail, but do not establish
whether it carries useful perceptual coda information or only background.
Absence of selected F0 is not a rejection criterion.

The current pool already has a positive central run (frames 22–26) between
strongly negative early frames and mixed late frames. Removing the **central**
region also restores T3 (margin −.635562); removing late or final regions gives
T3 at −.182716 / −.413393. Thus this is not solely one anomalous outermost frame.
The prefix gradually crosses at **21 frames**, when frame 33 at 2.17996875 s is
added (margin +.017853). Tail evidence and averaging both matter.

Classification: **C CODA_TAIL_SENSITIVITY** (temporal tail, not an asserted phone),
**D MEAN_POOL_DILUTION**. There is heterogeneous model evidence in the body;
its status as actual heterogeneous tone evidence is **J INCONCLUSIVE**.

For comparison only, existing ownership results show take-1 买 stays T2/T2
(expanded TV .123683; pilot .237029); Google 买 becomes usable T3/T3 but has no
usable current comparison; take-2 买 remains abstained for ownership ambiguity.
Those saved summaries do not establish the frame mechanisms in those cases.
No extra frame extraction or inference was performed on them.

## Shared-versus-added counterfactuals

Pairs/margins retain the expanded old→new orientation. Shared+all is exactly the
new pool, not a separate representation. Empty early/late additions leave shared
unchanged; those duplicates are retained transparently in the data.

| Case | Shared expanded | Shared+early expanded | Shared+late expanded | Shared+all expanded | Pilot shared→early / late / all |
|---|---|---|---|---|---|
| take-1 这 | T3 −3.251716 | T2 +.756574 | T3 −2.969049 | T2 +.494972 | T2→T3 / T2 / T3 |
| take-2 这 | T3 −2.324060 | T4 +.822385 | T3 −2.324060 | T4 +.822385 | T3→T3 / T3 / T3 |
| take-3 想 | T3 −.335840 | T2 +.561836 | T3 −.508322 | T2 +.387280 | T1→T1 / T1 / T1 |
| take-3 买 | T3 −1.068295 | T3 −1.068295 | T2 +.362408 | T2 +.362408 | T3→T3 / T3 / T3 |

Five neutral positional regions are `numpy.array_split(sorted_new_ids, 5)`:
earliest, early, central, late, final. Each is omitted once, and the remaining
frames are re-mean-pooled through the same head. These are diagnostic ablations,
not proposed valid production spans or acoustic phone labels. Every resulting
four-class probability vector, argmax, TV, margin and frame set is recorded in
the [numerical appendix](data/generated/frame-attribution-v1/numerical-appendix.md)
and per-head `*-subsets.csv`. No preferred region is selected from these outputs.

## Prefix/suffix stability

Every prefix/suffix from 1 through N frames was fixed before loading the heads.
Sub-minimum-duration subsets are allowed here **only as diagnostics**. Center-out
was unnecessary: the directional curves and region ablations isolate the effects.

| Case | Expanded prefix | Expanded suffix | Pilot |
|---|---|---|---|
| take-1 这 | T2 for all 1–11 | T3 at 1–8, T4 at 9–10, T2 at 11 | Prefix T1 at 1 then T3; suffix T2 at 1–7 then T3 |
| take-2 这 | T4 at 1–2, T2 at 3, T1 at 4, T4 at 5–11 | T3 at 1–10, T4 at 11; earliest frame completes flip | Prefix T4 at 1–2 then T3; short suffixes vary, full is T3 |
| take-3 想 | T2 for all 1–17 | T3 at 1–15, T2 at 16–17 | Prefix T4 at 1, T2 at 2–7, T1 at 8–17; all suffixes T1 |
| take-3 买 | T3 at 1–20, T2 at 21–23 | T1 at 1, T2 at 2–23 | Every prefix and suffix T3 |

For the expanded destination class to overtake the old class while accumulating
from the tail toward the onset, the first counts are **9, 11, 16** for take-1 这,
take-2 这 and take-3 想. Take-1's destination T2 overtakes T3 at 9 frames but
only becomes the overall winner at 11 because T4 intervenes. For take-3 买,
the relevant forward prefix first crosses at **21** frames. Take-2 shows a sudden
last-frame completion; take-1 and 想 accumulate early evidence over multiple frames;
买 changes gradually over its tail. Removing all additions returns the exact current
set and prediction in all four cases, for both heads.

The curves rule out a universal “single peripheral outlier” account. 买 changes
gradually over a long tail, 想 separates a fricative onset from a stronger pilot
T1 body, and 这 contains early-vs-late opposition with additional multiclass effects.

## Embedding geometry and head comparison

| Case | Cosine distance old/new | L2 distance | Expanded old→new top-two logit gap | Pilot old→new top-two logit gap |
|---|---:|---:|---:|---:|
| take-1 这 | .255060 | 4.631723 | .277811→.261083 | 1.288002→.286826 |
| take-2 这 | .220327 | 4.087846 | 2.324060→.822385 | .369260→.758457 |
| take-3 想 | .086570 | 2.219626 | .335840→.387280 | 2.398117→1.799682 |
| take-3 买 | .088957 | 2.082798 | 1.068295→.362408 | 2.181317→2.132184 |

| Case | Pooled cosine similarity | Expanded probability TV | Pilot probability TV | Movement interpretation |
|---|---:|---:|---:|---|
| take-1 这 | .744940 | .334372 | .349412 | Large composition change plus a small multiclass gap. |
| take-2 这 | .779673 | .651128 | .102219 | Large composition change; old expanded gap was 2.324, not near a tie. |
| take-3 想 | .913430 | .191896 | .114460 | Smaller movement crosses the low expanded starting gap .336. |
| take-3 买 | .911043 | .334244 | .045452 | Smaller movement than 这, but sustained tail projection overcomes a 1.068 gap. |

“Smaller” compares these four cases; it is not a calibrated embedding-distance
threshold. Pilot moves opposite expanded in the common competing pair for both 这
cases. Both move positively in that pair for 想 and 买, but 买 pilot's net change
is only .049 despite opposite-signed added evidence. Starting margins and effective
weight orientation both matter; native training quality is not inferred.

Individual frame-to-current/new cosine similarities are in both `*-frames.csv`
files. Ranges to current are .091–.980, .010–.943, .223–.742 and −.158–.863;
to new they are .559–.723, .447–.755, .497–.640 and −.174–.811. Mean pooling
changes the mixture substantially, particularly in the three-/five-frame 这
references. This is not an inference-code mismatch or new encoding of a shifted
context.

On the common raw embedding coordinates, expanded pair-weight norms are
**33.1702** for T2−T3 and **31.5821** for T4−T3; pilot norms are **13.7634** and
**13.5778**. Cross-head cosines for these effective directions are only
**.325880 / .385214**. Scalers and classifier weights both contribute to these
effective directions. The delta-vector alignment and resulting signed changes are:

| Case | Expanded cos(Δembedding, pair weight) | Pilot cosine | Expanded Δmargin | Pilot Δmargin |
|---|---:|---:|---:|---:|
| take-1 这 | +.024387 | −.024704 | +3.746688 | −1.574828 |
| take-2 这 | +.024372 | −.007012 | +3.146445 | −.389196 |
| take-3 想 | +.009822 | +.030295 | +.723120 | +.925498 |
| take-3 买 | +.020709 | +.001714 | +1.430702 | +.049133 |

The identity `Δmargin = ||Δembedding|| ||w_pair|| cos(angle)` accounts for these
changes. Larger expanded weight norm alone is not the whole explanation: orientation,
intercept and which class leads also matter. Pilot stability on 想 comes from a
different leading family and larger top-two margin, not a smaller T2−T3 movement.
Pilot's protection on 买 and take-2 这 comes from different projections of added
frames. Stability does not establish pilot accuracy or superiority.

Different training distributions are plausible causes of the learned geometry,
but this audit does not isolate their causal role. No training-distribution,
calibration or perceptual-truth claim follows from four unlabeled inference cases.

## Synthesis, decision and one next offline experiment

There is a shared **algebraic** mechanism: temporally different features change a
uniform mean; direct projection and denominator rescaling both change margins.
That identity alone cannot establish a pooling defect. The acoustic triggers have
three forms: early peripheral/onset-transition material in 这, strong onset
frication in 想, and a quieter tail in 买. Internal body projections also matter.
Head geometry determines whether these movements reverse, reinforce or leave the
leading class unchanged. A two-mechanism or one-bad-edge story would hide evidence.

**REPRESENTATION AND HEAD BOTH CONTRIBUTE.** This identifies how the four flips
occur, while leaving the perceptual legitimacy and training-distribution origin
of some influential features unresolved. Context contamination is possible because
layer-9 frames are contextual, but not demonstrated. Frame rounding is reproduced
exactly; none of the flips is explained by a changed context origin or convolution
grid. The ordinary center-only ownership rule can include a frame whose 25-ms
convolutional footprint crosses an Azure edge; transformer context is wider still.
No alternative grid/context was tested, so **H ENCODER_FRAME_BOUNDARY_EFFECT** is
not established as a causal mechanism.

**One next experiment: a preregistered acoustic pooling-representation comparison.**
Test exactly three deterministic representations over the unchanged safe owner:

1. Uniform mean over every owned frame (the existing control).
2. Central-half mean, retaining sorted frame positions `floor(N/4)` through
   `ceil(3*N/4)-1`, fixed in advance as a positional control rather than a presumed
   correct nucleus.
3. Acoustic energy/low-band weighted mean: at each owned frame center use the
   nearest existing 20-ms acoustic diagnostic and set
   `weight_i = rms_20ms_i * (1 - high_band_fraction_i)`, using the already defined
   3400-Hz high-band boundary. Normalize these nonnegative weights to sum to one;
   if their sum is zero, report unavailable. Missing diagnostics fail closed.
   This is a **sonority proxy hypothesis**, not a validated tone-bearing detector.

Seal all frame sets and weights before running either head. Use no F0, target,
expected tone, classifier output, parameter search, or desired prediction in
construction. The energy factor tests quiet-tail influence; the low-band factor
tests frication influence. The central control tests whether position alone explains
anything and can fail on the observed central positive evidence in 买. No candidate
is declared correct or selected for integration by prediction agreement.

Evaluate the same four frozen physical recordings plus a small, fixed cohort of
existing native held-out clips, selected from archived acoustic/segment metadata
before inspecting model outputs to cover onset and tail structures. No new audio
collection. Freeze the cohort IDs and existing ownership/context before extraction;
reuse saved embeddings where present. Report embedding displacement, frame-weight
concentration, both heads' signed margins/TV, and sensitivity across the same
predeclared temporal ablations. Acoustic review should check whether the weighting
preserves plausible syllable body/support without seeing tone predictions. Compare
native and physical behavior descriptively, without expected-tone accuracy ranking.

This single experiment tests representation rationale across the three acoustic
patterns while exposing head-specific disagreement. It does not assume the old
F0-defined pool is correct. The present evidence warrants this bounded comparison;
it does not warrant one universal correction. No candidate is implemented in this
audit. **READY for this focused offline representation experiment; NOT READY for
ownership-selector integration.** Retraining and calibration remain later decisions.

## Reproduction, tests and freeze

The previous caches contained `(3,768)` pooled vectors, not frame tensors. Four
fixed contexts were therefore encoded once each; full layer-9 tensors are persisted
as `layer9.npy` for all subsequent calculations/tests. There was no all-20 replay.
The existing encoder implementation, processor and head code were used unchanged.

Commands from repository root (output folder must be new for `seal`/`run`; they
fail rather than overwrite existing numerical results):

```sh
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m perceptual_tone.frame_attribution seal
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m perceptual_tone.frame_attribution run
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p test_frame_attribution.py -v
MPLCONFIGDIR=/tmp/frame-attribution-mpl PYTHONPATH=/tmp/ownership-plotting benchmark/pronunciation_v2/.venv/bin/python research/perceptual-tone-model/scripts/frame_attribution_figures.py
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m perceptual_tone.frame_attribution verify
```

Plotting uses the already available `/tmp/ownership-plotting` Matplotlib environment,
separate from frozen inference; no project dependency changes. Figures are PNG/PDF,
not generated illustrations. All four timelines and stability figures were inspected.

**11 focused research tests pass**, covering exact four-case membership and
frame reconstruction, half-open membership, affine/raw contribution sums across
all subsets, a removed-frame synthetic accounting case, deterministic ablations,
label/pitch/prediction metadata independence, rejection of nonfinite embeddings,
frozen model/tensor integrity and original-output reproduction. No pre-existing
historical test is altered or suppressed; no unrelated suite or benchmark rerun.

The starting-state scoped freeze verifies **1,642 files unchanged**. It includes
existing tracked files, research sources/reports, both preceding experiments and
caches, inherited consumed audio and lock-listed files. It also seals this audit's
inference source before extraction. It is not a new full-corpus audit. HEAD and
the pre-existing untracked ownership/F0-independent work remain unchanged.
Expanded model SHA-256:
`b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b`;
pilot:
`c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9`.
All three encoder-file hashes match `configs/dev-learned-lock.json`.

## Additive artifacts and files changed

- [Complete machine-readable results](data/generated/frame-attribution-v1/results.json).
- [Numerical appendix: all frames, subsets, ablations and curves](data/generated/frame-attribution-v1/numerical-appendix.md).
- [Compact per-case summary](data/generated/frame-attribution-v1/per-case-summary.csv).
- [Exact reconstruction residuals](data/generated/frame-attribution-v1/reconstruction-verification.json).
- [Expanded/pilot comparison CSV](data/generated/frame-attribution-v1/comparison.csv).
- [Acoustic frame diagnostics](data/generated/frame-attribution-v1/acoustic-frame-diagnostics.csv).
- Per-case folders `take-1-3/`, `take-2-3/`, `take-3-1/`, `take-3-2/`: `layer9.npy`,
  `encoder.json`, `results.json`, both `*-frames.csv` and `*-subsets.csv`,
  `timeline.png/pdf`, `stability.png/pdf`.
- `freeze-before.json`, `plan-before-inference.json`, `freeze-verification.json`,
  `freeze-final-verification.json`, `artifact-manifest.json`, inference/test/plot logs.

New source/report files only:

- `perceptual_tone/frame_attribution.py`
- `scripts/frame_attribution_figures.py`
- `tests/test_frame_attribution.py`
- `frame-attribution-report.md`

Generated data stays under the existing ignored-data policy. Earlier experiment
artifacts are preserved. **NOT READY for ownership-selector integration.**
