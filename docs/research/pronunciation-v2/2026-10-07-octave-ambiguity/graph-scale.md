# Graph scale and six-take visual review

**Ambiguity rejection did not solve scaling, and no scale change was implemented.** The table distinguishes actual production from counterfactual research. Production after this pass is exactly the “before” column.

Mine inherits the full selected smoothed contour's bounds even after simplification and timing projection. `PitchPlot` expands those bounds for any displayed vertex outside them; it performs no percentile clipping. Thus a selected extreme can determine the domain even if its timestamp is not attributed to a character cell. More Detail additionally includes unsmoothed extrema. Raw uses its own domain and cannot contaminate Mine's domain by being opened.

## Before and experimental after

“Suspicious” counts exclude the preserved broad low-dip controls B1/C1. Events are acoustic review windows, which may contain several segments. Display range is smoothed min…max before the ±1 st domain margin. All values are relative to each version's retained median.

| Take | Before selected; suspicious frames / events | Before display range | Before Mine domain | Frame-rule excluded → surviving | Experimental range / Mine domain | Complete-run excluded → surviving |
| --- | --- | --- | --- | --- | --- | --- |
| 1 `40357072` | 253; 16 / 4 | −13.25…4.27 | −14.25…5.27 | 7 → 246 | −13.38…4.14 / −14.38…5.14 | 4 → 249 |
| 2 `8d252264` | 189; 29 / 3 | −15.14…22.29 | −16.14…23.29 | 0 → 189 | unchanged | 0 → 189 |
| 3 `d47274bc` | 214; 3 / 1 | −13.02…9.30 | −14.02…10.30 | 0 → 214 | unchanged | 0 → 214 |
| 4 `4b9dbd2b` | 224; 0 / 0 | −2.68…6.29 | −3.68…7.29 | 0 → 224 | unchanged | 0 → 224 |
| 5 `8faf1a90` | 164; 0 / 0 | −3.58…5.22 | −4.58…6.22 | 0 → 164 | unchanged | 0 → 164 |
| 6 `a5acd04c` | 140; 6 / 2 | −3.62…20.47 | −4.62…21.47 | 0 → 140 | unchanged | 0 → 140 |

Take 1's complete-run domain is −14.33…5.20. Both variants shift its median slightly but leave its **19.52 st domain width unchanged**: the 51.7 Hz region still supplies the minimum. The other domain widths remain 39.43, 24.32, 10.97, 10.80 and 26.09 st. Removing some suspicious points is not equivalent to fixing the scale.

More Detail domains before the experiment are, respectively: −14.25…5.31, −16.14…23.29, −14.02…10.47, −3.71…7.30, −4.82…6.22 and −4.63…21.47. Small differences from Mine are caused by unsmoothed measured extrema, not a separate robust policy. The precise values for both trials appear in [replay.json](replay.json).

Selected display islands before / frame-rule after / complete-run after: **11/9/11, 12/12/12, 9/9/9, 6/6/6, 4/4/4, 5/5/5**. Start/end/length and extrema of every island are exported. The diagnostic branch grouping used to measure ambiguous-run duration is distinct from these display islands: the former can span short missing evidence, while the latter always breaks there.

The frame table's domain-influence flag includes baseline shifts. Its separate `domain_span_reduction_if_only_this_frame_removed_st` distinguishes genuine compression from recentering. Removing one endpoint often leaves neighboring extreme frames to set the same span; that is not evidence the whole run is harmless.

## Six-take review

| Take / saved overview | Broad contour / remaining issue | Useful extrema |
| --- | --- | --- |
| [1](../../../../services/api/var/octave-ambiguity/figures/40357072-all.png) | Partial removal of A1 and removal of A4 do not make the full trace coherent. A1's later low region, A2 and A3 remain; low extremes still flatten the broad motion. | No wholesale low-range removal; unresolved selected 51–60 Hz evidence remains. |
| [2](../../../../services/api/var/octave-ambiguity/figures/8d252264-all.png) | B2/B3 low islands and the 250 ms B4 high branch survive. High and low extremes compress the middle into a narrow visual band. | B1's gradual low dip is preserved. No assumption that a wide span itself is invalid. |
| [3](../../../../services/api/var/octave-ambiguity/figures/d47274bc-all.png) | Broad movement is plausible, but three ~51.7 Hz onset samples still set the lower domain. | The ~70 Hz dip/recovery and sustained rise to ~189 Hz survive. |
| [4](../../../../services/api/var/octave-ambiguity/figures/4b9dbd2b-all.png) | Coherent before and after; no obvious octave island found. | Entire selected range and all six islands unchanged. |
| [5](../../../../services/api/var/octave-ambiguity/figures/8faf1a90-all.png) | Coherent before and after; visible broad fall/recovery remains. | Entire selected range unchanged. |
| [6](../../../../services/api/var/octave-ambiguity/figures/a5acd04c-all.png) | The ~354–380 Hz island and ~209–210 Hz island remain. The former dominates the upper Y bound. | Main fall/recovery remains measured; neither ambiguous island was silently corrected. |

No legitimate physical extremum was removed merely for its absolute frequency or range. However, the frame experiment **does lose a known legitimate extremum in the historical protected corpus**, so these physical plots cannot earn integration on appearance alone. Every “after” plot is marked a rejected experiment.

## Minimal robust-domain policy considered, not implemented

An evidence-based primary domain could begin with coherent selected runs lasting at least 120 ms, then expand for other truthful selected extrema. That proposal fails to resolve this evidence set: B4 already has a 210 ms contiguous high segment, so a duration/coherence guard admits the artifact that dominates take 2's upper scale. Conversely, the protected 54–55 Hz run is only 40 ms, so treating all short extremes as disposable would suppress known truth.

If remaining selected points are not acoustically rejected, preserving them requires domain expansion or an explicit overflow design. Expansion returns the unresolved extremes to the domain. The existing graph has no overflow semantics that could honestly hide those points; adding one would be a different UI change and still would not establish which branch is reliable. Arbitrary percentile clipping, hard pitch ranges and chart-edge capping therefore do not satisfy the acceptance criteria.

The needed distinction is acoustic branch reliability, not an additional scaling preference. With no accepted evidence selector, the decision is **GRAPH SCALE STILL UNSOLVED**, rather than claiming that a robust-domain heuristic is proven necessary or safe. `PitchPlot.tsx`, `SentenceToneGraph.tsx`, `sentenceToneGraph.ts` and all mobile tests remain unchanged by this pass.
