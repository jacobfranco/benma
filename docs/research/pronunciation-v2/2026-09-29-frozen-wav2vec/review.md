# Experiment #1: frozen wav2vec2 tone probe

**INCONCLUSIVE.** A frozen waveform representation contains substantial recoverable tone signal, but this mean-pooled linear formulation is not robust across the observed source groups. On the untouched 60-clip Luilui6666 primary test it achieves **71.67% accuracy, 0.7075 balanced accuracy and 0.6610 macro F1**. Tone 3 recall collapses to **2/13 (15.38%)**, with several very high-softmax errors. V2 improves over frozen V1 on the common covered subset by **0.0919 macro F1**, but that subset has only **13 clips**, including just one T3 and one T4. This supports further controlled research, not production integration or a population-level superiority claim.

The initial preflight stop was correct. This continuation excluded the bad replacement file and all singletons, reverified the corpus, froze the source-group split, selected only on validation, locked the configuration, evaluated the primary test once, and then ran the requested fixed-config secondary diagnostic. No fine-tuning, F0 fusion, architecture changes, threshold tuning or production changes followed the result.

## 1–10. Starting state and remediation

Current branch: **pronunciation-v2-research**. Continuation starting commit: **5d92c73**, `research: add pronunciation v2 model preflight`; working tree initially clean. Earlier acquisition checkpoint `30820a4` and baseline `68057aa` remain present. No commit or push was made during this continuation.

**commons:3052714 is excluded**, not reassigned: speaker/text/date/license conflicts and embedded ShareAlike terms. All four singleton groups remain excluded. **commons:3052537 / Zh-nǎ.ogg is retained** as `na3`: cached primary revision 447926522 explicitly supplies nǎ/T3; its embedded `na` lacks a tone mark but does not contradict that reading. No acoustic/model output was used to resolve it.

Remaining Shtooka evidence: **326 total / 326 explicitly Wei Gao / zero contradictory names / zero unknown names**. Dates and text agree with cached primary records; embedded license fields consistently say Creative Commons BY, compatible with the per-file CC BY 2.0 France grants. No residual documentary mixed-voice evidence remains after the known exclusion. Nicolas Vion's joint contributor credit is supported; his exact recorder role is not independently established. These remain source/speaker groups, not biometric identities.

| Group | Role | N | T1 | T2 | T3 | T4 |
|---|---|---:|---:|---:|---:|---:|
| shtooka:wei-gao | Train | 326 | 84 | 71 | 81 | 90 |
| CanonNi | Train | 60 | 15 | 12 | 9 | 24 |
| Levi Highway | Validation | 49 | 7 | 11 | 14 | 17 |
| Luilui6666 | Final test | 60 | 11 | 15 | 13 | 21 |
| **Primary total** | | **495** | **117** | **109** | **117** | **152** |

**Readiness PASS:** N≥300, every tone≥50, every group≥40, every group/tone cell≥5. All 500 originals still decode and match source/local/PCM hashes; zero exact duplicates. The clean experiment includes 495 and excludes five. Licenses: 326 CC BY 2.0 France, 169 CC0. [Remediation evidence](remediation.md), [machine counts](remediation-summary.json), [all 500 inclusion decisions](clean-corpus-manifest.csv).

All native-Mandarin statuses remain **UNKNOWN**. The earlier 38-item stratified metadata/signal audit covers all group/tone cells, duration extremes and anomalies. **No direct listening was available or performed.** These are conservative isolated lexical-pronunciation labels, not listening-audited connected-speech surface-tone gold.

## 11–17. Frozen split, model and extraction

The [frozen split](split-manifest.csv) is **386 train / 49 validation / 60 test**, with zero source-group or exact-content leakage. Train tone distribution is **99/83/90/114**; no class weighting. All 326 remaining Shtooka files stay together. Split SHA-256:

`1ee5ab2d6bbb6739e461c53949d699cef687d8b6e25412717400889f219e6416`

Original acquisition manifest SHA-256:

`fcdacce34f9894356fa9549b9fb3d06ffb1d4427bed5153f996f9ad736e42b43`

