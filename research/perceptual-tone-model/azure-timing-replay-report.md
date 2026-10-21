# Fast Azure timing versus the frozen MFA diagnostic reference

**Engineering result: MIXED.** Azure is fast and supplies every character timestamp, but
whole-syllable pooling is not a compatible replacement by itself. A single generic,
audio-only F0-envelope refinement improves expanded-model family agreement from **6/10
to 9/10**, restores take-1 买=T2 / take-3 买=T3, and restores 这=T3/T3/T4.
Take-2 买 still changes materially, and provider ownership of some voiced material remains
unresolved. This supports continuing with fast timing, not changing the model.

The refined path's measured stage sums imply about **0.97–1.34 s warm server processing**,
including Azure network time, F0, frozen inference, evidence I/O and a conservative report
allowance. This is a composition of measured stages, not a browser end-to-end measurement.
Cold encoder construction/loading adds **2.81–2.87 s**.

No production behavior changed. No recording, training, fine-tuning, probability
calibration, classifier adjustment, commit, push or deployment occurred.

## Scope, freeze and preserved conclusions

| Take | Frozen physical recording |
|---|---|
| 1 | `98432f75ad124110b591bd877dec3b73` |
| 2 | `d05e1d81a39b4889aa9e461fc32e6c2a` |
| 3 | `b8f38711296c418da6922d7e334661c0` |

Numbering follows the requested order, not capture chronology. The initial
[freeze manifest](data/generated/azure-timing-replay-v1/freeze-manifest.json) hashes
**1,999 pre-existing files**: all Git-visible source/dirty research files, prior stability
artifacts, original and snapshotted takes, and locked model/reference files.
All **279 original files and 279 snapshot copies** also matched their prior manifest.
The final focused verification checks all 1,999 hashes.

| Take | Canonical WAV SHA-256 |
|---|---|
| 1 | `889df70be4144007f976693874413ed172462e6d9aa59fc8215d3758b958857b` |
| 2 | `af0350402925e51ebebfafb6adc808830cc4a794a72e21a677fb604ea41e0a17` |
| 3 | `24c1e6f5abd1d1da9534c794884afb4f1dfb7660ce8aeb8cfc8dfa8e8ebe39ec` |

The frozen layer-9 encoder, expanded balanced logistic-regression head, pilot head,
class order, C=0.1, preprocessing, edge padding and inference implementation were reused.
All **10 previously successful predictions reproduce exactly for both heads**, with
maximum probability difference **0**, using the frozen MFA contracts. Encoder/model hashes
pass the existing release checks. Fresh unchanged F0 extraction exactly reproduces the
three frozen full-utterance graphs.

The previous perturbation sweep was not rerun or modified. Its conclusions stand:
small MFA pool-boundary noise was not the main cross-take explanation; no family flipped
among the 105 admissible perturbations with both changes at most 20 ms. This experiment
changes whole-region placement, context and pooling representation, often by much more
than 20–40 ms. It does not contradict that controlled result or establish a clear
learned-model-instability candidate.

## Exact existing Azure path reused

The production path was traced before editing:

* [azure.py](../../services/api/src/benma_api/speech/providers/azure.py),
  `request_azure_speech`: existing synchronous `httpx.post` transport to
  `https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=zh-CN&format=detailed`.
  The existing credential is read privately; no credential appears in output.
* [azure_alignment.py](../../services/api/src/benma_api/pronunciation/azure_alignment.py),
  `AzureSpeechAligner.align`, `AZURE_TIMING_CONFIG`, `azure_grapheme_units`:
  the replay calls the exact shared transport and mapper separately so their times can
  be measured. It uses the identical alignment configuration and a 12 s timeout.
  No parallel Azure client or production configuration change was introduced.
