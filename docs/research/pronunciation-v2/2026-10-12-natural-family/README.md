# Natural-speech family calibration — October 12–13, 2026

Complete. This pass continued from the existing working tree, preserving the preceding measurement, dominant-gesture, shallow-valley, subordinate-island, neutral and learner-grading work. The final implementation and physical replays pass validation. No commit, push, deployment, provider call, new recording, or tracker investigation occurred.

The result is bounded: clean weak contours can receive a family without proving a canonical shape. Human 我 becomes weak T3; human 想 becomes a stable weak-T4 mismatch. Existing raw tracker failures in the Google take now correctly prevent numbered judgments. Those failures are an upstream limitation, not evidence that natural Mandarin requires exaggerated contours.

## Evidence and artifacts

- [Immutable arrival baseline](baseline.json): old scoring results for all 53 historical units, both newest takes and the new synthetic matrix, with original source hashes.
- [Final deterministic replay](results.json): all scores, geometric features, decisions, strengths, grades, perturbations, fixed-denominator gray counts and frozen controls.
- [Manual historical review](historical-review.json): every changed family/strength/grade/reason row, with winner, runner-up, features and an acoustic justification; all remaining trustworthy-gray units reviewed.
- [Original retained historical contours](historical-review.svg) and [physical/boundary contours](physical-and-boundary-contours.svg): original samples and original segment gaps, no interpretation smoothing applied to the plotted lines. Each panel has its own semitone scale; these are audit figures, not a changed learner graph.
- [Existing tone audit](tone-feedback-results.json), [CSV](tone-feedback-matrix.csv), [validation record](validation.json), [pass-specific file inventory](changed-files.json).
- The two takes use unchanged [saved provenance](../2026-10-12-learner-classification/physical-provenance.json). Canonical WAV hashes are verified by browser playback. Audio remains private and is not copied into this audit.

## Failure mode and architecture

The old ranker added 0.4 to whichever family matched the binary canonical shape. It then rejected all numbered families when that shape was UNCLEAR or its geometry label changed under perturbation. Thus clear weak motion could lose its family solely because it did not cross a 1–1.5 st geometry threshold. A visually level canonical label could also dominate a shallow natural valley.

The new ranker has no canonical-label bonus. `pitchShape.ts` exposes `familySafe` separately from the older `structurallyUsable` contract, which neutral handling still uses unchanged. Stable measurement support can survive a canonical-label boundary. Family ranking then evaluates all four explanations on the retained contour. Family-specific perturbations may veto a ranking; they cannot make unsafe evidence acceptable. Strength and contextual learner grading follow the family decision.

```text
retained and raw structural checks
  ├─ unreliable → UNAVAILABLE, no numbered family
  └─ trustworthy → four geometric supports → support + margin + stability
        ├─ clear winner → numbered family → strength → existing learner grade
        └─ competition, contradictory geometry or noise → UNCLEAR
```

Raw branch flags veto before initial scoring, even if the retained projection looks orderly or no longer contains the flagged raw frame. The offline adapter now preserves that raw flag fact. Initial unavailable results have zero storage placeholders for fits and null winner/runner-up; those zeros are not evaluated evidence. Further structural perturbation failure can only veto the result as UNAVAILABLE.

The existing structural rules remain: at least 8 finite points, at least 70 ms extent, strictly increasing timestamps, at least 75% support on the existing 10 ms source clock, no gap above 90 ms, no unexplained >1.5 st transition over a >25 ms gap, and no >6 st adjacent discontinuity. Existing narrow dominant-island handling is applied where it already qualified. All deletion probes must retain structural support. Raw voiced jumps >6 st within 120 ms retain the existing corruption veto. Grouped timing cannot acquire an individual numbered family. Unresolved readings still block grading when required.

No existing hard measurement/support failure is overridden by a fit. The saved broad eligibility/completeness diagnostic is not itself a new blanket veto: the already-approved dominant-island path remains available (human 这), while sparse support, missing critical support, contradictory islands, raw branches and octave errors stay unavailable. Neither source identity nor lexical expectation enters the acoustic scorer.

`decision` distinguishes NUMBERED, UNCLEAR and UNAVAILABLE; `evidence` distinguishes trustworthy from unavailable. For compatibility, the old `tone` field still stores UNCLEAR for both non-numbered decisions. Consumers and audits must use `decision`/`evidence` for the distinction. The learner UI retains the requested simple family copy and gray state; no scores or fake probabilities are exposed.

## Actual scoring terms

All supports are deterministic heuristics, not calibrated probabilities. Values below use semitones and seconds. `clip` clamps to [0,1]. Within each original island, a three-point median is used only for interpretation; all original graph points, timing and gaps are unchanged. The existing approved subordinate-island case scores its primary island only and still displays both islands.

