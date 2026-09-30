# Experiment 2: locked temporal-pooling comparison

Protocol date: 2026-09-30. This pass does acquisition, metadata labeling, integrity
checks and protocol freezing only. No encoder forward pass, head fitting, F0
analysis, listening-based selection or model predictions on candidates. The exact
bytes of this protocol are hashed in `seal.json` before any Experiment 2 execution.
If no trustworthy complete test can be sealed, the execution gate remains closed.

## Data and contamination boundary

Keep Experiment 1's existing `split-manifest.csv` byte-for-byte unchanged:
386 training clips from Wei Gao / CanonNi, 49 development clips from Levi Highway,
and 60 Luilui6666 clips. The last group is now **previously inspected diagnostic /
stress data**, despite its historical `test` partition name. Report that new role
explicitly; never describe Luilui as pristine again. Do not delete or relabel audio.
Hash-check the original split against
`1ee5ab2d6bbb6739e461c53949d699cef687d8b6e25412717400889f219e6416`.

The new panel is exactly `sealed-test-manifest.csv`, conditional on `seal.json`
having status `SEALED`, a nonzero row count, and matching protocol, selection and
manifest hashes. Retain all selected clips as a fixed set. Any missing, changed,
undecodable or newly contradictory asset stops evaluation; no substitutions or
silent denominator changes. A subsequent scientifically justified correction must
be a new version with its reason recorded before predictions, never an overwrite.

Labels are lexical targets, not acoustic assertions of realized tone. Only
unambiguous isolated single-character Mandarin targets with one numbered pinyin
reading in pypinyin 0.55.0 (heteronym=True, neutral_tone_with_five=True) qualify.
Reject multiple readings even if they share a tone. Exclude T0/T5, unresolved text,
contradictory metadata, unknown speaker IDs and unsupported licenses. Mandarin
language IDs are Q9192 / Q727694. Do not infer native status from a name, accent,
recording location or a generic native-Chinese declaration.

Selection uses only the previously cached 1,710 single-character Commons metadata
records, not a new crawl: audit actual speaker/locutor ID, text, qualifier, language,
filename agreement and per-file license. Require at least eight eligible examples
of EACH tone per speaker; this is a coverage rule, not a model success threshold.
Rank each speaker-tone cell by SHA256(UTF-8 source_asset_id), break ties by the ID,
and select the first ten or all if fewer. No replacement after acquisition failure.
Exclude all eight speakers represented in the previous corpus, including its
audited singletons; the four substantial groups are mandatory exclusions.
Sort the final CSV by `(speaker_id, source_asset_id)`, Unicode code-point order,
UTF-8 without BOM, fixed header order, LF newlines. Hash the exact file bytes.

CC BY-SA 4.0 is considered only for the new evaluation assets: preserve the
per-file author/recorder, URL, revision, license and unchanged-original notice.
Distributed audio adaptations must retain the applicable ShareAlike obligations.
This does not change the earlier training-data policy or clear use in fitting.
Speaker independence is established at explicit source-profile ID level and checked
against known names/aliases; unrelated public pseudonyms cannot prove biological
identity. State this limit and UNKNOWN native status wherever applicable.

Before sealing: verify original byte length and SHA-1, compute SHA-256, decode to
finite PCM, record duration, reject corruption, and check source IDs, original byte
hashes and native-format decoded PCM hashes against all 500 historical corpus rows
and within the new test. Check duplicate speaker/text/pinyin metadata too. Word
overlap across speakers is allowed. These checks detect exact duplicates, not every
possible edited/re-encoded excerpt. No classifier or acoustic similarity model is
used to infer identity or eligibility.

## Exact A / B comparison

Both use frozen `facebook/wav2vec2-base`, revision
`0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`, on CPU FP32. Load the existing local
checkpoint and verify the file hashes in Experiment 1's locked configuration.
Use `hidden_states[8]`: output after transformer block 8; state 0 is the
pre-transformer input. Set eval mode, requires_grad=False, inference_mode,
eager attention, torch threads=4, deterministic algorithms=True, seed=20260929.
Check encoder state digest before/after and absence of gradients.

Decode through the same FFmpeg path to mono 16 kHz float32 PCM. Apply the pinned
checkpoint feature extractor's waveform normalization. No trim, VAD, augmentation,
ASR, expected tone, lexical identity, pinyin, F0 or speaker input. One unpadded clip
per encoder forward; pass no encoder attention mask, matching the base checkpoint's
group-norm behavior. The entire clip, including recorded silence, is retained.

Let H be the chronological matrix of VALID layer-8 frames, shape N × 768. In this
unpadded batch-size-one implementation every emitted frame is valid. If implementing
an equivalent masked test helper, gather only valid frames before binning; never
divide padded tensor length into thirds.

* **A — whole mean:** `mean(H[0:N], axis=0)`, 768 dimensions.
* **B — three means:** define integer boundaries
  `b = (0, N // 3, (2 * N) // 3, N)` and concatenate
  `mean(H[b[j]:b[j+1]], axis=0)` for j=0,1,2, in that order: 2,304 dimensions.
These are half-open contiguous bins with no overlap or lost frames. Remainder
  frames follow the floor-boundary definition, not `array_split` behavior.

