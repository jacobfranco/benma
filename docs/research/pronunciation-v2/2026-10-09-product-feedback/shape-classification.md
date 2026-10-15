# Broad retained geometry

`pitchShape.ts` classifies the exact selected numeric evidence that the learner graph
renders. The original API `observed_gesture`, strict eligibility and diagnostics are
preserved. The new result is a separate client-derived description, never a lexical
T1/T2/T3/T4 result. Vocabulary: **Level, Rising, Falling, Dip and rise, Shape unclear**.
Grouped timing and multi-unit chunks receive no aggregate shape judgment; separately
accepted constituents can be inspected independently.

## Candidate comparison

All methods use semitones and relative time, not absolute Hz or pixels. Linear uses
Theil–Sen slope and median residual. Quadratic uses four robust reweighting iterations,
positive curvature, an interior fitted minimum, >=1 st on both fitted limbs and
median residual <=0.75 st. The quadratic candidate falls back to the linear candidate.
Both fit candidates also receive the same basic support/gap/discontinuity guards and
first/last/every-tenth/flagged-point deletion checks. Raw ungated fit diagnostics are
recorded separately. No fitted curve is substituted for the measured graph.

| Method | Named outputs | Matches 29 unambiguous labels | Names a previously unclear item |
| --- | ---: | ---: | ---: |
| Existing saved five-bin + strict gate | 24 | 18 | 3 |
| Robust linear + guards/deletions | 22 | 9 | 9 |
| Robust quadratic/linear + guards/deletions | 35 | 23 | 9 |
| Retained piecewise geometry + stability | 29 | 28 | 1 |

A single slope loses valleys, particularly when recovery ends above onset. Quadratic
curvature recovers many valleys but can infer a misleading overall parabola across
local reversals. The direct piecewise method best describes the drawn evidence here.
These exploratory counts are not independent statistical accuracy or lexical tone
recognition. All manual labels remain those frozen before this pass; full per-item
fit coefficients, residuals, excursion, previous labels and abstentions are in JSON/CSV.

## Final piecewise model

Require >=8 retained samples and >=70 ms of selected extent. Keep the original 10 ms
source clock; selected support must occupy >=75% of that extent. Abstain on a gap
>90 ms between samples, a >6 st adjacent jump, or a >1.5 st reset across a gap >25 ms.
These are learner geometry guards; they neither relax nor replace the strict diagnostic
eligibility or production energy gate.

Summarize neighboring points with within-segment three-point medians. End regions use
30 ms of actual selected evidence. The observed low region is the median time of
smoothed points within 0.35 st of the measured low. Express its position relative to
the selected temporal extent. No smoothing or directional path step crosses an
original segment boundary. Small internal missing intervals stay missing in the graph.

- Dip/rise: low position 0.1–0.9, fall and recovery each >=1 st, weaker limb at least
  25% of the stronger, and directional consistency >=0.70 on each limb. Evaluate first.
- Level: local summarized range <=1.5 st and absolute endpoint movement <=1 st.
- Rise/fall: endpoint movement >=1.5 st, consistency >=0.75, and the contrary limb
  <1 st or <25% of the dominant limb.
- Anything else: unclear.

The 1 st limb / 1.5 st direction policy retains sustained shallow controls that the
previous 1.5/2 st prototype lost. A 0.2 st wobble stays level. The dominance condition
retains clear falls with small terminal rebounds instead of turning them into U shapes.
This is a bounded product policy, not a universal perceptual threshold. No global
threshold search or new recordings were used.

For every named result, remove first point, last point, every tenth point and retained
points implicated by raw discontinuities, and vary endpoint regions to 20/40 ms. Every
label must remain identical. Original segments are preserved throughout. A flagged
raw point already excluded from selected evidence makes that deletion a recorded no-op.
Strict mixed/incomplete evidence can support a stable retained shape; it cannot earn
a correctness claim or imply the missing tail was observed.

## Required cases and the 29th item

Exaggerated `7e6b6fe9` 我/想/买 all become stable **DIP_RISE**. Approximate 30 ms
fall/recovery values are **3.17/4.20**, **3.14/5.13**, **4.89/5.40 st** respectively.
All six perturbations preserve each result. The historical raw short-anchor 我 descent
was 3.7271 st; five-bin summarization reduced it to 0.2595 st. The new 3.17 st is a
different explicit endpoint summary of the same evidence, not a replacement physical
measurement. Normal physical `89cee47e:我` also becomes dip/rise, including its weaker
recovery (~1.51 st); its saved diagnostic remains level under Technical details.

**28/29**: `4b9dbd2b:苹` is the remaining unambiguous manually reviewed valley. Base
fall/recovery = **1.439504/5.163686 st**, ratio **0.278775**. Removing only its first
point gives **1.048572/5.163686 st**, ratio **0.203067**, crossing 0.25. Cause:
**endpoint sensitivity at the relative-limb threshold**, not gap handling or curvature.
The resulting candidate is unclear and therefore the final result is unclear. It
remains the requested borderline valley; no whole-classifier tuning forces 29/29.

**Previously ambiguous:** `40357072:想` is now dip/rise. Base fall/recovery =
**1.335526/2.252314 st** (ratio 0.592957); drop-first ratio remains 0.520989. All
six perturbations retain DIP_RISE. The retained plot has an internal valley followed
by recovery and a ~0.71 st late retreat. Calling its broad shape dip/rise is a useful,
stable product approximation; it does not assert the contour is a perfect U. Keep
its frozen manual UNCLEAR label and report the disagreement separately.

All 18 old useful descriptions remain; ten previously missed unambiguous shapes are
recovered. The pathological `40357072:买`, contradictory 这 fragments, unavailable 个,
and grouped 雨伞 do not receive invented shape judgments. Absolute pitch transposition
preserves labels. Independent labelled natural low-F0 shape truth is still absent;
synthetic transposition and saved low-F0 acceptance controls are explicitly distinct.
