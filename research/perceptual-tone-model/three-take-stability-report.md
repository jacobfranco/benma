# Three physical takes: representation stability and runtime alignment

**Direct answer: no, small nucleus/coda boundary noise is not supported as the primary cause
of the observed cross-take variation.** The evidence supports a combination of acoustic
differences, representation sensitivity, and evidence loss. Family flips occur in only
3/10 usable cases, at 30–40 ms shifts; none occur in the tested shifts of at most 20 ms.
The strongest 这 difference survives the perturbations and accompanies a much larger measured fall.
Take 2's 想 has a serious alignment/coverage concern, while take 3's 我 exposes a different
pitch-tracking limitation. There is no clean demonstration here of model instability on
independently verified equivalent acoustic inputs.

**Recommended next experiment: replay these same three frozen takes through Benma's existing
Azure grapheme timing path and compare the frozen HuBERT outputs against this MFA diagnostic.**
Audit coverage and use explicit approximate syllable/tone regions. Precise nucleus/coda MFA
is not a demonstrated product requirement. This experiment is recommended, not implemented.

The following take numbering follows the user's list, **not capture chronology**:

| Take | Physical recording ID |
|---|---|
| 1 | `98432f75ad124110b591bd877dec3b73` |
| 2 | `d05e1d81a39b4889aa9e461fc32e6c2a` |
| 3 | `b8f38711296c418da6922d7e334661c0` |

All probabilities below are **raw classifier preferences**, not probabilities of correctness.
No perception of Jacob's own pronunciation, intended tone, model consensus, or MFA phone tone
label is used as realized-tone ground truth.

## 1. Frozen verification and scope

Before new diagnostics, all **279 files** in the three original take directories were copied
byte-for-byte into `data/generated/three-take-stability-v1/frozen/`. SHA-256 and byte counts
cover original and canonical audio, TextGrids, MFA logs/resources, `alignment/units.json`,
whole/tone/context clips, deterministic raw F0 and output, linguistic metadata, and reports.
Expanded/pilot predictions and span metadata are contained in the sealed original reports.
Additional canonical-JSON component digests identify those fields separately; these are explicitly
projection digests, not substitutes for the original file-byte hashes.

[Complete file manifest](data/generated/three-take-stability-v1/freeze-manifest.json) ·
[Component digests](data/generated/three-take-stability-v1/component-hashes.json) ·
[Final verification](data/generated/three-take-stability-v1/report-verification.json).

| Take | Canonical WAV SHA-256 | Original report SHA-256 |
|---|---|---|
| 1 | `889df70be4144007f976693874413ed172462e6d9aa59fc8215d3758b958857b` | `5a925d3ff889ef665eae6d48476afc5e802405018386797f0bc0ce2d135451eb` |
| 2 | `af0350402925e51ebebfafb6adc808830cc4a794a72e21a677fb604ea41e0a17` | `eb652dc8ea2fd410a2a3e95e5772b1104dab0f037f1e164ce135e46e49bfe67a` |
| 3 | `24c1e6f5abd1d1da9534c794884afb4f1dfb7660ce8aeb8cfc8dfa8e8ebe39ec` | `2793db932e36a5b2bd4307a450d13b913e9aaaeec5862abf465b665871d110c7` |

The frozen encoder, two model heads, releases and 413-file production baseline pass their
existing verification. All **1,381 pre-existing Git-visible source files**, including dirty
research work, were also pinned and remain unchanged. All 45 saved clips reproduce their exact
canonical PCM slices. The ten original successful learned outputs reproduce with **zero
maximum vector/probability difference**. New full-utterance F0 extraction exactly reproduces
all 15 saved within-unit retained contours. No new recordings or provider calls were made.

## 2. Inspectable comparison and crop quality

Open the [local comparison/playback report](data/generated/three-take-stability-v1/index.html)
or [side-by-side Markdown tables](data/generated/three-take-stability-v1/comparison.md).
The latter has one three-column comparison per syllable with every requested field:
whole/pooling/context bounds, duration, phones/ownership, HuBERT frame count, voiced support,
F0 frames, full expanded and pilot probabilities, deterministic family/shape/abstention,
pitch eligibility, comparison state and alignment likelihood. Also available:
[CSV](data/generated/three-take-stability-v1/comparison.csv).

Important measurement distinctions:

- “Voiced support” sums retained 10 ms F0 cells clipped to the interval; it never fills gaps.
  Frame count and cell-support duration are reported separately.
