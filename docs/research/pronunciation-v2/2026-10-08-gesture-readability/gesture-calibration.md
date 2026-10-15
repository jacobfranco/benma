# Broad geometry calibration

**Decision B: GESTURE READABILITY NEEDS ONE SPECIFIC REFINEMENT.** Replace the fixed
three-frame endpoint anchors with duration-supported endpoint regions whose label
survives reasonable changes to region width. Preserve the observed onset descent
and recover the five already-useful rise/fall/valley controls lost by this candidate.
Production gesture semantics and strict eligibility remain unchanged.

## Three independent questions

1. **Measurement integrity:** is the native/raw path complete and consistent with
   selection? The unchanged `voiced-support-completeness-v1` gate records boundary
   loss, attrition, raw discontinuities, fragmentation, sustained support, and provenance.
2. **Gesture readability:** what coarse movement is supported by the exact retained
   measurements shown in this unit's graph? A clean selected valley can coexist
   with a rejected raw tail and mixed integrity. This describes retained evidence,
   not a reconstructed whole syllable or reliable acoustic ground truth.
3. **Learner agreement:** is a sufficiently trustworthy readable gesture compatible
   with contextual expected realization? Neither of the first two questions grants
   permission to grade. This layer remains unimplemented.

## Exact reported-label match

Six saved short 我想买 takes were inspected by timestamp and included in the corpus.
The analysis `44075f37-3359-4efb-8f88-73e373470fdd`, recording `7e6b6fe9`, at
2026-10-09 02:22:56 UTC / October 8 22:22:56 EDT uniquely matches the reported
combination within those takes: rising/clear, unavailable/mixed-disagreement,
unavailable/mixed-missing. The newer `6b5b2135` at 22:56:51 EDT has sufficient 想,
so it is not the same three-label example. Capture intent is not stored; this
matching analysis is the strongest evidence match, not user confirmation of a take ID.

| Unit | Timing | Selected support | Strict state/reason | Current | Prototype |
| --- | --- | --- | --- | --- | --- |
| 我 | 0.52–1.22 | 55 points, 0.672–1.212 s | sufficient | rising | readable dip_rise |
| 想 | 1.23–2.23 | 51 points, 1.622–2.122 s | unstable: raw_pitch_discontinuity | unclear | tentative dip_rise |
| 买 | 2.36–3.25 | 59 points, 2.422–3.002 s | incomplete: voiced_boundary_lost, raw_to_selected_attrition, fragmented_voiced_support | unclear | tentative dip_rise |

想's raw jump is **14.0975 st**; the selected contour is continuous, maximum adjacent
jump **0.4604 st**, and its excluded tail lasts 100 ms. 买 loses 240 ms of its raw
voiced extent; its late-third retention is 0.30 and its raw gap is 170 ms. Its retained
59-point contour is continuous. Describing that visible valley does not imply the
lost tail was correct or that the entire uttered gesture is known.

## Current classifier and five-bin loss

The current path is `display_from_track` → accepted slice → `classify_contour` →
strict `gate_observation` → serialized `observed_gesture` → mobile strict gate.
It uses a smoothed display contour and five equal-count median bins, while the
workspace plots unsmoothed retained measurements. The classifier already measures
an internal minimum, fall/recovery, residuals, path movement, and gaps. It is not
merely a last-minus-first test. Its rise rule, however, precedes its canonical
valley rule and admits a minor sag if the five-bin fall is below 1.5 st, endpoint
rise is at least 2 st, and the other movement conditions pass.

| Unit | Existing five median bins (st) | Five-bin fall / recovery | Prototype robust start / minimum / end | Prototype fall / recovery |
| --- | --- | --- | --- | --- |
| 我 | 0.3506, 0.4219, 0.0911, 1.3711, 4.1039 | 0.2595 / 4.0128 | 3.6828 / −0.0443 / 4.1039 | 3.7271 / 4.1482 |
| 想 | 0.0705, −2.0101, −1.7082, −0.0268, 2.8966 | 2.0806 / 4.9066 | 0.9861 / −2.2274 / 2.8966 | 3.2135 / 5.1240 |
| 买 | −0.2144, −3.0898, −2.9560, −2.9251, 1.1474 | 2.8754 / 4.2372 | 2.1722 / −3.1629 / 2.1188 | 5.3352 / 5.2817 |

For 我 the first bin contains eleven frames. Its median mostly sees the low plateau,
discarding the duration-short but substantial early descent. The current endpoint
movement is +3.7533 st; short robust endpoint movement is only +0.4211 st. Both
valley limbs are measured. Thus the binning plus representation choice concretely
explains the rise label; merely swapping rise/valley priority would not recover the
lost fall feature. Five bins still work on many clean controls and are not rejected
universally. Complete per-item five-bin arrays are in the comparison CSV.

## Candidate geometry and explicit limitations

