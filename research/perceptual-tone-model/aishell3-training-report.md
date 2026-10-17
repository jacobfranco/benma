# AISHELL-3 first four-tone training pass — 2026-10-17

**CORE TONE-ML FEASIBILITY: CLEARLY PROMISING.** Learned connected-speech tone perception is materially more promising than the frozen deterministic Benma family scorer on this AISHELL-3 pilot.

**CURRENT PRODUCT GENERALIZATION: MIXED / UNPROVEN.** This pilot does not yet establish reliable generalization to Benma learner recordings. The natural learner-speech problem has not been solved.

**Hypothesis:** a small classifier on frozen speech representations can predict corpus numbered tones from audio on held-out speakers more accurately than the frozen acoustic-family scorer. The experiment tests this corpus-feasibility question separately from learner acceptability or product readiness.

The validation-selected model is frozen Chinese HuBERT layer 9, ±250 ms context, nucleus-plus-coda frame-center mean pooling, and balanced multinomial logistic regression with C=0.1. It gets 160/177 test units correct (90.40%), balanced accuracy 89.30%, and macro F1 89.78%. Benma covers 114/177 (64.41%), abstains on 63, and gets 33/114 covered units correct (28.95%). On exactly those same 114 covered units, HuBERT gets 102/114 (89.47%).

**Concentration is the main limitation:** SSB0043 supplies 164/177 units (92.66%), 29/31 T3s (93.55%), and all 17 HuBERT errors. The other two speakers contribute only 4 and 9 units. The gain is numerically dominated by SSB0043; this cannot establish robust across-speaker generalization. No unit-level confidence interval is presented as a substitute for independent speakers.

## Human QA and immutable release

Round 2: **18/18 PASS for both whole units and tone-bearing targets**. Schema, packet hash, item hashes, reviewer, timestamps, context/final listening flags, completeness and uniqueness passed. Round 1 remains 18 PASS / 8 non-PASS; its history was not rewritten. A nested-label summary bug in the ingestion adapter was fixed and regression-tested; there was no alignment-integrity mismatch.

Dataset version: `aishell3-nucleus-coda-context-v1-20261017`. Manifest SHA-256:

`8407533341c3707e4cc5ff3fc839859fbb72157ca3c381f10621df6bdd6cec0f`.

The release has 787 accepted units, 729 T1–T4 primary units, 58 preserved neutral units, and the original two >500 ms phone quarantines excluded. Original read-unit timing, reviewed nucleus/coda pooling, and short context remain separate. The old derived-span fields `eligible_for_training=false` and `ml_target_changed=false` are preserved pre-review evidence; release-level `primary_eligible` and the accepted representation govern this experiment. `training_started=false` records the release instant, not the current experiment status. The release was not rewritten after training.

[Release manifest and evidence](data/generated/aishell3/releases/aishell3-nucleus-coda-context-v1-20261017/release.json) pin source subset/audio hashes, speaker registry, MFA 3.3.9, Mandarin MFA model 3.0.0, dictionary/config, lexicon audits, parser/reconstruction source, decimal half-up half-open sample extraction, nucleus/coda policy, both original QA exports and normalized decisions, and quarantines.

| Partition | T1 | T2 | T3 | T4 | Primary | T5 retained |
| --- | --- | --- | --- | --- | --- | --- |
| train | 98 | 98 | 80 | 119 | 395 | 31 |
| validation | 35 | 35 | 36 | 51 | 157 | 13 |
| test | 42 | 50 | 31 | 54 | 177 | 14 |


- **test:** SSB0038, SSB0043, SSB0133
- **train:** SSB0009, SSB0011, SSB0012, SSB0016, SSB0018, SSB0057, SSB0073, SSB0080, SSB0122, SSB0139
- **validation:** SSB0005, SSB0033, SSB0112

Speaker, utterance, source PCM and all 2,361 target/context/final derivative-audio checks passed. Each primary partition contains all four classes. Split membership was not changed.

## Fixed protocol and feature inputs

All 729 annotation-mutation checks passed before classifier training. Encoders receive only verified audio reference/hash and three numeric spans. Acoustic features use a fixed 86-column numeric schema: duration, existing contour geometry, family-noise/clarity/scale, voicing/projection metrics, acoustic family support, F0 contour quantiles, and missingness indicators. Tone, numbered/marked pinyin, Hanzi, expected tone and contextual acceptable families never enter primary feature matrices. Labels are used only as training targets or scoring metadata. Transcript-conditioned forced alignment remains an upstream assumption; mutation tests do not prove its timing is free of every annotation influence.

[Protocol](models/generated/aishell3-first-four-tone-v1/protocol.json), [feature schema](models/generated/aishell3-first-four-tone-v1/acoustic-feature-schema.json), [selected models](models/generated/aishell3-first-four-tone-v1/selected.json), and [all validation trials](models/generated/aishell3-first-four-tone-v1/validation-trials.json) record exact source hashes, dependencies, hyperparameters, weighting and seed 20261017. Median imputation and scaling fit on train only; no train+validation refit. The LR search is C∈{0.1,1}, layers 6/9/12, target/context, mean pooling only. Selection order is validation macro F1, balanced accuracy, accuracy, then stable trial order. There were 29 attempted head configurations. Optional model 5 (phonetic identity) was omitted to keep this pass strictly audio-only.

