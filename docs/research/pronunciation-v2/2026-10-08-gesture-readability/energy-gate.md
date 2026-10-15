# Energy gate: exact cause and bounded decision

**Decision C: one specific energy question remains.** The eight late estimates
cannot yet be distinguished confidently as low-energy phonation versus periodic
background/subharmonic evidence. The production threshold and every saved selection
remain unchanged. The corresponding checkpoint is **ENERGY GATE NEEDS ONE SPECIFIC
REFINEMENT**, referring to evidence discrimination before any gate change, not a
proven defect requiring a lower threshold.

## Exact semantics

The Praat adapter first estimates a text-independent path on the entire canonical
waveform. Its Benma energy gate then uses:

```text
energies = RMS of 40 ms waveform windows at 10 ms steps
floor = tenth percentile of energies
threshold = max(0.003, min(3 * floor, 0.15 * max(energies)))
admit at energy stage only if raw F0 exists and centered 40 ms RMS >= threshold
```

This mixes an absolute floor with utterance-relative noise/peak measurements.
It uses neither syllable identity, lexical/neutral tone, expected surface tone,
target, utterance median energy, nor a per-unit loudness normalization. The peak
cap prevents continuous quiet speech from making its own noise floor too demanding;
the absolute floor can still reject sufficiently quiet speech. Its stated purpose
is suppressing periodic background evidence. Quality and display gates run separately.

For `89cee47e`: floor **0.002322822686988702**, peak-window RMS **0.06554961113327316**,
three-floor term **0.006968468060966106**, peak cap **0.009832441669990975**.
The three-floor term determines the threshold. Recomputing from canonical PCM
reproduces it to 1e-12 without running any pitch estimator.

## All eight raw 个 estimates

All eight are tracker-voiced, `energy_gated=true`, `f0_hz=null`, and have no selected
pitch. The native high-pass comparison also has no voiced estimate for these
frames. A stored disagreement of zero with a missing comparison is **not** evidence
that two estimates agree. All eight fail `below_energy_gate`; the downstream
`missing_or_out_of_range_f0` reason reflects the already-null gated value.

| Time / source index | Raw Hz | RMS | Previous / next RMS | Canonical peak | Strength | Unit position |
| --- | --- | --- | --- | --- | --- | --- |
| 2.9404 / 291 | 56.353 | 0.003220 | 0.003920 / 0.003382 | 0.007965 | 0.6749 | 0.668 |
| 2.9504 / 292 | 56.057 | 0.003382 | 0.003220 / 0.003568 | 0.009979 | 0.7348 | 0.701 |
| 2.9604 / 293 | 56.118 | 0.003568 | 0.003382 / 0.003598 | 0.009979 | 0.5810 | 0.735 |
| 2.9704 / 294 | 55.551 | 0.003598 | 0.003568 / 0.003935 | 0.009979 | 0.5959 | 0.768 |
| 2.9804 / 295 | 54.238 | 0.003935 | 0.003598 / 0.004018 | 0.009979 | 0.6558 | 0.801 |
| 2.9904 / 296 | 53.941 | 0.004018 | 0.003935 / 0.003742 | 0.008484 | 0.5441 | 0.835 |
| 3.0004 / 297 | 69.451 | 0.003742 | 0.004018 / 0.003657 | 0.008484 | 0.5985 | 0.868 |
| 3.0104 / 298 | 70.350 | 0.003657 | 0.003742 / 0.002973 | 0.008331 | 0.5849 | 0.901 |

RMS is linear full-scale PCM amplitude, not loudness or confidence. The table's
neighbor RMS values are immediately preceding/following saved frames. Canonical
40 ms RMS matches the saved six-decimal values within 1e-6. Position is time since
accepted onset / 0.30 s; it is not an interpretation score.

The first six native estimates drift 56.353→53.941 Hz, then jump to 69.451 Hz
by **4.3754 st**, followed by 70.350 Hz. There are only 80 ms of nominal frame
support (70 ms between centers), far short of proving a sustained syllable gesture.
Autocorrelation strengths 0.5441–0.7348 indicate some periodic structure but do not
identify its source. Missing high-pass support alone cannot disqualify real 54 Hz
speech because that diagnostic filter attenuates frequencies below 70 Hz.

## Canonical waveform cross-check

The 2.78–2.89 s louder part of 个 has RMS **0.011785**, peak amplitude **0.041351**,
and the accepted unit has **12** saved frame centers above the energy threshold,
yet none of those centers has native voiced F0. Therefore lowering this gate
cannot recover F0 from the main audible part.
The 2.94–3.02 s raw-voiced tail has RMS **0.003656**, peak **0.009979**, and about
0.589 of its 40–4000 Hz spectral energy in 40–80 Hz. Pre-speech RMS is 0.002253;
post-speech RMS is 0.004579. These are waveform context measurements, not a new
tracker or a speech/voicing ground-truth label. The 80 ms tail spectrum has only
12.5 Hz resolution and cannot resolve reliable harmonic ownership on its own.

