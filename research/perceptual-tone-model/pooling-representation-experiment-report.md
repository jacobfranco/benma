Preregistered offline pooling representation experiment

Pre-inference record — representations and their separate pooled-vector hashes are sealed. Neither frozen classifier has been loaded for this experiment.

Manifest: `data/generated/pooling-representation-v1/representation-manifest.json`

SHA-256: `347f9d9867b5c6abe2d23f03da95c968c9fdd8f0aa5e76e9312f7d7c166f8adb`

Sealed at: 2026-10-22T03:13:05.784141+00:00

Preregistration SHA-256: `b7b1b8ead9144776fab0bdd96d49d3978343ed72a01c49fd6261355cbc421fbc`.

276 items (20 physical/Google, 256 native), exactly three candidate arms. The native subset and speaker-disjoint checks are sealed in `native-control-ids.json`. Native owners are frozen MFA boundaries; physical owners are persisted GAP_AWARE_AZURE. This tests pooling, not native Azure ownership.

| Dataset | Arm | Total | Valid ownership | Representation usable | Head eligible | Abstention reasons |
|---|---|---:|---:|---:|---:|---|
| physical | UNIFORM_SAFE_OWNER | 20 | 19 | 19 | 15 | {'ownership_ambiguous': 1} |
| physical | CENTRAL_HALF | 20 | 19 | 19 | 15 | {'ownership_ambiguous': 1} |
| physical | ACOUSTIC_WEIGHTED | 20 | 19 | 19 | 15 | {'ownership_ambiguous': 1} |
| native | UNIFORM_SAFE_OWNER | 256 | 256 | 255 | 255 | {'insufficient_60ms_support': 1} |
| native | CENTRAL_HALF | 256 | 256 | 253 | 253 | {'insufficient_60ms_support': 3} |
| native | ACOUSTIC_WEIGHTED | 256 | 256 | 255 | 255 | {'insufficient_60ms_support': 1} |

This paragraph, hash, and coverage table were written before inference. Final results are appended below; this pre-inference record is retained verbatim.

**Final decision: NO_CLEAR_WINNER. NOT READY for dev integration.**
Acoustic weighting is the strongest candidate in this experiment: it largely preserves
frozen native recognition, reduces the early low-energy and quiet-tail contributions,
and reduces head disagreement. It does not consistently resolve strong-frication
sensitivity or the opposite head interpretations of take-1 这 and take-3 我. Central
pooling removes some peripheral frames but can concentrate other problematic material
and substantially worsens expanded native recognition. These mixed findings do not
justify integration, a tuned rule, or a head-retraining recommendation.

All physical outputs below are diagnostic. No dictionary, expected/surface tone, learner
grade, or physical correctness score entered representation construction or evaluation.
Neither head is perceptual ground truth. Smaller distance to CURRENT_REFERENCE is
descriptive stability, not proof of better recognition on learner speech.

Exactly three candidate definitions were sealed. **Uniform** uses every center in the
fixed safely owned span, with weight 1/N. **Central** uses K=ceil(N/2), starts at
floor((N-K)/2), and keeps K consecutive IDs with weight 1/K. This selects the earlier
window on a tie: N=4 → offsets [1,2]; N=5 → [1,2,3]; N=6 → [1,2,3]; N=11 → [2,…,7].
**Acoustic** assigns raw weight RMS_20ms * (1-high_band_fraction), then divides by the
sum in float64. It keeps the full eligible frame set; it does not trim ownership.

RMS is sqrt(mean(x²)) of the uncentered 20 ms waveform. Spectral power is
abs(rFFT((x-mean(x))*Hann))², with the symmetric NumPy Hann window. The high-band
fraction is power at frequencies ≥3400 Hz divided by max(total power, 1e-24), exactly
the previous low-level diagnostic definition. The hop is 5 ms. Physical features are
read from the frozen diagnostic CSVs; native features use the same equations on
canonical PCM16 16 kHz audio. Each encoder center maps to the nearest timestamp,
earlier on a tie; no interpolation, F0, periodicity estimate, or pitch mask is used.
Only negative RMS and out-of-range band fractions are clamped to their mathematical
domains. Nonfinite values fail. A total weight ≤float64.tiny
(2.2250738585072014e-308) abstains; there is no uniform fallback or weight floor.

