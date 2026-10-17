# Active scope update — 2026-10-17

Round 2 is complete: 18/18 whole-unit PASS and 18/18 tone-bearing PASS. Dataset
`aishell3-nucleus-coda-context-v1-20261017` is immutable. The first audio-only
four-tone experiment has completed validation-only model selection, sealed test
evaluation, and the post-freeze external probe. See the
[complete report](aishell3-training-report.md) for the 29 trials, all final metrics,
17 HuBERT errors, six archived 我想买这个 takes, and reproducibility evidence.
Chinese HuBERT context/layer-9 LR is the validation-selected winner: 90.40% test
accuracy, 89.30% balanced accuracy, 89.78% macro F1, 83.87% T3 recall. Evidence is
dominated by one held-out speaker. Core tone-ML feasibility is CLEARLY PROMISING;
current product generalization is MIXED / UNPROVEN. Production
remains frozen. The next step is an independent, more balanced speaker and physical
recording evaluation, not integration or retuning on this test set.

# Archived scope before the completed Round-2 review

AISHELL-3 pronunciation pairs are the primary actual-reading targets. A corpus
read unit can contain multiple Hanzi, including erhua. MFA supplies timing only.
The [recovery report](aishell3-recovery-report.md) records the unchanged 32-utterance
pilot plus 157 newly aligned existing recordings. Automatic QA passes for 787/789
units across 16 verified speakers; two long-phone units are quarantined. The frozen
10/3/3 speaker split has 31 test T3s and passes four-tone coverage with 729 candidates.

Human playback checks **read-unit ownership and boundary integrity**, not native
tone quality or relabeling. Round 1 failed: 18 PASS and eight non-PASS.
The [18-item Round-2 packet](data/generated/aishell3/round2-final/index.html)
asks separately about original whole units and experimental tone-bearing spans.
**Training remains blocked.** A later release can use contextual encoder input
with trustworthy tone-bearing pooling even if whole-unit onset transitions remain
fuzzy. Genuine final clipping, wrong ownership or mismatch must be resolved or
explicitly quarantined; PASS controls must not regress.
See [exact review/ingestion instructions](aishell3-qa.md).
Neutral remains in the audited data but is excluded from the first model. The
frozen baseline and encoder revision pins remain unchanged. No model selection,
test evaluation or external physical probe has occurred.

# Previous scope update — 2026-10-15

The zero-budget native-tone experiment supersedes the acceptability pilot below
for the present pass. Its [evaluation report](native-evaluation-report.md)
records a stopped Phase A data-quality audit, actual public audio extraction,
encoder smoke checks, exclusions, and all unavailable metrics. The earlier
listener-study design is preserved for later work; it is not required now.

# Perceptual acceptability feasibility protocol

The hypothesis is that frozen pretrained speech representations, combined with
Benma's existing measurements and linguistic context, can predict what native
listeners find acceptable **on previously unseen speakers**, with fewer false
confident corrections at useful incorrect-speech recall than frozen Benma.

The primary question is: “Would a reasonable native Mandarin listener consider
this syllable acceptable in this utterance?” It is not textbook contour matching.
Labels are acceptable, borderline, incorrect, ungradable. Optional perceived
T1/T2/T3/T4/unclear is stored independently; this pass does not train an auxiliary
tone-family classifier. Acoustically unusual speech may still be acceptable.

## Collection stages

Counts are engineering targets, not statistical guarantees.

| Stage | Collection | Purpose / gate |
| --- | --- | --- |
| 0 | Existing physical/research recordings; temporary fixture identities and mock annotations | Exercise manifest → packet/import → split → frozen replay → real embeddings → feature matrix → classifier → report. No model-quality inference. |
| 1 | About 300–600 labeled syllables, ideally 6–10 or more speakers, three independent native listeners per target where practical | Test whether there is enough out-of-speaker signal to justify scaling. Inspect class coverage, errors and disagreement. |
| 2 | Only if Stage 1 improves meaningfully over frozen Benma: about 1,500–3,000+ syllables, more speakers, contexts and learner mistakes | Replicate the signal and safety/recall tradeoff with broader collection. Not an automatic production/fine-tuning stage. |

Positive examples must include natural native speech, acceptable learner speech,
reduced/coarticulated connected tones, T3 sandhi and neutral tones. Negative
examples must include genuine learner errors, intentionally produced wrong-tone
versions and naturally occurring incorrect pronunciations. Keep deliberate-control
intent separate from labels and model features. Do not train mostly on synthetic
textbook contours. Each speaker should contribute varied contexts and, where
possible, multiple acceptability classes; avoid proficiency/speaker identity
becoming a surrogate target. Do not assign a desired class to meet quotas.

For the first collection, obtain roughly 50 target syllables from each of 6–10
speakers in short connected utterances. Use 30 separate practice items to agree
on the listener rubric before freezing version 1.0. Do not count practice items
as scored pilot evidence. Three independent listeners should judge every scored
item where practical. Review ungradable/high-disagreement yield before collecting
more of the same material. Known repeated takes and speaker aliases stay together.

## Annotation and consensus

Use the bilingual [listener guide](annotations/LISTENER_GUIDE.md). ACCEPTABLE
means normal enough not to correct; BORDERLINE means noticeably questionable but
not confidently wrong; INCORRECT means clearly wrong enough to correct;
UNGRADABLE means audio/segmentation prevents reliable judgment. Show the phrase and
target, play connected context, and hide system judgments/supports. Confidence and
notes are optional; no textbook contour reasoning is required.

