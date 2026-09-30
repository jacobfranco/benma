# Experiment 2: whole mean versus temporal thirds

**Temporal pooling did not improve fresh-speaker generalization in this frozen comparison.**
A scored 81/118 and B 78/118. Fresh B-A deltas are
accuracy -0.025423728813559254,
balanced accuracy -0.025574712643678166,
and macro F1 -0.01813117801617392.
The modest T3 gain (9/29 to 11/29) accompanies a substantial descriptive T2 recall
regression (19/29 to 15/29, -13.793103448275862 percentage points), concentrated
in 雲角 (5/10 to 2/10). B does not satisfy the protocol's promising-result rule.
No numerical definition of “major” was preregistered; these are observed sizes,
not a new pass/fail cutoff. The conclusion already follows from lower overall
performance, and the T2 tradeoff adds a material concern.

The primary evidence is the fresh 118-clip panel. Luilui is a known/inspected
stress set and has no role in selection. All three fresh contributors have
**UNKNOWN native status**. This is not a native-Mandarin benchmark. Labels are
lexical targets, not independently verified realized-tone labels.

## Execution integrity and fixed configuration

The required offline verifier passed before model access and at each stage;
all 118 local files and recorded hashes verified. The sealed manifest remains
`7e9ba24601a1199ad07f721e9ca9cb22ef5736095a0fdb2b44091aa143dce75d`. Corpus selection/acquisition was not repeated.

Baseline A reproduced Experiment 1 **exactly**, before B fitting and fresh opening:
all 435 development pooled vectors were bitwise equal; scaler mean/variance/scale,
coefficients/intercepts/classes, and all 49 validation probabilities had maximum
absolute difference 0. Predictions were identical. The predeclared absolute
numerical tolerance was 1e-10 (metric tolerance 1e-12), with no relaxation.
Authoritative artifact hashes and checks are in
[baseline-reproduction.json](baseline-reproduction.json).

Lock UTC: **2026-09-30T20:16:35.787153+00:00**. Lock SHA-256:
`ed96d9e35388b44a0f03dd7155a537913bd64cdf07609956ac532aca1b0d2c0d`. Git HEAD: `64ae7e17c92dac0b5db563ff56725fea784a4e3f`.
Fresh opening: `2026-09-30T20:16:50.887107+00:00`.
Stress opening: `2026-09-30T20:17:37.163935+00:00`, after the fresh
results were saved and reported to the user. No model implementation/configuration
changed after the lock or opening; no corrective rerun occurred. Reporting-only
code was added after evaluation, separately hashed in provenance.

Both arms use frozen `facebook/wav2vec2-base` revision `0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`,
CPU FP32, four Torch threads, eager attention, seed 20260929, deterministic
algorithms and layer 8. Each untrimmed clip is decoded by the unchanged FFmpeg
function to mono 16 kHz and normalized by the checkpoint processor. One unpadded
clip per forward, no encoder attention mask; all emitted frames are valid.

A retains the Experiment 1 mean arithmetic over every valid frame (768 features).
B concatenates the arithmetic means of `[0:N//3)`, `[N//3:(2*N)//3)` and
`[(2*N)//3:N)` in order (2,304 features). N<3 fails both arms. No interpolation,
padding, frame repetition, lexical/expected-tone/speaker/F0 input or augmentation.

Both primary heads use the same original 386 training clips (Wei Gao 326,
CanonNi 60), with train-only StandardScaler (population variance). Each head is
multinomial L2 logistic regression: C=0.1, lbfgs, no class weights,
fit_intercept=True, max_iter=3000, tol=1e-8, random_state=20260929, one BLAS thread.
A converged in 111 iterations; B in 132. No tuning, layer search or model search.
Levi, Luilui, fresh clips and OMPAL never entered fitting. Source diagnostic fits
use only named subsets of those original training rows and do not replace heads.

