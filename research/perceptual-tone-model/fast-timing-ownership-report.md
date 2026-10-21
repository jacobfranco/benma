# Final guarded Azure timing: READY FOR DEV PRODUCT INTEGRATION

The generic fast representation is suitable for feature-gated DEV product testing.
Azure retains **15/15 character timestamps**, the useful 买 and 这 distinctions survive,
and acoustically ambiguous take-2 买 abstains. No remaining defect requires forcing
an ownership assignment before ordinary dev testing. This is a three-recording
compatibility decision, not general recognition accuracy or a production release.

All provider responses, audio, MFA diagnostic references, previous predictions,
reports and pre-existing source were preserved. This pass made **zero Azure requests,
zero MFA runs, zero recordings and zero model changes**. The follow-up finalization
reused completed results and did not rerun inference.

## Take-2 ownership diagnosis

The original MFA 想 pool `[1.520,1.580)` contains no retained F0, while 21 retained
frames at 1.732–1.932 s were left unowned by its whole-unit timing. Azure's 想
`[1.530,2.000)` and envelope `[1.727,1.997)` recover continuous voiced support.
Its 27 retained frames / 270 ms support / 13 pooled HuBERT frames are plausible
speech evidence. Spectral and energy transitions occur near Azure's 想/买 boundary,
but voicing is continuous across it; no unique silence boundary supports confident
reallocation. Provider ownership remains a hypothesis, not a phonetic label.

Four alternatives were sealed before fresh inference: unchanged provider ownership,
midpoint between grapheme centers, nearest local minimum of the saved RMS curve
between those centers, and withholding the contiguous low-energy trough around the
provider boundary. The latter uses the existing selector's 0.6 median-energy ratio
as a diagnostic, not a new adopted boundary rule. Resulting boundaries are:

| Alternative | 想 whole end | 买 whole start | Expanded / pilot families |
|---|---:|---:|---|
| Provider | 2.0000 | 2.0100 | T1 / T2 for both heads |
| Center midpoint | 2.0125 | 2.0125 | T1 / T2 for both heads |
| Nearest saved-energy minimum | 2.0020 | 2.0020 | T1 / T2 for both heads |
| Withhold energy trough | 1.8970 | 2.0070 | T1 / T2 for both heads |

None identifies the correct ownership. The withholding alternative discards clearly
voiced sonorant material, so it is not adopted. Numeric alternatives retain the original
Azure encoder context to isolate the effect of pooling/ownership.

The more consequential ambiguity is **inside Azure 买**, whose envelope
`[2.010,2.367)` bridges retained centers 2.172→2.262 s. Four intervening saved
40 ms RMS windows, centered at 2.212/2.222/2.232/2.242 s, fall below the existing
recording energy gate 0.0052237865. Their RMS values are
0.002282/0.001118/0.000360/0.002141. This is a deep acoustic interruption, not just
an F0 tracking dropout. It does not establish whether the second portion is a
restart, interrupted continuation or another vocalization.

Diagnostic-only separate pools give:

| Pool | Duration | Retained F0 frames / support | HuBERT frames | Expanded | Pilot |
|---|---:|---:|---:|---|---|
| First `[2.010,2.177)` | 167 ms | 17 / 167 ms | 8 | T3 .530109 | T3 |
| Second `[2.257,2.367)` | 110 ms | 11 / 110 ms | 6 | T2 .913574 | T2 |
| Bridged `[2.010,2.367)` | 357 ms | 28 / 277 ms | 18 | T2 .640581 | T2 |

Neither portion was selected. The guard and final output were sealed **before** these
alternative predictions. The final path retains the numeric envelope for audit but
pools **zero frames** and returns `ambiguous_interrupted_voiced_envelope`.
This is **representation / ownership ambiguity**, not demonstrated HuBERT instability
or a new confidence threshold. Different acoustic portions need not yield the same
family. Exact same-input frozen inference reproduced exactly.

## Take-3 这 / 个

Azure 这 is `[2.260,2.620)`; its envelope `[2.3953,2.5653)` retains **all 17 supported
F0 frames**, 170 ms of support and 8 HuBERT frames. No retained final voicing is lost.
The trimmed tail still has waveform energy but no retained contour; it must not be
called absent speech. The model remains T4 .999921 under every declared boundary
alternative, including the center midpoint at 2.5775 and nearest energy trough at
2.6103 s.

Azure 个 is **170 ms**, `[2.630,2.800)`, rather than an intrinsically 30 ms provider
span. Its problem is weak/untracked voicing and competing placement, not proven
extreme duration reduction. It has zero retained F0. MFA's earlier whole 个
`[2.510,2.570)` contains six retained frames; its 30 ms nucleus contains three.
Those earlier frames are inside Azure 这's continuous final. The waveform/spectrum
provides no clear internal separation warranting moving them to 个. The F0 envelope
does not create the provider ownership difference and cannot repair it by trimming.