TencentGameMate/chinese-hubert-base revision `fce0375452b1dd6c080ac3248d423d4d037bc831`; microsoft/wavlm-base-plus revision `4c66d4806a428f2e922ccfa1a962776e232d487b`. Both encoders stay frozen in eval mode; three hidden layers are extracted in one forward pass. CPU, four torch/BLAS threads, deterministic torch operations. Whole utterances are polyphase-resampled to mono 16 kHz PCM16 before cropping. Target input is the original read-unit crop; context adds up to 250 ms on each side. Uniform 200-sample zero padding per edge is applied before the pinned feature extractor so the shortest accepted finals retain convolutional frame centers. Pooling timestamps are shifted by that padding; no neighboring frame centers are pooled. Contextual hidden states can still encode surrounding speech. Every used span has at least one owned center. HuBERT uses its pinned waveform normalization; WavLM uses its pinned no-normalization setting.

Model 0 uses unchanged production Praat, pitch-track/display, raw-discontinuity and family functions on whole-read-unit timing. It is acoustic-family inference, not the contextual learner grade. Family supports are not calibrated probabilities. No production scorer compatibility rules changed.

Label-free acoustic measurements and fixed baseline outputs were cached for all 729 units. Selection used train/validation rows only. Learned test embeddings, model predictions and all label-based test scoring followed the configuration/model freeze.

Selection/models frozen at `2026-10-17T16:29:25.871926+00:00`; test evaluation at `2026-10-17T16:29:47.291268+00:00`; external probe began at `2026-10-17T16:32:57.662797+00:00` after the test-result seal. No choices were changed from test errors or external predictions.

A preflight test caught reuse of the corpus-only 44.1 kHz WAV decoder for canonical 16 kHz audio. The research adapter was fixed before any classifier fit; its failed preflight protocol is archived. No failed or successful test metrics were used for model selection.

## Every validation configuration

All speech configurations below use tone-bearing frame-center mean pooling. HuBERT context/layer 9/C=0.1 won because its validation macro F1, 95.1541%, was the highest across all 29 trials. Its validation accuracy was 95.5414% and balanced accuracy 95.0595%. Neither test accuracy nor external predictions were a selection criterion. WavLM's own winner was context/layer 6/C=0.1, validation macro F1 73.4715%.

| Trial | Family | View | Layer | C | Accuracy | Balanced accuracy | Macro F1 | T3 recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 Acoustic LR | — | — | 0.1 | 70.06% | 70.01% | 69.76% | 69.44% |
| 1 | 1 Acoustic LR | — | — | 1.0 | 73.25% | 72.95% | 72.76% | 63.89% |
| 2 | 2 Chinese HuBERT LR | target | 6 | 0.1 | 77.07% | 77.58% | 77.05% | 77.78% |
| 3 | 2 Chinese HuBERT LR | target | 6 | 1.0 | 77.07% | 77.58% | 77.04% | 77.78% |
| 4 | 2 Chinese HuBERT LR | target | 9 | 0.1 | 76.43% | 76.52% | 75.91% | 63.89% |
| 5 | 2 Chinese HuBERT LR | target | 9 | 1.0 | 75.16% | 75.33% | 74.60% | 61.11% |
| 6 | 2 Chinese HuBERT LR | target | 12 | 0.1 | 64.97% | 66.19% | 65.06% | 55.56% |
| 7 | 2 Chinese HuBERT LR | target | 12 | 1.0 | 65.61% | 66.88% | 65.73% | 58.33% |
| 8 | 2 Chinese HuBERT LR | context | 6 | 0.1 | 87.90% | 87.65% | 87.42% | 86.11% |
| 9 | 2 Chinese HuBERT LR | context | 6 | 1.0 | 86.62% | 86.24% | 86.05% | 83.33% |
| 10 | 2 Chinese HuBERT LR | context | 9 | 0.1 | 95.54% | 95.06% | 95.15% | 91.67% |
| 11 | 2 Chinese HuBERT LR | context | 9 | 1.0 | 94.90% | 94.57% | 94.58% | 91.67% |
| 12 | 2 Chinese HuBERT LR | context | 12 | 0.1 | 80.89% | 80.60% | 80.44% | 66.67% |
| 13 | 2 Chinese HuBERT LR | context | 12 | 1.0 | 82.80% | 82.50% | 82.26% | 69.44% |
| 14 | 3 WavLM LR | target | 6 | 0.1 | 58.60% | 57.05% | 57.56% | 52.78% |
| 15 | 3 WavLM LR | target | 6 | 1.0 | 58.60% | 57.27% | 57.73% | 52.78% |
| 16 | 3 WavLM LR | target | 9 | 0.1 | 39.49% | 39.59% | 38.82% | 30.56% |
| 17 | 3 WavLM LR | target | 9 | 1.0 | 36.94% | 36.99% | 36.25% | 25.00% |
| 18 | 3 WavLM LR | target | 12 | 0.1 | 42.04% | 41.69% | 41.50% | 41.67% |
| 19 | 3 WavLM LR | target | 12 | 1.0 | 42.04% | 41.71% | 41.34% | 38.89% |
| 20 | 3 WavLM LR | context | 6 | 0.1 | 73.25% | 74.01% | 73.47% | 72.22% |
| 21 | 3 WavLM LR | context | 6 | 1.0 | 72.61% | 72.87% | 72.54% | 69.44% |
| 22 | 3 WavLM LR | context | 9 | 0.1 | 54.78% | 54.22% | 53.57% | 36.11% |
| 23 | 3 WavLM LR | context | 9 | 1.0 | 52.23% | 51.85% | 50.95% | 30.56% |
| 24 | 3 WavLM LR | context | 12 | 0.1 | 39.49% | 40.14% | 39.77% | 47.22% |
| 25 | 3 WavLM LR | context | 12 | 1.0 | 41.40% | 41.81% | 41.42% | 50.00% |
| 26 | 4 Small MLP | context | 9 | fixed MLP | 94.90% | 94.59% | 94.68% | 88.89% |
| 27 | 6 HuBERT + acoustics LR | context | 9 | 0.1 | 94.90% | 94.35% | 94.46% | 91.67% |
| 28 | 6 HuBERT + acoustics LR | context | 9 | 1.0 | 94.90% | 94.35% | 94.46% | 91.67% |


