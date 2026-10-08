# Local gesture centering + robust overflow composition — October 7, 2026

**Outcome B: COMPOSITION STILL FAILS the complete product acceptance gate. It does not earn integration. CURRENT MINE LINE-GRAPH MODEL SHOULD BE RECONSIDERED.**

The composition solves the two original local failures: `40357072` has materially readable broad gestures with its continuous terminal plunge still explicit, and all 24 high-register 果 points in `8d252264` retain visible internal motion. At the strongest admissible setting in this bounded comparison, **3.5 MAD**, both clean controls have zero overflow. Nevertheless, `a5acd04c` acquires overflow in **four of six units**: **16/136 points, five runs, 152.02 ms / 11.26% selected support**. This includes 27.81% of the ordinary coherent 苹 gesture and two overflow runs around 果's crest. The previous absolute robust window needed only two runs / five points / 50 ms in this take and retained both ordinary shapes completely.

This is a visual/product rejection, not an arithmetic failure or acoustic rejection. Existence, side, duration and boundary crossings remain explicit; outside curvature and extent cannot be read from the rails. In the learner-sized strip, these marks are no longer exceptional: four cells need interpretation, and a continuous crest alternates between line and overflow twice. A short “Pitch gesture” label does not recover that lost shape. The decision is an engineering visual assessment of the saved browser views, **not a measured learner-comprehension study or physical-device re-smoke**. No further threshold, filtering, tracker, fragment-centering or display-transform iteration was attempted.

[Interactive A/B/C viewer](../../../../services/api/var/relative-pitch-gesture/composed/viewer.html) · [numeric replay](composed-replay.json) · [primary comparison](../../../../services/api/var/relative-pitch-gesture/composed/figures/40357072-mad3.5.png) · [high-register comparison](../../../../services/api/var/relative-pitch-gesture/composed/figures/8d252264-mad3.5.png) · [decisive a5 comparison](../../../../services/api/var/relative-pitch-gesture/composed/figures/a5acd04c-mad3.5.png).

## Pipeline and evidence boundary

Selected measured absolute F0 → existing accepted timing ownership → `12 * log2(Hz / 1 Hz)` → subtract **one median per entire accepted unit** → collect all relative selected samples → one robust utterance domain → linear projection with explicit overflow.

The accepted timing adapter reads persisted pitch projections tied to the saved evidence ID. Trustworthy character timing supplies one unit; grouped timing supplies one whole group. It does not infer boundaries from pitch, text targets, raw provider words or equal splits. `d47274bc` supplies no units. The centered helper refuses selected evidence without a unit and refuses a segment crossing unit identities. Each unit is plotted separately; a constant offset never creates a line between units. Actual source-index/cadence gaps remain exactly the same segments as the earlier measured-overflow replay. No fragment medians are used.

The exact absolute semitone reference cancels. Hz-equivalent centers below are `2 ** (median_st / 12)`, so an even-count center is the geometric mean of the two middle Hz values, not an arithmetic-Hz median. The transformation is strictly a translation. All 961 owned physical samples preserve their selected Hz, source index, timestamp and mobile X coordinate. All within-unit pairwise differences, slopes, extrema, second differences/curvature and amplitudes are preserved within floating-point tolerance, including pairs across gaps. No smoothing, interpolation of missing evidence, deletion, scaling or nonlinear pitch compression is introduced. Interpolation occurs only at a visible boundary along an already continuous measured edge.

All source selection/candidates, accepted/rejected status, acoustic eligibility, completeness, stability, observation/classification, confidence, grouping and reference comparison remain unchanged. Source snapshots and production files are checked by hash. Target, perceived text, pinyin, lexical/reference tone and contextual surface tone cannot influence the numerical composition; the actual mobile X/geometry adapter also replays changed identity/reference metadata with fixed accepted spans. No display result feeds classification. Overflow is not uncertainty; clearer projection supplies no stronger evidence. Learner grading remains disabled.

## Domain and bounded comparison

Use the prior normal-consistent MAD family, making its convention explicit:

```text
m = median(all relative selected samples)
sigma_MAD = 1.4826 * median(abs(relative - m))
lo = max(actual_relative_min, m - k * sigma_MAD)
hi = min(actual_relative_max, m + k * sigma_MAD)
domain = [min(-3, lo - 1), max(+3, hi + 1)]
```

The robust bounds are limited to the actual range **before** the existing one-semitone padding and minimum ±3-st window. This matches the earlier `mad3` implementation exactly at `k=3`; no alternate MAD definition is smuggled in. One shared linear Y domain applies to every unit, preserving relative excursion comparisons **within the recording**. Pixel scale can differ between recordings, as it did before. The domain uses full selected measurements, never simplified vertices.

The first replay used 3.0 MAD. It unnecessarily clipped three points / 26.92 ms of clean `8faf1a90`. Only the predeclared nearby set **2.5, 3.0, 3.5** was compared. 3.5 removes clean-control overflow, so it is the representative final composition below; it is **not an approved production setting**. No wider search followed the remaining failure.

| Take | MAD multiplier | Domain (st) | Outside points | Runs | Outside support |
| --- | --- | --- | --- | --- | --- |
| 40357072 | 2.5 | -3.653…3.653 | 18 | 7 | 176.74 ms |
| 40357072 | 3 | -4.183…4.183 | 17 | 7 | 164.88 ms |
| 40357072 | 3.5 | -4.714…4.714 | 16 | 6 | 156.03 ms |
| 8d252264 | 2.5 | -4.158…4.158 | 12 | 4 | 120.00 ms |
| 8d252264 | 3 | -4.790…4.790 | 12 | 4 | 120.00 ms |
| 8d252264 | 3.5 | -5.422…5.422 | 12 | 4 | 120.00 ms |
| d47274bc | 2.5 | -3.000…3.000 | 0 | 0 | 0.00 ms |
| d47274bc | 3 | -3.000…3.000 | 0 | 0 | 0.00 ms |
| d47274bc | 3.5 | -3.000…3.000 | 0 | 0 | 0.00 ms |
| 4b9dbd2b | 2.5 | -4.776…5.317 | 0 | 0 | 0.00 ms |
| 4b9dbd2b | 3 | -4.776…5.438 | 0 | 0 | 0.00 ms |
| 4b9dbd2b | 3.5 | -4.776…5.438 | 0 | 0 | 0.00 ms |
| 8faf1a90 | 2.5 | -3.376…3.376 | 5 | 1 | 51.99 ms |
| 8faf1a90 | 3 | -3.852…3.852 | 3 | 1 | 26.92 ms |
| 8faf1a90 | 3.5 | -4.327…4.250 | 0 | 0 | 0.00 ms |
| a5acd04c | 2.5 | -3.169…3.169 | 19 | 5 | 189.99 ms |
| a5acd04c | 3 | -3.603…3.603 | 18 | 4 | 177.71 ms |
| a5acd04c | 3.5 | -4.036…4.036 | 16 | 5 | 152.02 ms |

## Three-view comparison and overflow burden

Every take has all three simultaneous panels: **A current production Mine geometry**, **B full-range timing-unit centering**, and **C that same centered evidence with robust domain and overflow**. A is the actual existing mobile adapter output; B/C retain the full selected samples, rather than reusing current smoothed/simplified vertices. Thus the amplitude invariants concern the selected evidence, not an assertion that every existing A vertex was unmodified. X positions are identical for all 961 owned selected points. All panels use the same 128-pixel plot height and 96-pixel character cells; the grouped zoom changes only X.

