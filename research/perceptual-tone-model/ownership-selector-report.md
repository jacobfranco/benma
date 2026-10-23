# F0-independent speech ownership selector experiment

**Decision: B. PROMISING BUT NOT READY.** The structural distinction works on the
four primary cases, restores Google 买 and take-3 我, and loses no currently usable
unit. It does **not** resolve the frozen recognizer's sensitivity to broader owned
speech. Four expanded argmax changes and one pilot change among 13 mutually usable
units prevent a readiness claim. No integration is authorized by this result.

This is an additive offline experiment on the current working tree. The previous
80-row experiment was reused, not rerun. No training, fine-tuning, calibration,
HuBERT/head change, F0 extraction change, grading/sandhi/UI change, new recording,
provider request, commit, push or deployment occurred. The learned minimum is still
**60 ms**. No normal Practice or DEV runtime source was changed.

## Acoustic distinction, before inference

Gap spans below are the union of saved 10 ms RMS cells (centers ±5 ms, clipped to
Azure). Saved RMS uses a 40 ms window. These are measurement-scale gap estimates,
not claims of sample-exact silence or manual phonetic boundaries. Aligned 20 ms
waveform features corroborate the differences; all feature traces and neighbor
boundaries are in the accompanying figures and tables.

| Case | Azure span | Internal low-energy run | Median depression relative to weaker island | Adjacent supported islands | Structural interpretation |
|---|---|---|---:|---|---|
| Google 买 | 1.36–1.65 s | None | — | 225.3 ms supported envelope, then terminal low energy | Continuous audible syllable; no internal split |
| take-2 买 | 2.01–2.51 s | 2.207–2.247 s; 40 ms | −24.88 dB | 197 / 140 ms | Two substantial low-frequency speech bodies, unresolved ownership |
| take-2 想 | 1.53–2.00 s | 1.597–1.657 s; 60 ms | −39.44 dB | 67 / 340 ms | Short fricative onset followed by dominant speech body |
| Google 这 | 1.66–1.96 s | 1.8753–1.9453 s; 70 ms | −2.48 dB | 190 / 10 ms | Shallow trailing dip and tiny edge support, not two bodies |

Google 买 has no internal below-gate run: its low-energy tail is not enclosed by
a second substantial supported island. The selected full Azure span preserves the
user-confirmed audible syllable, including low-amplitude material. The listening
assessment is the user's established QA, not a new listening claim from this pass.

Take-2 买's gap is 197 ms from the Azure start and 263 ms from its end. Both adjacent
islands have median ZCR about .085; their median >=3400 Hz power fractions are
.0019 and .0041. Neither island has any support classified as fricative by the
joint spectral test. They remain two independently substantial bodies, and the
selector does not choose one or bridge them into a usable input.

Take-2 想 is **not distinguished by a shorter or shallower gap**—its gap is longer
and deeper. Its first 67 ms island touches the left Azure edge and has median ZCR
.467 and >=3400 Hz power fraction .459, versus .096 and .0018 in the later body.
52.5/67 ms (78.4%) of the first island passes the joint frication test; only 14.5 ms
is nonfricative. The following island is 340 ms, with 300 ms nonfricative support,
over five times as long. This is compatible with onset/transition/body structure,
so the full onset and gap are preserved. It is an acoustic interpretation conditional
on Azure attribution, not proof that every fricative/quiet/body pattern is one syllable.

Google 这's low run is merely a shallow dip relative to its weaker neighboring
support, ending 14.7 ms before the Azure right edge. The renewed support lasts only
10 ms—far below the unchanged minimum for an independent learned region. It supplies
neither the depth nor two substantial islands required for ambiguity. Its full span
is retained; no tone identity is consulted.

## Signals evaluated

The frozen PCM and existing NumPy/SciPy environment supply:

- Original waveform; saved 40 ms RMS on the existing 10 ms lattice and recording gate.
- New 20 ms waveform RMS/log energy on a 5 ms lattice.
- Zero-crossing rate, Hann-window FFT energy fractions at 300–3400 Hz and >=3400 Hz,
  spectral flatness, and positive normalized spectral flux.
