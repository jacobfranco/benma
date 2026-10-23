# Pooling blocker audit: native RIGHT concentration and natural learner disagreement

**TWO_BLOCKERS. Head-only refit justified: NO. Acoustic pooling integration: NOT READY.**

The native blocker is concentrated dependence on heterogeneous final-frame evidence, interacting with head margin geometry. The worst frame supports the correct native label; deleting it causes a confident expanded prediction to become wrong. Concentration increases sensitivity but does not identify inherently bad evidence. The learner blocker remains unresolved head disagreement without reliable independent realization evidence. These blockers do not exhibit a clear common concentration mechanism in this sample. “Two blockers” is an operational diagnosis, not proof of statistical independence or proof that either learner head is wrong.

The established **PROMISING_NOT_READY** result is preserved: acoustic BASE accuracy remains 91.35% for both frozen heads on 659 native items, with the previously reported recognition and average stability advantages. This audit does not reopen general effectiveness. The acoustic formula, encoder, heads, ownership, admissibility rules, grading and UI are unchanged. No inference replay, pooling reconstruction, training, tuning, integration, new recordings, commit, push or deployment occurred. Detailed linear attribution reads cached frame scores/frames and sealed logits; it is not a confirmatory replay.

## Fixed selection and chronology

Selection used only already-sealed confirmatory outputs: the union of every acoustic RIGHT argmax flip in either head, the top three RIGHT TVs per head, and the top three removed-frame weight shares, with ID tie breaks. This produces **22 unique native audit cases**, including **21 distinct flipping items**. The 22nd is a stable high-concentration case. No flip was discarded to satisfy an arbitrary 20-case cap.

**22 unique native controls** were fixed before contributions: both heads correct at BASE and after RIGHT, each RIGHT TV ≤0.02; match lexicographically on same native tone, nearest frame count, support duration, effective_n, then ID. All matches share the native tone. This is a descriptive selection rule, not a safety threshold. The 7 natural learner disagreements and 7 unique agreement controls were likewise fixed before interpretation, matching geometry without learner expected tone or grade. There are only seven eligible agreement controls, so matching uses all seven and cannot produce close matches for every case; per-match differences are saved. Unit IDs are zero-based IDs from the frozen artifacts.

The sets are preserved in `selection.json`, with SHA-256 **`5c4ac1ad525691648044362cecba32495acace05165b9536819ffdef23aabe6e`** bound by `audit-preregistration.json`. The initial seal's freeze inventory contains 3,106 pre-existing files. The finish phase did not reselect, replay inference, rebuild representations, or repeat a full freeze scan.

Native audit ID | Matched stable control | Selection reasons
--- | --- | ---
aishell3:SSB02870075:14 | aishell3:SSB04070044:17 | any_head_RIGHT_flip
aishell3:SSB02870078:19 | aishell3:SSB07860058:1 | any_head_RIGHT_flip
aishell3:SSB02880104:17 | aishell3:SSB02870075:17 | any_head_RIGHT_flip
aishell3:SSB02880113:12 | aishell3:SSB03540048:10 | any_head_RIGHT_flip
aishell3:SSB02880113:20 | aishell3:SSB02880113:5 | any_head_RIGHT_flip
aishell3:SSB03540009:15 | aishell3:SSB07860041:18 | any_head_RIGHT_flip
aishell3:SSB03540048:0 | aishell3:SSB04070025:18 | any_head_RIGHT_flip, top3_expanded_tv, top3_removed_weight_share
aishell3:SSB03540048:1 | aishell3:SSB06030046:4 | any_head_RIGHT_flip
aishell3:SSB03800054:0 | aishell3:SSB07940081:10 | top3_removed_weight_share
aishell3:SSB03800054:6 | aishell3:SSB03800054:11 | any_head_RIGHT_flip, top3_pilot_tv
aishell3:SSB03800084:10 | aishell3:SSB04070030:10 | any_head_RIGHT_flip
aishell3:SSB04070025:17 | aishell3:SSB06030046:2 | any_head_RIGHT_flip
aishell3:SSB04070025:5 | aishell3:SSB05340079:7 | any_head_RIGHT_flip, top3_pilot_tv, top3_removed_weight_share
aishell3:SSB04070030:18 | aishell3:SSB07860058:10 | any_head_RIGHT_flip, top3_expanded_tv
aishell3:SSB04070030:7 | aishell3:SSB06030100:9 | any_head_RIGHT_flip
aishell3:SSB04070044:11 | aishell3:SSB07940081:5 | any_head_RIGHT_flip
aishell3:SSB05900057:1 | aishell3:SSB05900057:2 | any_head_RIGHT_flip
aishell3:SSB06030046:3 | aishell3:SSB07840051:17 | any_head_RIGHT_flip, top3_expanded_tv
aishell3:SSB06030100:21 | aishell3:SSB03540048:5 | any_head_RIGHT_flip, top3_pilot_tv
aishell3:SSB07840015:17 | aishell3:SSB03800084:5 | any_head_RIGHT_flip
aishell3:SSB07840031:7 | aishell3:SSB02880113:7 | any_head_RIGHT_flip
aishell3:SSB07860058:5 | aishell3:SSB04070025:3 | any_head_RIGHT_flip