Let `R` be the summary range and `noise` the 75th percentile absolute residual between original values and that median. Endpoint summaries are medians over `min(0.030, 0.10 × extent)` seconds. The movement scale is `s=max(0.12,3×noise)` and `S(x)=max(0,x)/(max(0,x)+s)`. A noise factor `C=1/(1+(3×noise/max(0.04,R))²)` multiplies every final support, preventing alternating jitter from becoming T1 merely through small amplitude.

Signed path consistency is movement in a direction divided by total absolute movement. Directional duration uses supported steps larger than local noise. `U` and `D` blend 75% path consistency with 25% duration consistency. `N` is end minus start, or the already-qualified dominant-gesture net change. Let `V` be valley support and `L` reduced-low support:

```text
T1 = C × max(exp(-abs(N)/0.35) × exp(-R/1.2),
             0.95 × exp(-R/2) × (1-abs(U-D))) × (1-0.6×max(V,L))
T2 = C × S(N) × U² × (1-0.5×V)
T3 = C × max(V,L)
T4 = C × S(-N) × D² × (1-0.65×L) × (1-0.5×V)
```

The trough time is the median time of samples within `min(0.35,0.10×R)` of the minimum. This avoids choosing an arbitrary absolute argmin on a low plateau. `F` is onset lowering, `Q` subsequent recovery to a peak, `p` normalized trough position and `q` normalized peak position. A short onset contribution uses the original first point only after subtracting `2×noise`, scaled by at least 20 ms of falling support and directional consistency; its weight fades between 30 and 70 ms. It is not a bonus from the canonical label.

```text
limb ratio = min(F,Q)/max(F,Q)
interior = clip((p-.06)/.09) × clip((.90-p)/.15)
limb time = clip(fall seconds/.025) × clip(recovery seconds/.040)
terminal = clip(1-max(0,1-q-.25)×4)
           × clip(1-max(0,retreat/max(Q,s)-.5)×3)
late rebound = clip((p-.60)/.15) × clip((.30-Q/max(s,F))/.15)
V = (1-late rebound) × S(min(F,Q)) × sqrt(fall consistency × rise consistency)
    × sqrt(clip((limb ratio-.08)/.17)) × interior × limb time × terminal
```

For reduced T3, inspect the final 40% of time. Let `lowering=max(0,start-median(tail))`, `tailRange=q90(tail)-q10(tail)`, and `arrival` be the normalized time where 80% of lowering is first reached:

```text
plateau = clip(1-tailRange/max(s,.5×lowering))
early = clip((.75-arrival)/.30)
context = clip(1-max(0,(R-lowering)/max(s,R)-.30))
L = (1-late rebound×(1-plateau)) × S(lowering) × plateau × early
    × downward consistency before tail × context
```

This requires lowering into a sustained low region. A continuing coherent fall with an active falling tail has little plateau support and remains T4. Relative low-register occupancy is within the unit; there is no absolute-Hz threshold or lexical-T3 input. Recovery/valley and T1 explanations still compete. All reduced T3 judgments are weak. Human 想 has plateau=0 and reduced support=0, so its lexical T3 cannot turn its measured fall into T3. The synthetic reduced-low contour and historical low-tail/fall boundary are explicit controls.

A numbered result requires winner support **≥0.42**, winner-minus-runner-up **≥0.12**, and the same ranked family on at least **5 of 7** family probes (`≥0.70`): remove first, last or every tenth point; alternate timestamps by ±2 ms; scale the endpoint region by 0.67 or 1.33. Every structural probe must pass. Consensus tolerates losing much of a short onset in one probe; it does not waive structural checks. Close scores, insufficient whole-contour support, noise dominance or unstable family competition remain UNCLEAR.

Strength is downstream: T2/T4 are full at `abs(existing geometry net)≥2 st`; ordinary T3 requires both existing fall and recovery ≥1.5 st. Reduced and completed-shallow variants stay weak. T1 retains full strength when its stable-level explanation wins. Family endpoint summaries can differ from the preserved strength summaries: human 想 has family net −2.043 st but existing strength net −1.806 st and is therefore weak. Strong compatible remains green, weak compatible amber, stable incompatible red, and unavailable/ambiguous gray. No contextual sandhi acceptance, lexical fallback, surface authority or neutral policy was expanded.

## Small-movement calibration

No absolute 0.1 or 0.2 st family gate was added. The dense 0.100–0.400 st sweep uses 0.005 st increments in both directions; maximum adjacent support change is 0.012300. Discrete labels still cross explicit support/margin boundaries, as any categorical decision must. A nearly level 0.1 st contour can remain T1; 0.2 st lies in level/direction competition; 0.4 st supports a weak direction.