Compact [head-A.npz](head-A.npz) and [head-B.npz](head-B.npz) preserve fitted mean,
variance, scale, sample count, coefficients, intercepts and class order.
[lock.json](lock.json) records file hashes and canonical scaler/classifier array
hashes, complete configuration, dependencies, code hashes and development metrics.
The exact selected training rows are in [training-manifest.csv](training-manifest.csv).

## Reading the metrics

Values below preserve the saved Python floating-point representations. All
principal panels contain all four tones. Balanced accuracy is mean four-tone
recall; macro F1 is mean four-tone F1; undefined precision/F1 uses zero. T3-only
stress recall is reported separately, without inventing a four-tone balanced
accuracy for a single-tone subset. Raw maximum softmax is uncalibrated and no
confidence rejection/acceptance threshold is used. Predictions cover every clip.

## Development: Levi Highway (49)

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 49 | 49 | 0 |
| accuracy | 0.9591836734693877 | 0.9387755102040817 | -0.020408163265306034 |
| balanced_accuracy | 0.9464285714285714 | 0.9366883116883118 | -0.009740259740259605 |
| macro_f1 | 0.9557692307692308 | 0.9333333333333333 | -0.022435897435897467 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7 | 1.0 | 0.875 | 0.8571428571428571 | 1.0 | 0.9230769230769231 | 0.9333333333333333 |
| 2 | 11 | 1.0 | 1.0 | 1.0 | 0.8181818181818182 | 1.0 | 0.9 |
| 3 | 14 | 0.9285714285714286 | 0.9285714285714286 | 0.9285714285714286 | 0.9285714285714286 | 0.9285714285714286 | 0.9285714285714286 |
| 4 | 17 | 0.9444444444444444 | 0.9444444444444444 | 1.0 | 1.0 | 0.9714285714285714 | 0.9714285714285714 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[6, 0, 1, 0]                   [7, 0, 0, 0]
[0, 11, 0, 0]                  [1, 9, 1, 0]
[0, 0, 13, 1]                  [0, 0, 13, 1]
[0, 0, 0, 17]                  [0, 0, 0, 17]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 0 | 0.0 | 1 | 0.09090909090909091 |
| T3->T2 | 0 | 0.0 | 0 | 0.0 |
| T3->T4 | 1 | 0.07142857142857142 | 1 | 0.07142857142857142 |
| T4->T3 | 0 | 0.0 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=0, B=1; T3↔T4: A=1, B=1.

Paired correctness: A_only_correct=3; B_only_correct=2; both_correct=44; both_wrong=0.

## Fresh speakers: aggregate (118)

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 118 | 118 | 0 |
| accuracy | 0.6864406779661016 | 0.6610169491525424 | -0.025423728813559254 |
| balanced_accuracy | 0.6830459770114943 | 0.6574712643678161 | -0.025574712643678166 |
| macro_f1 | 0.6676944023718218 | 0.6495632243556478 | -0.01813117801617392 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 30 | 0.8125 | 0.8333333333333334 | 0.8666666666666667 | 0.8333333333333334 | 0.8387096774193549 | 0.8333333333333334 |
| 2 | 29 | 0.8260869565217391 | 0.8333333333333334 | 0.6551724137931034 | 0.5172413793103449 | 0.7307692307692307 | 0.6382978723404256 |
| 3 | 29 | 0.5625 | 0.6111111111111112 | 0.3103448275862069 | 0.3793103448275862 | 0.4 | 0.46808510638297873 |
| 4 | 30 | 0.574468085106383 | 0.5192307692307693 | 0.9 | 0.9 | 0.7012987012987013 | 0.6585365853658537 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[26, 0, 0, 4]                  [25, 0, 0, 5]
[4, 19, 4, 2]                  [3, 15, 5, 6]
[2, 4, 9, 14]                  [1, 3, 11, 14]
[0, 0, 3, 27]                  [1, 0, 2, 27]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 4 | 0.13793103448275862 | 5 | 0.1724137931034483 |
| T3->T2 | 4 | 0.13793103448275862 | 3 | 0.10344827586206896 |
| T3->T4 | 14 | 0.4827586206896552 | 14 | 0.4827586206896552 |
| T4->T3 | 3 | 0.1 | 2 | 0.06666666666666667 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=8, B=8; T3↔T4: A=17, B=16.

