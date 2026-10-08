# Semi-blinded acoustic review

## Final RMVPE extension

A fresh six-label key was withheld until the [initial RMVPE review notes](rmvpe-blind-review-before-reveal.md) were saved and hashed. Thirteen raw panels were inspected. Reveal: A RMVPE, B Harvest, C pYIN, D CREPE, E AC, F CC. Notes recognize A's improved difficult paths and its substantial negative/background pitch and weak-fundamental octave switching. The same assistant already knew the five candidate families and earlier trajectories, so identities could be inferred; this is semi-blinded, not an independent expert panel. No new support windows, lexical-tone scores or listening claims were introduced. [Receipt](rmvpe-blind-review-receipt.json), [final interpretation](rmvpe.md).

The original five-label review below is preserved history.


The original plots use **Tracker A–E**. Initial observations were written to `blind-review-initial.txt` before the key was opened; that file is preserved unchanged in the local artifact set. The reviewer was the assistant that implemented the adapters, knew the five families, and could infer some identities from behavior. This is a **semi-blinded visual review**, not an independent expert annotation or listening panel. Browser audio decoding/playback was checked; no human listening study was performed.

Review used whole-file waveform, elapsed-time spectrogram, native F0 and native confidence. It examined harmonic support, real gaps, octave branches and weak tails before assigning tracker names. Character identities, lexical tone classes and desired contours were not used to judge acoustic correctness.

| Blind label | Revealed tracker |
| --- | --- |
| A | pYIN |
| B | Praat CC |
| C | CREPE full |
| D | Praat AC |
| E | WORLD Harvest |

| Representative recording | Observations recorded before reveal | Check against numerical evidence |
| --- | --- | --- |
| Exact native_24k | A conservative around breaks; B irregular late branches; C smooth speech but fills weak tail/silence; D isolated high/low branches; E extends downward into weak tail | All five 45/45 clear core frames; raw continuity provides no tail truth |
| Healthy human_control | A/B/C/D follow strong low harmonic regions and later rise; E has stronger boundary excursions; C fills gaps | Healthy rise is preserved by AC/CC/pYIN/CREPE; Harvest's broad-window trend is distorted |
| Old Google | C follows ~200–300-Hz voice while A/B/D often select low background/subharmonics; E intermittently follows speech then drops | C 101/101 broad-band core agreement; raw low branches remain in difficult AC/CC/pYIN windows |
| New take_1 | C avoids B/D doubled onset and preserves more late rise; A omits a relevant middle patch; E drops at boundaries; C fills padding | Post-hoc window endpoints and first/last quintile changes support the observation |
| Low-register 7787300e | A/B/D and C follow strong ~85–115-Hz harmonic regions; C supplies a path across multi-second background; E adds many background islands | C raw 305/305 pause frames, E 87/305; clean pYIN loses 24/113 clear core frames |
| Historical f5dc0cc1 | B avoids D's high terminal branch; A misses clear patches; C follows speech but extends into background; E tracks too much low background | CC/CREPE avoid the ~21.9-st branch; pYIN has 0/22 core coverage |
| Periodic silence | C has a stable continuous path; A sparse low paths; B/D many islands; E more continuous low background | All have some raw false vocal evidence; native confidence must be checked quantitatively |

The frozen notes are available at [the local initial-review file](/home/jacob/benma/services/api/var/f0-foundation/blind-review-initial.txt). The [interactive viewer](/home/jacob/benma/services/api/var/f0-foundation/viewer.html) retains blind labels and an explicit reveal control; `figures/` contains all 49 overlays and 15 representative blind panels. Toggle trackers separately where overlapping colors obscure a branch.

The first native and low-register voiced/pause intervals were marked during the initial visual review. Additional coarse harmonic bands and human/Google/州 intervals were finalized after reveal, using the preserved observations. They are explicitly post-hoc, approximate annotations; no gold cents-error estimate or independent blinded ranking is claimed. The final decision combines these observations with deterministic synthetic truth, known negatives, repeatability, low-F0 protection and runtime.
