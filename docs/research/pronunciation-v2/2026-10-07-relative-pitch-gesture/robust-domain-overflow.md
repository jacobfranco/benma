# Robust Mine display domain + truthful overflow — October 7, 2026

**Outcome B: ROBUST DOMAIN HELPS BUT OVERFLOW MAKES MINE MISLEADING. No production integration. GRAPH QUALITY STILL BLOCKS CHECKPOINT.**

The bounded three-MAD prototype makes the primary `40357072` take's ordinary U-like gestures materially more readable: **60.1% more pixels per semitone**, with the **−11.5547 st terminal drop explicitly continuing below the window**. Both clean takes have **zero overflow**. Nevertheless, the same policy replaces **all 24 selected points of 果 in `8d252264`** with duration indicators. Its 353–434 Hz run's existence and duration survive, but its entire 3.567-st internal gesture becomes unavailable in Mine. The low branch in 个 also puts 55.6% of that unit's selected support outside. A low utterance-wide burden does not establish useful per-unit gesture visibility.

This is a success for the truthfulness of the overflow primitive, **not** a safe general default domain. No tested policy meets all acceptance conditions. The narrower quantile policies preserve more local shape but do not adequately solve the primary scale problem; the 90% and 95% policies also put 55.6% of 个 outside in `8d252264`. No additional tuning or conditional fallback policy was added to force success.

## Review artifacts and scope

- [Focused local viewer](../../../../services/api/var/relative-pitch-gesture/overflow/viewer.html): all six recordings, four policies, actual current mobile X layout, robust projection, grouped 雨伞 zoom, every boundary crossing and outside run, per-unit burden, full selected detail and raw tracker points, protected low-F0, synthetic 70 Hz, continuous jump and coherent sweep.
- [Primary group zoom](../../../../services/api/var/relative-pitch-gesture/overflow/figures/40357072-zoom.png) and [all screenshots](../../../../services/api/var/relative-pitch-gesture/overflow/figures/).
- [Numeric replay](overflow-replay.json): domains, all selected source points, X positions, derived paths, events, durations, per-unit statistics, controls and input hashes.
- Reusable sources: `benchmark/pronunciation_v2/robust_domain_overflow.py`, `robust_domain_overflow_report.py`, `robust_domain_overflow_viewer.html`, `robust_domain_overflow_browser_check.cjs`, `test_robust_domain_overflow.py`.

All data came from the preceding passes' frozen six-take analyses/tracks and 23 control snapshots. No database write, provider call, tracker/VAD run, acoustic decision, new timing, or relative-centering experiment. The actual TypeScript `normalizedMine` and `normalizedGeometry` functions are executed by the existing offline adapter. All 961 owned selected X coordinates match the previous replay. `d47274bc` has no accepted timing and remains empty. The earlier whole-unit and fragment relative projections remain unintegrated and are **not combined with this window**.

The viewer uses a 128 px plot interior and 96 px cells for current/prototype comparisons; narrow viewports scroll. The group zoom enlarges X only and preserves the utterance Y-domain. Full selected ordinates expose small wiggles that current smoothed/simplified Mine omits; they are not a new cleanup or rejection policy. Screenshots were inspected for all six takes, primary policies and the group zoom. This is a geometry/visual assessment, not a listening study, user-comprehension study, or acoustic truth claim.

## 1. Exact current domain trace and insertion point

The existing chain is documented in [projection.md](projection.md); it remains unchanged:

1. `contours.py:display_contour` derives a **whole-recording median retained-Hz baseline**, computes `12 log2(hz / baseline)`, applies the existing within-segment median-of-three display smoothing, and rounds display ordinates to four decimals. Transport baseline is rounded to three decimals.
2. Its bounds are `low = min(-3, min(display) - 1)` and `high = max(3, max(display) + 1)`: one semitone padding, at least the existing −3…+3 domain.
3. `tone_graph.py:sentence_pitch_evidence` splits at accepted timing boundaries before existing ≤0.15-st simplification. `mine` inherits recording-wide bounds. `filtered` reconstructs **unsmoothed selected measurements** using the transported recording baseline. `raw` retains tracker/selected Hz and source metadata.
4. `sentenceToneGraph.ts:normalizedMine` changes X only: one cell per identity, 0.12 inset, accepted whole-group spans, and existing 0.2-cell pause spacers. It does not center or normalize Y per unit. Half-open ownership does not manufacture a boundary inside 雨伞.
5. `PitchPlot` takes the union of supplied display bounds and the whole supplied contour's extrema ±1 st. This can include evidence outside Mine's accepted timing cells. Current Mine therefore has one **shared utterance domain**.
6. With drawable height `H=128`, `y = H - (s-low)/max(2,high-low) * H`, followed by the 4 px inset. `x = position/extent * drawableWidth + 4`. Projection remains linear in semitones; all units use the same slope.