Paired correctness: A_only_correct=6; B_only_correct=3; both_correct=75; both_wrong=34.

## Fresh speaker: Jouketou

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 40 | 40 | 0 |
| accuracy | 0.825 | 0.85 | 0.025000000000000022 |
| balanced_accuracy | 0.825 | 0.8500000000000001 | 0.025000000000000133 |
| macro_f1 | 0.8285087719298245 | 0.849624060150376 | 0.02111528822055142 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | 1.0 | 0.9090909090909091 | 1.0 | 1.0 | 1.0 | 0.9523809523809523 |
| 2 | 10 | 1.0 | 1.0 | 0.9 | 0.9 | 0.9473684210526315 | 0.9473684210526315 |
| 3 | 10 | 0.6363636363636364 | 0.7272727272727273 | 0.7 | 0.8 | 0.6666666666666666 | 0.7619047619047619 |
| 4 | 10 | 0.7 | 0.7777777777777778 | 0.7 | 0.7 | 0.7 | 0.7368421052631579 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[10, 0, 0, 0]                  [10, 0, 0, 0]
[0, 9, 1, 0]                   [0, 9, 1, 0]
[0, 0, 7, 3]                   [0, 0, 8, 2]
[0, 0, 3, 7]                   [1, 0, 2, 7]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 1 | 0.1 | 1 | 0.1 |
| T3->T2 | 0 | 0.0 | 0 | 0.0 |
| T3->T4 | 3 | 0.3 | 2 | 0.2 |
| T4->T3 | 3 | 0.3 | 2 | 0.2 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=1, B=1; T3↔T4: A=6, B=4.

Paired correctness: A_only_correct=0; B_only_correct=1; both_correct=33; both_wrong=6.

## Fresh speaker: 雲角

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 40 | 40 | 0 |
| accuracy | 0.6 | 0.575 | -0.025000000000000022 |
| balanced_accuracy | 0.6 | 0.575 | -0.025000000000000022 |
| macro_f1 | 0.5676413255360624 | 0.5378420696772357 | -0.0297992558588267 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | 0.7777777777777778 | 0.8888888888888888 | 0.7 | 0.8 | 0.7368421052631579 | 0.8421052631578947 |
| 2 | 10 | 0.5555555555555556 | 0.4 | 0.5 | 0.2 | 0.5263157894736842 | 0.26666666666666666 |
| 3 | 10 | 0.4 | 0.42857142857142855 | 0.2 | 0.3 | 0.26666666666666666 | 0.35294117647058826 |
| 4 | 10 | 0.5882352941176471 | 0.5263157894736842 | 1.0 | 1.0 | 0.7407407407407407 | 0.6896551724137931 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[7, 0, 0, 3]                   [8, 0, 0, 2]
[1, 5, 3, 1]                   [1, 2, 4, 3]
[1, 4, 2, 3]                   [0, 3, 3, 4]
[0, 0, 0, 10]                  [0, 0, 0, 10]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 3 | 0.3 | 4 | 0.4 |
| T3->T2 | 4 | 0.4 | 3 | 0.3 |
| T3->T4 | 3 | 0.3 | 4 | 0.4 |
| T4->T3 | 0 | 0.0 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=7, B=7; T3↔T4: A=3, B=4.

Paired correctness: A_only_correct=3; B_only_correct=2; both_correct=21; both_wrong=14.

