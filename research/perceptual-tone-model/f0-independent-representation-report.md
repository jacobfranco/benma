# F0-independent learned-tone representation diagnosis

**Decision: MIXED. DECOUPLING IS ARCHITECTURALLY SUPPORTED; THE TESTED GENERIC
SPEECH-REGION POLICY IS NOT READY FOR INTEGRATION.** Pitch survival is not a valid
prerequisite for learned recognition. Google 买 and take-3 我 have independently
supported Azure-owned audio from which frozen HuBERT can classify without usable
pitch explanation. However, **Azure bounds plus the existing RMS gate do not yet
define a sufficiently selective generic speech region**: using the whole supported
envelope both introduces coverage losses at interrupted edge material and changes
several physical-take probability vectors/families substantially. Do not integrate
this candidate as-is, delete the old continuity guard, or lower the 60 ms minimum.

This is an additive offline diagnosis of four existing recordings, with 80 candidate
rows (20 units × four policies). No new recording, provider request, retraining,
fine-tuning, calibration, classifier change, grading/UI change, commit, push or
deployment was performed. All production/dev defaults remain unchanged.

**NOT READY for integration of a new representation selector. READY to proceed to
the next focused representation-selection experiment.** The finishing continuation
reused persisted inference, tests and freeze verification. It did not rerun the
80-row replay, any model inference, tests or full-tree hashing.

## 1. Coupling and listening evidence

The current adapter derives learned pooling from first/last **retained F0 centers**
±5 ms, clamped to Azure ownership. It then checks interruptions and the existing
60 ms minimum. Thus loss of selected pitch can remove the input to a recognizer
that otherwise uses waveform representations. Recognition, explanation and grading
are different questions; their present shared eligibility is the defect.

Exact Google attempt: `dadff527-d15b-4ceb-a652-8bdb56c7d72d`; analysis
`fc06e59f-d725-4c18-9f44-3a93de823614`; Azure evidence
`f67ea565-895f-4435-b8fd-a201691f5392`.
Canonical mono PCM16, 16 kHz audio SHA-256:
`0c0b8a82b5cb57221b16ab16999b489e882d93a2d2ab9b353572c4e29b1316ae`.

User-supplied listening QA is incorporated as evidence, not claimed as independent
listening by this agent:

| Audition | User finding |
|---|---|
| Full utterance | Sounds fine |
| Raw Azure 买 | Normal complete 买; could use slightly more initial “m” |
| Above-energy-gate crop | Does not really sound like a meaningful syllable |
| Final retained/F0-dependent crop | Essentially the same as above / not meaningful |
| Local 想–买–这 context | Sounds good |

This supersedes the earlier report's pending listening question for the raw Azure
crop. It confirms an audible representation was discarded. It does **not** establish
the exact realized tone, validate energy trimming perceptually, or make Google TTS
ground truth. In particular, the poor above-gate-crop judgment is a reason not to
select the energy candidate just because its T3 probability is larger. The old
crop manifest does not separately identify that auditioned above-gate crop; this
pass reports its newly derived numeric envelope explicitly without assuming the
two crops are byte-identical.

Google 买 Azure ownership is **[1.36, 1.65), 290 ms**. Only three Praat selected
voiced frames survive, centered at 1.3603/1.3703/1.3803 s. Pitch becomes null at
1.3903 s and remains null through the rest of the character. There are **23/29
above-gate frames**, 20 without selected F0, at saved threshold
**0.010798918764352643 RMS**. None of the three voiced frames is removed by the
energy gate or quality filtering. The final F0-derived pool is
**[1.36, 1.3853), 25.3 ms**. Continuity passes; the duration check abstains before
HuBERT. The 4.7 ms Azure left clamp is not the cause: the unclamped 30 ms envelope
also fails 60 ms. Selected-F0 dropout, propagated into pooling, explains the current
abstention; the perceptual/physical cause of that pitch dropout is not established.

