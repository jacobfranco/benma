# Confirmatory pooling generalization and perturbation stability replay

**PROMISING_NOT_READY — ACOUSTIC_WEIGHTING PROMISING BUT NOT YET READY. NOT READY for dev integration.**

Independent native recognition and mean perturbation stability reproduce the acoustic advantage. This is not full confirmation for integration: concentrated right-edge failures, residual physical frication disagreement, and worse head agreement on the small independent natural learner set remain unresolved. No head-only refit is justified yet.

## Frozen scope and dataset composition

All **659** remaining eligible test IDs are included, without resampling: the exact 915-ID eligible frozen release minus the prior sealed 256. The intersection is empty and the union recovers all 915. The 659 units cover **12 held-out speakers**, disjoint from both heads' training speakers; tone counts are **T1 154, T2 139, T3 103, T4 263**. 'Independent' here means excluded from the 256-item pooling control, not never used in the historical frozen-head test evaluation. Speakers and recordings can overlap the earlier test subset; this is item-disjoint confirmation, not a new speaker cohort.

Also replayed: the original **20 physical units** (three learner takes plus Google playback) and **27 disjoint frozen learner units**: 16 accepted natural units from S01/S02/S03 and 11 accepted diagnostic units from S13 and the documented U-shape recording. All five learner source recordings have decoded PCM identities disjoint from the four physical recordings. Selection uses existing accepted provenance and boundaries, never expected tones, grades, characters, outputs, or acoustic outcomes. Unknown-provenance and quarantined units remain excluded. No learner realized-tone gold exists; no learner accuracy is computed.

The release contains additional unknown-provenance accepted material; it was not promoted into a new learner benchmark. The existing accepted natural/diagnostic strata are sufficient disjoint material. Exact IDs, source references, PCM hashes and exclusion proof are in `native-ids.json`, `prior-256-exclusion-proof.json`, and `disjoint-learner-ids.json`.

## Exact unchanged definitions and perturbations

UNIFORM_SAFE_OWNER takes the float64 uniform mean of every eligible encoder frame in the frozen owner. ACOUSTIC_WEIGHTED uses **RMS_i × (1 − high_band_fraction_i)**: uncentered 20 ms RMS; demeaned 20 ms symmetric Hann FFT; power at **≥3.4 kHz** divided by `max(total_power, 1e-24)`; 5 ms acoustic hop; nearest absolute timestamp mapping, earlier timestamp on ties. Negative RMS is clamped to zero and spectral fraction to [0,1], as in the sealed original. Weights normalize in float64 by their sum; sum ≤ float64.tiny abstains. No new exponent, floor, fallback, threshold, or effective-support rule. The original source file is byte-identical and is called directly.

BASE retains the eligible sequence. CONTRACT_LEFT removes exactly its first frame; CONTRACT_RIGHT removes exactly its last. A candidate needs ≥3 frames and ≥60 ms of contiguous frame-cell support clipped to the **unchanged owner boundaries**, with the original 1e-9-second arithmetic tolerance. Failed contractions are persisted as `perturbation_not_admissible`, without a vector. Kish effective_n = 1/sum(w²) is descriptive only. No spans expand, shift or change ownership. Physical ownership is the persisted GAP_AWARE result; native and accepted learner ownership use frozen MFA read units. Ambiguous take-2 买 remains ownership-abstained in all six conditions.

Only these two arms and three variants are candidates. CURRENT_REFERENCE is an unperturbed historical comparator: exact archived native layer-9 nucleus-coda vectors, or the existing physical/learner reference span in the same context. CENTRAL_HALF is excluded. HuBERT layer 9, audio normalization, 200-sample padding, head standardization, class mapping, weights and biases remain frozen. Pre-existing neutral compatibility is applied only after representation sealing; it never changes frame selection.

## Seal and chronology

Manifest SHA-256: **`d8ea363ed77ecab0a9d5cd664cc829e249a47cb14e1740a6772419f5334bfbd5`**.

Preregistration sealed at `2026-10-22T18:05:21.631704+00:00`; **4935** manifest rows sealed at `2026-10-22T18:07:12.689400+00:00`; inference-start recorded at `2026-10-22T18:07:41.198354+00:00` immediately before loading either classifier. The manifest contains 706 × 2 × 3 = 4,236 candidate records plus 699 historical references. It embeds pooled vectors and records IDs, dataset, speaker, native evaluation label, frozen owners/status, eligible and selected frame IDs/centers, RMS, high-band fractions, raw/normalized weights, support, effective_n and abstention reasons. Hidden artifacts and the complete manifest are hashed. Raw logits and probabilities are persisted.

All vectors and the manifest were reconstructed and verified before inference. Native re-extracted reference vectors match the frozen archive within **3.7e-07** absolute coordinate error; inference uses the exact archived reference vectors. This is float64 mean versus archived float32 mean, not an encoder change.

## Coverage

