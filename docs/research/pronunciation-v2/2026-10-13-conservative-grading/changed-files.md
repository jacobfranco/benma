# Files changed relative to arrival

This report compares against the user's working tree at the start of this pass, including existing untracked files. It does not attribute previous pronunciation-v2 work to this change.

**29 files; +101,014 / −124 lines.** Most added lines are immutable baseline and replay evidence.

Production: **3 files; +74 / −36 lines.** No backend, acoustic, classifier, pitch-selection, fixture, alignment, graph, ASR, or neutral-evidence implementation changed.

| Path | Added | Removed |
| --- | ---: | ---: |
| `apps/mobile/scripts/tone-classification-browser.cjs` | 9 | 3 |
| `apps/mobile/scripts/tone-feedback-browser.cjs` | 22 | 9 |
| `apps/mobile/src/__tests__/chunkPitchGrade.test.ts` | 1 | 1 |
| `apps/mobile/src/__tests__/conservativeLearnerGrade.test.ts` | 76 | 0 |
| `apps/mobile/src/__tests__/learnerPitchGrade.test.ts` | 8 | 10 |
| `apps/mobile/src/__tests__/pronunciationWorkspace.test.ts` | 1 | 1 |
| `apps/mobile/src/__tests__/toneClassification.test.ts` | 2 | 2 |
| `apps/mobile/src/__tests__/toneFeedbackWorkspace.test.ts` | 4 | 4 |
| `apps/mobile/src/speech/PronunciationWorkspace.tsx` | 5 | 2 |
| `apps/mobile/src/speech/chunkPitchGrade.ts` | 3 | 1 |
| `apps/mobile/src/speech/learnerPitchGrade.ts` | 66 | 33 |
| `benchmark/pronunciation_v2/conservative_grading_audit.cjs` | 111 | 0 |
| `benchmark/pronunciation_v2/natural_acceptance_audit.cjs` | 18 | 45 |
| `benchmark/pronunciation_v2/test_conservative_grading_audit.cjs` | 19 | 0 |
| `benchmark/pronunciation_v2/test_natural_family_audit.cjs` | 1 | 1 |
| `benchmark/pronunciation_v2/test_tone_feedback.cjs` | 4 | 4 |
| `docs/development/pronunciation-learner-experience.md` | 15 | 4 |
| `docs/development/pronunciation-workspace.md` | 15 | 4 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/README.md` | 175 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/baseline.json` | 55,046 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/browser-results.json` | 1,010 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/changed-files.md` | 39 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/finalization.json` | 64 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/frozen-inputs.json` | 188 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/red-contours.svg` | 87 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/results.json` | 30,881 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/tone-feedback-matrix.csv` | 161 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/tone-feedback-results.json` | 12,691 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/validation.json` | 292 | 0 |