The smallest potential integration point is a pure Mine-only presentation adapter immediately before `PitchPlot`: derive a window from the owned full selected samples and pass explicit clipped geometry plus continuation marks. Its explicit domain must bypass `PitchPlot`'s union with old global bounds. It must not enter `filtered`, `raw`, acoustic tracks, eligibility or classification. **No integration was made.**

## 2. Four bounded candidates, unchanged representation

All candidates consume **all Mine-owned selected sample ordinates**, using the same transported recording baseline as More Detail. No local recentering, reference tone, Hz cutoff, simplified-vertex weighting, per-unit fit, or nonlinear compression.

| Candidate | Definition before existing padding/minimum |
| --- | --- |
| q90 | Interpolated 5th…95th percentiles |
| q95 | Interpolated 2.5th…97.5th percentiles |
| q97.5 | Interpolated 1.25th…98.75th percentiles |
| mad3 | `m ± 3 × 1.4826 × median(abs(s-m))`, with `m=median(s)`, intersected with measured min/max |

Each then uses `low=min(-3, lower-1)` and `high=max(3, upper+1)`. MAD's min/max intersection prevents a robust spread estimate from unnecessarily zooming farther out than full evidence. The 1.4826 factor is a conventional spread normalization, **not an acoustic normality assumption**. Empty projection uses [−3,+3] without inventing evidence. A 0.5-st contour cannot fill the graph. Inside any candidate, 2 st occupies exactly half the distance of 4 st.

**No policy chosen for production.** `mad3` is the strongest diagnostic candidate, selected for the detailed comparison below, and is rejected at the generalization gate.

## 3. Overflow geometry and burden definition

For a consecutive selected pair `(t0,x0,s0)` → `(t1,x1,s1)` crossing boundary `B`:

```
alpha = (B-s0)/(s1-s0)
t_cross = t0 + alpha*(t1-t0)
x_cross = x0 + alpha*(x1-x0)
```

The visible measured line ends or resumes **at that intersection**, never at the first outside sample's X. A segment crossing both boundaries renders its in-window middle. Multi-sample outside evidence becomes one outward chevron plus a dashed boundary duration rail, with an end tick. The rail is explicitly labeled as continuation beyond the window, **not a measured horizontal plateau**. A fully outside fragment still gets its own rail and arrow. Hover exposes exact selected source indices and times. No repeated arrow per sample.

Fragments are maximal consecutive selected source indices with `0 < delta_time <= 1.5 × saved cadence`, inside an accepted timing owner. All six saved tracks use 10 ms cadence; observed 9.9/10.1 ms jitter remains continuous. Missing/rejected frames, existing segment boundaries and unit boundaries break both lines and rails. No split depends on pitch magnitude. The terminal primary jump stays within the same continuous source fragment.

**Duration convention:** interpolate linearly between consecutive selected timestamps. Add half-hop constant support at each fragment endpoint, clipped to its accepted timing span, solely for burden and the dashed duration symbol. No contour line is extended into endpoint support. Missing slots remain unsupported. Event tables give actual crossing/endpoint times separately from support duration; this avoids confusing 21 samples' 200 ms endpoint span with **210 ms selected support**. Singletons still count as one frame of support where timing permits.

```
point burden = outside selected points / all Mine-owned selected points
support burden = outside selected-support duration / total selected-support duration
```

Both are diagnostics, not confidence or eligibility. Per-unit burden is also reported: a whole high-register unit can vanish from a gesture view even when sentence-wide burden appears tolerable.

## 4. Primary 40357072: every candidate

Phrase **我想买五把雨伞**. Current domain **−14.2543…+5.2661 st**, 252 selected owned points. Prototype preserves all 252 source points.