| Dataset | Arm | Variant | Intended | Representable | Head usable | Abstention reasons |
| --- | --- | --- | --- | --- | --- | --- |
| learner_diagnostic | Uniform | BASE | 11 | 11 | 11 | {} |
| learner_diagnostic | Uniform | LEFT | 11 | 11 | 11 | {} |
| learner_diagnostic | Uniform | RIGHT | 11 | 11 | 11 | {} |
| learner_diagnostic | Acoustic | BASE | 11 | 11 | 11 | {} |
| learner_diagnostic | Acoustic | LEFT | 11 | 11 | 11 | {} |
| learner_diagnostic | Acoustic | RIGHT | 11 | 11 | 11 | {} |
| learner_primary | Uniform | BASE | 16 | 15 | 14 | {"insufficient_60ms_support": 1} |
| learner_primary | Uniform | LEFT | 16 | 14 | 13 | {"perturbation_not_admissible": 2} |
| learner_primary | Uniform | RIGHT | 16 | 14 | 13 | {"perturbation_not_admissible": 2} |
| learner_primary | Acoustic | BASE | 16 | 15 | 14 | {"insufficient_60ms_support": 1} |
| learner_primary | Acoustic | LEFT | 16 | 14 | 13 | {"perturbation_not_admissible": 2} |
| learner_primary | Acoustic | RIGHT | 16 | 14 | 13 | {"perturbation_not_admissible": 2} |
| native | Uniform | BASE | 659 | 659 | 659 | {} |
| native | Uniform | LEFT | 659 | 659 | 659 | {} |
| native | Uniform | RIGHT | 659 | 659 | 659 | {} |
| native | Acoustic | BASE | 659 | 659 | 659 | {} |
| native | Acoustic | LEFT | 659 | 659 | 659 | {} |
| native | Acoustic | RIGHT | 659 | 659 | 659 | {} |
| physical | Uniform | BASE | 20 | 19 | 15 | {"ownership_ambiguous": 1} |
| physical | Uniform | LEFT | 20 | 19 | 15 | {"ownership_ambiguous": 1} |
| physical | Uniform | RIGHT | 20 | 19 | 15 | {"ownership_ambiguous": 1} |
| physical | Acoustic | BASE | 20 | 19 | 15 | {"ownership_ambiguous": 1} |
| physical | Acoustic | LEFT | 20 | 19 | 15 | {"ownership_ambiguous": 1} |
| physical | Acoustic | RIGHT | 20 | 19 | 15 | {"ownership_ambiguous": 1} |

Every native condition covers **659/659**; every native comparison therefore uses all 659 paired items. Physical coverage is 19/20 representations, 15/20 four-class outputs after four neutral exclusions. Learner natural coverage is 15/16 BASE and 14/16 contracted representations; head denominators are 14 and 13 after one neutral exclusion. One natural item fails BASE support, and two fail each contraction (including that item). Diagnostic learner coverage is 11/11 throughout. Failures remain in coverage and manifests.

## Native performance, every condition

Percentages below are on usable items. All denominators are 659; all-selected and mutually covered metrics coincide.

| Head | Arm | Variant | n | Accuracy | Balanced acc. | Macro F1 | T1 recall | T2 recall | T3 recall | T4 recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | Uniform | BASE | 659 | 88.77% | 88.23% | 87.78% | 82.47% | 92.81% | 86.41% | 91.25% |
| expanded | Uniform | LEFT | 659 | 88.77% | 88.15% | 87.77% | 82.47% | 92.09% | 86.41% | 91.63% |
| expanded | Uniform | RIGHT | 659 | 88.01% | 87.57% | 87.15% | 81.82% | 94.24% | 84.47% | 89.73% |
| expanded | Acoustic | BASE | 659 | 91.35% | 91.01% | 90.58% | 89.61% | 91.37% | 90.29% | 92.78% |
| expanded | Acoustic | LEFT | 659 | 91.65% | 91.35% | 90.89% | 89.61% | 91.37% | 91.26% | 93.16% |
| expanded | Acoustic | RIGHT | 659 | 90.59% | 90.36% | 89.92% | 88.31% | 93.53% | 88.35% | 91.25% |
| expanded | Reference | BASE | 659 | 90.14% | 89.79% | 89.46% | 87.66% | 89.21% | 90.29% | 92.02% |
| pilot | Uniform | BASE | 659 | 88.92% | 87.30% | 87.93% | 87.01% | 86.33% | 81.55% | 94.30% |
| pilot | Uniform | LEFT | 659 | 89.07% | 87.67% | 88.02% | 87.66% | 85.61% | 83.50% | 93.92% |
| pilot | Uniform | RIGHT | 659 | 88.32% | 86.77% | 87.22% | 87.01% | 86.33% | 80.58% | 93.16% |
| pilot | Acoustic | BASE | 659 | 91.35% | 90.09% | 90.48% | 94.16% | 87.05% | 84.47% | 94.68% |
| pilot | Acoustic | LEFT | 659 | 91.50% | 90.18% | 90.61% | 94.16% | 87.05% | 84.47% | 95.06% |
| pilot | Acoustic | RIGHT | 659 | 91.20% | 90.04% | 90.27% | 95.45% | 86.33% | 84.47% | 93.92% |
| pilot | Reference | BASE | 659 | 89.38% | 88.50% | 88.39% | 92.86% | 82.73% | 86.41% | 92.02% |

BASE acoustic is 602/659 correct under each head, versus uniform 585/659 expanded and 586/659 pilot; reference is 594/659 expanded and 589/659 pilot. Acoustic minus uniform is **+2.58 pp expanded, +2.43 pp pilot**; acoustic minus reference is **+1.21 pp expanded, +1.97 pp pilot**.

The preregistered 10,000-replicate paired speaker-cluster bootstrap (seed 20261022) gives 95% percentile intervals of **[+1.24,+3.94] pp expanded** and **[+1.32,+3.63] pp pilot** for acoustic minus uniform. Paired acoustic-only/uniform-only correct counts are **22/5** and **21/5**. Against reference, acoustic-only/reference-only counts are **17/9** and **20/7**; intervals are **[−0.16,+2.44] pp** and **[+0.29,+4.05] pp**. These 12-speaker descriptive intervals support reproducibility of the direction, not proof of equivalence, population-wide superiority, or perceptual correctness. No significance search or numerical readiness threshold was introduced.