## Fresh speaker: Fake estate

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 38 | 38 | 0 |
| accuracy | 0.631578947368421 | 0.5526315789473685 | -0.07894736842105254 |
| balanced_accuracy | 0.6138888888888889 | 0.5361111111111111 | -0.07777777777777783 |
| macro_f1 | 0.5408902691511387 | 0.4759049773755656 | -0.0649852917755731 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | 0.6923076923076923 | 0.7 | 0.9 | 0.7 | 0.782608695652174 | 0.7 |
| 2 | 9 | 1.0 | 1.0 | 0.5555555555555556 | 0.4444444444444444 | 0.7142857142857143 | 0.6153846153846154 |
| 3 | 9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 4 | 10 | 0.5 | 0.4166666666666667 | 1.0 | 1.0 | 0.6666666666666666 | 0.5882352941176471 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[9, 0, 0, 1]                   [7, 0, 0, 3]
[3, 5, 0, 1]                   [2, 4, 0, 3]
[1, 0, 0, 8]                   [1, 0, 0, 8]
[0, 0, 0, 10]                  [0, 0, 0, 10]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 0 | 0.0 | 0 | 0.0 |
| T3->T2 | 0 | 0.0 | 0 | 0.0 |
| T3->T4 | 8 | 0.8888888888888888 | 8 | 0.8888888888888888 |
| T4->T3 | 0 | 0.0 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=0, B=0; T3↔T4: A=8, B=8.

Paired correctness: A_only_correct=3; B_only_correct=0; both_correct=21; both_wrong=14.

## Equal-speaker fresh means

| Metric | A | B |
| --- | --- | --- |
| accuracy | 0.6855263157894737 | 0.6592105263157895 |
| balanced_accuracy | 0.6796296296296296 | 0.6537037037037037 |
| macro_f1 | 0.6456801222056752 | 0.6211237024010591 |

B improves Jouketou by one correct clip, loses one on 雲角 and three on Fake estate. On Fake estate neither arm correctly classifies any of the nine T3 targets; eight are predicted T4 and one T1. Fake estate T1 recall falls from 9/10 to 7/10. Fresh T3→T4 errors remain 14/29 in both arms. The T3 gain does not resolve the primary T3/T4 failure pattern.

## Luilui: KNOWN / INSPECTED STRESS SET (60)

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 60 | 60 | 0 |
| accuracy | 0.7166666666666667 | 0.7 | -0.01666666666666672 |
| balanced_accuracy | 0.7075091575091574 | 0.6908424908424908 | -0.016666666666666607 |
| macro_f1 | 0.6610114873438857 | 0.6471593075573858 | -0.013852179786499885 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11 | 0.55 | 0.55 | 1.0 | 1.0 | 0.7096774193548387 | 0.7096774193548387 |
| 2 | 15 | 1.0 | 1.0 | 0.8666666666666667 | 0.8 | 0.9285714285714286 | 0.8888888888888888 |
| 3 | 13 | 1.0 | 1.0 | 0.15384615384615385 | 0.15384615384615385 | 0.26666666666666666 | 0.26666666666666666 |
| 4 | 21 | 0.68 | 0.6538461538461539 | 0.8095238095238095 | 0.8095238095238095 | 0.7391304347826086 | 0.723404255319149 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[11, 0, 0, 0]                  [11, 0, 0, 0]
[2, 13, 0, 0]                  [3, 12, 0, 0]
[3, 0, 2, 8]                   [2, 0, 2, 9]
[4, 0, 0, 17]                  [4, 0, 0, 17]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 0 | 0.0 | 0 | 0.0 |
| T3->T2 | 0 | 0.0 | 0 | 0.0 |
| T3->T4 | 8 | 0.6153846153846154 | 9 | 0.6923076923076923 |
| T4->T3 | 0 | 0.0 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=0, B=0; T3↔T4: A=8, B=9.

Paired correctness: A_only_correct=3; B_only_correct=2; both_correct=40; both_wrong=15.

## The 13 known Luilui T3 cases

