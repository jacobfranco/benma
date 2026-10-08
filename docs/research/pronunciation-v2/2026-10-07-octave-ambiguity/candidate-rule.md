# Candidate-aware rule: tested and rejected

The experiment lives only in `benchmark/pronunciation_v2/octave_ambiguity.py`. Production does not import it. It consumes frozen acoustic frame dictionaries, never text, intended targets, characters, pinyin, expected tones or reference contours.

## Definition and local context

A frame is a research `octave_candidate_ambiguous` exclusion only when:

1. It is already selected by current production.
2. A measured alternative is within **1 semitone of ¼×, ½×, 2× or 4×** its selected frequency. Arbitrary integer harmonics or octave-shifted invented frequencies are not alternatives.
3. The alternative has strength **>=.45** and selected-minus-alternative strength **<=.25**. A stronger alternative is permitted. These are candidate periodicity strengths, not correctness probabilities.
4. The alternative is within **3 st** of the local robust prediction and improves absolute log-frequency residual by **>=6 st** on every available stable side.
5. The selected branch lasts **<=120 ms**, including one hop. A long branch cannot be cut into short pieces merely because only some of its frames pass the candidate test.

Selected branches are grouped until a >6 st change or >45 ms separation between surviving measurements. This permits small missing intervals for diagnostic grouping; it never joins display lines or fills a gap. Context uses the nearest previous/following branch, at most its five nearest measurements. All five must be contiguous source indices, with <=45 ms adjacent steps and <=2 st total spread. The predictor is the median adjacent semitone slope plus median centered intercept. Every tested frame must be within 120 ms of each context edge. No sophisticated fit, absolute human pitch range or language assumption is used.

One stable side is sufficient when the other side is unavailable or incoherent. At a true utterance boundary with no stable context, abstain. If both sides supply stable predictions, both must support the alternative. This conservative agreement requirement deliberately leaves F1/F2 unresolved; selecting whichever side gives the desired answer would need separate safety evidence. Near a gap, A1's 55 Hz samples can still be evaluated from bounded surrounding context. Candidate-poor 59–60 Hz samples remain selected; the rule never extends a rejection to them by analogy alone.

Contiguous passing frame indices form ambiguity runs. The **complete-run variant** additionally requires every selected frame in the short branch to pass the same test. This prevents carving the last sample out of a coherent low register run when only that sample has a credible alternative. It is evaluated as a stricter version of the same experiment, not introduced as an additional production rule.

The four tunable dimensions are ratio tolerance, strength margin, residual advantage and run duration. Context size/bounds, 3 st alternate residual and the existing .45 credibility floor are fixed design constraints, not secretly tuned per file.

## Small parameter neighborhood

Nine settings were evaluated one at a time; no grid search, optimization against characters or corpus relabeling occurred.

| Setting | Difference from central | Physical frame exclusions | Complete-run exclusions | Protected low-F0 loss |
| --- | --- | ---: | ---: | --- |
| Central | 1 st / .25 margin / 6 st advantage / 120 ms | 7 | 4 | 54.610 Hz at 2.5124 s |
| Ratio low / high | .75 / 1.25 st | 7 / 7 | 4 / 4 | Same in both |
| Margin low / high | .20 / .30 | 7 / 7 | 4 / 4 | Same in both |
| Advantage low / high | 5 / 7 st | 7 / 7 | 4 / 4 | Same in both |
| Duration low / high | 100 / 140 ms | 7 / 7 | 4 / 4 | Same in both |

The selected physical frame sets are identical across all nine settings, not just their counts. Complete-run agreement loses **zero** protected samples across all nine. Both the failure and the conservative variant's inadequate recall are stable in this neighborhood. Exact per-setting indices are in [replay.json](replay.json).

## Decisive low-F0 counterexample

The existing protected `7787300e` run is 55.853 → 55.288 → 54.773 → **54.610** Hz at 2.4824–2.5124 s. It is followed by 107.282 → 105.687 → 103.845 → 101.830 → 99.965 Hz. The final low frame's measured 108.620 Hz alternative has strength .7776 versus selected .8415: margin **.0639**, ratio **1.9890**, octave error **.0954 st**, trajectory residual **.1313 st**, advantage **11.9046 st**. It satisfies the proposed ambiguity test more comfortably than several new artifacts.

This sample was previously protected as valid human low-F0 evidence. That acceptance criterion is binding. It is not relabeled an error now because an algorithm finds a better-looking doubled trajectory. The local spectrum also favors energy near 109/216 Hz, demonstrating that “strong doubled spectral peak” is not a safe escape from the counterexample.

