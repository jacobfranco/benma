# Google 买 autopsy and contextual tone helper

This pass continues the existing working tree. It adds resolver metadata and a
small learner helper, plus read-only diagnostics of the exact saved Google result.
No acoustic behavior, classifier, grading severity, or production defaults changed.

## Part A — Google 买

**Decision: C. INCONCLUSIVE about audible completeness / whether abstention is
perceptually warranted.** The first loss of selected pitch and the exact abstention
path are confirmed. The retained representation is demonstrably much shorter than
the energetic audio, and frozen-model counterfactuals strongly support investigating
representation loss. A complete, normal-sounding 买 has **not** been independently
confirmed by listening in this session; the tools available here cannot audition
local audio. The exposed crops allow that remaining check without another recording.
Do not interpret this result as learner pronunciation failure.

### 1. Exact attempt and provenance

The unique recent result matching the user's Google signature is:

| Item | Identifier |
|---|---|
| Attempt | `dadff527-d15b-4ceb-a652-8bdb56c7d72d` |
| Analysis | `fc06e59f-d725-4c18-9f44-3a93de823614` |
| Created | 2026-10-21 19:35:03.352172 UTC / 15:35:03 EDT |
| Utterance | `bb150643-4399-4754-88b4-a2da197a7086` |
| Canonical audio asset | `02267e33-3ee7-4c99-b16e-6bb12193b546` |
| Acoustic run | `5a070df1-0a71-426f-b373-9d2a0021560e` |
| Perception run | `8cb0b137-19c2-4829-8ecf-197f2c21eb8e` |
| Azure timing evidence | `f67ea565-895f-4435-b8fd-a201691f5392` |

Canonical WAV SHA-256:
`0c0b8a82b5cb57221b16ab16999b489e882d93a2d2ab9b353572c4e29b1316ae`.
The file is mono PCM16, 16 kHz, duration 2.600625 s. The persisted result is
我=T2, 想=T2, 买=`too_little_material`, 这=T4, 个=`neutral_outside_four_tone_model`.
The target is 我想买这个; the saved ASR/alignment reference includes final punctuation.

The immediately preceding human attempt is `a20433e8-c69a-40c2-9787-e44a3ef2becd`,
analysis `929e3fb4-0475-408f-a7ab-dfce63b0fc08`, at 19:33:16.999290 UTC. Its audio
SHA-256 is `2eba5e7c809e40b636f3bf84245cbe5792428fb733c8786168d3313af448215f`;
its output is T2/T3/T2/continuity-abstain/no-voiced-support. These are distinct
recordings. Attribution to Google follows the user's exact signature and sequence;
the database does not independently authenticate which external player was used.

The database was queried in read-only transactions. Identifiers and audio hashes
were recorded before detailed inspection; exported snapshot hashes were recorded
before tracing stages. Original evidence was never rewritten. Azure evidence is
embedded in this perceived-analysis row, not a separate `AlignmentRun` row.

| Frozen exported snapshot | SHA-256 |
|---|---|
| Analysis, including learned output/debug metadata | `c7c253405a5347445bfeae22f5942e6a88e18f88c07ca648cd2551b44684e70e` |
| Acoustic run, including candidates and energy | `6631f0c7f4b388562a597ba1425188770e875b2ce10f8007ff137eaa4d361f91` |
| Perception | `5d5c9876caf95f038948b5e31814964e72b1d117fa49e57d8469f587e952ce0a` |
| Extracted Azure timing object | `48ee9cd869e0f188572133b038c38bd5a718b461c6688fcaf4036d2cb6d7a5a4` |

Snapshot hashes refer to the exported JSON bytes, not a claimed provider hash.
Local evidence: [artifact directory](../../services/api/var/google-mai-autopsy/).

### 2–3. Raw span and crop QA

Azure reports 买 offset 13,600,000 and duration 2,900,000 in 100 ns ticks:
**[1.36, 1.65) s, 290 ms**, character offsets [2,3). No equal subdivision or
word-boundary inference supplies this span; it is the provider's grapheme timing.

[Diagnostic playback](../../services/api/var/google-mai-autopsy/playback.html)
contains unchanged PCM crops, with no gain, fades, padding or resynthesis:

| Playback | Canonical span |
|---|---|
| [Full utterance](../../services/api/var/google-mai-autopsy/full.wav) | 0–2.600625 s |
| [Raw Azure 买](../../services/api/var/google-mai-autopsy/azure-mai.wav) | 1.36–1.65 s |
| [Owned F0-cell envelope before clamp](../../services/api/var/google-mai-autopsy/pre-clamp-f0-envelope.wav) | 1.3553–1.3853 s |
| [Final retained 买](../../services/api/var/google-mai-autopsy/retained-mai.wav) | 1.36–1.3853 s |
| [Local 想–买–这 context](../../services/api/var/google-mai-autopsy/xiang-mai-zhe.wav) | 1.08–1.96 s |

Crop samples use nearest 16 kHz sample boundaries. The pre-clamp crop is the
10 ms envelope of **already Azure-owned** retained centers; it is not a newly
proposed syllable boundary. It contains 4.7 ms outside the left Azure edge and
is exposed solely to make the clamp visible.

**Does raw Azure 买 audibly contain a normal complete 买?** Listening confirmation
is pending; no claim of direct audition is made. The waveform contains substantial
material well beyond the retained fragment. **Does the final fragment adequately
represent the same syllable?** It preserves only 25.3 ms (8.72%) of the Azure
span and omits the later energy peak/decay. It cannot stand in for that full audio
region; exact auditory/phonetic adequacy remains unverified.

### 4–8. Stage trace and exact abstention

![Frozen waveform, candidates and energy](../../services/api/var/google-mai-autopsy/trace.png)

[All local frame values](../../services/api/var/google-mai-autopsy/local-frames.csv),
[all raw candidates](../../services/api/var/google-mai-autopsy/local-raw-f0-candidates.json),
and [stage summary](../../services/api/var/google-mai-autopsy/stage-summary.json)
retain the complete local evidence without downsampling.

| Stage | 想 | 买 | 这 |
|---|---|---|---|
| Azure span, s | 1.08–1.35 | 1.36–1.65 | 1.66–1.96 |
| Raw 10 ms frames | 27 | 29 | 30 |
| Praat selected voiced frames | 22 | **3** | 14 |
| After recording-energy gate | 22 | **3** | 14 |
| After acoustic quality selection | 15 | **3** | 14 |
| After chart filtering / owned support | 15 | **3** | 14 |
| Final learned pool, s | 1.1253–1.2753 | **1.36–1.3853** | 1.6953–1.8353 |
| Continuity guard | pass | **pass** | pass |
| HuBERT pooled frames | 8 | **not run** | 7 |

For 买, retained centers are 1.3603, 1.3703 and 1.3803 s, at 284.436, 279.090
and 273.818 Hz. Their RMS values are 0.031038, 0.040825 and 0.046851. At
**1.3903 s**, Praat's selected track becomes unvoiced/null and stays null through
1.6403 s. Thus 26 of 29 local frames are already missing **before** Benma's
recording-energy and acoustic-quality gates.

Raw candidates still exist. For example, at 1.3903 s there are candidates at
264.738 Hz (strength .4725), 350.704 Hz (.4306) and 540.113 Hz (.5047), but Praat
selects no voiced F0. Candidates are not recovered truth and were not substituted.
Later maximum candidate strengths vary roughly .234–.492. Selected-pitch dropout
is established; its underlying perceptual cause (aperiodicity, playback/recording
conditions, competing candidates, etc.) is not established by these values alone.

The recording gate is **0.010798918764352643 RMS**, with noise floor
0.005159464239781736. 买 RMS ranges 0.007163–0.063966. There are **23 above-gate
frames**, including **20 with no selected F0**. The last six frames, 1.5903–1.6403 s,
are below gate, but already lack tracker F0; **zero voiced candidates selected by
Praat are removed by the energy gate** in 买. No quality rejection removes the
three surviving 买 frames. 想 separately loses seven selected frames to
`low_frequency_contamination` at 1.2803–1.3403; that is not the cause of 买's dropout.

