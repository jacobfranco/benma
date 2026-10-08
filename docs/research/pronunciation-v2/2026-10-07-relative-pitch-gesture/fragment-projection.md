# Disconnected gesture fragment projection — October 7, 2026

**Outcome B: FRAGMENT PROJECTION HELPS BUT STILL DOES NOT MAKE MINE TRUSTWORTHY. Production unchanged. GRAPH QUALITY STILL BLOCKS CHECKPOINT.**

The gap-based model removes the isolated low fragment's register displacement in grouped 雨伞, but does not materially fix the primary acceptance take. 雨伞's final connected fragment still spans **11.724 st**, including an uninterrupted **−11.555 st step at 4.7047–4.7147 s**. 买 also retains a continuous **12.709 st** fragment. Both remain exposed. In contrast, large register mismatches in `8d252264` and `a5acd04c` occur across real missing evidence, so those graphs become much easier to inspect. Those partial successes do not satisfy outcome A.

## Review artifacts and scope

- [Local six-take fragment viewer](../../../../services/api/var/relative-pitch-gesture/fragments/viewer.html): opens on **grouped 雨伞**, with all selected points, original time/source indices, three fragments, shaded existing gaps and exact gap durations; current Mine / proposed Mine, shared domains, absolute selected Hz, More Detail equivalent and Raw; protected low-F0 and continuous-jump controls.
- [Primary group zoom screenshot](../../../../services/api/var/relative-pitch-gesture/fragments/figures/40357072-zoom.png)
- [Six full screenshots](../../../../services/api/var/relative-pitch-gesture/fragments/figures/)
- [Fragment replay](fragment-replay.json): all accepted units, all fragment centers/ranges/indices/points, cadence evidence, controls, exact horizontal-preservation checks and input hashes.

Source is `benchmark/pronunciation_v2/relative_pitch_fragments.py`, `relative_pitch_fragments_report.py`, `relative_pitch_fragments_viewer.html`, `relative_pitch_fragments_browser_check.cjs`, and `test_relative_pitch_fragments.py`. The helper reuses the preceding pass's validated timing ownership; the report reuses its saved rows, acoustic snapshots and actual mobile geometry adapter. No database query, provider request, re-extraction, tracker/VAD evaluation, outlier rule, octave selection or new recording was needed. No previous artifact was regenerated or replaced. Viewer outputs, screenshots and logs stay under ignored `services/api/var/`.

All six plots and the detailed 雨伞 zoom were visually inspected. This is a review of preserved measured geometry against the user's confirmed take, not an independent listening study or a claim that selected tracker values equal the true physical fundamental.

## 1. Exact fragment definition and cadence

A fragment is a maximal run of **already-selected** frames within one accepted timing unit. Its boundary is a break in source/time continuity, never a large F0 difference. Grouped and character-timed spans use exactly the same acoustic logic.

The frozen production track reports **10 ms** cadence in all six takes. Actual successive extraction timestamps span approximately **9.9–10.1 ms** in `a5acd04c`; the others differ from 10 ms only by binary floating-point roundoff. The existing `interpretation_eligibility` run logic in `services/api/src/benma_api/pronunciation/pitch_evidence.py` uses `1.5 × hop` to detect lost cadence. This prototype uses that existing guard and exact source continuity:

```text
same fragment iff:
  same accepted timing owner
  both frames already selected
  next.source_index == previous.source_index + 1
  0 < next.time - previous.time <= 1.5 * track.frame_cadence_seconds

for these takes: maximum contiguous time step = 0.015 s
```

A rejected/missing source frame always breaks the run—even one missing 10 ms frame. A source-index discontinuity or a time step >15 ms also breaks it. Accepted unit boundaries delimit different display owners; this does not invent a finer timing unit. Half-open `[start,end)` attribution and original X positions are unchanged.

The half-hop margin tolerates the observed 0.1 ms timestamp quantization without treating a missing two-slot time step (20 ms) as contiguous. It is not a large silence threshold. No threshold sweep was warranted: all observed full-track steps are well within the existing 15 ms guard. A focused test covers the observed 9.9/10.1 ms alternation and a missing 20 ms step. Fragment membership is identical under arbitrary replacement of pitch magnitudes, including gigantic jumps.

