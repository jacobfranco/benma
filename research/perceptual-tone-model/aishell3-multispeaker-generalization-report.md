# AISHELL-3 multi-speaker generalization — 2026-10-17

**Pass complete. Outcome: STRONGLY REPLICATED. Research only.**

Human spot-check adjudication, release and Experiment A were frozen before expanded-model training. No encoder, layer, context, pooling, classifier, C or grading threshold was selected from these tests.

## Human decisions and adjudication

The original 24-item export is preserved byte-for-byte: **22 final PASS / 2 CLIPPED**, and **23 whole-unit PASS / 1 BOTH**. The raw enums, notes, reviewer, timestamps, hashes and listening confirmations were ingested unchanged. Two uncertain final starts were quarantined. The whole-target outlier retains its explicit final PASS. No additional auditory judgments were fabricated; the assistant inspected alignment, exact sample exports and spectrograms.

| Example | Partition | Unit | Raw whole / final | Classification | Outcome |
| --- | --- | --- | --- | --- | --- |
| aishell3:SSB03230044:5 | validation | 一 yi1 | PASS / CLIPPED | UNCERTAIN_ACOUSTIC_START_OWNERSHIP | QUARANTINE_UNIT |
| aishell3:SSB03420076:12 | train | 与 yu3 | PASS / CLIPPED | UNCERTAIN_ACOUSTIC_START_OWNERSHIP | QUARANTINE_UNIT |
| aishell3:SSB05650015:10 | train | 不 bu4 | BOTH / PASS | TARGET_OWNED_FINAL_HUMAN_PASS | PASS_AS_IS |

### aishell3:SSB03230044:5

E: uncertain acoustic start ownership, with possible A (preceding-vowel tail). The beginning of the 480 ms /i/ interval shows continuing periodic energy from the /ow/ transition, followed by lower energy and a later stronger /i/ region. This is compatible with the developer's excess-start observation, but a spectrogram cannot independently certify read-unit identity. No target onset/medial is represented; no neighbor MFA phone or export offset is included. Relevant target clipping is not established; quarantine.

Actual-reading label **T1**; previous 州 zhou1; next 零 ling2. Whole interval [1.6, 2.08]; pooling [1.6, 2.08] (480 ms); context [1.35, 2.33]. Pooling starts at the nucleus; neighbor phones included: 0. Source sample bounds: [70560, 91728] at 44.1 kHz, half-open.

MFA phones: `i˥ 1.600–2.080`. Pooled phones: `i˥`.

Whole and final WAV byte-identical: **True**. No timestamp, phone inventory, padding, MFA or derivation changes.

### aishell3:SSB03420076:12

E: uncertain acoustic start ownership. Consecutive /y/ vowels yu2->yu3 are continuous in the spectrogram; MFA assigns 30 ms to preceding yu2 and 490 ms to target yu3. This does not independently establish their acoustic boundary. The human note suggests excess initial material, not missing target material. No onset, medial or neighboring MFA phone enters the pool. Coarticulation and an early MFA boundary cannot be distinguished confidently; quarantine.

Actual-reading label **T3**; previous 于 yu2; next 烟 yan1. Whole interval [3.23, 3.72]; pooling [3.23, 3.72] (490 ms); context [2.98, 3.97]. Pooling starts at the nucleus; neighbor phones included: 0. Source sample bounds: [142443, 164052] at 44.1 kHz, half-open.

MFA phones: `y˨˩˦ 3.230–3.720`. Pooled phones: `y˨˩˦`.

Whole and final WAV byte-identical: **True**. No timestamp, phone inventory, padding, MFA or derivation changes.

### aishell3:SSB05650015:10

PASS_AS_IS for tone-bearing use. Whole target is 90 ms /p-w/ onset plus 30 ms /u/ nucleus. Pooling excludes the onset and contains exactly the target-owned /u/, with no neighboring phone. Human explicitly passed this final. The whole-target BOTH finding remains a real playback objection; no reconstruction or export defect is found. Poor/fuzzy whole-unit acoustic boundaries do not override the intact structurally owned, human-passed final.

Actual-reading label **T4**; previous 家 jia1; next 敢 gan3. Whole interval [1.88, 2.0]; pooling [1.97, 2.0] (30 ms); context [1.63, 2.25]. Pooling starts at the nucleus; neighbor phones included: 0. Source sample bounds: [86877, 88200] at 44.1 kHz, half-open.

MFA phones: `pʷ 1.880–1.970 / u˥˩ 1.970–2.000`. Pooled phones: `u˥˩`.

Whole and final WAV byte-identical: **False**. No timestamp, phone inventory, padding, MFA or derivation changes.

### Corpus scope and gate

All 4,454 pre-adjudication primary units were covered by the structural integrity audit: **0 proven derivation/export defects**. 210 units share the single-phone whole=final structure; only the two flagged units have that structure with duration at least 480 ms. This is descriptive, not a new duration rejection rule. The complete MFA predecessor check finds 9 same-segment transitions. An append-only scope supplement corrects the earlier count of eight, which omitted the already quarantined 30 ms preceding yu2. It changes no adjudication, example membership or timestamp.

**QA gate satisfied:** 22 direct final PASS (including the whole-target outlier) plus two explicit quarantines. Both quarantines are outside TEST (one train T3 and one validation T1). There is no demonstrated systematic ownership defect; automatic timing accuracy remains a limitation.

## Acquisition and immutable release