### Selected-family validation comparison

Frozen Benma validation metrics below were calculated during finalization from its existing cached outputs for reporting only. It has no fitted or selected parameters. All learned validation metrics are the original, pre-test trial records.

| Model | Coverage | Accuracy | Balanced accuracy | Macro F1 | T3 recall |
| --- | --- | --- | --- | --- | --- |
| 0 Frozen Benma | 45.86% | 34.72% | 33.05% | 29.95% | 43.75% |
| 1 Acoustic LR | 100.00% | 73.25% | 72.95% | 72.76% | 63.89% |
| 2 Chinese HuBERT LR | 100.00% | 95.54% | 95.06% | 95.15% | 91.67% |
| 3 WavLM LR | 100.00% | 73.25% | 74.01% | 73.47% | 72.22% |
| 4 Small MLP | 100.00% | 94.90% | 94.59% | 94.68% | 88.89% |
| 6 HuBERT + acoustics LR | 100.00% | 94.90% | 94.35% | 94.46% | 91.67% |


## Selected models on the sealed test set

| Model | Selected configuration | Coverage | Accuracy | Balanced accuracy | Macro F1 | T3 recall | T3→T4 /31 | T3→T2 /31 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 Frozen Benma | frozen | 64.41% | 28.95% | 28.20% | 25.55% | 20.00% | 15 (48.39%) | 1 (3.23%) |
| 1 Acoustic LR | {'C': 1.0, 'features': 'acoustic', 'kind': 'logistic'} | 100.00% | 57.06% | 56.15% | 55.80% | 48.39% | 6 (19.35%) | 7 (22.58%) |
| 2 Chinese HuBERT LR | {'C': 0.1, 'encoder': 'chinese_hubert_base', 'features': 'embedding', 'kind': 'logistic', 'layer': 9, 'view': 'context'} | 100.00% | 90.40% | 89.30% | 89.78% | 83.87% | 2 (6.45%) | 3 (9.68%) |
| 3 WavLM LR | {'C': 0.1, 'encoder': 'wavlm_base_plus', 'features': 'embedding', 'kind': 'logistic', 'layer': 6, 'view': 'context'} | 100.00% | 69.49% | 69.26% | 68.84% | 74.19% | 1 (3.23%) | 7 (22.58%) |
| 4 Small MLP | {'encoder': 'chinese_hubert_base', 'features': 'embedding', 'kind': 'mlp', 'layer': 9, 'view': 'context'} | 100.00% | 87.01% | 85.84% | 86.44% | 77.42% | 3 (9.68%) | 4 (12.90%) |
| 6 HuBERT + acoustics LR | {'C': 0.1, 'encoder': 'chinese_hubert_base', 'features': 'embedding_acoustics', 'kind': 'logistic', 'layer': 9, 'view': 'context'} | 100.00% | 89.83% | 88.97% | 89.36% | 83.87% | 3 (9.68%) | 2 (6.45%) |


Benma accuracy, balanced accuracy, macro F1 and the recall column above are conditional on coverage. Its T3 recall is 4/20 covered (20.00%), or 4/31 total (12.90%). Its T3→T4 rate is 15/31 total (48.39%), or 15/20 covered (75%); T3→T2 is 1/31 total (3.23%), or 1/20 covered (5%). HuBERT has no abstentions: T3 recall 26/31 (83.87%), T3→T4 2/31 (6.45%), T3→T2 3/31 (9.68%). Thus T3→T2 increases while the much larger T3→T4 failure declines.

A coverage-aware interpretation counts correct numbered decisions over all test units: Benma is 33/177 (18.64%), with 81 wrong numbered decisions and 63 abstentions. HuBERT is 160/177 (90.40%), with 17 wrong decisions and no abstentions. This does not assume abstention has the same practical cost as a wrong confident prediction.

The fixed MLP uses one 64-unit hidden layer, alpha=0.01, lbfgs, max_iter=400 and balanced train sample weights. Train accuracy is 100%, validation 94.90%, test 87.01%; its generalization gap and 13 high-confidence errors are worse than the selected LR. It offered no benefit. Combined embeddings + acoustics also failed to improve validation and test over HuBERT LR. No convergence warnings occurred in the 29 head fits. WavLM emitted a torch attention-mask deprecation warning during extraction, without failed or nonfinite outputs.

## Per-tone metrics and confusion matrices

Rows are corpus T1/T2/T3/T4, columns predicted T1/T2/T3/T4. Benma matrices exclude abstentions; abstention counts and all-example recall are shown separately. Macro F1 always averages the fixed four classes; absent classes receive zero in per-speaker F1, so two tiny speakers have macro F1 0.75 despite perfect accuracy. Balanced accuracy averages present true classes.

### 0 Frozen Benma