The research-only `benchmark/pronunciation_v2/gesture_readability.py` takes retained
semitone points, segment boundaries, grouped status, integrity state and flagged
source indices. There are no characters, Hz thresholds, lexical tones, targets,
surface expectations, learned models, or screenshots among its inputs.

The candidate summarizes three neighboring real samples at a time within continuous
segments. Start/end use three actual edge frames. A robust low region consists of
observed local medians within 0.5 st of the minimum; its median time describes a
plateau without inventing an F0 point. It records start/end, min/max, minimum time
and relative position, fall, recovery, total excursion, net movement, directional
consistency, support duration/fraction, gap count/duration, and retained jump metrics.

One fixed candidate, no threshold grid search: ≥12 selected frames / 120 ms,
≥0.8 support fraction within selected extent, no gap exceeding 80 ms, no retained
jump over 6 st. Dip/rise requires both excursions ≥1.5 st, an interior low region
between 0.15 and 0.85, and ≥0.7 directional consistency on each limb. It is checked
before rise/fall. Rise/fall use ≥2 st endpoint movement with ≥0.8 directional
consistency; level requires ≤1.5 st robust range and ≤1 st endpoint movement.
These borrow the scale of existing diagnostic rules, not empirically certified
pronunciation thresholds. Their failures are the reason integration is denied.

Small gaps remain missing. No line, point, or gesture evidence is interpolated.
Movement across a gap does not count toward directional consistency; smoothing
never spans a missing frame. Missing a critical region, contradictory fragments,
an isolated large retained branch, or grouped timing produces unavailable. There
is no policy that all unstable/incomplete evidence becomes readable.

For a named candidate, four read-only perturbations are mandatory: remove the
first frame, remove the last frame, remove every tenth selected point, and remove
selected endpoints implicated in raw jumps over 6 st. Preserve original gaps and
account for newly missing support. Every perturbation must retain the same label.
A stable result is `readable` only with sufficient strict integrity, otherwise
`tentative`. Neither is a tone grade. In particular, removing excluded raw jumps
can be a no-op on already retained points; the audit records this honestly.

## Corpus and manual labels

The frozen corpus is 13 existing recordings, 53 accepted units, 1,852 exact displayed
points. It includes six short 我想买 takes, the physical 我想买这个, the historical
40357072 long phrase/grouped 雨伞, four apple-phrase controls, and untimed d47274bc.
Its 53 accepted units exclude the untimed take. It covers broad U gestures, rise,
fall, level, connected reduced movement, neutral 个, short/sparse evidence,
raw discontinuity, excluded tails, retained octave branches, and grouping. Recording
intent (“normal” versus “deliberately exaggerated”) is not independently attested
for every capture. No lexical tone was used as an observed label.

Assistant numeric review was recorded before running the candidate classifications:
18 DIP_RISE, 6 FALLING, 3 RISING, 2 LEVEL, 24 UNCLEAR. Ambiguous shapes are explicitly
unclear. These are exploratory manual numeric geometry labels, not an independent
human-visible-graph study. There is no screenshot classifier. Low-F0 safety is
tested by semitone transposition and the separately saved 70/110 Hz controls;
we do not claim independently labelled natural low-F0 geometry in this corpus.

## Results and gate

| Comparison | Current | Proposed |
| --- | --- | --- |
| Named descriptions | 24 | 20 |
| Named descriptions agreeing with the 29 unambiguous numeric labels | 18 | 20 |
| New useful descriptions versus current | — | 7 |
| Previously useful descriptions lost | — | 5 |
| Mixed-integrity descriptions | 0 | 4 tentative |

The current vocabulary's `dipping` is mapped to DIP_RISE only for this coarse
comparison, not redefined in production. Current's six other named outputs include
two rises against manually labelled valleys and four labels on manually unclear
paths; unclear review labels do not prove the current label acoustically wrong.
All 20 proposed named outputs agree with this review, but the labels and prototype
are not independent and there is no held-out accuracy claim.

The seven gains are `7e6b6fe9` 我/想/买, `0b194cf9` 想/买, `ee8a8b32` 买, and
`8faf1a90` 果. The five losses are `0b194cf9` 我, `ee8a8b32` 我, `8d252264` 一,
`4b9dbd2b` 一, and `a5acd04c` 果. Six candidates abstain after sensitivity checks;
three of the five useful losses are among these, while two shallow rises no longer
clear the candidate's short-endpoint movement threshold. Fixed endpoints therefore
solve one compression problem but introduce another.

The old 40357072 买 still has **three raw jumps >6 st, max 10.7347 st** and retained
contradictory branches. It remains unavailable. The physical 这 also remains
unavailable because the second falling fragment resets upward; it is not made a
clean fall by discarding that inconvenient evidence. Grouped 雨伞 is always
unavailable for a unit gesture grade.

**Integration not earned.** The failure is specifically endpoint-region stability
and support for small sustained excursions, rather than inability to compute a
valley. Keep the strict integrity type, old observed gesture, UI, and evidence
unchanged. No colors follow this gate.
