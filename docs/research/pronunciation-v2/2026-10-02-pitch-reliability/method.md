# Method and fixed criteria

> **Superseded by the [Trust Pass](trust-pass.md).** The second real silence case exposed a periodic-background false accept. Current behavior adds post-ASR acoustic corroboration, removes default reference-tone labels, and keeps the primary pitch tracker. The content below records the earlier pass.

The local `method.txt` was written before examining candidate results. Ten recordings
were selected by exact persisted transcript (terminal punctuation ignored only for
lookup), timestamp, perception/utterance linkage, saved target and SHA-256. There is
no filename-based identification or guessed assignment of takes to speaking speed.
The two mismatch cases actually say `我们要去贵州。` and `贵州。`; no recent exact
`我要去贵州。` recording was found. The separate saved S13 fixture still tests that phrase.

## Available methods

API environment: NumPy and Parselmouth 0.4.7 / embedded Praat 6.1.38. Both AC and CC are
usable offline. Current production and its older normalized-autocorrelation fallback
are present in source. Root environment has neither acoustic package; isolated model
environment has Torch/NumPy but no torchaudio or pitch model adapter. Across these
three environments: librosa/pYIN, pyworld/DIO/Harvest, CREPE/torchcrepe, torchaudio,
WebRTC VAD and Silero VAD are unavailable. No model/package was downloaded.
Praat exposes frequency and strength for every frame's candidates; production already
stores these. A candidate's strength is not a calibrated speech probability.

Compared: production AC50 including application work; plain AC50 (raw control), CC50,
AC40, CC40. The latter four are **raw tracker comparisons, not fully integrated
production candidates**. All use ceiling 550 Hz, step 10 ms, voicing .45, silence .03,
octave cost .01, octave-jump cost .5, voiced/unvoiced cost .14, up to 15 candidates,
`very_accurate=False`. Only floor/method differ. No utterance-adaptive experiment,
per-character tuning, tone labels, expected shape, target or transcript enters tracking.

## Metrics

- Finite F0 / total frames; no resampling to hide different native frame grids.
- An island breaks at missing F0 or >15.1 ms separation. Singleton = one frame;
  short = fewer than four frames (<40 ms support at 10 ms cadence).
- Adjacent finite frame jumps >6 semitones; likely octave jumps 9–15 semitones.
- Isolated octave-like excursions: <=80 ms branch, bracketing evidence within 120 ms,
  preceding/following median within 2 st, branch displaced 9–15 st. Artifact proxy only.
- Independent 60 ms normalized ACF maximum over 40–550 Hz lags: >=.65 with RMS >=.0003
  is a periodic-looking frame; <=.25 is aperiodic-looking. Count missing pitch in the
  former, pitch in the latter, and pitch below RMS .0003. Waveform, RMS distribution,
  peak, clipping >=.98, recording duration/rate and RMS <.003 fraction accompany these.
- Repeat equality over three runs; runtime median of those three sequential runs.
  Full production time includes its second tracker, spectral checks and normalization;
  plain tracker timings exclude that work. They are not end-to-end API latency.

These ACF proxies are **not voiced/unvoiced ground truth**: colored background in the
no-speech control has high correlation. Consequently periodic-looking missing frames
are not automatically false missing pitch. Production timestamps are rounded to four
decimals; candidate grids retain native precision, creating small proxy-count differences
between production raw and the equal-frequency AC50 control. No accuracy ranking is
claimed from these counts alone. Adjacent-jump metrics intentionally do not jump across
nulls; the separate 州 forensic check reports its across-gap 21.9-st discontinuity.

## Selection audit and acceptance

The existing display filter now optionally emits an internal diagnostic row per source
frame: tracker absence, energy gate, quality/contamination, invalid/missing/out-of-range
value, periodicity threshold, bracketed short island and local Hampel outlier. Flags can
overlap; they must not be summed as unique rejected frames. Raw finite, energy-gated,
acoustic-selected and display-retained counts are reported separately. No selection
condition or threshold changed. Every saved production frame list exactly matched its
offline re-extraction (10/10). Untimed characters cannot have per-syllable acoustic counts.

Acceptance required consistent improvement without extra noise pitch, instability,
fragmentation or material latency regression. More coverage alone cannot win.
The [historical comparison](../../../development/perception-alignment-pitch-2026-09-18.md)
already found the Python normalized-AC fallback much slower with more octave-sized jumps,
and naïve octave unwrapping propagated errors. It also found raw Praat tracking periodic
background, motivating the current gates. This pass supplies new connected-speech
missingness/branch evidence; it provides no reason to revive those rejected approaches.
No neural candidate previously shown superior was available here.