All arms require at least three encoder frames AND ≥60 ms of contiguous selected
20 ms frame-cell support clipped to the owner. Arithmetic tolerance is 1e-9 seconds.
No outward expansion is allowed. Kish effective_n=1/sum(w²), and effective_n*20 ms,
are descriptive only; no concentration cutoff is applied. Owner duration, center
extent, cell support, clipped support, and effective support are separately saved.

The representation seal was written at **2026-10-22T03:13:05.784141+00:00**; inference began at
**2026-10-22T17:45:44.431911+00:00**. The report's original prefix and coverage table were also
hashed before that inference event (`pre-inference-report-seal.json`).
The primary manifest hashes every pooled vector and layer-9 tensor; its own hash is
`347f9d9867b5c6abe2d23f03da95c968c9fdd8f0aa5e76e9312f7d7c166f8adb`. It contains all 828 item/arm records, including explicit
abstentions, plus the available historical reference records. The separately sealed
`pre-inference-inventory.json` adds source/speaker, explicit frame counts and central
window offsets, and links native-only evaluation labels. No sealed representation
was overwritten, invalidated, or changed. The two frozen heads produced
2154 saved head/representation outputs, once per unique combination.

The native control uses 64 items per T1/T2/T3/T4, selected from the existing 915
primary-eligible test units by deterministic round robin over sorted speaker IDs,
with lexicographically sorted item IDs within each speaker/tone. The exact 256 IDs
were persisted before encoder extraction or classifier inference. All 12 held-out
speakers are represented and disjoint from both heads' training speakers. Labels
are used only for native stratification and metrics, never pooling. No new model
was fitted. These 256 items are clustered within speakers/utterances; descriptive
changes of one item do not establish statistical equivalence or superiority.

Native ownership is the existing frozen MFA whole read-unit boundary; physical
ownership is the persisted GAP_AWARE_AZURE result. This is an explicit limitation:
the native control tests representation transfer under frozen ownership, not the
Azure ownership selector. CURRENT_REFERENCE is the historical physical pooling
or native nucleus/coda pooling in the identical encoder context, not a fourth
candidate. Historical native references shorter than 60 ms remain historical
comparators; none are used to relax candidate support rules.

Coverage must separate representation availability from class inventory. All arms
provide representations for 19/20 physical/Google units. The one unavailable unit
is ownership-ambiguous take-2 买, unchanged under all arms. The four neutral units
have usable representations but are outside the heads' T1-T4 inventory: they are
**head exclusions, not model abstentions**. Thus each arm has 15 usable numbered-tone
head inputs out of 16 numbered units. Native units are all numbered and ownership-valid.

| Dataset | Arm | Usable / total | Abstained | Head usable | Support failures |
| --- | --- | --- | --- | --- | --- |
| physical | Uniform | 19/20 | 1 | 15 | 0 |
| physical | Central | 19/20 | 1 | 15 | 0 |
| physical | Acoustic | 19/20 | 1 | 15 | 0 |
| native | Uniform | 255/256 | 1 | 255 | 1 |
| native | Central | 253/256 | 3 | 253 | 3 |
| native | Acoustic | 255/256 | 1 | 255 | 1 |

The shared native failure is `aishell3:SSB02870020:2`: its 60 ms owner contains
three centers, but clipped cell support is **59.96875 ms** under the sealed half-sample
geometry. It remains rejected; the threshold was not rounded down after observing
data. Central additionally rejects `aishell3:SSB05700009:14` and
`aishell3:SSB07860039:11`, each retaining two frames / 40 ms. No zero-weight failure
occurred. There are zero effective-support exclusions because that statistic has
no gating role.

Native metrics are conditional on the arm's covered items. Recalls and confusion matrices use T1,T2,T3,T4 order. All-selected correct fractions and paired denominators follow so coverage cannot hide errors.