## Exact RIGHT deletion: worst case and counterexample

At the frozen head's standardized training-mean origin, let `s_i` be its four-class frame scores, `b` its intercept, `w` the final normalized frame weight, and `z_R` the contracted logits:

`z_BASE = b + sum_i w_i s_i`

`z_RIGHT - z_BASE = -w*s_last + w*(z_RIGHT-b)`.

The two terms are direct removal and renormalization, respectively. Bias is retained once. Their separation depends on the chosen origin; the total logit/margin change is invariant. Both standardized-origin and raw-origin decompositions are saved. These are exact linear identities, not post-hoc importance scores or a causal phonetic localization of contextual HuBERT features.

Worst item **aishell3:SSB03540048:0**, native **T3**: expanded **T3→T2**, TV **0.83816192**, versus uniform **0.17959682**. Pilot remains **T3→T3**, TV **0.09497124**. The removed frame carries **42.2306%** of acoustic weight, with **6 frames / 119.96875 ms** remaining. effective_n changes **3.75915→3.80644**: it increases slightly even though expanded fails catastrophically. A scalar minimum-effective_n explanation is inadequate.

The frame center is **0.39996875 s**, at relative owner position **0.9997596** within `[0.27,0.40)`. Its mapped acoustic timestamp is 0.400 s, raw weight 0.04889727, RMS 0.04890185, and high-band fraction 0.000093615. The three preceding normalized weights are 0.08724466, 0.14830392 and 0.19466803; the last quarter of the owner contains 61.6974% of the weight.

Head | BASE p-margin / logit margin | Removed class contributions [T1,T2,T3,T4] | Removed T3−T2 contribution | Renormalization T3−T2 delta | T3−T2 before→after
--- | --- | --- | --- | --- | ---
expanded | 0.7179 / 2.1847 | [1.3093, -1.8723, 2.2668, -1.7038] | 4.1391 | -1.1019 | 2.1847 → -3.0562
pilot | 0.9308 / 3.3508 | [-1.2958, 0.1813, 2.5185, -1.4039] | 2.3371 | 0.9220 | 3.3508 → 1.9357

For expanded, direct removal reduces the T3−T2 margin by **4.13908782**, and renormalization reduces it by another **1.10185471**: **+2.18469347→−3.05624906**. Direct removal alone crosses zero (−1.95439); renormalization alone does not (+1.08284). Classification: **DIRECT_FRAME_EVIDENCE + RENORMALIZATION**, dominated by direct removal, **not LOW_MARGIN**. It destroys evidence supporting the known correct class. Pilot loses 2.33713289 directly but recovers 0.92203649 through renormalization, retaining a positive 1.93567922 margin.

A presealed high-weight counterexample is **aishell3:SSB03800054:0**, also native T3. Its final weight is **41.3047%**, with effective_n **3.15064** and only **4 frames / 80 ms** remaining. Both heads stay correct T3. Expanded TV is **0.00445178** and pilot TV **0.04333108**. Expanded margin **5.84879→5.44763** combines direct removal **−2.83597** with renormalization **+2.43480**. Pilot margin **4.72319→2.96270** combines **−3.08652 +1.32603**. Similar concentration, fewer remaining frames and lower effective_n do not cause the same failure. This item was already included by the top-weight rule; it was not added to the matched controls after attribution.

The standardized-origin frame contributions and exact decomposition are available for **all 44 fixed native items × both heads**. Maximum BASE/RIGHT logit reconstruction error is **5.329e-15**; maximum pair-margin decomposition residual is **1.332e-15**. Reconstruction uses the saved contribution scores, never model inference.

## Lightweight acoustics and limits of phonetic interpretation

