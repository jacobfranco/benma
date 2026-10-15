# Deterministic pronunciation checkpoint — 2026-10-15

This describes the current working tree, including the uncommitted conservative
grading work. No thresholds, measurements, UI policy, or production files are
changed by this checkpoint. The hash manifest identifies the baseline more
precisely than HEAD alone. Existing historical reports describe earlier stages;
the current comparison is the 2026-10-13 conservative-grading `results.json`.

| Stage | Current implementation | Responsibility |
| --- | --- | --- |
| Audio | Canonical mono PCM WAV; audio hash and utterance identity | Acoustic evidence; original recording retained; exact spans use the canonical recording |
| ASR / alignment | `services/api/src/benma_api/pronunciation/perceived.py`, `alignment.py`, `azure_alignment.py`, `timing.py` | Linguistic transcription and timing ownership. Uses perceived transcript; exact ASR timings or configured aligner. Ambiguous/grouped timing stays grouped. Alignment and acoustic extraction can run concurrently. |
| Raw pitch / F0 | `acoustics.py`, `PraatAcousticAnalyzer` | Acoustic, target-independent tracker measurements, energy and voicing; no expected-tone repair |
| Candidate evidence | `acoustics.py`, `pitch_types.py`, `pitch_evidence.py` | Acoustic candidate frequencies/strengths, raw and selected values, exclusion reasons and content-addressed utterance track |
| Filtering / artifact rejection | `pitch_rejection.py`, `contours.py`, `build_pitch_track` | Acoustic energy/background/branch checks and retained-contour filtering. Rejects unsafe observations; does not manufacture a desired contour. |
| Syllable ownership | `project_pitch`, `tone_graph.py`; mobile `pronunciationWorkspace.ts`, `pronunciationChunks.ts` | Timing-bound projection of acoustic frames. Linguistic timing supplies boundaries, never a tone-dependent frame selection. |
| Structural reliability | `interpretation_eligibility`; mobile `pitchShapeEvidence.ts`, `pitchShape.ts` | Acoustic completeness, gaps, discontinuities, branch/deletion sensitivity and perturbation checks. Reliable ambiguity is different from unavailable evidence. |
| Acoustic tone-family scoring | mobile `toneLikeness.ts` | Target-independent T1/T2/T3/T4 heuristic support from retained geometry, relative movements and local noise. Produces numbered/unclear/unavailable decision, family probes and separate gesture strength. |
| Contextual acceptable families | backend `readings.py`, `surface.py`; mobile `pitchExpectation` in `learnerPitchGrade.ts` | Linguistic lexical/surface rules and conservative contextual alternatives. Resolved surface decisions take precedence; unresolved T3 chains may license T3/T2; lexical fallback is not an exact surface prediction. |
| Learner grading | `gradeLearnerPitch`, `learnerPitchEvidence`, `chunkPitchGrade.ts` | Learner-facing burden of proof using acoustic reliability, contextual compatibility, margins and probes. Neutral dependent non-veto and chunk aggregation are separate policies. |
| Coaching / presentation | `gestureCoaching`, `pitchGradePresentation`, `pitchFeedback.ts`, `PronunciationWorkspace.tsx`, `PitchPlot.tsx`, `PitchShapePlot.tsx` | Coaching describes reduced gestures independently of correctness. Labels, colors and graph rendering are presentation-only; UI geometry does not retune acoustic scores or measurements. |

The main flow is audio → ASR/alignment + raw F0/candidates → rejection/filtering →
owned syllable evidence → structural reliability → acoustic families → contextual
comparison → learner grade → coaching/presentation. Context is a parallel input
to comparison, never feedback into acoustic scoring. Backend contour diagnostics
and mobile family/learner results are distinct layers; the current learner grader
runs in mobile TypeScript, so exporting backend diagnostics alone is insufficient.

## Frozen invariants

- Raw tracker F0, candidates, audio identity and timing survive downstream stages.
  Selected pitch is a retained raw measurement, never interpolated, octave-repaired
  or moved toward the expected tone. Gaps and rejection reasons remain inspectable.
- Owned frames fall in the accepted timing span; playback uses that same canonical
  interval. Grouped timing does not imply separate character-level measurements.
- Shape, family scores, perturbations and gesture strength do not read target tones.
  Changing expectations can change the grade, never the observed family or frames.
- Structural trust, family clarity, family compatibility and gesture strength are
  different quantities. Support scores are heuristics, not calibrated probabilities.
- GREEN means compatible pronunciation **or insufficient evidence of meaningful
  learner concern**. It does not certify the acoustic label or imply native quality.
- AMBER means meaningful non-decisive concern or trustworthy ambiguity. RED requires
  the existing strong, stable, contextually incompatible evidence certificate.
  GRAY means evidence/expectation unavailable or untrustworthy, including standalone
  neutral with no fixed shape. No gate is changed here.
- A stable compatible family needs no minimum excursion/strength. Weak gesture
  coaching can coexist with GREEN. Trustworthy ambiguity remains AMBER.
- Contextual neutral non-veto requires the existing recognized chunk and exact
  playback conditions. An unreliable neutral remains GRAY but need not veto its
  head. Grade-bearing chunk precedence remains RED, then GRAY, then AMBER, then GREEN.
- Saved analyses remain immutable. Replays/export write only new research outputs.

Newest human analysis `cc8be88b-1211-4ef1-ae7e-0ebf8b99327c` remains 我 GREEN,
想 RED, 买 GREEN, 这 GREEN, 个 GRAY (neutral non-veto), 这个 GREEN. 我 and 买 retain
“Dip is shallow.” coaching. The newest background fixture remains GRAY. The
53-unit historical replay remains 20 GREEN / 16 AMBER / 3 RED / 14 GRAY.

## Why a perceptual experiment

Natural connected speech can be acceptable to a learner/native-listener standard
while deterministic acoustic-family interpretation is not trustworthy enough to
describe the perceived tone correctly. A normally spoken lexical T3 can rank as
T4-ish; conservative grading can avoid falsely correcting the learner while the
internal acoustic diagnosis remains misleading. The saved `a5acd04c:我` and
`b9067bec:想` are diagnostic instances of a T4 leader with GREEN, **not collected
native-listener ground truth**. Their family labels must not be relabeled to hide
this limitation.

This is **not another grading-threshold problem**. This checkpoint does not solve
it, add tone-shape exceptions, or change the retained ambiguity policy.

The next research question is:

> Can a learned perceptual/contextual model predict native-listener acceptability
> more reliably than the current deterministic grader?