Both arms get only 晚 and 表 correct: **2/13 = 0.15384615384615385 recall**. A predicts T1/T2/T3/T4 counts 3/0/2/8; B predicts 2/0/2/9. The only T3 label change is 我, T1→T4, still wrong. Full-set accuracy falls from 43/60 to 42/60. The same locked B head does not repair this inspected failure.

| Text | Pinyin | A prediction | A max softmax | A correct | B prediction | B max softmax | B correct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 你 | ni3 | 4 | 0.969003199361207 | False | 4 | 0.9814404101122337 | False |
| 我 | wo3 | 1 | 0.47856225273262276 | False | 4 | 0.5461120059902678 | False |
| 早 | zao3 | 4 | 0.9632611779863199 | False | 4 | 0.9190332803891654 | False |
| 晚 | wan3 | 3 | 0.8865126136543119 | True | 3 | 0.7067324954308105 | True |
| 五 | wu3 | 4 | 0.832169163203037 | False | 4 | 0.8721279109145698 | False |
| 想 | xiang3 | 1 | 0.5033670871136694 | False | 1 | 0.7280668333999949 | False |
| 表 | biao3 | 3 | 0.7545788225502328 | True | 3 | 0.5913259124482471 | True |
| 纸 | zhi3 | 1 | 0.9535472332821139 | False | 1 | 0.7000880720641269 | False |
| 买 | mai3 | 4 | 0.8593461301195562 | False | 4 | 0.8214576774737441 | False |
| 笔 | bi3 | 4 | 0.9489258948835089 | False | 4 | 0.9709171658847684 | False |
| 等 | deng3 | 4 | 0.9893760946256098 | False | 4 | 0.988629853940798 | False |
| 狗 | gou3 | 4 | 0.8455758164353191 | False | 4 | 0.8645375056047042 | False |
| 碗 | wan3 | 4 | 0.7379659927563229 | False | 4 | 0.9118191210021542 | False |

你、早、笔、等、五、买、狗 remain T4 errors in both arms; 纸 remains T1. 晚 and 表 remain correct but their max-softmax values decrease. Changes in uncalibrated softmax do not establish changes in actual pronunciation quality.

## Development diagnostic: train CanonNi_only

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 326 | 326 | 0 |
| accuracy | 0.6840490797546013 | 0.6809815950920245 | -0.0030674846625767804 |
| balanced_accuracy | 0.6683825173261794 | 0.6678568323521376 | -0.0005256849740418179 |
| macro_f1 | 0.6670967131174227 | 0.6556282498876763 | -0.011468463229746373 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 84 | 0.8059701492537313 | 0.9024390243902439 | 0.6428571428571429 | 0.44047619047619047 | 0.7152317880794702 | 0.592 |
| 2 | 71 | 0.8529411764705882 | 0.64 | 0.4084507042253521 | 0.4507042253521127 | 0.5523809523809524 | 0.5289256198347108 |
| 3 | 81 | 0.6585365853658537 | 0.6632653061224489 | 0.6666666666666666 | 0.8024691358024691 | 0.6625766871165644 | 0.7262569832402235 |
| 4 | 90 | 0.6013986013986014 | 0.6423357664233577 | 0.9555555555555556 | 0.9777777777777777 | 0.7381974248927039 | 0.775330396475771 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[54, 2, 11, 17]                [37, 16, 10, 21]
[11, 29, 14, 17]               [4, 32, 21, 14]
[1, 3, 54, 23]                 [0, 2, 65, 14]
[1, 0, 3, 86]                  [0, 0, 2, 88]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 14 | 0.19718309859154928 | 21 | 0.29577464788732394 |
| T3->T2 | 3 | 0.037037037037037035 | 2 | 0.024691358024691357 |
| T3->T4 | 23 | 0.2839506172839506 | 14 | 0.1728395061728395 |
| T4->T3 | 3 | 0.03333333333333333 | 2 | 0.022222222222222223 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=17, B=23; T3↔T4: A=26, B=16.