`native-acoustic-diagnostics.json/csv` and 44 standalone SVGs in `acoustic-diagnostics/` inspect frozen PCM waveforms and 20-ms Hann spectra for every fixed native item. Recomputed window RMS and high-band fraction match their sealed values within 1e-14; these diagnostic spectra do not rebuild weights or pooled representations. Final-frame and neighboring weights, timestamps, normalized/raw weights and before/after support are in `right-edge-contributions.json/csv`.

The worst frame's spectrum is dominated by low frequencies: 99.653% below 1 kHz, spectral centroid 247.1 Hz, flatness 0.000407. The stable 41.30% case has RMS 0.04031, high-band fraction 0.002533, centroid 984.7 Hz and flatness 0.001144. Neither is a high-band-frication-dominated final window. The worst acoustic window `[0.39,0.41]` extends 10 ms beyond the frozen owner end; centered acoustic analysis and contextual encoder frames do not localize all evidence strictly within the nominal owner. This is recorded, without changing ownership or clipping.

Native F0 and autocorrelation strength are unavailable in the consumed native artifacts and were not extracted. Low-band energy and native-label-aligned head evidence do not prove periodic voicing, a particular contour, or a coda/tail identity. The audit identifies a mathematical deletion mechanism; it cannot establish that the frame is purely legitimate final tone material rather than context/boundary mixture. No blanket “bad tail” claim is supported.

## Concentration, effective support and margins across all 659

The following weight bins were fixed before detailed attribution. Every row is a descriptive slice of the same 659 native items; no boundaries were optimized and none is proposed as a production threshold. TV is half L1 probability distance. Margins below are BASE top-two probability margins.

Head | Removed weight bin | n | Flips / rate | Mean / median TV | BASE / RIGHT accuracy | Mean p-margin
--- | --- | --- | --- | --- | --- | ---
expanded | [0,5)% | 191 | 1 / 0.52% | 0.0026 / 0.0003 | 92.67% / 92.15% | 0.9128
expanded | [5,10)% | 247 | 1 / 0.40% | 0.0130 / 0.0011 | 92.31% / 91.90% | 0.8860
expanded | [10,20)% | 184 | 6 / 3.26% | 0.0300 / 0.0030 | 90.22% / 91.85% | 0.8705
expanded | [20,30)% | 30 | 4 / 13.33% | 0.0962 / 0.0153 | 86.67% / 73.33% | 0.7654
expanded | [30,40)% | 5 | 1 / 20.00% | 0.1505 / 0.1393 | 60.00% / 40.00% | 0.4573
expanded | [40,100]% | 2 | 1 / 50.00% | 0.4213 / 0.4213 | 100.00% / 50.00% | 0.8556
pilot | [0,5)% | 191 | 0 / 0.00% | 0.0049 / 0.0017 | 92.67% / 92.67% | 0.7954
pilot | [5,10)% | 247 | 2 / 0.81% | 0.0139 / 0.0073 | 95.14% / 94.33% | 0.8024
pilot | [10,20)% | 184 | 3 / 1.63% | 0.0257 / 0.0133 | 86.41% / 86.96% | 0.7739
pilot | [20,30)% | 30 | 0 / 0.00% | 0.0512 / 0.0281 | 86.67% / 86.67% | 0.7887
pilot | [30,40)% | 5 | 2 / 40.00% | 0.1696 / 0.1352 | 60.00% / 60.00% | 0.4914
pilot | [40,100]% | 2 | 0 / 0.00% | 0.0692 / 0.0692 | 100.00% / 100.00% | 0.9562

The top decile of removed weights (66 items, observed boundary 0.1701078, **descriptive only**) contains **9/14 expanded flips** and **4/7 pilot flips**. Flip rates are **13.64% versus 0.84%** for expanded and **6.06% versus 0.51%** for pilot, compared with the other 593. Mean TV is **0.08687 versus 0.01342** expanded and **0.05835 versus 0.01308** pilot. BASE errors are **12/66 versus 45/593** and **11/66 versus 46/593**. Thus higher concentration is disproportionately associated with instability and errors, but most high-concentration items are still correct.

Of these same 66 high-weight items, **37 expanded** and **22 pilot** are correct, have no flip, and TV≤0.02. Those stable-correct groups have mean BASE probability margins **0.9768 / 0.9453**, versus **0.3593 / 0.1520** among high-weight flips. The spectral and support measurements overlap; the data do not isolate a universal acoustic pathology. `high-weight-stable-vs-flip` provides all IDs, class-margin effects, RMS, high-band fractions, remaining frames and durations. This whole-population descriptive slice does not alter the fixed case/control set.