| Tone | Precision | Covered recall | F1 | All-example recall | Abstentions |
| --- | --- | --- | --- | --- | --- |
| T1 | 66.67% | 8.33% | 14.81% | 4.76% | 18 |
| T2 | 28.57% | 10.26% | 15.09% | 8.00% | 11 |
| T3 | 7.55% | 20.00% | 10.96% | 12.90% | 11 |
| T4 | 52.27% | 74.19% | 61.33% | 42.59% | 23 |


| Truth / prediction | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 2 | 5 | 16 | 1 |
| T2 | 0 | 4 | 30 | 5 |
| T3 | 0 | 1 | 4 | 15 |
| T4 | 1 | 4 | 3 | 23 |


### 1 Acoustic LR

| Tone | Precision | Covered recall | F1 | All-example recall | Abstentions |
| --- | --- | --- | --- | --- | --- |
| T1 | 46.81% | 52.38% | 49.44% | 52.38% | 0 |
| T2 | 62.07% | 72.00% | 66.67% | 72.00% | 0 |
| T3 | 45.45% | 48.39% | 46.88% | 48.39% | 0 |
| T4 | 71.79% | 51.85% | 60.22% | 51.85% | 0 |


| Truth / prediction | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 22 | 13 | 3 | 4 |
| T2 | 5 | 36 | 8 | 1 |
| T3 | 3 | 7 | 15 | 6 |
| T4 | 17 | 2 | 7 | 28 |


### 2 Chinese HuBERT LR

| Tone | Precision | Covered recall | F1 | All-example recall | Abstentions |
| --- | --- | --- | --- | --- | --- |
| T1 | 100.00% | 83.33% | 90.91% | 83.33% | 0 |
| T2 | 84.91% | 90.00% | 87.38% | 90.00% | 0 |
| T3 | 86.67% | 83.87% | 85.25% | 83.87% | 0 |
| T4 | 91.53% | 100.00% | 95.58% | 100.00% | 0 |


| Truth / prediction | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 35 | 5 | 0 | 2 |
| T2 | 0 | 45 | 4 | 1 |
| T3 | 0 | 3 | 26 | 2 |
| T4 | 0 | 0 | 0 | 54 |


### 3 WavLM LR

| Tone | Precision | Covered recall | F1 | All-example recall | Abstentions |
| --- | --- | --- | --- | --- | --- |
| T1 | 79.31% | 54.76% | 64.79% | 54.76% | 0 |
| T2 | 66.07% | 74.00% | 69.81% | 74.00% | 0 |
| T3 | 60.53% | 74.19% | 66.67% | 74.19% | 0 |
| T4 | 74.07% | 74.07% | 74.07% | 74.07% | 0 |


| Truth / prediction | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 23 | 9 | 1 | 9 |
| T2 | 4 | 37 | 5 | 4 |
| T3 | 0 | 7 | 23 | 1 |
| T4 | 2 | 3 | 9 | 40 |


### 4 Small MLP

| Tone | Precision | Covered recall | F1 | All-example recall | Abstentions |
| --- | --- | --- | --- | --- | --- |
| T1 | 94.59% | 83.33% | 88.61% | 83.33% | 0 |
| T2 | 81.82% | 90.00% | 85.71% | 90.00% | 0 |
| T3 | 85.71% | 77.42% | 81.36% | 77.42% | 0 |
| T4 | 87.72% | 92.59% | 90.09% | 92.59% | 0 |


| Truth / prediction | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 35 | 4 | 0 | 3 |
| T2 | 0 | 45 | 4 | 1 |
| T3 | 0 | 4 | 24 | 3 |
| T4 | 2 | 2 | 0 | 50 |


### 6 HuBERT + acoustics LR

| Tone | Precision | Covered recall | F1 | All-example recall | Abstentions |
| --- | --- | --- | --- | --- | --- |
| T1 | 97.30% | 85.71% | 91.14% | 85.71% | 0 |
| T2 | 84.91% | 90.00% | 87.38% | 90.00% | 0 |
| T3 | 86.67% | 83.87% | 85.25% | 83.87% | 0 |
| T4 | 91.23% | 96.30% | 93.69% | 96.30% | 0 |


| Truth / prediction | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| T1 | 36 | 5 | 0 | 1 |
| T2 | 0 | 45 | 4 | 1 |
| T3 | 0 | 2 | 26 | 3 |
| T4 | 1 | 1 | 0 | 52 |


## Held-out speakers