The pre-clamp owned-center envelope is [1.3553,1.3853]. Azure clipping removes
only **4.7 ms at the left**, producing [1.36,1.3853], **25.3 ms**. Both are already
below the frozen 60 ms minimum. The clamp itself is not the first loss and removing
that clipping alone would not change abstention.

Continuity checks the two 10 ms gaps between the three retained centers. Neither
exceeds 15 ms; `checked=true`, `passed=true`, `interruptions=[]`. The trailing
unvoiced region has no later retained endpoint within 买, so it is not an internal
interruption. No continuity rejection occurs. Adjacent Azure spans have 10 ms gaps;
there is no demonstrated overlapping ownership. Auditory boundary correctness is
still subject to crop QA.

Exact reason: **`too_little_material`**, assigned by `refine_span` before inference.
The production adapter submits no 买 contract to HuBERT: **zero frames actually
pooled for 买**, with persisted `owned_encoder_frames=null` (not a measured zero).
Three retained F0 frames must not be confused with encoder frames.

An offline rerun of the unchanged Praat analyzer exactly reproduced every persisted
raw F0/candidate/energy frame; replaying the unchanged refinement exactly reproduced
the entire saved 买 realization. These are diagnostic checks, not tests that force
this recording to pass.

### 9. Frozen-model counterfactuals

Two prespecified, offline audio-only diagnostics reused the same canonical WAV,
Azure ownership [1.36,1.65], context [1.11,1.90], frozen encoder/layer/head and
existing runtime. No phonological expectation entered inference. The second span
uses the same gate's above-threshold frame envelope, without requiring selected F0.
It is an experiment, not a proposed production support rule.

| Diagnostic pool | Encoder frames | P(T1) | P(T2) | P(T3) | P(T4) | Prediction |
|---|---:|---:|---:|---:|---:|---|
| Azure whole: 1.36–1.65 | 15 | .0001291142 | .0062805234 | .9922919749 | .0012983875 | T3 |
| Above-gate envelope: 1.36–1.5853 | 11 | .0000018423 | .0003141745 | .9996550449 | .0000289383 | T3 |

[Exact contracts and outputs](../../services/api/var/google-mai-autopsy/counterfactual.json).
The model sees its usual neighboring context; these are not independent listening
judgments or calibrated correctness probabilities. Google TTS is not treated as
ground truth. No alternative rule was selected from these outputs. There is no
separate continuity-rejected envelope to test in this attempt.

### 10–12. Root cause, decision and next engineering hypothesis

Confirmed category: **PITCH_TRACKER_DROPOUT** at the selected-F0 stage. The
F0-derived envelope propagates that loss into learned pooling, so
**F0_ENVELOPE_OVERTRIM is a downstream representation hypothesis**, not a demonstrated
clamp implementation bug. ENERGY_GATE_INTERACTION and CONTINUITY_GUARD_REJECTION
are not the triggering causes. AZURE_BOUNDARY_FAILURE, TOO_SHORT_ACTUAL_PRODUCTION
and CROSS_SYLLABLE_OWNERSHIP are not established.

**C. INCONCLUSIVE** remains the formal A/B/C decision until the raw crop is heard.
The current abstention correctly follows the frozen policy for a 25.3 ms retained
span. Whether that policy has discarded a clearly intact, normally pronounced 买
is strongly suggested by signal duration and frozen-model outputs, but is not
proven by a model agreeing with the target. If crop QA confirms a complete 买,
classify the product issue as **B. REPRESENTATION DEFECT CONFIRMED**.

The smallest generic follow-up hypothesis is to test whether **learned pooling
support should remain available during selected-F0 dropout when independent local
speech evidence exists inside the same validated Azure span**, while keeping F0
filtering for the pitch chart. Test against frozen positive cases and silence,
noise, interrupted speech and neighboring-syllable controls. Do not lower the
60 ms minimum, weaken the 15 ms guard, or choose a new energy threshold from this
one example. No Part A production fix was implemented.

## Part B — Contextual tone UX

### 13–15. Contract, trigger and content

The linguistic learner resolver now emits optional **`contextual_rule`**, initially
`third_tone_sandhi`, alongside existing `lexical_tone`,
`acceptable_surface_tones`, `expectation_resolution`, `expected_neutral` and
`surface_rule`. It is a string identifier rather than a closed UI enum.
Only supported T3 pair/triple positions that introduce a contextual alternative
receive the identifier. The final unchanged T3, unknown longer-chain interiors,
neutral expectations and other rules receive no new identifier.