The prior research helper's 45 ms display guard is looser than this cadence rule. The new helper reuses its ownership/absolute values, then applies the stricter existing cadence continuity rule. It explicitly limits this prototype to cadence ≤30 ms so that the old 45 ms guard cannot silently over-split a slower future tracker. No production API behavior is changed.

## 2. Primary grouped 雨伞 forensics

File: `40357072fc994a0ab052752ca119b2e6.wav`; phrase: 我想买五把雨伞. Five timed characters and **one grouped 雨伞 span, 3.56–4.87 s**. The group owns **79 selected points**, in exactly **three connected fragments**. It retains one horizontal span across the existing two identity cells; neither 雨 nor 伞 receives an invented acoustic start/end.

Semitone ranges and centers in the table are relative to the original recording baseline, so they show the original cross-fragment register differences. All computations use unrounded `12 log2(Hz)` before constant subtraction. Endpoint duration is last-minus-first sample time; support duration adds one observed 10 ms frame interval. Gap duration is last-selected to next-selected; missing support subtracts one frame interval, not an invented phonetic boundary.

| Fragment / source indices | Selected endpoints (s) | Points | Endpoint / support duration | Absolute Hz range | Original st range | Median-equivalent Hz / original st | Within-fragment excursion | Following gap / missing support |
| --- | --- | ---: | --- | --- | --- | --- | ---: | --- |
| F1 / 353–406 | 3.5647–4.0947 | 54 | 530 / 540 ms | 101.570…117.236 | -1.555…0.928 | 105.496 / -0.899 | 2.483 st | 190 / 180 ms (18 source frames) |
| F2 / 425–428 | 4.2847–4.3147 | 4 | 30 / 40 ms | 51.676…51.978 | -13.254…-13.153 | 51.759 / -13.227 | 0.101 st | 230 / 220 ms (22 source frames) |
| F3 / 451–471 | 4.5447–4.7447 | 21 | 200 / 210 ms | 65.836…129.587 | -9.062…2.662 | 123.561 / 1.838 | 11.724 st | none |

F2's median is **12.328 st below F1**. F3's median is **15.064 st above F2**, or **2.736 st above F1**. The combined 15.916-st group span is exactly `12 log2(129.587 / 51.676)`: the minimum lies in F2 and maximum in F3. Thus part of the large span is genuinely a disconnected-register mismatch. **It is not all disconnected:** F3 itself includes both ~129 Hz and ~66 Hz with continuous selected frames.

After fragment centering:

| Fragment | Relative range | Measured interpretation, without lexical judgment |
| --- | --- | --- |
| F1 | −0.657…+1.827 st | A modest dip/recovery and rise remain visible. |
| F2 | −0.028…+0.073 st | A nearly level four-point fragment; no fabricated U shape. |
| F3 | −10.899…+0.824 st | Rise followed by the same abrupt terminal drop; not a coherent recovered U gesture. |

Across all three independently centered fragments, the group covers **−10.899…+1.827 st**, a **12.726-st** shared-coordinate range. The maximum individual fragment excursion remains 11.724 st. Do not confuse those two ranges. The primary take's utterance domain changes from **−14.2543…+5.2661** (19.5204 st) to **−11.8993…+4.7226** (16.6219 st), a **14.8%** span reduction. Its U gestures get about **17.4%** more pixels per semitone, but the large connected drops remain visually dominant. The final 雨伞 drop still sets the lower endpoint of the whole graph domain.

**Grouped 雨伞 remains misleading as a simple picture of the intended gesture.** The plotted evidence itself is preserved honestly; centering has not resolved its disputed continuous shape. This is why the result is B, not A.

### 买 in the same take

Four evidence fragments have **12, 2, 1 and 26 points**, with endpoint gaps **20, 30 and 20 ms** (one, two and one missing source frames). Centers are **105.455, 55.729, 53.019 and 99.903 Hz**. The isolated low fragments now center near zero, but the last 26-point run at **2.1347–2.3847 s** still spans **12.709 st**. It contains the continuous **+9.143 st step at 2.1647–2.1747** and **−10.568 st step at 2.3747–2.3847**. Neither step is a fragment boundary. Together with 雨伞's terminal drop, these are the three previously reviewed large continuous transitions left in the primary take.