| Model | Speaker | n | T1/T2/T3/T4 | Covered | Accuracy | T3→T4 | T3→T2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 Frozen Benma | SSB0038 | 4 | 0/1/1/2 | 4 | 75.00% | 0 | 0 |
| 0 Frozen Benma | SSB0043 | 164 | 40/49/29/46 | 105 | 24.76% | 15 | 1 |
| 0 Frozen Benma | SSB0133 | 9 | 2/0/1/6 | 5 | 80.00% | 0 | 0 |
| 1 Acoustic LR | SSB0038 | 4 | 0/1/1/2 | 4 | 75.00% | 0 | 1 |
| 1 Acoustic LR | SSB0043 | 164 | 40/49/29/46 | 164 | 56.71% | 6 | 5 |
| 1 Acoustic LR | SSB0133 | 9 | 2/0/1/6 | 9 | 55.56% | 0 | 1 |
| 2 Chinese HuBERT LR | SSB0038 | 4 | 0/1/1/2 | 4 | 100.00% | 0 | 0 |
| 2 Chinese HuBERT LR | SSB0043 | 164 | 40/49/29/46 | 164 | 89.63% | 2 | 3 |
| 2 Chinese HuBERT LR | SSB0133 | 9 | 2/0/1/6 | 9 | 100.00% | 0 | 0 |
| 3 WavLM LR | SSB0038 | 4 | 0/1/1/2 | 4 | 75.00% | 0 | 0 |
| 3 WavLM LR | SSB0043 | 164 | 40/49/29/46 | 164 | 69.51% | 1 | 7 |
| 3 WavLM LR | SSB0133 | 9 | 2/0/1/6 | 9 | 66.67% | 0 | 0 |
| 4 Small MLP | SSB0038 | 4 | 0/1/1/2 | 4 | 100.00% | 0 | 0 |
| 4 Small MLP | SSB0043 | 164 | 40/49/29/46 | 164 | 86.59% | 3 | 3 |
| 4 Small MLP | SSB0133 | 9 | 2/0/1/6 | 9 | 88.89% | 0 | 1 |
| 6 HuBERT + acoustics LR | SSB0038 | 4 | 0/1/1/2 | 4 | 100.00% | 0 | 0 |
| 6 HuBERT + acoustics LR | SSB0043 | 164 | 40/49/29/46 | 164 | 89.02% | 3 | 2 |
| 6 HuBERT + acoustics LR | SSB0133 | 9 | 2/0/1/6 | 9 | 100.00% | 0 | 0 |


HuBERT is 4/4 on SSB0038, 147/164 on SSB0043, and 9/9 on SSB0133. Benma is 3/4, 26/105 and 4/5 covered respectively. SSB0038 has no T1; SSB0133 has no T2. The 17 HuBERT errors all belong to SSB0043: five T1→T2, two T1→T4, four T2→T3, one T2→T4, three T3→T2, two T3→T4. All 54 test T4s are recovered.

## Confidence and complete error review

Probabilities are uncalibrated classifier outputs. No learner thresholds were created. The following confidence-bin counts are the histogram; all bins were fixed before test.

### 1 Acoustic LR — 17 errors at confidence ≥0.8

| Max-probability bin | n | Correct | Incorrect | Accuracy |
| --- | --- | --- | --- | --- |
| [0.25, 0.40) | 4 | 2 | 2 | 50.00% |
| [0.40, 0.50) | 10 | 3 | 7 | 30.00% |
| [0.50, 0.60) | 31 | 12 | 19 | 38.71% |
| [0.60, 0.70) | 31 | 12 | 19 | 38.71% |
| [0.70, 0.80) | 26 | 14 | 12 | 53.85% |
| [0.80, 0.90) | 30 | 22 | 8 | 73.33% |
| [0.90, 1.00] | 45 | 36 | 9 | 80.00% |


### 2 Chinese HuBERT LR — 5 errors at confidence ≥0.8

| Max-probability bin | n | Correct | Incorrect | Accuracy |
| --- | --- | --- | --- | --- |
| [0.25, 0.40) | 2 | 1 | 1 | 50.00% |
| [0.40, 0.50) | 3 | 1 | 2 | 33.33% |
| [0.50, 0.60) | 9 | 5 | 4 | 55.56% |
| [0.60, 0.70) | 10 | 9 | 1 | 90.00% |
| [0.70, 0.80) | 16 | 12 | 4 | 75.00% |
| [0.80, 0.90) | 15 | 14 | 1 | 93.33% |
| [0.90, 1.00] | 122 | 118 | 4 | 96.72% |


### 3 WavLM LR — 12 errors at confidence ≥0.8

| Max-probability bin | n | Correct | Incorrect | Accuracy |
| --- | --- | --- | --- | --- |
| [0.25, 0.40) | 3 | 1 | 2 | 33.33% |
| [0.40, 0.50) | 8 | 1 | 7 | 12.50% |
| [0.50, 0.60) | 22 | 11 | 11 | 50.00% |
| [0.60, 0.70) | 20 | 11 | 9 | 55.00% |
| [0.70, 0.80) | 24 | 11 | 13 | 45.83% |
| [0.80, 0.90) | 42 | 35 | 7 | 83.33% |
| [0.90, 1.00] | 58 | 53 | 5 | 91.38% |


### 4 Small MLP — 13 errors at confidence ≥0.8

| Max-probability bin | n | Correct | Incorrect | Accuracy |
| --- | --- | --- | --- | --- |
| [0.25, 0.40) | 0 | 0 | 0 | — |
| [0.40, 0.50) | 0 | 0 | 0 | — |
| [0.50, 0.60) | 4 | 1 | 3 | 25.00% |
| [0.60, 0.70) | 5 | 1 | 4 | 20.00% |
| [0.70, 0.80) | 4 | 1 | 3 | 25.00% |
| [0.80, 0.90) | 7 | 4 | 3 | 57.14% |
| [0.90, 1.00] | 157 | 147 | 10 | 93.63% |


### 6 HuBERT + acoustics LR — 5 errors at confidence ≥0.8

| Max-probability bin | n | Correct | Incorrect | Accuracy |
| --- | --- | --- | --- | --- |
| [0.25, 0.40) | 1 | 1 | 0 | 100.00% |
| [0.40, 0.50) | 4 | 1 | 3 | 25.00% |
| [0.50, 0.60) | 10 | 7 | 3 | 70.00% |
| [0.60, 0.70) | 10 | 7 | 3 | 70.00% |
| [0.70, 0.80) | 14 | 10 | 4 | 71.43% |
| [0.80, 0.90) | 19 | 18 | 1 | 94.74% |
| [0.90, 1.00] | 119 | 115 | 4 | 96.64% |


