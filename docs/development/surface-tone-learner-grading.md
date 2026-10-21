# Surface expectations and learner grading

READY for physical retest. This report supersedes the unresolved-chain grading
and learner-copy sections of the earlier learned-tone integration/UI reports.
Validation uses reported learned families and controlled F0 support; it does not
claim a new physical recording or a rerun of recognition.

## Trace and root cause

`readings.py` / target pinyin supply lexical tones. The legacy
`surface.surface_expectations` marked every member of longer T3 chains
`prosodic_grouping_unresolved`, including the known final T3. `learned.comparison`
then treated a null scalar expected tone as unknown. Mobile
`learnedToneView.workspaceExpectation` also required one scalar expected tone,
and `workspaceChunkFeedback` stopped with an unavailable grade. Its previous
mismatch branch could only be amber. Neutral support existed in
`chunkPitchGrade`, but the aggregate used the generic “Pitch acceptable” label.

The new path is:

1. The existing dev-only branch in `PerceivedSpeechAnalysisService.run` resolves
   `learner_surface_expectations` from lexical tones and exact character offsets.
2. `analyze_learned` receives these expectations only for downstream comparison;
   its acoustic preparation, inference contract, runtime, and output allowlist
   are unchanged.
3. `LearnedUnit` carries the acceptable set, neutral flag and resolution through
   OpenAPI and generated mobile DTOs.
4. `workspaceExpectation` preserves alternatives without selecting an arbitrary
   member. `workspaceChunkFeedback` compares the usable learned family with the
   set and assigns the existing learner agreement/color states.
5. Existing `PronunciationWorkspace` status text and details display the grade.
   Technical details retain full learned JSON and show the final agreement,
   reason, lexical tone and surface rule. Charts, playback, selection, dialogs,
   navigation and styles are preserved.

## Contract and linguistic scope

`SurfaceExpectation` retains its scalar `tone` and `rule`, adding an alternatives
tuple and derived `acceptable_tones` / `resolution`. New optional fields on
`LearnedUnit` are:

| State | acceptable_surface_tones | expected_neutral | expectation_resolution | legacy expected_surface_tone |
|---|---|---|---|---|
| Exact T2 | `[2]` | false | exact | 2 |
| Alternatives | `[2,3]` | false | alternatives | null |
| Neutral | `[]` | true | neutral | 0 |
| Unknown | `[]` | false | unresolved | null |

Old callers remain valid; the client falls back to the legacy scalar only when
the new set is absent. Existing `experimental_match` / `experimental_mismatch`
comparison keys remain compatible. Their legacy `correction: false` is a backend
family-comparison field, **not the final learner severity**; the workspace assigns
that severity with the existing F0 safeguards. No calibrated correctness score
is introduced. Neutral is an expectation, never a fifth HuBERT prediction.

The learner resolver uses lexical tones, contiguous offsets and chain position,
with no phrase-specific cases:

- Isolated T3 and T3 before non-T3: `{3}`.
- Two uninterrupted T3s: `{2}`, `{3}`.
- Three uninterrupted T3s: `{2,3}`, `{2}`, `{3}`.
- More than three: unparsed interiors remain unknown; the final T3 is retained.
- Punctuation, spaces and other character gaps break the chain.
- Other existing grammatical/sandhi rules are retained.