| Direction | Excursion | Decision / strength | Winner | Runner-up | Margin |
| --- | --- | --- | --- | --- | --- |
| fall | 0.1 st | T1 / full | T1 0.673 | T4 0.422 | 0.251 |
| fall | 0.2 st | UNCLEAR / unavailable | T4 0.597 | T1 0.481 | 0.115 |
| fall | 0.4 st | T4 / weak | T4 0.756 | T1 0.242 | 0.514 |
| rise | 0.1 st | T1 / full | T1 0.702 | T2 0.442 | 0.260 |
| rise | 0.2 st | UNCLEAR / unavailable | T2 0.613 | T1 0.493 | 0.120 |
| rise | 0.4 st | T2 / weak | T2 0.760 | T1 0.243 | 0.517 |

Alternating ±0.05 st jitter and rapid sine jitter remain trustworthy but UNCLEAR. A 0.4 st coherent rise with small superimposed noise remains weak T2. Separate 0.98–1.02 st rise/fall/valley probes preserve their weak family across the former canonical excursion boundary.

## Physical replay

Each score triple is winner / runner-up / margin, rounded to three decimals. Unavailable evidence is not assigned a winner. Chunk grades aggregate constituents; 这个 has no invented single acoustic family or score. These are saved physical recordings replayed offline, not new live speaking trials.

### Human — `208711dc-c437-4afe-b6d3-2aa0e16fb7cb`

| Unit | Before family / strength / grade | After family / strength / grade | Evidence | Winner / runner-up / margin |
| --- | --- | --- | --- | --- |
| 我 | T1 / full / red | T3 / weak / amber | trustworthy | T3 0.597 / T1 0.284 / 0.313 |
| 想 | UNCLEAR / unavailable / gray | T4 / weak / red | trustworthy | T4 0.711 / T1 0.079 / 0.632 |
| 买 | T3 / full / green | T3 / full / green | trustworthy | T3 0.889 / T2 0.159 / 0.730 |
| 这 | T4 / full / green | T4 / full / green | trustworthy | T4 0.960 / T1 0.000 / 0.960 |
| 个 | UNCLEAR / unavailable / gray | UNAVAILABLE / unavailable / gray | unavailable | — (scoring bypassed) |
| 这个 | Aggregate / — / green | Aggregate / — / green | Trustworthy head; unmeasured neutral non-veto | — |

我 has 0.449 st onset lowering, an interior low region and 0.902 st measured recovery: T3 support 0.597 beats T1 0.284. 想 continues falling through its tail: T4 0.711 beats T1 0.079, with no reduced-low support. Its red grade is a stable mismatch against the unchanged lexical-T3 fallback, not a forced pass. 买 remains full T3. 这 retains the already-approved 11-frame primary island plus three-frame tiny tail, full T4, and an unchanged visible gap. 个 has no retained pitch (`insufficient_support` / learner reason `no_retained_pitch`); it remains neutral non-veto, so 这个 remains green. All four trustworthy units receive families; trustworthy gray falls from 1/4 to 0/4. Substituting intended text and changing lexical/surface tones leaves all acoustic results, including 我 and 想, exactly equal.

### Google — `df7476d5-5716-4399-a528-924075c3a0fb`

| Unit | Before family / strength / grade | After family / strength / grade | Evidence | Winner / runner-up / margin |
| --- | --- | --- | --- | --- |
| 我 | T2 / full / red | UNAVAILABLE / unavailable / gray | unavailable | — (scoring bypassed) |
| 想 | T3 / weak / amber | T3 / weak / amber | trustworthy | T3 0.828 / T2 0.196 / 0.631 |
| 买 | UNCLEAR / unavailable / gray | UNAVAILABLE / unavailable / gray | unavailable | — (scoring bypassed) |
| 这 | T4 / full / green | UNAVAILABLE / unavailable / gray | unavailable | — (scoring bypassed) |
| 个 | T1 / full / gray | UNAVAILABLE / unavailable / gray | unavailable | — (scoring bypassed) |
| 这个 | Aggregate / — / green | Aggregate / — / gray | Unavailable head; unreliable neutral non-veto | — |

The one trustworthy unit, 想, remains weak T3; there is **no trustworthy classifier abstention** in this take. Four units fail measurement reliability:

- 我: `raw_tracker_discontinuity`; an existing raw adjacent jump reaches 25.961 st. An orderly retained rise cannot override it.
- 买: `contradictory_fragments`; two comparable four-frame retained islands, separated by a large 13.016 st branch. Neither is a qualifying dominant island. The raw sequence also has a 140 ms gap. Family scoring is bypassed.
- 这: `raw_tracker_discontinuity`; existing raw jump reaches 30.649 st. Its retained fall cannot override that evidence.
- 个: `raw_tracker_discontinuity`; raw jump reaches 19.089 st. Its role stays `neutral_unreliable_nonveto` and its learner reason stays `unreliable_contextual_neutral`. It provides no correctness credit and cannot hide the unavailable head, so 这个 changes from green to gray.

The correction is at the reliability/scorer boundary; no attempt was made to repair, filter or explain the upstream tracker behavior.

## Gray-rate audit