Preserve all raw judgments and explicit revision history. The default aggregation
uses a unique ≥2/3 majority with at least three current judgments, normalized
four-label entropy ≤0.6, and no mixed ungradable/gradable votes. Unanimous mode and
thresholds are configurable. Report disagreement count/entropy and excluded cases;
never force ties into a class. Ungradable and unresolved examples remain in the
manifest and coverage reporting, while classifier fitting uses only three-class
human consensus. Training rederives labels from raw judgments, not cached consensus.

## Speaker partitions and leakage

Split persistent speaker IDs with a deterministic hash ordering and the frozen
seed `20261015`; allocate approximately 60/20/20 by largest remainder, reserving
at least one speaker per partition. Ten speakers produce 6/2/2; six produce 4/1/1.
These tiny held-out speaker counts cannot establish a rare-error guarantee.
There is no syllable-random split or random MLP early-stopping holdout.

Before fitting, reject a speaker, recording ID, source file/decoded PCM or cropped
PCM appearing in multiple partitions. Check source/window hashes and sample
ownership rather than trusting a renamed file. Resolve cross-session aliases in
the real speaker registry; software cannot infer true identity from audio hashes.
Require pilot/human/verified provenance for scientific runs. Reuse the same split
for every model family; never swap problematic examples across partitions.

Features are a fixed numeric allowlist. Speaker/recording/example IDs, labels,
annotator identity/notes/confidence, derived consensus, perceived-tone answers,
learner grades/coaching, free-text metadata, filenames and collection intent never
enter the matrices. Replay and compare the full deterministic payload before
training. Fit imputation/scaling/class weights only on labeled training speakers.
The only label source is the append-only listener response ledger. Human provenance
still requires an honest collection process; a JSON flag cannot prove listening.

## Encoders, views and models

Both frozen candidates, their exact revisions, preprocessing and caching are in
[embeddings/README.md](embeddings/README.md). Use the provided immutable HuBERT and
WavLM pins. Default local window is target ±0.35 s; wide is target ±1.2 s, clipped
to recording bounds. Original timings remain intact. Annotation additionally
provides the full recording. Compare both views without declaring one superior.

Start with layer-9 target mean pooling, then compare context mean and optional
concatenated target/context means using declared configs. Frozen encoders use
inference mode and no gradients. Do not fine-tune an encoder or add attention/
transformer heads. Acoustic and contextual feature groups are documented in
[features/README.md](features/README.md).

Compare Model 0 frozen Benma; Model 1 numeric Benma; Model 2 speech embeddings;
Model 3 speech + Benma; Model 4 speech + Benma + context. Models 1–4 each have
logistic regression and a small single-hidden-layer MLP. Include the
always-acceptable sanity reference. Fix a small set of configs before using test
results; broader search, fitted calibration and automatic operating-point tuning
are not part of this pass.

## Evaluation and decision gate

Run every comparison on identical held-out examples. Report validation and test
separately, with per-speaker reports, speaker-average macro F1 and syllable-micro
counts. Report the unanimous subset as well as the configured majority consensus.

| Metric | Definition |
| --- | --- |
| Confusion / per-class precision, recall, F1 | Three human-class rows and acceptable/borderline/incorrect/abstain prediction columns. Macro F1 uses all three classes; balanced accuracy averages recall over classes present. |
| Warning on acceptable | Predicted borderline or incorrect / all human-acceptable examples, including abstentions in the denominator |
| Incorrect on acceptable | Predicted incorrect / all human-acceptable examples |
| Confident false correction | Predicted incorrect with P(incorrect) ≥0.8 / all human-acceptable examples; frozen Benma uses its native CLEAR_DIFFERENCE decision |
| Confident incorrect precision | Human incorrect / all confident incorrect predictions on gradable consensus rows |
| Incorrect recall | Predicted incorrect / all human-incorrect examples; abstentions count as misses |
| Coverage | Abstention overall and on consensus rows; separate prediction counts/reasons for ungradable, disputed and insufficiently labeled cases |
| Calibration diagnostics | Multiclass Brier score, log loss, top-label ECE and ten reliability bins on all consensus rows before abstention; only learned probabilities |
| Comparison | Paired-example differences in macro F1, warning/false-incorrect rate and incorrect recall against frozen Benma, with identical denominators |

Rate metrics include numerators/denominators; absent denominators are null.
Per-class precision/F1 use zero when undefined, with support counts shown.
Probability diagnostics do not imply the probabilities are calibrated. Benma
supports are not probabilities. No baseline threshold or acoustic rule is tuned.

Argmax predictions and the reporting threshold are predeclared. Any later choice
of RED policy, recall/coverage tradeoff or false-RED budget must use validation
speakers only and be frozen before test inspection. A potential ≤1% false-RED
engineering target cannot be established by this tiny pilot. Zero observed errors
is not a zero-error guarantee. Always-acceptable has zero corrections and zero
incorrect recall and cannot count as success.

Stage 1 should justify expansion only if useful incorrect recall improves with
very few confident corrections of human-acceptable speech, without hiding mistakes
in abstention or worsening disagreement/coverage. Inspect paired failures with
listeners and report variation across held-out speakers. Cluster-bootstrap
intervals and richer native/learner/context slices are recommended before making
statistical or product claims; this first harness reports the underlying
per-speaker/per-example results but does not assert significance. If no signal
appears, improve data/representations or stop; do not relabel test data or retune
the frozen baseline to change the comparison.

The next concrete step is the first real collection and `preflight` packet workflow
in [README.md](README.md#first-real-pilot-exact-workflow). Infrastructure readiness
is the only conclusion supported by Stage 0.