* The request uses `ReferenceText=我想买这个`, Mandarin, `Granularity=Phoneme`,
  `GradingSystem=HundredMark`, `Dimension=Comprehensive`, `EnableMiscue=True`,
  `PhonemeAlphabet=SAPI`. Actual responses contain word spans plus explicit
  `Words[].Syllables[].Grapheme`, `Offset`, `Duration`; SAPI reference phone labels are
  also returned but never enter region construction or learned inference.
* Offsets/durations are provider ticks divided by 10,000,000. Start is Offset; end is
  Offset+Duration. There is **no equal splitting, interpolation, fuzzy matching, onset
  guessing or timestamp repair** in the exact-grapheme mapper.
* In production, perceived speech uses persisted perceived text as the reference.
  Its `reference_kind="perceived_text"` selects the reading-independent grapheme mapper.
  The legacy target-relative path can use SAPI/readings; that path was not used here.
  This replay supplies the authorized known phrase, not independently obtained ASR text.
  Returned prose matches it, but a reference-conditioned response is not an independent
  transcript verification.
* [alignment.py](../../services/api/src/benma_api/pronunciation/alignment.py) selects
  Azure when explicitly configured or enabled under `auto`; its existing
  `AlignmentRun.latency_ms` encloses alignment and validation.
  [perceived.py](../../services/api/src/benma_api/pronunciation/perceived.py) records
  alignment latency/status, preserves provider evidence, and can retain existing token
  timing. The replay bypasses database orchestration, not provider/mapping semantics.
* A single-character word may supply its own exact word span when its character tier
  is absent. Multi-character words are not split. Missing character timing stays missing;
  mismatched or conflicting character tiers reject the word. Whole-reference mismatch,
  overlapping words or out-of-audio words fail closed. Provider timeout, HTTP failure,
  rejection and malformed JSON use existing provider exceptions. The perceived path can
  return partial/unavailable timing rather than manufacture spans.

Azure response fields `Confidence`, pronunciation scores and reference phone tone digits
are retained in raw evidence only. The classifier receives exactly five allowed fields:
audio path, audio hash, whole span, pooling span and context span. Neutral scope is gated
outside the recognizer; no numbered expected tone, resolved tone, learner grade, character
or pinyin enters its input.

## Raw timing, coverage and failures

All units are explicit provider grapheme spans. Times below are seconds; each cell is
start–end (duration ms).

| Character | Take 1 | Take 2 | Take 3 |
|---|---|---|---|
| 我 | .880–1.150 (270) | 1.060–1.520 (460) | .950–1.420 (470) |
| 想 | 1.160–1.450 (290) | 1.530–2.000 (470) | 1.430–1.760 (330) |
| 买 | 1.460–1.840 (380) | 2.010–2.510 (500) | 1.770–2.230 (460) |
| 这 | 2.010–2.220 (210) | 2.540–2.760 (220) | 2.260–2.620 (360) |
| 个 | 2.230–2.330 (100) | 2.770–2.920 (150) | 2.630–2.800 (170) |

**Structural character coverage is 15/15; missing, merged and overlapping character
timings are all 0.** Acoustic/phonetic ownership is less certain than this structural count.
The gaps between consecutive characters are 10/10/170/10 ms in take 1, and
10/10/30/10 ms in takes 2 and 3. Gaps are preserved.

The provider words are 我, 想, 买, 这个. The first three word spans equal their grapheme
spans; 这个 is 2.010–2.330 / 2.540–2.920 / 2.260–2.800 across the takes, with two explicit
graphemes. Word `Confidence` is 0.0 for every word; grapheme confidence is absent.
Utterance hypothesis confidence is .8907138 / .8530837 / .9341952. None is treated as
boundary confidence. `AccuracyScore` is not a substitute for that missing confidence.
`Lexical` is `我 想 买 这个`; display is `我想买这个。` in each response.

Raw, unfiltered returned JSON:
[take 1](data/generated/azure-timing-replay-v1/98432f75ad124110b591bd877dec3b73/azure-raw.json),
[take 2](data/generated/azure-timing-replay-v1/d05e1d81a39b4889aa9e461fc32e6c2a/azure-raw.json),
[take 3](data/generated/azure-timing-replay-v1/b8f38711296c418da6922d7e334661c0/azure-raw.json).
[Provider summary](data/generated/azure-timing-replay-v1/provider-summary.json) preserves
word identity, word timing and confidence.

