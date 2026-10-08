# Known-F0 accuracy

## Final RMVPE extension

RMVPE retains **1404/1404 known-voiced core frames**, raw and gated, with zero false gaps and no halving. Nine controls have no octave error. The weak-fundamental/strong-second-harmonic control has **one core doubling event, 79/145 doubled frames**, retained throughout the native-confidence sweep. This is better than CREPE/pYIN's 145 doubled frames but worse than AC/CC/Harvest's zero.

The critical **70-Hz signal passes: 145/145 frames, median absolute error .230 Hz / 5.705 cents, p95 .116 st and max .119 st**. The interrupted-voice control retains 99/99 voiced frames and emits no pitch in its 40 evaluated negative frames. [rmvpe.md](rmvpe.md) summarizes all ten controls; [synthetic-tables.md](synthetic-tables.md) now joins all six trackers without re-extracting prior outputs. The original five-tracker findings below remain unchanged.

**Praat AC/CC and Harvest recover the known fundamental in all ten raw controls. pYIN and CREPE double it throughout the weak-fundamental control.** The latter failure survives the fixed confidence cleanup. Strong synthetic scores do not overrule observed real speech/background failures.

The corpus includes exactly 70, 110, 180 and 260-Hz steady signals; a rise, fall and valley; an octave-risk mixture; a weak fundamental with amplified second harmonic; and voiced 110 Hz interrupted by noise. [Definitions](benchmark-corpus.md) and hashes are frozen. No additional synthetic signal was added after results were seen.

[Full tables](synthetic-tables.md) report every signal × tracker × raw/clean view, plus the production AC ablation. They include voiced coverage, median absolute Hz error, median cents, p95/max semitone error, separate halving/doubling events and frame counts, false gaps and false pitch. [Per-recording CSV](per-recording-metrics.csv) additionally retains median semitones, p95/max absolute Hz, p90, all denominators and general continuity metrics.

Accuracy excludes ±80 ms around excitation/gap boundaries. Absolute error is `abs(12*log2(estimated/truth))` st; one semitone is 100 cents. Octave-error frames exceed 9 st absolute error. A halving/doubling event is a contiguous run with signed error within −15…−9 / +9…+15 st. Missing frames break events. These are known-truth errors, unlike the real-speech discontinuity proxies.

| Raw tracker | Evaluated voiced coverage | >9-st errors | Halving / doubling events | Main numerical behavior |
| --- | --- | --- | --- | --- |
| AC | 1404/1404 | 0 | 0 / 0 | Median errors around zero to .001 st |
| CC | 1403/1403 | 0 | 0 / 0 | Sweeps have ~.086–.091-st median error; max ~.125 st |
| pYIN | 1404/1404 | 145 | 0 / 1 | Typical median .024–.050 st; weak fundamental ~12.050 st |
| Harvest | 1404/1404 | 0 | 0 / 0 | Median around zero to .001 st; weak-case max .018 st |
| CREPE | 1404/1404 | 145 | 0 / 1 | Non-weak-case medians ~.058–.111 st; weak fundamental ~12.064 st |

Native edge placement gives CC one fewer eligible voiced frame; it is not a false gap. All raw trackers have zero known-voiced core gaps. CREPE cleanup removes **26 otherwise correct frames** in the varying octave-risk signal, reducing overall coverage to 1378/1404 (98.15%). Other minimal views preserve their synthetic core coverage.

## Weak fundamental is a decisive counterexample

The nominal F0 remains 110 Hz because higher odd harmonics remain, even though the first harmonic is weak and the second is strongest.

| Tracker, raw and clean | Median absolute Hz error | Median cents | p95 st | Max st | Doubling events / frames |
| --- | --- | --- | --- | --- | --- |
| pYIN | 110.636 | 1204.996 | 12.050 | 12.050 | 1 / 145 |
| CREPE | 110.811 | 1206.369 | 12.190 | 12.238 | 1 / 145 |

Neither native-confidence gate rejects the doubled path. Low adjacent-jump counts and a smooth trajectory can therefore coexist with a completely wrong fundamental. CREPE's Viterbi transition prior especially limits abrupt per-frame changes; its zero adjacent >9-st jumps are not a correctness certificate.

## Low frequency and gaps

All five raw and minimally cleaned trackers retain every evaluated 70-Hz core frame. CREPE's median absolute error there is about .111 st (11.1 cents), max .273 st. However, clean synthetic 70 Hz does not establish safety on weak 54–70-Hz human evidence. See [the real low-register comparison](low-f0-and-silence.md).

**Production AC drops all 145 steady-70-Hz core frames**, despite correct raw F0 and very high periodicity. The production low-frequency-contamination rule causes this rejection. It retains every eligible core frame of the other nine controls. Thus production synthetic coverage falls to 89.67% without any raw octave error to fix.

On the interrupted-voice control, AC/CC/pYIN/Harvest correctly leave the evaluated noise/silence cores without pitch. CREPE raw emits in all 40 of its eligible negative frames; cleanup removes all 40 while preserving its voiced core. This simple generated negative is substantially easier than the real periodic/accidental backgrounds, where the same cleanup fails.