## 2. Prespecified generic candidates and ownership limits

The source hashes, all selected spans, gate decisions, baseline outputs and pitch
states were sealed in [policy-before-inference.json](data/generated/f0-independent-v1/policy-before-inference.json)
before fresh inference. The known take-2 想 coverage cost was explicitly recorded
before outputs. No candidate or threshold was selected by prediction or expected tone.

| Candidate | Definition |
|---|---|
| CURRENT_REFERENCE | Unchanged production `refine_span`, retained F0 cell envelope and existing continuity/duration rules |
| AZURE_WHOLE | Full Azure character interval, subject to independent acoustic/ownership validation |
| AZURE_ENERGY_SUPPORTED | First/last above-existing-gate RMS centers ±5 ms, clamped inside Azure; no retained-F0 requirement |
| AZURE_WITH_SMALL_ONSET_CONTEXT | Azure whole plus at most 5 ms onset, clamped to the midpoint of the unassigned gap after the preceding Azure unit |

The onset allowance uses the existing acoustic half-cell width, not a 买-specific
phonetic rule. No preceding neighbor samples are owned by the candidate; overlapping
Azure owners fail closed. The right edge never exceeds the original Azure end.
Utterance limits apply. The onset variant's numeric `read_unit` expands solely to
contain its pool; the original Azure span remains separately recorded. The encoder
context stays **original Azure ±250 ms for every candidate**, so changes isolate
pooling. That context already contains neighboring audio in the frozen architecture;
pool ownership is not a claim of context-free embeddings.

Independent validation accepts only numeric boundaries, duration, ordered timestamp/RMS
pairs and the already saved recording gate. Missing/nonfinite evidence, missing
10 ms lattice coverage, missing timing and overlapping neighbors fail closed.
At least 60 ms of pool **and** above-gate cell support are required. An internal
below-gate region between supported centers yields
`ambiguous_interrupted_energy_support`; no island is chosen or bridge filled.
The additional support-duration check is experimental and causes no extra loss on
these recordings. RMS support is not a speech/noise classifier or phonetic oracle.
Here `ownership_status=safe` means the declared numeric checks pass, conditional
on Azure attribution; it does not certify phonetic boundaries across all recordings.

All three new candidates use the same guard. Rejected candidates retain spans and
geometric frame counts for audit but execute no encoder/head. This is deliberately
conservative, and it is **not** a production replacement for continuity yet.
Neutral scope is applied after span selection and before inference.

## 3. Google 买 results

Probabilities are ordered **T1/T2/T3/T4**, uncalibrated. All three broader candidates
pass the declared acoustic ownership checks; pitch explanation remains unavailable
(`too_little_sustained_evidence`) for all candidates. Retained F0 support is three
frames in every span. Current representation is invalid for inference because it
is too short, despite passing continuity.

| Candidate | Span, s | Duration | Added onset | Energy frames above gate | Actual pooled frames | Expanded probabilities | Expanded | Pilot |
|---|---|---:|---:|---:|---:|---|---|---|
| CURRENT_REFERENCE | 1.3600–1.3853 | 25.3 ms | 0 | 3/3 | **0; not run** | — | abstain | abstain |
| AZURE_WHOLE | 1.3600–1.6500 | 290.0 ms | 0 | 23/29 | 15 | .000129114 / .006280524 / .992291976 / .001298386 | T3 | T3 .973598 |
| AZURE_ENERGY_SUPPORTED | 1.3600–1.5853 | 225.3 ms | 0 | 23/23 | 11 | .000001842 / .000314175 / .999655045 / .000028938 | T3 | T3 .991706 |
| AZURE_WITH_SMALL_ONSET_CONTEXT | 1.3550–1.6500 | 295.0 ms | 5 ms | 23/29 | 15 | .000129114 / .006280524 / .992291976 / .001298386 | T3 | T3 .973598 |