| Head | Arm | N | Accuracy | Balanced accuracy | Macro F1 | Recall T1/T2/T3/T4 |
| --- | --- | --- | --- | --- | --- | --- |
| expanded | Reference | 256 | 91.02% | 91.02% | 91.06% | 93.75% / 85.94% / 92.19% / 92.19% |
| expanded | Uniform | 255 | 88.63% | 88.59% | 88.57% | 92.19% / 79.37% / 90.62% / 92.19% |
| expanded | Central | 253 | 84.19% | 84.01% | 83.91% | 85.94% / 68.85% / 85.94% / 95.31% |
| expanded | Acoustic | 255 | 91.76% | 91.73% | 91.74% | 92.19% / 84.13% / 93.75% / 96.88% |
| pilot | Reference | 256 | 89.84% | 89.84% | 89.87% | 92.19% / 85.94% / 85.94% / 95.31% |
| pilot | Uniform | 255 | 89.41% | 89.42% | 89.48% | 87.50% / 90.48% / 85.94% / 93.75% |
| pilot | Central | 253 | 89.72% | 89.69% | 89.73% | 90.62% / 86.89% / 87.50% / 93.75% |
| pilot | Acoustic | 255 | 89.41% | 89.41% | 89.47% | 90.62% / 88.89% / 85.94% / 92.19% |

| Head | Arm | Confusion: truth rows * predicted columns |
| --- | --- | --- |
| expanded | Reference | [60, 1, 2, 1]`; `[3, 55, 6, 0]`; `[1, 1, 59, 3]`; `[1, 0, 4, 59] |
| expanded | Uniform | [59, 1, 1, 3]`; `[2, 50, 10, 1]`; `[1, 2, 58, 3]`; `[2, 2, 1, 59] |
| expanded | Central | [55, 4, 1, 4]`; `[2, 42, 16, 1]`; `[1, 3, 55, 5]`; `[2, 1, 0, 61] |
| expanded | Acoustic | [59, 1, 1, 3]`; `[2, 53, 7, 1]`; `[1, 0, 60, 3]`; `[1, 0, 1, 62] |
| pilot | Reference | [59, 1, 0, 4]`; `[4, 55, 2, 3]`; `[0, 3, 55, 6]`; `[0, 2, 1, 61] |
| pilot | Uniform | [56, 3, 0, 5]`; `[2, 57, 2, 2]`; `[1, 1, 55, 7]`; `[0, 2, 2, 60] |
| pilot | Central | [58, 2, 1, 3]`; `[4, 53, 3, 1]`; `[1, 1, 56, 6]`; `[0, 1, 3, 60] |
| pilot | Acoustic | [58, 2, 0, 4]`; `[3, 56, 2, 2]`; `[1, 1, 55, 7]`; `[0, 2, 3, 59] |

| Head | Arm | Correct / all 256 | Accuracy on common 253 | Paired accuracy Δ (pp; relative) |
| --- | --- | --- | --- | --- |
| expanded | Reference | 91.02% | 91.30% | +0.00; +0.00% |
| expanded | Uniform | 88.28% | 88.54% | -2.75; -3.00% |
| expanded | Central | 83.20% | 84.19% | -7.11; -7.79% |
| expanded | Acoustic | 91.41% | 91.70% | +0.39; +0.43% |
| pilot | Reference | 89.84% | 89.72% | +0.00; +0.00% |
| pilot | Uniform | 89.06% | 89.33% | -0.39; -0.44% |
| pilot | Central | 88.67% | 89.72% | +0.00; +0.00% |
| pilot | Acoustic | 89.06% | 89.33% | -0.39; -0.44% |

Paired deltas compare each arm with the reference on that arm's covered IDs.
Acoustic changes expanded accuracy by **+0.39 pp (+0.43% relative)** and pilot
by **-0.39 pp (-0.44% relative)**: one additional correct expanded item and one
fewer correct pilot item. Central changes expanded by **-7.11 pp (-7.79% relative)**,
while pilot is unchanged on the same 253 items. Native balanced accuracy and macro
F1 deltas, including relative differences, are saved in `native-metrics.json`.
These are recognition metrics only for known native labels.

The six required cases below show expanded/pilot predictions and probability top-two margins. Logit margins and all four probabilities are saved alongside them in `six-diagnostic-cases.json` and `all-predictions.csv`.