`LearnedUnit`, OpenAPI and generated mobile DTOs carry it without putting it into
the acoustic inference contract. The dev expectation-cache version becomes
`learner-surface-context-v2` so freshly requested analyses cannot reuse an old
metadata-free response. Existing persisted rows are not rewritten.

The helper requires a matching learned-unit identity, a resolved expectation,
resolver metadata, and at least one acceptable tone different from the lexical
tone. It never inspects specific Hanzi or rewrites pinyin. An unobtrusive ⓘ appears
beside the selected chunk's primary feedback, not on every tile. It opens the
existing `WorkspaceDialog` with dictionary tone, spoken-here expectation, rule
explanation and heard tone. No Technical details visit is needed.

Single changed T3 copy:

> Third-tone sandhi
>
> Dictionary tone: Tone 3
>
> Spoken here: Tone 2
>
> Before another third tone, this dictionary Tone 3 changes to a rising Tone-2-like realization.
>
> Heard: Tone 2
>
> The pinyin keeps the dictionary tone mark.

For alternatives, spoken-here is **“Tone 2 or Tone 3”** and the explanation is
**“Tone 2 or Tone 3 can be acceptable here, depending on phrasing.”** No universal
mechanical triple pattern is claimed. Technical details retain the complete sets
and exact resolver rule identifiers.

### 16–21. Learner display and preserved pinyin

| Case | Primary feedback | Help |
|---|---|---|
| 我, learned T2 / accepted {2,3} | Correct · Tone 2 here | Dictionary T3; spoken T2 or T3 depending on phrasing |
| 我, learned T3 / accepted {2,3} | Correct · Tone 3 here | Same alternatives |
| 想, learned T2 / expected {2} | Correct · Tone 2 here | Dictionary T3; spoken T2; third-tone sandhi |
| 想, learned T3 / expected {2} | Expected Tone 2 here · heard Tone 3 | Same rule explanation |
| 买, this saved abstention | Not enough evidence | No contextual change/helper |
| 买, usable learned T3 | Correct · Tone 3 | No helper |
| Ordinary unchanged numbered tone | Correct · Tone N | No helper |
| 这个, accepted T4 + neutral | Correct · Tone 4 + neutral | No new neutral helper |

The neutral explanation remains in the existing details. No neutral linguistic
coverage or fifth classifier family was added. Canonical target and syllable
pinyin stay **wǒ xiǎng mǎi zhè ge**; `xiáng` belongs only to the already separate
heard-tone rendering when T2 is actually heard.

All grade decisions remain the same: a usable learned match is green; only an
incompatible family plus existing decisive corroboration is red; nondecisive
mismatches are amber; abstention is gray. No F0 shape veto on matches was added.

### 22. Extensibility

`ContextualToneExplanation` and `ContextualToneHelp` accept a string rule ID and
resolved dictionary/spoken/heard information. The known T3 explanation is selected
by ID. An unknown future ID renders a generic contextual-pronunciation explanation
and the supplied tones, without pretending to know a new phonology rule. A future
rule can add an explanation without changing component types. Tests use a future
ID as a contract value only; no 不/一/neutral resolver coverage was introduced.

### 23. Validation

- **109 API tests passed**: learner surface, dev learned integration, perceived
  speech and sentence tone graph suites. Includes metadata from arbitrary-character
  resolver inputs through API DTOs, pair/triple/final distinctions, lexical pinyin,
  cache/idempotence, feature-off and future-ID contract coverage.
- **296 mobile/web tests passed across 11 suites**: helper interaction, exact
  vs alternative expectations, mismatch copy, canonical pinyin, absence for
  unchanged/unknown/metadata-free/feature-off cases, arbitrary Hanzi, future IDs,
  retained technical sets, neutral aggregate and existing Practice/playback behavior.
- TypeScript, Expo lint, Ruff, API mypy (83 source files), OpenAPI generation and
  `git diff --check` passed.