There were three successful live responses. The initial sandbox attempt failed DNS before
receiving provider evidence and is preserved as `provider-failure.json`. An automatic
network approval rejection was resolved after checking the attached request's explicit
Azure replay authorization. No further authorization remains pending, and there were no
extra successful provider calls for refinement or testing.

## Representations and why refinement was evaluated

**A: raw whole-syllable pooling.** Pool the unmodified Azure character interval. Context
is that interval ±250 ms, clamped to the audio, with the frozen 200-sample zero padding
on each side. This evaluates the runtime representation, including its changed context.

**B0: existing conservative evidence-region selector.** The existing
`select_tone_evidence` in
[evidence_region.py](../../services/api/src/benma_api/pronunciation/evidence_region.py)
was evaluated on the unchanged acoustic output. It made **no boundary changes on all
15 cases**. Therefore B0=A exactly; the results explicitly reuse identical inputs/outputs,
not a fabricated second latency measurement. This selector does not generally remove
unvoiced consonant attacks and cannot be presented as vowel alignment.

**C: the frozen MFA nucleus/coda representation.** Its original whole/context/pool spans
and predictions remain unchanged. Exact inference reproduction was verified separately.

**B1: optional minimal F0-envelope refinement.** Raw results were sealed first. Observed
whole spans include long leading/trailing intervals without retained F0: for example,
take-1 这 starts at 2.010 but its first retained F0 is 2.1517; take-3 买 ends at 2.230
but its last retained F0 is 2.0803. The existing selector leaves these intervals intact.
That is a concrete pooling-representation defect, not proof of incorrect provider words.
The [pre-refinement rationale](data/generated/azure-timing-replay-v1/refinement-rationale.json)
pins the raw-result hash and all observed support endpoints.

The one generic rule is:

> Within the Azure character, pool from the first retained F0 frame minus 5 ms to the last
> retained F0 frame plus 5 ms, clamped to that same character.

The 5 ms edges are halves of the existing 10 ms tracker cell, not a tuned trim parameter.
Interior dropouts remain inside the interval. The rule does not select pitch direction,
tone shape, a preferred island, character or take, and never expands across an Azure
boundary. A no-support region remains explicitly unavailable. The Azure whole/context
is identical in A and B1, so their difference is pooling alone.

This is an approximate supported envelope, **not an exact vowel/nucleus boundary**.
The existing >=60 ms pool requirement, retained-F0 guard and neutral policy remain.
No threshold was fitted. No largest-island alternative, boundary search or model tuning
was attempted.

## Frozen-model results and probability changes

| Character | Take | MFA expanded | Raw A / B0 | Refined B1 |
|---|---|---|---|---|
| 我 | 1 | T2 | T2 | T2 |
| 想 | 1 | T3 | T3 | T3 |
| 买 | 1 | T2 | T2 | T2 |
| 这 | 1 | T3 | T2 | T3 |
| 个 | 1 | abstain | abstain | abstain |
| 我 | 2 | T3 | T3 | T3 |
| 想 | 2 | abstain | T1 | T1 |
| 买 | 2 | T3 | T3 | T2 |
| 这 | 2 | T3 | T4 | T3 |
| 个 | 2 | abstain | abstain | abstain |
| 我 | 3 | abstain | abstain | abstain |
| 想 | 3 | T3 | T2 | T3 |
| 买 | 3 | T3 | T2 | T3 |
| 这 | 3 | T4 | T4 | T4 |
| 个 | 3 | abstain | abstain | abstain |