BASE acoustic-minus-uniform recall changes (T1/T2/T3/T4) are **+7.14/−1.44/+3.88/+1.52 pp expanded** and **+7.14/+0.72/+2.91/+0.38 pp pilot**. Expanded T2 loses a net two correct items out of 139; this deserves visibility despite the overall gain. Against reference, pilot T3 loses two correct items out of 103 (−1.94 pp), while expanded T3 is unchanged. The sample cannot establish absence of a small tone-specific regression. Full pairwise balanced-accuracy, F1, recalls, counts and IDs are in `paired-native-metrics.json`.

Confusion matrices use true rows and predicted columns in T1/T2/T3/T4 order:

| Head | Arm | Variant | Confusion matrix |
| --- | --- | --- | --- |
| expanded | Uniform | BASE | [[127, 15, 1, 11], [3, 129, 6, 1], [1, 10, 89, 3], [5, 8, 10, 240]] |
| expanded | Uniform | LEFT | [[127, 13, 0, 14], [3, 128, 7, 1], [1, 9, 89, 4], [3, 6, 13, 241]] |
| expanded | Uniform | RIGHT | [[126, 15, 1, 12], [3, 131, 4, 1], [1, 11, 87, 4], [5, 12, 10, 236]] |
| expanded | Acoustic | BASE | [[138, 8, 0, 8], [4, 127, 7, 1], [1, 5, 93, 4], [5, 4, 10, 244]] |
| expanded | Acoustic | LEFT | [[138, 8, 0, 8], [4, 127, 7, 1], [1, 4, 94, 4], [4, 3, 11, 245]] |
| expanded | Acoustic | RIGHT | [[136, 9, 1, 8], [3, 130, 5, 1], [1, 5, 91, 6], [7, 6, 10, 240]] |
| expanded | Reference | BASE | [[135, 7, 0, 12], [4, 124, 5, 6], [1, 6, 93, 3], [3, 2, 16, 242]] |
| pilot | Uniform | BASE | [[134, 7, 1, 12], [10, 120, 3, 6], [1, 5, 84, 13], [1, 4, 10, 248]] |
| pilot | Uniform | LEFT | [[135, 6, 1, 12], [12, 119, 4, 4], [1, 6, 86, 10], [2, 3, 11, 247]] |
| pilot | Uniform | RIGHT | [[134, 8, 0, 12], [11, 120, 3, 5], [1, 7, 83, 12], [1, 5, 12, 245]] |
| pilot | Acoustic | BASE | [[145, 1, 0, 8], [10, 121, 2, 6], [2, 7, 87, 7], [1, 4, 9, 249]] |
| pilot | Acoustic | LEFT | [[145, 1, 0, 8], [10, 121, 2, 6], [1, 8, 87, 7], [2, 2, 9, 250]] |
| pilot | Acoustic | RIGHT | [[147, 1, 0, 6], [10, 120, 3, 6], [2, 7, 87, 7], [1, 6, 9, 247]] |
| pilot | Reference | BASE | [[143, 1, 0, 10], [13, 115, 6, 5], [1, 6, 89, 7], [3, 2, 16, 242]] |

## Perturbation stability

Each comparison uses only items usable in BASE and the indicated contraction. TV is half the L1 probability difference (0–1 scale); margins are top-one minus top-two. All margin changes are contraction minus BASE.