Paired correctness: A_only_correct=29; B_only_correct=28; both_correct=194; both_wrong=75.

## Development diagnostic: train CanonNi_only, evaluate Wei Gao

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 326 | 326 | 0 |
| accuracy | 0.6840490797546013 | 0.6809815950920245 | -0.0030674846625767804 |
| balanced_accuracy | 0.6683825173261794 | 0.6678568323521376 | -0.0005256849740418179 |
| macro_f1 | 0.6670967131174227 | 0.6556282498876763 | -0.011468463229746373 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 84 | 0.8059701492537313 | 0.9024390243902439 | 0.6428571428571429 | 0.44047619047619047 | 0.7152317880794702 | 0.592 |
| 2 | 71 | 0.8529411764705882 | 0.64 | 0.4084507042253521 | 0.4507042253521127 | 0.5523809523809524 | 0.5289256198347108 |
| 3 | 81 | 0.6585365853658537 | 0.6632653061224489 | 0.6666666666666666 | 0.8024691358024691 | 0.6625766871165644 | 0.7262569832402235 |
| 4 | 90 | 0.6013986013986014 | 0.6423357664233577 | 0.9555555555555556 | 0.9777777777777777 | 0.7381974248927039 | 0.775330396475771 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[54, 2, 11, 17]                [37, 16, 10, 21]
[11, 29, 14, 17]               [4, 32, 21, 14]
[1, 3, 54, 23]                 [0, 2, 65, 14]
[1, 0, 3, 86]                  [0, 0, 2, 88]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 14 | 0.19718309859154928 | 21 | 0.29577464788732394 |
| T3->T2 | 3 | 0.037037037037037035 | 2 | 0.024691358024691357 |
| T3->T4 | 23 | 0.2839506172839506 | 14 | 0.1728395061728395 |
| T4->T3 | 3 | 0.03333333333333333 | 2 | 0.022222222222222223 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=17, B=23; T3↔T4: A=26, B=16.

Paired correctness: A_only_correct=29; B_only_correct=28; both_correct=194; both_wrong=75.

## Development diagnostic: train Wei_Gao_only

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 109 | 109 | 0 |
| accuracy | 0.8256880733944955 | 0.8532110091743119 | 0.02752293577981646 |
| balanced_accuracy | 0.7980815578906777 | 0.8316783958353418 | 0.03359683794466406 |
| macro_f1 | 0.7984866828087167 | 0.8355864322969586 | 0.03709974948824191 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 22 | 0.9230769230769231 | 0.9333333333333333 | 0.5454545454545454 | 0.6363636363636364 | 0.6857142857142857 | 0.7567567567567568 |
| 2 | 23 | 0.6388888888888888 | 0.6764705882352942 | 1.0 | 1.0 | 0.7796610169491526 | 0.8070175438596491 |
| 3 | 23 | 0.9411764705882353 | 1.0 | 0.6956521739130435 | 0.7391304347826086 | 0.8 | 0.85 |
| 4 | 41 | 0.9069767441860465 | 0.9069767441860465 | 0.9512195121951219 | 0.9512195121951219 | 0.9285714285714286 | 0.9285714285714286 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[12, 9, 0, 1]                  [14, 7, 0, 1]
[0, 23, 0, 0]                  [0, 23, 0, 0]
[1, 3, 16, 3]                  [1, 2, 17, 3]
[0, 1, 1, 39]                  [0, 2, 0, 39]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 0 | 0.0 | 0 | 0.0 |
| T3->T2 | 3 | 0.13043478260869565 | 2 | 0.08695652173913043 |
| T3->T4 | 3 | 0.13043478260869565 | 3 | 0.13043478260869565 |
| T4->T3 | 1 | 0.024390243902439025 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=3, B=2; T3↔T4: A=4, B=3.