| Descriptive metric | MFA | Raw A / B0 | Refined B1 |
|---|---|---|---|
| Expanded family agreement, both usable | reference | 6/10 (60%) | 9/10 (90%) |
| Pilot family agreement, both usable | reference | 9/10 (90%) | 9/10 (90%) |
| Expanded family changes | reference | 4 | 1 |
| All-row abstentions | 5/15 (33.3%) | 4/15 (26.7%) | 4/15 (26.7%) |
| Numbered-scope abstentions | 2/12 (16.7%) | 1/12 (8.3%) | 1/12 (8.3%) |
| Previously usable cases lost | — | 0 | 0 |
| Newly classifiable cases | — | take-2 想 | take-2 想 |

The neutral three cases are excluded from numbered-family agreement. Newly classifiable
想 has no MFA probability vector to compare; it is not counted as either agreement or
disagreement. No synthetic vector replaces an abstention.

**Meaningful changes:** four raw and one refined case change the expanded winning family.
Probability changes also matter without an argmax change. No arbitrary numeric
“meaningful shift” cutoff was invented: the tables retain every class delta, total
variation distance (half L1), confidence delta and top-two-margin delta.
An additional reference-relative descriptor counts any class outside its previously
saved admissible ±40 ms perturbation range: **10/10 raw, 7/10 refined**. This is not a
pass threshold and can include tiny low-probability excursions. Context also changes.
The 1e-6 comparison tolerance is solely numerical reproduction tolerance.

| Usable case | Raw TV | Refined TV | Raw margin Δ | Refined margin Δ |
|---|---:|---:|---:|---:|
| Take 1 我 | .150764 | .117557 | +.089764 | +.221626 |
| Take 1 想 | .252840 | .111891 | −.249041 | −.199752 |
| Take 1 买 | .051162 | .172713 | −.100192 | −.345089 |
| Take 1 这 | .270909 | .093302 | −.000833 | +.029467 |
| Take 2 我 | .468225 | .153465 | −.790527 | −.279245 |
| Take 2 买 | .326790 | .522328 | −.644922 | −.479751 |
| Take 2 这 | .577929 | .088213 | −.336276 | +.161411 |
| Take 3 想 | .191028 | .013487 | +.017177 | +.002947 |
| Take 3 买 | .366321 | .032077 | −.373184 | −.063837 |
| Take 3 这 | .001552 | .000077 | −.002688 | −.000148 |

Pilot agreement is not model consensus or truth. Its raw mismatch is take-1 这
(reference T2 → raw T3); refinement restores that pilot case but changes take-2 买
(reference T3 → refined T2). Expanded and pilot still disagree on several cases.

The [complete comparison tables](data/generated/azure-timing-replay-v1/comparison.md)
contain **every whole/pool boundary, edge/duration/frame delta, both four-probability
vectors, argmax, confidence, margin, abstention reason, span duration and measured
inference time**. [Full CSV](data/generated/azure-timing-replay-v1/full-outputs.csv)
has 90 rows: 15 cases × 3 distinct representations × 2 frozen heads.
Full-precision outputs and provenance are in
[raw-results.json](data/generated/azure-timing-replay-v1/raw-results.json) and
[voiced_envelope-results.json](data/generated/azure-timing-replay-v1/voiced_envelope-results.json).

## Known cases and ownership limits

**想, take 2.** Azure whole `[1.530,2.000)` and refined `[1.727,1.997)` cover all
21 retained frames at 1.732–1.932 from the suspicious unowned MFA interval, about 210 ms
of voiced material. They also cover six frames at 1.942–1.992 that MFA assigns to 买.
There are 27 retained frames in this Azure region, a continuous voiced island.
The prior waveform/spectral diagnosis supports plausible voiced material there; the
fresh identical F0 confirms coverage. It does **not** certify that all 27 frames belong
to 想. Expanded raw T1=.968116 and refined T1=.988844 are diagnostic model outputs,
not validated realized-tone judgments. The reference abstained for its original empty
pool. Azure improves coverage while introducing an explicit competing ownership hypothesis.