- Alignment likelihood is **utterance-level**, repeated for each unit; it is not local boundary confidence.
- For gated units, the report distinguishes a geometric HuBERT frame count from actual inference,
  which did not run.
- `comparison=INSUFFICIENT_EVIDENCE` can mean unresolved expected surface tone or neutral handling.
  It does **not** necessarily mean the recording lacks acoustic evidence.

Signal inspection supports plausible whole/final crops for take 1's first four units and take
3's 想/买/这. Take 2's 这 is also plausible. These are waveform/spectrogram/F0 assessments,
**not an independent listening attestation** that every phonetic identity is correct. Frozen
playback is supplied for that distinction.

The most important crop findings are:

- **Take 2 想:** its claimed vowel/coda lies in a noise-like interval. A substantial later
  voiced island is left outside every syllable. Whole-unit ownership fails an acoustic coverage
  plausibility check, although the TextGrid passes structural checks.
- **Take 2 我:** MFA assigns 250/320 ms to `w`; the 70 ms pool discards 22 retained voiced
  frames and nearly all the whole-unit fall. This is a suspicious internal division, even though
  the final still contains voiced material.
- **Take 2 买:** the 100 ms `m` assignment excludes most of the whole-span fall. The preceding
  orphan voiced island makes broader word ownership uncertain as well.
- **个:** all three pools are exactly 30 ms. Take 1's pool contains a burst/short residual
  signal and no retained pitch; takes 2/3 contain only 2/3 retained frames.
- **Neighbor contamination:** take 1 想's first retained frame is contiguous with 我 and
  precedes a long unvoiced gap; this likely reflects a boundary carryover. Early 个 pitch in
  all takes continues from 这, so it cannot be assumed to establish a separate usable 个 vowel.
  Context windows deliberately include neighbors; the experiment holds that context fixed.

Each of the 15 individual crop assessments is in the comparison tables.
Figures: [take 1](data/generated/three-take-stability-v1/take-1-acoustics.png),
[take 2](data/generated/three-take-stability-v1/take-2-acoustics.png),
[take 3](data/generated/three-take-stability-v1/take-3-acoustics.png),
[cross-take contours](data/generated/three-take-stability-v1/cross-take-contours.png).
SVG versions are included for export.

## 3. Controlled perturbation method

Each unit uses one frozen layer-9 hidden-state sequence from its original context waveform.
Only the half-open frame-center pooling mask changes. No encoder rerun per variant, change of
context, interpolation, model fitting, probability calibration, or parameter selection occurs.
Saved hidden arrays and their hashes establish identical reuse.

The compact grid requests 33 offset pairs: start-only, end-only, translation, and symmetric
expansion/contraction, using every 10 ms offset from −40 through +40 ms. Resulting intervals
are clamped to the original whole read unit and deduplicated. This prevents borrowing a
neighbor's final. Since the original pool ends at the whole-unit end, positive end shifts
clamp there; they are **not** falsely counted as different tests.

Original abstentions remain unclassified. Successful units' variants still require the existing
60 ms minimum, a retained F0 frame and a HuBERT frame. The result contains **189 admissible
clamped variants across 10 usable units**, including baselines. Variants can share an encoder
mask because HuBERT's frame spacing is about 20 ms. Counts are perturbation counts, not
independent statistical samples. All requested/actual offsets, rejected variants, masks,
durations, full expanded/pilot probabilities, margins and deltas are preserved in
[perturbations.csv](data/generated/three-take-stability-v1/perturbations.csv) and
[diagnostics.json](data/generated/three-take-stability-v1/diagnostics.json).

This tests local pooling sensitivity, **not** larger missing-word alignment errors, movement
of the context crop, or all possible onset/end combinations. It cannot certify every crop.

## 4. Descriptive stability results

`MARGIN-SENSITIVE` is an explicit qualitative annotation of the displayed ranges, not a new
numeric operating point. Family flips take precedence. No labels affect production.