## 3. Transform and invariants

For each existing fragment F:

```text
s_i = 12 * log2(selected_hz_i)
c_F = median(s_i for i in F)
r_i = s_i - c_F
```

This is one constant vertical translation. No frequency is replaced, repaired or reselected. No frame is removed, no gap filled, no amplitude scaled and no slope changed. An even-count center is the mean of the middle two semitone values (their geometric-mean equivalent Hz).

For any a,b in the **same fragment**, `(r_b-r_a) = (s_b-s_a)`. Rise/fall, ties, minima/maxima, U shapes, excursion amplitude, first differences and second differences/curvature are preserved. Original time and source order remain exact, so real-time slopes are unchanged too. The actual mobile `normalizedMine` helper gives every one of the **961** projected points exactly the same X coordinate as the previous whole-unit prototype. Fragments do not create new timing cells.

The pairwise invariant intentionally does **not** hold between independently centered fragments. Measured endpoint registers across a gap remain known from the absolute evidence; what is absent is the trajectory between them. The prototype chooses to omit that cross-gap register relationship in Mine. A real gap alone does not make the relationship unmeasured or certify a coherent pronunciation.

Every fragment is its own polyline/dot sequence, with **no connector** across a gap or timing-unit boundary. One shared utterance domain is ordinary `min(-3,min(r)-1)` to `max(3,max(r)+1)`. A 2 st excursion remains one quarter of an 8 st excursion. No percentile clipping, individual zoom-to-height or domain outlier detector exists.

The viewer uses full-resolution selected points to satisfy the exact measured-pair invariant; current Mine retains its existing smoothing/simplification. Compared with the preceding prototype, only the independent centers change, because selected-point geometry/X positions remain identical. Maximum exhaustive within-fragment pairwise error on the six takes is **0.0 st**. Register copies, including separate ±12 st offsets on different existing fragments, preserve membership and relative geometry.

## 4. Six-take comparison

| Take | Accepted units / fragments | Selected / projected points | Current Mine domain | Prior whole-unit domain | Fragment domain | Span change vs current | Finding |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `40357072` | 6 / 12 | 253 / 252 | -14.254…5.266 | -13.584…5.303 | -11.899…4.723 | -14.8% | Primary still fails: continuous 买 and 雨伞 excursions remain. |
| `8d252264` | 6 / 13 | 189 / 188 | -16.139…23.287 | -10.021…17.133 | -3.267…3.689 | -82.4% | Substantial scale improvement; fragmented units are not complete gestures. |
| `d47274bc` | 0 / 0 | 214 / 0 | empty | empty | empty | not applicable | No accepted timing; no Mine evidence created. |
| `4b9dbd2b` | 6 / 6 | 224 / 224 | -3.678…7.291 | -4.776…5.438 | -4.776…5.438 | -6.9% | Same as whole-unit prototype; all units have one fragment. |
| `8faf1a90` | 6 / 6 | 164 / 161 | -4.580…6.220 | -5.277…4.250 | -5.277…4.250 | -11.8% | Same as whole-unit prototype; all units have one fragment. |
| `a5acd04c` | 6 / 8 | 140 / 136 | -4.617…21.468 | -6.331…22.895 | -6.331…5.593 | -54.3% | Substantial scale improvement; high islands were separated by real gaps. |

Totals: **30 accepted timing units, 45 acoustic fragments, 961 projected selected points**. Eight timing units have multiple fragments; 22 have one. No accepted unit is pitch-empty. `d47274bc` still has 214 selected acoustic points but zero accepted timing units and zero Mine fragments. Unassigned selected points remain in absolute More Detail. An empty [−3,+3] plotting fallback is not evidence or a scale improvement.

### Every accepted timing unit