This is not an unseen-word test: 40/60 test characters and 50/60 tone-marked pinyin readings occur in training; validation overlap is 33/49 and 41/49 respectively. These fields are metadata/labels only and never encoder/head features.

Encoder: **facebook/wav2vec2-base**, `transformers.Wav2Vec2Model`, pinned revision **0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8**, Apache-2.0 consistent with prior reconnaissance. CNN acoustic frontend plus **12 Transformer blocks**, actual hidden dimension **768**, loaded parameter count **94,371,712**. No ASR/CTC head. All acoustic weights load without missing/mismatched parameters; unused quantizer/projection weights belong to the original pretraining objective and are not used. [Checkpoint/hash record](checkpoint.json), [actual config/loading evidence](development-extraction.json).

CPU FP32, Intel i7-10700F, four Torch threads, deterministic algorithms, seed **20260929**. No functioning CUDA driver. Isolated research virtualenv: **PyTorch 2.8.0+cpu, Transformers 4.57.6, scikit-learn 1.7.2, NumPy 2.3.3, SciPy 1.16.2**, Python 3.12.13. All dependency changes are scoped to the ignored research virtualenv and research requirement files; production dependencies unchanged. [Environment and exact commands](environment.md).

Each full original clip is FFmpeg-decoded to mono float32 **16 kHz**, with checkpoint zero-mean/unit-variance waveform normalization. All retained files are mono. No trimming, augmentation, manual acoustic features, expected tone, text, pinyin, speaker identity, ASR or V1 input. One waveform per encoder forward avoids the checkpoint's group-normalization padding sensitivity; no encoder attention mask is passed. Mean pooling includes only actual hidden frames. A general masked mean is tested on nonzero padded hidden states; actual extraction has no padded waveform or hidden timestep.

**Indexing:** `hidden_states[0]` is the pre-Transformer input after acoustic projection/positional processing; `hidden_states[4]`, `[6]`, `[8]` are outputs after Transformer blocks 4, 6 and 8. Tiny-model forward-hook tests verify this convention. Each candidate layer yields one 768-vector per clip.

Frozen enforcement: `eval()`, `requires_grad_(False)`, `inference_mode()`, no encoder optimizer, all parameter gradients absent, entire state SHA-256 identical before/after extraction:

`7b4d7d625fafe1b6cf291223a3fc91db2d34c4de9196da64faa45936295a1d41`

Repeated first-clip extraction is bitwise identical. The bounded training-clip smoke run preceded selection. Development extraction (435 clips, all three layers) took **44.680 s**; test extraction (60 clips, selected layer only) **7.534 s**, total **52.213 s**, including model load/hash checks and the determinism repeat in each process. Approximate peak RSS: **927.7 MiB** development, **820.4 MiB** test. No encoder runs were repeated for hyperparameters. Pooled arrays and selected scaler/head remain outside Git.

## 18–20. Validation and configuration lock

For each layer, StandardScaler mean/population variance is fitted on **training only**. The validation/test transforms reuse those parameters. The head is unweighted **multinomial logistic regression / linear softmax**, L2, lbfgs, max_iter 3000, tolerance 1e-8. All fits converged. Coefficients, intercept, classes and scaler parameters are saved locally; saved-head softmax reproduces scikit-learn probabilities.

| Layer | C | Validation accuracy | Balanced accuracy | Macro F1 | Mean T2/T3 recall |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.1 | 0.8367 | 0.8050 | 0.8092 | 0.8831 |
| 4 | 1 | 0.8571 | 0.8277 | 0.8282 | 0.9286 |
| 4 | 10 | 0.8571 | 0.8277 | 0.8282 | 0.9286 |
| 6 | 0.1 | 0.8163 | 0.8068 | 0.8212 | 0.6851 |
| 6 | 1 | 0.8367 | 0.8247 | 0.8410 | 0.7208 |
| 6 | 10 | 0.8367 | 0.8247 | 0.8410 | 0.7208 |
| **8** | **0.1** | **0.9592** | **0.9464** | **0.9558** | **0.9643** |
| 8 | 1 | 0.9592 | 0.9464 | 0.9558 | 0.9643 |
| 8 | 10 | 0.9592 | 0.9464 | 0.9558 | 0.9643 |