| Unit | Take 1 | Take 2 | Take 3 |
|---|---|---|---|
| 我 | **MARGIN-SENSITIVE**: T2 16/16; preference .538–.832 | **STABLE**: T3 11/11; .870–.891 | **UNUSABLE**: no retained pool F0 |
| 想 | **BOUNDARY-SENSITIVE**: T3 19, T4 2; .377–.494 | **UNUSABLE**: no retained pool F0 | **BOUNDARY-SENSITIVE**: T3 17, T2 4; .487–.560 |
| 买 | **STABLE**: T2 21/21; .908–.998 | **BOUNDARY-SENSITIVE**: T3 19, T2 1; .587–.909 | **MARGIN-SENSITIVE**: T3 21/21; .734–.920 |
| 这 | **MARGIN-SENSITIVE**: T3 19/19; .363–.627 | **MARGIN-SENSITIVE**: T3 19/19; .775–.963 | **STABLE**: T4 20/20; .999987–1.000000 |
| 个 | **UNUSABLE**: 30 ms pool | **UNUSABLE**: 30 ms pool | **UNUSABLE**: 30 ms pool |

Totals: **3 STABLE, 4 MARGIN-SENSITIVE, 3 BOUNDARY-SENSITIVE, 5 UNUSABLE**.
Among the ten usable cases, seven keep the same family over the entire tested grid.

Ranges are each variant's winning-class preference; the machine-readable tables also retain
each class's probability and top-two margin. No family flips occur in the tested variants whose
actual changes to **both** edges are at most 20 ms. The observed flips require 30–40 ms.

## 5. 买 diagnosis

**Take 1 stays T2**, including changes in the retained dip/recovery portions; its original T2
preference is .963836. **Take 3 stays T3**, original .775875. **Take 2 does not stay T3**:
moving start +30 ms and end −30 ms changes `[2.040,2.170)` to `[2.070,2.140)`,
130→70 ms and 7→3 pooled frames. Expanded preference changes from T3=.880843 to
T2=.654603 / T3=.345024. The 40 ms symmetric contraction is below the existing minimum
and is not classified. A 30 ms shift of each edge is a large fraction of this short final;
this is material representation sensitivity, not a claim that every small shift fails.

The original whole-span F0 fall/recovery magnitudes differ:

| 买 evidence | Take 1 | Take 2 | Take 3 |
|---|---:|---:|---:|
| Whole / pool duration ms | 270 / 220 | 230 / 130 | 300 / 260 |
| Pool retained F0 frames | 21 | 13 | 25 |
| Whole largest-island fall / recovery st | 1.52 / 1.36 | 3.79 / .36 | 1.59 / .19 |
| Pool largest-island fall / recovery st | .72 / 1.36 | .23 / .36 | 1.59 / .19 |
| Pool overall pitch range st | 2.09 | .47 | 4.12 |

Take 1 has a more substantial recovery. Take 2's internal boundary removes most of its fall.
Take 3's 4.12 st overall range includes a discontinuity/rejected transition around 1.84 s;
it must not be read as a clean rise or fall. These are genuinely different measured signals,
but take 2's segmentation and take 3's pitch ambiguity prevent a pure acoustic-truth inference.
The result supports **A+B**, with evidence-quality limitations, not “take 1 definitely correct/wrong.”

Here, fall is the largest contiguous island's first value minus its minimum; recovery is
its last value minus that minimum. It is terminal recovery, not the largest interim rebound.
Overall range includes all retained samples in the stated interval and is qualified separately
when islands are fragmented.

## 6. 这 diagnosis

The T3/T3/T4 split survives every admissible perturbation. Comparable 110/100/120 ms pools
contain measured falls of **0.58 / 1.92 / 4.15 semitones**, with no terminal recovery.
Take 3's steep fall is materially different from take 1's shallow motion. Take 2 is intermediate.
Thus the strong T4 in take 3 is not explained away by ±40 ms local pooling changes.

Take 1 is diffuse and margin-sensitive; take 2 is strongly T3 despite a falling contour,
while its deterministic family is T4. That disagreement is a learner-model review candidate,
but it is not a matched-acoustics demonstration: pitch magnitude, baseline, context and
phonation differ. All three deterministic eligibility states flag short sustained support;
do not treat a deterministic T4 as authoritative realized-tone labeling.

## 7. 想 abstention and evidence-layer diagnosis

Take 2 whole=`[1.440,1.580)`, nucleus/coda=`[1.520,1.580)`, phones
`ɕ 80 ms / a 30 ms / ŋ 30 ms`. The pool has **zero** retained F0; the whole has only one
frame at 1.442 s, contiguous with preceding 我. No within-unit grid variant finds sustained
voiced support. The saved abstention is correct **for that supplied crop**.