- Maximum normalized autocorrelation magnitude over 2–15 ms lags, without choosing
  a lag, estimating F0, or invoking Praat again.
- Azure and immediate neighbor boundaries; above-gate island durations, gap duration,
  relative depth, edge position, and adjacent support.

The minimal selected rule uses saved RMS plus ZCR and high-band fraction. Speech-band
energy, flatness, flux, and autocorrelation are diagnostics only. In particular,
autocorrelation reaches about .66 in the deep near-silent gaps because of residual
low-frequency structure; it is not reliable standalone speech support. No neural
VAD, Whisper, new speech model or pitch-success requirement was introduced.

The saved gate was reproduced **exactly for all four recordings from waveform energy
alone**: `max(.003, min(3 * quantile(RMS40ms, .1), .15 * max(RMS40ms)))`.
The fact that saved RMS resides in a field named `f0` does not make its values pitch
estimates: every timestamp/RMS row is retained, including frames with no pitch.

## Three candidate families and sealed selection

1. **AZURE_SAFE_BASELINE:** full neighbor-valid Azure span with >=60 ms broadband
   support and complete finite metadata. Its name describes the permissive control;
   it has no effective internal split guard and therefore fails take-2 买 safety.
2. **CONTIGUOUS_SPEECH_SUPPORT:** largest continuous above-gate island, but abstain
   if a second island independently reaches 60 ms. It preserves Google 买/这 but
   still incorrectly loses take-2 想. No ambiguous largest-island rescue is allowed.
3. **GAP_AWARE_AZURE:** full Azure span, preserving ordinary onset/offset structure;
   abstain for a deep split between substantial islands, with the constrained
   fricative-onset exception below. This was the only family selected for full-20 replay.

The final experimental rule is deterministic:

- Validate finite ordered Azure bounds, neighboring ownership, utterance duration,
  RMS coverage and spectral coverage. Overlapping owners are ambiguous; no overlap
  is silently reassigned. Every selected span remains inside its original owner.
- Require >=60 ms span and >=60 ms above-existing-gate support.
- For an internal below-gate run, compare its median RMS to the **weaker** adjacent
  supported island's median RMS. A deep run is >=20 ms and at least 20 dB lower.
- If both adjacent islands are >=60 ms, reject the deep run as ownership ambiguous,
  except for a leading island attached within 10 ms of the Azure left edge whose
  majority support has both ZCR >=.25 and high-band power fraction >=.25, whose
  nonfricative support is <60 ms, and whose following body has >=60 ms nonfricative
  support and is at least three times as long. Preserve the complete span in that case.
- Shallow dips, short gaps, and gaps lacking two substantial islands do not by
  themselves break ownership. No other island is silently selected.

20 ms corresponds to one encoder stride; 20 dB is a tenfold RMS depression;
majority frication and 3:1 duration encode an onset/body asymmetry. These are fixed,
exploratory structural constants motivated by acoustic inspection, **not independently
validated operating thresholds**. No parameter grid, tone-based adjustment, or
speaker/character exception was used. The rule is intentionally conservative for
other deep multi-island patterns; it cannot prove general phonetic ownership from
four recordings.

[Policy sealed before inference](data/generated/ownership-selector-v1/policy-before-inference.json)
contains every selected span, candidate definitions, diagnostic/source hashes and
acoustic choice rationale. Reproduction tests verify the exact plan. Models were
loaded only afterward. Previously known predictions were not selection inputs.