| Dataset | Head | Arm | Edge | n | Agreement | Flips | TV mean | TV median | TV max | Embedding cosine mean | L2 mean | Probability margin Δ | Logit margin Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| learner_diagnostic | expanded | Uniform | LEFT | 11 | 100.00% | 0 | 0.0263 | 0.0165 | 0.0665 | 0.9967 | 0.4072 | -0.0024 | 0.0472 |
| learner_diagnostic | expanded | Uniform | RIGHT | 11 | 100.00% | 0 | 0.0338 | 0.0214 | 0.0797 | 0.9971 | 0.4053 | 0.0167 | 0.2179 |
| learner_diagnostic | expanded | Acoustic | LEFT | 11 | 100.00% | 0 | 0.0198 | 0.0055 | 0.1003 | 0.9985 | 0.2600 | 0.0137 | 0.1168 |
| learner_diagnostic | expanded | Acoustic | RIGHT | 11 | 100.00% | 0 | 0.0362 | 0.0092 | 0.2060 | 0.9979 | 0.3451 | 0.0460 | 0.1484 |
| learner_diagnostic | pilot | Uniform | LEFT | 11 | 100.00% | 0 | 0.0188 | 0.0172 | 0.0419 | 0.9967 | 0.4072 | -0.0043 | 0.0103 |
| learner_diagnostic | pilot | Uniform | RIGHT | 11 | 100.00% | 0 | 0.0195 | 0.0158 | 0.0532 | 0.9971 | 0.4053 | 0.0025 | 0.0409 |
| learner_diagnostic | pilot | Acoustic | LEFT | 11 | 100.00% | 0 | 0.0136 | 0.0067 | 0.0627 | 0.9985 | 0.2600 | -0.0137 | -0.0297 |
| learner_diagnostic | pilot | Acoustic | RIGHT | 11 | 100.00% | 0 | 0.0114 | 0.0104 | 0.0269 | 0.9979 | 0.3451 | 0.0008 | 0.0467 |
| learner_primary | expanded | Uniform | LEFT | 13 | 92.31% | 1 | 0.0518 | 0.0218 | 0.1761 | 0.9928 | 0.6540 | -0.0104 | -0.0193 |
| learner_primary | expanded | Uniform | RIGHT | 13 | 92.31% | 1 | 0.0674 | 0.0529 | 0.2203 | 0.9922 | 0.6615 | -0.0235 | 0.1271 |
| learner_primary | expanded | Acoustic | LEFT | 13 | 100.00% | 0 | 0.0330 | 0.0186 | 0.1884 | 0.9955 | 0.4975 | -0.0050 | 0.1526 |
| learner_primary | expanded | Acoustic | RIGHT | 13 | 100.00% | 0 | 0.0500 | 0.0422 | 0.1555 | 0.9932 | 0.6319 | -0.0104 | 0.1766 |
| learner_primary | pilot | Uniform | LEFT | 13 | 84.62% | 2 | 0.0452 | 0.0359 | 0.1097 | 0.9928 | 0.6540 | 0.0582 | 0.2568 |
| learner_primary | pilot | Uniform | RIGHT | 13 | 92.31% | 1 | 0.0293 | 0.0264 | 0.1379 | 0.9922 | 0.6615 | 0.0160 | 0.0088 |
| learner_primary | pilot | Acoustic | LEFT | 13 | 100.00% | 0 | 0.0264 | 0.0226 | 0.0595 | 0.9955 | 0.4975 | 0.0297 | 0.2374 |
| learner_primary | pilot | Acoustic | RIGHT | 13 | 100.00% | 0 | 0.0237 | 0.0152 | 0.1082 | 0.9932 | 0.6319 | -0.0061 | -0.0293 |
| native | expanded | Uniform | LEFT | 659 | 96.81% | 21 | 0.0224 | 0.0054 | 0.3037 | 0.9941 | 0.6073 | 0.0221 | 0.4255 |
| native | expanded | Uniform | RIGHT | 659 | 97.72% | 15 | 0.0238 | 0.0047 | 0.3069 | 0.9927 | 0.6260 | 0.0090 | 0.1917 |
| native | expanded | Acoustic | LEFT | 659 | 99.24% | 5 | 0.0144 | 0.0010 | 0.3871 | 0.9961 | 0.4514 | 0.0147 | 0.3491 |
| native | expanded | Acoustic | RIGHT | 659 | 97.88% | 14 | 0.0208 | 0.0010 | 0.8382 | 0.9917 | 0.6189 | 0.0079 | 0.2468 |
| native | pilot | Uniform | LEFT | 659 | 98.33% | 11 | 0.0287 | 0.0192 | 0.2352 | 0.9941 | 0.6073 | 0.0310 | 0.2503 |
| native | pilot | Uniform | RIGHT | 659 | 98.63% | 9 | 0.0226 | 0.0144 | 0.2434 | 0.9927 | 0.6260 | 0.0114 | 0.1089 |
| native | pilot | Acoustic | LEFT | 659 | 99.09% | 6 | 0.0179 | 0.0069 | 0.2853 | 0.9961 | 0.4514 | 0.0198 | 0.2044 |
| native | pilot | Acoustic | RIGHT | 659 | 98.94% | 7 | 0.0176 | 0.0060 | 0.3505 | 0.9917 | 0.6189 | 0.0115 | 0.1589 |
| physical | expanded | Uniform | LEFT | 15 | 80.00% | 3 | 0.0424 | 0.0253 | 0.1906 | 0.9949 | 0.4821 | -0.0157 | 0.0453 |
| physical | expanded | Uniform | RIGHT | 15 | 93.33% | 1 | 0.0310 | 0.0254 | 0.0897 | 0.9954 | 0.4561 | 0.0218 | 0.2288 |
| physical | expanded | Acoustic | LEFT | 15 | 100.00% | 0 | 0.0162 | 0.0029 | 0.1003 | 0.9988 | 0.2209 | 0.0024 | 0.0584 |
| physical | expanded | Acoustic | RIGHT | 15 | 100.00% | 0 | 0.0169 | 0.0112 | 0.0759 | 0.9963 | 0.3533 | 0.0071 | 0.1340 |
| physical | pilot | Uniform | LEFT | 15 | 100.00% | 0 | 0.0252 | 0.0255 | 0.0522 | 0.9949 | 0.4821 | 0.0359 | 0.1587 |
| physical | pilot | Uniform | RIGHT | 15 | 100.00% | 0 | 0.0201 | 0.0184 | 0.0399 | 0.9954 | 0.4561 | 0.0133 | 0.1031 |
| physical | pilot | Acoustic | LEFT | 15 | 100.00% | 0 | 0.0071 | 0.0027 | 0.0407 | 0.9988 | 0.2209 | 0.0113 | 0.0906 |
| physical | pilot | Acoustic | RIGHT | 15 | 100.00% | 0 | 0.0085 | 0.0034 | 0.0441 | 0.9963 | 0.3533 | 0.0007 | 0.0632 |

Native acoustic weighting lowers mean TV in all four head/edge comparisons and lowers TV on **551/659 expanded-left, 546/659 expanded-right, 538/659 pilot-left, 515/659 pilot-right** items. Left flips fall **21→5 expanded, 11→6 pilot**; right flips fall **15→14 expanded, 9→7 pilot**. Embedding stability improves clearly on the left. On the right, acoustic mean cosine is **0.99169 versus uniform 0.99275**, despite slightly lower mean L2 and lower mean probability TV. Thus average probability stability is better, but the representation is not uniformly less boundary-sensitive.

## Per-tone perturbation stability