However, MFA then assigns `[1.580,1.940)` to silence/unowned space, while the unchanged tracker
retains **21 frames at 1.732–1.932 s** there, about 210 ms of support. Waveform/spectral
structure is vowel-like. Another unowned voiced island occurs between 买 and 这.
This is strong evidence that structural TextGrid success is insufficient and whole-unit
placement/coverage is suspect. It is **not** proof that all orphan material is 想: a hesitation,
restart, nonlexical vocalization or transcript mismatch remains possible. ASR was unavailable
for these three takes. No orphan interval has been relabeled or used for model classification.

The same-parameter cross-correlation tracker also finds no F0 in the selected 60 ms pool
and does find the later island. Therefore a pure F0-tracker omission inside the selected
crop is not the strongest explanation. Primary responsibility: **MFA/reference-hypothesis
coverage**, propagated by strict span derivation. The runtime's no-support guard behaved
as implemented; no slicing/PCM corruption was found.

For usable 想, take 1 flips T3→T4 under +30/−30 ms contraction (also +40/−40, same mask).
Take 3 flips T3→T2 when the start moves 30–40 ms earlier, including frication; its retained
F0 contour barely changes. This directly demonstrates sensitivity to which contextual
hidden frames are pooled. Their original final falls, 1.38 versus 1.78 st, are fairly similar,
and both original expanded outputs are T3; the evidence identifies boundary sensitivity,
not an established cross-take learned-family error.

## 8. 个 and every other support abstention

| Case | Main cause category | Measured evidence / responsible layer |
|---|---|---|
| 个 take 1 | **Unresolved mixture**, with definite short-span gate | whole 110 ms, pool 30 ms; whole/pool F0 2/0; k 80 ms. Pool near a burst has no usable pitch; early whole support likely 这 carryover. Actual reduced/devoiced final vs late MFA nucleus unresolved. |
| 个 take 2 | **Unresolved mixture: short/reduced material + ownership**, possible MFA compression | whole 60 ms, pool 30 ms; F0 5/2; k 30 ms. Both very short observed tail and restrictive nucleus ownership; more voicing is assigned to onset. |
| 个 take 3 | **Unresolved mixture: short/reduced material + ownership**, possible MFA compression | whole 60 ms, pool 30 ms; F0 6/3; k 30 ms. Short voiced tail is observed, exact syllable boundary not independently verified. |
| 想 take 2 | **Alignment/coverage problem suspected** | pool 0 F0; whole 1 carryover frame; 21 later orphan frames. Gross coverage concern, not merely inadequate ±40 ms padding. Orphan phonetic identity unresolved. |
| 我 take 3 | **Pitch/voicing extraction limitation** | whole/pool 180/80 ms; retained AC F0 0/0 despite energy. AC selects no pitch before downstream filtering. CC finds only 3 late pool frames around 92–98 Hz; no full contour. |

No failed learned-model execution, corrupt embedding, or incorrect sample extraction was found.
The short-span and no-support guards are functioning; that does not certify the input boundaries.

For 我 take 3, the waveform and spectrum show energy consistent with a voiced segment, but
many AC candidates are weak; a few stronger candidates do not form a selected track.
This is **not evidence that Jacob produced no sound or an entirely unvoiced syllable**.
The independent raw cross-correlation check uses the same pitch range and costs and is
diagnostic only. It neither substitutes F0 nor triggers learned inference.
[Full acoustic evidence](data/generated/three-take-stability-v1/full-acoustics.json) ·
[Independent tracker check](data/generated/three-take-stability-v1/cross-correlation-check.json).

The deterministic path additionally abstains on several usable learned units. Its reasons
are retained individually in the tables: missing critical/fragmented support (notably
take 1 想), insufficient sustained support in the short finals, or ambiguous family geometry.
All three 这 have only about 100–110 ms sustained F0; deterministic families where emitted
must be read together with that insufficient-support status. `INSUFFICIENT_EVIDENCE` caused
by unresolved 我/想/买 surface expectation is a separate linguistic/comparison layer.

The complete deterministic abstention inventory is: take 1 我=`close_candidates`,
想=`missing_critical_support`, 这=`contradictory_geometry`, 个=`insufficient_support`;
take 2 我=`close_candidates`, 想/个=`insufficient_support`; take 3 我/个=`insufficient_support`,
买=`contradictory_geometry`. Close candidates and contradictory geometry are family-decision
ambiguity, not missing audio. The five insufficient-support cases correspond to the five
learned abstentions dissected above. Take 1 想's critical-support failure is driven by the
whole-unit fragment/carryover despite an intact 180 ms retained final.