“Absolute st” below means full selected values relative to the original recording baseline, before current Mine smoothing. “Extra centering” distinguishes the new fragment transform from the prior whole-unit transform; even a one-fragment unit is translated relative to current absolute Mine. This avoids falsely attributing whole-unit centering benefits to a newly discovered fragment effect. Readability assessments concern visible measured shapes, not lexical correctness.

#### `40357072` / 我想买五把雨伞

| Unit / timing (s) | Fragments (point counts) | Absolute st min…max | Fragment-relative st min…max | Extra centering vs whole-unit | Readability / continuous failure |
| --- | --- | --- | --- | --- | --- |
| 我 / 0.84–1.37 | 1 (41) | -0.711…2.532 | -0.582…2.661 | no | Measured gesture slightly larger; no material primary-take rescue. |
| 想 / 1.38–1.93 | 1 (42) | 1.284…4.309 | -1.536…1.489 | no | Measured gesture slightly larger; no material primary-take rescue. |
| 买 / 1.94–2.52 | 4 (12/2/1/26) | -12.810…2.817 | -9.225…3.723 | yes | Partial only; 12.709-st connected fragment survives. |
| 五 / 2.55–3.17 | 1 (40) | -0.345…2.566 | -0.997…1.914 | no | Measured gesture slightly larger; no material primary-take rescue. |
| 把 / 3.18–3.55 | 2 (6/3) | -3.238…-2.045 | -1.015…0.369 | yes | Sparse fragments remain; no full gesture confidence. |
| 雨伞 **grouped** / 3.56–4.87 | 3 (54/4/21) | -13.254…2.662 | -10.899…1.827 | yes | Partial only; 11.724-st connected fragment survives. |

#### `8d252264` / 我要一个苹果

| Unit / timing (s) | Fragments (point counts) | Absolute st min…max | Fragment-relative st min…max | Extra centering vs whole-unit | Readability / continuous failure |
| --- | --- | --- | --- | --- | --- |
| 我 / 0.47–0.96 | 1 (36) | -2.512…0.982 | -0.966…2.528 | no | Much clearer shared scale; measured shape unchanged. |
| 要 / 0.97–1.46 | 5 (14/5/1/2/5) | -9.866…2.224 | -2.267…1.998 | yes | Fragments clearer, but whole cross-gap dip is intentionally not conveyed. |
| 一 / 1.68–2.46 | 1 (41) | -0.630…1.553 | -1.251…0.932 | no | Much clearer shared scale; measured shape unchanged. |
| 个 / 2.47–2.94 | 3 (1/4/4) | -15.139…1.414 | -0.254…0.166 | yes | Three tiny fragments center near zero; cannot infer a full gesture. |
| 苹 / 3.26–4.02 | 1 (51) | -1.299…2.113 | -1.369…2.044 | no | Much clearer shared scale; measured shape unchanged. |
| 果 / 4.03–4.67 | 2 (3/21) | 18.720…22.287 | -0.815…2.689 | yes | 24 high points retained in 3+21 runs; genuine rejected-frame gap only. |

#### `d47274bc` / 我有一个苹果

No accepted units. No per-character or grouped fragment projection.

#### `4b9dbd2b` / 我要一个苹果

| Unit / timing (s) | Fragments (point counts) | Absolute st min…max | Fragment-relative st min…max | Extra centering vs whole-unit | Readability / continuous failure |
| --- | --- | --- | --- | --- | --- |
| 我 / 0.68–1.61 | 1 (55) | -2.056…3.795 | -1.503…4.348 | no | Coherent shape retained; modest common-scale change. |
| 要 / 1.62–2.44 | 1 (12) | -0.867…2.627 | -1.370…2.124 | no | Coherent shape retained; modest common-scale change. |
| 一 / 2.86–3.25 | 1 (29) | -2.089…5.534 | -3.776…3.848 | no | Coherent shape retained; modest common-scale change. |
| 个 / 3.26–3.85 | 1 (22) | -2.708…0.487 | -0.940…2.254 | no | Coherent shape retained; modest common-scale change. |
| 苹 / 4.59–5.53 | 1 (47) | 0.772…6.301 | -1.540…3.990 | no | Coherent shape retained; modest common-scale change. |
| 果 / 5.54–6.38 | 1 (59) | -2.221…3.082 | -0.865…4.438 | no | Coherent shape retained; modest common-scale change. |