**买, take 1.** T2 survives raw (.912674) and refined (.791461), versus MFA .963836.
The refined span `[1.460,1.6867)` is close to the MFA pool `[1.480,1.700)`.
This is useful evidence that exact MFA nucleus boundaries are unnecessary for this
family distinction. The reduced probability/margin remains visible.

**买, take 3.** Raw pooling changes T3→T2 (.588441). Removing unsupported tail material
restores T3=.743798, versus MFA T3=.775875. Refined `[1.770,2.0853)` retains 16 HuBERT
frames, versus 13 in MFA and 23 raw. This is evidence for a pooling refinement, not a
whole-span-only replacement.

**买, take 2.** MFA T3=.880843 → raw T3=.554053 → refined T2=.640581.
The refined `[2.010,2.367)` is much wider than MFA `[2.040,2.170)`, with 18 versus
7 pooled frames. Its 28 retained F0 frames span two islands: 16 within the MFA 买 whole
span and 12 in later MFA-unowned material. This is **not the same geometry** as the
previous sensitive 70 ms contraction `[2.070,2.140)`, although both move the model toward
T2. It confirms representation sensitivity in that already-suspect case; it does not
identify the correct segmentation or tone. The total-variation difference .522328 is
the largest refined discrepancy and prevents treating the result as uniform compatibility.

**这, all takes.** MFA T3/T3/T4 becomes raw T2/T4/T4, then refined T3/T3/T4.
Refined expanded confidences are .458487 / .891125 / .999921. The take-1 refined pool is
only 70 ms / 3 HuBERT frames and remains diffuse. Azure ends it 40 ms before the MFA
whole end; refinement stays within that boundary and cannot recover omitted tail frames.
Take 3's refined span includes material MFA assigns to the following 个. Preserved family
agreement does not validate those ownership edges.

**我, take 3.** Azure expands the region substantially to `[.950,1.420)`, yet retained
F0 support remains zero and the learned path still abstains. The prior signal-energy
and weak/brief independent pitch findings stand. Timing alone does not resolve this
tracker/evidence limitation; this is not a claim that the speaker produced no sound.

**个.** Azure whole spans are 100/150/170 ms, versus the repeated 30 ms MFA nuclei.
Longer spans do not establish a realistic separate neutral vowel. Takes 1/2 have only
5/6 retained frames, including 3/1 frames that MFA assigns to preceding 这.
Their refined envelopes are only 46.7/57 ms and fail the unchanged 60 ms requirement.
Take 3's Azure `[2.630,2.800)` has no retained F0 and misses the earlier MFA final;
its preceding Azure 这 span includes that earlier material. No numbered prediction or
correction is forced for any 个 under either Azure representation.

[Competing-ownership evidence](data/generated/azure-timing-replay-v1/competing-ownership.json)
enumerates every retained timestamp by its old MFA owner. These are comparisons between
timing hypotheses, not new ownership labels. Prior acoustic plots/playback remain in the
unchanged [three-take report](three-take-stability-report.md).

## Latency and interactive suitability

All times below are fresh measured seconds. The three live provider requests are reused
for A/B0/B1 so representation comparisons cannot be confounded by different Azure responses.
Local inference uses a loaded encoder but **zero embedding-cache hits** in both runs.
Both heads are included.

| Stage | Take 1 | Take 2 | Take 3 |
|---|---:|---:|---:|
| Azure request, upload/network + response JSON decode | .859396 | .858485 | .667347 |
| Existing timestamp mapping | .000313 | .000048 | .000048 |
| Fresh full-utterance F0 + retained evidence graph | .168298 | .065387 | .056484 |
| Existing conservative selector B0 | .000193 | .000244 | .000214 |
| Refined numeric region derivation B1 | .000067 | .000058 | .000056 |
| Raw A inference + gating | .249650 | .264350 | .186503 |
| Refined B1 inference + gating | .247134 | .257867 | .183173 |
| Refined core sequential stage sum | 1.275208 | 1.181844 | .907108 |
| Capture + local-analysis measured wall sum, including evidence I/O | 1.292819 | 1.204345 | .926038 |
| Warm estimate including entire batch evidence-report cost | **1.336530** | **1.248056** | **.969749** |

