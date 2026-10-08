# Low-register safety and false vocal pitch

## Final RMVPE extension

RMVPE improves low-register retention: **617/617** protected proxy samples and **11/11** lowest samples survive raw and gate .05. Of the lowest eleven, eight agree near 55.4/58.25 Hz; three in `7787300e` are **111.42 Hz versus baseline 54.77 Hz**. These are baseline-relative disagreements, not independently certified real F0 errors. All 113 marked clear low-voice frames and the synthetic 70-Hz control survive. The broader low-proxy cohort has three upward octave disagreements and no missing frames.

False voicing still blocks migration: **374/1947 raw → 326/1947 gated negative frames**. Original/periodic/accidental controls emit 103/111/160 raw frames, with longest runs .87/.70/.93 seconds. At .05 they retain 98/75/153 frames; original and accidental confidence reaches .842/.947. All three synthetic negatives have zero pitch. Marked long-recording pauses retain 34/305 raw and 23/305 gated frames.

The sole predeclared sweep (.01–.05) leaves 496/424/374/358/326 negative frames, while retaining all 617 protected and 329 coarse harmonic-core samples at each value. There is no safe nearby operating region. The .05 viewer view is a rejected safety strategy, not a recommended production gate. [RMVPE report](rmvpe.md), [sweep](rmvpe-threshold-summary.csv) and updated [safety tables](safety-tables.md) provide the six-tracker evidence. The five-tracker narrative below is retained history.

**None of the five configurations establishes a safe foundation across both low human F0 and known no-speech recordings.** pYIN's cleanup is the cleanest on negatives but removes too much real weak/low evidence. CREPE improves several speech trajectories but retains confident background and loses almost all of the smallest protected low-register subset. Harvest over-voices heavily. Praat retains low-register evidence but selects wrong branches elsewhere and still voices periodic background.

## What is and is not known low-F0 truth

The previous audit's protection proxy is replayed unchanged: baseline AC F0 below 100 Hz, strength ≥.8, high-pass F0 agreement within .5 st, retained by production, and inside a previously observed speech time region. This yields **617 frames in 18 recordings**. Prior time regions identify existing evidence only; they do not enter any tracker or the shared cleanup.

This is **baseline-selected evidence**, not independent ground truth. AC/production retention on this cohort is favorable by construction. Some lowest-frequency frames may be irregular phonation or subharmonics; disagreement does not prove another tracker wrong. Equally, discarding them cannot be advertised as fixing the Google/TTS low branch without establishing they are invalid. The tiny **11-frame ≤70-Hz subset** across three recordings is a safety countercheck, not a population error estimate. The known 70-Hz synthetic separately establishes an actual production-filter false rejection.

| Tracker/view | Finite /617 proxy frames | >9-st upward disagreements | Finite /11 lowest frames | >9-st upward disagreements in lowest subset |
| --- | --- | --- | --- | --- |
| AC raw/minimal/production | 617 | 0 | 11 | 0 |
| CC raw/minimal | 617 | 0 | 11 | 0 |
| pYIN raw | 606 | 1 | 1 | 1 |
| pYIN minimal | 450 | 0 | 0 | 0 |
| Harvest raw/minimal | 614 | 3 | 8 | 3 |
| CREPE raw | 617 | 8 | 11 | 8 |
| CREPE minimal | 578 | 1 | 1 | 1 |

Finite coverage is not automatically usable coverage: the final column exposes cases where retained evidence occupies the wrong octave relative to the protected baseline. [low-f0-proxy.csv](low-f0-proxy.csv) reports each recording/tracker/view's median Hz, confidence, upward/downward disagreements, missing frames through coverage, island count and longest run within eligible proxy timestamps. Missing intervals are never bridged. [low-f0-under70.csv](low-f0-under70.csv) isolates the three lowest cases.

The three lowest baseline medians are ~54.77, 55.58 and 58.33 Hz. CC agrees closely. pYIN retains only one raw ~107.18-Hz frame, then none after cleanup. Harvest retains the five ~56-Hz `c95673d3` samples but doubles the three `7787300e` samples and misses the three `27ea3b92` samples. CREPE's sole cleaned lowest-subset frame is ~108.88 Hz. Its native confidence medians over these three subsets are approximately .118, .000000657 and .0131 respectively. Rejecting these is not demonstrated low-register safety.

