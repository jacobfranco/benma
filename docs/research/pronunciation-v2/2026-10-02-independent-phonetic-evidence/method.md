# Method fixed before extraction

Research only. Written before running the selected-region probe. No parameter search,
threshold adjustment, training, new pitch extraction, or pronunciation judgment.

## Independent evidence

A measurement is independent here if its computation depends only on the waveform,
the supplied interval, and saved target-independent acoustic frames. The interval is
provider-supplied and conditioned on perceived text: **this is conditional acoustic
independence, not an independently discovered syllable segmentation**. Timing is not
gold. Intended text, readings, phones, scores and self-report are forbidden extractor
inputs. Selection and later unblinding are separate operations. A measurement is not
sound identification; sound identification would still not establish correctness.

## Fixed procedure

- Validate original audio hashes and equality of saved acoustics with the previous
  reviewed v2 records. Use their existing timing; do not redo the mapping pass.
- Decode once with local ffmpeg to mono 16 kHz float PCM. No trimming, enhancement,
  normalization, gain change or pitch processing. Crop `[start,end)` at nearest sample.
- Whole-region duration, RMS, peak and fraction of samples at absolute amplitude
  >=0.98. RMS is digital amplitude, not calibrated intensity/SPL; clipping threshold
  comes from the existing acoustic code and is only a near-full-scale indicator.
- 25 ms Hann-windowed, mean-removed frames every 10 ms, wholly inside the crop;
  512-point real FFT. Power-weighted centroid, standard-deviation bandwidth, 85%
  rolloff, >=4 kHz power fraction and zero-crossing rate. These describe spectral
  distribution, not consonant identity. Zero-power frames return missing spectrum.
  No SNR estimate: no independently identified noise-only reference is available.
- Saved pitch is sliced unchanged at `[start,end)`. Usability is exactly the existing
  selected-F0-present AND `quality_usable` rule. Report raw and selected missingness
  separately. Saved `voicing_probability` is Praat candidate strength, not calibrated
  probability. Missing pitch does not establish unvoiced speech.
- Group contiguous usable selected frames at the saved 10 ms cadence (maximum gap
  15 ms permits timestamp rounding only). A nucleus **candidate analysis window**
  requires at least five contiguous usable frames, the existing descriptive minimum.
  Use the longest run, earlier run on ties, with half-hop margins clamped to the span.
  No equal splitting, text-based segmentation, gap filling or forced nucleus.
- Before/after that window, retain prefix/tail analysis windows only when each is
  at least 25 ms. Prefix is not an initial, tail is not a coda. A prefix qualifies
  for generic spectral inspection only with >=3 complete FFT frames. Report any raw
  pitch present there; lack of saved pitch is never called confirmed aperiodicity.
- Formants: one general Praat Burg setting for every candidate: 10 ms step,
  five formants, 5500 Hz ceiling, 25 ms window length (50 ms effective support),
  pre-emphasis from 50 Hz. Only centers whose full 50 ms support fits inside the
  candidate are considered. No expected vowel or speaker-specific tuning.
- Formant feasibility guards, fixed here, are conservative research filters, not
  validated physical limits: F1 150–1200 Hz, F2 500–3500 Hz, F3 1200–4500 Hz;
  ordered with >=100 Hz separation; positive bandwidths <=500/700/1000 Hz.
  A frame must pass all three. A summary additionally needs >=3 passing frames,
  >=70% passing candidate frames, and no adjacent passing-frame relative jump
  >25% for any formant. Jumps are compared only across adjacent 10 ms centers.
  Report raw availability, rejected frames, missingness and failures separately.
  Genuine vowel movement can fail these guards; stable wrong Burg tracks can pass.
  Accepted values mean only a feasible numeric track, not a verified resonance.
- Pitch median/range use existing usable frames. First/last usable points retain
  their timestamps; midpoint is missing unless a usable point lies within 10 ms of
  the interval midpoint. Descriptive slope uses only the longest contiguous run
  with >=5 points, never interpolates gaps, and has no tone label.