- Real Chromium smoke passed at desktop and 390 px widths, with no page errors or
  horizontal overflow. The browser replay used saved Google evidence plus current
  resolver metadata and the API's normal pure chunk enrichment. It checked helper
  visibility from normal UI, Escape dismissal, existing details and exact playback.
  No new recording, live provider call or learned inference was performed by this UI
  smoke. Screenshots: [phone helper](../../services/api/var/google-mai-autopsy/benma-context-helper-narrow.png),
  [desktop helper](../../services/api/var/google-mai-autopsy/benma-context-helper-desktop.png).
- Diagnostic-only exact Praat/frame and refinement replay passed. No acoustic
  behavior-changing regression test was added because no implementation bug was fixed.

Logs are `/tmp/benma-context-api-suites.log`,
`/tmp/benma-context-mobile-suites.log`, and
`services/api/var/google-mai-autopsy/benma-context-browser.log`.

### 24. Freeze verification

The turn-start manifest covered 30,635 existing files. All **29,021 research files**
and **405 original audio files** in it remain byte-identical. The latter include
both new physical recordings and previous recordings. All **21 locked artifacts**,
including expanded and pilot classifiers, and **three encoder files** match the
existing lock hashes. Frozen research releases were not modified.

AST/file verification also confirms unchanged `refine_span`, the entire inference
pre-grading body, runtime, Azure alignment, acoustic extraction/F0 policy, recording
energy gate, 15 ms continuity rule, timing configuration, legacy linguistic resolver,
deterministic grading functions, Practice screen and existing workspace styles.
Only explanation metadata/copy changed downstream of inference. The frozen head
is still SHA-256 `b3369239c5b6da261f0d38ea5ea0ab129f316552bda78b11cb0f755abfea011b`,
encoder weights `2fefccd26c2794a583b80f6f7210c721873cb7ebae2c1cde3baf9b27855e24d8`,
layer 9, revision `fce0375452b1dd6c080ac3248d423d4d037bc831`.

Verification records are [file freeze](../../services/api/var/google-mai-autopsy/benma-context-freeze-tree.json)
and [locked artifacts / AST](../../services/api/var/google-mai-autopsy/benma-context-freeze-locks.json).
No training, tuning, calibration, acoustic threshold changes, commits, pushes or
deployments occurred.

### 25. Files changed in this pass

Existing files updated:

- `services/api/src/benma_api/pronunciation/surface.py`
- `services/api/src/benma_api/pronunciation/learned_contracts.py`
- `services/api/src/benma_api/pronunciation/learned.py`
- `services/api/tests/test_learner_surface.py` (already untracked at turn start)
- `services/api/tests/test_dev_learned_tone.py`
- `apps/mobile/src/api/openapi.json`
- `apps/mobile/src/api/openapi.generated.ts`
- `apps/mobile/src/speech/learnedToneView.ts`
- `apps/mobile/src/speech/PronunciationWorkspace.tsx`
- `apps/mobile/src/__tests__/learnedTone.test.ts`

New files:

- `apps/mobile/src/speech/ContextualToneHelp.tsx`
- `docs/development/google-mai-contextual-tone-ux.md`
- Local diagnostic artifacts under `services/api/var/google-mai-autopsy/`
  (ignored evidence copies, playback crops/page, candidates/CSV, plots,
  counterfactual outputs, reproduction scripts, checks and screenshots).

Other pre-existing working-tree edits were preserved. The original physical
fixture was not changed to make Google pass.

## Recommended next physical/product test

First listen to the **existing** Azure 买 and retained crops alongside the local
context; no replacement recording is needed for the autopsy. If the full crop is
complete, record that judgment and promote the Part A conclusion to representation
defect before testing a generic alternative support policy offline.

Then restart the local dev API and reload the dev mobile bundle with their existing
learned-tone flags. Record one new 我想买这个 attempt in normal Practice. Verify
canonical wǒ/xiǎng/mǎi remains visible, select 我 and 想, and open ⓘ directly to
explain the accepted alternatives and the expected T2. Check 买 remains honestly
gray if the same extraction failure recurs and 这个 retains its T4 + neutral status
when evidence is sufficient. This product retest validates learner understanding;
it does not assume a new acoustic pass for 买.