The repeated 30 ms 个 finals are suspiciously uniform, but do **not** prove an implementation
bug or an acoustic duration of exactly 30 ms. Projection faithfully follows the phones.
The four-class model also has no neutral class: even adequate duration would not justify a
numbered-tone correction. No 个 classification was forced.

## 9. Cross-take model-sensitivity conclusion

我 take 1 has only a shallow whole-span fall (~0.64 st); take 2 has ~3.07 st, mostly outside
its small pool; take 3 lacks trustworthy F0. 想's two usable finals have similar falling
movement but different onset/context and boundary sensitivity. 买 and 这 differ as detailed
above. Duration, phonation and coverage vary, so these are not acoustic replicas.

**No case clearly meets the required bar for a true remaining model-instability candidate:**
plausible alignment/crop, stability to small shifts, comparable cross-take acoustic evidence,
and materially different learned predictions. Take 1 我's T2 preference on nearly level F0
and take 2 这's T3 preference on a falling short final are model/F0 disagreements for review,
not qualifying matched-acoustics instability cases. Both usable 想 cases demonstrate
pooling sensitivity, not stable cross-take disagreement. F0 is only part of HuBERT's input;
similarity in normalized pitch does not establish equivalent waveform/context features.
There is no basis here to trigger retraining, fine-tuning, calibration or Jacob-specific rules.

## 10. Latency: what the existing measurements actually say

These are the three physical takes' saved **server** measurements. Capture finalization,
upload, network and browser paint were not timed. The per-take encoder-load field is used,
not the cumulative process-load field. This avoids charging every take for the same load.

| Stage, seconds | Take 1 | Take 2 | Take 3 |
|---|---:|---:|---:|
| Recording finalization/upload | unmeasured | unmeasured | unmeasured |
| Preparation bridge (decode/canonicalization, linguistic work, presence) | .852 | .881 | .896 |
| MFA wrapper total | **12.199** | **12.448** | **12.305** |
| MFA internal logged run, nested in wrapper | 9.904 | 10.055 | 9.914 |
| Outside-internal residual: startup/wrapper/exit, not pure startup | 2.295 | 2.393 | 2.391 |
| Alignment setup, nested in internal | 4.806 | 4.811 | 4.713 |
| Feature generation, nested in setup | 3.319 | 3.408 | 3.314 |
| Graph compilation | 1.001 | 1.001 | 1.001 |
| Alignment round incl. worker coordination | 1.114 | 1.138 | 1.131 |
| Collect phone/word alignment | 1.113 | 1.135 | 1.119 |
| Alignment quality analysis | 1.045 | 1.049 | 1.045 |
| TextGrid export | .007 | .008 | .006 |
| HuBERT load this take | 0 | 0 | 2.896 |
| Learned inference/validation excluding encoder load | .215 | .170 | .254 |
| Deterministic/F0 subprocess path | .900 | .889 | .875 |
| Report work incl. spans/crops/pinyin subprocess | .809 | .796 | .750 |
| Span derivation separately | not instrumented | not instrumented | not instrumented |
| Server total, before final serialization | **14.976** | **15.184** | **17.976** |
| MFA share of measured total | **81.5%** | **82.0%** | **68.5%** |

Nested rows must not be added together. The difference between total and the displayed
top-level stage sum is small orchestration overhead. Report work is not browser rendering.
Classifier loading was about 1.24 ms once; no per-take head-loading distribution was recorded.

**MFA is confirmed dominant.** More specifically, this dev path runs a fresh
`mfa align` corpus workflow, new work directory/database/model extraction/features/graph,
even for one three-second file. Production's optional MFA adapter uses `align_one`; do not
generalize this exact timing to every MFA deployment.

The worker log for take 1 spans about 86 ms from its first alignment options entry to completion;
its logged `Processing 1-1`→`Done` interval is only **5 ms**. These timestamp bounds are not a
kernel profiler, but they decisively caution against calling the full 12 seconds acoustic
decoding. Similar measurements for every take are in `diagnostics.json`.

The installed MFA 3.3.9 `utils.py::run_kaldi_function` uses
`return_queue.get(timeout=1)` and checks worker completion after the timeout, **also in its
non-multiprocessing branch**. Repeated ~1.0-second graph/feature/collection stages and the
small worker window are consistent with substantial coordination waits. This mechanism is
supported by source and timestamps; the exact accumulated wait cost is not separately profiled.
No MFA settings, code, caching or scheduling were optimized.