| Case | Arm | Expanded | Pilot | Probability margins E / P | Logit margins E / P |
| --- | --- | --- | --- | --- | --- |
| take-1 这 | Reference | T3 | T2 | 0.1112 / 0.5138 | 0.2778 / 1.2880 |
| take-1 这 | Uniform | T2 | T3 | 0.0809 / 0.1196 | 0.2611 / 0.2868 |
| take-1 这 | Central | T2 | T3 | 0.5364 / 0.4564 | 1.5231 / 1.1030 |
| take-1 这 | Acoustic | T3 | T2 | 0.0349 / 0.2496 | 0.0989 / 0.6046 |
| take-2 这 | Reference | T3 | T3 | 0.8039 / 0.1460 | 2.3241 / 0.3693 |
| take-2 这 | Uniform | T4 | T3 | 0.3062 / 0.2549 | 0.8224 / 0.7585 |
| take-2 这 | Central | T3 | T3 | 0.1227 / 0.4796 | 0.3367 / 1.4921 |
| take-2 这 | Acoustic | T3 | T3 | 0.6188 / 0.0770 | 1.5105 / 0.1933 |
| take-3 想 | Reference | T3 | T1 | 0.1596 / 0.7813 | 0.3358 / 2.3981 |
| take-3 想 | Uniform | T2 | T1 | 0.1738 / 0.6218 | 0.3873 / 1.7997 |
| take-3 想 | Central | T2 | T1 | 0.2586 / 0.8210 | 0.5769 / 2.6313 |
| take-3 想 | Acoustic | T2 | T1 | 0.1506 / 0.7403 | 0.3611 / 2.2971 |
| take-3 买 | Reference | T3 | T3 | 0.4882 / 0.7470 | 1.0683 / 2.1813 |
| take-3 买 | Uniform | T2 | T3 | 0.1789 / 0.7027 | 0.3624 / 2.1322 |
| take-3 买 | Central | T2 | T3 | 0.2373 / 0.3553 | 0.4850 / 0.8995 |
| take-3 买 | Acoustic | T3 | T3 | 0.4142 / 0.8174 | 0.8819 / 2.6156 |
| google 买 | Uniform | T3 | T3 | 0.9860 / 0.9615 | 5.0626 / 4.3882 |
| google 买 | Central | T3 | T3 | 0.9986 / 0.9863 | 7.2688 / 5.3919 |
| google 买 | Acoustic | T3 | T3 | 0.9997 / 0.9877 | 8.8648 / 5.4184 |
| take-3 我 | Uniform | T2 | T3 | 0.7277 / 0.5304 | 2.0412 / 1.5303 |
| take-3 我 | Central | T2 | T3 | 0.4403 / 0.6337 | 0.9513 / 1.6426 |
| take-3 我 | Acoustic | T2 | T3 | 0.7399 / 0.8501 | 1.9653 / 2.6587 |

**Take-1 这:** central keeps IDs 15-20. It removes earliest IDs 13-14 but retains
15 and increases the mass on all added early material (13-19) from 63.64% to
83.33%. Acoustic reduces that mass to 28.48%; earliest 13-15 mass drops from
27.27% to 13.65%. Expanded/pilot remain opposite under every arm: uniform and
central give T2/T3, acoustic gives T3/T2. Acoustic expanded's probability margin
is only .0349 (logit .0989). This reduces early weight without resolving the
head-dependent low-margin instability. The old prediction is not a truth label.

**Take-2 这:** central keeps IDs 15-20 and excludes both influential below-gate
frames 13-14. Acoustic assigns them .005825 and .007484 normalized weight
(RMS .001594/.001839; high-band .1654/.0706), together **1.33% versus 18.18%**
uniform. Later speech IDs 20-23 receive .156702/.232366/.234311/.262977 each;
the early pair is far less influential in the weighted mean. Both candidates give
T3/T3, whereas uniform gives T4/T3. Acoustic expanded's margin rises to .6188,
but pilot's falls to .0770; head agreement does not mean both heads became more certain.

**Take-3 想:** known strong-frication IDs 13-16 have high-band fractions
.6688/.4539/.5593/.5364 and RMS .226988/.267388/.225599/.159438. Acoustic
weights are .034885/.067761/.046134/.034302, totaling **18.31% versus 23.53%**
uniform, only a 22.19% relative reduction. Frame 14 actually increases from
5.88% uniform to 6.78%: strong RMS can outweigh the spectral penalty. Central
keeps 17-25 and excludes all four fricative frames, but both alternatives still
give expanded T2 / pilot T1. Acoustic expanded's logit margin .3611 is close to
uniform .3873. This does not establish that frication sensitivity is solved;
contextual encoder vectors can carry information outside their local center.

