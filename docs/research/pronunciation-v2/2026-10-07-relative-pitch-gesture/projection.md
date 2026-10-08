# Geometry trace and projection contract

## Current path, verified against the working tree

1. `pronunciation/pitch_evidence.py:build_pitch_track` calls the existing `contours.py:display_contour` selection and creates the frozen `UtterancePitchTrack`. Each frame retains raw tracker Hz, energy-gated Hz, analyzer-selected Hz, final selected Hz, periodicity, candidates, exclusion reasons and time. This pass reads saved tracks; it does not rerun selection for the six captures.
2. `display_contour` computes a whole-recording median retained-Hz baseline, then `12 log2(selected_hz / baseline)`. Within each contiguous selected region, existing median-of-three smoothing changes interior display values; endpoints stay measured. Values are rounded to four decimals. Missing/rejected frames and >45 ms gaps split regions. Transport baseline is rounded. Display bounds are `min(-3,min(display)-1)` and `max(3,max(display)+1)`.
3. `display_from_track` reconstructs that saved smoothed display without changing frozen evidence. `project_pitch` stores accepted half-open `[start,end)` timing and exact original frame indices. Eligibility and observed gestures consume acoustic evidence separately.
4. `tone_graph.py:sentence_pitch_evidence` splits at character/group boundaries **before** `simplify_display` (≤0.15 st vertex error). `mine` carries the smoothed/simplified recording-baseline values and global bounds. `filtered` contains the unsmoothed selected measured Hz converted using that same transported recording baseline. Its actual vertex extrema can extend beyond the smoothed supplied bounds. `raw` carries native tracker Hz, energy-gated and selected values, source index, retention and exclusions.
5. `speech/sentenceToneGraph.ts:normalizedMine` changes **X only**. Timed characters receive width-one cells with 0.12 inset; accepted grouped spans occupy their member cells as one acoustic region. Mapping is affine over the whole timed span, including its unvoiced margins. ≥0.30 s accepted adjacent-character pauses add width 0.2. Half-open ownership uses the later start, then later perceived index for tolerated tiny overlaps. Untimed identity cells do not authorize acoustic lines. Synthetic alignment yields no Mine line.
6. `SentenceToneGraph.tsx` passes `graph.mine` plus `normalizedMine(data)` to `PitchPlot`, or `graph.filtered` with real time in More Detail. The default height is 136 px, with a drawable 128 px interior. `PitchPlot` takes the union of supplied bounds and the **whole supplied contour's** extrema ±1 st. Those can include points outside accepted cells. Default Mine therefore preserves absolute cross-unit register relationships even though its axis is in recording-baseline semitones rather than Hz.
7. `normalizedGeometry` computes `x = position/extent * width`, `y = height - (value-low)/max(2,high-low)*height`. `ContourLines` draws only consecutive points **within each segment**; singletons remain dots. The existing timed mapping already separates units. More Detail uses elapsed-time `contourGeometry`; Raw uses points only and its own domain. Opening Raw does not change Mine's scale.

Files above are under `services/api/src/benma_api/` and `apps/mobile/src/`. No part of that production chain was edited. `relative_pitch_geometry.cjs` transpiles and executes the actual mobile `normalizedMine`, `rawPitch` and `normalizedGeometry` functions to avoid a hand-drawn imitation of their cell attribution.

## Prototype

For accepted unit `u`, let `I_u` be its already selected, owned source indices:

```text
s_i = 12 * log2(selected_hz_i / 1 Hz)
c_u = median({s_i : i in I_u})
r_i = s_i - c_u
```

Median of an even count is the arithmetic mean of its two middle **semitone** values. Its reported Hz equivalent is therefore their geometric mean. Median is over all selected frames in the accepted unit, never simplified vertices, candidate frequencies, per-run medians or reference shapes. Subtracting a recording baseline first gives the same result up to floating-point tolerance. `center_st_re_recording` is exported for comparison with current Mine; `center_semitones_re_1hz` records the exact computational center.