## 11. Fast timing sources already in Benma

| Existing path | What is actually available | Interactive suitability and limitation |
|---|---|---|
| `pronunciation/perceived.py`, `exact-asr-then-configured-aligner-v1` | Exact persisted single-character tokens with matching character offsets and `timing` take precedence; complete coverage skips aligner | Local mapping is cheap. Current default OpenAI adapter returns logprob tokens and `segments=None`, not timestamps. None of these three takes has ASR timing. |
| `speech/providers/openai.py` | Audio-only transcript, fixed nonsemantic language policy, logprobs | No word/segment timestamps requested or mapped in this adapter. Token probability is not token time. |
| `pronunciation/azure_alignment.py` | Exact provider `Syllables`/`Grapheme` offsets; single-character word fallback; grouped words retained when character timing is absent | Already implemented live timing option. Historical local report records .892/1.119/1.503 s provider calls; current network latency unmeasured. Mapping ~1 ms. Grapheme coverage can be partial. |
| Legacy target Azure/SAPI and Tencent assessment adapters | Word/phone timing exists in provider evidence; Azure SAPI can label an entire syllable as a “phone” | Not proven nucleus boundaries; reference tone/assessment score is not audio truth. Tencent is not wired as the perceived-speech aligner. |
| `alignment.py` MFA parser | Syllable/word tier; grouped words deliberately not divided | Actual production parser does not expose research nucleus/coda ownership. |
| Praat `acoustics.py`, `pitch_evidence.py`, `tone_graph.py` | Full-utterance timestamped pitch and immutable track, independent of alignment | Already warmable alongside ASR. Historical warm extraction ~41.56 ms + track construction 7.54 ms; projection/eligibility well below 1 ms. F0 islands do not identify syllables or unvoiced consonants. |
| `audio/presence.py` | Audio-only activity/periodicity support summaries | Presence check, not labeled syllable boundaries. |
| Research Silero VAD | Speech regions, preloaded CPU path | Historical representative 2.856 s clip ~10.9–14.8 ms warm; not integrated because quality acceptance failed. Cannot partition syllables. |
| Replay aligner | Equal-duration synthetic intervals | Test-only timing, not an acoustic replacement. |

Code paths above are under `services/api/src/benma_api/`.
Historical timing sources:
[ASR/Azure audit](../../docs/development/perception-alignment-pitch-2026-09-18.md),
[pitch timing](../../docs/research/pronunciation-v2/2026-10-05-utterance-evidence/latency.md),
[VAD timing/quality caveat](../../docs/research/pronunciation-v2/2026-10-06-silero-vad/latency.md).
These existing measurements were reused; no other recordings were analyzed in this pass.

## 12. Replacement options

Expected timings below are explicitly historical observations or engineering budgets/inferences,
not new benchmarks. None of these replacements was implemented.

| Option | Expected incremental timing | Complexity / segmentation quality | Target-independent acoustics | Frozen HuBERT compatibility / training |
|---|---|---|---|---|
| A. ASR timestamps + approximate syllable partition | Mapping itself roughly ms; ASR acquisition remains provider latency. Current adapter supplies no timing. | Low arithmetic cost, weak quality for grouped Mandarin words, pauses and reduced syllables. Uniform partitions can recreate the present failure. | Yes if based on audio-only ASR; supplying intended answer as recognition prompt would compromise it. | Same vector dimension, but whole/approximate pools change distribution. Inference-only evaluation possible; retraining not inherently required, equivalence not established. |
| B. Resident Mandarin CTC/phoneme aligner | Aim for <0.5 s warm incremental timing for these short clips; **unmeasured budget**, model/hardware dependent. Cold model load separate. | Medium. Character CTC aligns syllables through transcript, not precise nuclei; true phoneme models need phonetic inventory and lexicon checks. Must expose gaps and missing tokens. | Use exact audio-only recognized text, retain omissions; acoustics remains audio-only, timing is transcript-conditioned. Avoid expected-tone constraints. | Compatible audio contract for coarse syllable pools; phoneme model could supply finals. Existing frozen heads can be tested without training; deployment depends on validation. |
| C. Immediate provisional result + background/cached MFA | Immediate track/coarse result can avoid 12 s; fresh MFA still ~12 s in background. Identical-input cache cheap; fresh physical takes do not hit it. | Low–medium orchestration; corrections/provenance/versioning needed. Background MFA still has observed quality issues. | Yes with honest transcript provenance; never treat provisional timing as gold. | No training needed. Current exact-final learned result must wait unless a separate coarse representation has passed validation. |
| D. Whole-syllable/context representation | Same order as current warm encoder (~.17–.25 s for 3–4 units); exact coarser timing cost separate. | Medium evaluation burden; reduces dependence on fine internal phone division but still needs syllable identity. | Yes: retain the five-field audio-only contract. | Whole-syllable mean is dimension-compatible and already researched. No retraining to test it; a newly learned segment-free/context model would require training and is a different future option. |
| E. Existing Azure grapheme timing + whole-syllable representation | Historical .89–1.50 s timing call plus cheap mapping; useful nearer-term path, not a guarantee | Lowest integration novelty; actual character coverage must be checked, grouped words remain groups. No fabricated nuclei. | Perceived-speech path aligns exact persisted ASR text and discards scores/reference tone as evidence. Transcript-conditioned timing remains a hypothesis. | Frozen-head research comparison feasible without training; current nucleus-only adapter needs an explicit validated coarse contract. |

