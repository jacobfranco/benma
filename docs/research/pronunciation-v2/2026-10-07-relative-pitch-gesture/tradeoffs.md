# Semantics and unchanged evidence boundaries

## Default-view decision

**ABSOLUTE UTTERANCE F0 SHOULD REMAIN DEFAULT for this checkpoint.** This is a decision to leave production unchanged after outcome B, not a finding that the existing view is satisfactory. The desired product goal—showing a user's locally measured gesture—is reasonable, and whole-unit relative centering satisfies its mathematical contract. The six-take result does not satisfy the physical acceptance contract, especially the confirmed exaggerated U-shape take.

A future locally centered Mine would need a small **“Relative pitch”** label: current “Your pitch” plus an unlabeled vertical axis does not explain why a 369 Hz unit and a 51 Hz unit both center near zero. Existing More Detail's recording-relative wording describes a different baseline. If this projection were integrated, a brief detail explanation of independent unit centers would be warranted. No default UI copy or surrounding UI was changed for this rejected prototype.

The intentional information loss is **between-unit absolute register**: a whole syllable spoken in genuine falsetto may have the same default shape as a low syllable. Relative 0 is each unit's median, not a common physical frequency or expected tone. Within-unit amplitudes retain a common semitone scale. All independently centered units must be disconnected. A trusted group has one center and can retain continuity inside its original selected segments.

This is a **relative measured contour** or **relative pitch gesture**. It is not corrected pitch, normalized pronunciation, octave correction or denoised F0. A coherent wrong tracker branch can look benign after centering; therefore a scale improvement must not be described as better acoustic correctness.

## More Detail and Raw

**More Detail remains the same unsmoothed selected absolute F0 over actual time.** The production plot expresses it in semitones relative to one fixed recording baseline; “absolute” here means original selected frequencies and absolute inter-unit register relationships are preserved, not that the UI currently labels the axis in Hz. No local centering is applied to `tone_graph.filtered`. The diagnostic viewer includes both an absolute-Hz selected plot and the original filtered-semitone plot.

**Raw remains raw tracker evidence.** Native tracker Hz (legacy stored-Hz fallback where needed), retention, original time, source index and exclusion reasons are unchanged. The production Raw display uses recording-baseline semitones with isolated dots. The diagnostic viewer uses original tracker Hz for direct numerical inspection and leaves excluded values visible in gray. Full candidates and provenance remain available in `UtterancePitchTrack`; current mobile Raw does **not** expose every candidate. This pass adds no candidate/public-schema expansion.

Saved input JSON is checked for mutation around replay, frozen evidence IDs are matched, and source hashes are recorded. The actual mobile helper runs against cloned display containers and verifies unchanged original input. No database write occurs.

## Eligibility and confidence

Eligibility is not an input to centering and is never recomputed from relative display points. Existing raw-support completeness, selected retention, missing head/tail, fragmentation and raw discontinuity semantics remain authoritative. The prototype does not erase an unstable/insufficient line just to improve its domain, and does not turn a centered trace into confidence.

For the primary U take, 买 and 雨伞 remain `unstable`; 把 remains `insufficient`. In `8d252264`, 要 remains `unstable`, 个 `insufficient`, and 果 `sufficient`. The last state means that selected support is locally complete enough; it is not proof that the high tracker branch is correct. `a5acd04c` 有/个 remain `unstable`.

A focused research test replays all **30** accepted physical units with their frozen tracks. Existing eligibility results are unchanged; changing the presentation contour supplied to `classify_contour` to an empty contour leaves the acoustic observation identical. This exercises the existing separation rather than modifying it. Learner correctness comparison remains disabled/uncertain through the unchanged production path.

## Observed-gesture audit

The shape decision is already effectively offset-invariant when the same acoustic evidence is represented with a consistent baseline. `_classify_contour` uses median-bin differences, delta, range, minimum position, total movement, residuals, slopes, gap changes and frame ratios; it does not use an expected tone or an absolute register threshold to select level/rise/dip/fall. Absolute-valued diagnostic fields such as `bin_1_st` would shift with a baseline translation, but classification thresholds use their differences. Confidence depends on evidence quality rather than display position.

The full acoustic pipeline is not claimed universally invariant under arbitrary frequency multiplication: existing extraction/selection frequency limits and quality flags still exist. The classifier's raw/display disagreement must compare consistently referenced evidence; shifting only its acoustic contour while keeping its raw baseline fixed would change that diagnostic. The prototype never does this.

Crucially, public `classify_contour` already **discards its presentation-contour argument** and reconstructs evidence from the frozen track when supplied (or from raw evidence in the legacy fallback). Locally centered graph geometry therefore cannot influence its classification. No classifier change is necessary or made. No expected/reference tone supplies a center, domain, point, slope or label for the research geometry.

## Target/reference independence

The pure transform accepts only selected values, source identities and accepted timing. The mobile replay additionally changes target text, every character identity, pinyin, lexical tone and surface tone; group labels are changed consistently with their same character spans. `normalizedGeometry` is byte-identical before and after those metadata changes for all six recordings. This isolates the required guarantee: same **accepted acoustic timing unit** means same geometry. Altering the alignment boundaries themselves could change ownership and the median, as already architected; that is not a reference-tone effect.

## Why no integration

The specific sustained high branch stops setting global extremes, but the main U take is not materially clearer, and one take becomes more compressed. Group splitting or independently centering acoustic islands would manufacture a finer display unit than the accepted timing. Keeping ordinary relative min/max honestly exposes the residual branch failures; no clipping or second normalization is added. No mobile/API/backend production file, schema, selection rule, grade policy, or historical report changes.