**High weight alone is insufficient as a safety rule.** Large final weights can retain useful correct-class evidence. No cap, weight blend, trimming rule or effective_n threshold follows from this audit.

Feature | Expanded ρ(TV) | Pilot ρ(TV) | Expanded ρ(flip) | Pilot ρ(flip)
--- | --- | --- | --- | ---
removed_weight_share | 0.3802 | 0.5147 | 0.1710 | 0.1104
effective_n | -0.2221 | -0.3052 | -0.1770 | -0.0930
effective_n_fraction | 0.1214 | 0.2175 | -0.0277 | -0.0296
remaining_frames | -0.2894 | -0.4228 | -0.1745 | -0.0795
support_after_ms | -0.2842 | -0.4194 | -0.1741 | -0.0795
removed_rms | 0.1859 | 0.3572 | 0.0932 | 0.0369
removed_high_band_fraction | -0.0724 | -0.1203 | -0.0228 | -0.0235
base_probability_margin | -0.9063 | -0.7138 | -0.2268 | -0.1663
base_logit_margin | -0.9034 | -0.7046 | -0.2260 | -0.1661

These are unadjusted descriptive rank correlations, not causal effects or independent tests: frame count, duration, effective_n and edge weight covary. Pearson coefficients are also saved. TV depends on softmax saturation, so strong inverse margin–TV association is partly mathematical and is not a correctness judgment.

Absolute effective_n is negatively associated with TV (ρ −0.222 / −0.305), whereas effective_n divided by frame count is not negatively associated with TV (ρ +0.121 / +0.218). The short/effective-support regime warrants attention without a cutoff:

Head | effective_n bin | n | RIGHT flips | Mean TV
--- | --- | --- | --- | ---
expanded | [3,5) | 20 | 7 | 0.1903
expanded | [5,10) | 443 | 7 | 0.0195
expanded | [10,20) | 196 | 0 | 0.0063
pilot | [3,5) | 20 | 2 | 0.0974
pilot | [5,10) | 443 | 5 | 0.0175
pilot | [10,20) | 196 | 0 | 0.0098

The preregistered descriptive margin categories are low `<0.20`, intermediate `[0.20,0.50)`, confident `≥0.50` in top-two probability difference. They are not calibrated confidence guarantees or altered classifier thresholds.

Head | Top concentration decile? | BASE margin category | n | Flips | Max TV
--- | --- | --- | --- | --- | ---
expanded | False | low | 20 | 4 | 0.3311
expanded | False | intermediate | 31 | 1 | 0.2531
expanded | False | confident | 542 | 0 | 0.1609
expanded | True | low | 6 | 3 | 0.3329
expanded | True | intermediate | 7 | 3 | 0.5567
expanded | True | confident | 53 | 3 | 0.8382
pilot | False | low | 29 | 3 | 0.1477
pilot | False | intermediate | 56 | 0 | 0.1295
pilot | False | confident | 508 | 0 | 0.1130
pilot | True | low | 8 | 3 | 0.3505
pilot | True | intermediate | 6 | 1 | 0.1451
pilot | True | confident | 52 | 0 | 0.2935

Small margins amplify sensitivity, but are **not necessary**: three expanded high-concentration flips start confident, including the worst 0.838 TV case. No expanded confident flip occurs outside the top concentration decile. Expanded flips comprise 7 low, 4 intermediate and 3 confident starts; pilot flips comprise 6 low and 1 intermediate, none confident. Native instability combines edge heterogeneity, concentration and head geometry; it is not merely too little remaining audio or universal low-margin behavior.

## Per-tone RIGHT analysis

High concentration below means the same whole-native top-decile slice, without tone-specific tuning. Recall uses known native labels. “Support/oppose” means whether including the final frame increases/decreases the known-label margin against the strongest non-label BASE competitor, including exact renormalization. It is not a phonetic annotation; a decrease can leave the label overwhelmingly correct.

