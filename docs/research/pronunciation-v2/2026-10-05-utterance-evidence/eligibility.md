# Acoustic eligibility, presence and comparison permission

**ACOUSTIC ELIGIBILITY != PERMISSION TO GIVE LEARNER FEEDBACK.**

Three separate gates:

1. **Speech presence**: the existing audio/presence service decides whether a recording is accepted as speech. This pass leaves it unchanged.
2. **Acoustic interpretation eligibility**: within an accepted/timed projection, does the available pitch evidence support describing a broad whole-region gesture? `PitchInterpretationEligibility` is purely acoustic/timing data. It neither asserts speech ownership nor proves that Praat chose the right octave.
3. **Learner comparison permission**: presence, real timing, eligible observation and allowed reference must all be trustworthy. `tone_comparison_policy=experimental` remains separate from eligibility, and mobile emits only `uncertain`. An eligible diagnostic is not permission to display consistent/different.

The implementation **keeps these gates separate and retains healthy acoustic observations**. Sufficient observations remain acoustic descriptions. Comparison remains disabled.

## Generic rule and limits

No character, pinyin, lexical/surface tone, reference or target enters the rule. It counts native raw voiced frames, final selected frames, raw/selected extents, retention, early/middle/late retention over the **raw voiced extent**, largest selected island, gaps, lost head/tail and raw jumps. It preserves candidate strengths and high-pass disagreement for inspection but introduces no new candidate-selection or repair algorithm.

The local rule uses these explicit, provisional thresholds:

- Fewer than 12 selected frames or no contiguous selected island of at least 120 ms: insufficient.
- Lost raw-voiced head/tail at least max(50 ms, 20% of raw voiced extent): incomplete.
- Selected/raw retention below 70%, or any raw-extent third retaining below 50%: incomplete.
- Raw adjacent-voiced jumps above 6 semitones over at most 120 ms, or missing raw/selected gap above 80 ms: unstable when not already insufficient/incomplete. All reasons remain recorded, even when another state takes precedence.
- Native raw history absent: insufficient; legacy energy-gated history cannot establish pre-filter completeness.
- Otherwise: sufficient **local acoustic support**. The existing classifier may still abstain for ambiguity/quality. This is not a pronunciation score, voice detector, universal estimator-validation claim or a tuned expected-tone template.

Unvoiced initials and margins do not count as lost evidence: completeness is relative to acoustic raw voicing, not a grapheme's entire duration. All three temporal thirds and attrition are inspectable; a gap is never filled. Existing downstream classifier core checks remain stricter in some cases. This can conservatively suppress useful recordings; it does not prove rejected raw pitch was valid.

## Repeated 苹: no repair

Extents below are first/last existing voiced timestamps, not invented interval boundaries. The rule distinguishes lost late evidence from a measured level gesture.

| Take | Raw voiced extent | Selected extent | Early / middle / late retained | Raw→selected | Largest island | Previous | Eligibility | Resulting gesture | Comparison |
|---|---|---|---|---|---:|---|---|---|---|
| take_1 | 2.4239–2.7839 s | 2.4239–2.6239 s | 100.0% / 66.7% / 0.0% | 28→21; 25.0% lost | 210 ms | Level-like | incomplete | Unclear | uncertain |
| take_2 | 1.7237–1.9937 s | 1.7337–1.9737 s | 90.0% / 55.6% / 77.8% | 28→21; 25.0% lost | 140 ms | Rising | sufficient | Rising | uncertain |
| take_3 | 2.9934–3.3434 s | 2.9934–3.1934 s | 100.0% / 75.0% / 0.0% | 26→21; 19.2% lost | 210 ms | Level-like | incomplete | Unclear | uncertain |

Takes 1/3 lose the final 160/150 ms of raw voiced evidence; late retention is zero. Their raw paths also contain 90/100-ms missing gaps, preserved as additional reasons. Neither has a >6-st adjacent raw jump in this window. Take 2 retains late support, has a 40-ms selected gap and maximum raw jump 1.45 st; its rising observation remains available. **The other takes are not “repaired to Rising.”** They lack evidence for a whole-region level-like interpretation.

## 一 / 州 / 吧

| Recording / region | Raw→selected | Largest island | Max raw jump | Eligibility | Result / reasons |
|---|---:|---:|---:|---|---|
| take_1 / 一 | 17→17 | 90 ms | 11.84 st | insufficient | Unclear; too_little_sustained_evidence, raw_pitch_discontinuity |
| take_2 / 一 | 11→11 | 100 ms | 3.26 st | insufficient | Unclear; too_little_sustained_evidence |
| take_3 / 一 | 19→16 | 80 ms | 12.15 st | insufficient | Unclear; too_little_sustained_evidence, raw_pitch_discontinuity |
| f5dc0cc1 / 州 | 13→13 | 100 ms | 21.88 st | insufficient | Unclear; too_little_sustained_evidence, raw_pitch_discontinuity |
| f3c642b5 / 吧 | 0→0 | 0 ms | 0.00 st | insufficient | Unclear; no_voiced_support |
| e59a6350 / 吧 | 0→0 | 0 ms | 0.00 st | insufficient | Unclear; no_voiced_support |
| 209ef0c7 / 吧 | 17→8 | 80 ms | 10.40 st | insufficient | Unclear; too_little_sustained_evidence, voiced_boundary_lost, raw_to_selected_attrition, raw_pitch_discontinuity, fragmented_voiced_support |
| dccf8a63 / 吧 | 6→6 | 60 ms | 0.44 st | insufficient | Unclear; too_little_sustained_evidence |

