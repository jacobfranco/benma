# Eager tone-likeness — October 10 continuation

The [October 12 classification pass](../2026-10-12-learner-classification/README.md)
adds bounded completed shallow-valley and subordinate late-island paths. Its named
thresholds, physical replays and corruption controls supplement the rules below.

**EAGER TONE-LIKENESS EARNED INTEGRATION.** Choose the best Mandarin tone family
unless ambiguity is real. This is a best-fit interpretation of retained pitch,
not an independently proven lexical-tone identity or calibrated probability.

The production sequence is retained audio evidence → dominant supported measured shape →
`classifyToneLikeness` → perceived contextual expectation → learner agreement →
pitch-only status. The classifier accepts only `ShapeResult` and retained semitone
points. It has no parameter for target, characters, pinyin, expected tone, strict
eligibility, or absolute Hz. Extraction, normalization, graph measurements, timing, ownership, reading, chunk
recognition and backend production functions are unchanged.

**MEASURED SHAPE != TONE-LIKENESS.** “Dip and rise” remains the measured description
in More Details. Default observed copy is exactly “Most like Tone 1”, “Most like
Tone 2”, “Most like Tone 3”, “Most like Tone 4”, or “Tone unclear”. Empty retained
pitch instead shows “Pitch couldn't be measured reliably.”

## Dominant supported gesture

Before tone ranking, `pitchShape` can summarize a primary gesture ending at or after
72% of the retained extent, supported for at least 120 ms, with excursion ≥1.5 st.
The full smoothed tail range must be ≤25% of that primary excursion. Directional
consistency is ≥0.8 for a rise/fall, or ≥0.7 for both valley limbs. Named constants
and audit features expose primary/counter excursions and the gesture end position.
Measured endpoint/net values remain available separately. No data is trimmed from
the graph or full-track integrity checks. Endpoint/window/deletion checks rerun
the entire geometry and must preserve the family. Comparable opposing movements
cannot claim dominance. A dominant boundary fall is distinct from early-fall/low-tail
reduced T3.

## Fits and decision

All four fits are computed; they are bounded heuristic ranking values, not
probabilities and need not sum to one. Let C(x) clamp x to [0,1], F be the measured
fall, R recovery, N=R−F, E excursion, and Cf/Cr the directional consistencies.

| Family | Fit |
| --- | --- |
| T1 | 0.4 for measured LEVEL + 0.6 × C(1−E/3) × C(1−abs(N)/2) |
| T2 | 0.4 for measured RISING + 0.6 × C(N/2) × Cr × (1−C(F/max(1,R))) |
| T3 | 0.4 for DIP_RISE + 0.6 × min(C(F/1.5), C(R/1.5)) × sqrt(Cf×Cr), with an interior minimum |
| T4 | 0.4 for measured FALLING + 0.6 × C(−N/2) × Cf × (1−C(R/max(1,F))) |

An interior minimum lies between 10% and 90% of the selected extent. Thus a
dip-rise ending above its start still favors T3; net rise cannot erase a supported
descent. Small movement and large competing excursions reduce fit independently
of the shape prior. Slope, support, valley position and low-tail support are kept
with the result for audit; slope is the supported gesture net change per second,
not an additional least-squares fit or a duration-dependent scoring multiplier.

An early fall followed by a supported low tail has a bounded reduced-T3 candidate:
measured FALLING without a dominant boundary fall/rebound, minimum position 0.35–0.8, F≥1.5 st, R<1 st, Cf≥0.8, and at least
32% of all selected points lying in the final 40% of time within 0.65 st of the
contour minimum. This sets the reduced-T3 fit to at least 0.85 and discounts T4 by
0.45. It is always **weak/partial**, not independently strong correctness. “Low”
here means low within the contour, not low speaker Hz. The constructed reduced
control passes; this subfamily has not earned an independent recorded-tone accuracy
claim. Flat pitch alone remains T1-like; it cannot establish low-register T3.

