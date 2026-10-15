# Per-unit pitch truth, energy rejection, and gesture readability

Completed October 9, 2026, continuing the October 8 bounded pass. No production
semantics changed; no commit, push, deployment, tracker rerun, VAD study, model,
numeric pronunciation score, or color grading was introduced.

| Layer | Checkpoint | Evidence |
| --- | --- | --- |
| Projection | **PER-UNIT PITCH PROJECTION VERIFIED** | Actual production mobile projection and PCM cropping replayed on 13 recordings, 53 units, 1,852 selected measurements; focused regression tests pass. |
| Energy | **ENERGY GATE NEEDS ONE SPECIFIC REFINEMENT** | Decision C: distinguish weak 54–70 Hz phonation from periodic background before proposing an admission rule. This is an evidence-discrimination question, not proof of a threshold bug. |
| Gesture | **GESTURE READABILITY NEEDS ONE SPECIFIC REFINEMENT** | Decision B: a boundary-stable start/turn/end summary that retains the onset descent without losing established rise/fall controls. |
| Color | **COLOR NOT YET JUSTIFIED** | No agreement implementation or color experiment. |
| Overall | **TONE FEEDBACK STILL BLOCKED** | Projection is closed; energy provenance and geometry stability remain separate unresolved issues. |

The sole locally saved perception matching 我想买这个 is attempt
`2706b173-a023-43fe-a018-a8925a58a60f`, analysis `874ae05a-bd67-4836-a53c-f78df5d129b0`,
recording `89cee47ede594941baf0f4ad758b971a.wav`, October 8 at **23:03:11 EDT**
(October 9 03:03:11 UTC). It reproduces the reported graph configuration. Device
playback was not repeated by the agent.

这's two fragments are both inside its accepted 2.34–2.73 s span. The second is
2.6604–2.7004 s, before 个 begins at 2.74 s. There is no evidence theft to fix.
个 has eight native raw estimates and zero selected measurements: all eight fail
the existing RMS threshold **0.006968468060966106**. Its louder middle has no native
voiced estimate, independently of the energy gate. Audible speech is not proof of F0.

The matching exaggerated 我想买 analysis `44075f37-3359-4efb-8f88-73e373470fdd`
(recording `7e6b6fe9`, October 8 22:22:56 EDT) explains the reported labels. 我's
five-bin fall is only **0.2595 st**, although its retained early descent is **3.7271 st**
under the prototype's short robust start/low-region summary. 想/买 retain clear
numeric valleys but fail strict raw-integrity criteria. The research prototype
describes all three as dip/rise, yet loses five useful descriptions elsewhere.
It has not earned production integration.

- [Projection identity, bounds, and source indices](projection-forensics.md)
- [Eight-frame energy audit and controls](energy-gate.md)
- [Geometry, calibration, and integration gate](gesture-calibration.md)
- [Agreement policy and unchanged learner presentation](agreement-policy.md)
- [Validation, reproducibility, and next step](validation.md)
- [Every calibration item](calibration-comparison.csv), [numeric corpus](calibration-corpus.json),
  [results and sensitivity](calibration-results.json), [summary](calibration-summary.json)
- [Full projection audit](projection-replay.json), [energy audit](energy-replay.json)

Manual geometry labels are the assistant's explicit review of numeric retained
paths, not screenshot classification, an independent human panel, lexical tone
truth, acoustic ground truth, or a claim about what the speaker intended. Multiple
我想买 takes exist; only `7e6b6fe9` matches all three reported eligibility/gesture
states. Its intended exaggeration is inferred from the user report and numeric
shape, not independently documented capture instructions.

The interrupted worktree contained the production-function replay bridge, numeric
audit/corpus, the physical fixture, and incomplete projection regression additions.
It contained no integrated geometry classifier or production edit. Continuation
fixed the fixture import and target-mismatch test setup, finished those regressions,
and continued the same short-region/minimum semitone geometry family with sensitivity
checks. No existing user work was discarded.

**One next step:** refine the start/turn/end summary against this frozen corpus,
requiring recovery of the five lost controls while preserving the three exaggerated
valleys and abstention on contradictory fragments. Keep the energy gate unchanged.