**Take-3 买:** quiet tail IDs 29-35 have RMS .024342-.036308, versus
.043861-.133777 in IDs 13-28. Acoustic tail weights are
.022830/.017551/.019372/.015743/.012623/.017742/.015240, totaling
**12.11% versus 30.43%** uniform. Central keeps 18-29 and only one tail frame,
8.33% total tail weight, but still gives T2/T3. Acoustic gives T3/T3 with margins
.4142/.8174. Central also removes early body frames with different projections;
less tail mass alone is insufficient. Acoustic improves head consistency here,
without establishing a correct perceived tone.

**Google 买:** uniform and acoustic retain 15 frames and 290 ms clipped support;
central retains 8 frames and 160 ms. Acoustic effective_n is 10.37. All three
remain usable without F0 and produce T3/T3. Its existing pitch status is reported
only as metadata; neither missing pitch nor the T3 output selects the representation.

**Take-3 我:** uniform/acoustic retain 24 frames / 470 ms; central retains 12 /
240 ms. All arms give expanded T2 / pilot T3. Acoustic increases pilot margin
from .5304 to .8501 while retaining expanded margin .7399: confident disagreement
persists. Neither output is called correct. There is no usable CURRENT_REFERENCE
comparison for this unit or Google 买.

The complete 20-unit inventory is below. Each candidate has identical representation
and head coverage on these recordings. Full per-arm probabilities, margins, support,
weights, and existing pitch status are in `physical-20-unit-comparison.csv`.
Pitch status is copied only after inference for interpretation; it is absent from
the sealed representation function's inputs.

| Unit | Ownership | Representation (all arms) | Saved pitch status | Uniform E/P | Central E/P | Acoustic E/P |
| --- | --- | --- | --- | --- | --- | --- |
| google 我 | safe | usable | usable | T2/T2 | T2/T2 | T2/T2 |
| google 想 | safe | usable | unavailable | T2/T2 | T2/T2 | T2/T2 |
| google 买 | safe | usable | unavailable | T3/T3 | T3/T3 | T3/T3 |
| google 这 | safe | usable | usable | T4/T4 | T4/T4 | T4/T4 |
| google 个 | safe | usable | usable | neutral: excluded | neutral: excluded | neutral: excluded |
| take-1 我 | safe | usable | usable | T2/T3 | T2/T3 | T2/T3 |
| take-1 想 | safe | usable | usable | T3/T1 | T1/T1 | T1/T1 |
| take-1 买 | safe | usable | usable | T2/T2 | T2/T2 | T2/T2 |
| take-1 这 | safe | usable | unavailable | T2/T3 | T2/T3 | T3/T2 |
| take-1 个 | safe | usable | unavailable | neutral: excluded | neutral: excluded | neutral: excluded |
| take-2 我 | safe | usable | usable | T3/T3 | T3/T3 | T3/T3 |
| take-2 想 | safe | usable | usable | T1/T1 | T1/T1 | T1/T1 |
| take-2 买 | ambiguous | abstained | usable | ownership abstained | ownership abstained | ownership abstained |
| take-2 这 | safe | usable | unavailable | T4/T3 | T3/T3 | T3/T3 |
| take-2 个 | safe | usable | unavailable | neutral: excluded | neutral: excluded | neutral: excluded |
| take-3 我 | safe | usable | unavailable | T2/T3 | T2/T3 | T2/T3 |
| take-3 想 | safe | usable | usable | T2/T1 | T2/T1 | T2/T1 |
| take-3 买 | safe | usable | usable | T2/T3 | T2/T3 | T3/T3 |
| take-3 这 | safe | usable | usable | T4/T4 | T4/T4 | T4/T4 |
| take-3 个 | safe | usable | unavailable | neutral: excluded | neutral: excluded | neutral: excluded |

Pairwise stability uses mutually usable numbered-tone units: 15 among candidates and 13 against the available reference. TV is half the L1 probability-vector difference. Embedding cosine/L2 are independent of the head and appear once per pair.