Exactly nine primary candidates, [full numerical table](validation-results.csv). Selection order was macro F1, balanced accuracy, mean T2/T3 recall, stronger regularization (smaller C), then lower layer as a final deterministic tie break. Metric equality is evaluated at 12 decimals. Layer 8 candidates tie, so **layer 8 / C=0.1** wins. Validation data were not folded into final primary head fitting.

[experiment-config.locked.json](experiment-config.locked.json) was written at **2026-09-30 01:32:26.494750 UTC** (September 29 local time), before test feature extraction or metric computation. Lock SHA-256:

`d9fbce75b1cd2a741924241d54d5a68f18edffc7c13687383828486a8f385cc9`

The lock records checkpoint, split/corpus/clean-manifest hashes, all feature/head choices, software versions, seed, head/cache hashes and research-code hashes. The exclusive [test-opening receipt](primary-test-opened.json) is **01:33:40.455460 UTC**; [primary metrics](primary-metrics.json) were recorded **01:33:48.007382 UTC**. The test stage validates locked artifacts and refuses a second opening. These local timestamps and hashes form an auditable execution record, not an external timestamp attestation.

## 21–23. Primary test and baselines

**N=60, 43 correct, 17 errors, 100% V2 coverage.** Accuracy **0.7167**, balanced accuracy **0.7075**, macro F1 **0.6610**.

| Tone | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| T1 | 11 | 0.5500 | 1.0000 | 0.7097 |
| T2 | 15 | 1.0000 | 0.8667 | 0.9286 |
| T3 | 13 | 1.0000 | 0.1538 | 0.2667 |
| T4 | 21 | 0.6800 | 0.8095 | 0.7391 |

Confusion matrix: rows lexical labels, columns predicted T1/T2/T3/T4.

| Actual | T1 | T2 | T3 | T4 |
|---|---:|---:|---:|---:|
| T1 | 11 | 0 | 0 | 0 |
| T2 | 2 | 13 | 0 | 0 |
| T3 | 3 | 0 | 2 | 8 |
| T4 | 4 | 0 | 0 | 17 |

**T2→T3=0; T3→T2=0.** Other errors: T2→T1=2, T3→T1=3, T3→T4=8, T4→T1=4; all other off-diagonal cells zero. High precision for T3 reflects only two predictions and must not obscure its very low recall.

Train-majority baseline is **always T4**: test accuracy **0.3500**, balanced accuracy **0.2500**, macro F1 **0.1296**. Uniform-random conceptual accuracy/balanced-accuracy expectation is 0.25; no sampled random classifier is presented as a measured headline model. The learned representation clearly exceeds these naive references.

V1 is the unchanged **68057aa** Praat/contour pipeline, using production-equivalent mono 16-kHz PCM16 conversion, full isolated-clip bounds and existing evidence-region selection. No expected tone/text supplied; no thresholds tuned. Source bytes are verified against that historical checkpoint. [V1 config and source hashes](v1-config.json).

| View | N | Coverage of 60 | Accuracy | Macro F1 |
|---|---:|---:|---:|---:|
| V2 full test | 60 | 100% | 0.7167 | 0.6610 |
| V1 categorical subset | 13 | 21.67% | 0.5385 (7/13) | 0.5278 |
| V2 same V1-covered subset | 13 | 21.67% subset | 0.8462 (11/13) | 0.6197 |

V1 abstains/unclear on **47/60**: tracker instability 26, insufficient voicing 11, ambiguous shape 6, fragmented voicing 4. All 13 covered items have usable recording-level quality; among abstentions, 46 have usable recording-level quality and one is invalid. A usable recording does not imply reliable tone evidence. Per-tone coverage: **T1 4/11=36.36%, T2 7/15=46.67%, T3 1/13=7.69%, T4 1/21=4.76%**. No V1 ordinal confidence was converted to probability. Abstentions are reported separately, not silently counted as ordinary wrong predictions.

