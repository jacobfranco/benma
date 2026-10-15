# Normalized learner graph

The previous graph already mapped an accepted selected timing interval onto the graph
width. Apparent variable starts/ends partly represented missing onset/tail evidence.
Its larger problem was the utterance-wide Y range: unrelated extreme points elsewhere
flattened the selected movement. Full-width/104 px proportions, axes and legend spacing
also consumed height and made shallow valleys harder to read.

`PitchShapePlot` now owns a separate display projection, `shapeDisplay`. Physical
`unitPitch`/`chunkPitch` retain original timestamps, semitone values, point ordering,
segment boundaries, ownership, accepted timing and recording-wide evidence domain.
The technical `PitchPlot` remains available and uses physical time.

## X contract

`position = (timestamp - accepted_start) / (accepted_end - accepted_start)`.
The **timing span** starts at 0 and ends at 1 for every timed unit, regardless of duration.
The graph has the same bounds at a given viewport. The first/last **measurement** is
not forced to 0/1: doing so would erase real missing onset/tail support. No extrapolated
point, endpoint line extension, interpolation or gap bridge is added. All original
segments remain distinct, even when neighboring segments touch.

A chunk uses one whole-span transform. For 这个 at 2.34–3.04 s, 这 ends at 0.55714
and 个 begins at 0.57143. All 20 measurements remain owned by 这. 个 contributes
zero selected measurements, so its interval stays empty. Constituents never receive
invented 50/50 widths. Existing grouped 雨伞 retains its one timing span.

## Y contract and calibration

Use the midpoint of local 10th/90th percentiles as the display center. The half-range
is the maximum of **3 st** and every retained point's distance from that center plus
**0.5 st** padding. This is a robust local center with an **all-point visibility guard**:
no outlier is clipped, winsorized or silently removed. A bad retained branch can still
widen the graph; that is preferable to hiding contradictory evidence.

The frozen corpus's median raw selected range is approximately 3.91 st. Compared
minimum visible ranges of 4/6/8 st would occupy approximately 97%/65%/49% of graph
height before extrema padding. Four st overfills many controls and provides more
noise magnification; eight flattens ordinary movement. Six is a bounded compromise
across all 53 units, not a value chosen only for 我. A 0.2 st movement occupies at
most 3.3% of height (about 3 px of the compact inner plot). Classification receives
none of these display coordinates or range choices.

## Layout decision

**Keep the graph beside text/playback.** The 100 px identity rail shows character,
reading and a 44 px exact-playback control. The graph takes the remaining width and
is 96 px high with consistent 4 px plotting insets. Two-character chunks can wrap
playback within the rail without shrinking its tap target or the graph's horizontal
bounds. Longer existing timing groups wrap text naturally. Missing pitch keeps
playback plus the established reliability message; no empty chart is shown.

Compared the actual previous export (header above shared-scale graph), the new
beside layout, and the new local-scale graph moved below its header in Chromium.
The beside layout saves about 76 px versus the normalized below-header alternative
for exaggerated 我 and gives the contour a less flattened aspect ratio. At 320 px
the graph is about 156 px wide, at 390 about 226, and at 412 about 248. These are
viewport effects, not duration effects. The larger learner detail uses the same
normalization and a 152 px plot. Technical evidence retains its separate real-time
sentence graph and Raw surface.

Reviewed 320/390/412 × 844 screenshots for normal/exaggerated 我, exaggerated 想/买,
这个, unavailable 个, grouped 雨伞, a clear rise and fall, learner details and technical
details. No horizontal page overflow or inaccessible New Attempt footer was found.
The selector remains visibly marked and keyboard operable; meaning does not rely
on color. The accent outline visible on a focused selector is browser focus, not a grade.

Both **Relative pitch** and **Time** axis titles are absent from compact and enlarged
learner shape graphs. Accessible graph text says it spans the selected spoken unit
and gaps mean missing pitch. A brief learner detail explanation distinguishes the
fitted display span from physical axes; no normalization jargon appears in the flow.
