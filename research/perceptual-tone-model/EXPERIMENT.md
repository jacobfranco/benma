# First perceptual feasibility experiment

This is an offline research plan, not a production integration or a claim of
perceptual accuracy. Do not train a speech encoder from scratch. Freeze the
encoder and compare small classifiers before considering any end-to-end tuning.

## Targets and annotation

Primary target: **native-listener contextual acceptability** with labels
`acceptable`, `borderline`, `incorrect`, `ungradable`. Optional auxiliary target:
perceived family `T1`, `T2`, `T3`, `T4`, `unclear`; null means not answered.
An acceptable T3 may sound unlike a canonical T3; auxiliary labels never determine
acceptability labels. Benma GREEN is a baseline prediction, never a human label.

Ask native Mandarin listeners:

> Would you consider this syllable's pronunciation acceptable in this utterance?

UI choices map verbatim as follows: acceptable → `acceptable`;
noticeable/borderline → `borderline`; incorrect → `incorrect`;
cannot judge → `ungradable`. Define borderline as a noticeable concern that does
not justify a confident correction. Cannot judge covers audibility/ownership or
insufficient context, not merely a mild pronunciation difference.

Optional second question: “What tone does this syllable sound most like?” Permit
skipping when unsure; `unclear` means an explicit unclear response. Present this
after acceptability to reduce canonical-tone priming. Play the complete utterance
and a replayable target-centered window; show target text and position, not Benma
grades, F0, scores, prescribed tone shapes or another annotator's answer.

Use three independent listeners per pilot target. Start with 30 shared practice
items outside the scored data to clarify the rubric, then freeze it. Randomize
order and include ~10% concealed repeats to inspect listener consistency (repeats
do not count as new data). Keep every judgment and annotator pseudonym; retain
revisions separately rather than overwriting the original. Report raw counts,
pairwise agreement, class-specific disagreement and the cannot-judge fraction.

Primary hard evaluation: ≥2/3 agreement on a class. Reserve “clearly incorrect”
for 3/3 incorrect judgments (report ≥2/3 incorrect recall separately). Ties and
mixed cannot-judge cases remain disputed, receive an independent adjudication if
needed, and are reported separately; never silently force them into acceptable.
Preserve both pre-adjudication votes and the adjudicator identity/rationale.
For training, compare consensus hard labels with soft vote distributions only
after the hard-label baseline; optional tone loss remains separate and masked
when unanswered. Do not discard ungradable examples from coverage reporting.

## Inputs and first-pass models

| Group | Input and extraction |
| --- | --- |
| A: speech representation | Frozen pretrained encoder on target span ±0.5 s, clipped to recording bounds. Preserve target start/end relative to the crop. Pool target hidden states plus left/right context separately (mean and standard deviation); compare a simple whole-window mean only as an ablation. Store exact sample indices, sample rate, padding mask, model revision, layer and audio hash. |
| B: Benma acoustics/prosody | Existing normalized F0, T1–T4 supports/margins, duration, retained/raw voicing and reliability, contour geometry, clarity, probe stability, gesture strength. Keep missing masks and gap information; no invented F0. Reuse existing measurements, not new target-aware repairs. |
| C: linguistic context | Lexical tone, resolved surface tone/acceptable set and resolution basis, previous/next lexical tones, neutral context, syllable index/utterance length and phrase position when available. Unknown gets an explicit missing value. Use the same inference-time context source for all models; log ASR/reference mismatch. |

Compare on exactly the same examples and speaker partitions:

1. Frozen deterministic Benma grader: GREEN→acceptable, AMBER→borderline,
   RED→incorrect, GRAY→ungradable. Preserve its native decisions without retuning.
2. B-only multinomial logistic regression, then a small MLP.
3. A-only logistic regression/linear softmax head, then a small MLP.
4. A+B+C logistic regression, then a small MLP.

Add C-only and always-acceptable sanity baselines to detect lexical shortcuts or
an apparent gain from refusing all corrections. Do not put learner grade,
coaching text, listener labels, speaker identity or recording IDs into B/C.
An MLP starts with one 64-unit hidden layer, dropout 0.1, weight decay and early
stopping. Use a small predeclared regularization grid, three seeds, at most two
encoder candidates, and no broad hyperparameter search. Fit scaling, imputation,
feature selection/PCA if needed, class weights and all calibration on training/
validation speakers only. Log all settings and retain missingness indicators.

