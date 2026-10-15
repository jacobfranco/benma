# Minimum-concern continuation: arrival-relative changes

16 files changed; 5357 insertions, 427 deletions. This includes the new saved arrival grades, replay artifacts, validation records and this inventory.

Code/tests/audit scripts: 8 files, +152/−22. Production alone: learnerPitchGrade.ts, +18/−2.

The comparison starts from the exact working tree received for this continuation, including pre-existing untracked files. Whole-tree git status/diff includes earlier work and is not this pass's diff. Arrival copies and full checksums are local under /tmp/benma-concern/before and arrival-hashes.json.

| File | Added | Removed |
| --- | ---: | ---: |
| `apps/mobile/scripts/tone-feedback-browser.cjs` | 14 | 3 |
| `apps/mobile/src/__tests__/chunkPitchGrade.test.ts` | 3 | 1 |
| `apps/mobile/src/__tests__/conservativeLearnerGrade.test.ts` | 49 | 2 |
| `apps/mobile/src/__tests__/learnerPitchGrade.test.ts` | 1 | 1 |
| `apps/mobile/src/speech/learnerPitchGrade.ts` | 18 | 2 |
| `benchmark/pronunciation_v2/conservative_grading_audit.cjs` | 35 | 10 |
| `benchmark/pronunciation_v2/test_conservative_grading_audit.cjs` | 31 | 2 |
| `benchmark/pronunciation_v2/test_tone_feedback.cjs` | 1 | 1 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/README.md` | 120 | 131 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/concern-baseline.json` | 2922 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/concern-browser-results.json` | 1013 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/concern-changed-files.md` | 30 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/concern-validation.json` | 275 | 0 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/results.json` | 816 | 245 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/tone-feedback-matrix.csv` | 4 | 4 |
| `docs/research/pronunciation-v2/2026-10-13-conservative-grading/tone-feedback-results.json` | 25 | 25 |

All backend, acoustic, scoring, probe-generation, surface/context resolution, neutral handling, alignment, timing, graph, and selected-frame code/fixtures remain unchanged. The only production edit is the learner mismatch concern floor.

No commit, push or deployment.