| Policy | Visible domain (st) | Inside / outside | Events | Outside support | Units | Gesture readability / terminal drop |
| --- | --- | --- | --- | --- | --- | --- |
| q90 | -10.015…4.651 | 241 / 11 | 4 | 106.14 ms | 买, 雨伞 | Partial scale relief (33.1% more px/st); continuous terminal drop remains fully in range and dominates group height. |
| q95 | -12.611…5.154 | 247 / 5 | 2 | 50.00 ms | 买, 雨伞 | Only 9.9% more px/st; broad U shapes remain compressed; full terminal drop remains in range. |
| q97.5 | -14.106…5.226 | 252 / 0 | 0 | 0.00 ms | none | Only 1.0% more px/st; effectively original compression; full terminal drop remains in range. |
| mad3 | -6.884…5.309 | 236 / 16 | 6 | 153.34 ms | 买, 雨伞 | Material improvement (60.1% more px/st); terminal drop explicitly exits lower boundary. |

For `mad3`, the 128 px interior gives **10.50 px/st**, versus **6.56 px/st** current. Measured 我's 3.243-st motion occupies **34.04 px instead of 21.26**; 想 **31.76 instead of 19.84**; 五 **30.56 instead of 19.09**. This is visibly material, without normalizing every character to the same amplitude.

### Grouped 雨伞 zoom

One accepted **3.56–4.87 s** timing group, with the same **54 / 4 / 21** selected-point fragments. No individual 雨/伞 timing or grades. The first fragment's **2.483-st motion** grows from **16.28 to 26.07 px**. The disconnected four-point low island remains explicit as a **40 ms** lower-boundary continuation, not deleted or bridged.

The final fragment still contains its complete **11.724-st measured excursion**. Its **−11.5547-st step at 4.7047→4.7147 s**, from **+2.5418 to −9.0129 st**, crosses the `mad3` lower boundary **−6.883588 st** at **4.712857204 s**. The line reaches the exact interpolated X **6.668876854 cells**, then an outward chevron and rail represent **36.8428 ms** of outside support, through 4.7497 s (last measured point 4.7447 s plus half hop). All four terminal measurements remain unchanged, source indices **468–471**. Exact magnitude remains visible in full detail.

Group total: **71 inside / 8 outside**, **2 events / 76.8428 ms**, **9.73% support burden**. The visually separated events remain separated by the original gap. The zoom communicates both ordinary U-like motion and the terminal plunge. It does not assert that the plunge is acoustically correct.

## 5. All six takes: strongest diagnostic candidate (`mad3`)

| Take | Current domain (st) | Robust domain (st) | Inside points | Events / outside support | Support burden | Units affected | Assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40357072 | -14.254…5.266 | -6.884…5.309 | 236/252 (93.65%) | 6 / 153.34 ms | 6.09% | 买, 雨伞 | Primary ordinary gestures materially clearer; terminal continuation explicit. |
| 8d252264 | -16.139…23.287 | -7.071…7.028 | 153/188 (81.38%) | 7 / 351.82 ms | 18.76% | 要, 个, 果 | Other gestures clearer, but 果 has no visible pitch shape; 个 majority outside. Reject. |
| d47274bc | -14.022…10.300 | -3.000…3.000 | 0 (N/A) | 0 / 0.00 ms | 0.00% | none | No accepted timing: both Mine views empty. |
| 4b9dbd2b | -3.678…7.291 | -3.708…7.301 | 224/224 (100.00%) | 0 / 0.00 ms | 0.00% | none | Effectively unchanged; no contour overflow. |
| 8faf1a90 | -4.580…6.220 | -4.819…5.685 | 161/161 (100.00%) | 0 / 0.00 ms | 0.00% | none | Effectively unchanged; no contour overflow. |
| a5acd04c | -4.617…21.468 | -4.631…8.743 | 131/136 (96.32%) | 2 / 50.00 ms | 3.70% | 有, 个 | Clearer; both short high islands explicit; ordinary broad 苹 motion remains complete. |