Repeated 一 already abstained; the new diagnostics explain gaps/short islands and doubled-branch jumps. Historical 州's **21.88-st jump is explicitly identified**. Its primary state is insufficient because the largest island is only 100 ms; `raw_pitch_discontinuity` retains the instability evidence. It is not silently declared stable, corrected, or relabeled to match 州/T1. All raw and selected samples remain inspectable.

## Healthy retention and broad replay

The fixed saved-production replay contains **152 regions across 35 existing recordings** (29 captures and six negative controls); no tracker benchmark was rerun. Baseline character intervals and observations come from the saved capture-robustness replay, with frozen diagnostic windows as fallback. Whole-waveform negative/untimed diagnostic spans are explicitly labeled and are not learner character boundaries. Record IDs, audio hashes, intervals, source indices, before/after observations and metrics are in `replay.json`.

| Set | Regions | Before classifiable | Acoustically sufficient | After classifiable |
|---|---:|---:|---:|---:|
| All saved regions | 152 | 52 | 71 | 37 |
| Speech captures | 140 | 50 | 70 | 37 |
| Negative-control regions | 12 | 2 | 1 | 0 |
| Named healthy human 苹 + two healthy 要 | 3 | 3 | 3 | 3 |

Healthy human 苹 remains Rising; `5ca771a7` 要 remains Falling; `484e80c0` 要 remains Level-like, independent of its reference. These three named controls retain 3/3 useful observations. Coherent rising/falling unit controls retain 2/2; coherent 54/60/70-Hz unit controls retain 3/3. The rule is not an all-abstain solution. However, the human-control 要 is conservatively incomplete (31→20 frames, 130-ms lost tail, 9.21-st raw discontinuity) despite its prior falling label. That loss is reported, not concealed as “healthy retention.”

Representative ordinary speech `6f56aef1` and T3-heavy `7787300e`, `c95673d3`, `a0270cee`, `02927481` are included, with all available saved regions; no target-tone success rate is computed.

## Low-F0 protection

**LOW F0 != CONTAMINATION.** The eligibility rule has no frequency floor or low-frequency-contamination veto. All **11/11 saved under-70-Hz proxy points** (54.61–66.615 Hz) remain selected, unchanged; `low-f0-replay.json` lists exact samples. These sparse proxy points are not by themselves proof of a complete syllable. Sustained coherent 54/60/70-Hz unit controls are sufficient and remain classifiable. Legacy production selection can still remove valid low pitch elsewhere: this pass makes such attrition visible and does not redesign the filter or claim to restore those samples.

## Negative-control lesson

All six negative recordings are replayed: original silence, periodic background, newest accidental silence, digital silence, stationary noise and clicks. Whole-waveform projections all abstain. Of the saved character/whole-waveform negative regions, one accidental-silence interval (saved 要 timing, 24/25 retained frames) is **acoustically sufficient**, but the existing gesture classifier remains unclear. Its previously Level-like 我 and Falling 个 now abstain because of incompleteness. Consequently the saved negative regions have 2 prior classifiable observations and **0 after gating**.

A harder scan of every available start at 120/200/400-ms widths finds **61 sufficient local windows in accidental silence**; none in the other five controls. The scan is a stress diagnostic, never invented product character timing. `negative-window-stress.json` records every admitted interval. Local periodicity/coverage cannot validate speech presence or source ownership. We deliberately retain these sufficient diagnostics instead of adding recording-ID/character-specific rejection or hiding the counterexample.

The unchanged presence replay still **accepts newest accidental silence**. It also accepts the pre-existing synthetic clicks fixture, while rejecting original/periodic silence, digital silence and stationary noise (`presence-replay.json`). Neither accepted negative can enable learner comparison: the separate comparison permission remains experimental. Presence acceptance is therefore still the next product blocker; no local eligibility threshold is being asked to solve it.

## Backend and mobile gates

Perceived and target paths apply `gate_observation`: anything other than sufficient becomes unclear/low with `pitch_evidence_<state>`, retaining diagnostic features and visual fragments. Old perceived responses without eligibility also abstain without rewriting stored JSON. Sufficient support does not force a shape; all existing classifier abstentions remain.

Mobile consumes the backend eligibility and observed gesture; it no longer repeats contamination/gap/tracker-instability tests. `toneGestureMatch` leaves **every** comparison uncertain under the experimental permission policy, including sufficient Rising/T2 or Falling/T2. Incomplete detail says “Observed pitch: Incomplete evidence”; unstable detail says “Pitch tracking: Uncertain.” The character, lexical/reference pronunciation, grouped word span, More Detail and Raw remain visible. No new pronunciation grade is emitted.
