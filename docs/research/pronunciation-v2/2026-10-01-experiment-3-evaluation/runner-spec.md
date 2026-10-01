# Experiment 3 evaluation runner, version experiment3-evaluation-v1

This is the specification locked before opening the 18-speaker, 720-clip panel.
The current pass may run only `verify` and `lock`. No evaluation is performed here.
Runner: `benchmark/pronunciation_v2/evaluate_experiment3.py`.
Use `benchmark/pronunciation_v2/.venv/bin/python` from the repository root.

## Interface and integrity

- `verify`: validate frozen inputs and read-only source/PCM checks. After a runner
  lock exists, supply `--lock-sha256` with its externally recorded SHA-256.
- `lock`: repeat verification, require a passing validation receipt matching the
  tested source/schema bytes, then exclusively create `runner.lock.json` and
  `runner.lock.sha256`. Existing locks, including partial finalizations, abort.
- `evaluate --lock-sha256 <externally recorded SHA-256>`: future pass only. Verify
  all frozen inputs, code/tests/schemas, environment, lock bytes, and all selected
  audio/PCM hashes before importing/loading an encoder or constructing a head.
  The literal lock SHA must come from the pre-opening record, not a fresh digest
  of a potentially modified lock. Git HEAD is provenance; source hashes govern
  executable identity even though this pass deliberately creates no commit.

`verify` returns `VERIFIED_SEALED_UNOPENED` only while no `opened/` claim exists.
The historical data seal remains unchanged. An exclusive `opened/` directory and
`opening-receipt.json` precede model access; every failure leaves that claim in
place. There is no retry, repair, reseal, replacement, alternative row, fallback
model, or resume command. A missing completion receipt means incomplete output.

Pinned inputs:

| Input | SHA-256 |
|---|---|
| sealed-test-manifest.csv | `141a9349da2786b822d6bbb109ff726f97b466bdb0f4548c5a7f1a2874b60490` |
| seal.json | `4de7c7d8c5d16409439f449496fe67b1980b798a645bbfcd37963b4527eb6be0` |
| head-linear.npz | `d3f1cbe4a6ac7ea7c76b4538805d57cf99a36dd7d14909432725d4bc5cf696c2` |
| head-nonlinear.npz | `eb2c29fb7473faac715b93cdb1671134d7c408dc87065166b77e50d630efd28d` |
| nonlinear arrays | `d3961629af0f7f91005c60911ea408a3fe1d149db2cc986df231765f35170659` |
| protocol.lock.json | `f795f15d970043d65592ac9ef7cd3ee4af9b36bf2310de23a840bcf12db08721` |

The protocol lock transitively binds protocol.md and the unchanged preprocessing
implementation. The encoder is facebook/wav2vec2-base revision
`0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`, with every snapshot file verified and
unexpected snapshot files rejected. The lock records all file hashes, package
versions, Python/platform, and Python/FFmpeg/FFprobe executable hashes.
Preprocessing config SHA is SHA-256 of sorted, indented UTF-8 JSON plus LF, using
`encoded()` in the runner. Source SHA separately binds features.py.

Composition must be the exact 18 sealed speaker IDs, 720 unique asset IDs, 40 per
speaker, 10 per tone/speaker, and 180 per tone. The sealed bytes preserve full row
metadata and order. Each local file's SHA-256, source SHA-256/SHA-1, archive CRC32,
byte length, source rate/channels/duration, source PCM SHA-256 and mono-16 kHz PCM
SHA-256 are recomputed. The original seal's artifact/code hashes are verified.
Four independent read-only decode workers are permitted; no model is involved.

## Frozen inference

CPU FP32, eval, no gradients; layer hidden_states[8]; mean over every valid frame;
768 dimensions. Reuse unchanged features.py FFmpeg decode, checkpoint waveform
normalization, eager attention, no encoder attention mask or padded waveform,
one complete clip per forward. No trimming, cropping, augmentation, F0, temporal
thirds, text, expected tone or speaker inputs. No embedding cache is reused or
written. Encoder uses four Torch threads and deterministic algorithms.

A uses the unchanged frozen `model_probe.predict_head` softmax implementation.
B uses the saved train-only scaler and CPU FP32 Linear(768,8) -> Tanh -> Linear(8,4)
with all saved parameters loaded strictly, eval, gradients disabled, one Torch
thread. StandardScaler float32 transform uses subtraction and division in place,
matching the training transform's intermediate precision. BLAS is limited to one
thread. Neither head is fitted. Argmax selects T1-T4; exact ties choose the lowest
numbered tone. Probabilities are uncalibrated; no confidence threshold/abstention.

## Outputs

Machine-readable contract: `benchmark/pronunciation_v2/experiment3-output-schema.json`.
It contains JSON Schema definitions and exact CSV rules; both it and the strict
schema validator are hashed. Files go only into this directory's `opened/` child:

- `predictions.csv`: UTF-8, LF, one header plus exactly 720 rows in manifest order.
- `results.json`: schema_version, panel, primary, per_speaker,
  source_declared_status_subgroups, decision.
- `bootstrap.json`: schema_version, configuration, speaker_order,
  sampled_speaker_indices, differences, intervals_95_percent, interpretation.
- `evaluation-receipt.json`: schema_version, completed_at, status, runner_lock_sha256,
  manifest_sha256, rows, speakers, test_predictions_opened, artifacts_sha256.
  Written last; binds all four other outputs plus opening-receipt.json.