#### `8faf1a90` / 我要一个苹果

| Unit / timing (s) | Fragments (point counts) | Absolute st min…max | Fragment-relative st min…max | Extra centering vs whole-unit | Readability / continuous failure |
| --- | --- | --- | --- | --- | --- |
| 我 / 0.59–0.87 | 1 (19) | 0.106…2.894 | -1.826…0.962 | no | Coherent shape retained; modest common-scale change. |
| 要 / 0.88–1.23 | 1 (29) | -0.348…0.915 | -0.483…0.780 | no | Coherent shape retained; modest common-scale change. |
| 一 / 1.24–1.49 | 1 (19) | -0.220…1.154 | -0.418…0.957 | no | Coherent shape retained; modest common-scale change. |
| 个 / 1.50–1.89 | 1 (31) | -2.082…0.896 | -1.012…1.967 | no | Coherent shape retained; modest common-scale change. |
| 苹 / 1.92–2.32 | 1 (26) | -1.781…5.220 | -4.277…2.724 | no | Coherent shape retained; modest common-scale change. |
| 果 / 2.33–2.86 | 1 (37) | -3.819…0.793 | -1.361…3.250 | no | Coherent shape retained; modest common-scale change. |

#### `a5acd04c` / 我有一个苹果

| Unit / timing (s) | Fragments (point counts) | Absolute st min…max | Fragment-relative st min…max | Extra centering vs whole-unit | Readability / continuous failure |
| --- | --- | --- | --- | --- | --- |
| 我 / 0.68–0.91 | 1 (15) | 2.981…4.986 | -1.716…0.289 | no | Much clearer shared scale; continuous shape unchanged. |
| 有 / 0.92–1.25 | 2 (29/3) | -2.274…20.468 | -0.772…3.294 | yes | Disconnected high-register island centers separately; its measured local shape survives. |
| 一 / 1.26–1.47 | 1 (18) | 0.492…1.515 | -0.742…0.280 | no | Much clearer shared scale; continuous shape unchanged. |
| 个 / 1.48–1.67 | 2 (14/2) | -2.643…10.220 | -1.888…1.825 | yes | Disconnected high-register island centers separately; its measured local shape survives. |
| 苹 / 1.68–2.01 | 1 (25) | -2.488…5.984 | -5.331…3.142 | no | Much clearer shared scale; continuous shape unchanged. |
| 果 / 2.02–2.47 | 1 (30) | -3.631…1.777 | -0.814…4.593 | no | Much clearer shared scale; continuous shape unchanged. |


## 5. Critical-case safety

**8d252264:** 果 owns the 353–434 Hz selected branch. It is already separated into **3 points at 4.1002–4.1202 s** and **21 at 4.1402–4.3402 s** by the rejected source frame at **4.1302**. The 20 ms selected-endpoint gap contains exactly 10 ms missing support. Fragment centers are **356.948 and 371.528 Hz**, and excursions **0.331 and 3.504 st**. The long 21-point high run remains intact. No high/low comparison, candidate strength or pitch jump splits it. The whole utterance domain becomes **−3.267…+3.689 st**, an **82.4%** reduction versus current Mine. Much of the additional improvement over whole-unit centering comes from real gaps inside 要 and 个. Their formerly broad cross-gap register relationships are intentionally omitted; this is not evidence that their original F0 was wrong or their gestures correct.

**a5acd04c:** the prominent high excursion in 有 is a **three-point fragment, 1.2217–1.2417 s**, separated from 29 preceding points by one missing source frame (20 ms endpoint gap). 个 has **14 + 2** points separated by three missing frames (40 ms endpoint gap). Their high centers are **365.159 and 210.250 Hz**. These specific large discontinuities are **disconnected register mismatches**, not continuous jumps hidden by this prototype. A subsequent high sample outside accepted cell ownership is still visible in detail; boundaries are not moved to capture it. The domain improves from current **−4.617…+21.468**, and prior whole-unit **−6.331…+22.895**, to **−6.331…+5.593 st**. Broad continuous motion in 苹 (8.472 st) remains unchanged and is not treated as a failure just for being large.