### Selected HuBERT high-confidence errors

| Example | Truth→prediction | Confidence |
| --- | --- | --- |
| aishell3:SSB00430061:0 | T2→T3 | 99.77% |
| aishell3:SSB00430061:1 | T3→T2 | 95.15% |
| aishell3:SSB00430124:3 | T3→T4 | 98.79% |
| aishell3:SSB00430396:3 | T2→T3 | 83.85% |
| aishell3:SSB00430488:1 | T1→T2 | 94.64% |


The five error identities are also shown with all four probabilities and provenance below. [Finalization audit](reports/aishell3-finalization-audit.json) preserves exact bin counts and high-confidence error identities for every learned model.

All 17 selected-model errors were inspected through their released timing/phone provenance, neighbors, probabilities and frozen acoustic evidence. This is a metadata/acoustic review, not a new native-listener label adjudication. Seven errors have confidence <0.6, five ≥0.8. Only 啄 has a flagged <60 ms final (30 ms). That is a sensitivity candidate, not proof of residual misalignment. Two T3 errors are utterance-final: 鸟→T2 and 使→T4. 宝宝 has a high-confidence T2/T3 reversal across adjacent units; label-order, actual realization and sandhi deserve a future independent audit. All tested labels, spans and predictions remain frozen. There is insufficient repeated segment/speaker evidence to infer a general segment-specific mechanism.

| Speaker | Utterance | Example / unit | Base | Truth→pred | P1/P2/P3/P4 | Whole / final ms | Prev / next | Benma | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SSB0043 | SSB00430011 | aishell3:SSB00430011:0 待 | dai | T1→T2 | 0.3069/0.3538/0.0095/0.3298 | 180 / 120 | start / T4 | T3 | T1->T2, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430035 | aishell3:SSB00430035:0 等 | deng | T3→T2 | 0.0129/0.4798/0.4368/0.0705 | 210 / 160 | start / T4 | T3 | T3->T2, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430051 | aishell3:SSB00430051:2 啄 | zhuo | T2→T4 | 0.0027/0.2377/0.0497/0.7099 | 150 / 30 | T1 / T4 | T4 | T2->T4, short-pooling-span, SSB0043-concentration |
| SSB0043 | SSB00430051 | aishell3:SSB00430051:4 鸟 | niao | T3→T2 | 0.0579/0.5220/0.3909/0.0292 | 320 / 170 | T4 / end | abstain | T3->T2, utterance-final, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430061 | aishell3:SSB00430061:0 宝 | bao | T2→T3 | 0.0006/0.0010/0.9977/0.0008 | 160 / 100 | start / T3 | T4 | T2->T3, high-confidence-error, SSB0043-concentration |
| SSB0043 | SSB00430061 | aishell3:SSB00430061:1 宝 | bao | T3→T2 | 0.0295/0.9515/0.0166/0.0024 | 170 / 100 | T2 / T4 | T2 | T3->T2, high-confidence-error, SSB0043-concentration |
| SSB0043 | SSB00430061 | aishell3:SSB00430061:3 儿 | er | T2→T3 | 0.0049/0.2188/0.7520/0.0243 | 280 / 160 | T4 / T2 | abstain | T2->T3, SSB0043-concentration |
| SSB0043 | SSB00430124 | aishell3:SSB00430124:3 使 | shi | T3→T4 | 0.0005/0.0019/0.0096/0.9879 | 310 / 130 | T1 / end | abstain | T3->T4, utterance-final, high-confidence-error, SSB0043-concentration |
| SSB0043 | SSB00430186 | aishell3:SSB00430186:0 阿 | a | T1→T4 | 0.4220/0.0391/0.0267/0.5122 | 170 / 110 | start / T1 | T2 | T1->T4, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430364 | aishell3:SSB00430364:4 歌 | ge | T1→T2 | 0.1869/0.4185/0.0977/0.2969 | 340 / 230 | T5 / end | abstain | T1->T2, utterance-final, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430396 | aishell3:SSB00430396:3 什 | shen | T2→T3 | 0.0124/0.1473/0.8385/0.0019 | 220 / 110 | T4 / T5 | T4 | T2->T3, high-confidence-error, SSB0043-concentration |
| SSB0043 | SSB00430400 | aishell3:SSB00430400:1 传 | chuan | T2→T3 | 0.0377/0.1336/0.7792/0.0495 | 250 / 110 | T2 / T4 | T4 | T2->T3, SSB0043-concentration |
| SSB0043 | SSB00430423 | aishell3:SSB00430423:1 滚 | gun | T3→T4 | 0.0980/0.1176/0.2548/0.5296 | 230 / 70 | T2 / T1 | abstain | T3->T4, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430426 | aishell3:SSB00430426:0 乌 | wu | T1→T2 | 0.2686/0.6225/0.0087/0.1001 | 130 / 130 | start / T2 | T3 | T1->T2, SSB0043-concentration |
| SSB0043 | SSB00430474 | aishell3:SSB00430474:0 相 | xiang | T1→T4 | 0.2195/0.0194/0.0126/0.7485 | 140 / 110 | start / T4 | T3 | T1->T4, SSB0043-concentration |
| SSB0043 | SSB00430488 | aishell3:SSB00430488:0 千 | qian | T1→T2 | 0.3639/0.5835/0.0476/0.0049 | 260 / 170 | start / T1 | T3 | T1->T2, low-confidence, SSB0043-concentration |
| SSB0043 | SSB00430488 | aishell3:SSB00430488:1 杯 | bei | T1→T2 | 0.0307/0.9464/0.0214/0.0015 | 160 / 120 | T1 / T2 | T3 | T1->T2, high-confidence-error, SSB0043-concentration |