Head | Tone | n | Flips | TV mean / max | Weight mean / max | High n | BASE→RIGHT recall | Label margin support / oppose
--- | --- | --- | --- | --- | --- | --- | --- | ---
expanded | T1 | 154 | 3 | 0.0223 / 0.3329 | 9.72% / 36.74% | 20 | 89.61% → 88.31% | 29 / 125
expanded | T2 | 139 | 3 | 0.0207 / 0.2771 | 9.13% / 34.35% | 19 | 91.37% → 93.53% | 43 / 96
expanded | T3 | 103 | 4 | 0.0280 / 0.8382 | 8.09% / 42.23% | 7 | 90.29% → 88.35% | 34 / 69
expanded | T4 | 263 | 4 | 0.0171 / 0.5567 | 8.22% / 30.87% | 20 | 92.78% → 91.25% | 61 / 202
pilot | T1 | 154 | 2 | 0.0217 / 0.3505 | 9.72% / 36.74% | 20 | 94.16% → 95.45% | 15 / 139
pilot | T2 | 139 | 3 | 0.0207 / 0.1747 | 9.13% / 34.35% | 19 | 87.05% → 86.33% | 36 / 103
pilot | T3 | 103 | 0 | 0.0154 / 0.1359 | 8.09% / 42.23% | 7 | 84.47% → 84.47% | 29 / 74
pilot | T4 | 263 | 2 | 0.0145 / 0.1451 | 8.22% / 30.87% | 20 | 94.68% → 93.92% | 84 / 179

Expanded T3 has the largest mean and worst TV, with four flips and two net lost correct predictions. Expanded T2 has three flips but **gains three correct predictions**: all its RIGHT flips correct misleading BASE evidence. Pilot T2 has three flips and loses one net correct prediction. Hence “fragility” is not synonymous with degradation; deleting a high-weight frame sometimes improves correctness. Relative to the previous uniform RIGHT results, expanded T2/T3 flips remain 3/4 versus 2/3, and pilot T2 3 versus 1. Pilot T3 has zero acoustic RIGHT flips despite the worst expanded T3 failure. Pooling is not changed by tone.

## Learner evidence: seven disagreements, zero adjudicable

All seven disagreeing natural BASE units fail the existing frozen F0 interpretation eligibility rules. The admissible evidence was taken only from the frozen deterministic `raw.json` and `output.json` produced without text or expected tones. The source bridge calls acoustic shape/family functions; no expected-tone, sandhi, learner grade or Jacob judgment is used. The failed solo annotation's gate remains INSUFFICIENT (10/28 native exact agreement, 3/8 exact repeat agreement); its learner labels were never read as truth. No other reliable independently obtained listener realization reference was found in the available frozen artifacts.

Quality is **STRONG 0, MODERATE 0, WEAK 5, UNAVAILABLE 2**. “WEAK” means retained measurements exist but are insufficient, fragmented or otherwise invalid for adjudication. “UNAVAILABLE” means no retained independent contour; raw rejected tracker samples do not rescue it. An ambiguous valid realization is conceptually distinct from a missing contour; none of these seven has sufficient independent evidence to declare a reliably ambiguous realized tone either. The preregistration's generic word “eligible” maps to the frozen schema's `sufficient` state; no eligibility rules changed.

Probabilities are in T1/T2/T3/T4 order; each head's margins are probability / logit top-two differences. No winner is inferred from confidence.

ID / recording | Expanded prediction, probabilities | Expanded margins | Pilot prediction, probabilities | Pilot margins | Quality
--- | --- | --- | --- | --- | ---
learner:0b44eac1332ea0859ac54d67:4 / S03.wav | T2 [0.0003, 0.9945, 0.0000, 0.0052] | 0.9893 / 5.2490 | T1 [0.5839, 0.3501, 0.0508, 0.0152] | 0.2337 / 0.5113 | WEAK
learner:39e33220c5dec271b192f561:2 / S02.wav | T2 [0.0062, 0.7601, 0.2011, 0.0326] | 0.5590 / 1.3294 | T1 [0.4208, 0.0682, 0.2948, 0.2161] | 0.1260 / 0.3558 | UNAVAILABLE
learner:39e33220c5dec271b192f561:3 / S02.wav | T2 [0.0000, 0.9926, 0.0073, 0.0000] | 0.9853 / 4.9063 | T3 [0.0580, 0.2645, 0.6644, 0.0131] | 0.3998 / 0.9208 | WEAK
learner:4cf712ee935667d1ab00dd9f:1 / S01.wav | T3 [0.0204, 0.2222, 0.6398, 0.1176] | 0.4175 / 1.0574 | T4 [0.3942, 0.0100, 0.0546, 0.5413] | 0.1472 / 0.3173 | WEAK
learner:4cf712ee935667d1ab00dd9f:10 / S01.wav | T3 [0.1271, 0.0099, 0.8611, 0.0020] | 0.7340 / 1.9132 | T1 [0.5207, 0.0034, 0.3294, 0.1466] | 0.1913 / 0.4580 | WEAK
learner:4cf712ee935667d1ab00dd9f:4 / S01.wav | T2 [0.0000, 0.9495, 0.0027, 0.0478] | 0.9018 / 2.9899 | T4 [0.0359, 0.3538, 0.0382, 0.5721] | 0.2182 / 0.4804 | UNAVAILABLE
learner:4cf712ee935667d1ab00dd9f:5 / S01.wav | T1 [0.7145, 0.0124, 0.0050, 0.2681] | 0.4463 / 0.9801 | T4 [0.0521, 0.0087, 0.1098, 0.8294] | 0.7196 / 2.0218 | WEAK

