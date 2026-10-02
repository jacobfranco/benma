# Blind acoustic observations

No correctness judgments. Missing pitch is not proof of absent voicing.

| Region | ms | RMS | Saved F0 usable/total | Longest run frames | Formants | Prefix spectrum |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | 350 | 0.0809 | 14/35 | 14 | quality_abstention | generic_prefix_available |
| R02 | 460 | 0.0413 | 0/46 | 0 | no_candidate | unresolved |
| R03 | 280 | 0.2736 | 20/28 | 19 | quality_abstention | insufficient_support |
| R04 | 90 | 0.0355 | 2/9 | 2 | no_candidate | unresolved |
| R05 | 420 | 0.2687 | 32/42 | 30 | quality_abstention | generic_prefix_available |
| R06 | 250 | 0.0314 | 0/25 | 0 | no_candidate | unresolved |
| R07 | 90 | 0.0570 | 5/9 | 5 | insufficient_support | insufficient_support |
| R08 | 430 | 0.0526 | 11/43 | 11 | quality_abstention | generic_prefix_available |
| R09 | 350 | 0.0444 | 3/35 | 2 | no_candidate | unresolved |
| R10 | 380 | 0.0387 | 0/38 | 0 | no_candidate | unresolved |
| R11 | 340 | 0.1034 | 19/34 | 17 | quality_abstention | generic_prefix_available |
| R12 | 460 | 0.0734 | 15/46 | 7 | quality_abstention | generic_prefix_available |

## Interpretation recorded before opening the key

All twelve regions contain nonzero waveform and measurable spectrum. Seven have a
candidate analysis window; five have prefix spectra with at least three complete
frames. Five have no sufficiently long saved voiced run, and one candidate is too
short for a Burg center with full support. Six regions have finite raw F1/F2/F3
estimates, but **zero accepted formant summaries**. A failed feasibility filter is
not evidence of an incorrectly pronounced vowel. All six attempted regions have
zero adjacent jumps among passing frames; five fail the passing-fraction guard,
and R12 has only two passing frames. R03 and R08 also have fewer than three passing
frames. Consequently, calling every abstention "unstable formants" would be wrong.

R08 has five existing tracker-instability frames. R03, R05 and R12 retain wide
selected-F0 ranges, despite having no existing instability flag. Preserve these
values and flags exactly: no new pitch filtering or correction was performed.
All crops have zero near-full-scale samples under the existing 0.98 indicator.

Measured observation is not segment identity or pronunciation correctness. A
prefix before the longest voiced candidate may contain earlier voicing. Missing
F0 may reflect tracker/gate failure, boundaries, noise or unvoiced sound; this pass
does not distinguish those causes. No independent phonetic listening annotation
has been completed. Two representative plots were visually checked for rendering;
that check does not validate acoustic segmentation or phonetic identity.