| Head | Arm | Edge | Tone | Admissible n | Agreement | Flips | Mean TV | Recall Δ pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | Uniform | LEFT | T1 | 154 | 96.10% | 6 | 0.0196 | +0.00 |
| expanded | Uniform | LEFT | T2 | 139 | 98.56% | 2 | 0.0199 | -0.72 |
| expanded | Uniform | LEFT | T3 | 103 | 96.12% | 4 | 0.0360 | +0.00 |
| expanded | Uniform | LEFT | T4 | 263 | 96.58% | 9 | 0.0200 | +0.38 |
| expanded | Uniform | RIGHT | T1 | 154 | 98.05% | 3 | 0.0244 | -0.65 |
| expanded | Uniform | RIGHT | T2 | 139 | 98.56% | 2 | 0.0209 | +1.44 |
| expanded | Uniform | RIGHT | T3 | 103 | 97.09% | 3 | 0.0315 | -1.94 |
| expanded | Uniform | RIGHT | T4 | 263 | 97.34% | 7 | 0.0220 | -1.52 |
| expanded | Acoustic | LEFT | T1 | 154 | 98.70% | 2 | 0.0112 | +0.00 |
| expanded | Acoustic | LEFT | T2 | 139 | 100.00% | 0 | 0.0160 | +0.00 |
| expanded | Acoustic | LEFT | T3 | 103 | 99.03% | 1 | 0.0264 | +0.97 |
| expanded | Acoustic | LEFT | T4 | 263 | 99.24% | 2 | 0.0108 | +0.38 |
| expanded | Acoustic | RIGHT | T1 | 154 | 98.05% | 3 | 0.0223 | -1.30 |
| expanded | Acoustic | RIGHT | T2 | 139 | 97.84% | 3 | 0.0207 | +2.16 |
| expanded | Acoustic | RIGHT | T3 | 103 | 96.12% | 4 | 0.0280 | -1.94 |
| expanded | Acoustic | RIGHT | T4 | 263 | 98.48% | 4 | 0.0171 | -1.52 |
| pilot | Uniform | LEFT | T1 | 154 | 98.05% | 3 | 0.0345 | +0.65 |
| pilot | Uniform | LEFT | T2 | 139 | 97.84% | 3 | 0.0278 | -0.72 |
| pilot | Uniform | LEFT | T3 | 103 | 97.09% | 3 | 0.0368 | +1.94 |
| pilot | Uniform | LEFT | T4 | 263 | 99.24% | 2 | 0.0227 | -0.38 |
| pilot | Uniform | RIGHT | T1 | 154 | 98.05% | 3 | 0.0249 | +0.00 |
| pilot | Uniform | RIGHT | T2 | 139 | 99.28% | 1 | 0.0232 | +0.00 |
| pilot | Uniform | RIGHT | T3 | 103 | 98.06% | 2 | 0.0260 | -0.97 |
| pilot | Uniform | RIGHT | T4 | 263 | 98.86% | 3 | 0.0196 | -1.14 |
| pilot | Acoustic | LEFT | T1 | 154 | 100.00% | 0 | 0.0139 | +0.00 |
| pilot | Acoustic | LEFT | T2 | 139 | 100.00% | 0 | 0.0194 | +0.00 |
| pilot | Acoustic | LEFT | T3 | 103 | 97.09% | 3 | 0.0277 | +0.00 |
| pilot | Acoustic | LEFT | T4 | 263 | 98.86% | 3 | 0.0156 | +0.38 |
| pilot | Acoustic | RIGHT | T1 | 154 | 98.70% | 2 | 0.0217 | +1.30 |
| pilot | Acoustic | RIGHT | T2 | 139 | 97.84% | 3 | 0.0207 | -0.72 |
| pilot | Acoustic | RIGHT | T3 | 103 | 100.00% | 0 | 0.0154 | +0.00 |
| pilot | Acoustic | RIGHT | T4 | 263 | 99.24% | 2 | 0.0145 | -0.76 |

Mean acoustic TV is lower than uniform in every native tone/head/edge cell. Flip counts do not improve in every cell: expanded-right T2/T3 have 3/4 acoustic flips versus 2/3 uniform; pilot-left T4 has 3 versus 2; pilot-right T2 has 3 versus 1. Expanded acoustic RIGHT lowers T1/T3/T4 recall by **1.30/1.94/1.52 pp** and raises T2 by 2.16 pp. These small counts and the worst-case tail prevent a blanket robustness claim.

## Left versus right, quiet tails and frication

There is no universal dominant edge under uniform: expanded mean TV is slightly higher at the right, pilot at the left; physical cases are more sensitive at the left. Under acoustic weighting, expanded native right mean TV is **0.02078 versus left 0.01443** (44% higher), while pilot edges are similar (**0.01762 right, 0.01792 left**). Acoustic's reduction is larger at the left: **35.6% expanded / 37.7% pilot**, versus **12.8% / 22.0%** at the right. This is aggregate evidence for reduced onset influence, not proof that every removed frame is pre-vowel.

Quiet-tail suppression is reproduced in take-3 买 and improves average native right sensitivity. However, a loud low-high-band edge can receive a large normalized acoustic weight. For **aishell3:SSB03540048:0 (T3)** the last frame carries **42.23%** of acoustic weight versus uniform 14.29%; removing it gives expanded **TV 0.83816**, versus uniform **0.17960**, and a correct-to-incorrect flip. Six frames and 119.97 ms remain: it is fully admissible, with effective_n 3.806 after contraction. This is not a hidden support failure. Two further expanded-right examples reach TV 0.55673 and 0.43391. The raw RMS and high-band fraction identify these as energetic, low-high-band edges, not quiet tails or evidence that a new effective_n threshold would solve the issue.

Frication remains unresolved: the take-3 想 high-band region spans multiple frames; a one-frame contraction leaves much of it and expanded/pilot T2/T1 disagreement survives both edges. The native worst right-edge events have very low high-band fractions, so frication is not the only source of instability. Continuous edge RMS/high-band versus TV-delta correlations and original-region weight masses are saved in `descriptive-audit.json`; these are descriptive acoustic proxies, not independent phonetic labels. Across the 659 native pairs, the correlation of relative edge RMS with acoustic-minus-uniform TV is +0.319/+0.231 expanded left/right and +0.499/+0.382 pilot; corresponding high-band correlations are weakly negative (-0.015/-0.027 and -0.110/-0.067). These associations support an energetic-edge concentration concern without assigning phonetic causes. In take-3 想 the originally identified strong-frication region retains 15.36% acoustic weight after LEFT (18.31% BASE), so its influence is broader than the single removed frame. No population-wide frication cure can be inferred from average stability.