Generation of the full three-take tables, CSV and supporting summaries took **.043711 s**;
the conservative last row charges that entire batch cost to each take. It does not include
human report-writing time. Capture time includes preserving raw/acoustic evidence.
No full deterministic family classifier was invoked: the existing F0/graph work needed
for gating and refinement is what was freshly measured. The older .88–.90 s full
deterministic path is a different workload and was not silently substituted into this table.

Encoder construction/loading took **2.872678 s** in the raw process and **2.813340 s**
in the refinement process. Classifier loading took .001270/.001254 s; existing release
verification took .432493/.432314 s. These are startup costs, excluded from warm inference
but explicitly recorded. A fully cold path would therefore be roughly **4.2–4.6 s**
including these measured setup costs, before interpreter/library import overhead.
Keep the encoder resident for interactive use.

The refined warm estimates are roughly 9–13× below the previous 12.2–12.45 s MFA pipeline
stage alone. A post-recording user wait would be this server work **plus** recorder
finalization, client→Benma upload, scheduling and browser rendering, which were not measured.
A roughly **1–2 s warm wait on a fast connection is plausible, not demonstrated end to end**.
Three calls do not measure tail latency, concurrency, retry behavior or provider reliability.

The timing budget is practical enough to optimize further; representation/ownership
validation is the remaining obstacle to an unconditional product replacement.
[Full latency records](data/generated/azure-timing-replay-v1/latency-summary.json)
explicitly distinguish stage sums from a single live server request.

## Tests, artifacts and next engineering move

Focused validation: **12 provider/mapper tests + 8 research tests passed**.
They cover raw JSON round-trip and write-once preservation, exact mapping of the saved
responses, order/overlap rejection, missing/invalid timestamps, whole-word fallback,
audio bounds, preserved gaps, independence from phone/score fields, generic envelope
construction, five-field inference allowlist, neutral/short/no-support abstention,
geometric versus actual frame counts, frozen-model identity and exact reproduction,
latency accounting and all 1,999 pre-existing hashes. Tests make no live calls.
Ruff and `git diff --check` are also checked; the final
[verification record](data/generated/azure-timing-replay-v1/verification.json) records results.

New research source/report files:

* [Capture script](scripts/azure_timing_capture.py)
* [Frozen inference experiment](perceptual_tone/azure_timing_replay.py)
* [Evidence-table generator](perceptual_tone/azure_timing_report.py)
* [Provider tests](tests/test_azure_timing_provider.py)
* [Research tests](tests/test_azure_timing_replay.py)
* This report

All generated outputs are under `data/generated/azure-timing-replay-v1/`, including
three raw responses/captures/acoustic graphs, separate raw/refined results and embedding
caches, the freeze manifest, refinement rationale, full comparison Markdown/CSV,
provider/ownership/probability-range summaries, latency records and final verification.
Pre-existing dirty work and all earlier reports remain intact.

Azure agreement with MFA does not prove correctness; disagreement does not prove Azure
wrong. Neither the supplied phrase nor provider pronunciation scores establish learner
realized-tone truth. The F0 envelope restores useful distinctions but cannot repair a
missing character tail, establish ownership across two voiced islands, or recover a
tracker failure. Selecting another boundary merely to restore take-2 买=T3 would be
reference tuning, not validation.

**Architectural branch — MIXED:** keep the single generic retained-F0-envelope refinement
as the candidate; it has now been validated on these same three frozen takes. Before
product integration or any model work, inspect the competing ownership around take-2
想/买 (1.53–2.51 s) and take-3 这/个 (2.51–2.80 s) using the frozen waveform/playback,
then validate any mechanically justified generic ownership/availability fix on these
same takes. Do not replace synchronous MFA with untrimmed whole-span pooling. No model
training, tuning or calibration is justified by this result.