Whole/energy-supported spans contain 225.3 ms of above-gate cell support. The onset
variant contains 230 ms because it includes the left part of the first cell.
The current crop contains approximately 25.3 ms. Current geometric capacity is
one encoder center, but **zero actually pooled**; the minimum is never bypassed.
The broader cases explicitly represent **learned usable + pitch unavailable**.
This restores useful inference, not a verified correct tone or a coaching contour.

Whole versus energy: expanded total variation (TV = half L1 probability distance)
is **.00736307**, same T3 family; pilot TV is **.01810822**, same T3 family.
The onset variant adds no encoder centers and exactly preserves the whole-span
embedding and both vectors. Therefore onset recovery has **no demonstrated model
effect at this allowance**. It does not prove that the onset sounds fully restored;
no new listening claim is made and no larger allowance was swept.

## 4. Same three physical takes: regression results

These are the original frozen take IDs, not the later preceding human Google-session
attempt. Exact take IDs, audio paths/hashes, pitch evidence, spans, durations, frame
counts, abstention reasons and full expanded/pilot vectors for **every** unit and
candidate are in [all-candidates.csv](data/generated/f0-independent-v1/all-candidates.csv),
[readable full table](data/generated/f0-independent-v1/all-candidates.md), and
[results.json](data/generated/f0-independent-v1/results.json). The table below gives
expanded family / actual pooled frames. It is comparison, not accuracy against a gold label.

| Take | Frozen take ID | Canonical WAV SHA-256 |
|---|---|---|
| 1 | `98432f75ad124110b591bd877dec3b73` | `889df70be4144007f976693874413ed172462e6d9aa59fc8215d3758b958857b` |
| 2 | `d05e1d81a39b4889aa9e461fc32e6c2a` | `af0350402925e51ebebfafb6adc808830cc4a794a72e21a677fb604ea41e0a17` |
| 3 | `b8f38711296c418da6922d7e334661c0` | `24c1e6f5abd1d1da9534c794884afb4f1dfb7660ce8aeb8cfc8dfa8e8ebe39ec` |

| Take | Unit | Current | Whole | Energy | Onset | Pitch explanation |
|---|---|---|---|---|---|---|
| 1 | 我 | T2 / 7 | T2 / 14 | T2 / 10 | T2 / 14 | usable measurements |
| 1 | 想 | T3 / 10 | T3 / 15 | **T1 / 14** | T3 / 15 | usable measurements |
| 1 | 买 | T2 / 11 | T2 / 19 | T2 / 19 | T2 / 19 | usable measurements |
| 1 | 这 | T3 / 3 | **T2 / 11** | **T2 / 10** | **T2 / 11** | unavailable |
| 1 | 个 | short / 0 | neutral / 0 | neutral / 0 | neutral / 0 | unavailable |
| 2 | 我 | T3 / 15 | T3 / 23 | T3 / 21 | T3 / 23 | usable measurements |
| 2 | 想 | T1 / 13 | **ownership abstain / 0** | **ownership abstain / 0** | **ownership abstain / 0** | usable measurements |
| 2 | 买 | ownership abstain / 0 | ownership abstain / 0 | ownership abstain / 0 | ownership abstain / 0 | usable measurements; ownership still blocks |
| 2 | 这 | T3 / 5 | **T4 / 11** | T3 / 9 | **T4 / 11** | unavailable |
| 2 | 个 | short / 0 | neutral / 0 | neutral / 0 | neutral / 0 | unavailable |
| 3 | 我 | no F0 / 0 | **T2 / 24** | **T2 / 21** | **T2 / 24** | unavailable |
| 3 | 想 | T3 / 11 | **T2 / 17** | **T2 / 16** | **T2 / 17** | usable measurements |
| 3 | 买 | T3 / 16 | **T2 / 23** | **T2 / 23** | **T2 / 23** | usable measurements |
| 3 | 这 | T4 / 8 | T4 / 18 | T4 / 18 | T4 / 18 | usable measurements |
| 3 | 个 | no F0 / 0 | neutral / 0 | neutral / 0 | neutral / 0 | unavailable |