ID | Frozen eligibility / reasons | Retained segment n; net / range semitones | Adjudication
--- | --- | --- | ---
learner:0b44eac1332ea0859ac54d67:4 | insufficient: too_little_sustained_evidence, raw_to_selected_attrition | n=10, +0.822 / 0.822 | unresolved
learner:39e33220c5dec271b192f561:2 | insufficient: too_little_sustained_evidence, voiced_boundary_lost, raw_to_selected_attrition, fragmented_voiced_support | none | unresolved
learner:39e33220c5dec271b192f561:3 | insufficient: too_little_sustained_evidence, voiced_boundary_lost, raw_to_selected_attrition | n=3, +0.098 / 0.098 | unresolved
learner:4cf712ee935667d1ab00dd9f:1 | unstable: fragmented_voiced_support | n=2, -0.141 / 0.141; n=14, -2.382 / 2.382 | unresolved
learner:4cf712ee935667d1ab00dd9f:10 | insufficient: too_little_sustained_evidence, raw_to_selected_attrition | n=2, +0.069 / 0.069 | unresolved
learner:4cf712ee935667d1ab00dd9f:4 | insufficient: no_voiced_support | none | unresolved
learner:4cf712ee935667d1ab00dd9f:5 | insufficient: too_little_sustained_evidence | n=7, -1.272 / 1.325 | unresolved

**Adjudicable disagreements: 0/7. Expanded-favored, pilot-favored, neither and both-compatible outcomes on STRONG/MODERATE evidence are all unestimated (zero eligible cases), not competing accuracy scores.** The partial rising S03 trace is specifically not promoted to T2 truth: it fails duration/attrition eligibility. Full timestamped segments, within-segment rise/fall sums, range, continuity and eligibility metrics are saved in `independent-evidence.json/csv`. Gaps are never bridged to manufacture one contour.

## Learner head geometry and comparison with native

Acoustic native head disagreements are **65/659 (9.86%)**, versus **7/14 (50%)** natural learner BASE items. Uniform had 92/659 native and 5/14 learner disagreements. Agreement is not correctness, and these descriptive rates are not a speaker-disjoint learner population estimate: the learner clips come from one speaker and three recordings.

Expanded / pilot pair | Learner count / 7 | Native count / 65
--- | --- | ---
T1/T4 | 1 | 4
T2/T1 | 2 | 14
T2/T3 | 1 | 4
T2/T4 | 1 | 8
T3/T1 | 1 | 1
T3/T4 | 1 | 11

Expanded T2 / pilot T1 is the most frequent learner pair (2/7), also the most frequent native pair (14/65), but no pair dominates the learner set. Every observed learner pair occurs natively. Native expanded T3 / pilot T2 occurs 10 times and is absent among these learners, so the learner sample is not simply a uniform multiplication of native pair frequencies.

Expanded / pilot margin category | Learners | Natives
--- | --- | ---
confident/confident | 0 | 12
confident/intermediate | 3 | 9
confident/low | 2 | 16
intermediate/confident | 1 | 10
intermediate/intermediate | 0 | 4
intermediate/low | 1 | 3
low/confident | 0 | 6
low/intermediate | 0 | 3
low/low | 0 | 2

Learner breakdown: **both low 0; expanded confident / pilot below confident 5; pilot confident / expanded below confident 1; both confident 0; neither confident 1**. More narrowly, expanded confident/pilot low is 2; expanded confident/pilot intermediate 3; expanded intermediate/pilot confident 1; expanded intermediate/pilot low 1. Native disagreements show all these patterns, as well as 12 confident/confident and 2 low/low cases. Qualitative answer: **A — the observed learner disagreements resemble native head-geometry disagreements**, at a higher observed frequency. This does not prove the same cause or justify accent/training-data speculation.