| Case | Policy | Owned span, s | Frames | Expanded / pilot | Result |
|---|---|---|---:|---|---|
| take-2 想 | AZURE_SAFE_BASELINE | 1.5300–2.0000 | 24 | T1 / T1 | usable |
| take-2 想 | CONTIGUOUS_SPEECH_SUPPORT | 1.5300–2.0000 | 0 | abstain / abstain | multiple_substantial_energy_islands |
| take-2 想 | GAP_AWARE_AZURE | 1.5300–2.0000 | 24 | T1 / T1 | usable |
| take-2 买 | AZURE_SAFE_BASELINE | 2.0100–2.5100 | 25 | T3 / T3 | usable |
| take-2 买 | CONTIGUOUS_SPEECH_SUPPORT | 2.0100–2.5100 | 0 | abstain / abstain | multiple_substantial_energy_islands |
| take-2 买 | GAP_AWARE_AZURE | 2.0100–2.5100 | 0 | abstain / abstain | deep_split_between_substantial_islands |
| google 买 | AZURE_SAFE_BASELINE | 1.3600–1.6500 | 15 | T3 / T3 | usable |
| google 买 | CONTIGUOUS_SPEECH_SUPPORT | 1.3600–1.5853 | 11 | T3 / T3 | usable |
| google 买 | GAP_AWARE_AZURE | 1.3600–1.6500 | 15 | T3 / T3 | usable |
| google 这 | AZURE_SAFE_BASELINE | 1.6600–1.9600 | 15 | T4 / T4 | usable |
| google 这 | CONTIGUOUS_SPEECH_SUPPORT | 1.6853–1.8753 | 10 | T4 / T4 | usable |
| google 这 | GAP_AWARE_AZURE | 1.6600–1.9600 | 15 | T4 / T4 | usable |

The baseline's unsafe take-2 买 output was recorded (expanded T3 .554053; pilot
T3 .373762), **not used to select the policy**. The final policy abstains before
encoding that region. Google 这's contiguous alternative is T4/T4 as well; that
agreement is not the reason for preferring full speech preservation.

## Five required outcomes

| Case | Ownership | Learned representation | Span / actual HuBERT frames | Expanded | Pilot | Pitch evidence |
|---|---|---|---|---|---|---|
| Google 买 | safe | usable | 1.36–1.65 s; 290 ms; 15 frames | T3 .992292 | T3 .973598 | unavailable |
| take-2 买 | ambiguous | abstain | audit span 2.01–2.51 s; **0 frames executed** | — | — | usable measurements, cannot override ownership |
| take-2 想 | safe | usable | 1.53–2.00 s; 470 ms; 24 frames | T1 .968116 | T1 .905951 | usable |
| Google 这 | safe | usable | 1.66–1.96 s; 300 ms; 15 frames | T4 .992420 | T4 .910085 | usable |
| take-3 我 | safe | usable | .95–1.42 s; 470 ms; 24 frames | T2 .836362 | T3 .676960 | unavailable |

All probabilities are uncalibrated frozen-head outputs. None is labeled correct.
Take-3 我 retains the previously observed expanded/pilot disagreement. Google 买
restores eligibility from a 25.3 ms current pool; it does not recover a pitch contour.
Full probability vectors, including all inconvenient outputs, are in `results.json`.

## Full frozen 20-unit regression

Coverage changes **13 usable / 7 abstained → 15 usable / 5 abstained**. Google 买 and
take-3 我 are restored; nothing is lost. Across the 16 numbered units this is
13/16 → 15/16. All four 个 remain outside the existing four-tone model; they pass
acoustic ownership but abstain at the unchanged downstream neutral scope gate.

Ownership is 19 safe / 1 ambiguous / 0 invalid. Of the 15 learned-usable units,
10 have usable pitch evidence and 5 have unavailable pitch evidence. All 20 audit
pooling contracts change relative to CURRENT_REFERENCE, including the five final
abstentions; all 13 mutually usable units have changed pool bounds. This is not
20 new model calls or 20 prediction flips.