The common-subset macro-F1 difference is **+0.0919**, above the suggested 0.05 screening margin, but only two of the 13 covered items are T3/T4. This is fragile descriptive evidence, not proof of overall superiority. [Per-item paired comparison](v1-comparison.csv), [complete metrics](metrics.json).

## 24–25. Errors and raw softmax diagnostics

Every one of the **17 errors** has asset/text/pinyin/lexical label, prediction, all four probabilities, source, duration, signal diagnostics and V1 status in [error-analysis.csv](error-analysis.csv). [All primary predictions](test-results.csv) preserve probabilities, entropy and margin.

The dominant pattern is **11 missed T3 clips**: eight predicted T4, three predicted T1. The five incorrect items with max softmax≥0.9 are all T3:

| Asset | Item | Prediction | Max softmax | V1 |
|---|---|---|---:|---|
| commons:113935570 | 等 deng3 | T4 | 0.9894 | unclear |
| commons:113935451 | 你 ni3 | T4 | 0.9690 | T4-like |
| commons:113935453 | 早 zao3 | T4 | 0.9633 | unclear |
| commons:113935556 | 纸 zhi3 | T1 | 0.9535 | unclear |
| commons:113935564 | 笔 bi3 | T4 | 0.9489 | unclear |

These are **uncalibrated softmax values**, not calibrated confidence. The 0.9 flag is a reporting convention only; it does not affect selection, coverage or a production threshold. Mean max softmax: correct **0.8554**, wrong **0.7359**; 24/43 correct and 5/17 wrong exceed 0.9. Overall max softmax ranges **0.3904–0.9988**, mean entropy **0.4368 nats**, mean top-1/top-2 margin **0.6780**. No temperature scaling, abstention policy or Good/Close/Unclear mapping was fitted.

Error durations average **0.8927 s**, versus **0.9442 s** for correct clips; this small descriptive difference does not establish a duration cause. Error durations fall inside the ordinary test range and RMS spans **0.02190–0.07684**, with no clipping flags. Errors occur across varied pinyin initials/finals, including d-, n-, z-, zh- and b- among the largest-softmax failures. Twelve of 17 error characters and 14 of 17 tone-marked pinyin readings occur in training, so simple unseen-word novelty does not explain the whole pattern. No surviving primary metadata conflict was identified. Do not infer that these source speakers pronounced the words incorrectly: lexical/surface-label mismatch, realization style, representation/pooling and source conditions remain unseparated possibilities.

## 26–28. Fixed-config source-group diagnostic and firewall

After primary recording, each of the four substantial groups was held out once. Every fold refits the scaler on the other groups only, then the same unweighted linear head at **layer 8 / C=0.1**. No choices were retuned. These are **SOURCE-GROUP HELD-OUT DIAGNOSTICS**, not a pristine second final test; Luilui6666 contributes to training in other secondary folds and Levi Highway previously informed configuration selection.

| Held-out group | N | Macro F1 | Balanced accuracy | T1 recall | T2 recall | T3 recall | T4 recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Wei Gao group | 326 | 0.7567 | 0.7504 | 0.7381 | 0.6338 | 0.9630 | 0.6667 |
| CanonNi | 60 | 0.7756 | 0.8160 | 0.6667 | 1.0000 | 0.8889 | 0.7083 |
| Levi Highway | 49 | 0.8914 | 0.8813 | 0.7143 | 1.0000 | 0.9286 | 0.8824 |
| Luilui6666 | 60 | 0.7025 | 0.7432 | 1.0000 | 0.8667 | 0.1538 | 0.9524 |

All 495 assets receive one out-of-fold prediction. Aggregate accuracy **0.7717 (382/495)**, balanced accuracy **0.7738**, macro F1 **0.7765**; unweighted mean of four group macro F1s **0.7816**. The pooled aggregate is dominated by the 326-file Shtooka group and must not obscure the Luilui6666 failure. Each fold's confusion matrix is preserved in [source-group-evaluation.csv](source-group-evaluation.csv) and [source-group-metrics.json](source-group-metrics.json); [all OOF predictions](source-group-predictions.csv).