| Take | A: current domain (st) | B: centered full domain (st) | C: centered 3.5-MAD domain (st) | C px/st versus A |
| --- | --- | --- | --- | --- |
| 40357072 | -14.254…5.266 | -13.584…5.303 | -4.714…4.714 | +107.1% |
| 8d252264 | -16.139…23.287 | -10.021…17.133 | -5.422…5.422 | +263.6% |
| d47274bc | -14.022…10.300 | -3.000…3.000 | -3.000…3.000 | N/A: no Mine |
| 4b9dbd2b | -3.678…7.291 | -4.776…5.438 | -4.776…5.438 | +7.4% |
| 8faf1a90 | -4.580…6.220 | -5.277…4.250 | -4.327…4.250 | +25.9% |
| a5acd04c | -4.617…21.468 | -6.331…22.895 | -4.036…4.036 | +223.1% |

Final 3.5-MAD burden:

| Take | Inside / selected | Outside points | Outside support | Runs | Affected units | Entire units outside |
| --- | --- | --- | --- | --- | --- | --- |
| 40357072 | 236/252 | 16 (6.35%) | 156.03 ms (6.19%) | 6 | 买, 雨伞 | 0 |
| 8d252264 | 176/188 | 12 (6.38%) | 120.00 ms (6.40%) | 4 | 要, 个 | 0 |
| d47274bc | 0/0 | 0 (0.00%) | 0.00 ms (0.00%) | 0 | none | 0 |
| 4b9dbd2b | 224/224 | 0 (0.00%) | 0.00 ms (0.00%) | 0 | none | 0 |
| 8faf1a90 | 161/161 | 0 (0.00%) | 0.00 ms (0.00%) | 0 | none | 0 |
| a5acd04c | 120/136 | 16 (11.76%) | 152.02 ms (11.26%) | 5 | 有, 个, 苹, 果 | 0 |

No physical timing unit is entirely outside. This is observed for all three tested settings; it is not claimed as a mathematical guarantee for arbitrary distributions. A median between two separated modes need not itself be an observed point. Constant register translation alone cannot change any of these outcomes, because the per-unit translation cancels before domain estimation.

Duration means **selected support**, not the elapsed duration of the accepted word or the recording. As in the tested overflow primitive, linear support joins consecutive selected measurements; the outer endpoints have half-cadence support clipped to accepted timing. Missing/rejected evidence contributes no connecting line or overflow rail. A singleton can have a support rail but no invented contour. The six physical takes use 10 ms cadence.

## Primary 40357072: broad gestures now readable; terminal plunge retained

`40357072fc994a0ab052752ca119b2e6.wav` / **我想买五把雨伞** improves from −14.254…+5.266 st current, through −13.584…+5.303 st centered-only, to **−4.713861…+4.713861 st** composed. Ordinary movement is **107.1% taller per semitone than current**, and **100.3% taller than centering alone**, at the same graph height. The intended broad measured dips/rises are materially more legible. This is not a claim that the questionable continuous movements became acoustically correct.

| Unit | Accepted span (s) | Median st re 1 Hz | Median-equivalent Hz | Relative min…max (st) | Excursion (st) | Inside / selected |
| --- | --- | --- | --- | --- | --- | --- |
| 我 | 0.84–1.37 | 81.422055 | 110.291 | -0.582…2.661 | 3.243 | 41/41 |
| 想 | 1.38–1.93 | 84.371181 | 130.774 | -1.536…1.489 | 3.025 | 42/42 |
| 买 | 1.94–2.52 | 80.065200 | 101.977 | -11.324…4.303 | 15.627 | 33/41 |
| 五 | 2.55–3.17 | 82.203582 | 115.384 | -0.997…1.914 | 2.911 | 40/40 |
| 把 | 3.18–3.55 | 79.133149 | 96.632 | -0.820…0.373 | 1.193 | 9/9 |
| 雨伞 | 3.56–4.87 | 80.881255 | 106.899 | -12.584…3.332 | 15.916 | 71/79 |

**买:** 101.977-Hz equivalent center; unchanged **15.627-st excursion**. 33/41 points are inside; eight outside points form four distinct runs totaling **77.890 ms**, 19.01% of its selected support. Existing gaps explain the separate low islands. Its two continuous boundary crossings are at **2.170010414 s** (reentry) and **2.382120593 s** (exit). No pitch jump was split merely because of magnitude.