- Quality is a list of explicit flags, with no overall correctness/quality score.
  Every region carries `boundary_not_independently_validated`. Dimensions may be
  available independently: waveform/spectrum, saved pitch, candidate, formants,
  prefix spectrum. No global GOOD bucket implies evidence in every dimension.

## Blinding and controls

Nine requested focal regions plus three controls. Control candidates are nonfocal
regions from S02/S03; exclude S01 because its entire attempt was reported imperfect
and S13 because it contains deliberate manipulation. Require valid mapped timing,
no mapping issue, at least five usable saved frames, no saved tracker instability,
nonzero saved energy. Rank by usable-frame fraction descending, then usable count,
then study/unit identifier. Take three. This selects evidence-rich examples, not
correct-pronunciation examples; it is intentionally not a representative sample.
Neither readings nor provider scores rank candidates.

Order all twelve using a fixed SHA-256 ordering of study/unit identifiers with a
versioned salt, then assign R01…R12. A preparation-only key contains identities and
selection reasons. Extraction runs as a separate process with a strict numeric
input allowlist. Public packet contains only R IDs, relative times, waveform crops,
plots and acoustic measurements; absolute times, source paths and identity hashes
stay in the separate provenance/key directory. Blinding hides supplied text and
case status; audible speech can of course reveal lexical identity to a listener.
This is tooling blinding, not a claim that the implementing author forgot the cases.
Seal numeric summaries before reading the key to write unblinded results.

## Frozen representation

If the verified local cache loads, use existing waveform-only `features.py` routines
in the research environment: frozen CPU eval, float32, deterministic algorithms,
eager attention, one crop per forward, checkpoint normalization, no padding.
Choose transformer block 6 in advance; mean-pool all valid hidden frames, 768 values.
Repeat every crop to check bitwise determinism; check encoder state unchanged and no
gradients. No head, labels, PCA, training, distances or correctness inference. Short
crops have little context, and embeddings are not directly interpretable by a human.

## Feature meanings and limits

| Measurement | Potential future use | Present limitation |
| --- | --- | --- |
| Supplied duration | Relative rhythm, duration/context review | Provider boundaries, no speech-rate or target-normalized judgment |
| Waveform, RMS mean/median/envelope, peak | Locate energy transitions; inspect weak or truncated regions | Digital amplitude depends on microphone/gain; not SPL or correctness |
| Near-full-scale fraction | Detect possible recording saturation | Existing 0.98 threshold; does not detect all distortion; not SNR |
| Raw/selected F0 counts and missingness | Describe available pitch support and abstention | Tracker and gating dependent; missing is not unvoiced |
| Saved strength and longest run | Periodicity support, candidate window proposal | Praat strength is not probability; longest run is not a vowel boundary |
| F0 median/range/dated endpoints/slope | Inspect local prosody where supported | No tone class, expected contour or pitch correction; gaps and outlying branches remain |
| Power centroid/bandwidth/rolloff/HF ratio | Compare spectral concentration and changing high-frequency content | Whole syllables/prefixes mix sources and phones; cannot identify s/sh/x or any other initial |
| Zero crossing | Complement spectral/noise inspection | Frequency, voicing, noise and waveform offsets can all affect it; no calibrated noisiness score |
| Burg estimates/bandwidths/guards | Test whether resonance tracks can be retained | Model/speaker/window sensitive; raw numeric candidates may be wrong; no vowel or final label |
| Frozen embedding | Future representation input | Not an interpretable phone inventory; no local supervised head or distance interpretation |

The only post-run code clarification added more explicit reasons for the already fixed
formant abstentions. No parameter, guard, feature value, window or pitch selection changed;
initial artifacts were preserved, and all numeric observations/embeddings were verified
identical. Spectrogram scales are shared across regions: 0–650 ms, 0–8 kHz, fixed
-100 to -20 dB bin-power grayscale. Waveform scale is ±1, RMS 0–1, F0 0–600 Hz.
Saved pitch has the historical PCM16 canonicalization provenance; fresh waveform features
use float32 decoding at the same 16 kHz rate without PCM16 quantization. No new temporal
offset is applied. Isolated listening crops are quantized to PCM16 for portability.