Current primary sources support CTC token/word/segment alignment and language-specific
alignment models; neither establishes a Benma CPU latency guarantee:
[NeMo Forced Aligner documentation](https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/tools/nemo_forced_aligner.html),
[WhisperX alignment implementation](https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py),
[WhisperX paper](https://arxiv.org/abs/2303.00747).
The WhisperX Mandarin default is a **large** language-specific model, so it should not be
called lightweight without a local measurement. A small resident Mandarin CTC aligner is the
architectural candidate; selection of an actual model requires a separate latency/coverage trial.

**Ranked engineering choices, favoring the smallest route back to interactive UX:**

| Rank | Next option | Latency basis | Effort / fidelity | Frozen HuBERT / retraining |
|---|---|---|---|---|
| 1 | Reuse Azure grapheme timestamps; explicitly approximate syllable/tone windows | Historical ~0.9–1.5 s provider timing plus cheap local mapping | Smallest integration step; real character timing where supplied, incomplete coverage must remain visible | Same frozen heads can be evaluated; no retraining required for the test, output equivalence not assumed |
| 2 | Minimal local acoustic/voicing refinement of Azure windows, only if needed | Incremental mapping/refinement budget of milliseconds after existing ~50 ms local pitch work; unmeasured | Low–medium; may avoid silence or flag missing support, cannot identify syllables from F0 alone | Compatible timing contract; no retraining; no tuned thresholds or automatic borrowing of neighbor voicing |
| 3 | Lightweight resident Mandarin CTC/phoneme alignment | <0.5 s warm is an engineering budget, not a measured result | Medium; validates coverage locally, model/language and onset fidelity need testing | Compatible coarse or phone timing; no retraining of HuBERT required to evaluate |
| 4 | Background/cached MFA for diagnostics only | Fresh one-shot pipeline still ~12 s off the interactive path; cache only helps identical inputs | Low–medium orchestration; useful audit provenance, not guaranteed better boundaries | Frozen final-pooling outputs can remain diagnostic; no retraining |
| 5 | New representation/model to reduce timing dependence | Inference latency depends on design; current encoder cost remains a useful reference | Higher evaluation/engineering cost; defer architectural changes until fast timing is tested | Whole-syllable pooling can be tested with frozen heads; learning a new representation/model would require training |

## 13. Is precise nucleus/coda MFA fundamentally necessary?

**No evidence establishes that requirement.** The original native classifier was strong,
and the previous learner report found no general improvement from nucleus/coda pooling.
Its controlled comparison changed expanded argmax on 4/15 accepted primary units without
improving resolved expected-tone agreement. Those are expectation comparisons, not learner
realized-tone accuracy. This pass adds local fragility and obvious coverage concerns.

A slightly coarser but acoustically supported syllable representation is a credible product
direction. The same frozen heads accept a whole-syllable mean mathematically, but changing
pooling distribution still requires an explicit evaluation. It is neither necessary to preserve
MFA because research used it nor justified to silently ship arbitrary equal-duration partitions.
See [existing learner representation findings](learner-domain-transfer-report.md).

## 14. One focused next experiment and freeze

In a **separate pass**, replay only these three frozen canonical WAVs through the existing
Azure grapheme timing adapter. Record its exact transcript/reference provenance and returned
coverage; these takes currently have no ASR timing, so do not pretend such evidence is cached.
For the initial timing-only comparison, the existing phrase can remain an explicitly labeled
reference hypothesis, never a realized-tone label or semantic prompt for recognition.
Preserve the original MFA diagnostic as the comparison baseline.

Derive explicit approximate runtime syllable/tone regions without MFA. Start with the
provider's actual character spans, retain gaps and missing coverage, and add minimal
deterministic acoustic refinement only if a concrete crop defect requires it. Do not
invent nucleus precision from a word timestamp or force 个 into a numbered class.
Reuse the same frozen expanded/pilot heads and encoder preprocessing. Keep the existing
context fixed for the first comparison so pooling effects can be separated from a
runtime-context change. Record full probabilities, family changes, frame counts, support,
crop plausibility and component/warm end-to-end timings. If a fast region lies outside
the fixed diagnostic context, flag it instead of silently clamping away relevant audio.

The question is: **can this existing fast path preserve useful learned classifications and
adequate coverage closely enough for product use?** Agreement with MFA is a stability measure,
not correctness; inspect disagreements, especially the suspect take 2 gaps. No new microphone
recordings, model training or confidence threshold selection are needed initially.
Do not add a CTC-model bakeoff to this next experiment unless the Azure result establishes
a concrete unmet requirement.

**Prioritize validating Azure's historical ~0.9–1.5 s timing route instead of the ~12 s
synchronous MFA pipeline.** A coarser fast segmentation strategy is the preferred engineering
direction. Keep MFA optional/background for diagnostics and preserve immediate utterance
pitch/partial evidence. Do not ship a record→12–15-second wait→grade interaction or optimize
UI around that delay. A warm encoder also avoids the separately observed 2.9 s load.

Production files, original takes, model weights, dependencies and frozen configurations remain
unchanged. No recording, training, fine-tuning, tuning, calibration, production optimization,
commit, push or deployment occurred.

## 15. Reproduction, focused tests, changed files and artifacts

Run from the repository root:

```sh
services/api/.venv/bin/python research/perceptual-tone-model/scripts/three_take_acoustics.py research/perceptual-tone-model/data/generated/three-take-stability-v1
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m perceptual_tone.three_take_stability
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m perceptual_tone.three_take_report
MPLCONFIGDIR=/tmp/benma-stability-matplotlib research/perceptual-tone-model/.cache/mfa-env/bin/python research/perceptual-tone-model/scripts/three_take_plots.py research/perceptual-tone-model/data/generated/three-take-stability-v1
PYTHONPATH=research/perceptual-tone-model benchmark/pronunciation_v2/.venv/bin/python -m unittest discover -s research/perceptual-tone-model/tests -p test_three_take_stability.py -v
git diff --check
```

Only new research files were added:

- `perceptual_tone/three_take_stability.py`: fixed-context inference, clamped perturbations,
  acoustic summaries, saved latency parsing and no-mutation verification.
- `perceptual_tone/three_take_report.py`: descriptive annotations, three-column comparison,
  full perturbation CSV, local playback HTML and component hashes.
- `scripts/three_take_acoustics.py`: unchanged full-utterance production F0 and independent
  same-range cross-correlation diagnostic.
- `scripts/three_take_plots.py`: waveform/spectrum/F0 PNG and SVG figures.
- `tests/test_three_take_stability.py`: focused regression and frozen-artifact checks.
- This report.

Generated artifacts are isolated in `data/generated/three-take-stability-v1/`.
Focused tests cover grid coverage/clamping/deduplication, subminimum spans, gap-preserving
F0 support, diagnostic-state precedence, latency accounting, no mutation, original-vector
reproduction, fixed hidden-state reuse, abstention preservation, report fields and orphan
evidence non-reassignment. Exact results are recorded in
[validation.txt](data/generated/three-take-stability-v1/validation.txt).

**Decision:** the diagnostic does not support small crop-boundary noise as the main cause of
the observed variation. Important 买 and 这 distinctions survive reasonable perturbations
and correspond to measured acoustic differences. Separate abstentions expose alignment
coverage, short-neutral/ownership, and pitch-support problems. The immediate engineering
bottleneck is runtime timing: the one-shot MFA pipeline is far too slow even though its core
alignment round is much faster. Next, validate the frozen HuBERT recognizer on these same
three takes using Benma's existing fast Azure timing path before considering model retraining.