**8d252264 safety:** none of the 24 selected 353–434 Hz points is deleted. The existing rejected frame separates the high branch into **3 points / 30 ms** and **21 points / 210 ms**, rendered as distinct duration rails. The 10 ms missing slot remains a gap. The sustained run cannot look like a one-frame anomaly. However, **100% of 果's selected support** is outside; its measured internal rise/shape disappears from Mine. **个 loses 5/9 points and 55.6% support**, and 要 loses 6/27 points and 23.3% support. This is the decisive rejection, despite correct overflow geometry.

**a5acd04c safety:** **two events**, 有 **30 ms / 3 points** and 个 **20 ms / 2 points**. They represent 9.5% and 12.8% of those units' selected support, respectively, not half a character. Total **3.70%** support is outside. The graph is clearer but does not silently present these islands as resolved: the upper continuations remain visible. 苹's coherent **8.472-st** movement remains completely in range. This take passes the local visualization check; it cannot override `8d252264`.

**Clean controls:** `4b9dbd2b` and `8faf1a90` have zero outside points, events or duration under MAD. Their pixel scales differ by **−0.36% and +2.82%**, respectively. Small bound/vertex differences reflect full selected measurements versus current smoothed/simplified Mine. No new pitch processing was applied. q90 creates one unnecessary **10.80 ms** upper overflow in clean `8faf1a90`; q95/q97.5 create none in either clean take.

### Complete four-policy physical matrix

| Take | Policy | Domain (st) | Inside / outside | Events | Outside support | Support burden | Timing units affected |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 40357072 | q90 | -10.015…4.651 | 241 / 11 | 4 | 106.14 ms | 4.21% | 买, 雨伞 |
| 40357072 | q95 | -12.611…5.154 | 247 / 5 | 2 | 50.00 ms | 1.98% | 买, 雨伞 |
| 40357072 | q97.5 | -14.106…5.226 | 252 / 0 | 0 | 0.00 ms | 0.00% | none |
| 40357072 | mad3 | -6.884…5.309 | 236 / 16 | 6 | 153.34 ms | 6.09% | 买, 雨伞 |
| 8d252264 | q90 | -9.128…21.279 | 177 / 11 | 4 | 110.51 ms | 5.89% | 要, 个, 果 |
| 8d252264 | q95 | -12.443…22.144 | 181 / 7 | 3 | 67.08 ms | 3.58% | 个, 果 |
| 8d252264 | q97.5 | -15.794…22.805 | 188 / 0 | 0 | 0.00 ms | 0.00% | none |
| 8d252264 | mad3 | -7.071…7.028 | 153 / 35 | 7 | 351.82 ms | 18.76% | 要, 个, 果 |
| d47274bc | q90 | -3.000…3.000 | 0 / 0 | 0 | 0.00 ms | 0.00% | none |
| d47274bc | q95 | -3.000…3.000 | 0 / 0 | 0 | 0.00 ms | 0.00% | none |
| d47274bc | q97.5 | -3.000…3.000 | 0 / 0 | 0 | 0.00 ms | 0.00% | none |
| d47274bc | mad3 | -3.000…3.000 | 0 / 0 | 0 | 0.00 ms | 0.00% | none |
| 4b9dbd2b | q90 | -3.194…6.592 | 224 / 0 | 0 | 0.00 ms | 0.00% | none |
| 4b9dbd2b | q95 | -3.485…6.982 | 224 / 0 | 0 | 0.00 ms | 0.00% | none |
| 4b9dbd2b | q97.5 | -3.634…7.139 | 224 / 0 | 0 | 0.00 ms | 0.00% | none |
| 4b9dbd2b | mad3 | -3.708…7.301 | 224 / 0 | 0 | 0.00 ms | 0.00% | none |
| 8faf1a90 | q90 | -4.201…5.002 | 160 / 1 | 1 | 10.80 ms | 0.67% | 苹 |
| 8faf1a90 | q95 | -4.373…5.559 | 161 / 0 | 0 | 0.00 ms | 0.00% | none |
| 8faf1a90 | q97.5 | -4.424…5.641 | 161 / 0 | 0 | 0.00 ms | 0.00% | none |
| 8faf1a90 | mad3 | -4.819…5.685 | 161 / 0 | 0 | 0.00 ms | 0.00% | none |
| a5acd04c | q90 | -4.294…6.918 | 131 / 5 | 2 | 50.00 ms | 3.70% | 有, 个 |
| a5acd04c | q95 | -4.539…11.217 | 133 / 3 | 1 | 30.00 ms | 2.22% | 有 |
| a5acd04c | q97.5 | -4.590…20.400 | 135 / 1 | 1 | 5.98 ms | 0.44% | 有 |
| a5acd04c | mad3 | -4.631…8.743 | 131 / 5 | 2 | 50.00 ms | 3.70% | 有, 个 |