The denominator is held at the **same 39 trustworthy historical units** before and after, using final unchanged structural rules plus correctly retained raw vetoes. The remaining 14 units are counted separately. This avoids crediting safety failures as improved classification.

| Historical category | Before | After |
| --- | ---: | ---: |
| Trustworthy T1 | 2 | 1 |
| Trustworthy T2 | 3 | 2 |
| Trustworthy T3 | 15 | 18 |
| Trustworthy T4 | 6 | 8 |
| Trustworthy UNCLEAR | 13 / 39 (33.3%) | 10 / 39 (25.6%) |
| Untrustworthy UNAVAILABLE | 11 / 14 | 14 / 14 |
| Untrustworthy, incorrectly numbered | 3 / 14 | 0 / 14 |
| Total learner gray | 24 / 53 | 24 / 53 |

Total gray stays unchanged because three unsafe numbered rows are now correctly unavailable. Green/amber/red counts change from 15/4/10 to 12/5/12. This is not an optimization for green or total pass rate.

The intentionally constructed 18-case matrix changes from T1/T2/T3/T4/UNCLEAR = 10/4/2/1/1 to 1/4/5/3/5. The five ambiguous controls are deliberately competing or contradictory; accepting all of them would be a regression. All 13 clear matrix cases survive the tested perturbations. The historical corpus was selected for difficult contours and is not a population estimate of Mandarin accuracy.

### Every remaining trustworthy-gray unit

The numeric runner-up below is the actual ranked runner-up. A local rise/valley/fall may also explain one portion of a contradictory contour without earning a high whole-contour score. Thus some gray cases fail the 0.42 support floor despite a large numerical margin; ambiguity is not restricted to two nearly equal numbers.

| Identifier | Winner / runner-up / margin | Abstention reason | Manual review |
| --- | --- | --- | --- |
| `89cee47e:想` | T4 0.360 / T1 0.049 / 0.310 | `contradictory_geometry` | The large middle rise is followed by a comparable terminal fall. A T4-like final descent competes with a valley plus a large third gesture; neither explains the whole contour coherently. |
| `6b5b2135:我` | T2 0.415 / T1 0.105 / 0.310 | `contradictory_geometry` | The later rise suggests T2, but an early abrupt rise and counter-fall interrupt the initial low region. T3-like lowering followed by recovery and T2-like net rise remain competing partial readings; the whole-track directional support is marginal. |
| `6b5b2135:想` | T4 0.298 / T1 0.147 / 0.151 | `contradictory_geometry` | Fall, large rise, and another large fall occupy substantial time. T3 explains the first two phases; T4 explains only the final descent. The terminal movement is not subordinate. |
| `ee8a8b32:想` | T1 0.271 / T4 0.238 / 0.033 | `contradictory_geometry` | An initial dip, middle rise and large terminal fall compete. Limited net movement alone does not establish T1; the directional lobes do not establish a single sustained T4 or completed T3. |
| `8d252264:一` | T3 0.565 / T2 0.428 / 0.137 | `family_perturbation_sensitive` | A supported shallow onset dip precedes the main rise. T2 and T3 fits are close across onset deletion and timing probes. The old canonical RISING bonus incorrectly made that competition disappear. |
| `8d252264:苹` | T2 0.206 / T1 0.167 / 0.039 | `contradictory_geometry` | The valley recovery loses most of its height in a substantial late fall. T2 and T3 explain the ascent but cannot account for the terminal counter-gesture as a small transition. |
| `8faf1a90:要` | T1 0.407 / T4 0.286 / 0.121 | `contradictory_geometry` | A middle peak is followed by lowering, a smaller rebound, then another fall. T1 explains the limited overall excursion and T4 the net fall, but neither has decisive whole-contour support. This is not a clean small monotonic movement. |
| `a5acd04c:果` | T3 0.499 / T2 0.446 / 0.052 | `close_candidates` | An interior lowering phase followed by a large rise gives T3 support alongside the dominant T2 trend. Removing the first point changes their balance. The old shape bonus concealed this close competition. |
| `b9067bec:我` | T4 0.518 / T3 0.403 / 0.115 | `close_candidates` | Early lowering and a long nearly-low tail support reduced T3, but continued downward drift supports T4. Their margin is below 0.12; this is deliberately not accepted as reduced T3 solely because it falls. |
| `5c70f317:想` | T3 0.344 / T1 0.204 / 0.140 | `contradictory_geometry` | A valley followed by a large rise and substantial retreat supports a T3 partial reading and a level/net-flat partial reading. The tail is too large to treat as subordinate; whole-contour support remains insufficient. |

The remaining cases have competing phases, a close low-tail/fall or rise/valley reading, or marginal whole-contour support. Manual review found no remaining plainly coherent weak direction/valley that should be classified solely to reduce gray. `6b5b2135:我` (best 0.415) and `8faf1a90:要` (best 0.407) are near the support floor and remain explicit calibration limitations.