## Six interpretation checks

| Case | Arm | Head | BASE→LEFT→RIGHT | Left TV | Right TV |
| --- | --- | --- | --- | --- | --- |
| take-1 这 | Uniform | expanded | T2 → T4 → T2 | 0.0696 | 0.0599 |
| take-1 这 | Uniform | pilot | T3 → T3 → T3 | 0.0267 | 0.0339 |
| take-1 这 | Acoustic | expanded | T3 → T3 → T3 | 0.0125 | 0.0234 |
| take-1 这 | Acoustic | pilot | T2 → T2 → T2 | 0.0100 | 0.0311 |
| take-2 这 | Uniform | expanded | T4 → T3 → T4 | 0.1906 | 0.0897 |
| take-2 这 | Uniform | pilot | T3 → T3 → T3 | 0.0522 | 0.0261 |
| take-2 这 | Acoustic | expanded | T3 → T3 → T3 | 0.0107 | 0.0759 |
| take-2 这 | Acoustic | pilot | T3 → T3 → T3 | 0.0027 | 0.0441 |
| take-3 想 | Uniform | expanded | T2 → T2 → T2 | 0.0546 | 0.0385 |
| take-3 想 | Uniform | pilot | T1 → T1 → T1 | 0.0473 | 0.0184 |
| take-3 想 | Acoustic | expanded | T2 → T2 → T2 | 0.0290 | 0.0256 |
| take-3 想 | Acoustic | pilot | T1 → T1 → T1 | 0.0237 | 0.0071 |
| take-3 买 | Uniform | expanded | T2 → T2 → T2 | 0.0669 | 0.0254 |
| take-3 买 | Uniform | pilot | T3 → T3 → T3 | 0.0040 | 0.0114 |
| take-3 买 | Acoustic | expanded | T3 → T3 → T3 | 0.0752 | 0.0112 |
| take-3 买 | Acoustic | pilot | T3 → T3 → T3 | 0.0023 | 0.0034 |
| google 买 | Uniform | expanded | T3 → T3 → T3 | 0.0020 | 0.0044 |
| google 买 | Uniform | pilot | T3 → T3 → T3 | 0.0006 | 0.0062 |
| google 买 | Acoustic | expanded | T3 → T3 → T3 | 0.0000 | 0.0000 |
| google 买 | Acoustic | pilot | T3 → T3 → T3 | 0.0006 | 0.0005 |
| take-3 我 | Uniform | expanded | T2 → T2 → T2 | 0.0669 | 0.0078 |
| take-3 我 | Uniform | pilot | T3 → T3 → T3 | 0.0279 | 0.0129 |
| take-3 我 | Acoustic | expanded | T2 → T2 → T2 | 0.0000 | 0.0016 |
| take-3 我 | Acoustic | pilot | T3 → T3 → T3 | 0.0000 | 0.0008 |

Take-1 这: left removal flips expanded uniform T2→T4; acoustic remains T3, with T3/T2 head disagreement. Take-2 这: expanded uniform flips T4→T3; acoustic left TV falls 0.19058→0.01067 and both acoustic heads stay T3. Take-3 想: no flips, but T2/T1 head disagreement persists and contraction does not remove the broader frication region. Take-3 买: right TV falls 0.02536→0.01118 expanded and 0.01137→0.00343 pilot; acoustic heads stay T3. Google 买: all six variants remain usable without F0 and both heads stay T3. Take-3 我: all variants retain expanded T2/pilot T3; neither is declared correct. These checks corroborate the previous attribution patterns without tuning.

## Expanded/pilot agreement

| Dataset | Arm | Variant | n | Agreement | Disagreements | Mean head TV |
| --- | --- | --- | --- | --- | --- | --- |
| learner_diagnostic | Uniform | BASE | 11 | 54.55% | 5 | 0.3991 |
| learner_diagnostic | Uniform | LEFT | 11 | 54.55% | 5 | 0.3866 |
| learner_diagnostic | Uniform | RIGHT | 11 | 54.55% | 5 | 0.4150 |
| learner_diagnostic | Acoustic | BASE | 11 | 54.55% | 5 | 0.3115 |
| learner_diagnostic | Acoustic | LEFT | 11 | 54.55% | 5 | 0.3158 |
| learner_diagnostic | Acoustic | RIGHT | 11 | 54.55% | 5 | 0.3333 |
| learner_diagnostic | Reference | BASE | 11 | 54.55% | 5 | 0.3810 |
| learner_primary | Uniform | BASE | 14 | 64.29% | 5 | 0.3614 |
| learner_primary | Uniform | LEFT | 13 | 61.54% | 5 | 0.3651 |
| learner_primary | Uniform | RIGHT | 13 | 69.23% | 4 | 0.3709 |
| learner_primary | Acoustic | BASE | 14 | 50.00% | 7 | 0.3924 |
| learner_primary | Acoustic | LEFT | 13 | 53.85% | 6 | 0.3983 |
| learner_primary | Acoustic | RIGHT | 13 | 53.85% | 6 | 0.3919 |
| learner_primary | Reference | BASE | 15 | 53.33% | 7 | 0.3819 |
| native | Uniform | BASE | 659 | 86.04% | 92 | 0.1934 |
| native | Uniform | LEFT | 659 | 88.16% | 78 | 0.1793 |
| native | Uniform | RIGHT | 659 | 85.43% | 96 | 0.1966 |
| native | Acoustic | BASE | 659 | 90.14% | 65 | 0.1463 |
| native | Acoustic | LEFT | 659 | 91.05% | 59 | 0.1361 |
| native | Acoustic | RIGHT | 659 | 89.07% | 72 | 0.1493 |
| native | Reference | BASE | 659 | 90.44% | 63 | 0.1373 |
| physical | Uniform | BASE | 15 | 53.33% | 7 | 0.3271 |
| physical | Uniform | LEFT | 15 | 53.33% | 7 | 0.3205 |
| physical | Uniform | RIGHT | 15 | 60.00% | 6 | 0.3194 |
| physical | Acoustic | BASE | 15 | 73.33% | 4 | 0.2974 |
| physical | Acoustic | LEFT | 15 | 73.33% | 4 | 0.3006 |
| physical | Acoustic | RIGHT | 15 | 73.33% | 4 | 0.2850 |
| physical | Reference | BASE | 13 | 69.23% | 4 | 0.2912 |