The winner must have fit ≥0.45 and best–runner-up margin ≥0.12. Ties have a stable
ordering for reproducible diagnostics, but never resolve uncertainty by that
ordering. Missing features have no best/runner-up and zero fits, not four equally
likely tone probabilities. The broad classifier's six region/deletion
perturbations, support, missing-region and contradiction checks remain authoritative.
UNCLEAR broad shape always remains tone unclear. Additional ±0.1 st fall/recovery
perturbations must preserve the winner. Reduced-family winners also survive actual
endpoint/every-tenth deletion replays because their extra tail feature is not
validated merely by a stable FALLING label.

Classification strength is separate from winner confidence: net rise/fall below
2 st, or valley fall/recovery below 1.5 st, is weak but still classifiable. These
boundaries drive deterministic coaching only after contextual comparison.

## Calibration and fresh physical take

The original **53 units / 1,852 selected points** remain unchanged. All **29/29
classifiable shapes** receive a tone-family winner: T1=2, T2=3, T3=18, T4=6. The
24 unclear shapes stay unclear. The earlier 28/29 agreement with unambiguous
manual *geometry* labels and all 18 previously useful descriptions are preserved.
Those labels are not independent lexical-tone ground truth. The borderline
`4b9dbd2b:苹` still abstains under perturbation. Exaggerated `7e6b6fe9` 我/想/买 and
normal archived `89cee47e:我` all remain T3-like.

The fresh take is **separate** from `89cee47e`:

- Analysis: `e5c17b4e-64e2-47da-806a-0aaacb61ca76`
- Utterance: `4377ae29-2397-4641-bafe-abb7003ce05a`
- Saved at: `2026-10-10T15:46:50.976890Z`
- Canonical recording: `19d8333bc4e04ce4bf026e393ea1f3e7`
- Audio SHA-256: `b3e0f2964bb4a9831e008475d184fb7db3fb19b9dc2fd59f2d3547d3566d757d`

Only derived measurements/metadata were added as `toneFeedbackPhysical.json`.
The latest eight analyses were located read-only, then this exact take's canonical
metadata was read for local playback verification. No waveform was copied into
versioned files. Existing chunks-v1 derives the history-response chunk metadata
from the saved perceived readings; the saved database analysis was not rewritten.

| Fresh unit | Shape | T1 fit | T2 fit | T3 fit | T4 fit | Winner / runner-up | Margin | Grade |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 我 | Dip and rise | 0 | 0 | 1.0000 | 0.0346 | T3 / T4 | 0.9654 | Green: lexical T3 family |
| 想 | Dip and rise | 0.0483 | 0.1649 | 0.7843 | 0 | T3 / T2 | 0.6195 | Amber: lexical T3 family, shallow dip |
| 买 | Unclear | 0 | 0 | 0 | 0 | None | 0 | Gray: missing critical support |
| 这 | Falling | 0 | 0 | 0 | 0.9696 | T4 / tied-zero runner-up T1 | 0.9696 | Green |
| 个 | No retained pitch | 0 | 0 | 0 | 0 | None | 0 | Independently unavailable; non-veto neutral |

Fresh 我 has a 3.646 st descent and 2.998 st dominant recovery. Fresh 想 has a 1.033 st
descent and 2.190 st recovery. Fresh 这 has a −3.414 st net change. Poor-voice 买
has missing critical support; its lexical T3 never repairs the acoustic absence.

The complete [CSV matrix](tone-feedback-matrix.csv) and [JSON results](tone-feedback-results.json)
include geometry, all fits, best, runner-up, margin, observed label, context, grade,
color and gray reason. Corpus, fresh measurements, constructed controls and chunk
aggregates have separate provenance. No aggregate chunk is given an invented
single-tone ranking. Run `node benchmark/pronunciation_v2/tone_feedback_audit.cjs`
from the repository root; no provider, model, screenshot classification or new
audio collection is involved.