No stronger prosodic parse exists in this path. The triple policy preserves the
223/323 possibilities described in section 1.3 of
[Tu, Wong & Cha (2017)](https://www.isca-archive.org/interspeech_2017/tu17c_interspeech.pdf).
It does not infer one grouping or generalize the triple rule to longer chains.

Boundary checks cover arbitrary-character `甲，乙丙` with lexical 333, which yields
`{3},{2},{3}`, plus API free-speech `我，想买这个`. Prepared targets with punctuation
have an existing parser limitation: `parse_mandarin_target` retains a punctuation
pinyin slot (`，5`) while perceived syllables exclude punctuation. The existing
mapping guard therefore returns genuinely unresolved expectations for that target;
it never joins a T3 chain across the boundary. That parser is unchanged.

## Acceptance and grading

For the user's reported families, with usable evidence:

| Syllable | Lexical | Acceptable surface | Heard | Learner result |
|---|---|---|---|---|
| 我 | T3 | T2 or T3 | T3 | Green, Correct · Tone 3 |
| 想 | T3 | T2 | T4 | Red with decisive corroboration; otherwise amber |
| 买 | T3 | T3 | T3 | Green, Correct · Tone 3 |
| 这 | T4 | T4 | T4 | Green, Correct · Tone 4 |
| 个 | neutral | neutral | outside numbered model | Green, Correct · Neutral, when neutral evidence is safe |

`这个` remains one tile: **green, “Correct · Tone 4 + neutral”** when both
components are accepted. Unavailable neutral evidence does not mark it wrong;
copy becomes “Correct where measured · Tone 4”. A decisive numbered component
error takes precedence over unavailable members, preserving existing aggregation
semantics.

HuBERT is the primary heard-family authority. A usable family in the acceptable
set is green even when deterministic classification or displayed geometry
strongly disagrees. No isolated 214 shape, probability cutoff, or perturbation
consensus is imposed on a learned match.

An incompatible learned family is amber by default. It becomes red only when
`gradeLearnerPitch` satisfies the unchanged `CONSERVATIVE_RED` policy and the F0
family agrees with the incompatible learned family. That policy checks support,
acceptable/runner-up margins, clarity and stable perturbation probes. F0 explains
and corroborates mismatches; it cannot veto a match. For decisive T2-vs-T4:
“Expected Tone 2 · heard Tone 4” and “Your pitch fell here; this syllable should
rise in this context.”

Acoustic abstention stays gray, “Not enough evidence”. Genuine unknown expectation
stays nonjudgmental: “Heard Tone N. Benma can't reliably grade this tone in context
yet.” Neutral acceptance requires the existing contextual/structural policy plus
the unchanged acoustic guard reaching `neutral_outside_four_tone_model`; an
actual validity failure is not interpreted as neutral success.

Primary learned feedback replaces “Most like” with “Heard Tone N”, and uses
explicit correct/expected/heard/neutral text instead of vague pitch acceptance.
Raw probabilities remain in Technical details and remain uncalibrated.

## Validation and isolation

- **323 backend tests passed** across learner surface, dev learned integration,
  sentence tone graph, readings/contours, quantity references, live pronunciation,
  perceived speech, chunks, tone evidence regions, pitch projection contracts,
  and utterance pitch. API tests cover dev on, feature off, production rejection,
  idempotence, target mapping, punctuation, and additive response fields.
- **791 mobile tests passed in all 47 native/web suites**, including Practice,
  exact playback, charts, details, feature-off behavior and production payload
  rejection. The shared grading fixture is
  `services/api/tests/fixtures/learner_grading_physical.json`; its F0 controls are
  expressly synthetic, not attributed to the original physical take.
- Focused checks cover both alternative families; learned T3 against falling F0;
  corroborated red and nondecisive amber mismatches; abstention; genuine unknown;
  neutral success/failure; compound success, unavailable members, and errors.
- Ruff, API mypy (83 source files), mobile TypeScript, Expo lint, generated schema
  export and `git diff --check` passed.
- New behavior is confined to the existing dev learned gate. Defaults, config,
  legacy scalar resolver and deterministic grade functions remain unchanged.
  The shared TypeScript `PitchExpectation` gains only a basis discriminator.
  Dev analysis cache identity adds `learner-surface-sets-v1` so stale unresolved
  saved responses are not reused as new grading results.

Freeze verification compared source/AST with the starting HEAD: Azure alignment,
acoustic extraction, refinement, continuity guard, the entire pre-grading
inference body, runtime lifecycle and legacy surface function are unchanged.
The original Practice screen and workspace styles are unchanged. No new
phrase-specific token checks appear in the learner resolver or adapter.

Hash verification reused the existing lock and manifests:

- All **21 locked artifacts**, including expanded and pilot heads, unchanged.
- All **3 encoder files**, including HuBERT weights, unchanged.
- All **918 research snapshot files**, unchanged.
- All **915 research/audio entries** selected from the existing fast-timing
  freeze manifest, unchanged, covering original takes, timing evidence and saved
  results. These overlap the research snapshot; counts are not additive.

Encoder layer 9, classifier C=0.1, pooling, probability generation and acoustic
abstention are untouched. No model/corpus benchmark, training, tuning,
calibration, commit, push or deployment was performed.

Logs: `/tmp/benma-learner-api-suites.log`, `/tmp/benma-learner-mobile-all.log`,
`/tmp/benma-learner-lint.log`, `/tmp/benma-learner-freeze.json`.

## Physical retest

Restart the existing local dev API so it loads this code; use the same environment
and credentials. From `/home/jacob/benma`:

```bash
BENMA_ENVIRONMENT=development \
BENMA_ENABLE_DEV_LEARNED_TONE=true \
BENMA_ALIGNMENT_PROVIDER=azure \
BENMA_ACOUSTIC_PROVIDER=praat \
benchmark/pronunciation_v2/.venv/bin/python services/api/scripts/dev_learned_server.py
```

In a second terminal, substitute the computer's LAN IP for the phone:

```bash
EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE=true \
EXPO_PUBLIC_BENMA_API_URL=http://YOUR_LAN_IP:8000 \
npm --prefix apps/mobile start -- --clear
```

Open normal **Practice**, prepare **我想买这个** without punctuation, and record a
new natural attempt. Tap 我, 想, 买, and 这个. If heard families remain T3/T4/T3/T4
and neutral evidence is safe, expect the table above. 想 must show the T2-vs-T4
concern; red still requires the existing decisive evidence checks. In More
details inspect 个 for “Correct · Neutral”. In Technical details check sets
`[2,3]`, `[2]`, `[3]`, `[4]`, `[]` with the last neutral flag true, the heard
families, final grade/reason and supported explanation. Charts and playback
should work as before. Do not use an old saved attempt to assess this change.

## Files changed

Backend:
- `services/api/src/benma_api/pronunciation/surface.py`
- `services/api/src/benma_api/pronunciation/learned.py`
- `services/api/src/benma_api/pronunciation/learned_contracts.py`
- `services/api/src/benma_api/pronunciation/perceived.py`
- `services/api/tests/test_learner_surface.py`
- `services/api/tests/test_dev_learned_tone.py`
- `services/api/tests/fixtures/learner_grading_physical.json`

Mobile:
- `apps/mobile/src/speech/learnedToneView.ts`
- `apps/mobile/src/speech/learnerPitchGrade.ts` (type only)
- `apps/mobile/src/speech/PronunciationWorkspace.tsx` (status/copy/details only)
- `apps/mobile/src/api/openapi.json`
- `apps/mobile/src/api/openapi.generated.ts`
- `apps/mobile/src/__tests__/learnedTone.test.ts`
- `apps/mobile/src/__tests__/practiceScreen.test.ts`

Documentation:
- `docs/development/surface-tone-learner-grading.md`
- `docs/development/dev-learned-tone-integration.md` (current-report pointer)