Native uniform→acoustic agreement is **86.04%→90.14% BASE**, **88.16%→91.05% LEFT**, **85.43%→89.07% RIGHT**. Acoustic still diverges somewhat more after RIGHT (65→72 disagreements); uniform changes 92→96. Physical agreement is 8/15→11/15 BASE, 8/15→11/15 LEFT, 9/15→11/15 RIGHT. Independent natural learner BASE agreement worsens **9/14→7/14**. On the 13 items admissible under contraction, acoustic agreement stays **7/13**; uniform changes **9/13→8/13 LEFT** and **9/13→9/13 RIGHT**. Thus contractions are stable under acoustic for these learners, yet the heads remain less concordant than under uniform. The diagnostic learner stratum stays 6/11 for every condition. Agreement is not correctness.

## Distribution shift

| Head | Arm | Variant | Standardized norm mean | Reference cosine mean | Reference L2 mean | Training-mean distance | Standardized reference distance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| expanded | Uniform | BASE | 24.4144 | 0.8831 | 2.6190 | 4.0314 | 14.5328 |
| expanded | Uniform | LEFT | 25.7484 | 0.8958 | 2.4496 | 4.2296 | 13.9449 |
| expanded | Uniform | RIGHT | 25.8351 | 0.8542 | 2.9359 | 4.2291 | 16.6321 |
| expanded | Acoustic | BASE | 26.6508 | 0.9282 | 1.9782 | 4.4313 | 11.5610 |
| expanded | Acoustic | LEFT | 27.7548 | 0.9340 | 1.8601 | 4.6155 | 11.1100 |
| expanded | Acoustic | RIGHT | 28.0004 | 0.9067 | 2.3237 | 4.6305 | 13.8171 |
| expanded | Reference | BASE | 27.5470 | 1.0000 | 0.0000 | 4.8058 | 0.0000 |
| pilot | Uniform | BASE | 25.2036 | 0.8831 | 2.6190 | 4.0876 | 14.7819 |
| pilot | Uniform | LEFT | 26.5462 | 0.8958 | 2.4496 | 4.2841 | 14.1805 |
| pilot | Uniform | RIGHT | 26.6190 | 0.8542 | 2.9359 | 4.2802 | 16.9212 |
| pilot | Acoustic | BASE | 27.5308 | 0.9282 | 1.9782 | 4.4944 | 11.7629 |
| pilot | Acoustic | LEFT | 28.6402 | 0.9340 | 1.8601 | 4.6764 | 11.3012 |
| pilot | Acoustic | RIGHT | 28.8747 | 0.9067 | 2.3237 | 4.6889 | 14.0628 |
| pilot | Reference | BASE | 28.4570 | 1.0000 | 0.0000 | 4.8703 | 0.0000 |

Acoustic BASE is closer to the archived reference than uniform: mean cosine **0.92825 versus 0.88312**, raw L2 **1.97817 versus 2.61899**. Standardized norms are closer to reference under both heads: expanded **26.65 acoustic / 24.41 uniform / 27.55 reference**; pilot **27.53 / 25.20 / 28.46**. Distances to each frozen training mean are reported in raw embedding units; these scalar checks do not establish equality of distributions or validate every outlier. No new distribution model was fitted.

## Effective support

| Variant | n | Min | 5th percentile | Median | 95th percentile | Max |
| --- | --- | --- | --- | --- | --- | --- |
| BASE | 659 | 3.1506 | 5.4956 | 8.7515 | 13.5945 | 19.7508 |
| LEFT | 659 | 3.1506 | 4.7967 | 8.1217 | 12.7786 | 19.6484 |
| RIGHT | 659 | 2.3470 | 4.6885 | 7.9683 | 13.1016 | 19.7014 |

| Variant | Extreme low-effective-n ID | effective_n | Frames | Support ms |
| --- | --- | --- | --- | --- |
| BASE | aishell3:SSB03800054:0 | 3.1506 | 5 | 100.00 |
| BASE | aishell3:SSB03540048:0 | 3.7592 | 7 | 130.00 |
| BASE | aishell3:SSB06030021:4 | 3.9167 | 10 | 199.97 |
| LEFT | aishell3:SSB03800054:0 | 3.1506 | 4 | 80.00 |
| LEFT | aishell3:SSB06030046:3 | 3.3840 | 7 | 140.00 |
| LEFT | aishell3:SSB04070025:5 | 3.6042 | 6 | 120.00 |
| RIGHT | aishell3:SSB03800054:0 | 2.3470 | 4 | 80.00 |
| RIGHT | aishell3:SSB06030021:4 | 2.9215 | 9 | 179.97 |
| RIGHT | aishell3:SSB02880104:6 | 3.4336 | 9 | 179.97 |

The minimum after RIGHT is **2.347**, which remains usable if geometric support passes. No effective_n threshold is introduced. The largest TV case does not have the minimum effective_n; concentration statistics alone do not resolve the observed failure.