The user's audible 个 establishes that speech is present in the accepted interval.
It does not establish that the weak late periodicity is vocal F0. Classification
for this take is **mixed/ambiguous (C)**. Neither “the gate is certainly correct”
nor “neutral syllables are being incorrectly removed” is supported.

## Controls and raw-versus-selected evidence

The audit covers 57 accepted units (the 53 projection units plus four saved legacy
我们去吧 units) and 11 whole-recording diagnostic controls. The legacy controls
retain original timing/selection and do not claim modern immutable source indices.
Full counts, path jumps, gaps, threshold values, hashes, and provenance for every
item are in [energy-replay.json](energy-replay.json). Whole-recording windows are
explicitly diagnostic, never invented learner timing. All audio/archived evidence
is reused. No recordings or tracker results were generated.

| Control | Raw / selected | Energy rejected | Raw / selected maximum jump (st) | Interpretation |
| --- | --- | --- | --- | --- |
| a5acd04c:个 | 16 / 16 | 0 | 12.855 / 12.855 | Retained octave-like jump; not clean geometry |
| 4b9dbd2b:个 | 22 / 22 | 0 | 0.707 / 0.707 | Useful coherent neutral contour |
| 8d252264:个 | 10 / 9 | 1 | 0.310 / 0.310 | Sparse conflicting register fragments |
| 89cee47e:我 | 41 / 41 | 0 | 1.905 / 1.905 | Useful strong retained control |
| 89cee47e:个 | 8 / 0 | 8 | 4.375 / 0.000 | Ambiguous weak tail; no safe recovery proven |
| 8faf1a90:个 | 32 / 31 | 1 | 0.361 / 0.361 | Useful coherent neutral contour |
| fe8c8279:们 | 16 / 16 | 0 | 0.414 / 0.414 | Coherent short neutral evidence retained |
| fe8c8279:吧 | 6 / 6 | 0 | 0.442 / 0.442 | Only 60 ms raw support; gate rejected none |
| human_control | 204 / 102 | 99 | 13.264 / 3.599 | Gated background/tail plus retained speech; no whole-file quality label |
| google_old | 253 / 146 | 88 | 29.092 / 2.405 | Known path/discontinuity issues remain |
| silence_accidental | 279 / 76 | 195 | 31.860 / 14.800 | Known nonspeech; existing false pitch survives |
| silence_original | 0 / 0 | 0 | 0.000 / 0.000 | Correctly unavailable |
| silence_periodic | 148 / 46 | 75 | 2.843 / 2.107 | Known nonspeech; coherent low periodicity survives |
| neg_digital_silence | 0 / 0 | 0 | 0.000 / 0.000 | Correctly unavailable |
| neg_stationary_noise | 0 / 0 | 0 | 0.000 / 0.000 | Correctly unavailable |
| neg_clicks | 0 / 0 | 0 | 0.000 / 0.000 | Correctly unavailable |
| syn_steady_70 | 159 / 2 | 0 | 0.036 / 0.000 | Known voiced low F0; quality failure, no energy rejection |
| syn_steady_110 | 161 / 161 | 0 | 0.031 / 0.031 | Known voiced control retained |
| native_gain | 73 / 72 | 1 | 36.491 / 36.491 | Reduced-gain reference; retained pitch still has octave jumps |

For `silence_periodic`, eight consecutive rejected estimates at 0.9831–1.0531 s
range from 54.887 to 58.996 Hz, maximum adjacent jump **0.7288 st**, all strengths
above 0.52 and all other saved quality flags usable. Thus coherence plus moderate
periodicity would admit a known nonspeech counterexample. `silence_accidental`
also has a rejected 80 ms run with maximum jump **0.1081 st**, strengths ≥0.8204;
its low-frequency quality flags reject it independently. Neither is proof that
this 个 is noise; both prevent claiming that a coherence-only relaxation is safe.

The known 70 Hz synthesized voiced control has **159 raw estimates, zero energy
rejections, and two selected points**; the separate low-frequency quality/display
policy removes its interior. The 110 Hz control retains 161/161. These results
are read from the existing study, not rerun. We do not misattribute a known low-F0
quality failure to energy gating or “protect” low F0 by suppressing the inconvenient
negative controls.

The clean neutral 个 controls retain 22/22 and 31/32 raw points; 们 retains 16/16.
吧 retains only six estimates with zero energy rejections: limited voicing there
comes from the tracker, not the energy gate. A saved reduced-gain reference retains
72/73 raw estimates, with one energy rejection, but has octave jumps; lower volume
does not itself certify or invalidate a path. Strong 我 retains 41/41.

Evidence therefore does **not** establish systematic disproportionate rejection of
neutral, short, final, or low-F0 speech. Absolute/relative thresholds can reject
quiet speech in principle, and the physical 个 is concretely energy-excluded, but
this small observational corpus has no independent voiced-F0 labels for weak tails
and cannot estimate class-specific false-rejection rates. Audible voiced duration
is recorded as unavailable rather than invented from tracker counts. The current
graph is useful for clean controls; absence is appropriate for known unvoiced
negatives; the physical weak 个 remains unadjudicated. There is no earned local
or lexical exception and no global threshold reduction.