[Full error records and per-speaker confusion matrices](models/generated/aishell3-first-four-tone-v1/test-results.json). No errors were used to retune, quarantine or reclassify this test set.

## External physical recordings — exploratory only

Physical archives have whole-syllable timings, not reviewed nucleus/coda phone spans. Uniformly pool the existing whole syllable as a proxy. Same frozen weights/layer/context; this is an exploratory representation mismatch, not matched-span evaluation.

The inventory covers 77 suitable units across the archived Stage-0 recordings and additional tone-feedback/classification physical fixtures. One grouped timing unit was excluded rather than split artificially. All six distinct archived 我想买这个 takes with verified audio and individual timings are included below (30 syllables). The two Google/phone-TTS takes are not claimed as human speech. This is the available archived evidence inventory, not a claim that every unindexed WAV on disk has been transcribed. Sources and full recording IDs are in the [sealed probe](models/generated/aishell3-first-four-tone-v1/external-probe.json).

| Take | Unit | P(T1) | P(T2) | P(T3) | P(T4) | Learned | Confidence | Frozen Benma |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 89cee47e | 我 | 0.0313 | 0.5996 | 0.3458 | 0.0234 | T2 | 0.5996 | T3 |
| 89cee47e | 想 | 0.1987 | 0.6480 | 0.1479 | 0.0053 | T2 | 0.6480 | abstain |
| 89cee47e | 买 | 0.6892 | 0.0574 | 0.2199 | 0.0335 | T1 | 0.6892 | abstain |
| 89cee47e | 这 | 0.0079 | 0.1503 | 0.1020 | 0.7397 | T4 | 0.7397 | abstain |
| 89cee47e | 个 | 0.2029 | 0.1556 | 0.3662 | 0.2753 | T3 | 0.3662 | abstain |
| cad88597 | 我 | 0.0186 | 0.8912 | 0.0697 | 0.0204 | T2 | 0.8912 | abstain |
| cad88597 | 想 | 0.0128 | 0.9203 | 0.0645 | 0.0024 | T2 | 0.9203 | abstain |
| cad88597 | 买 | 0.0017 | 0.0154 | 0.9769 | 0.0059 | T3 | 0.9769 | abstain |
| cad88597 | 这 | 0.0166 | 0.1100 | 0.0443 | 0.8292 | T4 | 0.8292 | abstain |
| cad88597 | 个 | 0.0866 | 0.5012 | 0.1447 | 0.2675 | T2 | 0.5012 | abstain |
| 4f1ab9ed | 我 | 0.0798 | 0.1976 | 0.6533 | 0.0693 | T3 | 0.6533 | T3 |
| 4f1ab9ed | 想 | 0.2107 | 0.1440 | 0.0711 | 0.5741 | T4 | 0.5741 | T4 |
| 4f1ab9ed | 买 | 0.1675 | 0.4385 | 0.3718 | 0.0222 | T2 | 0.4385 | T3 |
| 4f1ab9ed | 这 | 0.0053 | 0.0292 | 0.0623 | 0.9032 | T4 | 0.9032 | T4 |
| 4f1ab9ed | 个 | 0.3551 | 0.1940 | 0.1970 | 0.2539 | T1 | 0.3551 | abstain |
| 19d8333b | 我 | 0.0350 | 0.5048 | 0.4417 | 0.0185 | T2 | 0.5048 | abstain |
| 19d8333b | 想 | 0.4905 | 0.2033 | 0.2356 | 0.0706 | T1 | 0.4905 | T3 |
| 19d8333b | 买 | 0.6720 | 0.0427 | 0.2247 | 0.0606 | T1 | 0.6720 | abstain |
| 19d8333b | 这 | 0.0092 | 0.1502 | 0.0848 | 0.7557 | T4 | 0.7557 | T4 |
| 19d8333b | 个 | 0.1082 | 0.1344 | 0.1032 | 0.6542 | T4 | 0.6542 | abstain |
| b8049b3e | 我 | 0.0172 | 0.9236 | 0.0457 | 0.0135 | T2 | 0.9236 | abstain |
| b8049b3e | 想 | 0.0140 | 0.9113 | 0.0744 | 0.0003 | T2 | 0.9113 | T3 |
| b8049b3e | 买 | 0.0027 | 0.0107 | 0.9748 | 0.0118 | T3 | 0.9748 | abstain |
| b8049b3e | 这 | 0.0193 | 0.1032 | 0.0290 | 0.8485 | T4 | 0.8485 | abstain |
| b8049b3e | 个 | 0.0844 | 0.7665 | 0.0862 | 0.0629 | T2 | 0.7665 | abstain |
| d7b27845 | 我 | 0.0319 | 0.1442 | 0.8044 | 0.0194 | T3 | 0.8044 | T3 |
| d7b27845 | 想 | 0.7804 | 0.1687 | 0.0223 | 0.0286 | T1 | 0.7804 | T4 |
| d7b27845 | 买 | 0.0414 | 0.5465 | 0.3612 | 0.0508 | T2 | 0.5465 | T3 |
| d7b27845 | 这 | 0.0132 | 0.1017 | 0.1404 | 0.7447 | T4 | 0.7447 | T4 |
| d7b27845 | 个 | 0.1358 | 0.0978 | 0.3862 | 0.3802 | T3 | 0.3862 | abstain |


