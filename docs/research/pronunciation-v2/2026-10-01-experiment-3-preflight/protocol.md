# Experiment 3 preregistration: frozen representation, linear versus nonlinear

Status: PRE-FLIGHT. This protocol and its executable code are hashed in
`protocol.lock.json` before any real-data nonlinear training or fresh-test
prediction access. The date in this directory is the requested study identifier;
actual execution timestamps are UTC receipts. No fresh-test evaluation is authorized
in this pass. A future evaluation implementation must itself be locked before use.

Question: does frozen layer-8 whole-clip-mean wav2vec2 contain tone information
that the fixed linear classifier does not adequately separate? Frozen lexical
T1–T4 labels are benchmark truth absent concrete contradictory evidence. A model
error alone is not such evidence. Realized-tone listening is optional diagnostics.

## Fixed representation and membership

`facebook/wav2vec2-base`, revision
`0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`; CPU FP32; eval mode, no gradients;
Transformer block 8 (`hidden_states[8]`); mean of every valid frame, 768 dimensions.
Use unchanged `features.py`: FFmpeg mono 16 kHz float32 decode, checkpoint waveform
normalization, one complete waveform per forward, eager attention, no encoder
attention mask/padding, trimming, cropping or augmentation. No F0, text, lexical
identity, expected tone, speaker identity, temporal thirds or fine-tuning as inputs.

Train only the original ordered 386 rows in the hash-pinned Experiment 1 split
(`1ee5ab2d6bbb6739e461c53949d699cef687d8b6e25412717400889f219e6416`).
Counts T1/T2/T3/T4: 99/83/90/114. Only Wei Gao and CanonNi train. Preserve full rows,
labels, order and provenance; membership checks compare entire rows, not just IDs.
Levi Highway's 49 rows are a development diagnostic only. Luilui's 60 and the
opened 118 (Jouketou, 雲角, Fake estate) are inspected stress sets. None may fit
scalers, models, stopping rules or hyperparameters. No new split or row expansion.

## Arm A: exactly the frozen baseline

Train-only `StandardScaler(copy=True, with_mean=True, with_std=True)`;
multinomial L2 `LogisticRegression(C=0.1, solver='lbfgs', class_weight=None,
fit_intercept=True, max_iter=3000, tol=1e-8, random_state=20260929)`.
Use pinned scikit-learn 1.7.2, one BLAS fit thread. Four classes select multinomial
loss. Re-extract only original train/Levi features, then refit. Require bitwise
identity with authoritative features, scaler arrays, classifier arrays and Levi
probabilities/predictions. Failure aborts; no tolerance relaxation or retuning.

## Arm B: one small nonlinear head

`Linear(768, 8, bias=True) → Tanh → Linear(8, 4, bias=True)`; logits in T1–T4 order.
There are **6,188 parameters** (6,152 first layer, 36 output), versus 3,076 for A.
The eight-unit bottleneck compresses width 96-fold and limits capacity to about
2.01 times A. This choice follows the actual 386-row/two-speaker training regime
and the repository's fixed, no-sweep comparison convention. It is not chosen from
Levi or stress performance. Even this head has 16 parameters per example; being
small relative to common MLPs does not eliminate overfitting risk or prove capacity
optimality. No alternative widths/activations are tested on real data.

- Standardization: identical train-only StandardScaler policy as A; fit in NumPy/
  scikit-learn precision, then cast standardized head inputs to CPU float32.
- Initialization: fixed seed **20261001** for Python, NumPy and Torch; construct
  both Linear layers in their written order, then apply Xavier uniform gain 1
  to first and second weight matrices in order; zero both biases. No pretrained
  tone parameters. One seed only, no ensemble, retries or best-seed selection.
- Optimizer: AdamW, learning rate **0.001**, betas **(0.9, 0.999)**, epsilon
  **1e-8**, amsgrad=False, foreach=False, fused=False. Decoupled weight decay
  **0.01 on both weight matrices**, zero on biases. No schedule or gradient clipping.
- Loss: unweighted mean cross entropy, no label smoothing, classes 0–3 internally.
- Batch: all **386** rows, original order, one update per epoch, no shuffling.
- Epoch cap and stopping: **exactly 200 epochs/updates**, retain final epoch.
  No patience, validation-based early stopping or best-checkpoint selection.
  Nonfinite loss, gradients or parameters abort the run without retuning.
- No dropout or additional regularization. CPU FP32, one Torch thread,
  deterministic algorithms enabled, pinned research requirements lock.
- Levi is never consulted for stopping; it may be reported after head parameters
  are locked. Synthetic fixtures exercise this exact optimizer/epoch policy and
  test determinism and learning, without changing it from fixture performance.

This pass runs synthetic nonlinear tests only, reproduces A, and locks the
protocol. The next `develop` stage fits B on 386 rows and locks both heads before
any optional development/stress report. It writes exclusive stage receipts and
refuses silent replacement. No command in this implementation opens a fresh test.

