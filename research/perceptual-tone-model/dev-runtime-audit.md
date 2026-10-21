# Runtime audit before integration — 2026-10-19

No production files were edited for this audit. The starting tree includes the
uncommitted learner-transfer and blind-review work. It is preserved.

1. `apps/mobile/src/speech/useSpeechTurn.ts::useSpeechTurn` uses
   `audio/useAudioCapture` and calls `speech/workflow.ts::submitSpeech`.
2. `submitSpeech` uploads through `api/client.ts::uploadUtterance` to
   `services/api/src/benma_api/api/routes.py::create_utterance`;
   `audio/service.py` canonicalizes and stores the recording. Unknown-target
   `create_perception` calls `perception/service.py::PerceptionService` and the
   configured audio-only perception provider. `speech/providers/openai.py` owns
   the fixed transcription profile. Target text is not an ASR prompt.
3. The perceived branch calls `analyze_perceived_speech`,
   `pronunciation/perceived.py::PerceivedSpeechService.analyze`,
   `perceived_syllables`, `readings.py::resolve_run`, and
   `surface.py::surface_expectations`. Linguistic expectation is derived from
   exact text independently of acoustics, not after acoustic recognition.
4. `pronunciation/alignment.py` selects the configured aligner;
   `timing.py` validates/projects timing. Existing MFA `parse_textgrid` retains
   words/syllables, not phone-owned nucleus/coda intervals. Grouped timing must
   not be divided proportionally. Azure/provider timing is likewise not proof
   of a nucleus boundary.
5. `acoustics.py::PraatAcousticAnalyzer.analyze`,
   `pitch_evidence.py::{build_pitch_track,project_pitch,interpretation_eligibility}`,
   and `tone_graph.py::sentence_pitch_evidence` produce audio-only pitch evidence.
   Raw utterance acoustics can run before alignment; alignment projects it later.
6. The client `pronunciationWorkspace.ts::{pronunciationUnits,unitPitch}` and
   `pitchShapeEvidence.ts::unitShape` feed
   `toneLikeness.ts::classifyToneLikeness`. `learnerPitchGrade.ts::pitchExpectation`
   resolves grading expectation with surface precedence and documented lexical
   fallback; `gradeLearnerPitch` compares it with the deterministic family.
   `chunkPitchGrade.ts::gradeChunkPitch` preserves neutral non-veto handling.
7. `PronunciationWorkspace.tsx`, `SentenceToneGraph.tsx`, `PitchShapePlot.tsx`,
   and `PitchPlot.tsx` display pronunciation chunks, verdicts and contours.
8. The optional known-target branch separately creates an attempt and calls
   `PronunciationLaboratoryService.analyze/result`, `AssessmentService.assess`,
   alignment and acoustics. It does not replace the perceived speech graph.

## Narrow insertion and isolation

Insert a research adapter **after phone-owned alignment and acoustic extraction,
before experimental comparison/presentation**. Feed only verified source audio
and read-unit/pooling/context bounds to the frozen `Encoder.extract`; send its
layer-9 vector to the two saved heads. Expectation joins the results afterward.

All 413 baseline files are hash pinned, including runtime/client code. A new,
explicitly enabled loopback research recorder therefore calls the existing
read-only linguistic/acoustic functions through a service-environment subprocess,
and the existing frozen model through the research environment. No application
imports, settings, dependencies, routes or default grading change.

Use the pinned MFA model/lexicon in new per-take directories, strict
`aishell3_alignment.reconstruct`, and `aishell3_boundaries.derive`. No hand edits,
fixed-fraction crops, speaker adaptation or model fitting. Failed structural
checks abstain. Alignment remains a hypothesis requiring playback inspection.

`我想买这个` currently resolves 我/想/买 surface tones to **unresolved**
(`prosodic_grouping_unresolved`), 这 to T4, 个 to neutral, and proposes the
`这个` chunk. Preserve that exact behavior. Display lexical T3 separately;
the experimental path must not manufacture resolved sandhi or a numbered-neutral
judgment. No pre-learner learned-confidence operating point was established:
show probabilities and descriptive comparison without confident-error labels.

Before implementation: baseline 413/413; learner release manifest
`8024a51df91e60b9e336189cd9b04dfbf2d5d8c530fd0656778c731e1306f4ae`;
primary/diagnostic/unknown result seals verified. A read-only hash snapshot of
27,770 pre-existing research files is saved under
`data/generated/dev-learned-integration-v1/starting-files.json` for final checking.