## Disjoint learner stability

Coverage, left/right TV and flips, and head agreement are reported above separately for natural and diagnostic strata. On the 13 mutually usable natural units, acoustic has **zero flips under either edge or head**, versus uniform expanded 1/1 and pilot 2/1 left/right flips. Mean TV improves for all four natural head/edge comparisons. The 11 diagnostic units have no flips under either arm; expanded acoustic right mean TV is slightly worse (0.03619 versus 0.03377) with a 0.20601 maximum. These are small, correlated samples from one learner, not evidence of learner-tone accuracy.

| Learner set | Head | Variant | Paired n | Uniform-vs-acoustic TV mean | TV median | TV max |
| --- | --- | --- | --- | --- | --- | --- |
| learner_diagnostic | expanded | BASE | 11 | 0.1658 | 0.0743 | 0.5175 |
| learner_diagnostic | expanded | LEFT | 11 | 0.1600 | 0.0476 | 0.5284 |
| learner_diagnostic | expanded | RIGHT | 11 | 0.1558 | 0.0574 | 0.5479 |
| learner_diagnostic | pilot | BASE | 11 | 0.0634 | 0.0707 | 0.1317 |
| learner_diagnostic | pilot | LEFT | 11 | 0.0590 | 0.0608 | 0.1383 |
| learner_diagnostic | pilot | RIGHT | 11 | 0.0632 | 0.0620 | 0.1260 |
| learner_primary | expanded | BASE | 14 | 0.1326 | 0.0825 | 0.6350 |
| learner_primary | expanded | LEFT | 13 | 0.1339 | 0.0739 | 0.6727 |
| learner_primary | expanded | RIGHT | 13 | 0.1603 | 0.0831 | 0.6426 |
| learner_primary | pilot | BASE | 14 | 0.0614 | 0.0413 | 0.1865 |
| learner_primary | pilot | LEFT | 13 | 0.0461 | 0.0304 | 0.1653 |
| learner_primary | pilot | RIGHT | 13 | 0.0693 | 0.0598 | 0.2112 |

## Decision and exact next step

**ACOUSTIC_WEIGHTING PROMISING BUT NOT YET READY (PROMISING_NOT_READY).** Native preservation and the average structural advantage generalize beyond the prior 256. Uniform does not consistently win. Nevertheless, A's complete stability bar is not established: right-edge worst cases are substantially worse, a few per-tone cells gain flips, and independent natural learner head disagreement increases. This conclusion does not rely on a post-hoc cutoff.

**Head-only refit: not yet justified.** Independent average representation benefit is supported, but frozen-head mismatch is not isolated as the clear blocker. High normalized edge weight can change the embedding itself, and neither head supplies learner realization truth.

Preregister a bounded offline audit of the already-sealed largest right-edge changes and disjoint learner head disagreements, inspect frozen audio/boundaries and existing frame/logit contributions, and establish independent realization evidence before deciding whether a head-only refit addresses the blocker. Keep representation and heads frozen; no product integration.

## Tests, freeze and reproducibility

Focused tests cover exact 256/659 disjointness and full inclusion, deterministic ID ordering, one-frame contractions, 3-frame/60ms clipping, immutable owners, acoustic equation/source identity, poisoned F0/expected-tone/character/prediction inputs, vector reconstruction, manifest/hash reproducibility, seal-before-inference, neutral/ambiguous semantics, learner recording disjointness, output completeness, unchanged model/checkpoint and frozen reference hashes. Pre-inference: 14 tests, 13 passed and the prediction-only check skipped. Final: **33 focused pooling tests passed**, with no skips. Test transcript: `focused-tests.txt`.

Freeze-after verifies **2209 existing files unchanged**, including previous experiments, sources, audio, releases, both head joblibs, pinned configuration and tracked API/mobile files; git HEAD is unchanged. Actual encoder checkpoint hashes are verified separately by focused tests. The new source files pass Ruff. No product/mobile suite, F0 estimator, training, refit, threshold search, ownership recomputation, grading/UI/Practice modification, recording, commit, push or deployment occurred.

Reproduction phases (write-once artifacts intentionally refuse overwrite):

```sh
export PYTHONPATH=research/perceptual-tone-model
export OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=benchmark/pronunciation_v2/.venv/bin/python
$PY -m perceptual_tone.pooling_confirmatory preregister
$PY -m perceptual_tone.pooling_confirmatory construct
$PY -m unittest discover -s research/perceptual-tone-model/tests -p test_pooling_confirmatory.py -v
$PY -m perceptual_tone.pooling_confirmatory infer
$PY -m perceptual_tone.pooling_confirmatory_analysis
$PY research/perceptual-tone-model/scripts/pooling_confirmatory_report.py
```

Artifacts: `research/perceptual-tone-model/data/generated/pooling-confirmatory-v1/`. Preregistration and its seal; native IDs/exclusion proof; learner IDs/PCM proof; evaluation metadata; full representation manifest and seal; frame arrays; inference-start and raw probabilities/logits; coverage; native and paired metrics; per-tone performance/stability; item-level TV/cosine/L2/margins; expanded/pilot comparisons; distribution diagnostics; effective_n statistics and extremes; six cases; descriptive edge/region audit; decision; freeze-before/after; logs and focused tests. Tables are provided as JSON and CSV. Generated files remain gitignored under existing policy.

Added source/report files: `perceptual_tone/pooling_confirmatory.py`, `perceptual_tone/pooling_confirmatory_analysis.py`, `scripts/pooling_confirmatory_report.py`, `tests/test_pooling_confirmatory.py`, and `pooling-confirmatory-report.md`. Pre-existing untracked work remains intact. **NOT READY for dev integration.**