- `review.md`: primary coverage, decision and every failed condition, full results
  table as JSON (including all subgroup/tone/speaker details), bootstrap intervals
  and descriptive-uncertainty caveats. The renderer is frozen in the runner.

Exact CSV column order:

```text
source_asset_id,speaker_id,source_declared_speaker_status,character,pinyin,true_lexical_tone,A_prediction,A_T1_probability,A_T2_probability,A_T3_probability,A_T4_probability,B_prediction,B_T1_probability,B_T2_probability,B_T3_probability,B_T4_probability,A_correct,B_correct
```

Status is copied from source-declared `speaker_native_status` (NATIVE/LEARNER),
character from text, and true_lexical_tone from tone. Correctness is integer 0/1.
Probabilities must be finite in [0,1], with row sum within 1e-6 of one; that is a
serialization check, never an exclusion or decision tolerance. Every prediction
is validated against its probability argmax, truth, all six identity fields,
manifest row order and unique row coverage, including a CSV round-trip check.

## Metrics and paired reporting

Primary = all 18 speakers and all 720 clips. Every arm has correct_count, support,
accuracy, balanced_accuracy, macro_f1, per_tone and confusion_matrix. Confusion
rows are true tones and columns predicted tones, both ordered T1,T2,T3,T4.
For tone t, let TP=C[t,t], S=sum(C[t,:]), P=sum(C[:,t]):

- Accuracy = trace(C)/sum(C).
- Precision = TP/P, or zero when P=0.
- Recall = TP/S, or null when S=0.
- F1 = 2*TP/(S+P), or zero when S+P=0.
- Balanced accuracy = unweighted mean of all four recalls; null if any tone absent.
- Macro F1 = unweighted mean of all four tone F1 scores, including zeros.
- Equal-speaker mean BA = unweighted arithmetic mean of 18 individual speaker BAs.

Per-tone support is S; overall support is sum(C). Directed confusions T2->T3,
T3->T2,T3->T4,T4->T3 report count C[a,b], denominator S[a], and count/denominator.
Per-speaker records include the same complete A/B metrics and B-minus-A metrics.
Each paired summary records both_correct, A_only_correct, B_only_correct and
both_wrong. Differences are B-A for the three pooled metrics, every tone's
precision/recall/F1 and every speaker's BA; primary additionally includes the
equal-speaker mean BA difference. Metrics are never rounded before comparison.

Source-declared NATIVE controls (12 speakers/480 clips) and LEARNER participants
(6/240) get separate complete paired summaries, marked SECONDARY_DESCRIPTIVE.
Neither subgroup replaces the primary panel or establishes status beyond the
source documentation. No diagnostic filtering exists.

## Promising decision: all nine conditions

1. Pooled B accuracy >= A.
2. Pooled B balanced accuracy >= A.
3. Pooled B macro F1 >= A.
4. At least one of those three strictly improves.
5. Equal-speaker mean B balanced accuracy >= A.
6. No pooled tone precision falls by more than 1/20 (0.05 absolute).
7. No pooled tone recall falls by more than 1/20.
8. No pooled tone F1 falls by more than 1/20.
9. No speaker's balanced accuracy falls by more than 1/10 (0.10 absolute).

Counts produce exact rational Fractions for decisions and differences. Exactly
0.05 and 0.10 drops are allowed; there is no epsilon/tolerance. JSON metrics are
converted to ordinary numbers only after decisions. decision.checks records each
condition/pass/details; violations identify specific tones/speakers and drops;
failed_conditions lists every failed condition. A ceiling tie fails condition 4.
A false promising flag alone is not a claim of worse performance: the complete
metric differences remain visible for mixed, unchanged or worse behavior.

## Paired speaker bootstrap

10,000 draws; NumPy default_rng(seed=20261002). Speaker IDs are sorted. Draw an
integer index array of shape (10000,18), each element uniformly in [0,18), with
replacement. Each selected speaker contributes all its clips and both arms,
including repeated contributions when selected repeatedly. Implementation sums
speaker confusion matrices, exactly equivalent to copying every selected clip.
Equal-speaker mean BA averages 18 selected-speaker BAs, retaining multiplicity.

Store B-A differences for accuracy, balanced accuracy, macro F1 and equal-speaker
mean BA for every draw, plus every sampled index. Report 2.5th and 97.5th
percentiles with numpy.percentile(method='linear'). No independent clip sampling.
No bootstrap result affects the promising decision. These are speaker-bootstrap
descriptive uncertainty intervals from only 18 speakers, not population
guarantees. Intervals containing zero do not demonstrate superiority.

## Validation and lock

Synthetic tests cover metric formulas against scikit-learn, directed denominators,
missing-tone semantics, equal-speaker weighting under unequal fixture sizes,
paired categories, subgroup separation, all differences, every decision condition,
exact and just-over limits, identity/order/metadata mutation, probability validity,
bootstrap reproducibility and explicit speaker-copy equivalence, schemas, saved
synthetic head inference, input/lock tampering and exclusive lifecycle gates.
No Experiment 3 evaluate invocation occurs in these tests.

validation.json records checks and hashes of the tested implementation/schema.
The lock binds that receipt, this specification, every local research Python file
(including transitive dependencies/tests), the schema, requirements lock,
pyproject.toml, all frozen artifacts and environment. Raw audio is never staged.
Existing research source files, model heads, protocol and data seal remain intact.