No empty-timing take is counted as a scale-quality success. The numeric replay and viewer include every accepted unit and every event's separate duration and source indices, not only sentence aggregates.

## 6. Protected low register and large movement

All **617 protected samples**, **11 sub-70-Hz entries**, and **2,827 selected samples across 23 frozen controls** remain in the source arrays. Every selected Hz, timestamp and source index is unchanged. The **54.610 Hz** measurement at **2.5124 s in 7787300e** remains selected and explicitly represented. Its recording-relative ordinate is **−9.756690 st**: it is outside q90 and MAD, inside q95/q97.5. Overflow is not rejection or uncertainty. This legitimate low dip illustrates the cost of putting valid shape outside the window.

| Policy | Outside / 2,827 points | Outside support | Outside / 617 protected | Outside / 11 sub-70 entries |
| --- | --- | --- | --- | --- |
| q90 | 84 | 821.89 ms (2.91%) | 5 | 3 |
| q95 | 25 | 245.28 ms (0.87%) | 0 | 0 |
| q97.5 | 4 | 29.33 ms (0.10%) | 0 | 0 |
| mad3 | 99 | 980.38 ms (3.47%) | 11 | 10 |

These control units cover full recordings for stress replay; they are **explicit control fixtures**, not newly inferred character timing. MAD's worst control support burdens are `native_24k` **13.70%**, `7787300e` **11.54%**, and `f5dc0cc1` **10.71%**. The explicit low control retains all 189 selected points, with 22 outside MAD. A tiny global percentage cannot certify all legitimate local gestures.

The saved synthetic-70 fixture's two selected **70.254 Hz** frames survive. A deterministic coherent **70 Hz** shape has **zero overflow in every policy**; the same shape at 54.610, 55, 60, 350, 380 and 440 Hz has the same domain and no overflow. Multiplying all Hz and the recording median baseline by the same factor leaves `12 log2(hz/baseline)` invariant. There is no “too low” or “too high” absolute threshold and no special low-F0 exception.

The existing deterministic **55→220 Hz sweep** has **61 consecutive samples / 24 st**. MAD retains the complete motion within **−13…+13 st**; q95/q97.5 also keep all samples inside. q90's **−11.8…+11.8 st** window truthfully overflows **two endpoint samples in two events, 15 ms support total**, with exact intersections. The full selected 24-st sweep remains available. The existing continuous **100→105→210→220 Hz** control stays one segment, keeps its **12-st internal jump / 13.650-st total movement**, and has no overflow under any candidate.

Product tradeoff: a linear window can communicate that a gesture exceeds its range, but cannot convey that outside portion's amplitude or internal curvature. It must never imply the edge is the measured value. More Detail supplies exact amplitude. For a small tail this tradeoff works in the primary take; for an entirely outside unit it defeats Mine's gesture purpose. No grading or confidence can be improved because the plot looks cleaner.

## 7. Preservation, tests and implementation gate

**31 focused checks pass**: 30 new research checks plus the existing acoustic independence replay over all 30 accepted physical units. They cover ordinary geometry, exact upward/downward crossings, both boundaries in one segment, correct reentry (including a sample exactly on the boundary), one coherent event per outside run, duration rails, missing/rejected-source and cadence gaps, unchanged extreme evidence, linear amplitude, minimum span, group identity, no timing, reference independence, clean controls, register copies, protected samples, large coherent movement, saved evidence hashes and the decisive whole-unit overflow failure.

The actual mobile adapter changes target, characters, pinyin, lexical tone and expected surface tone with timing held fixed and checks identical pixel geometry. The robust domain accepts only numeric selected ordinates; direct overflow tests change unit labels/reference metadata and produce identical geometry. Current X placement is unchanged for **961/961** selected owned points.