**Continuous counterexample:** 100→105→210→220 Hz at consecutive 10 ms source frames produces **one** four-point fragment, retains its exact **12 st internal jump**, and occupies a **13.650 st** measured excursion. Independent magnitude changes never alter fragment membership. The viewer renders one connected line. Splitting this contour to make it look smooth would fail the contract and the tests.

## 6. Low/high register controls

All **617/617 protected samples**, all **11/11 saved sub-70-Hz controls**, and all **2,827 selected points across the same 23 frozen control recordings** survive. No raw exclusion is reversed. Source indices and times are preserved; pairwise differences are checked separately inside each actual fragment. The explicit **54.610 Hz at 2.5124 s in 7787300e** remains. Its neighboring continuous register transition is not split merely because it is large; the low-control viewer makes this visible.

The saved synthetic-70 control contains only two already-selected **70.254 Hz** frames; both survive. Separate deterministic coherent 70 Hz shape inputs test the transform itself, along with 54.610, 55 and 60 Hz copies. High controls include the existing saved `native_24k`, `take_1`, `take_2`, `take_3` evidence, synthetic **350→380→410→440 Hz**, and same-shape 350/380/440 Hz copies. No independent real-falsetto truth is newly claimed. All high samples retain their local amplitude and order; only absolute fragment register is omitted from Mine.

The control fixtures cover entire saved recordings to stress continuity and retention; they do not assert new character timing. The physical replay separately proves accepted timing/grouping and no-timing behavior. Registers shifted independently per existing fragment produce the same fragment membership and geometry, including ±12-st shifts, without running any acoustic selector.

## 7. Semantics and unchanged production boundaries

**Timing identity remains separate from acoustic fragmentation.** 雨伞 is one group with three internal fragments, not three syllables, nor separately attributed 雨 and 伞. Character-timed units can have fragments under the identical continuity rule. No individual grade is added.

A gap alone does not tell a viewer that vertical register has been reset. The diagnostic therefore says **“Relative gesture fragments”** and explicitly states that vertical register across a gap is not comparable. No transition connector is added. There is no need for another symbol merely marking a gap that is already visible, but if this ever earned integration, the semantic reset would need clear wording in context. Since outcome B fails integration, **no product wording or default semantics change in this pass**.

- **Mine today:** unchanged smoothed/simplified recording-baseline contour with current absolute inter-unit relationships. Prototype only: independently centered measured fragments within unchanged trusted timing spans, common semitone amplitude scale, visible gaps.
- **More Detail:** unchanged selected absolute F0 over true time. Production uses one fixed recording-baseline semitone axis, preserving cross-unit and cross-gap absolute register; the viewer also exposes exact stored selected Hz. No local centers enter `filtered`.
- **Raw:** unchanged tracker output, retention and exclusions. Full candidate/provenance evidence stays in the frozen track. The mobile Raw payload does not expose all candidates, and no schema expansion is made. The local Hz raw plot uses points only.
- **Eligibility, classifier and confidence:** unchanged; fragment geometry is never fed back into them. `classify_contour` already ignores the supplied display contour and derives from frozen acoustic evidence. A focused replay checks all 30 units retain acoustic results. Group instability and sparse-unit insufficiency stay as before; fewer visual excursions do not create confidence.
- **Reference independence:** changing target, perceived characters, pinyin, lexical tone or surface expectation while preserving accepted timing yields identical actual mobile geometry for all six takes. The helper accepts only selected samples, accepted timing and measured cadence. No reference tone chooses boundaries, centers or domains.

## 8. Validation and preservation

**29 focused checks passed:** 28 new fragment tests plus the preceding research test that proves presentation cannot alter classifier/eligibility across all 30 accepted physical units. Tests cover real gaps, single-frame gaps, time/source discontinuity, cadence jitter, arbitrary-magnitude boundary independence, continuous octave-sized jumps, ±12 st geometric equivalence, all within-fragment pairs, direction, extrema, curvature, amplitude, source/time order, grouped identity, character/group parity, shared scaling, no accepted timing, input immutability, protected controls and exact physical failure findings.