## Every changed historical row

There are **13 family/strength/grade changes** and **8 additional reason changes**. All 21 were manually reviewed against original retained plots, numeric geometry and raw flag metadata. The following records include every row; unlisted historical rows retain their family/strength/grade/reason. Scores necessarily change across the whole corpus because the scoring model changed.

The requested category “desired newly-explicit ambiguity” also houses safety corrections in the review schema; those records explicitly say UNAVAILABLE and do not imply family competition. No changed row was accepted as an unexpected regression.

### `89cee47e:想` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `contradictory_geometry`.

T4 0.360; runner-up T1 0.049; margin 0.310. Geometry: net -2.532, fall 2.658, recovery 0.038, trough position 0.976, valley support 0.000, reduced support 0.000

The large middle rise is followed by a comparable terminal fall. A T4-like final descent competes with a valley plus a large third gesture; neither explains the whole contour coherently.

### `89cee47e:买` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNAVAILABLE / unavailable / gray**. Reason: `ambiguous_geometry` → `raw_tracker_discontinuity`.

None: measurement safety bypassed ranking. Geometry: Family geometry not evaluated because measurement safety failed.

Frozen raw branch flags 196/201 lie outside the retained projection. They now survive replay: unavailable evidence, not a newly accepted valley.

### `7e6b6fe9:想` — desired newly-explicit ambiguity

T3 / full / green → **UNAVAILABLE / unavailable / gray**. Reason: `best_fit` → `raw_tracker_discontinuity`.

None: measurement safety bypassed ranking. Geometry: Family geometry not evaluated because measurement safety failed.

Retained fall/recovery is clear, but raw branch flags 211/217 were previously dropped by the replay adapter. Structural rejection precedes scoring. This is an evidence-unavailable safety correction, not family competition.

### `6b5b2135:我` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `contradictory_geometry`.

T2 0.415; runner-up T1 0.105; margin 0.310. Geometry: net 3.243, fall 0.581, recovery 3.461, trough position 0.075, valley support 0.084, reduced support 0.000

The later rise suggests T2, but an early abrupt rise and counter-fall interrupt the initial low region. T3-like lowering followed by recovery and T2-like net rise remain competing partial readings; the whole-track directional support is marginal.

### `6b5b2135:想` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `contradictory_geometry`.

T4 0.298; runner-up T1 0.147; margin 0.151. Geometry: net -1.174, fall 1.520, recovery 3.412, trough position 0.202, valley support 0.000, reduced support 0.000

Fall, large rise, and another large fall occupy substantial time. T3 explains the first two phases; T4 explains only the final descent. The terminal movement is not subordinate.

### `0b194cf9:买` — desired newly-explicit ambiguity

T3 / full / green → **UNAVAILABLE / unavailable / gray**. Reason: `best_fit` → `raw_tracker_discontinuity`.

None: measurement safety bypassed ranking. Geometry: Family geometry not evaluated because measurement safety failed.

The retained valley cannot override raw branch flags 255/262. Previously numbered despite structurallyUsable=false; now unavailable before scoring.

### `ee8a8b32:我` — desired natural-speech calibration

T4 / full / red → **T3 / weak / amber**. Reason: `best_fit` → `best_fit`.

T3 0.660; runner-up T4 0.286; margin 0.373. Geometry: net -3.666, fall 4.616, recovery 1.099, trough position 0.672, valley support 0.660, reduced support 0.483

Early lowering reaches a sustained low region and a coherent, roughly 1.1 st recovery follows. T3 beats sustained T4 in the complete contour. Recovery is weak, so amber rather than green; endpoint/rebound sensitivity remains a documented T3/T4 boundary limitation.

### `ee8a8b32:想` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `contradictory_geometry`.

T1 0.271; runner-up T4 0.238; margin 0.033. Geometry: net -0.488, fall 1.000, recovery 0.000, trough position 1.000, valley support 0.000, reduced support 0.000

An initial dip, middle rise and large terminal fall compete. Limited net movement alone does not establish T1; the directional lobes do not establish a single sustained T4 or completed T3.

### `ee8a8b32:买` — desired newly-explicit ambiguity

T3 / full / green → **UNAVAILABLE / unavailable / gray**. Reason: `best_fit` → `raw_tracker_discontinuity`.

None: measurement safety bypassed ranking. Geometry: Family geometry not evaluated because measurement safety failed.

The retained valley looks strong, but raw branch flags 310/322 were outside the selected projection and silently disappeared in old replay. It is now unavailable evidence before ranking.

### `8d252264:一` — desired newly-explicit ambiguity

T2 / weak / amber → **UNCLEAR / unavailable / gray**. Reason: `best_fit` → `family_perturbation_sensitive`.

T3 0.565; runner-up T2 0.428; margin 0.137. Geometry: net 1.721, fall 0.410, recovery 2.130, trough position 0.188, valley support 0.565, reduced support 0.000