## Fresh panel selection and seal gate

Metadata inspection is allowed; model predictions are not. Audit cached sources
first, then bounded additional Lingua Libre/Wikimedia leads, then previously GREEN
sources, then OMPAL feasibility. Do not turn correctness annotations into tone
identities. Whole OMPAL sentences cannot be assigned one lexical class and cropping
is prohibited here. Do not relax coverage, identity or license rules to fill a quota.

Exclude the seven substantial previous speakers by stable ID AND normalized name:
Wei Gao, CanonNi, Levi Highway, Luilui6666, Jouketou, 雲角, Fake estate. Also exclude
previously inspected auxiliary groups Xudong Yang/Wyverald, Wang Cheng, Jun Da and
Yue Tan. Public profiles establish no known overlap, not biological identity proof.
Require explicit voice identity rather than uploader identity; unresolved aliases
remain excluded. Disclose Mandarin native status as NATIVE, LEARNER or UNKNOWN
based on explicit evidence, never a name, location, accent or broad Chinese label.
UNKNOWN is eligible but precludes a native-specific generalization claim.

Require isolated unqualified Mandarin targets, exact source/revision URLs,
per-file license evidence and attribution, and conservative singleton numbered
reading from pypinyin 0.55.0 (`heteronym=True`, neutral=5). Exclude unresolved,
polyphonic and neutral readings, even same-tone alternate readings. ShareAlike
CC BY-SA 4.0 is evaluation-only under the existing repository policy, not training
permission. Preserve originals, licenses, attribution and any change notices.

Before model access, require **at least three** independent new speakers and
**at least eight unique eligible targets in every tone for each speaker**.
Deduplicate source bytes globally and text within speaker. Rank each speaker/tone
cell by SHA256(source_asset_id UTF-8), then ID; take at most ten. All qualifying
speakers enter, with no performance-based choice. This inherits Experiment 2's
coverage scale and adds an explicit three-speaker minimum; it is a feasibility
floor, not a powered population study. Do not promote tiny/singleton speakers.

A future seal requires verified source checksums, decode success, duration and
mono-16k preprocessing compatibility, raw SHA-256 and decoded-PCM hashes, duplicate
and speaker/asset/hash overlap checks against ALL historical corpora, including
the opened 118. Freeze the final CSV bytes with SHA-256 and an exclusive seal
receipt. Bind that receipt and both fitted heads' hashes to the evaluation runner
before opening predictions once. Any later manifest mutation invalidates the seal;
no automatic replacement, retry, fallback rows or silent exclusion after opening.
If coverage is insufficient, create **no sealed-test-manifest.csv**.

## Reporting and interpretation, fixed before results

Primary evidence comes only from that new sealed speaker-disjoint panel. Report A
and B separately: accuracy, balanced accuracy, macro F1; T1–T4 precision, recall,
F1/support; 4×4 confusion matrix with true rows/predicted columns; counts and
source-tone-denominator rates for T2→T3, T3→T2, T3→T4, T4→T3. Report pooled and
per-speaker results and equal-speaker mean balanced accuracy. Pair each clip into
both correct, linear only, nonlinear only, both wrong; report B-minus-A differences.
Missing-tone subgroup balanced accuracy is undefined, not silently averaged over
fewer classes. Zero-denominator precision/F1 uses zero as in the existing harness.
Raw softmax is uncalibrated, with no abstention/confidence threshold.

Preregistered **promising** decision: B's pooled accuracy, balanced accuracy and
macro F1 must each be at least A's; at least one must improve strictly; equal-speaker
mean balanced accuracy must be at least A's. No tone's pooled precision, recall or
F1 may fall by more than **0.05 absolute**, and no speaker's balanced accuracy may
fall by more than **0.10 absolute**. These are prospective practical regression
limits, not significance or noninferiority margins. Otherwise classify mixed,
unchanged or worse from the complete metric table, without moving thresholds.
A 100%-ceiling tie preserves performance but is not evidence of extra separability.

Publish paired speaker-bootstrap 95% percentile intervals for pooled metric
*differences*: 10,000 draws with seed 20261002, sample speakers with replacement,
retain all clips of each sampled speaker and pair both heads within every draw.
Use NumPy default_rng and percentile(method='linear'); disclose the instability
of intervals from very few speakers. If intervals include zero, describe the result
as suggestive, not demonstrated superiority. No clip-independent significance
claim. No subgroup or tone tradeoff may be hidden by a single aggregate score.

Levi, opened 118 and Luilui have their own separately labeled diagnostic tables and
cannot qualify B as promising. A null result concerns this one capacity and frozen
training protocol, not absence of tone information or validity of lexical labels.
No production integration, commit or push is part of this experiment.