The replay verifies saved evidence identities, selected/raw values and frame indices; original input, filtered and raw JSON remain equal; all 961 X coordinates match the preceding actual mobile layout. Browser checks pass for six recordings, exact projected counts, the primary 79-point/three-fragment group zoom, both measured gap lengths, 24 high points/two existing fragments, explicit low-F0, one-line continuous-jump control, source hover, no-timing empty Mine and a narrow viewport. Six full screenshots plus the focused zoom were captured and inspected.

Research Ruff and formatting checks, Python compile checks, browser-script syntax, `git diff --check`, and new untracked-file whitespace checks pass. All **163** pre-pass mobile/backend source hashes remain unchanged. No production files or schemas changed; no mobile/native/web product suite, backend full suite or persistence tests were rerun. Generated outputs remain ignored; source/templates and numeric report data are reviewable. The initial sandboxed Chromium attempt could not start its debugging pipe; the approved local-only rerun passed with HTTP/HTTPS blocked. No automatic-approval rejection occurred.

Reproduce from the repository root using existing local dependencies and snapshots:

```sh
PYTHONPATH=. services/api/.venv/bin/python -m benchmark.pronunciation_v2.relative_pitch_fragments_report
PYTHONPATH=. services/api/.venv/bin/pytest -q benchmark/pronunciation_v2/test_relative_pitch_fragments.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py::test_presentation_cannot_change_existing_eligibility_or_observation
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/relative_pitch_fragments.py benchmark/pronunciation_v2/relative_pitch_fragments_report.py benchmark/pronunciation_v2/test_relative_pitch_fragments.py
services/api/.venv/bin/ruff format --check benchmark/pronunciation_v2/relative_pitch_fragments.py benchmark/pronunciation_v2/relative_pitch_fragments_report.py benchmark/pronunciation_v2/test_relative_pitch_fragments.py
node --check benchmark/pronunciation_v2/relative_pitch_fragments_browser_check.cjs
node benchmark/pronunciation_v2/relative_pitch_fragments_browser_check.cjs
git diff --check
```

The final Git output is preserved locally at `services/api/var/relative-pitch-gesture/fragments/final-git-state.txt`. Its tracked diff is the cumulative pre-existing stack; newly added research files remain untracked. No commit, push or deployment.

## 9. Seven decisions

| Decision | Result | Basis |
| --- | --- | --- |
| 1 — fragment model | **REAL EVIDENCE GAPS JUSTIFY INDEPENDENT GESTURE FRAGMENTS** | For an explicitly relative fragment view; absolute endpoint register is intentionally omitted, not disproved. |
| 2 — 40357072 / 雨伞 | **GROUPED 雨伞 REMAINS MISLEADING** | Isolated register mismatch improves, but its continuous 11.724-st last fragment still dominates scale. |
| 3 — continuous-error safety | **CONTINUOUS WITHIN-FRAGMENT FAILURES REMAIN EXPOSED** | Physical 买/雨伞 steps and the continuous synthetic 12-st step remain connected and unchanged. |
| 4 — register safety | **LOW/HIGH REGISTER SHAPE PRESERVED** | No loss of protected/selected samples; exact within-fragment differences and shared amplitude scale. |
| 5 — six-take quality | **PHYSICAL GRAPH QUALITY STILL INSUFFICIENT** | Two problematic takes improve strongly, but the primary physical acceptance take still fails. |
| 6 — checkpoint | **GRAPH QUALITY STILL BLOCKS CHECKPOINT** | Outcome B; no integration and no four-case re-smoke yet. |
| 7 — next step | **NAME EXACTLY ONE REMAINING GRAPH ISSUE** | The continuous terminal **−11.555 st drop at 4.7047–4.7147 s inside grouped 雨伞** still sets the lower Mine domain and obscures its gesture. |

**One next step:** address how Mine communicates that continuous terminal 雨伞 excursion without hiding it, splitting it by pitch magnitude, or changing its measured frequencies.