All policies yield 10 usable numbered cases out of 12, but they are **not the same
10**: the new policies gain take-3 我 and lose take-2 想. All three 个 stay outside
the numbered recognizer. Broader support does not authorize numbered neutral
classification, a fifth family, or a neutral grading change.

Across **all 20 units** (Google plus the three physical takes), the aggregate is:

| Candidate | Usable | Abstained | Changed vs current | Restored | Lost | Ownership concerns | Argmax changes / both usable |
|---|---:|---:|---:|---:|---:|---:|---:|
| CURRENT_REFERENCE | 13 | 7 | 0 | 0 | 0 | 1 | 0/13 |
| AZURE_WHOLE | 13 | 7 | 8 | 2 | 2 | 3 | 4/11 |
| AZURE_ENERGY_SUPPORTED | 13 | 7 | 8 | 2 | 2 | 3 | 4/11 |
| AZURE_WITH_SMALL_ONSET_CONTEXT | 13 | 7 | 8 | 2 | 2 | 3 | 4/11 |

“Changed” counts changed usable/abstained status or changed expanded argmax, not
every probability or boundary change: two restored + two lost + four family flips.
Abstention-reason-only changes are excluded. Ownership concerns count explicit
ambiguous/interrupted states; neutral scope is not an ownership concern. Restored
cases are Google 买 and take-3 我; lost cases are take-2 想 and Google 这. The same
aggregate counts do not imply the same changed families: whole/onset flip take-2
这, while energy flips take-1 想 instead. No expected tone is used in this summary.
[Aggregate counts and completeness record](data/generated/f0-independent-v1/aggregate-summary.json).

The existing CSV has all 80 unique recording/index/candidate combinations and
includes recording/attempt ID, character, span endpoints, duration, geometric and
actual HuBERT frame counts, expanded and pilot predictions and all four probabilities,
abstention reason, pitch availability/reasons, and representation/ownership states.
No field was missing and no replay rows needed regeneration.

**Take-2 买 safety:** Azure [2.010,2.510) spans an interruption. Four saved RMS
centers 2.212/2.222/2.232/2.242 are below the unchanged .005223786537342459 gate;
values are .002282/.001118/.000360/.002141. They separate energetic portions even
if every F0 field is removed. All new candidates abstain before HuBERT; no confident
classification is manufactured. Pitch completeness reports sufficient measurements
here, which cannot override ownership ambiguity. No first/second portion is selected.

**Take-3 我:** Azure [0.95,1.42), 470 ms; energy span [0.9853,1.4153), 430 ms;
43 above-gate frames and no internal below-gate gap. There is zero retained F0.
Whole expanded probabilities are [.013453534,.836361679,.108619609,.041565178],
T2; energy probabilities [.008434773,.684721603,.243622797,.063220827], T2.
Pilot is **T3** on both (.676960/.742318). Audio can be classified while pitch is
unavailable; head disagreement and absent gold labels preclude calling it correct.

**Additional safety cost:** take-2 想 has six below-gate centers at
1.602–1.652 s between early and later energy. The old pool starts at 1.727 s and
does not bridge them. The new conservative guard rejects the full Azure support.
Google 这 also loses its previously usable T4: seven below-gate centers at
1.8803–1.9403 precede renewed edge energy. The old pool ends at 1.8353 s. Neither
new rejection proves the syllable was invalid; both expose the need to distinguish
owned speech from leading/trailing acoustic material without using F0 or predictions.

## 5. Stability and continuity diagnosis

Only mutually classified physical units are compared. Coverage changes are reported
above and not hidden as agreement. No probability-distance cutoff was fitted.