A supported shallow onset dip precedes the main rise. T2 and T3 fits are close across onset deletion and timing probes. The old canonical RISING bonus incorrectly made that competition disappear.

### `8d252264:苹` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `contradictory_geometry`.

T2 0.206; runner-up T1 0.167; margin 0.039. Geometry: net 0.542, fall 0.581, recovery 3.400, trough position 0.210, valley support 0.044, reduced support 0.000

The valley recovery loses most of its height in a substantial late fall. T2 and T3 explain the ascent but cannot account for the terminal counter-gesture as a small transition.

### `4b9dbd2b:要` — desired natural-speech calibration

UNCLEAR / unavailable / gray → **T2 / full / red**. Reason: `ambiguous_geometry` → `best_fit`.

T2 0.480; runner-up T1 0.103; margin 0.377. Geometry: net 2.075, fall 0.066, recovery 3.335, trough position 0.182, valley support 0.000, reduced support 0.000

Pitch rises well above its onset over the short supported span and remains above onset after the terminal retreat. T2 has clear support over the level alternative; full strength follows the preserved measured net excursion. Thinning this short track further can legitimately exhaust structural support.

### `4b9dbd2b:苹` — desired natural-speech calibration

UNCLEAR / unavailable / gray → **T3 / weak / red**. Reason: `perturbation_sensitive` → `best_fit`.

T3 0.923; runner-up T2 0.308; margin 0.615. Geometry: net 4.048, fall 1.440, recovery 5.487, trough position 0.228, valley support 0.923, reduced support 0.000

Coherent onset lowering, an interior low region and a much larger recovery support T3. The old fall/recovery-ratio gate flipped under deletion; family scoring retains the valley, with weak strength because the established fall summary is below 1.5 st.

### `8faf1a90:要` — desired newly-explicit ambiguity

T1 / full / red → **UNCLEAR / unavailable / gray**. Reason: `best_fit` → `contradictory_geometry`.

T1 0.407; runner-up T4 0.286; margin 0.121. Geometry: net -0.344, fall 0.418, recovery 0.276, trough position 0.732, valley support 0.000, reduced support 0.000

A middle peak is followed by lowering, a smaller rebound, then another fall. T1 explains the limited overall excursion and T4 the net fall, but neither has decisive whole-contour support. This is not a clean small monotonic movement.

### `8faf1a90:一` — desired natural-speech calibration

UNCLEAR / unavailable / gray → **T4 / weak / red**. Reason: `ambiguous_geometry` → `best_fit`.

T4 0.803; runner-up T3 0.077; margin 0.726. Geometry: net -1.251, fall 1.280, recovery 0.058, trough position 0.889, valley support 0.000, reduced support 0.077

The small fall is sustained across the unit; the latter portion keeps lowering instead of settling into a sufficiently stable low tail. T4 beats reduced T3. Low excursion changes strength to weak, not family to unclear.

### `a5acd04c:我` — desired natural-speech calibration

UNCLEAR / unavailable / gray → **T4 / weak / red**. Reason: `ambiguous_geometry` → `best_fit`.

T4 0.542; runner-up T1 0.184; margin 0.358. Geometry: net -1.205, fall 1.345, recovery 0.000, trough position 1.000, valley support 0.000, reduced support 0.000

After a small onset rise, sustained descent ends clearly below onset. T4 decisively exceeds T1; the 1.02 st legacy net summary gives weak strength.

### `a5acd04c:果` — desired newly-explicit ambiguity

T2 / full / red → **UNCLEAR / unavailable / gray**. Reason: `best_fit` → `close_candidates`.

T3 0.499; runner-up T2 0.446; margin 0.052. Geometry: net 4.371, fall 0.806, recovery 5.178, trough position 0.397, valley support 0.499, reduced support 0.000

An interior lowering phase followed by a large rise gives T3 support alongside the dominant T2 trend. Removing the first point changes their balance. The old shape bonus concealed this close competition.

### `b9067bec:我` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `close_candidates`.

T4 0.518; runner-up T3 0.403; margin 0.115. Geometry: net -1.695, fall 1.695, recovery 0.137, trough position 0.893, valley support 0.000, reduced support 0.403

Early lowering and a long nearly-low tail support reduced T3, but continued downward drift supports T4. Their margin is below 0.12; this is deliberately not accepted as reduced T3 solely because it falls.

### `b9067bec:想` — desired natural-speech calibration

UNCLEAR / unavailable / gray → **T4 / full / red**. Reason: `perturbation_sensitive` → `best_fit`.

T4 0.484; runner-up T1 0.055; margin 0.429. Geometry: net -2.789, fall 3.324, recovery 0.000, trough position 1.000, valley support 0.000, reduced support 0.000

Both the early and later portions descend, separated by a smaller middle recovery. Sustained net lowering and the final low boundary make T4 the best numbered explanation; the middle recovery prevents a simple valley interpretation. The preserved net fall exceeds 2 st, so full T4 and a mismatch.