Examples: N=3 → [1,1,1]; N=4 → [1,1,2]; N=5 → [1,2,2]; N=7 → [2,2,3].
The executable, model-free reference is `temporal_bin_boundaries` in
`benchmark/pronunciation_v2/evaluation_preflight.py`. Focused tests cover these
examples, exhaustive coverage/nonoverlap for N=3..999, synthetic masked frame
gathering before binning, chronological means and rejection of N<3. These tests use
only synthetic numbers, never the new evaluation audio or model outputs.
For N<3, stop that comparison and report an input eligibility failure before
fitting/scoring. Do not pad, repeat frames, insert zero means or evaluate A on a
larger cohort. A sealed-test failure blocks both arms pending a versioned data
resolution. Waveforms shorter than the existing 400-sample decoder minimum also
fail. Validate short-clip handling with synthetic hidden states before any test use.

Fit a SEPARATE StandardScaler for each arm on exactly the same 386 training rows:
per-feature training mean/population variance, zero-variance scale=1, standard
scikit-learn behavior. Apply the fitted scaler unchanged to other partitions.
Each arm fits multinomial L2 logistic regression, C=0.1, solver=lbfgs,
class_weight=None, fit_intercept=True, max_iter=3000, tol=1e-8,
random_state=20260929, one BLAS thread. Classes must be [1,2,3,4]; stop on failure
to converge. No weighting, oversampling, feature selection, dimension-dependent C
adjustment or tuning. Label prediction is probability argmax, tied classes in
ascending class order. No confidence rejection or abstention thresholds.

Use the existing locked environment: torch 2.8.0+cpu, transformers 4.57.6,
scikit-learn 1.7.2, numpy 2.3.3, scipy 1.16.2, pypinyin 0.55.0; record FFmpeg and
Python versions. The full prior dependency lock remains authoritative. In the next
implementation pass, assert B shape/order, mask/short behavior and determinism
using synthetic states; verify A reproduces the frozen baseline on development
data before unsealing. Hash the completed implementation, environment, A/B heads,
scalers and input manifests before opening the new test. Development diagnostics
cannot change layer, C, bins or representation after this freeze.

## Metrics and separate report panels

For each arm and panel report n, support for each tone, accuracy, balanced accuracy,
macro F1, per-tone precision/recall/F1 and a 4×4 confusion matrix with TRUE tones as
rows and PREDICTED tones as columns, ordered [1,2,3,4]. Define zero-division
precision/F1 as zero and disclose absent classes. Four-tone balanced accuracy is
the arithmetic mean of the four recalls; report undefined if a true class is absent,
rather than silently average a smaller set. All planned principal panels have all
four classes. Report B−A deltas and paired correctness counts for the same clips.
Show directed T2→T3, T3→T2, T3→T4, T4→T3 counts and rates (denominator=true tone
support) and both-direction confusion totals. Do not merge these three panels:

1. **Development / source-held-out diagnostics:** fixed Levi Highway validation
   (previously used for Experiment 1 choices). Also two named source diagnostics:
   fit on Wei Gao alone, evaluate CanonNi+Levi; fit on CanonNi alone, evaluate Wei
   Gao. Refit only the scaler/head on each diagnostic training subset using the
   identical fixed A/B settings; these auxiliary fits do not replace primary heads.
   Report each evaluation speaker separately. Source and speaker are confounded;
   these are previously seen development diagnostics, not fresh test evidence.
2. **New untouched speaker panel:** primary heads trained only on Wei Gao+CanonNi.
   Report each new speaker, aggregate clip-weighted metrics, and equal-speaker means
   of accuracy/balanced accuracy/macro F1. Native status must remain explicit.
   Three convenience-sampled contributors do not establish population performance;
   omit significance claims based on treating clips as independent speakers.
3. **Luilui known stress set:** the 60 unchanged historical clips, explicitly labeled
   inspected diagnostic/stress data. Summarize its T3 behavior as supporting evidence.

No pooled headline across development, fresh speakers and Luilui. No tuning on the
new panel, even after initial results. Once either arm's outputs are opened, this
panel is no longer pristine for subsequent model choices; record that opening.

## Decision and next execution gate

Temporal pooling is promising only if fresh-speaker performance improves or is
preserved AND it introduces no major new per-tone regression. Assess aggregate,
equal-speaker and individual-speaker results with supports and directed confusions.
Disclose mixed evidence; do not call a tradeoff success solely because Luilui improves.
There is no new arbitrary numeric success/regression threshold. The representation
comparison also changes dimensionality and effective regularization at fixed C;
report that limit rather than tuning it away.

Next authorized execution: verify a nonempty seal and all hashes; implement isolated
A/B extraction and tests; reproduce A on development; fit/hash both fixed heads;
then evaluate the new test once, plus the two separately named diagnostic panels.
If sealing is blocked, resolve acquisition/provenance first. Do not run a classifier
against candidate or incomplete test data while resolving the blocker.

Neural F0 is outside Experiment 2. A separate future diagnostic could compare the
already available torchcrepe estimator with Praat/current Benma F0 on the existing
forensic clips, with fixed voicing/octave-error criteria and no classifier input.
It would be an analysis of an inspected stress set, not validation of unseen tones.
No neural F0 implementation or inference is authorized by this preflight.