An independent coarse visual check on **113 clearly harmonic low-voice frames** in long `7787300e` is less extreme: raw AC/CC cover 109, other trackers 113, all in broad ~70–135-Hz support bands. Cleanup preserves 109 AC/CC, 89 pYIN, 113 Harvest and 105 CREPE. Thus the low-register concern is not solely a proxy-selection artifact: the same cleanup loses 24 visibly supported pYIN frames and eight CREPE frames. These manually reviewed cores remain approximate spectral annotations, not exact F0 labels.

## Whole-recording negatives

All emitted F0 in the three known no-speech recordings and three generated negatives is counted as unsafe **vocal** evidence. A periodic machine/background can have a physical pitch; the concern is presenting it as the learner's voice. Counts remain on native grids.

| Tracker | All negative raw frames / total | Raw fraction | Minimal frames / total | Minimal fraction | Could a learner graph mistake this for voice? |
| --- | --- | --- | --- | --- | --- |
| AC | 427/1911 | 22.3% | 418/1911 | 21.9% | Yes, strong periodic/accidental background islands |
| CC | 471/1923 | 24.5% | 457/1923 | 23.8% | Yes, similar or more background |
| pYIN | 670/1947 | 34.4% | 39/1947 | 2.0% | Raw yes; clean still has accidental-background islands |
| Harvest | 1075/1947 | 55.2% | 1073/1947 | 55.1% | Yes, long apparently usable paths |
| CREPE | 1947/1947 | 100% | 289/1947 | 14.8% | Yes, both continuous raw paths and confident clean fragments |
| AC production | 122/1911 | 6.4% | — | — | Yes, residual periodic/accidental islands |

Every negative's emitted count/fraction can be recovered from [safety-tables.md](safety-tables.md) and [per-recording-metrics.csv](per-recording-metrics.csv); confidence median/max, median Hz, longest run and islands are included.

| Real negative | AC clean | CC clean | pYIN clean | Harvest clean | CREPE clean |
| --- | --- | --- | --- | --- | --- |
| Original hallucinated silence | 0 | 0 | 0 | 539/679, longest 1.46 s | 116/679, longest .60 s |
| Periodic-background silence | 139/345 | 176/347 | 0 | 188/351 | 36/351 |
| Accidental-silence false accept | 279/308 | 281/310 | 39/314 | 304/314, longest 2.54 s | 137/314, longest .27 s |

CREPE retained periodicity median/max is **.598/.906** on original silence, **.435/.648** on periodic silence, and **.750/.949** on accidental silence. These overlap or exceed supported-voice confidence. A single monotone confidence threshold therefore does not cleanly separate these backgrounds while protecting the observed weak low-register samples. Raising the threshold above the negative maximum would further reject already-low-confidence vocal evidence. No unmeasured threshold is recommended as a solution.

pYIN's remaining accidental-negative confidence median/max is .177/.827 and longest run .12 s. Its .1 gate removes original/periodic controls but costs much real speech. Praat clean accidental-background strength reaches .998, again showing that periodicity is not a vocal-presence probability. Harvest supplies no comparable confidence in its public output.

On generated digital silence, stationary Gaussian noise and clicks, AC/CC/pYIN emit zero frames. Harvest emits 37 noise and five click frames, retained by cleanup. CREPE emits all 201 frames in each raw generated negative and zero after cleanup. That easy success does not generalize to the real backgrounds. On the known synthetic noise gap, CREPE likewise goes from 40/40 false-pitch frames to zero while retaining voiced core evidence.

## Pauses inside real speech

The manually selected stationary pauses in `7787300e` contain 305 native query frames. Raw/minimal false vocal pitch counts are AC **20/18**, CC **35/33**, pYIN **25/0**, Harvest **87/87**, CREPE **305/52**. AC production removes all 20. CREPE's cleaned pause confidence reaches .836. These pauses show the same pattern within a speech recording, rather than only on whole negative files.

## Safety conclusion

Raw CREPE and Harvest cannot be judged by attractive continuity. pYIN's lower false pitch is useful but insufficient given missing clear voice, failed lowest-register protection and weak-fundamental doubling. AC/CC remain valuable low-register diagnostics, but their own strength is not safe vocal confidence. Current production filtering suppresses much background at the cost of some valid evidence—including every evaluated synthetic 70-Hz frame. These results support neither a naive confidence-only migration nor a multi-tracker ensemble.