| Pair | Expanded same family | Expanded mean / max TV | Pilot same family | Pilot mean / max TV |
|---|---:|---:|---:|---:|
| Current vs whole | 5/9 | .248827 / .651128 | 8/9 | .169896 / .349412 |
| Current vs energy | 5/9 | .209557 / .394266 | 8/9 | .156926 / .373808 |
| Whole vs energy | 8/10 | .084290 / .382736 | 10/10 | .041533 / .136791 |
| Whole vs onset | 10/10 | 0 / 0 | 10/10 | 0 / 0 |

Whole versus energy also has two expanded flips: take-1 想 (T3↔T1) and take-2
这 (T4↔T3). The first changes only one pooled frame at the right edge, despite
similar durations. It is a diffuse case, not decisive evidence of wrong speech.
Take-2 我 remains T3 but whole probabilities are nearly tied between T3 .406589
and T2 .396760. Take-3 想/买 move T3→T2 on all broader variants. These are real
representation-dependent shifts; agreement with expected tones is not used to
accept or reject them. Full pairwise vector distances, embedding L2/cosine distances,
and frame counts are preserved in results.json.

Cosine distances are descriptive float32 calculations; tiny signed deviations
around zero (approximately 1e-7) are numerical roundoff. Identical whole/onset
vectors have exactly zero L2 distance and identical probabilities.

HuBERT is stable for identical inputs and for the ineffective 5 ms onset change.
It is stable across whole/energy for Google 买, but the physical comparisons do
**not** establish that broader pooling is dramatically more stable or recognition-
equivalent to the accepted fast path. Whole/energy are close for some units and
substantially different for others. More frames alone is not validation.

The current continuity guard serves **ownership/representation continuity**, not
merely pitch reliability: it catches real low-energy interruptions enclosed by
retained F0. But retained F0 determines the endpoints of its inspection window.
Consequently it neither diagnoses Google 买's lost trailing speech nor rejects
edge interruptions trimmed away with pitch. The experimental energy guard preserves
the take-2 买 safety function without pitch, yet its broader inspection window
costs two previously usable units. There is no evidence here to justify deleting
or broadly replacing the existing guard. RMS envelope selection is still too coarse.

## 6. Desired output and downstream behavior

The experiment exposes representation validity, independent ownership checks and
existing pitch eligibility separately. The conceptual eventual contract, following
existing `ok`/`abstained`, `prediction` and `pooling_span` conventions, is:

```yaml
realization:
  status: ok | abstained
  prediction: T1 | T2 | T3 | T4 | null
  probabilities: null | {T1: number, T2: number, T3: number, T4: number}
  azure_span: [start, end]
  pooling_span: [start, end] | null
  representation_reason: string
pitch_evidence:
  status: usable | unavailable
  eligibility: existing_pitch_eligibility
  measurements: existing_contour_measurements
  coaching_capability: measurements_pending_corroboration | no_specific_pitch_coaching
ownership_evidence:
  status: safe | ambiguous | invalid
  reason: string
```

`realization.status=ok` must be possible with `pitch_evidence.status=unavailable`
when representation/ownership passes. `usable` pitch here means existing eligibility
permits measurements, not that any particular tone explanation is established.
Specific coaching still requires the existing contour confidence, direction and
family corroboration. Ownership ambiguity has priority over both branches.

Two explicitly valid state combinations demonstrated by the experiment are:

| Evidence case | Ownership / representation | Learned tone | Pitch evidence |
|---|---|---|---|
| Google 买, whole Azure candidate | safe under the declared checks | usable | unavailable |
| Take-2 买, every new candidate | ambiguous | abstain | measurements may exist; cannot override ambiguity |

Grading follows these branches and compares usable recognition against the
contextual expectation. It does not choose the acoustic region.

Expected downstream behavior, **documented only; no grading implementation change**:

- Usable learned family matching the resolved expectation: grade normally even
  without specific pitch coaching.
- Learned mismatch with unavailable/nondecisive pitch evidence: retain the existing
  nondecisive/amber policy; do not invent a contour explanation.