Actual reduction, untracked neutral speech, and exact phonetic boundaries remain
unresolved. There is energy in the later Azure 个 interval, so zero retained F0 does
not prove silence. There is no independently supported neutral nucleus outside the
selected interval that can safely be reassigned. **Neutral 个 remains outside the
four-tone classifier and must create no learner correction.** This is safe for dev
testing; it is not a claim of exact syllable alignment. Takes 1/2 also abstain, with
46.7/57.0 ms envelopes below the existing 60 ms gate.

## Exact generic candidate

1. Use the saved exact Azure grapheme spans without splitting or filling gaps.
2. Inside each span, take the first/last retained F0 centers ±5 ms, clamped to the
   provider span. Keep whole/context timing unchanged; context is Azure whole ±250 ms.
3. For consecutive retained F0 centers separated by more than 15 ms (the existing
   contiguous-island convention on a 10 ms lattice), inspect intervening saved raw
   acoustic frames. If **any RMS is below that recording's existing acoustic energy
   gate**, abstain. Do not bridge the interruption for inference, select an island,
   move ownership, or invent evidence.
4. Preserve the existing ≥60 ms duration gate, no-retained-support abstention and
   external neutral scope. Only usable numeric audio/span contracts reach resident
   frozen HuBERT layer 9 and the unchanged heads.

The threshold is the existing analyzer value:
`max(0.003, min(3 * recording_noise_floor, recording_peak_RMS * 0.15))`.
No amplitude or duration threshold was fitted. No pitch height, slope, tone family,
Hanzi, lexical tone, expected surface tone, prediction, grade, desired outcome or
speaker identity selects a span or activates the continuity guard. Neutral scope
is supplied outside the four-tone recognizer and does not select boundaries.

Take-3 买's 20 ms F0-center separation has no intervening below-gate energy and
remains usable. Legitimate glottalization can also trigger this conservative guard;
that is a possible coverage cost, not a learner error. These three recordings do
not establish the guard's wider false-abstention rate. Missing acoustic metadata
must not be treated as permission to bypass evidence validation during integration.

## Final expanded results

Confidence is the raw maximum class probability, not calibrated correctness.
MFA is a frozen diagnostic reference, **not ground truth**. NA includes matching
abstentions because no numbered-family comparison is available.

| Take | Unit | Fast status | Expanded | Raw confidence | Frozen MFA | Comparison | Abstention reason |
|---|---|---|---|---|---|---|---|
| 1 | 我 | ok | T2 | 0.915206 | T2 | same | — |
| 1 | 想 | ok | T3 | 0.382331 | T3 | same | — |
| 1 | 买 | ok | T2 | 0.791461 | T2 | same | — |
| 1 | 这 | ok | T3 | 0.458487 | T3 | same | — |
| 1 | 个 | abstained | abstain | — | abstain | NA | short pool; neutral scope |
| 2 | 我 | ok | T3 | 0.748107 | T3 | same | — |
| 2 | 想 | ok | T1 | 0.988844 | abstain | NA | — |
| 2 | 买 | abstained | abstain | — | T3 | NA | interrupted envelope / ownership ambiguity |
| 2 | 这 | ok | T3 | 0.891125 | T3 | same | — |
| 2 | 个 | abstained | abstain | — | abstain | NA | short pool; neutral scope |
| 3 | 我 | abstained | abstain | — | abstain | NA | no retained F0 |
| 3 | 想 | ok | T3 | 0.559338 | T3 | same | — |
| 3 | 买 | ok | T3 | 0.743798 | T3 | same | — |
| 3 | 这 | ok | T4 | 0.999921 | T4 | same | — |
| 3 | 个 | abstained | abstain | — | abstain | NA | neutral scope; no retained F0 |

## Compatibility and coverage accounting

| Metric | Final result |
|---|---:|
| Structural Azure coverage | 15/15; no missing or overlapping timestamps |
| Total units / numbered-scope units | 15 / 12 |
| Fast usable / MFA usable | 10 / 10 |
| Usable in both | 9 |
| Expanded family agreement, mutually usable | 9/9 |
| Pilot family agreement, mutually usable | 9/9 |
| Fast-only usable | 1: take-2 想 (MFA abstained) |
| MFA-only usable | 1: take-2 买 (fast guard abstains) |
| Abstentions, fast / MFA | 5/15 / 5/15 |
| Numbered-scope abstentions, fast / MFA | 2/12 / 2/12 |
| Abstained in both | 4: all 个 and take-3 我 |

**One of the ten previously MFA-usable cases is sacrificed.** Equal total usable
counts do not hide that loss: the newly usable 想 is a different case. Relative to
the unguarded envelope, usable count falls from 11 to 10 and abstentions rise from
4 to 5. This is preferable to forcing a numbered decision from ambiguous material.
The 9/9 figure is conditional agreement, not 100% coverage or a corrected MFA tone.