**More Detail and Raw:** no source code or saved payload changes. All 30 snapshot hashes (six tracks, saved analyses and 23 controls) verify unchanged; the replay compares selected ordinates exactly with the existing filtered payload. Full detail remains on real recording time and full absolute recording-baseline semitone scale. The viewer also exposes exact selected Hz. Raw plots exact tracker samples independently of selected display. No robust bounds propagate into either.

**Eligibility/classification/confidence/comparison:** unchanged; the focused backend independence check passes. Source arrays and timing/group spans are never mutated. Overflow is only a display-window fact. Grading remains disabled.

**Production files changed: none.** All **206** pre-pass mobile/backend source and test hashes match. Only five new research source/test/viewer files, this report, numeric replay, and README were added/updated. No development-current-state rewrite is appropriate because no policy earned production integration. The large pre-existing uncommitted stack is preserved.

Browser validation checks **six takes × four policies**, inside counts, event counts, group crossing, no-timing emptiness, 30/210 ms high-run durations, provenance hover and narrow-screen scrolling. Nine full screenshots and the group zoom were captured. The first sandboxed Chromium pipe could not start; the approved local-only rerun passed with HTTP/HTTPS blocked. No remote assets, service writes, installation or deployment. This is research HTML validation, not an iOS/Android physical re-smoke or user-comprehension test.

Reproduce with existing local dependencies and snapshots:

```sh
PYTHONPATH=. services/api/.venv/bin/python -m benchmark.pronunciation_v2.robust_domain_overflow_report
PYTHONPATH=. services/api/.venv/bin/pytest -q benchmark/pronunciation_v2/test_robust_domain_overflow.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py::test_presentation_cannot_change_existing_eligibility_or_observation
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/robust_domain_overflow.py benchmark/pronunciation_v2/robust_domain_overflow_report.py benchmark/pronunciation_v2/test_robust_domain_overflow.py
services/api/.venv/bin/ruff format --check benchmark/pronunciation_v2/robust_domain_overflow.py benchmark/pronunciation_v2/robust_domain_overflow_report.py benchmark/pronunciation_v2/test_robust_domain_overflow.py
node --check benchmark/pronunciation_v2/robust_domain_overflow_browser_check.cjs
node benchmark/pronunciation_v2/robust_domain_overflow_browser_check.cjs
git diff --check
```

No full mobile/backend suite was rerun because production remained byte-for-byte unchanged. Final Git state is saved locally at `services/api/var/relative-pitch-gesture/overflow/final-git-state.txt`; its tracked diff is the pre-existing stack, while this pass's research files remain untracked.

## 8. Final seven decisions

| Decision | Selected outcome | Basis |
| --- | --- | --- |
| 1 — Mine semantics | **ROBUST DISPLAY WINDOW WITH EXPLICIT OVERFLOW IS TRUTHFUL** | Correct crossings and labeled duration continuations represent evidence without clamping its value. This does not certify usefulness for every unit. |
| 2 — 40357072 | **U-SHAPE READABILITY MATERIALLY IMPROVED WHILE TERMINAL DROP REMAINS EXPLICIT** | MAD prototype: +60.1% px/st, exact lower-edge crossing and sustained terminal continuation. |
| 3 — clean controls | **CLEAN CONTOURS REMAIN EFFECTIVELY UNCHANGED** | MAD: zero overflow on both clean physical takes, near-identical scale. |
| 4 — register / large movement | **DISPLAY POLICY HIDES VALID MOVEMENT** | Although existence/duration remain truthful, MAD removes the entire high 果 unit's internal gesture from Mine and outside valid low dips cannot show their shape. No source evidence is hidden from detail or deleted. |
| 5 — production | **NO SAFE DISPLAY POLICY** | None of these four policies meets the full acceptance gate. Outcome B, production unchanged. |
| 6 — checkpoint | **GRAPH QUALITY STILL BLOCKS CHECKPOINT** | No four-case physical re-smoke yet. |
| 7 — next step | **NAME EXACTLY ONE REMAINING PRODUCT-VISUALIZATION ISSUE** | An entire sustained timing unit can lie outside a shared readable Mine window, leaving duration but no readable within-unit gesture. |

**One next step:** resolve how Mine preserves a readable gesture for a sustained timing unit that lies entirely outside its shared display window.

No commit. No push. No deployment. No further acoustic model research recommended.