No current frozen 我 prediction in these six full-phrase takes is T4: they are T3 or abstentions. The earlier natural-我→T4 concern must not be attributed to a newer frozen T3 result. Two archived other-phrase 我 units do retain frozen T4 predictions:

| Take / phrase | Benma | P(T1) | P(T2) | P(T3) | P(T4) | Learned |
| --- | --- | --- | --- | --- | --- | --- |
| 8faf1a90 我要一个苹果。 | T4 | 0.0491 | 0.3071 | 0.5959 | 0.0479 | T3 |
| a5acd04c 我有一个苹果。 | T4 | 0.0749 | 0.3838 | 0.1469 | 0.3944 | T4 |


**Partial improvement, not a solved external failure:** 我要一个苹果 / 8faf1a90 changes from T4 to T3 (P3≈0.596). 我有一个苹果 / a5acd04c stays T4 (P4≈0.394, P2≈0.384, P3≈0.147). On human d7b27845, 我 is T3 but 想 becomes T1 and 买 T2; 4f1ab9ed retains 想→T4. Google/phone-TTS b8049b3e and cad88597 yield T2/T2/T3 on 我/想/买, compatible with a possible sandhi realization but not independently adjudicated here. Neutral 个 is outside the four-class task; its forced four-way probabilities cannot be treated as a tone error or grade. Naturalness, prosodic grouping and expected acceptability are not determined by lexical tone alone.

This probe differs in microphone/environment, speaker population (the human learner takes do not constitute a new multi-speaker study), alignment provenance and pooling. It is exploratory external evidence, not a product-accuracy test or a matched-representation test of the AISHELL-3 model. The TTS phone-playback takes remain distinct from human learner speech.

## Reproduction, validation and limits

All five selected heads were serialized/reloaded and retrained with the frozen seed. Maximum test-probability delta is **0.0** for both reload and seeded refit. Fresh uncached HuBERT and WavLM speech extraction also reproduces the cached vectors exactly. Verified 2,562 training/test embedding cache entries and 2,361 released audio derivatives, including nonempty pooling. Temporary cache corruption is rejected. Canonical WAV/source corruption, annotation mutation, train-only preprocessing, metrics and immutable-release tampering tests pass.

Exact tolerances: reload and cached prediction checks use absolute tolerance 1e-12; the previous seeded head-refit check used 1e-10; the previous fresh embedding check used 1e-6, all with rtol=0. Observed maximum differences were 0.0, so probabilities were numerically identical, not merely within tolerance. Seeded refits were not compared as serialized model bytes. Separately, 5,737 generated artifact files survived a repeat pipeline byte-identically, and all 1,176 historical evidence hashes stayed unchanged. Another 2,187 resampled model input/pooling audio comparisons confirmed no partition leakage. The finalization pass uses cached matrices and saved models only: zero new fits, configurations or encoder extractions.

83 Python tests and three Node research tests pass; scoped Ruff and `git diff --check` pass. All **413 frozen hashes remain unchanged** and the **63-example replay is byte-identical**. Only research files were changed. No F0, family scorer, grader, app/UI, API or inference integration was changed; no commit, push or deployment occurred. Large audio, embeddings and joblib models remain under ignored generated directories.

The pre-trained encoders may have unknown corpus exposure; this pass does not establish absence of pretraining contamination. Corpus numbered pronunciation labels are not independent perceptual judgments; sandhi/label discrepancies remain possible. HuBERT can use spoken segment identity and surrounding lexical cues even without text inputs, so strong corpus-label prediction is not proof of purely acoustic tone perception. Sixteen corpus speakers, three very uneven test speakers, 31 test T3s, small validation selection, oracle-like offline timing, future context, phone-recording domain shift, external pooling mismatch, absent neutral class and uncalibrated probabilities all limit deployment conclusions.

**Smallest next experiment (proposed, not implemented):** expand the AISHELL-3 subset into a new version with balanced held-out speaker contributions and T3 examples across several held-out speakers. Keep the same frozen model methodology and selection discipline; evaluate the existing checkpoint on the new independent speakers before any new training choices. Preserve this test set as a completed experiment. A later, separate experiment should add reviewed learner recordings with matching nucleus/coda spans and realized-tone/sandhi judgments. No production integration.

## Reproduction commands

```sh
PY=benchmark/pronunciation_v2/.venv/bin/python
$PY research/perceptual-tone-model/scripts/aishell3_release.py --verify
$PY research/perceptual-tone-model/scripts/aishell3_finalize.py
$PY research/perceptual-tone-model/scripts/aishell3_report.py
$PY research/perceptual-tone-model/scripts/aishell3_finalize.py --check-report
# Historical full-pipeline commands below; finalization does not rerun training/extraction.
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 $PY research/perceptual-tone-model/scripts/aishell3_train.py
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 $PY research/perceptual-tone-model/scripts/aishell3_verify.py
$PY research/perceptual-tone-model/scripts/aishell3_probe.py
PYTHONPATH=research/perceptual-tone-model $PY -m unittest discover -s research/perceptual-tone-model/tests
node --test research/perceptual-tone-model/test_aishell3_baseline.cjs research/perceptual-tone-model/test_native_baseline.cjs research/perceptual-tone-model/test_evaluate.cjs
```

[Machine summary](reports/aishell3-training-summary.json), [validation/reproduction record](reports/aishell3-training-validation.json), [changed research files](reports/aishell3-training-changed-files.txt).