**Grouped 雨伞:** one accepted **3.56–4.87 s** unit, **one median over all 79 selected points**, 106.899-Hz equivalent center, relative range **−12.584185…+3.332072 st**, full excursion **15.916256 st**. Its existing 54/4/21-point segments remain unchanged. No 雨/伞 timing or separate median is invented. 71/79 points remain inside (89.87%). The disconnected four-point low island has **40 ms** explicit overflow support. The continuous **−11.5547-st** terminal step from **4.7047 to 4.7147 s**, source **467→468**, remains in the same measured segment. Its exact lower-boundary intersection is **4.711559380 s**, at mobile position **6.667133213**. From that crossing, the terminal outside run remains visible as an outward indicator and dashed duration rail through half-hop support ending **4.7497 s**, **38.140620 ms**. Four terminal measurements **468–471** are outside. The plunge neither ends at a fictional measured boundary value nor disappears into a gap.

[Grouped A/B/C zoom](../../../../services/api/var/relative-pitch-gesture/composed/figures/40357072-zoom.png).

| Unit | Side | Run endpoints (s) | Supported duration | Source indices |
| --- | --- | --- | --- | --- |
| 买 | below | 2.074700000–2.084700000 | 20.000 ms | 204, 205 |
| 买 | below | 2.114700000–2.114700000 | 10.000 ms | 208 |
| 买 | below | 2.134700000–2.170010414 | 40.310 ms | 210, 211, 212, 213 |
| 买 | below | 2.382120593–2.384700000 | 7.579 ms | 235 |
| 雨伞 | below | 4.284700000–4.314700000 | 40.000 ms | 425, 426, 427, 428 |
| 雨伞 | below | 4.711559380–4.744700000 | 38.141 ms | 468, 469, 470, 471 |

## Decisive high-register countercase: 8d252264 passes

果's center is **102.324871151 st re 1 Hz / 368.896578 Hz**. All **24 selected points** spanning approximately **353–434 Hz** remain in the internal relative range **−0.755371…+2.811589 st** (3.566960-st excursion). They sit wholly inside the shared **−5.421610…+5.421610-st** final domain: **100% inside, zero overflow**. Its internal rise is visible. The existing 3-point / 21-point segments and intervening missing evidence remain separate; the 240 ms of support no longer appears solely as rails. This holds at all three tested settings.

The sentence still has 12 outside points / 120 ms in 要 and 个. These are internal relative excursions, not 果's constant register offset. 要 has 80 ms in three actual-gap-separated runs; 个 has 40 ms in one. The unchanged 个 center is approximately 51.18 Hz: it is not raised or rejected for being low. Its higher relative branch remains explicitly outside.

## a5acd04c: the remaining product failure

Ordinary shapes grow substantially, but centering **increases rather than reduces overflow** compared with the prior absolute three-MAD prototype. The new ±4.036415-st window is narrower than the old −4.631…+8.743-st window. 有's three high points / 30 ms and 个's two / 20 ms remain explicit. Additionally:

- **苹:** the coherent **8.472343-st** movement is unchanged, but **7/25 points / 69.535 ms / 27.81% of selected support** are outside. Its descending endpoint and low tail become an overflow rail; the tail's internal shape is no longer readable in Mine. The previous robust-only view kept the whole gesture inside.
- **果:** **4/30 points / 32.486 ms / 10.95% support** are outside. A continuous upper crest alternates outside/inside/outside, creating **two** rails and several closely spaced crossings. These runs are correct geometrically; their crowded line/arrow interpretation is a poor default learner presentation.

Total **16/136 outside points (11.76%)**, **five runs**, **152.021 ms (11.26%)**, in **four of six units**, versus the prior two units / two runs / 50 ms (3.70%). There is no entirely outside unit, but that necessary condition is insufficient. Explicitly marking valid motion is not the same as leaving its useful gesture readable. The fixed nearby candidates do not resolve this: smaller windows are worse. Stop here.

[Phone-width composed view at 苹/果](../../../../services/api/var/relative-pitch-gesture/composed/figures/a5acd04c-narrow-composed.png).