| Pair | N | Expanded agree; mean TV | Pilot agree; mean TV | Mean embedding cosine | Mean embedding L2 |
| --- | --- | --- | --- | --- | --- |
| Reference → Uniform | 13 | 9/13; 0.1942 | 12/13; 0.1376 | 0.8568 | 2.9813 |
| Reference → Central | 13 | 9/13; 0.1794 | 12/13; 0.0915 | 0.8703 | 2.6930 |
| Reference → Acoustic | 13 | 11/13; 0.0593 | 13/13; 0.0405 | 0.9629 | 1.5249 |
| Uniform → Central | 15 | 13/15; 0.1264 | 15/15; 0.1325 | 0.8832 | 2.7465 |
| Uniform → Acoustic | 15 | 11/15; 0.1494 | 14/15; 0.1178 | 0.9043 | 2.2525 |
| Central → Acoustic | 15 | 13/15; 0.1532 | 14/15; 0.0894 | 0.8906 | 2.4422 |

| Dataset | Arm | Head disagreement | Rate | Mean head TV |
| --- | --- | --- | --- | --- |
| physical | Reference | 4/13 | 30.77% | 0.2912 |
| physical | Uniform | 7/15 | 46.67% | 0.3271 |
| physical | Central | 5/15 | 33.33% | 0.2713 |
| physical | Acoustic | 4/15 | 26.67% | 0.2974 |
| native | Reference | 31/256 | 12.11% | 0.1420 |
| native | Uniform | 33/255 | 12.94% | 0.1898 |
| native | Central | 34/253 | 13.44% | 0.1872 |
| native | Acoustic | 24/255 | 9.41% | 0.1482 |

On the same 13 reference-covered physical units, disagreements are reference 4, uniform 6, central 4, acoustic 3. This paired comparison avoids confusing the reference's smaller coverage with better agreement. Agreement and TV improve in different ways; none is an accuracy score for physical speech.

| Acoustic dataset | N usable | Effective_n min / median / max | Effective_n <3 (descriptive) |
| --- | --- | --- | --- |
| physical | 19 | 2.905 / 11.923 / 18.566 | 1 |
| native | 255 | 2.155 / 8.695 / 17.171 | 2 |

The most concentrated physical item is neutral take-2 个: effective_n 2.905 across
8 eligible frames, maximum weight .4692. It has a representation but no four-class
inference. The lowest numbered physical effective_n is take-2 这, 4.879 across
11 frames. Native `aishell3:SSB02880034:0` has effective_n 2.155 across 7 frames
(max weight .5402), and `aishell3:SSB04070025:0` has 2.671 across 9 (max .4511).
They remain included exactly as preregistered; no post-hoc support exclusions were made.

Native distribution diagnostics use only each head's frozen StandardScaler mean and scales. Standardized norm is a diagonal variance-scaled distance to that training mean; raw L2 is also shown. No covariance or new density model is fitted. Smaller norm is not automatically better: broad uniform averaging can dilute features toward the mean.

| Head | Arm | Mean standardized norm | Mean raw L2 to training mean | Mean cosine to reference | Mean paired standardized-norm Δ |
| --- | --- | --- | --- | --- | --- |
| expanded | Reference | 27.434 | 4.833 | 1.0000 | +0.000 |
| expanded | Uniform | 24.216 | 4.045 | 0.8751 | -3.182 |
| expanded | Central | 33.331 | 5.371 | 0.7704 | +5.940 |
| expanded | Acoustic | 26.491 | 4.461 | 0.9290 | -0.908 |
| pilot | Reference | 28.268 | 4.894 | 1.0000 | +0.000 |
| pilot | Uniform | 24.915 | 4.092 | 0.8751 | -3.317 |
| pilot | Central | 34.077 | 5.406 | 0.7704 | +5.855 |
| pilot | Acoustic | 27.289 | 4.517 | 0.9290 | -0.942 |

Central moves native embeddings furthest: reference cosine .7704, expanded
standardized norm 33.33 versus 27.43 reference, and mean standardized vector
distance 23.89. Its expanded recognition loss is consistent with frozen-head
distribution mismatch. However its physical structural benefit is inconsistent,
and pilot native accuracy is preserved, so this is insufficient for decision B.
Acoustic stays closer to the existing representation (cosine .9290, expanded
norm 26.49, standardized distance 11.55), with native metrics essentially unchanged
on this subset. There is no major acoustic head-compatibility regression to justify
retraining. Uniform has norm 24.22 and cosine .8751: pooling toward the mean can
reduce the norm while degrading expanded recognition.