Paired correctness: A_only_correct=2; B_only_correct=5; both_correct=88; both_wrong=14.

## Development diagnostic: train Wei_Gao_only, evaluate CanonNi

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 60 | 60 | 0 |
| accuracy | 0.7666666666666667 | 0.8333333333333334 | 0.06666666666666665 |
| balanced_accuracy | 0.7236111111111111 | 0.795138888888889 | 0.07152777777777786 |
| macro_f1 | 0.7158317872603587 | 0.8008791208791209 | 0.08504733361876227 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 15 | 0.8888888888888888 | 0.9090909090909091 | 0.5333333333333333 | 0.6666666666666666 | 0.6666666666666666 | 0.7692307692307693 |
| 2 | 12 | 0.5714285714285714 | 0.6666666666666666 | 1.0 | 1.0 | 0.7272727272727273 | 0.8 |
| 3 | 9 | 0.8 | 1.0 | 0.4444444444444444 | 0.5555555555555556 | 0.5714285714285714 | 0.7142857142857143 |
| 4 | 24 | 0.88 | 0.8846153846153846 | 0.9166666666666666 | 0.9583333333333334 | 0.8979591836734694 | 0.92 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[8, 6, 0, 1]                   [10, 4, 0, 1]
[0, 12, 0, 0]                  [0, 12, 0, 0]
[1, 2, 4, 2]                   [1, 1, 5, 2]
[0, 1, 1, 22]                  [0, 1, 0, 23]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 0 | 0.0 | 0 | 0.0 |
| T3->T2 | 2 | 0.2222222222222222 | 1 | 0.1111111111111111 |
| T3->T4 | 2 | 0.2222222222222222 | 2 | 0.2222222222222222 |
| T4->T3 | 1 | 0.041666666666666664 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=2, B=1; T3↔T4: A=3, B=2.

Paired correctness: A_only_correct=0; B_only_correct=4; both_correct=46; both_wrong=10.

## Development diagnostic: train Wei_Gao_only, evaluate Levi Highway

| Metric | A | B | B - A |
| --- | --- | --- | --- |
| n | 49 | 49 | 0 |
| accuracy | 0.8979591836734694 | 0.8775510204081632 | -0.020408163265306145 |
| balanced_accuracy | 0.8571428571428571 | 0.8424369747899159 | -0.014705882352941235 |
| macro_f1 | 0.866983016983017 | 0.8515852339381751 | -0.015397783044841962 |

| Tone | Support | A precision | B precision | A recall | B recall | A F1 | B F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7 | 1.0 | 1.0 | 0.5714285714285714 | 0.5714285714285714 | 0.7272727272727273 | 0.7272727272727273 |
| 2 | 11 | 0.7333333333333333 | 0.6875 | 1.0 | 1.0 | 0.8461538461538461 | 0.8148148148148148 |
| 3 | 14 | 1.0 | 1.0 | 0.8571428571428571 | 0.8571428571428571 | 0.9230769230769231 | 0.9230769230769231 |
| 4 | 17 | 0.9444444444444444 | 0.9411764705882353 | 1.0 | 0.9411764705882353 | 0.9714285714285714 | 0.9411764705882353 |

Confusion matrices: true rows / predicted columns, T1-T4.

```text
A                              B
[4, 3, 0, 0]                   [4, 3, 0, 0]
[0, 11, 0, 0]                  [0, 11, 0, 0]
[0, 1, 12, 1]                  [0, 1, 12, 1]
[0, 0, 0, 17]                  [0, 1, 0, 16]
```

| Directed confusion | A count | A rate | B count | B rate |
| --- | --- | --- | --- | --- |
| T2->T3 | 0 | 0.0 | 0 | 0.0 |
| T3->T2 | 1 | 0.07142857142857142 | 1 | 0.07142857142857142 |
| T3->T4 | 1 | 0.07142857142857142 | 1 | 0.07142857142857142 |
| T4->T3 | 0 | 0.0 | 0 | 0.0 |