There is no remaining mutually usable family disagreement. The retained unguarded
counterfactual still disagrees on take-2 买: MFA T3 .880843 versus envelope T2 .640581,
TV .522328. The guard does not make those representations equivalent; it declines
to use the ambiguous representation. All ten final usable vectors reproduce the
prior F0-envelope vectors exactly, for both heads. The guard changes eligibility,
not probabilities. Against MFA, retained-case expanded TV ranges .000077–.172713;
largest is take-1 买 (.963836→.791461 T2). Take-1 想 (.382331 T3) and 这 (.458487 T3)
remain diffuse and must not become confident-error labels. Full per-class changes,
margins, pilot vectors, acoustic summaries and frame counts are in the evidence tables.

## Latency and resident runtime

Preserve the established estimate: **Azure request ~0.67–0.86 s; warm post-recording
server processing ~0.97–1.34 s; cold encoder load adds ~2.81–2.87 s**. These are stage
estimates, not browser stop-to-render measurements. The new guard/refinement costs
about 0.10–0.12 ms per take. Fresh resident local inference costs .258/.192/.182 s;
composing these with saved Azure/F0 stages and the old I/O/report allowance gives
.97–1.35 s, ordinary small run variation consistent with the established estimate.
No network latency was remeasured.

Keep Chinese HuBERT and classifier heads resident in one long-lived process/worker.
The existing `DevRuntime` owns a `LearnedRecognizer`, and the HTTP handler reuses
that runtime. `LearnedRecognizer.infer` loads encoder/heads only when absent; no
per-recording reload bug was found. The completed replay reused the same encoder
and head objects. Final inference had zero embedding-cache hits, so warm timing
does not depend on repeated recordings sharing cached embeddings.

**Resident HuBERT resolves the per-attempt encoder-load concern.** A fresh process
still pays encoder load (this pass 2.805 s), verification/setup (.436 s), imports
and other initialization. Thus cold processing is roughly warm work plus ~3.24 s
of measured local setup (about 4.2–4.6 s before unmeasured startup/client overhead),
whereas normal attempts use the ~one-second warm path. Azure remains the principal
network component of this timing-plus-recognizer path; separate ASR/client stages
are not included. No runtime implementation was optimized or integrated here.

## Validation and freeze

The completed lightweight checks passed: **8 final-policy + 8 existing Azure replay
+ 12 saved-provider tests = 28 tests**. They cover determinism, saved timestamp
reproduction, pitch/text/expected-tone/model-output independence, neutral safety,
interrupted-envelope abstention, dropout preservation and immutable contracts.
Fresh same-input inference reproduced all ten usable frozen MFA references for
both heads with **maximum probability difference 0**; all ten final usable cases
also reproduce prior envelope probabilities exactly. No training/corpus pipeline
was run. After the finalization request only unfinished report and freeze checks
were performed; the replay and completed tests were not repeated.

The new freeze manifest verifies **2,102 pre-existing files byte-for-byte**, including
raw Azure responses/timings, saved spans/predictions, audio, prior reports, classifiers,
encoder lock and production source. The earlier 1,999-file freeze check also passed.
`git diff --check` and whitespace checking of new research text pass. Production is
unchanged; no commit, push or deployment occurred. Final verification is recorded in
[completion-checks.json](data/generated/fast-timing-ownership-v1/completion-checks.json).

## Decision and single next pass

**READY FOR DEV PRODUCT INTEGRATION.** Integrate Azure grapheme timing → generic
F0 envelope → acoustic continuity/eligibility guard → resident frozen HuBERT into
the **normal DEV Benma pronunciation flow**. Preserve production off/default feature
gating, separate linguistic expectation, learned realized-tone recognition, neutral
handling, abstention, deterministic/F0 coaching, target-vs-heard rendering and the
existing UX. Unavailable recognition must yield no learner correction. Then return
to physical product testing. **Do not retrain or calibrate. Integration was not
performed in this pass.**

## New research files and evidence

No pre-existing file was edited. Added research source/report files:

- `fast-timing-ownership-report.md` (this report).
- `perceptual_tone/fast_timing_ownership.py` (sealed offline policy and replay).
- `perceptual_tone/fast_timing_ownership_report.py` (evidence tables).
- `scripts/fast_timing_transition_plots.py` (local scientific plots).
- `tests/test_fast_timing_ownership.py` (focused invariants).

New artifacts are isolated under `data/generated/fast-timing-ownership-v1/`:

- [Full evidence tables](data/generated/fast-timing-ownership-v1/evidence-tables.md)
  and [CSV](data/generated/fast-timing-ownership-v1/final-outputs.csv).
- [Policy sealed before inference](data/generated/fast-timing-ownership-v1/policy-before-inference.json),
  [final results](data/generated/fast-timing-ownership-v1/final-results.json),
  [all alternatives](data/generated/fast-timing-ownership-v1/alternatives.json).
- [Take-2 acoustic transition](data/generated/fast-timing-ownership-v1/take-2-transition.png)
  and [take-3 transition](data/generated/fast-timing-ownership-v1/take-3-transition.png), with SVG copies.
- [Latency composition](data/generated/fast-timing-ownership-v1/latency.json),
  [model/freeze verification](data/generated/fast-timing-ownership-v1/verification.json),
  [freeze manifest](data/generated/fast-timing-ownership-v1/freeze-manifest.json).
