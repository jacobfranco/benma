# Files changed in this pass

This inventory compares the completed working tree with the untouched arrival snapshot at `/tmp/benma-robustness/before`, including files that were already untracked on arrival. It excludes prior work that this pass did not change. No arrival file was deleted.

The table excludes this inventory document itself to avoid a self-referential diff count. Finalization added only documentation and evidence records; implementation was frozen.

Listed total: **43 files, +71,161 / −58 lines**. Large physical fixtures and audit JSON account for most additions.

| File | Arrival-relative status | Added | Removed |
| --- | --- | ---: | ---: |
| [apps/mobile/scripts/tone-classification-browser.cjs](../../../../apps/mobile/scripts/tone-classification-browser.cjs) | modified | 9 | 7 |
| [apps/mobile/scripts/tone-feedback-browser.cjs](../../../../apps/mobile/scripts/tone-feedback-browser.cjs) | modified | 1 | 1 |
| [apps/mobile/src/__tests__/chunkPitchGrade.test.ts](../../../../apps/mobile/src/__tests__/chunkPitchGrade.test.ts) | modified | 3 | 3 |
| [apps/mobile/src/__tests__/fixtures/pitchRobustnessPhysical.json](../../../../apps/mobile/src/__tests__/fixtures/pitchRobustnessPhysical.json) | added | 11682 | 0 |
| [apps/mobile/src/__tests__/learnerPitchGrade.test.ts](../../../../apps/mobile/src/__tests__/learnerPitchGrade.test.ts) | modified | 46 | 4 |
| [apps/mobile/src/__tests__/pitchRobustness.test.ts](../../../../apps/mobile/src/__tests__/pitchRobustness.test.ts) | added | 68 | 0 |
| [apps/mobile/src/__tests__/toneClassification.test.ts](../../../../apps/mobile/src/__tests__/toneClassification.test.ts) | modified | 1 | 1 |
| [apps/mobile/src/__tests__/toneFeedbackWorkspace.test.ts](../../../../apps/mobile/src/__tests__/toneFeedbackWorkspace.test.ts) | modified | 3 | 3 |
| [apps/mobile/src/api/openapi.json](../../../../apps/mobile/src/api/openapi.json) | modified | 1 | 1 |
| [apps/mobile/src/speech/PronunciationWorkspace.tsx](../../../../apps/mobile/src/speech/PronunciationWorkspace.tsx) | modified | 2 | 2 |
| [apps/mobile/src/speech/chunkPitchGrade.ts](../../../../apps/mobile/src/speech/chunkPitchGrade.ts) | modified | 2 | 1 |
| [apps/mobile/src/speech/learnerPitchGrade.ts](../../../../apps/mobile/src/speech/learnerPitchGrade.ts) | modified | 32 | 6 |
| [apps/mobile/src/speech/pitchShapeEvidence.ts](../../../../apps/mobile/src/speech/pitchShapeEvidence.ts) | modified | 3 | 0 |
| [benchmark/pronunciation_v2/natural_acceptance_audit.cjs](../../../../benchmark/pronunciation_v2/natural_acceptance_audit.cjs) | added | 57 | 0 |
| [benchmark/pronunciation_v2/pitch_robustness_replay.py](../../../../benchmark/pronunciation_v2/pitch_robustness_replay.py) | added | 126 | 0 |
| [benchmark/pronunciation_v2/raw_tracker_audit.py](../../../../benchmark/pronunciation_v2/raw_tracker_audit.py) | modified | 16 | 3 |
| [benchmark/pronunciation_v2/test_natural_acceptance_audit.cjs](../../../../benchmark/pronunciation_v2/test_natural_acceptance_audit.cjs) | added | 13 | 0 |
| [benchmark/pronunciation_v2/test_natural_family_audit.cjs](../../../../benchmark/pronunciation_v2/test_natural_family_audit.cjs) | modified | 6 | 11 |
| [benchmark/pronunciation_v2/test_pitch_robustness_replay.py](../../../../benchmark/pronunciation_v2/test_pitch_robustness_replay.py) | added | 22 | 0 |
| [benchmark/pronunciation_v2/test_tone_feedback.cjs](../../../../benchmark/pronunciation_v2/test_tone_feedback.cjs) | modified | 3 | 3 |
| [benchmark/pronunciation_v2/tone_feedback.cjs](../../../../benchmark/pronunciation_v2/tone_feedback.cjs) | modified | 2 | 1 |
| [benchmark/pronunciation_v2/tone_feedback_audit.cjs](../../../../benchmark/pronunciation_v2/tone_feedback_audit.cjs) | modified | 1 | 1 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/README.md](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/README.md) | added | 204 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/baseline-api-failures.log](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/baseline-api-failures.log) | added | 190 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/baseline.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/baseline.json) | added | 9777 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/browser-results.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/browser-results.json) | added | 1004 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/historical-rejection-audit.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/historical-rejection-audit.json) | added | 238 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/measurement-audit.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/measurement-audit.json) | added | 779 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/natural-family-results.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/natural-family-results.json) | added | 21653 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/physical-provenance.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/physical-provenance.json) | added | 18 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/provenance-audit.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/provenance-audit.json) | added | 130 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/raw-tracker-audit.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/raw-tracker-audit.json) | added | 2203 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/results.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/results.json) | added | 9405 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/tone-feedback-matrix.csv](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/tone-feedback-matrix.csv) | added | 161 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/tone-feedback-results.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/tone-feedback-results.json) | added | 12534 | 0 |
| [docs/research/pronunciation-v2/2026-10-13-natural-acceptance/validation.json](../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/validation.json) | added | 264 | 0 |
| [services/api/src/benma_api/pronunciation/acoustics.py](../../../../services/api/src/benma_api/pronunciation/acoustics.py) | modified | 18 | 5 |
| [services/api/src/benma_api/pronunciation/contours.py](../../../../services/api/src/benma_api/pronunciation/contours.py) | modified | 28 | 1 |
| [services/api/src/benma_api/pronunciation/pitch_evidence.py](../../../../services/api/src/benma_api/pronunciation/pitch_evidence.py) | modified | 41 | 3 |
| [services/api/src/benma_api/pronunciation/pitch_rejection.py](../../../../services/api/src/benma_api/pronunciation/pitch_rejection.py) | added | 181 | 0 |
| [services/api/src/benma_api/pronunciation/pitch_types.py](../../../../services/api/src/benma_api/pronunciation/pitch_types.py) | modified | 1 | 1 |
| [services/api/tests/fixtures/pitch_robustness_physical.json](../../../../services/api/tests/fixtures/pitch_robustness_physical.json) | added | 1 | 0 |
| [services/api/tests/test_pitch_rejection.py](../../../../services/api/tests/test_pitch_rejection.py) | added | 232 | 0 |

## Scope

Product changes are limited to learner grading/coaching and its expectation adapter; explicit acoustic rejection and retained-evidence interpretation; algorithm/version defaults. Test, replay, browser, fixture, and audit changes validate those behaviors. Existing family-scoring, alignment, ASR, ownership, graph projection, and neutral-policy implementations were preserved.

Arrival and current SHA-256 hashes for this inventory comparison are retained locally in `/tmp/benma-robustness/pass-changes.json`. Existing audit directories from earlier passes were not overwritten.