Making the margin <.0639 or the octave tolerance <.0954 st would exclude many physical candidates and amount to fragile tuning. Requiring both clean sides loses the onset/gap behavior the pass needs. Requiring complete-run support preserves this sample, but also preserves A1's candidate-poor low branch and the sustained B4 branch. The failure is structural, not a knife-edge cutoff.

## Safety controls

All **49** existing production snapshots were replayed without another estimator or audio re-extraction. Production retained timestamps matched every frozen snapshot. All **617** protected low-register sample times across 18 recordings were selected before the experiment. Ten are explicitly protected below 70 Hz (54.610–66.615 Hz). Frame-rule retention becomes **616/617**, including **9/10** of those lowest points. Complete-run retention stays **617/617 and 10/10**. This is the production integration veto.

| Control | Current selected frames | Frame-rule exclusions | Complete-run exclusions | Interpretation effect |
| --- | ---: | ---: | ---: | --- |
| Synthetic steady 70 Hz | 2 (159 raw voiced) | 0 | 0 | Existing spectral quality gate already excludes most of this synthetic signal; this pass neither fixes nor hides that historical limitation. No additional loss. |
| Saved healthy synthetic rise / fall | 161 / 161 | 0 / 0 | 0 / 0 | Full selected movement preserved. |
| Deterministic 55→220 Hz sweep and its reverse | 61 / 61 input frames | 0 / 0 | 0 / 0 | Two-octave coherent movement survives even with close octave candidates; no new audio collection. |
| Old suspicious 州 `f5dc0cc1` | 28 | 0 | 0 | Insufficient / unclear remains. |
| Google low/subharmonic failure `google_old` | 146 | 0 | 0 | Both saved diagnostic intervals remain insufficient / unclear. |
| Clean 苹 `take_2` / `human_control` | 131 / 102 whole-recording frames | 0 / 0 | 0 / 0 | Named clean interval stays sufficient / rising (experimental `2-like`). |
| Incomplete 苹 `take_1` / `take_3` | 177 / 185 | 0 / 11 | 0 / 0 | Named incomplete interval stays incomplete / unclear. Other take-3 frame removals do not rescue it. |
| Sparse 吧 `f3c642b5` | 27 | 0 | 0 | Insufficient / unclear remains. |
| Original silence | 0 | 0 | 0 | Unchanged. |
| Periodic / accidental silence | 46 / 76 | 0 / 0 | 0 / 0 | Existing false-pitch islands remain; this pass makes no presence claim. |
| Saved digital silence / stationary noise / clicks | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | Unchanged. |

The frame rule removes 30 frames across all 49 historical snapshots, including the protected false rejection. The complete-run variant removes zero historical frames. Full per-recording changes and interval results are preserved in the replay file; unannotated historical removals are not asserted to be improvements.

The 16 focused research checks cover half/double/quarter branches, four-frame runs, small gaps, bounded one-sided evidence, distant gaps, no credible alternative, long-run duration enforcement, coherent 55–70 Hz, both sweep directions, raw immutability, metadata independence, grouped indices, incomplete eligibility and the real counterexample. The counterexample test **passes by proving the experimental rule fails the acceptance criterion**; it is not a product-safety pass.

## Raw, selection, eligibility and classification

Research replay copies the frozen track, sets only selected Hz/display availability/reason on excluded indices, and recomputes display baseline and median smoothing within surviving segments. It never replaces an F0 with a candidate. It never reruns old filters on changed neighborhoods, preventing hidden cascade attrition. Every frame's raw/analyzer/energy-gated/candidate/provenance data is asserted unchanged, and surviving selected Hz must exactly equal previous selected Hz. Source timestamps and projection indices stay exact.

Material removal leaves missing support relative to raw, rather than changing the denominator to surviving evidence. The existing eligibility logic already flags raw jumps, selected attrition, boundary loss and fragmented support. No previously non-sufficient saved diagnostic interval becomes sufficient in either experiment. Geometry is selected-only; raw jumps can still veto confidence. The test of a materially removed tail remains incomplete, and `gate_observation` suppresses classification.

Nothing is wired into production, so no experimental exclusions reach live Mine, Detail, gesture classification or comparisons. The existing Raw view and immutable saved runs are unchanged. A future accepted rule would need a versioned selection contract/reuse decision and its explicit acoustic reason; it must not retroactively alter old saved tracks. This pass deliberately does not perform that integration after failed acceptance.