Rates use true-tone support. Bidirectional T2↔T3 counts: A=1, B=1; T3↔T4: A=1, B=1.

Paired correctness: A_only_correct=2; B_only_correct=1; both_correct=42; both_wrong=4.

## Interpretation, limits and next experiment

The exact frozen three-bin representation has worse aggregate and equal-speaker
fresh point estimates. There is one small speaker gain and two speaker declines,
with a T2 recall regression and persistent T3→T4 errors. It is not promising under
the stated rule. This does not establish that all temporal representations fail,
or that this English-pretrained encoder cannot represent Mandarin tones.

The comparison changes both temporal representation and dimensionality (768 to
2,304); fixed C also changes effective regularization across representations.
Consequently it does not isolate temporal order as the sole causal factor.
Whole-clip thirds include recorded silence; they need not coincide with phonetic
onset/middle/offset. Recording conditions, source effects, lexical/realized-tone
mismatch and the chosen coarse partition are plausible explanations, not diagnosed
causes. No F0 analysis, relabeling, listening-based exclusion or alternative fit
was introduced to explain away this result.

Three convenience-sampled contributors cannot establish population performance.
Speaker independence is based on source-profile IDs, not verified biological
identity; exact-byte/PCM deduplication cannot rule out every edited duplicate.
There are no clip-independent significance claims or speaker-population confidence
intervals. UNKNOWN native status and lexical labels limit all tone-error claims.
All 118 clips were retained; the panel is now inspected and cannot be pristine
for later model choices. No aggregate combines development, fresh and stress data.

**Recommended next experiment:** preregister a fixed-head evaluation on a new,
larger speaker-disjoint panel with independent, prediction-blinded realized-tone
annotation, especially T2/T3/T4. Keep these A/B heads frozen; report lexical-target
and realized-tone agreement separately, with uncertainty/ambiguous labels handled
by a rule fixed before prediction access. This would distinguish label mismatch
from continued model error without tuning on this opened panel. It requires a
separate authorization and protocol; no new acquisition/annotation is performed
here. No production/API/mobile integration is supported by these findings.

## Validation and artifact scope

**120 tests pass:** 66 research/model unit tests (52 existing plus 14 new), and
54 existing seal/preflight pytest cases. New controls cover N=3-8 exact basis-vector
bin membership, 768/2,304 dimensions, N<3, frozen deterministic extraction,
training-only scaling, immutable settings, evaluation membership/speaker leakage,
seal-before-access, lock-before-extraction, exclusive opening receipts,
stress-after-fresh, paired row IDs/counts and metric conventions.

The initial broad unittest discovery could not import two API-side test modules
inside the ML-only virtualenv (missing pytest/sqlalchemy). The relevant model and
seal suites were then run in their existing intended environments; no dependencies
were installed or changed. The unrelated acoustic-forensics suite was not rerun.
New Python files pass Ruff check/format. Directory-wide Ruff still identifies the
pre-existing unrelated report.py:95 formatting/line-length issue, left unchanged.

[artifact-verification.json](artifact-verification.json) confirms execution order,
all prediction denominators, same A/B IDs, recomputed aggregate/per-speaker metrics,
probability/argmax/correctness consistency, original training-only scaler count,
unchanged locked source/parameters, and A's historical Luilui probability reproduction.
No hidden-state arrays are retained. Pooled vectors stay in the ignored local cache;
raw CC BY-SA 4.0 fresh audio remains local and uncommitted. The preflight manifest
retains file-level attribution/license evidence and original-byte hashes.

No model/configuration changed after locking; only reports/documentation were
added after results. No corpus repair/reselection, production integration,
staging, commit or push occurred. See [environment.md](environment.md),
[comparison.csv](comparison.csv), [provenance.json](provenance.json), and the
complete development/fresh/stress JSON and prediction CSVs alongside this report.