Initial candidate: [Tencent Chinese HuBERT base](https://huggingface.co/TencentGameMate/chinese-hubert-base),
whose author card describes audio-only pretraining on WenetSpeech and exposes
hidden-state features. Comparator: [Microsoft WavLM Base+](https://huggingface.co/microsoft/wavlm-base-plus),
whose card specifies 16 kHz audio and English pretraining. Its Mandarin utility
is a hypothesis, not established by that card. These are representation candidates,
not acceptability graders. Verify checkpoint licenses, immutable revisions,
preprocessing/sample rate and local runtime before caching embeddings. No model
download or training is part of this checkpoint. Sources checked 2026-10-15;
no new survey of Mandarin tone rules is proposed.

## Speaker-disjoint evaluation

Split **speakers**, never syllables. Stage 1 target: 30 speakers allocated
18 train / 6 validation / 6 sealed test; balance native/learner strata and recording
conditions at speaker level as far as possible. Every recording, crop, augmentation,
repeated take and session for a speaker stays together. Unknown speaker identities
are excluded from train/validation/test, not treated as independent recordings.
Deduplicate audio hashes and resolve aliases before splitting. Stage 0 speakers
and audio must not contaminate the sealed test set. Freeze a split manifest before
feature selection; never inspect test performance to choose a model.

Use grouped cross-validation inside training when useful; the
[scikit-learn grouped CV guidance](https://scikit-learn.org/stable/modules/cross_validation.html#group-k-fold)
explains why repeated observations from a subject should stay in a group. The
speaker protocol here is an engineering design; it does not claim a statistical
guarantee. Also report a secondary unseen-prompt slice if collection permits.

For learned models, predeclare a validation-only policy for RED and AMBER using
predicted incorrect/borderline probabilities; a separately selected ungradable
decision abstains. Save the thresholds before opening test labels. Do not interpret
Benma support scores as probabilities or calibrate the frozen baseline retroactively.

| Metric | Denominator / interpretation |
| --- | --- |
| False-warning rate | AMBER or RED on human ACCEPTABLE / all human ACCEPTABLE |
| False-RED rate | RED on human ACCEPTABLE / all human ACCEPTABLE |
| Incorrect recall | RED on unanimous INCORRECT / all unanimous INCORRECT; also report warning recall and ≥2/3 subset |
| RED precision | Human INCORRECT among all RED predictions on consensus gradable items; report REDs on ungradable/disputed items separately |
| Classification | Per-class precision/recall/F1, macro-F1, balanced accuracy and full confusion matrix for acceptable/borderline/incorrect; also a four-class matrix including ungradable |
| Coverage / abstention | Non-GRAY fraction overall and by human class; GRAY on incorrect counts as a miss, not an excluded denominator |
| Calibration | Multiclass Brier score, log loss and reliability plots/ECE for learned probabilities, with bins specified in advance |

Primary priority: **false confident correction of acceptable speech should be
very rare**. Compare false-RED and warning rates at matched incorrect recall or
coverage, and compare incorrect recall at a validation-selected false-RED budget
(provisional engineering goal ≤1%, to agree before training). Always-acceptable
achieves zero false-RED but zero incorrect recall and cannot pass.

Report paired differences against the frozen baseline on identical test examples,
speaker-macro as well as syllable-micro metrics, raw counts/denominators, and
speaker-cluster bootstrap intervals. Do not treat correlated syllables as
independent samples. Six test speakers cannot establish a rare-error guarantee;
zero observed false-REDs does not prove the rate is zero. Report slices for lexical
tone, T3 chains, neutral dependencies, clear/borderline speech, noise and native/
learner speech, with small-cell counts. Preserve all failures for listening review.

## Stages and decision gates

Counts below are **engineering targets, not statistical guarantees**.

| Stage | Approximate collection | Exit criterion |
| --- | --- | --- |
| 0 | Existing 13 historical recordings / 53 units, plus two newest physical recordings / 10 units. Grouped timing remains one unit. Speaker identities and native-listener labels are currently unknown. | Validate schema, canonical audio spans, frozen replay and feature alignment only; no accuracy claim or training. |
| 1 | 30 speakers × ~50 target syllables = ~1,500 labeled syllables from ~10 short connected utterances each; ~4,500 independent judgments from three listeners per target. Aim roughly half native/control and half learner speakers, and at least ~200 incorrect plus ~200 borderline targets across speakers if recruitment permits. | Learned model improves the paired safety/recall tradeoff and macro metrics over frozen Benma and trivial baselines on unseen speakers; inspect uncertainty and disagreement. Class yield is a recruitment target, never an assigned label. |
| 2 | If Stage 1 shows signal, ~100–150 speakers, ~8,000–15,000 syllables, varied proficiency, devices, rates and connected contexts, three judgments on the scored subset. | Replicate safety and incorrect-recall improvements with a new speaker-disjoint held-out collection before discussing deployment or encoder fine-tuning. |

Mix ordinary natural productions with deliberately difficult/incorrect controls;
store collection intent separately and never use it as ground truth. Ensure
individual speakers contribute multiple acceptability classes where possible so
speaker/proficiency is not a surrogate label. If pilot class coverage or listener
agreement is inadequate, improve collection/rubric first. If the signal does not
beat the baseline, stop and diagnose data/representation limitations; do not patch
more hand-coded Mandarin exceptions or quietly relabel test examples.

## Exact next implementation step and open decisions

Implement an **offline annotation-packet and dataset preflight command** that
reads this schema, verifies local audio hashes/sample spans, creates blinded
full-utterance/target-window listening items, joins persistent speaker pseudonyms,
imports raw judgments and writes a speaker-disjoint split manifest with explicit
audio/speaker overlap rejection. Validate it on Stage 0 first. Then collect the
pilot and cache frozen embeddings; no production changes are needed.

Before training, settle speaker identities and prior-corpus overlap; recruit
listeners and agree on the acceptability rubric/dialect scope; establish consent
and access for pilot recordings; pin encoder revisions/licenses and compute budget;
freeze annotation aggregation, class/condition mix, RED policy and the validation
false-RED budget. Determine whether existing backend perceived text is adequate
for annotation or a separately stored verified transcript is needed. The dataset
must preserve both if they differ rather than rewriting baseline context.
