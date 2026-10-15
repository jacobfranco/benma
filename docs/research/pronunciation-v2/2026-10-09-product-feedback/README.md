# Product feedback — October 9 pass, completed October 10, 2026

## Current checkpoint: dominant supported tone-family feedback

The focused post-smoke policy is implemented: dominant measured gestures,
explicit surface precedence, lexical-family fallback, green/amber/red/gray feedback,
and bounded positive neutral acceptance. All acoustic labels remain target-independent.

| Fresh constituent | Shape / tone | Basis | Result |
| --- | --- | --- | --- |
| 我 | Dip-rise / T3, full | Lexical T3 family | Green |
| 想 | Dip-rise / T3, weak shallow dip | Lexical T3 family | Amber |
| 买 | Unclear / unavailable | Lexical T3 family | Gray: missing/fragmented support |
| 这 | Falling / T4, full | Resolved surface T4 | Green |
| 个 | No retained pitch | Neutral | Gray, non-vetoing |
| 这个 | Constituent aggregation | Strong head, unmeasured neutral | Green |

All 29 previously classifiable corpus units keep their acoustic family; 24 stay
unclear. Corpus grades now total 15 green / 4 amber / 10 red / 24 gray.
No fixture, backend, provider, alignment or dependency change was needed.

- [Focused pass, changed cases and validation](dominant-gesture-pass.md)
- [Tone-likeness](tone-likeness.md), [expectation hierarchy](learner-grading.md)
- [Neutral acceptance](neutral-dependent-policy.md), [color semantics](color-policy.md)
- [Production CSV](tone-feedback-matrix.csv), [production JSON](tone-feedback-results.json)

Earlier checkpoint notes below remain historical. This pass does not claim a new
physical-device test or change speech-presence acceptance.

## Previous graph/shape pass (historical decisions, superseded above for tone/color)

**Normalized compact graph, broad measured shape, and learner details earned integration.**
The compact design is a 100 px identity/playback rail beside a 96 px graph. Both
learner axis titles are removed. More Details uses a 152 px normalized graph;
Technical details contains the existing real-time evidence and strict diagnostics.

The frozen 53-unit / 1,852-point replay agrees with **28/29 unambiguous broad geometry
labels**, preserves **all 18 previously useful descriptions**, and recovers exaggerated
我/想/买. These are exploratory geometry labels, not lexical-tone truth or an independent
accuracy estimate. One borderline valley abstains, and one previously ambiguous shape
is now described as a dip and rise. Neither exception is hidden or relabelled.

**Contextual comparison and colors remain research only.** No green, amber, orange,
red, score, or pronunciation correctness claim has been added. Existing perceived
identity, contextual surface rules, chunk policy and acoustic evidence remain authoritative.

**Acceptance needs one specific follow-up:** distinguish language-undetermined real
short/low-F0 speech from non-speech before allowing UNKNOWN to become learner evidence.
The approved experiment distinguishes the confirmed English and throat-clear failures,
but the low-F0 positive returns the same empty-language result as throat-clearing. One
short request times out. No production acceptance or provider configuration changed.

| Gate | Decision |
| --- | --- |
| Graph | NORMALIZED COMPACT GRAPH EARNED INTEGRATION |
| Shape | SIMPLE BROAD SHAPE CLASSIFIER EARNED INTEGRATION |
| Comparison | COMPARISON NOT YET JUSTIFIED |
| Color | COLOR NOT YET JUSTIFIED |
| Acceptance | ACCEPTANCE NEEDS ONE SPECIFIC FOLLOW-UP |
| Details | LEARNER DETAILS REDESIGN EARNED INTEGRATION |
| Overall | CORE FEEDBACK STILL BLOCKED by acceptance; the graph/shape/details slice is ready for physical smoke |

- [Normalized display and responsive decision](normalized-graph.md)
- [Shape method, fits, and both exceptional cases](shape-classification.md)
- [Exact approved requests and acceptance conclusion](acceptance-gate.md)
- [Contextual comparison and color gate](learner-comparison.md)
- [Validation, changed files, limitations, and phone checklist](validation.md)
- [53-unit matrix](calibration-matrix.csv), [full numeric results](shape-results.json),
  [summary](shape-summary.json), [frozen contextual expectations](expected-context.json)
- [Additional chunk/acceptance controls](supplemental-matrix.csv),
  [negative physical controls](negative-controls.json),
  [approved manifest](approved-upload-manifest.json), [preflight responses](acceptance-preflight.json)

Truth boundaries remain explicit: **physical evidence → display normalization → observed
shape**, separately **perceived reading/context → expected shape → proposed learner agreement**.
Display normalization never becomes acoustic truth. No user audio is added to versioned files.
No commit, push, deployment, destructive Git operation, tracker/VAD experiment, energy-gate
change, or chunk-policy expansion occurred.