Performance is source dependent: Luilui6666 T3 recall remains 15.38% even when the secondary training set adds Levi Highway, while other groups' T3 recall is 88.89–96.30%. Source, recording condition and person effects cannot be separated with four groups. One primary held-out source/speaker group cannot support Mandarin population inference. No clip-bootstrap interval is presented as a speaker-population interval.

**No primary-test contamination occurred.** Selection and code checks completed before locking; the primary test was opened once; no research model code, preprocessing or configuration changed afterward. The only pre-selection implementation correction concerned a synthetic stereo-downmix test expectation (FFmpeg equal-power mixing); all primary audio is mono. Post-test work was fixed-config diagnostics, unchanged V1 comparison, arithmetic/artifact verification and reporting, with no feedback into model selection.

## 29–34. Decision and next pass

**INCONCLUSIVE**, not GO to integration and not evidence that neural tone recognition is impossible. The weak hypothesis—English-pretrained frozen acoustic features contain recoverable Mandarin tone information—**survives**. The stronger requirement—reliable T1–T4 across unseen voices, materially better than V1—**is not established**. Useful overall signal and a small common-subset advantage coexist with severe primary T3 collapse, marked group variation, unaudited lexical labels and only one primary test group.

V2 **materially improves the measured common-subset point estimate** (+0.0919 macro F1), but a 13-item, uneven-tone subset cannot establish robust superiority. The failure remains a substantive result; the high validation score did not predict dependable primary Tone 3 behavior.

**Experiment #2 should prioritize label/voice validation and additional independently held-out speakers**, especially listening-audited isolated T3/T4 across recording conditions. First audit the affected source clips without relabeling this completed result to improve it. Then preregister an unchanged-configuration evaluation on new groups with a protected final test. More verified speaker diversity is the immediate need; learner speech should be a separately annotated challenge panel afterward. If an independently confirmed T3 failure remains, a small preregistered temporal-pooling control is a reasonable later hypothesis before fine-tuning or architecture expansion. This pass provides no controlled evidence that switching to HuBERT, adding context or explicit F0 would solve the problem, and none was attempted.

Do not integrate this head, add confidence thresholds, change learner feedback, replace V1, change the pitch graph/UI/API/schema, or use OMPAL/Benma/Jacob/Jia material for fitting. Those recordings remain untouched. Recommended next reasoning level: **HIGH**, for independent labels, source-disjoint evaluation and careful interpretation of tone-specific failure.

## 35–38. Deliverables and validation

Research code: `remediate.py`, `features.py`, `model_probe.py`, `v1_adapter.py`, `test_model_probe.py`; research `README.md`, pinned direct `requirements.txt` and installed `requirements-lock.txt`. Existing production/data-acquisition code and original corpus manifest are unchanged. This report and `environment.md` supersede their preflight-only summaries; historical stop evidence remains in `preflight.md` and the original preflight artifacts.

Curated outputs include remediation/split manifests and hashes, checkpoint/config/lock/extraction evidence, all nine validation results, primary test probabilities, immutable primary record/opening receipt, V1 config/results/comparison, per-error records, group-fold metrics/OOF predictions and aggregate `metrics.json`. No raw audio, model weights, embedding arrays, large tensors or head/scaler binaries enter Git. Local cache is approximately **378 MiB**; ignored research virtualenv approximately **1.1 GiB**.

**52 focused tests passed** (39 inherited + 13 new), including exclusion, primary-evidence remediation, singleton/group/hash leakage rejection, label range, deterministic manifests, 16-kHz stereo loading, masked pooling, layer hooks, frozen state/determinism, train-only scaling, selection tie breaks, saved-head probabilities and lock/firewall behavior. Both a real checkpoint extraction smoke test and V1 adapter smoke test used a training clip only. Ruff lint/format checks pass for all new Python files. The pre-existing unrelated `report.py:95` lint issue was left unchanged. The production/mobile suite was not run because no production source changed.

Final artifact arithmetic, hashes, unique OOF membership, lock/code integrity and file-scope checks are recorded in [artifact-verification.json](artifact-verification.json). Final Git status/stat are in [workspace-status.txt](workspace-status.txt); untracked files do not appear in the ordinary diff stat. No staging, commit or push occurred.