## Controls and large-movement safety

**Clean:** `4b9dbd2b` retains all 224 points; `8faf1a90` all 161. At 3.5 MAD both have **zero overflow**, useful unaltered within-unit shapes and a shared per-recording amplitude scale. Pixels per semitone increase **7.4% / 25.9%** versus A; this was visually useful, not a minimum-span noise zoom. Centering shifts units independently, so cross-unit absolute register is intentionally absent. The 3.0 and 2.5 settings fail the clean no-unnecessary-overflow preference for `8faf1a90`.

**No timing:** `d47274bc` has no accepted units and **zero Mine points, paths or overflow events** in B/C. Its full selected evidence and Raw remain available outside Mine. An empty view is not counted as scale-quality success.

**Low F0:** exact membership and Hz checks replay **all 617 protected samples**, **all 11 explicit sub-70-Hz entries**, and **2,827 selected samples across 23 frozen controls**. Nothing is removed. The saved synthetic-70 fixture keeps its two 70.254-Hz selected frames. The exact **54.610-Hz** sample at **2.5124 s in 7787300e** remains selected, relative ordinate **−9.756690 st**; it lies outside that control's ±7.085829-st final window and is explicitly represented by overflow. This is valid movement, not a special low-F0 exception.

At 3.5 MAD these frozen controls have **82/2,827 outside points**, **802.754 ms / 28.2701 s = 2.84% outside support**; **9 protected samples and 8 of the 11 sub-70 entries** are outside but still selected and explicitly represented. At 3.0 MAD the corresponding counts are 99 total / 11 protected / 10 sub-70 and 980.384 ms. These controls use explicit whole-recording stress-fixture spans, **not fabricated character timing**. Their retained evidence and overflow partition are checked point by point.

**Low/high register copies:** deterministic coherent copies at 54.610, 70, 350, 380 and 440 Hz produce the same local contour and no overflow. Independently multiplying alternating physical timing units by 0.5 or 2 preserves every composed path, crossing, event and shared domain within numerical tolerance. Existing whole-unit tests also replay the protected corpus under register shifts. Absolute register is removed only as a display offset; selected Hz stays in provenance and detail.

**Large real motion:** the existing coherent **55→220 Hz, 61-sample, 24-st sweep** remains one segment with the full amplitude. Alone, all samples fit the padded **−13…+13-st** domain, with zero overflow. In an explicit synthetic fixture alongside 60 ordinary small-gesture units, the *same* sweep faces a shared **±6.1891-st** domain: **30 sweep samples** are outside in exactly **two runs**, crossing at **0.1452725 / 0.4547275 s**, with **295.545 ms** total outside support. Both directions and continuation duration are explicit; no reshaping or deletion occurs. This is a display stress test, not a new acoustic experiment. The existing continuous 100→105→210→220-Hz control retains its 12-st internal step and 13.650-st total movement.

## Mine, More Detail and Raw semantics

If integrated, Mine would mean **relative measured pitch gesture within each trustworthy timing unit**. All units would share a linear relative semitone scale, but their independent vertical offsets would intentionally erase absolute register relationships between units. The concise product label would be **“Pitch gesture”**, accompanied by a short overflow legend. This trial does not earn that label or any UI integration: the combination still asks the learner to infer too much missing shape from rails in the a5 case.

**More Detail remains unchanged:** complete selected absolute-F0 information on real recording time, displayed using the existing single recording-baseline semitone offset. That is not a literal Hz axis; it preserves cross-unit register and full excursions, and source hover exposes exact Hz. No unit centering or robust bounds propagate into it. **Raw remains unchanged:** original tracker evidence, retained/excluded identity and exact source timestamps, independently plotted; no corrected frequency or invented sample is substituted. The saved payloads and source code remain byte-for-byte intact.

**Production files changed in this pass: none.** No backend schema change. No mobile label, graph, grading or acoustic-policy change. The pre-existing large uncommitted pronunciation stack is preserved; no reset, revert, stash, commit, push or deployment was performed. `docs/development/tone-graph-v2.md` is left unchanged because there is no new production state.