Downloaded 227 individually selected publisher-mirror recordings, 119,687,476 audio bytes (119.69 MB), from **60 new verified speakers**. They are disjoint from all 16 historical pilot speakers: 76 verified speakers across both studies, 60 in this release. The pinned mirror revision is `f20d5db4a31fe779ef07bb1af4ea92da5c786622`; speaker metadata and an overlap recording match retained official-source bytes exactly. Source: [publisher mirror](https://huggingface.co/datasets/AISHELL/AISHELL-3/tree/f20d5db4a31fe779ef07bb1af4ea92da5c786622), cross-checked against retained [OpenSLR 93](https://www.openslr.org/93/) bytes. No full-corpus download. File URLs, receipts, byte counts, SHA-256 and PCM provenance are retained in the acquisition manifest. The full official archive checksum is unavailable for this bounded acquisition.

All 63,262 train transcript lines parsed. MFA 3.3.9 and Mandarin acoustic/dictionary 3.0.0 were reused. Twenty new dictionary-backed corrections resolve observed G2P failures using the pilot correction procedure; original corrections and corpus labels are unchanged. 227/227 utterances aligned. Automatic quarantine: 10 implausible read-unit durations and 1 extreme phone duration. Human adjudication adds 2 units, giving **13 total quarantines**.

Release **`aishell3-multispeaker-context-v2-20261017`**: **4,452 T1–T4 units + 163 neutral units**. Manifest SHA-256:

`e3a3a72c7eca5a6ee365469a00f0b6d436893c5d6b2972e27be9df2ccc69c44f`.

Release descriptor SHA-256: `3bb07638eb87fe470e51831bab1e99681bfe01482136ae7f11eb7886ecd1b315`. Final split SHA-256: `96c6ea82fc9e78aa3d8927e189538109f39cd6eb1ff036089f2c579169132e06`.

| Partition | Speakers | T1 | T2 | T3 | T4 | Primary | T5 retained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test | 12 | 218 | 203 | 167 | 327 | 915 | 32 |
| train | 36 | 579 | 652 | 521 | 885 | 2637 | 106 |
| validation | 12 | 190 | 209 | 182 | 319 | 900 | 25 |

**train:** SSB0149, SSB0193, SSB0200, SSB0241, SSB0246, SSB0267, SSB0309, SSB0315, SSB0338, SSB0342, SSB0366, SSB0375, SSB0385, SSB0393, SSB0395, SSB0415, SSB0427, SSB0434, SSB0435, SSB0482, SSB0502, SSB0544, SSB0565, SSB0578, SSB0588, SSB0623, SSB0629, SSB0631, SSB0666, SSB0668, SSB0710, SSB0737, SSB0748, SSB0751, SSB0758, SSB0760

**validation:** SSB0273, SSB0316, SSB0323, SSB0339, SSB0341, SSB0379, SSB0470, SSB0599, SSB0607, SSB0609, SSB0686, SSB0720

**test:** SSB0287, SSB0288, SSB0354, SSB0380, SSB0407, SSB0534, SSB0570, SSB0590, SSB0603, SSB0784, SSB0786, SSB0794

<details><summary>All 60 speakers: partition and tone counts</summary>

| Speaker | Partition | T1 | T2 | T3 | T4 | T5 |
| --- | --- | --- | --- | --- | --- | --- |
| SSB0149 | train | 23 | 22 | 17 | 17 | 1 |
| SSB0193 | train | 13 | 13 | 15 | 35 | 4 |
| SSB0200 | train | 23 | 20 | 14 | 25 | 4 |
| SSB0241 | train | 16 | 14 | 13 | 22 | 1 |
| SSB0246 | train | 8 | 16 | 15 | 26 | 2 |
| SSB0267 | train | 21 | 16 | 14 | 28 | 7 |
| SSB0273 | validation | 21 | 17 | 17 | 28 | 2 |
| SSB0287 | test | 27 | 14 | 17 | 28 | 1 |
| SSB0288 | test | 15 | 15 | 12 | 22 | 1 |
| SSB0309 | train | 23 | 15 | 13 | 26 | 4 |
| SSB0315 | train | 21 | 16 | 12 | 18 | 0 |
| SSB0316 | validation | 16 | 14 | 18 | 29 | 6 |
| SSB0323 | validation | 14 | 17 | 13 | 31 | 0 |
| SSB0338 | train | 13 | 27 | 12 | 29 | 2 |
| SSB0339 | validation | 14 | 24 | 15 | 23 | 2 |
| SSB0341 | validation | 15 | 24 | 17 | 20 | 1 |
| SSB0342 | train | 19 | 20 | 13 | 30 | 2 |
| SSB0354 | test | 16 | 16 | 14 | 32 | 3 |
| SSB0366 | train | 14 | 21 | 15 | 25 | 5 |
| SSB0375 | train | 20 | 19 | 14 | 23 | 4 |
| SSB0379 | validation | 16 | 14 | 12 | 24 | 3 |
| SSB0380 | test | 12 | 20 | 13 | 21 | 3 |
| SSB0385 | train | 17 | 17 | 14 | 16 | 3 |
| SSB0393 | train | 9 | 17 | 15 | 23 | 2 |
| SSB0395 | train | 18 | 22 | 17 | 28 | 5 |
| SSB0407 | test | 20 | 21 | 15 | 21 | 6 |
| SSB0415 | train | 23 | 18 | 17 | 25 | 3 |
| SSB0427 | train | 14 | 15 | 18 | 18 | 3 |
| SSB0434 | train | 19 | 17 | 14 | 33 | 1 |
| SSB0435 | train | 12 | 20 | 14 | 24 | 4 |
| SSB0470 | validation | 23 | 17 | 15 | 26 | 1 |
| SSB0482 | train | 12 | 20 | 17 | 17 | 2 |
| SSB0502 | train | 13 | 17 | 13 | 22 | 0 |
| SSB0534 | test | 17 | 17 | 14 | 26 | 0 |
| SSB0544 | train | 16 | 16 | 12 | 21 | 2 |
| SSB0565 | train | 13 | 23 | 16 | 24 | 5 |
| SSB0570 | test | 24 | 16 | 14 | 28 | 3 |
| SSB0578 | train | 19 | 16 | 13 | 18 | 7 |
| SSB0588 | train | 16 | 22 | 14 | 21 | 5 |
| SSB0590 | test | 18 | 16 | 16 | 32 | 6 |
| SSB0599 | validation | 15 | 15 | 13 | 23 | 2 |
| SSB0603 | test | 21 | 16 | 13 | 27 | 2 |
| SSB0607 | validation | 18 | 11 | 17 | 27 | 1 |
| SSB0609 | validation | 11 | 17 | 13 | 23 | 3 |
| SSB0623 | train | 16 | 15 | 14 | 29 | 4 |
| SSB0629 | train | 14 | 14 | 12 | 25 | 0 |
| SSB0631 | train | 22 | 20 | 15 | 28 | 4 |
| SSB0666 | train | 10 | 16 | 18 | 33 | 8 |
| SSB0668 | train | 15 | 19 | 12 | 30 | 3 |
| SSB0686 | validation | 12 | 23 | 14 | 30 | 2 |
| SSB0710 | train | 13 | 21 | 15 | 23 | 2 |
| SSB0720 | validation | 15 | 16 | 18 | 35 | 2 |
| SSB0737 | train | 13 | 13 | 17 | 26 | 1 |
| SSB0748 | train | 12 | 16 | 16 | 23 | 1 |
| SSB0751 | train | 15 | 19 | 14 | 28 | 2 |
| SSB0758 | train | 20 | 19 | 12 | 13 | 2 |
| SSB0760 | train | 14 | 21 | 15 | 33 | 1 |
| SSB0784 | test | 12 | 14 | 13 | 30 | 3 |
| SSB0786 | test | 19 | 15 | 14 | 34 | 3 |
| SSB0794 | test | 17 | 23 | 12 | 26 | 1 |

</details>

Test: 915 units / 12 speakers; 167 T3s across 12 speakers. Largest speaker share **9.40%**, largest T3 speaker share **10.18%**; effective test speakers 11.91. Counts range from 64 to 86. This fixes the pilot's 92.66% overall / 93.55% T3 single-speaker concentration.

## Frozen methods and chronology

Chinese HuBERT revision `fce0375452b1dd6c080ac3248d423d4d037bc831`, context ±250 ms, hidden layer 9, owned nucleus/coda frame-center mean pooling, unchanged 200-sample edge padding, balanced multinomial LR C=0.1. Median imputation and scaling fit on train only. Validation reports sanity metrics, with no search or train+validation refit. The existing cache extracts layers 6/9/12 in one forward pass; only the fixed layer 9 enters either primary model.

A sealed at `2026-10-18T02:26:45.342686+00:00`. B heads frozen at `2026-10-18T02:31:09.728186+00:00`. Final test seal at `2026-10-18T02:31:20.063279+00:00`. A never retrained. B and acoustic LR used only expanded TRAIN. Secondary acoustic LR keeps the pilot's C=1.0. WavLM is omitted to avoid a second full encoder extraction; its earlier context/layer6/C0.1 configuration remains unchanged. No external Benma recording probe.

Validation sanity accuracy: B 90.78%; acoustic LR 64.67%. No setting changed.

## Overall results

| Model | Coverage | Accuracy (covered) | Balanced accuracy | Macro F1 (covered) | Correct / all | T3 recall / all | T3→T4 | T3→T2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fixed acoustic LR | 100.00% | 64.26% | 65.79% | 64.30% | 64.26% | 66.47% | 24/167 (14.37%) | 25/167 (14.97%) |
| Frozen deterministic Benma | 42.62% | 46.15% | 39.16% | 38.10% | 19.67% | 8.98% | 64/167 (38.32%) | 1/167 (0.60%) |
| A: unchanged pilot HuBERT | 100.00% | 89.51% | 88.82% | 89.02% | 89.51% | 86.23% | 13/167 (7.78%) | 9/167 (5.39%) |
| B: expanded fixed HuBERT | 100.00% | 90.38% | 90.17% | 89.96% | 90.38% | 91.02% | 6/167 (3.59%) | 7/167 (4.19%) |

Benma abstains on **525/915**. Benma precision/F1 and the covered-recall column below condition on covered examples; recall/all and correct/all include abstentions in their denominators. Learned models cover all examples.

### Fixed acoustic LR

| Tone | n | Covered | Precision | Recall covered | Recall/all | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 218 | 218 | 65.31% | 73.39% | 73.39% | 69.11% |
| T2 | 203 | 203 | 65.58% | 69.46% | 69.46% | 67.46% |
| T3 | 167 | 167 | 53.88% | 66.47% | 66.47% | 59.52% |
| T4 | 327 | 327 | 70.68% | 53.82% | 53.82% | 61.11% |

Confusion rows=true and columns=predicted, ordered T1/T2/T3/T4; abstentions excluded:

| True / predicted | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 160 | 14 | 8 | 36 |
| T2 | 26 | 141 | 23 | 13 |
| T3 | 7 | 25 | 111 | 24 |
| T4 | 52 | 35 | 64 | 176 |

| Speaker | n | T1/T2/T3/T4 | Covered | Accuracy | Macro F1 | T3 correct/total | Confusions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SSB0287 | 86 | 27/14/17/28 | 86 | 69.77% | 69.06% | 13/17 | T1->T2: 5; T1->T3: 1; T1->T4: 2; T2->T1: 1; T2->T3: 2; T3->T2: 4; T4->T1: 3; T4->T2: 3; T4->T3: 5 |
| SSB0288 | 64 | 15/15/12/22 | 64 | 48.44% | 49.16% | 8/12 | T1->T3: 2; T1->T4: 7; T2->T1: 1; T2->T3: 3; T2->T4: 3; T3->T1: 1; T3->T2: 1; T3->T4: 2; T4->T1: 2; T4->T2: 5; T4->T3: 6 |
| SSB0354 | 78 | 16/16/14/32 | 78 | 69.23% | 69.28% | 9/14 | T1->T2: 1; T1->T4: 3; T2->T1: 3; T3->T2: 1; T3->T4: 4; T4->T1: 4; T4->T2: 3; T4->T3: 5 |
| SSB0380 | 66 | 12/20/13/21 | 66 | 63.64% | 64.67% | 10/13 | T1->T2: 1; T1->T4: 2; T2->T1: 5; T2->T3: 2; T3->T1: 1; T3->T2: 1; T3->T4: 1; T4->T1: 10; T4->T3: 1 |
| SSB0407 | 77 | 20/21/15/21 | 77 | 62.34% | 62.84% | 11/15 | T1->T2: 1; T1->T3: 2; T1->T4: 6; T2->T1: 1; T2->T3: 3; T2->T4: 5; T3->T2: 2; T3->T4: 2; T4->T2: 2; T4->T3: 5 |
| SSB0534 | 74 | 17/17/14/26 | 74 | 77.03% | 75.40% | 8/14 | T1->T4: 1; T2->T1: 2; T2->T3: 3; T2->T4: 1; T3->T2: 1; T3->T4: 5; T4->T1: 2; T4->T3: 2 |
| SSB0570 | 82 | 24/16/14/28 | 82 | 60.98% | 61.01% | 11/14 | T1->T2: 1; T1->T3: 1; T1->T4: 5; T2->T1: 2; T2->T3: 2; T2->T4: 2; T3->T1: 1; T3->T2: 1; T3->T4: 1; T4->T1: 3; T4->T2: 6; T4->T3: 7 |
| SSB0590 | 82 | 18/16/16/32 | 82 | 69.51% | 69.36% | 10/16 | T1->T2: 1; T1->T4: 2; T2->T1: 3; T3->T1: 1; T3->T2: 4; T3->T4: 1; T4->T1: 7; T4->T2: 2; T4->T3: 4 |
| SSB0603 | 77 | 21/16/13/27 | 77 | 57.14% | 56.75% | 7/13 | T1->T2: 3; T1->T4: 5; T2->T1: 1; T2->T3: 2; T3->T2: 5; T3->T4: 1; T4->T1: 3; T4->T2: 4; T4->T3: 9 |
| SSB0784 | 69 | 12/14/13/30 | 69 | 76.81% | 76.12% | 9/13 | T1->T4: 1; T2->T1: 2; T3->T1: 1; T3->T2: 2; T3->T4: 1; T4->T1: 2; T4->T2: 2; T4->T3: 5 |
| SSB0786 | 82 | 19/15/14/34 | 82 | 47.56% | 47.71% | 7/14 | T1->T2: 1; T1->T3: 2; T1->T4: 2; T2->T1: 2; T2->T3: 3; T2->T4: 2; T3->T1: 1; T3->T2: 2; T3->T4: 4; T4->T1: 11; T4->T2: 5; T4->T3: 8 |
| SSB0794 | 78 | 17/23/12/26 | 78 | 67.95% | 66.52% | 8/12 | T2->T1: 3; T2->T3: 3; T3->T1: 1; T3->T2: 1; T3->T4: 2; T4->T1: 5; T4->T2: 3; T4->T3: 7 |

Unweighted speaker accuracy: max **77.03%**, mean **64.20%**, median **65.79%**, min **47.56%**.

| T3 context | n | Correct | Recall/all | Predictions |
| --- | --- | --- | --- | --- |
| before_T1 | 37 | 27 | 72.97% | {'T1': 1, 'T2': 7, 'T3': 27, 'T4': 2} |
| before_T2 | 43 | 27 | 62.79% | {'T1': 1, 'T2': 7, 'T3': 27, 'T4': 8} |
| before_T3 | 2 | 1 | 50.00% | {'T1': 1, 'T3': 1} |
| before_T4 | 65 | 39 | 60.00% | {'T1': 4, 'T2': 11, 'T3': 39, 'T4': 11} |
| before_T5 | 7 | 6 | 85.71% | {'T3': 6, 'T4': 1} |
| phrase_final | 70 | 45 | 64.29% | {'T1': 2, 'T2': 10, 'T3': 45, 'T4': 13} |
| phrase_medial | 87 | 59 | 67.82% | {'T1': 3, 'T2': 15, 'T3': 59, 'T4': 10} |
| phrase_position_unknown | 10 | 7 | 70.00% | {'T1': 2, 'T3': 7, 'T4': 1} |
| utterance_final | 13 | 11 | 84.62% | {'T3': 11, 'T4': 2} |

| Confidence bin | n | Accuracy |
| --- | --- | --- |
| 0.25–0.4 | 127 | 44.09% |
| 0.4–0.5 | 176 | 50.57% |
| 0.5–0.6 | 163 | 57.06% |
| 0.6–0.7 | 130 | 62.31% |
| 0.7–0.8 | 124 | 72.58% |
| 0.8–0.9 | 122 | 88.52% |
| 0.9–1 | 73 | 97.26% |

High-confidence errors (max probability ≥0.8): **16**. These are reporting bins, not learner grading thresholds. Probabilities have not been calibrated.

| True tone | n | Confidence min/Q1/median/Q3/max |
| --- | --- | --- |
| T1 | 218 | 0.304/0.482/0.631/0.791/0.985 |
| T2 | 203 | 0.265/0.453/0.619/0.815/0.995 |
| T3 | 167 | 0.313/0.486/0.580/0.736/0.959 |
| T4 | 327 | 0.271/0.425/0.569/0.734/0.984 |

### Frozen deterministic Benma

| Tone | n | Covered | Precision | Recall covered | Recall/all | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 218 | 74 | 75.00% | 16.22% | 5.50% | 26.67% |
| T2 | 203 | 102 | 43.84% | 31.37% | 15.76% | 36.57% |
| T3 | 167 | 80 | 14.71% | 18.75% | 8.98% | 16.48% |
| T4 | 327 | 134 | 60.80% | 90.30% | 37.00% | 72.67% |

Confusion rows=true and columns=predicted, ordered T1/T2/T3/T4; abstentions excluded:

| True / predicted | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 12 | 35 | 18 | 9 |
| T2 | 2 | 32 | 63 | 5 |
| T3 | 0 | 1 | 15 | 64 |
| T4 | 2 | 5 | 6 | 121 |

| Speaker | n | T1/T2/T3/T4 | Covered | Accuracy | Macro F1 | T3 correct/total | Confusions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SSB0287 | 86 | 27/14/17/28 | 37 | 40.54% | 38.02% | 3/17 | T1->T2: 4; T1->T3: 5; T1->T4: 1; T1->abstain: 15; T2->T3: 5; T2->abstain: 7; T3->T4: 6; T3->abstain: 8; T4->T3: 1; T4->abstain: 19 |
| SSB0288 | 64 | 15/15/12/22 | 22 | 45.45% | 32.77% | 0/12 | T1->T4: 4; T1->abstain: 10; T2->T3: 6; T2->abstain: 8; T3->T4: 2; T3->abstain: 10; T4->abstain: 14 |
| SSB0354 | 78 | 16/16/14/32 | 40 | 52.50% | 40.82% | 0/14 | T1->T2: 5; T1->T4: 1; T1->abstain: 8; T2->T3: 5; T2->abstain: 6; T3->T4: 6; T3->abstain: 8; T4->T2: 1; T4->T3: 1; T4->abstain: 16 |
| SSB0380 | 66 | 12/20/13/21 | 22 | 27.27% | 22.40% | 1/13 | T1->T2: 5; T1->T3: 1; T1->abstain: 6; T2->T3: 6; T2->abstain: 14; T3->T4: 2; T3->abstain: 10; T4->T1: 1; T4->T2: 1; T4->abstain: 14 |
| SSB0407 | 77 | 20/21/15/21 | 33 | 42.42% | 40.40% | 1/15 | T1->T2: 2; T1->T3: 1; T1->abstain: 16; T2->T3: 4; T2->T4: 1; T2->abstain: 12; T3->T4: 11; T3->abstain: 3; T4->abstain: 13 |
| SSB0534 | 74 | 17/17/14/26 | 35 | 37.14% | 23.85% | 0/14 | T1->T2: 1; T1->T3: 4; T1->abstain: 12; T2->T3: 7; T2->T4: 2; T2->abstain: 6; T3->T4: 7; T3->abstain: 7; T4->T2: 1; T4->abstain: 14 |
| SSB0570 | 82 | 24/16/14/28 | 35 | 45.71% | 42.22% | 4/14 | T1->T2: 3; T1->T3: 2; T1->T4: 2; T1->abstain: 15; T2->T1: 1; T2->T3: 5; T2->abstain: 8; T3->T4: 5; T3->abstain: 5; T4->T3: 1; T4->abstain: 19 |
| SSB0590 | 82 | 18/16/16/32 | 40 | 45.00% | 35.75% | 3/16 | T1->T2: 8; T1->T3: 1; T1->abstain: 9; T2->T3: 5; T2->abstain: 7; T3->T4: 7; T3->abstain: 6; T4->T1: 1; T4->abstain: 20 |
| SSB0603 | 77 | 21/16/13/27 | 34 | 61.76% | 51.64% | 0/13 | T1->T2: 2; T1->abstain: 16; T2->T1: 1; T2->T3: 4; T2->abstain: 5; T3->T2: 1; T3->T4: 4; T3->abstain: 8; T4->T2: 1; T4->abstain: 14 |
| SSB0784 | 69 | 12/14/13/30 | 27 | 70.37% | 58.44% | 1/13 | T1->T2: 1; T1->abstain: 10; T2->T3: 4; T2->abstain: 7; T3->T4: 3; T3->abstain: 9; T4->abstain: 16 |
| SSB0786 | 82 | 19/15/14/34 | 26 | 50.00% | 22.35% | 1/14 | T1->T2: 2; T1->abstain: 17; T2->T3: 2; T2->abstain: 13; T3->T4: 6; T3->abstain: 7; T4->T2: 1; T4->T3: 2; T4->abstain: 19 |
| SSB0794 | 78 | 17/23/12/26 | 39 | 35.90% | 27.01% | 1/12 | T1->T2: 2; T1->T3: 4; T1->T4: 1; T1->abstain: 10; T2->T3: 10; T2->T4: 2; T2->abstain: 8; T3->T4: 5; T3->abstain: 6; T4->T3: 1; T4->abstain: 15 |

Unweighted speaker accuracy: max **70.37%**, mean **46.17%**, median **45.23%**, min **27.27%**.

| T3 context | n | Correct | Recall/all | Predictions |
| --- | --- | --- | --- | --- |
| before_T1 | 37 | 5 | 13.51% | {'T3': 5, 'T4': 12, 'abstain': 20} |
| before_T2 | 43 | 4 | 9.30% | {'T3': 4, 'T4': 20, 'abstain': 19} |
| before_T3 | 2 | 0 | 0.00% | {'T4': 1, 'abstain': 1} |
| before_T4 | 65 | 6 | 9.23% | {'T2': 1, 'T3': 6, 'T4': 23, 'abstain': 35} |
| before_T5 | 7 | 0 | 0.00% | {'T4': 6, 'abstain': 1} |
| phrase_final | 70 | 5 | 7.14% | {'T3': 5, 'T4': 27, 'abstain': 38} |
| phrase_medial | 87 | 9 | 10.34% | {'T2': 1, 'T3': 9, 'T4': 33, 'abstain': 44} |
| phrase_position_unknown | 10 | 1 | 10.00% | {'T3': 1, 'T4': 4, 'abstain': 5} |
| utterance_final | 13 | 0 | 0.00% | {'T4': 2, 'abstain': 11} |

### A: unchanged pilot HuBERT

| Tone | n | Covered | Precision | Recall covered | Recall/all | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 218 | 218 | 90.58% | 92.66% | 92.66% | 91.61% |
| T2 | 203 | 203 | 91.89% | 83.74% | 83.74% | 87.63% |
| T3 | 167 | 167 | 85.21% | 86.23% | 86.23% | 85.71% |
| T4 | 327 | 327 | 89.64% | 92.66% | 92.66% | 91.13% |

Confusion rows=true and columns=predicted, ordered T1/T2/T3/T4; abstentions excluded:

| True / predicted | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 202 | 2 | 0 | 14 |
| T2 | 17 | 170 | 8 | 8 |
| T3 | 1 | 9 | 144 | 13 |
| T4 | 3 | 4 | 17 | 303 |

| Speaker | n | T1/T2/T3/T4 | Covered | Accuracy | Macro F1 | T3 correct/total | Confusions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SSB0287 | 86 | 27/14/17/28 | 86 | 95.35% | 95.18% | 16/17 | T1->T4: 2; T2->T1: 1; T3->T2: 1 |
| SSB0288 | 64 | 15/15/12/22 | 64 | 81.25% | 80.42% | 9/12 | T1->T4: 4; T2->T1: 1; T2->T3: 2; T3->T1: 1; T3->T2: 1; T3->T4: 1; T4->T1: 1; T4->T3: 1 |
| SSB0354 | 78 | 16/16/14/32 | 78 | 97.44% | 97.55% | 14/14 | T1->T4: 1; T4->T3: 1 |
| SSB0380 | 66 | 12/20/13/21 | 66 | 83.33% | 82.46% | 10/13 | T1->T2: 1; T1->T4: 2; T2->T1: 2; T2->T3: 1; T2->T4: 1; T3->T4: 3; T4->T3: 1 |
| SSB0407 | 77 | 20/21/15/21 | 77 | 79.22% | 79.00% | 13/15 | T1->T4: 2; T2->T1: 6; T2->T4: 4; T3->T2: 1; T3->T4: 1; T4->T3: 2 |
| SSB0534 | 74 | 17/17/14/26 | 74 | 94.59% | 93.94% | 13/14 | T2->T1: 1; T2->T3: 1; T3->T2: 1; T4->T3: 1 |
| SSB0570 | 82 | 24/16/14/28 | 82 | 93.90% | 94.06% | 14/14 | T1->T4: 1; T2->T4: 1; T4->T2: 2; T4->T3: 1 |
| SSB0590 | 82 | 18/16/16/32 | 82 | 93.90% | 94.33% | 15/16 | T3->T4: 1; T4->T1: 1; T4->T3: 3 |
| SSB0603 | 77 | 21/16/13/27 | 77 | 88.31% | 85.58% | 8/13 | T2->T3: 1; T3->T2: 4; T3->T4: 1; T4->T2: 1; T4->T3: 2 |
| SSB0784 | 69 | 12/14/13/30 | 69 | 91.30% | 91.04% | 12/13 | T2->T3: 2; T3->T4: 1; T4->T1: 1; T4->T3: 2 |
| SSB0786 | 82 | 19/15/14/34 | 82 | 87.80% | 85.93% | 10/14 | T1->T2: 1; T2->T1: 2; T2->T4: 1; T3->T2: 1; T3->T4: 3; T4->T2: 1; T4->T3: 1 |
| SSB0794 | 78 | 17/23/12/26 | 78 | 84.62% | 83.90% | 10/12 | T1->T4: 2; T2->T1: 4; T2->T3: 1; T2->T4: 1; T3->T4: 2; T4->T3: 2 |

Unweighted speaker accuracy: max **97.44%**, mean **89.25%**, median **89.81%**, min **79.22%**.

| T3 context | n | Correct | Recall/all | Predictions |
| --- | --- | --- | --- | --- |
| before_T1 | 37 | 29 | 78.38% | {'T1': 1, 'T2': 1, 'T3': 29, 'T4': 6} |
| before_T2 | 43 | 40 | 93.02% | {'T3': 40, 'T4': 3} |
| before_T3 | 2 | 2 | 100.00% | {'T3': 2} |
| before_T4 | 65 | 57 | 87.69% | {'T2': 8, 'T3': 57} |
| before_T5 | 7 | 7 | 100.00% | {'T3': 7} |
| phrase_final | 70 | 59 | 84.29% | {'T2': 2, 'T3': 59, 'T4': 9} |
| phrase_medial | 87 | 77 | 88.51% | {'T1': 1, 'T2': 6, 'T3': 77, 'T4': 3} |
| phrase_position_unknown | 10 | 8 | 80.00% | {'T2': 1, 'T3': 8, 'T4': 1} |
| utterance_final | 13 | 9 | 69.23% | {'T3': 9, 'T4': 4} |

| Confidence bin | n | Accuracy |
| --- | --- | --- |
| 0.25–0.4 | 3 | 0.00% |
| 0.4–0.5 | 30 | 56.67% |
| 0.5–0.6 | 42 | 61.90% |
| 0.6–0.7 | 47 | 63.83% |
| 0.7–0.8 | 67 | 74.63% |
| 0.8–0.9 | 121 | 92.56% |
| 0.9–1 | 605 | 96.53% |

High-confidence errors (max probability ≥0.8): **30**. These are reporting bins, not learner grading thresholds. Probabilities have not been calibrated.

| True tone | n | Confidence min/Q1/median/Q3/max |
| --- | --- | --- |
| T1 | 218 | 0.429/0.886/0.973/0.993/0.999 |
| T2 | 203 | 0.338/0.772/0.935/0.981/1.000 |
| T3 | 167 | 0.439/0.858/0.960/0.993/1.000 |
| T4 | 327 | 0.405/0.855/0.959/0.990/1.000 |

Speaker cluster bootstrap: 2,000 replicates, 12 independent speakers, 95% percentile intervals. accuracy: 86.23%–92.75%; macro_f1: 85.63%–92.41%; t3_recall: 79.37%–92.35%.

### B: expanded fixed HuBERT

| Tone | n | Covered | Precision | Recall covered | Recall/all | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 218 | 218 | 93.75% | 89.45% | 89.45% | 91.55% |
| T2 | 203 | 203 | 91.33% | 88.18% | 88.18% | 89.72% |
| T3 | 167 | 167 | 82.16% | 91.02% | 91.02% | 86.36% |
| T4 | 327 | 327 | 92.33% | 92.05% | 92.05% | 92.19% |

Confusion rows=true and columns=predicted, ordered T1/T2/T3/T4; abstentions excluded:

| True / predicted | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 195 | 8 | 2 | 13 |
| T2 | 7 | 179 | 11 | 6 |
| T3 | 2 | 7 | 152 | 6 |
| T4 | 4 | 2 | 20 | 301 |

| Speaker | n | T1/T2/T3/T4 | Covered | Accuracy | Macro F1 | T3 correct/total | Confusions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SSB0287 | 86 | 27/14/17/28 | 86 | 94.19% | 93.23% | 16/17 | T1->T3: 1; T1->T4: 1; T2->T1: 1; T2->T3: 1; T3->T2: 1 |
| SSB0288 | 64 | 15/15/12/22 | 64 | 75.00% | 74.55% | 9/12 | T1->T3: 1; T1->T4: 5; T2->T3: 2; T2->T4: 1; T3->T1: 1; T3->T2: 1; T3->T4: 1; T4->T1: 2; T4->T3: 2 |
| SSB0354 | 78 | 16/16/14/32 | 78 | 93.59% | 92.82% | 14/14 | T2->T3: 3; T4->T3: 2 |
| SSB0380 | 66 | 12/20/13/21 | 66 | 86.36% | 85.78% | 10/13 | T2->T1: 1; T2->T3: 1; T3->T1: 1; T3->T4: 2; T4->T1: 1; T4->T2: 1; T4->T3: 2 |
| SSB0407 | 77 | 20/21/15/21 | 77 | 81.82% | 81.72% | 13/15 | T1->T2: 1; T1->T4: 2; T2->T1: 3; T2->T3: 1; T2->T4: 2; T3->T2: 2; T4->T3: 3 |
| SSB0534 | 74 | 17/17/14/26 | 74 | 93.24% | 93.31% | 14/14 | T2->T3: 1; T2->T4: 1; T4->T3: 3 |
| SSB0570 | 82 | 24/16/14/28 | 82 | 93.90% | 94.55% | 14/14 | T1->T4: 3; T2->T4: 1; T4->T3: 1 |
| SSB0590 | 82 | 18/16/16/32 | 82 | 92.68% | 92.07% | 14/16 | T1->T2: 2; T3->T2: 1; T3->T4: 1; T4->T3: 2 |
| SSB0603 | 77 | 21/16/13/27 | 77 | 97.40% | 96.85% | 12/13 | T3->T2: 1; T4->T3: 1 |
| SSB0784 | 69 | 12/14/13/30 | 69 | 98.55% | 98.71% | 13/13 | T4->T2: 1 |
| SSB0786 | 82 | 19/15/14/34 | 82 | 87.80% | 85.84% | 12/14 | T1->T2: 4; T2->T1: 1; T2->T3: 1; T3->T2: 1; T3->T4: 1; T4->T1: 1; T4->T3: 1 |
| SSB0794 | 78 | 17/23/12/26 | 78 | 87.18% | 86.67% | 11/12 | T1->T2: 1; T1->T4: 2; T2->T1: 1; T2->T3: 1; T2->T4: 1; T3->T4: 1; T4->T3: 3 |

Unweighted speaker accuracy: max **98.55%**, mean **90.14%**, median **92.96%**, min **75.00%**.

| T3 context | n | Correct | Recall/all | Predictions |
| --- | --- | --- | --- | --- |
| before_T1 | 37 | 31 | 83.78% | {'T1': 1, 'T2': 1, 'T3': 31, 'T4': 4} |
| before_T2 | 43 | 40 | 93.02% | {'T1': 1, 'T2': 2, 'T3': 40} |
| before_T3 | 2 | 2 | 100.00% | {'T3': 2} |
| before_T4 | 65 | 62 | 95.38% | {'T2': 3, 'T3': 62} |
| before_T5 | 7 | 7 | 100.00% | {'T3': 7} |
| phrase_final | 70 | 61 | 87.14% | {'T2': 4, 'T3': 61, 'T4': 5} |
| phrase_medial | 87 | 83 | 95.40% | {'T1': 2, 'T2': 2, 'T3': 83} |
| phrase_position_unknown | 10 | 8 | 80.00% | {'T2': 1, 'T3': 8, 'T4': 1} |
| utterance_final | 13 | 10 | 76.92% | {'T2': 1, 'T3': 10, 'T4': 2} |

| Confidence bin | n | Accuracy |
| --- | --- | --- |
| 0.25–0.4 | 3 | 0.00% |
| 0.4–0.5 | 11 | 0.00% |
| 0.5–0.6 | 23 | 47.83% |
| 0.6–0.7 | 31 | 51.61% |
| 0.7–0.8 | 33 | 75.76% |
| 0.8–0.9 | 54 | 83.33% |
| 0.9–1 | 760 | 96.05% |

High-confidence errors (max probability ≥0.8): **39**. These are reporting bins, not learner grading thresholds. Probabilities have not been calibrated.

| True tone | n | Confidence min/Q1/median/Q3/max |
| --- | --- | --- |
| T1 | 218 | 0.364/0.962/0.997/1.000/1.000 |
| T2 | 203 | 0.448/0.933/0.992/0.999/1.000 |
| T3 | 167 | 0.490/0.968/0.994/0.999/1.000 |
| T4 | 327 | 0.350/0.965/0.995/0.999/1.000 |

Speaker cluster bootstrap: 2,000 replicates, 12 independent speakers, 95% percentile intervals. accuracy: 86.90%–93.50%; macro_f1: 86.46%–93.08%; t3_recall: 86.34%–95.32%.

## Expanded-model error patterns

Descriptive only; no retuning or exclusions from these errors.

```json
{
  "confusion": {
    "T1->T2": 8,
    "T1->T3": 2,
    "T1->T4": 13,
    "T2->T1": 7,
    "T2->T3": 11,
    "T2->T4": 6,
    "T3->T1": 2,
    "T3->T2": 7,
    "T3->T4": 6,
    "T4->T1": 4,
    "T4->T2": 2,
    "T4->T3": 20
  },
  "corpus_pinyin": {
    "cai2": 1,
    "cheng2": 2,
    "chi2": 1,
    "da3": 1,
    "fang2": 1,
    "fen1": 1,
    "gai3": 1,
    "gan1": 1,
    "ge1": 1,
    "guan4": 1,
    "gunr4": 1,
    "guo2": 1,
    "han4": 1,
    "ji1": 3,
    "jia3": 1,
    "jian1": 3,
    "jiao4": 1,
    "juan1": 1,
    "jue2": 1,
    "lai2": 1,
    "li2": 1,
    "li3": 2,
    "li4": 1,
    "liang4": 2,
    "luo2": 1,
    "men2": 1,
    "mou3": 1,
    "mu2": 1,
    "nian2": 1,
    "pu2": 1,
    "qi2": 2,
    "qi4": 1,
    "qiang2": 1,
    "qu4": 1,
    "rou4": 1,
    "ruan3": 1,
    "ruo4": 1,
    "shang1": 1,
    "sheng3": 1,
    "shi2": 2,
    "shi3": 1,
    "shi4": 3,
    "shou3": 1,
    "shu4": 1,
    "si1": 1,
    "ta1": 1,
    "wan4": 1,
    "wang4": 1,
    "wei1": 1,
    "wei2": 1,
    "wen2": 1,
    "wu4": 3,
    "xi4": 1,
    "xin1": 1,
    "ye3": 1,
    "yi1": 1,
    "yi2": 1,
    "yi3": 1,
    "yi4": 1,
    "yin1": 1,
    "yu2": 1,
    "yue1": 1,
    "zhang3": 1,
    "zhe2": 1,
    "zhi1": 2,
    "zhi4": 1,
    "zhui1": 1,
    "zi1": 1,
    "zi3": 2,
    "zi4": 1,
    "zui4": 2,
    "zun1": 1
  },
  "final_class": {
    "diphthong": 12,
    "nasal": 26,
    "open": 49,
    "rhotic": 1
  },
  "high_confidence_at_least_0_8": {
    "False": 49,
    "True": 39
  },
  "low_confidence_below_0_5": {
    "False": 74,
    "True": 14
  },
  "nucleus": {
    "a": 15,
    "aj": 3,
    "aw": 1,
    "e": 8,
    "ej": 5,
    "i": 17,
    "o": 9,
    "ow": 3,
    "u": 5,
    "y": 2,
    "z̩": 5,
    "ə": 5,
    "ʐ̩": 10
  },
  "short_under_60ms": {
    "False": 75,
    "True": 13
  },
  "speaker_id": {
    "SSB0287": 5,
    "SSB0288": 16,
    "SSB0354": 5,
    "SSB0380": 9,
    "SSB0407": 14,
    "SSB0534": 5,
    "SSB0570": 5,
    "SSB0590": 6,
    "SSB0603": 2,
    "SSB0784": 1,
    "SSB0786": 10,
    "SSB0794": 10
  }
}
```

Complete error records, per-speaker metrics, confidence distributions, contextual breakdowns and bootstrap intervals are preserved in [the machine summary](reports/aishell3-multispeaker-summary.json). Phrase position is used only for the 214/227 utterances whose auxiliary prosody matches exactly; 13 mismatches remain unattached. Phrase/next-tone groups overlap and must not be summed.

## Old pilot comparison and interpretation

| Study | Primary units | Speakers | Test speakers | Test accuracy | Macro F1 | T3 recall |
| --- | --- | --- | --- | --- | --- | --- |
| Preserved pilot | 729 | 16 | 3 | 90.40% | 89.78% | 83.87% |
| A: old head, new speakers | 4452 | 60 | 12 | 89.51% | 89.02% | 86.23% |
| B: fixed method, expanded train | 4452 | 60 | 12 | 90.38% | 89.96% | 91.02% |

Pilot T3→T4 remains 2/31 and its manifest remains `8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f`. The historical report, model files, decisions, predictions and splits are unchanged.

A is 0.89 percentage points below the old 90.40% despite zero retraining. B is 90.38%, with T3 recall improved to 91.02%. Both learned models outperform Benma's covered accuracy for every test speaker as well as in aggregate. This supports strong replication of the learned advantage, not uniform speaker performance: B's lowest speaker is still 75.00%. A and B uncertainty intervals overlap; this pass does not establish a precise overall gain from the larger training set. B has 39 high-confidence errors versus A's 30, and lower T3 precision despite higher recall.

**Learned connected-speech tone recognition has replicated across a substantially more diverse held-out AISHELL-3 speaker set.**

**The next research bottleneck is learner-domain transfer rather than native connected-speech tone recognition.** The smallest next step is a separate, reviewed learner-domain dataset with legitimate nucleus/coda timing and realized-tone judgments, keeping this corpus test frozen.

## Limits, validation and production freeze

This is native connected-speech corpus-label prediction, not learner grading or native-listener acceptability. Sixty speakers were selected from the available pinned mirror, with pre-split tone coverage selection; this is not a probability sample of Mandarin speakers or natural tone prevalence. There are only 12 independent test speakers. Encoder pretraining exposure is unknown. Text-conditioned forced alignment and context/segment cues remain potential sources of information beyond pure tone acoustics. Same-corpus lexical/prosodic regularities, offline future context, sparse per-speaker T3 denominators, no T5 classifier, uncalibrated confidence and no learner-domain evaluation limit transfer claims. Structural ownership checks do not prove every acoustic boundary; the two uncertain human findings were excluded without pretending to resolve their sound identity.

Validation:

```json
{
  "63_example_replay_byte_identical": true,
  "browser_audio_decodes": 96,
  "browser_export_import_passed": true,
  "commits_pushes_deploys": 0,
  "frozen_baseline": {
    "commit": "eaf9c4343b0b35f3a5572864fc9f4fc8e17e2a98",
    "manifest_sha256": "23177e44e58a3f7c991ee51ac5b4677899ddd71f5a6ef73ecf47a8213d59a52e",
    "verified_files": 413
  },
  "git_diff_check": "passed",
  "human_browser_answers_fabricated": 0,
  "node_passed": true,
  "node_tests": 3,
  "preflight": {
    "encoder_frame_geometry": {
      "config_sha256": "f6bd1bdef239518d022edcef31243acf344a2afa33d5428e16f221cac09cbcd0",
      "edge_padding": 200,
      "maximum_owned_frames": 25,
      "minimum_owned_frames": 1
    },
    "frozen_candidate_manifest_sha256": "3cfcb2e9d22b29cbe6dfc639f3033506ca315b021e042d32e56ba7384dcc4466",
    "history": {
      "historical_files": 11719,
      "pilot_manifest_sha256": "8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f"
    },
    "human_qa_inferred": false,
    "label_mutation_checks": 4617,
    "model_inference": false,
    "qa_items_bound_to_candidates": 24,
    "resampled_context_and_pool_checks": 9234,
    "source_derivatives_verified": 13851,
    "speaker_provenance_records_verified": 60,
    "status": "PASS_PRE_EVALUATION_INTEGRITY",
    "training": false,
    "utterance_audio_and_alignments": 227
  },
  "production_changes": false,
  "python_passed": true,
  "python_tests": 91,
  "reproduction": {
    "cache_entries_verified": 4452,
    "cache_repeat_exact": true,
    "canonical_audio_entries": 227,
    "configuration_searches": 0,
    "experiment_A_sealed_before_B": "FROZEN_OLD_MODEL_NEW_SPEAKERS_NO_RETRAINING",
    "fresh_embedding_max_delta": 0.0,
    "history": {
      "historical_files": 11719,
      "pilot_manifest_sha256": "8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f"
    },
    "models": {
      "acoustic_LR": {
        "model_sha256": "91c3fd6223bc44f856e976d707953b566c77e59dbcce7a4088bb47d6dc8576aa",
        "reload_max_probability_delta": 0.0,
        "seeded_refit_max_probability_delta": 0.0
      },
      "experiment_A": {
        "model_sha256": "c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9",
        "reload_max_probability_delta": 0.0
      },
      "experiment_B": {
        "model_sha256": "b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b",
        "reload_max_probability_delta": 0.0,
        "seeded_refit_max_probability_delta": 0.0
      }
    },
    "new_results_selected": false,
    "status": "PASS",
    "temporary_cache_corruption_rejected": true,
    "tolerances": {
      "fresh_embedding": 1e-06,
      "reload": 1e-12,
      "rtol": 0,
      "seeded_refit": 1e-10
    }
  },
  "staged_files": [],
  "tracked_files_modified": [],
  "untracked_research_files_whitespace_check": "passed"
}
```

All 413 frozen deterministic baseline hashes and the 63-example replay are unchanged. All 11,719 historical evidence files retain their hashes. Only new research files were added. No pronunciation UI, grading, F0, family scorer, production inference/API or deployment change. No commit, push or deployment.

## Reproduction commands

```sh
PY=benchmark/pronunciation_v2/.venv/bin/python
P=research/perceptual-tone-model
$PY $P/scripts/aishell3_multispeaker_verify.py
$PY $P/scripts/aishell3_multispeaker_train.py verify-a
# Completed experiments return verified sealed results; do not select new configurations.
$PY $P/scripts/aishell3_multispeaker_train.py experiment-a
$PY $P/scripts/aishell3_multispeaker_train.py experiment-b
$PY $P/scripts/aishell3_multispeaker_reproduce.py
```