Weight-mass comparisons quantify direct pooling composition, not causal waveform
attribution: HuBERT features are contextual. This pass does not repeat attribution,
change spans, or introduce perturbation/ablation arms. Therefore these results
support reduced peripheral weighting and observed representation stability, not
a complete demonstration of invariance to boundary changes or perceptual superiority.

Central helps geometric exclusion in some cases, but does not reliably reduce the
three known sensitivity patterns and loses expanded native performance. Acoustic
helps the early/pre-vowel and quiet-tail patterns, preserves Google 买 coverage,
and is the most promising overall candidate; the frication result and persistent
head disagreements remain unresolved. Consequently the selected outcome is
**NO_CLEAR_WINNER**, not READY, DISTRIBUTION_MISMATCH, or UNIFORM_BEST.

Exact next experiment (recommendation only; not performed): One confirmatory offline frozen-head experiment: retain the exact ACOUSTIC_WEIGHTED formula and Uniform comparator on the remaining 659 eligible native test IDs, plus a preregistered disjoint set of already frozen learner units. Before inference, seal exact IDs and one-frame left/right pooling contractions entirely inside each unchanged safe owner, applied symmetrically to both representations. Measure native recognition/coverage and within-item TV, argmax and head disagreement under those fixed perturbations. Keep encoder, heads, 60ms/3-frame rules and weights fixed; no parameter search, new recordings, integration or head refit.

Validation: 18 focused pooling tests pass, covering deterministic central selection
and earlier ties, acoustic-equation identity with existing diagnostics, nearest mapping,
normalization, effective_n, zero-weight abstention, frame/time minimums, ambiguous
ownership, neutral exclusion, native IDs, forbidden pitch/target/output fields,
manifest reconstruction and hashes, exact vector reconstruction, report-prefix
ordering, unique inference records, and frozen artifacts. Ruff passes on the new
modules/tests. No product/mobile suite or attribution audit was run.

Fresh layer-9 extraction reproduces all 256 historical native reference vectors
within **4.067e-07** absolute coordinate error;
uniform physical probabilities reproduce the ownership experiment within
**1.247e-07**. Differences are the
documented float64 weighted mean versus the archived float32 Torch mean.
The post-inference freeze verifies **727 files unchanged** and
the same git HEAD: model joblibs, pinned contracts/configuration, prior ownership,
frame-attribution and F0-independent artifacts, consumed audio, frozen releases,
research source and tracked API/mobile files. The encoder checkpoint hashes also
match the frozen lock. There was no retraining, calibration, classifier modification,
ownership change, Practice/UI/grading/sandhi/Azure timing change, commit, push or deploy.

Artifacts are additive under `data/generated/pooling-representation-v1/`:
`preregistration.json`, `preregistration-seal.json`, `native-control-ids.json`,
`evaluation-metadata.json`, `representation-manifest.json`,
`representation-manifest-seal.json`, `representations/*.npy`,
`pre-inference-inventory{,-seal}.json`, `pre-inference-report-seal.json`,
`inference-start.json`, `predictions.json`, `analysis-summary.json`,
`native-metrics.{json,csv}`, `physical-20-unit-comparison.csv`,
`six-diagnostic-cases.json`, `case-frame-weights.csv`, `pairwise-stability.csv`,
`expanded-pilot-comparison.csv`, `all-predictions.csv`, `coverage.csv`,
`effective-support.json`, `embedding-distribution.json`, `decision.json`,
`freeze-before.json`, `freeze-after.json`, and verification records.

Added source files: `perceptual_tone/pooling_representation.py`,
`perceptual_tone/pooling_experiment.py`, `perceptual_tone/pooling_analysis.py`,
`scripts/pooling_representation_report.py`, and `tests/test_pooling_representation.py`.
Added report: `pooling-representation-experiment-report.md`. Generated files are
gitignored by existing repository policy; none were force-added. Existing untracked
work from the previous experiments was preserved. **NOT READY for dev integration.**