`classifier-margins.json/csv` stores the exact 768-dimensional pooled embedding, relevant raw-space margin direction and intercept, signed expanded-predicted-class minus pilot-predicted-class margin, bias and per-frame margin contributions for each head. Those margins reconstruct the sealed outputs. Direction cosines are in `learner-structure`. Geometry establishes how the heads differ, not which is perceptually correct.

## Learner agreement controls, structure and perturbations

Fixed disagreement ID | Fixed agreement control
--- | ---
learner:0b44eac1332ea0859ac54d67:4 | learner:39e33220c5dec271b192f561:0
learner:39e33220c5dec271b192f561:2 | learner:0b44eac1332ea0859ac54d67:5
learner:39e33220c5dec271b192f561:3 | learner:39e33220c5dec271b192f561:5
learner:4cf712ee935667d1ab00dd9f:1 | learner:4cf712ee935667d1ab00dd9f:2
learner:4cf712ee935667d1ab00dd9f:10 | learner:39e33220c5dec271b192f561:8
learner:4cf712ee935667d1ab00dd9f:4 | learner:0b44eac1332ea0859ac54d67:2
learner:4cf712ee935667d1ab00dd9f:5 | learner:0b44eac1332ea0859ac54d67:1

Property | Disagreement mean / median (n=7) | Agreement mean / median (n=7)
--- | --- | ---
effective_n | 8.8939 / 8.7279 | 10.2237 / 10.6418
effective_n_fraction | 0.8355 / 0.8829 | 0.8630 / 0.8186
max_weight_share | 0.1833 / 0.1558 | 0.1435 / 0.1360
first_weight_share | 0.0733 / 0.0622 | 0.0813 / 0.0747
right_weight_share | 0.1173 / 0.0790 | 0.0962 / 0.0939
final_quarter_share | 0.3148 / 0.3178 | 0.3266 / 0.2841
frame_count | 11.1429 / 9.0000 | 12.0000 / 13.0000
support_ms | 215.7054 / 179.9688 | 232.8482 / 250.0000
normalized_entropy | 0.9460 / 0.9729 | 0.9660 / 0.9589
pooled_embedding_norm | 5.6109 / 5.6667 | 5.4022 / 5.5457
expanded_l2_to_reference | 2.8250 / 2.6619 | 3.2912 / 3.3834
expanded_cosine_to_reference | 0.8793 / 0.8877 | 0.8505 / 0.8757
expanded_standardized_distance_to_reference | 16.3918 / 15.3783 | 18.9510 / 19.7335
pilot_standardized_distance_to_reference | 16.7036 / 15.6944 | 19.2604 / 20.0078
expanded_distance_to_training_mean | 5.0605 / 4.9888 | 4.7627 / 4.8757
pilot_distance_to_training_mean | 5.1352 / 5.0531 | 4.8196 / 4.9485

Disagreements have somewhat greater mean max weight (18.33% versus 14.35%) and lower mean effective_n (8.89 versus 10.22). But RIGHT share medians go the other way (7.90% versus 9.39%), final-quarter weight means are 31.48% versus 32.66%, and normalized effective_n/entropy are similar. Spearman association with disagreement is **+0.230 max weight, −0.301 effective_n, −0.089 RIGHT share, −0.018 final-quarter share**. At n=14 these are descriptive, not evidence of absence or a basis for a fitted decision rule. Embedding norms and reference distances do not expose a distinct outlier regime; disagreement items are on average closer to the reference by L2/cosine.

The largest disagreement edge weight, **31.18%**, is the four-frame **learner:4cf712ee935667d1ab00dd9f:4**, with 70 ms BASE support; its contraction is inadmissible. It remains in all seven-case primary summaries. In a separately labeled admissibility stratum (6 disagreement versus 7 agreement units), mean RIGHT shares are **8.49% versus 9.62%**, max weights **16.18% versus 14.35%**, and effective_n **9.73 versus 10.22**. This explains much of the primary mean edge-weight difference without deleting a case from the fixed audit. Paired differences and full ranges are persisted; there is no claim of precise matching or statistical independence.

On the **13 mutually usable natural units**, expanded LEFT/RIGHT flips are **0/0**, and pilot LEFT/RIGHT flips are **0/0**. This includes **six** of the seven disagreement units; the seventh has no admissible contraction, so stability is unknown for it. Stability supports the conclusion that small admissible boundary changes do not generate the observed learner head disagreement. It cannot adjudicate realization or exclude all representation mismatch.

## Cross-synthesis, refit decision and exactly one next experiment

