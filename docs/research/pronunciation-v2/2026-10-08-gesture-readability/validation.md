# Validation and reproducibility

## Final scope

Production files changed: **none**. No API/schema/OpenAPI change, migration,
database mutation, acoustic configuration change, gesture release, UI copy change,
agreement state, commit, push, or deployment. Production workspace documentation
was intentionally not updated because production semantics did not change.

Research implementation:

- `benchmark/pronunciation_v2/workspace_projection.cjs`: executes real mobile unit
  projection and canonical crop functions; verifies every cropped PCM byte.
- `gesture_readability_audit.py`: saved identity/content hash, source indices,
  half-open spans, playback, and frozen numeric calibration corpus.
- `energy_gate_audit.py`: saved-path/selection statistics and canonical RMS check;
  no tracker, gate relaxation, or new classification of speech presence.
- `gesture_readability.py`: isolated research candidate and per-item comparison.
- `test_gesture_readability.py`: deterministic geometry, gaps, perturbation,
  discontinuity, grouping and saved failure tests.

API regressions:

- `services/api/tests/test_pitch_projection_contract.py` and physical fixture
  `pitch_projection_89cee47e.json`: source identity, API serialization, exact
  timestamp ownership, neighboring contours, boundary and gap cases, grouping,
  missing timing, and the actual eight energy-excluded 个 estimates.
- `test_energy_gate_saved_controls.py` and `energy_gate_saved_controls.json`:
  weak raw-only 个, strong/neutral controls, false-pitch negatives, digital
  silence/noise/clicks, unchanged low-F0 behavior, and character independence.

Mobile regression additions are confined to
`apps/mobile/src/__tests__/pronunciationWorkspace.test.ts`: physical 这/个 selection
switches, graph/playback identity, selected source indices, independent B evidence
despite strict ineligibility, target 广州 versus perceived 贵州, target changes,
and a new-analysis selection reset. Existing grouping/no-timing/accessibility tests
remain active.

## Checks

| Check | Result |
| --- | --- |
| Focused new projection + energy + research tests | **27 passed** |
| Actual production projection/crop replay | **13 recordings / 53 units / 1,852 measurements passed** |
| Immutable track content digests and canonical audio hashes | **13/13 matched** |
| Exact crop bytes | **Every cropped PCM byte matches the accepted canonical interval** |
| Mobile all native/web suites | **32 suites / 418 tests passed** |
| Mobile lint / typecheck | **Passed** |
| API pitch, groups, sentence graph, perceived speech, perception truth, laboratory | **167 passed** with expected test configuration |
| API Ruff / mypy | **Passed; 78 source files** |
| New research/test Ruff | **Passed** |
| Research mypy | **Passed; 3 new source files, Python 3.12 with API source path** |
| `git diff --check` | **Passed** |

The first broader API run had 166 passes and one laboratory assertion failure:
the local `.env` enables experimental tone interpretation, whereas that test
expects the default disabled flag. Rerunning the same selection with
`BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION=false` produced 167 passes. No
assertion, fixture default, local `.env`, or production configuration was weakened.
An initial mobile fixture import path and the research test's initially noncritical
removal window were corrected before the passing focused run. The geometry
regression exposed by calibration remains an explicit passing abstention test,
not an erased failed example.

Web/Android exports, generated OpenAPI and PostgreSQL write regressions were not
required: no production/build/schema/persistence code changed. PostgreSQL was used
only in read-only transactions to locate/export local evidence. Existing production
unit tests may run their ordinary synthetic analyzer checks; no research tracker
extraction or tracker/VAD bakeoff was rerun. No independent phone, listening panel,
VoiceOver or TalkBack smoke is claimed.

## Reproduce

Run from the repository root using existing local environments:

```sh
services/api/.venv/bin/python -m benchmark.pronunciation_v2.gesture_readability_audit
services/api/.venv/bin/python -m benchmark.pronunciation_v2.energy_gate_audit
services/api/.venv/bin/python -m benchmark.pronunciation_v2.gesture_readability
services/api/.venv/bin/python -m pytest benchmark/pronunciation_v2/test_gesture_readability.py services/api/tests/test_pitch_projection_contract.py services/api/tests/test_energy_gate_saved_controls.py -q
```

The first two commands need the existing private snapshots/canonical audio and
historical `services/api/var/f0-foundation` files. They never invoke trackers or
network services. The included numeric corpus and test fixtures make the
geometry candidate and focused regressions reproducible without those private
recordings. The projection bridge uses the existing mobile TypeScript dependency.
Each local source and waveform has a recorded hash. Manual corpus labels survive
replay rather than being overwritten by proposed classifications.

Local logs: `/tmp/benma-projection-replay.log`, `/tmp/benma-energy-replay.log`,
`/tmp/benma-geometry-replay.log`, `/tmp/benma-gesture-mobile-tests.log`,
`/tmp/benma-gesture-api-tests.log`, `/tmp/benma-gesture-api-tests-defaults.log`.

## Phone smoke status

No new production behavior earned a physical feedback smoke. The following small
checklist is prepared for the next implementation that passes these gates; it is
**not a passed test or a request for a new recording campaign**:

1. Exaggerated 我想买; compare the supported descent and recovery with each label.
2. Normal connected 我想买; do not expect a full U for every character.
3. 我想买这个; select 这 and compare graph bounds with exact Mine playback.
4. Select 个; distinguish a played syllable from available reliable F0. Inspect Raw
   if the graph is empty, without moving the accepted boundary.
5. Check a clear rising/falling contrast if needed; inspect textual state as well
   as any later-approved color.
6. Select grouped 雨伞; one span, one playback, no invented character grades.
7. New Attempt once; verify selection/audio do not retain the previous take.

## Remaining blockers and one next step

Energy: the eight weak estimates have no independently established vocal source;
coherence/periodicity exceptions admit known negative controls. Keep selection intact.

Geometry: short fixed endpoint anchors preserve the exaggerated onset but lose
five useful controls; six candidate descriptions fail perturbation stability.
The manual labels are exploratory assistant numeric review, with no held-out
independent human validation.

**One next step:** refine duration-supported endpoint regions on this frozen corpus
and require stable recovery of the five lost controls without losing the three
exaggerated valleys or admitting contradictory fragments. Do not change the energy
gate or proceed to colors during that refinement.