## Validation and reproduction

**86 focused research checks passed:** 26 composition checks, the 30 prior overflow checks and 30 whole-unit relative checks. They include all pairs across every physical unit, synthetic rising/falling/U/extrema/curvature, exact grouped median, gap and cross-unit separation, sustained/reentrant overflow, ±12-st independent-unit shifts, source preservation, all low controls, clean controls, no timing, high register, large movement, target/reference independence and the a5 acceptance counterexample. The existing eligibility/observed-gesture independence test also executes within this focused set. No tracker/VAD/provider or broad acoustic experiment runs.

All **31 frozen input hashes** match (the 30 earlier inputs plus the reused overflow viewer snapshot). All **205 pre-pass mobile/backend source and test file hashes** match. Ruff lint and format, JavaScript syntax and `git diff --check` pass. No production suite is required because production is unchanged.

Browser validation covers **six takes × three settings**, all three A/B/C panels, exact selected/inside/overflow counts, no-timing emptiness, grouped boundary crossing, 24/24 high 果 visibility, clean zero-overflow at 3.5 MAD, event provenance hover and 390-pixel horizontal scrolling. Screenshots cover all six final comparisons, both other primary settings, grouped zoom and phone-width composed views. All six final views and the primary group zoom were visually inspected; the decisive a5 phone view was inspected separately. The sandboxed Chromium pipe initially failed to start; the approved local-only rerun used blocked HTTP/HTTPS and no remote assets. This is browser research validation, not a mobile physical re-smoke.

```sh
PYTHONPATH=. services/api/.venv/bin/python -m benchmark.pronunciation_v2.composed_relative_overflow_report
PYTHONPATH=. services/api/.venv/bin/pytest -q benchmark/pronunciation_v2/test_composed_relative_overflow.py benchmark/pronunciation_v2/test_robust_domain_overflow.py benchmark/pronunciation_v2/test_relative_pitch_gesture.py
services/api/.venv/bin/ruff check benchmark/pronunciation_v2/composed_relative_overflow.py benchmark/pronunciation_v2/composed_relative_overflow_report.py benchmark/pronunciation_v2/test_composed_relative_overflow.py
services/api/.venv/bin/ruff format --check benchmark/pronunciation_v2/composed_relative_overflow.py benchmark/pronunciation_v2/composed_relative_overflow_report.py benchmark/pronunciation_v2/test_composed_relative_overflow.py
node --check benchmark/pronunciation_v2/composed_relative_overflow_browser_check.cjs
node benchmark/pronunciation_v2/composed_relative_overflow_browser_check.cjs
git diff --check
```

Reproduction uses existing private frozen snapshots and local dependencies. Viewer data, figures, logs and source-preservation manifests live under ignored `services/api/var/relative-pitch-gesture/composed/`. Reusable research helper/report/test/viewer/browser-check files live under `benchmark/pronunciation_v2/composed_relative_overflow*` and `test_composed_relative_overflow.py`; this report, numeric replay and README are the documentation changes. No audio is copied into documentation. Final Git status/stat are saved alongside those local artifacts; tracked diff statistics describe the pre-existing stack, not just this pass's untracked files.

## Seven final decisions