### `5c70f317:我` — desired natural-speech calibration

UNCLEAR / unavailable / gray → **T3 / weak / amber**. Reason: `ambiguous_geometry` → `best_fit`.

T3 0.835; runner-up T4 0.246; margin 0.589. Geometry: net -1.366, fall 1.924, recovery 0.607, trough position 0.581, valley support 0.835, reduced support 0.241

A supported descent, interior low region and small coherent recovery support the T3 family without a textbook U. Recovery remains below the full-strength criterion, producing amber.

### `5c70f317:想` — desired newly-explicit ambiguity

UNCLEAR / unavailable / gray → **UNCLEAR / unavailable / gray**. Reason: `ambiguous_geometry` → `contradictory_geometry`.

T3 0.344; runner-up T1 0.204; margin 0.140. Geometry: net 0.012, fall 1.125, recovery 2.504, trough position 0.250, valley support 0.344, reduced support 0.000

A valley followed by a large rise and substantial retreat supports a T3 partial reading and a level/net-flat partial reading. The tail is too large to treat as subordinate; whole-contour support remains insufficient.

## Perturbations and safety controls

Both physical takes preserve every final family under first/last/internal point deletion, every-tenth deletion, +2 ms alternating timestamp jitter, +0.015 st endpoint perturbation, and +24/−0.3 st transposition. All 53 historical rows preserve family under transposition. The 13 clear synthetic cases additionally pass ±24/±0.3 st shifts, a single-point +4 ms shift, 1.015× time scaling plus 10 ms translation, two internal deletions and the endpoint perturbation. Changing target text, lexical tone and surface expectation does not change physical acoustic output. Strength/support may vary independently of family.

Universal historical invariance is not claimed. Boundary cases are retained in the audit, including:

| Row | Original | Perturbation behavior and interpretation |
| --- | --- | --- |
| `6b5b2135:我` | UNCLEAR | Endpoint/tenth deletion can produce T2; original support is 0.415, just below 0.42. |
| `ee8a8b32:我` | Weak T3 | Last deletion, tenth thinning or timing jitter can become UNCLEAR; weak recovery versus sustained T4 is a genuine boundary. Original has 5/7 family consensus. |
| `8d252264:一` | UNCLEAR | Endpoint/internal deletion or timing changes can favor T2 or T3; onset lowering is precisely the disputed evidence. |
| `4b9dbd2b:要` | Full T2 | Repeated thinning exhausts structural stability of the 12-frame span; it becomes UNAVAILABLE, not a contrary family. |
| `8faf1a90:要` | UNCLEAR | Last deletion can leave a T3-like partial valley; full contour includes the conflicting final fall. |
| `a5acd04c:一` | Full T1, unchanged from arrival | Endpoint/internal deletion or timing can become UNCLEAR; support 0.448 is near the absolute floor and the 18-frame contour contains a late dip/rebound. The original passes exactly 5/7 family probes. This is an acknowledged marginal case, not an invariance success. |
| `a5acd04c:果` | UNCLEAR | First deletion can favor T3; full contour has close T2/T3 support. |
| `b9067bec:我` | UNCLEAR | Endpoint deletion/timing can favor T4; original T4/T3 margin is 0.115. |
| `5c70f317:想` | UNCLEAR | Last deletion can favor T3; the complete tail contains a competing retreat. |

All four frozen corrupted 买 controls remain unavailable: historical `89cee47e` (`raw_tracker_discontinuity`), saved physical `e5c17b4e` (`missing_critical_support`), measurement `430fcc2e` (`insufficient_support`), and newest Google `df7476d5` (`contradictory_fragments`). Sparse, octave-jump, major-branch and comparable-island controls remain unavailable; comparable supported opposing gestures remain unclear. Strong fit values cannot override raw safety flags.

The subordinate-island constants and implementation, completed-shallow-valley constants and implementation, dominant-gesture safeguards, graph projection and neutral architecture are unchanged. The broad family scorer can recognize a shallow natural valley without using the older canonical label as a prerequisite; it does not relax the old extension or manufacture support across missing time. Existing tests still cover tiny onset microprosody, terminal counter-gestures, large/early/repeated fragments and corrupted valleys.

## Validation and browser review

| Check | Final result |
| --- | --- |
| Focused natural family, classification, shape, grade and measurement tests | 175 passed, 7 suites |
| `npm run validate` | Lint and typecheck passed; 713 tests passed, 43 suites |
| Final browser-script lint | Passed |
| Pronunciation-v2 and backend measurement/ownership regressions | 250 passed |
| Existing tone audit tests | 2 passed |
| Natural audit reproducibility/manual-review coverage/physical robustness tests | 2 passed |
| Measurement audit tests | 2 passed |
| Saved gesture/PCM audit | All 53 units replayed; prior evidence/artifacts unchanged |
| Physical and gray-rate replay | Both saved takes, 53 historical units, 18 matrix cases, dense small-movement sweep passed |
| Expo web export | Passed |
| Physical browser suite | Both takes × 320/390/412 px, 6 runs passed |
| Tone-feedback, measurement-fidelity, pronunciation-chunks and product-feedback browser suites | Each passed at 320/390/412 px |
| `git diff --check` and pass-specific whitespace check | Passed |