- Learned mismatch with decisive F0 corroboration: existing red correction remains possible.
- Ambiguous ownership: abstain and issue no correction.
- Neutral scope remains downstream and outside the four-tone recognizer.

## 7. Decision and exactly one next engineering pass

**C. MIXED / ONE SPECIFIC DEFECT REMAINS: independent selection of the owned speech
region is not yet adequate.** The two manifestations are edge-interruption coverage
loss and large representation-dependent shifts. This does not vindicate pitch as
a necessary recognition gate, and it does not establish that every broader result
is wrong. It means the generic replacement has not passed the requested stability
and regression conditions. No candidate is promoted based on Google T3 agreement.

The next pass should be **one offline generic speech-region / ownership-selection
experiment on these same frozen recordings**, keeping both heads and all existing
thresholds frozen. Reuse the already implemented waveform, **10 ms RMS trace and
20 ms-window / 5 ms-hop spectrogram** in
[fast_timing_transition_plots.py](scripts/fast_timing_transition_plots.py), alongside
the saved analyzer's 40 ms RMS windows sampled every 10 ms. These are available
diagnostic cues, not newly validated segmentation rules. The smallest useful
investigation is whether their local onset/offset and internal-gap structure can
distinguish peripheral support from an interruption inside the intended syllable.
No new speech model, pitch-period estimator, DSP parameter sweep or onset-padding
tuning is proposed.

Inspect interrupted edge material (take-2 想, Google 这) and the largest existing
whole/current shifts, then seal **at most one** target-independent region refinement
before new inference. It must not depend on successful F0, Hanzi, speaker identity,
expected tone, model outputs or desired grade. It must preserve safely owned audible
speech, clamp to neighbor/utterance limits, explicitly detect internal split support,
produce deterministic spans, respect 60 ms, and preserve external neutral handling.
Do not rescue a case by choosing an arbitrary largest island. The selector must
distinguish **pitch tracker failure** from **speech ownership / representation
ambiguity**; pitch unavailability alone is not the latter.

The next pass's core acceptance contrast is precise:

- **Google 买:** a plausibly complete, continuous, safely Azure-owned region of at
  least 60 ms remains usable with F0 removed; HuBERT is allowed to run, while pitch
  explanation remains unavailable. No requirement to predict T3 is permitted.
- **Take-2 买:** the known internal split at 2.212–2.242 s remains ownership-ambiguous,
  with zero pooled frames, no numbered inference and no correction.
- **Coverage controls:** take-2 想 and Google 这 must not lose their useful owned
  speech solely because of peripheral energy. If a safe selection cannot be justified
  independently, report failure rather than force coverage. Take-3 我 must retain
  its valid F0-independent region, without asserting a correct tone.
- **All-unit controls:** no neighbor swallowing, neutral numbered inference, relaxed
  minimum, or output-driven span selection; repeat selection yields identical spans.
  Compare every existing unit's frame counts and probability vectors. Investigate
  material family shifts using acoustic ownership evidence; neither copying old
  argmax nor matching expected tone establishes success. Unexplained composition
  sensitivity blocks integration; do not fit a stability cutoff to these outputs.

If these conditions cannot be met, report the remaining limit rather than fitting
exceptions. Reuse this frozen baseline and produce only the additional candidate's
results; no need to rerun the already persisted four-policy replay. Do not move
production pooling to whole-span/energy-envelope selection yet. A validated policy
would then permit a later isolated integration: new learned pooling, unchanged F0
extraction, linguistic grading, neutral handling, UI and frozen HuBERT.

The **60 ms minimum remains unchanged**. This pass recovers 225–470 ms speech
representations where evidence exists; it never asks HuBERT to classify a 25 ms fragment.

## 8. Verification, artifacts and reproduction