The pure helper accepts only `Sample(source_index,time,selected_hz)` and `Unit(key,start,end,timing_source)`. It emits new display objects; no selected Hz is overwritten. Keys are identifiers, never center inputs. Accepted timing comes from persisted `pitch_projection` objects with matching evidence IDs and exact frame-index lists; raw provider words from a failed alignment are not promoted into accepted timing.

**Full-resolution measured points are the proposed line.** Reusing the current smoothed Mine ordinates would preserve differences between smoothed points, but would fail the requested invariant against original selected semitones. No new smoothing, simplification, rounding, filling, rescaling, rejection or clipping is applied. This choice exposes some small measured wiggles already hidden by current median smoothing; it is stated explicitly in the viewer. A separate sensitivity calculation translates the old smoothed Mine vertices by the same centers. It leaves the decisive domains essentially unchanged (see physical comparison), so the outcome is not caused by bypassing smoothing.

The safe presentation insertion point, if accepted later, is a pure display helper using `tone_graph.raw` selected Hz/source indices plus accepted timing, returning fresh Mine segments and bounds before `PitchPlot`. `UtterancePitchTrack`, backend evidence, filtered detail, raw frames, eligibility and observed output must remain outside that transform. Simply shifting `xLayout` values would be insufficient: passing the old global `display` bounds to `PitchPlot` would retain the old domain. No integration was made.

## Timing, gaps and domain

A trustworthy timed character is one unit. A trustworthy word with untimed members is one unit. `40357072` 雨伞 is exactly **3.56–4.87 s**, with one center for all **79** selected owned frames. No internal character boundary is invented. `d47274bc` has zero accepted units and zero projected points, despite 214 selected acoustic frames. No fallback centers an entire untimed sentence into character cells.

Independent units always produce separate segments. A null frame, source-index discontinuity, or >45 ms gap breaks a line. Existing missing spans are never interpolated; pairwise differences can still be checked across gaps without drawing a connection. Within a group, consecutive evidence stays connected when the original evidence allows it. No cross-unit transition decoration is necessary.

One shared domain is computed from **all projected relative measured points**:

```text
low  = min(-3, min(relative_points) - 1)
high = max( 3, max(relative_points) + 1)
```

This is ordinary min/max with the existing 1 st padding and ±3 minimum range. No quantile, robust clipping, per-unit zoom or per-unit amplitude fit. An empty projection receives the harmless empty fallback domain [−3,+3]; this is not an improvement score or acoustic evidence. Full absolute measurements outside accepted timing remain in More Detail/Raw. They are not lost by the acoustic pipeline.

## Mathematical invariants

For any two retained points in one unit:

```text
r_b - r_a = (s_b - c_u) - (s_a - c_u) = s_b - s_a
```

Therefore ordering, ties, extrema, semitone range, first differences, rise/fall and discrete second differences (curvature) are preserved. Since time is unchanged, slopes per real second are preserved too. Cell X mapping remains the existing affine timing projection; it already changes horizontal visual speed relative to real time. A common Y-domain gives every unit the same pixels per semitone: a 2 st excursion remains one quarter of an 8 st excursion.

For a multiplicative register shift `hz'_i = 2^(k/12) hz_i`, `s'_i = s_i + k`; median is translation-equivariant, so `c'_u = c_u+k` and `r'_i=r_i`. Tests cover `k=±12`, actual pixel-normalized geometry, low/high registers, gaps, and the surviving internal 100→105→210→220 step. The last example **must** retain its 12 st internal jump.

The replay exhaustively checks every pair within each physical unit and each frozen control unit, including across missing spans. Maximum difference error is **0.0 st** on these saved inputs; general tests use 1e−12 tolerance, and register-copy replays use 1e−10. Source indices and timestamps are copied exactly; mobile cell mapping is verified not to drop, duplicate or add prototype points. Changing target, character identity, pinyin, lexical and expected surface tone while retaining the same accepted spans leaves real mobile geometry identical.