| Recording | Unit | Current → new frames | Current → new expanded | Current → new pilot | Pitch | Ownership | New learned input |
|---|---|---:|---|---|---|---|---|
| take-1 | 我 (0) | 7 → 14 | T2 → T2 | T3 → T3 | usable | safe | usable |
| take-1 | 想 (1) | 10 → 15 | T3 → T3 | T1 → T1 | usable | safe | usable |
| take-1 | 买 (2) | 11 → 19 | T2 → T2 | T2 → T2 | usable | safe | usable |
| take-1 | 这 (3) | 3 → 11 | T3 → T2 | T2 → T3 | unavailable | safe | usable |
| take-1 | 个 (4) | 0 → 0 | abstain → abstain | abstain → abstain | unavailable | safe | abstain |
| take-2 | 我 (0) | 15 → 23 | T3 → T3 | T3 → T3 | usable | safe | usable |
| take-2 | 想 (1) | 13 → 24 | T1 → T1 | T1 → T1 | usable | safe | usable |
| take-2 | 买 (2) | 0 → 0 | abstain → abstain | abstain → abstain | usable | ambiguous | abstain |
| take-2 | 这 (3) | 5 → 11 | T3 → T4 | T3 → T3 | unavailable | safe | usable |
| take-2 | 个 (4) | 0 → 0 | abstain → abstain | abstain → abstain | unavailable | safe | abstain |
| take-3 | 我 (0) | 0 → 24 | abstain → T2 | abstain → T3 | unavailable | safe | usable |
| take-3 | 想 (1) | 11 → 17 | T3 → T2 | T1 → T1 | usable | safe | usable |
| take-3 | 买 (2) | 16 → 23 | T3 → T2 | T3 → T3 | usable | safe | usable |
| take-3 | 这 (3) | 8 → 18 | T4 → T4 | T4 → T4 | usable | safe | usable |
| take-3 | 个 (4) | 0 → 0 | abstain → abstain | abstain → abstain | unavailable | safe | abstain |
| google | 我 (0) | 10 → 16 | T2 → T2 | T2 → T2 | usable | safe | usable |
| google | 想 (1) | 8 → 14 | T2 → T2 | T2 → T2 | unavailable | safe | usable |
| google | 买 (2) | 0 → 15 | abstain → T3 | abstain → T3 | unavailable | safe | usable |
| google | 这 (3) | 7 → 15 | T4 → T4 | T4 → T4 | usable | safe | usable |
| google | 个 (4) | 0 → 0 | abstain → abstain | abstain → abstain | usable | safe | abstain |

## Frozen model stability

TV is half the L1 distance between uncalibrated T1/T2/T3/T4 probability vectors.
Only the 13 mutually usable units enter stability comparisons; restored/abstained
cases are separately reported. No expected-tone accuracy statistic is computed.

| Head | Same argmax | Changed argmax | Mean TV | Maximum TV |
|---|---:|---:|---:|---:|
| Expanded | 9/13 | 4/13 | .194237 | .651128 |
| Pilot | 12/13 | 1/13 | .137612 | .349412 |

Expanded flips: take-1 这 T3→T2; take-2 这 T3→T4; take-3 想 T3→T2; take-3 买 T3→T2.
Pilot flips only take-1 这 (T2→T3). Expanded/pilot disagreements are 4/13 currently
and 7/15 newly; on the same 13 mutually usable units the count grows from 4 to 6.
The restored take-3 我 contributes the seventh new disagreement.

Take-2 这 is the largest expanded shift: current 2.667–2.757 s, five frames, versus
2.54–2.76 s, eleven frames, TV .651128. These both pass their applicable ownership
checks, so safe ownership alone does not establish interchangeable learned input.
Take-3 想/买 also change families despite no internal below-gate gap. The primary
controls are steadier: take-2 想 TV .020728 expanded/.067711 pilot; Google 这
.005989/.082109. These facts block integration; no output-driven span repair is made.