| Decision | Selected result | Reason |
| --- | --- | --- |
| 1 — composition | **COMPOSITION STILL FAILS** | It solves the original two local failures but misses the full product gate on a5 ordinary shape/overflow burden. |
| 2 — primary | **PRIMARY U-SHAPE TAKE IS MATERIALLY READABLE** | +107.1% px/st at 3.5 MAD; terminal plunge remains explicitly continuous. |
| 3 — high register | **SUSTAINED HIGH-REGISTER UNIT RETAINS ITS INTERNAL GESTURE** | 果 24/24 inside, zero overflow, unchanged 3.567-st internal motion. |
| 4 — truth safety | **NO MEASURED MOVEMENT IS SILENTLY HIDDEN** | Every outside source sample belongs to an explicit event; this preserves existence/duration, not visible outside curvature or amplitude. |
| 5 — product semantics | **MINE SEMANTICS ARE TOO COMPLICATED / MISLEADING** | Four of six a5 cells require overflow interpretation, including an ordinary tail and crest; insufficient for default learner gesture reading. This is a design assessment, not a user-study result. |
| 6 — checkpoint | **CURRENT MINE LINE-GRAPH MODEL SHOULD BE RECONSIDERED** | No integration and no readiness claim for the four-case physical re-smoke. |
| 7 — next step | **STOP LINE-GRAPH HEURISTIC ITERATION AND RECOMMEND ONE PRODUCT-LEVEL ALTERNATIVE** | Move the default interaction to audio-first practice cards. |

**One next step:** prototype **audio-first listen-and-repeat cards for accepted timing units**, with recording playback and existing evidence status, while keeping the complete absolute pitch graph in optional detail. Preserve grouped spans and leave untimed audio at utterance level; do not add grading or another pitch projection. This is one product alternative, not another tracker/filter/domain proposal.

## Remaining per-unit centers and burden (3.5 MAD)

| Take | Unit | Center Hz | Relative min…max (st) | Inside / selected | Outside duration |
| --- | --- | --- | --- | --- | --- |
| 8d252264 | 我 | 109.533 | -0.966…2.528 | 36/36 | 0.00 ms |
| 8d252264 | 要 | 114.061 | -9.021…3.069 | 19/27 | 80.00 ms |
| 8d252264 | 一 | 124.140 | -1.251…0.932 | 41/41 | 0.00 ms |
| 8d252264 | 个 | 51.180 | -0.420…16.133 | 5/9 | 40.00 ms |
| 8d252264 | 苹 | 120.248 | -1.369…2.044 | 51/51 | 0.00 ms |
| 8d252264 | 果 | 368.897 | -0.755…2.812 | 24/24 | 0.00 ms |
| 4b9dbd2b | 我 | 107.548 | -1.503…4.348 | 55/55 | 0.00 ms |
| 4b9dbd2b | 要 | 114.308 | -1.370…2.124 | 12/12 | 0.00 ms |
| 4b9dbd2b | 一 | 122.399 | -3.776…3.848 | 29/29 | 0.00 ms |
| 4b9dbd2b | 个 | 100.259 | -0.940…2.254 | 22/22 | 0.00 ms |
| 4b9dbd2b | 苹 | 126.894 | -1.540…3.990 | 47/47 | 0.00 ms |
| 4b9dbd2b | 果 | 102.670 | -0.865…4.438 | 59/59 | 0.00 ms |
| 8faf1a90 | 我 | 123.075 | -1.826…0.962 | 19/19 | 0.00 ms |
| 8faf1a90 | 要 | 110.942 | -0.483…0.780 | 29/29 | 0.00 ms |
| 8faf1a90 | 一 | 111.343 | -0.418…0.957 | 19/19 | 0.00 ms |
| 8faf1a90 | 个 | 103.481 | -1.012…1.967 | 31/31 | 0.00 ms |
| 8faf1a90 | 苹 | 127.156 | -4.277…2.724 | 26/26 | 0.00 ms |
| 8faf1a90 | 果 | 95.513 | -1.361…3.250 | 37/37 | 0.00 ms |
| a5acd04c | 我 | 152.851 | -1.716…0.289 | 15/15 | 0.00 ms |
| a5acd04c | 有 | 107.320 | -0.848…21.895 | 29/32 | 30.00 ms |
| a5acd04c | 一 | 125.149 | -0.742…0.280 | 18/18 | 0.00 ms |
| a5acd04c | 个 | 112.564 | -2.042…10.820 | 14/16 | 20.00 ms |
| a5acd04c | 苹 | 137.331 | -5.331…3.142 | 18/25 | 69.53 ms |
| a5acd04c | 果 | 99.037 | -0.814…4.593 | 26/30 | 32.49 ms |