**Decision: TWO_BLOCKERS.** Native RIGHT instability has a clear exact mechanism: concentrated, heterogeneous correct-class evidence can be removed and the remaining evidence amplified. The concentration association is real, but high concentration is neither inherently pathological nor a sufficient safety signal. Learner disagreement is not clearly explained by the same RIGHT/tail concentration pattern and remains unadjudicable. A modest max-weight/effective_n difference leaves some representation involvement possible; it does not establish a common mechanism.

**Head-only refit justified now: NO.** Native generalization is supported and a fixed representation exists, but no independent realization evidence establishes systematic frozen-head error on these seven learner disagreements. Representation sensitivity also remains unresolved natively. Head agreement, confidence and weak pitch traces cannot substitute for independent labels.

**Exactly one next experiment:** Preregister one reliability-first, blinded independent native-listener realized-tone validation of the seven fixed learner disagreement recordings, using existing native control clips and concealed repeats. Fix listener qualification and reliability gates before collecting judgments; hide expected tones, text, grades and model outputs. Use only judgments that pass those gates. Reuse existing recordings; do not fit heads or change pooling in that experiment.

This follows the finish request's evidence-collection branch. A generic weight-cap experiment is not justified: the two highest-weight T3 examples include both catastrophic and stable behavior, and the catastrophic removal destroys correct evidence. Choosing a regularizer or cap from these observed failures would risk suppressing useful speech evidence. The recommended listener experiment fills the smallest missing adjudication evidence; it does not clear the native blocker or authorize a head refit. No next experiment was performed here.

## Focused validation, freezes and artifacts

The focused suite passes **12/12 tests**: deterministic set selection and order invariance; every flip/top-ranked case included; stable-correct controls; exact RIGHT weight extraction and ownership equality; cached linear score reconstruction for all 44 items and both heads; weighted deletion identity; learner disagreement completeness; poisoned expected-tone/grade/Jacob/solo-label inputs; invalid F0 never promoted by a deterministic prediction; deterministic summaries; and frozen manifest/head/selection identity. No product/mobile tests or broad inference jobs were run.

Command: `OPENBLAS_NUM_THREADS=1 PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p test_pooling_blocker_audit.py -v`. Transcript: `focused-tests.txt`. Ruff on all three new Python files and `git diff --check` pass. Additional no-index whitespace checks cover new files because git diff does not include untracked files.

Targeted finish verification checks **14 pre-existing protected files**, including the representation manifest and seal, preregistration and seal, predictions, both heads, pooling source, confirmatory source, exact attribution source, lock, deterministic pitch inputs/outputs, and failed reliability gate. (These grouped descriptions overlap the counted files.) Git HEAD and the selection seal match. The earlier 3,106-file inventory was not rescanned. Each consumed cached WAV was separately verified against that inventory during cheap diagnostics. No new full-checkpoint scan was performed.

Frozen object | SHA-256
--- | ---
Representation manifest | d8ea363ed77ecab0a9d5cd664cc829e249a47cb14e1740a6772419f5334bfbd5
Expanded head | b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b
Pilot head | c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9
Pooling source | fb29da07da713338c48bcd57f4e6f7e5e442e804ec5ef8574d8ec1d2f3e8d083
Selection | 5c4ac1ad525691648044362cecba32495acace05165b9536819ffdef23aabe6e

Artifacts are additive under **`research/perceptual-tone-model/data/generated/pooling-blocker-audit-v1/`**. Core JSON tables also have CSV versions: `right-edge-contributions`, `native-right-all`, `native-acoustic-diagnostics`, `concentration-legitimacy`, `weight-bins-complete`, `high-weight-stable-vs-flip`, `concentration-margin-joint`, `native-correlations`, `remaining-support-correlations`, `per-tone-summary`, `independent-evidence`, `classifier-margins`, `class-pair-summary`, `native-learner-margin-patterns`, `learner-group-comparison-extended`, `learner-matched-differences`, `learner-admissible-stratum`, and `learner-stability`. `cross-synthesis.json` records quantitative synthesis; `final-decision.json` records the final decision and one next experiment. `artifact-index.json` hashes completed outputs.

New repository-visible files in this pass:

- `perceptual_tone/pooling_blocker_audit.py`
- `scripts/pooling_blocker_diagnostics.py`
- `tests/test_pooling_blocker_audit.py`
- `pooling-blocker-audit-report.md`

The generated output directory is ignored by the existing repository policy but present locally. All earlier uncommitted work was retained. Acoustic pooling remains **NOT READY for integration**.