| Recording / unit | Current span, s | New span, s | Expanded TV | Pilot TV |
|---|---|---|---:|---:|
| take-1 我 | 0.9567–1.1067 | 0.8800–1.1500 | 0.112855 | 0.206413 |
| take-1 想 | 1.2467–1.4467 | 1.1600–1.4500 | 0.148268 | 0.068970 |
| take-1 买 | 1.4600–1.6867 | 1.4600–1.8400 | 0.123683 | 0.237029 |
| take-1 这 | 2.1467–2.2167 | 2.0100–2.2200 | 0.334372 | 0.349412 |
| take-2 我 | 1.1470–1.4470 | 1.0600–1.5200 | 0.341518 | 0.204810 |
| take-2 想 | 1.7270–1.9970 | 1.5300–2.0000 | 0.020728 | 0.067711 |
| take-2 这 | 2.6670–2.7570 | 2.5400–2.7600 | 0.651128 | 0.102219 |
| take-3 想 | 1.5353–1.7553 | 1.4300–1.7600 | 0.191896 | 0.114460 |
| take-3 买 | 1.7700–2.0853 | 1.7700–2.2300 | 0.334244 | 0.045452 |
| take-3 这 | 2.3953–2.5653 | 2.2600–2.6200 | 0.001475 | 0.200301 |
| google 我 | 0.8353–1.0453 | 0.7600–1.0700 | 0.249022 | 0.052629 |
| google 想 | 1.1253–1.2753 | 1.0800–1.3500 | 0.009908 | 0.057445 |
| google 这 | 1.6953–1.8353 | 1.6600–1.9600 | 0.005989 | 0.082109 |

## Neighbor ownership and encoder geometry

Selected bounds never expand. Neighbor overlaps fail closed and all 20 selections
remain within their original Azure bounds. Encoder context remains the original
Azure ±250 ms used by the frozen architecture; neighboring contextual audio is
not claimed to be owned pooled speech.

A geometry-only one-stride (20 ms) onset allowance was examined, clamped to the
midpoint of unassigned time after the previous owner. It is **not a fourth selector**
and triggers no inference. For Google 买 the preceding 想 ends at 1.35 s, so the
limit is 1.355 s: at most 5 ms, adding zero frame centers. Google 这 and take-2 想
have the same 5 ms restriction and zero added centers. A 20 ms onset allowance
therefore cannot materially recover Google's initial /m/ under these ownership
constraints. Larger free gaps elsewhere can add one center, but there is no acoustic
reason here to claim that material. No blind padding was added. Geometry for every
row is in `onset_geometry_only` in `results.json`.

## Separation, no leakage and reproducibility

Ownership (safe/ambiguous/invalid), acoustic representation (usable/abstain),
learned representation after neutral scope, learned tone, and pitch evidence are
separate fields. Grading is downstream and untouched. Pitch evidence is copied
unchanged from the frozen reference, including unavailable states. The selector
accepts only numeric timing, duration, RMS/gate, ZCR/high-band evidence and candidate
name. It has no access to character, expected/lexical tone, model prediction,
speaker identity, desired grade or pitch success.

Counterfactual tests delete/change pitch and target/model metadata while preserving
RMS/timing: all 28 planned choices remain identical. Additional tests cover exact
waveform-only gate reproduction, amplitude scaling, determinism, missing evidence,
neighbor clamping, and a synthetic nonfricative replacement for take-2 想's onset
that correctly makes the deep split ambiguous. The 59 ms boundary abstains and the
60 ms boundary passes. Inputs and frozen outputs are not mutated.

The experiment evaluates 12 primary candidate rows plus 16 remaining rows for the
chosen policy: **28 rows total, with 20 rows for the final policy**. There are only
**4 fresh encoder extractions** (take-2 想 whole, take-2 买 baseline-only, Google 这
whole, Google 这 contiguous). Fifteen rows reuse exact prior audio/context/pool
contracts and both saved heads, two reuse new exact contracts, and seven abstain.
The previous 80-row replay and CURRENT_REFERENCE inference are never rerun.
Frozen head files and the three encoder-weight hashes match the existing lock.

## Decision and one next engineering pass

**PROMISING BUT NOT READY.** The primary ownership distinction and coverage bar
pass. Model stability does not. The exact unresolved ambiguity is **whether the
frozen mean-pooled HuBERT representation is excessively sensitive to which equally
owned parts of a syllable are included**. Safe speech support is not enough to
answer that question, and predicted-tone agreement cannot resolve it.