The browser assertions check exact original graph line counts, coordinates within 0.1 px, separate islands/gaps, no horizontal overflow, no page errors, canonical hashed WAV playback, history, keyboard selection, focus containment, Escape, neutral non-veto and all four learner colors. Older chunk/product suites needed selectors updated for the already-existing grade symbols, current graph accessibility name and technical-details panel; no production UI was changed. Physical screenshots were visually inspected for human weak T3, stable T4 mismatch, strong T4/green chunk, Google weak T3, unavailable head/chunk and unreliable neutral.

Logs and screenshots remain under `/tmp/benma-natural/`. Detailed browser result JSON is also summarized in `validation.json`. Existing React test-renderer deprecation/act warnings remain nonfatal. Local browser/server operations required sandbox execution approval and succeeded. No validation step remains blocked.

## Reproduction

From `apps/mobile`:

```sh
npm test -- --runTestsByPath src/__tests__/naturalToneFamily.test.ts src/__tests__/toneClassification.test.ts src/__tests__/toneLikeness.test.ts src/__tests__/pitchShape.test.ts src/__tests__/learnerPitchGrade.test.ts src/__tests__/chunkPitchGrade.test.ts src/__tests__/pitchMeasurement.test.ts
npm run validate
CI=1 ./node_modules/.bin/expo export --platform web --output-dir /tmp/benma-natural/web
```

From the repository root:

```sh
node benchmark/pronunciation_v2/tone_feedback_audit.cjs
node benchmark/pronunciation_v2/natural_family_audit.cjs
node benchmark/pronunciation_v2/test_tone_feedback.cjs
node benchmark/pronunciation_v2/test_natural_family_audit.cjs
node benchmark/pronunciation_v2/test_measurement_audit.cjs
services/api/.venv/bin/python -m benchmark.pronunciation_v2.gesture_readability_audit
services/api/.venv/bin/python -m pytest services/api/tests/test_acoustic_frontend.py services/api/tests/test_canonical_audio.py services/api/tests/test_pitch_projection_contract.py services/api/tests/test_utterance_pitch.py services/api/tests/test_sentence_tone_graph.py services/api/tests/test_tone_evidence_region.py services/api/tests/test_pronunciation_chunks.py benchmark/pronunciation_v2/test_raw_tracker_audit.py benchmark/pronunciation_v2/test_gesture_readability.py benchmark/pronunciation_v2/test_product_feedback.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py benchmark/pronunciation_v2/test_relative_pitch_fragments.py
```

Serve `/tmp/benma-natural/web` on loopback port 8099. Set `BENMA_WEB_URL=http://127.0.0.1:8099` and `PLAYWRIGHT_MODULE` to the installed Playwright module. Run the five `apps/mobile/scripts/{tone-classification,tone-feedback,measurement-fidelity,pronunciation-chunks,product-feedback}-browser.cjs` scripts. The tone-feedback suite also requires `BENMA_TONE_AUDIO` pointing to the original private canonical `19d8333bc4e04ce4bf026e393ea1f3e7.wav`. Use separate `BENMA_BROWSER_OUTPUT` paths. Finally run `git diff --check`.

## Scope and concrete limits

Pass-specific changes are in `pitchShape.ts`, `toneLikeness.ts`, the offline replay/audit, tests, browser harnesses and this audit folder. See `changed-files.json` for exact files and a line diff relative to arrival; ordinary Git statistics also include extensive pre-existing dirty work and do not describe this pass alone.

Raw F0, Praat/tracker settings, pitch selection/filtering, energy gate, VAD/silence, ASR, Azure alignment, timing/ownership, measurement projection, displayed geometry, pronunciation chunks, linguistic resolution, neutral grading and learner colors retain their arrival contents. Existing physical fixtures and earlier audits are hash-identical. The existing work was not reset, reverted or recreated.

This is a deterministic calibration over a small, selected corpus, not independent accuracy validation. The 0.42 support, 0.12 margin and 5/7 stability rule still create categorical boundaries, and the marginal historical cases above remain sensitive. Median windows and landmark timing can matter on very short spans. Reduced T3 and T4 overlap acoustically; local low-tail evidence cannot establish an absolute speaker register or prosodic grouping. T1 full strength remains the existing category and is not a calibrated confidence measure. Google raw discontinuities remain unresolved upstream. Browser replay verifies saved audio and UI behavior; it does not replace another live physical smoke test across speakers and recording conditions.