- **17 focused diagnostic tests passed**: F0-independent validity; safe Azure span;
  onset/neighbor clamping; overlapping ownership and internal interruptions;
  missing/nonfinite metadata and silence; 60 ms minimum; Google evidence; original
  three-take cases; take-2 safety and explicit coverage cost; take-3 recognition;
  neutral abstention; restricted numeric selection/inference interfaces; deterministic
  plan reproduction; frozen model/output exactness; production/UI/default hashes.
- **67 existing API tests passed**: dev learned tone, learner surface grading and
  tone evidence region suites. Production default rejection, neutral handling and
  current refinement remain covered. No corpus/training benchmark was run.
- All **23 comparable current vectors reproduce exactly**: 20 physical expanded/pilot
  vectors plus three persisted Google expanded vectors, maximum delta **0**.
- Google older whole/energy counterfactual vectors reproduce to maximum absolute
  probability differences **1.34e-9 / 1.43e-10**. These are not claimed byte-exact;
  both use the locked model files. A fresh empty-cache Google whole rerun gives an
  exactly identical layer-9 embedding. Every reference/candidate uses unchanged
  frozen inference code, CPU deterministic mode and four threads.
- **21 lock files and three encoder files verified**. Expanded head SHA-256
  `b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b`;
  pilot `c20cc46ed715ce5ed1f3a76f405014069f4a98c0b9e6e467ce28635b4df725d9`;
  encoder `2fefccd26c2794a583b80f6f7210c721873cb7ebae2c1cde3baf9b27855e24d8`;
  revision `fce0375452b1dd6c080ac3248d423d4d037bc831`, layer 9.

The pre-experiment [freeze-before.json](data/generated/f0-independent-v1/freeze-before.json)
hashes **35,683 original files**, including canonical audio, saved Azure timing,
pitch evidence, final spans, abstentions, expanded/pilot artifacts, all three
physical takes and current timing/grading/UI code. Historical files were not
rewritten. [freeze-verification.json](data/generated/f0-independent-v1/freeze-verification.json)
records the final full-tree verification and unchanged Git HEAD. `git diff --check`
and whitespace checks on the new files passed.
All **35,683 files verified unchanged**, including **29,021 research files** and
**10,559 original audio-format files** (including corpus/generated historical audio,
not 10,559 new recordings). The comparison reports zero missing/changed originals.
The replay performed 52 eligible candidate encoder extractions plus one fresh
determinism repeat, with zero embedding cache hits.

New source/report files:

- [Numeric candidate selector](perceptual_tone/f0_independent.py).
- [Write-once replay and plan sealing](perceptual_tone/f0_independent_replay.py).
- [Focused tests](tests/test_f0_independent.py).
- This report.

Local additive artifacts (ignored by the repository's existing generated-data policy):

- [Sealed plan](data/generated/f0-independent-v1/policy-before-inference.json),
  [complete outputs](data/generated/f0-independent-v1/results.json),
  [80-row CSV](data/generated/f0-independent-v1/all-candidates.csv),
  [80-row readable table](data/generated/f0-independent-v1/all-candidates.md).
- Freeze manifests, inference log, `tests.log`, `production-tests.log`, and new
  content-addressed embedding/canonical caches in `data/generated/f0-independent-v1/`.

Executed with the existing benchmark Python environment plus the existing API
site-packages; no dependencies were installed. For tests:

```sh
PYTHONPATH=research/perceptual-tone-model:services/api/src \
  benchmark/pronunciation_v2/.venv/bin/python - <<'PY'
import site
site.addsitedir('services/api/.venv/lib/python3.12/site-packages')
import pytest
raise SystemExit(pytest.main(['-q', 'research/perceptual-tone-model/tests/test_f0_independent.py']))
PY
```

The same environment invoked `f0_independent_replay.seal()` and then `run()` with
`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`. Artifacts are write-once: repeating a full
experiment requires a fresh output directory and freeze manifest; do not overwrite
this evidence. The focused tests recompute the sealed spans and check the saved
inference evidence without retraining or running the corpus.