Do one bounded **offline frame-level pooling attribution audit** on the four
expanded-flip cases: take-1 这, take-2 这, take-3 想 and take-3 买. Hold waveform,
Azure context, encoder and heads fixed; cache the frame embeddings once and compare
only regions specified from existing acoustic onset/body/offset evidence before
reading outputs. Attribute the vector changes to added owned frames. Reuse the
current outputs and inspect sensitivity, without a threshold sweep, new recordings,
training, calibration or expected-tone ranking. Do not integrate or tune the model
in that pass. DEV-only replacement of F0-dependent selection is deferred.

## Tests, scoped freeze and artifacts

The final relevant run is **71 passed, 1 deselected**: new ownership tests, prior
F0-independent tests, fast timing/ownership behavior tests and API DEV learned-tone
tests. The deselected test was first executed and failed because its old historical
freeze expects `apps/mobile/src/__tests__/practiceScreen.test.ts` SHA
`e8a8d8a2ab0a4dd079f22a40595ab1427e6a5ff8e258e0d31e365824c344192f`.
This pass's starting and final SHA are both
`901f6aaa35d206d4304d336362170c90056519794259466721130b065e6a09aa`.
That pre-existing historical mismatch is documented, not patched or hidden.
The initial run was 70 passed / 1 failed; a waveform-only gate test was subsequently
added. No training/corpus benchmarks were run. Ruff and whitespace checks pass for
all new source files. Figures were inspected after rendering.

A scoped freeze verifies **559 existing files unchanged**, including all prior
experiment outputs/caches, consumed audio/JSON, prior freeze metadata, research
Python files, lock-listed artifacts, and tracked API/mobile files. It does not claim
a fresh 35k-file corpus verification. The previous full-tree freeze remains intact.
Starting HEAD/status, individual SHA-256 values, lock/encoder hashes, and verification
are persisted. New outputs are additive and generated data follows the existing
ignored-data policy.

Aligned Matplotlib PNG/PDF figures cover all five required cases:
[Google 买](data/generated/ownership-selector-v1/figures/google-2.png),
[take-2 买](data/generated/ownership-selector-v1/figures/take-2-2.png),
[take-2 想](data/generated/ownership-selector-v1/figures/take-2-1.png),
[Google 这](data/generated/ownership-selector-v1/figures/google-3.png),
[take-3 我](data/generated/ownership-selector-v1/figures/take-3-0.png).
Numeric CSV traces, original standalone SVG plots and gap/island tables are in
`diagnostics/`. Matplotlib was installed only under `/tmp/ownership-plotting` for
rendering; project dependencies and the inference environment were unchanged.

Key artifacts under `data/generated/ownership-selector-v1/`:

- `policy-before-inference.json`, `results.json`, `decision.json`, `all-candidates.csv`.
- `primary-candidates.md`, `full-20.md`, `stability.md`, `stability.csv`.
- `diagnostics/`, `figures/`, and new content-addressed `cache/`.
- `freeze-before.json`, `freeze-verification.json`, `freeze-final-verification.json`.
- `inference.log`, `tests.log`, `tests-current-freeze.log`, `tests-final.log`,
  `historical-test-mismatch.json`, and `artifact-manifest.json`.

New source/report files (no pre-existing source edited):

- `perceptual_tone/ownership_selector.py` — numeric selector and island accounting.
- `perceptual_tone/ownership_diagnostics.py` — scoped freeze and acoustic diagnostics.
- `perceptual_tone/ownership_replay.py` — seal, exact-contract reuse, frozen evaluation.
- `scripts/ownership_selector_figures.py` — standalone Matplotlib rendering.
- `tests/test_ownership_selector.py` — focused selector/evidence regression tests.
- `ownership-selector-report.md` — this report.

Existing untracked F0-independent files were preserved exactly as found.
