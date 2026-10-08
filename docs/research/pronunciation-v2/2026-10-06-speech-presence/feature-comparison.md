# Bounded feature comparison

## Frozen set and limitations

[corpus.json](corpus.json) freezes exact SHA-256, persisted perception identity where available, source path/provenance, labels, categories and parent intervals. All pre-existing canonical capture/reference/negative entries from the frozen F0 inventory are included; arbitrary synthetic voiced signals are excluded from the real-speech positives. `native_24k` is excluded because the existing 16-kHz canonical copy and two prior variants are already included. No new gain/noise/pitch transform was made.

The one failed, unlabelled capture `277e9941` remains **unresolved**, not a positive silently dropped after tuning and not a newly asserted negative. Six real speech excerpts use existing voiced review intervals or saved low-F0 support. Four non-speech padding excerpts use the prior acoustic review. Excerpts are exact PCM slices with pinned parent hash/sample boundaries; the audit/test reconstructs their bytes in memory. Padding annotations are existing approximate review, not new human ground truth.

The positive set is **31 whole waveforms +6 excerpts**. Repeated captures/derived reference variants are correlated. This is a bounded calibration/regression corpus, **not an independent held-out validation set**. No real whisper, confirmed nonsense recording, independently labelled noisy-speech category, or standalone 对/嗯/好/不 is available in the frozen evidence; none was manufactured. Short excerpts test 110–300-ms vocal activity, not the full diversity of isolated interjections. Quiet RMS is an amplitude proxy; `native_gain` is an existing attenuation control. Sparse pitch means saved production voiced fraction <.3, not a new linguistic annotation.

## Features (four families, no new tracker)

1. **Energy/envelope:** centered frame RMS; longest >3×background run; speech-band p90/p20 RMS ratio and run >3×speech-band baseline. Research frames are 25 ms, hop 10 ms. Guard diagnostics retain their exact existing 20-ms frames.
2. **Band distribution:** 1024-point real FFT of centered Hann frames, energy proportions in 0–150 / 150–300 / 300–600 / 600–1200 / 1200–2400 / 2400–4000 / 4000–8000 Hz. Compare 300–4000 power with total; low <150 power is diagnostic. There is no F0 cutoff.
3. **Spectral change:** total variation distance of those seven normalized proportions across 50 ms; report the 90th percentile. This can also be large in colored noise; it is not a speech probability.
4. **Entropy:** median normalized Shannon entropy over FFT bins. It measures spread/tonality, not lexical validity or biological source.

| Recording | 300–4000 ratio | <150 ratio | Band modulation | Flux p90 | Entropy |
| --- | --- | --- | --- | --- | --- |
| silence_accidental | 0.8757 | 0.0863 | 34.7321 | 0.5561 | 0.4517 |
| silence_periodic | 0.1077 | 0.6995 | 1.6648 | 0.4819 | 0.4885 |
| silence_original | 0.2249 | 0.3208 | 1.6290 | 0.5029 | 0.4998 |
| 7787300e | 0.2137 | 0.4308 | 17.4833 | 0.5380 | 0.5304 |
| c95673d3 | 0.6911 | 0.0697 | 32.6444 | 0.5035 | 0.5408 |
| 27ea3b92 | 0.5554 | 0.1750 | 53.9326 | 0.6717 | 0.5465 |
| human_control | 0.3157 | 0.4061 | 27.6117 | 0.5708 | 0.4655 |
| take_1 | 0.9651 | 0.0049 | 29.0069 | 0.5787 | 0.5258 |
| native_gain | 0.5220 | 0.0044 | 29.6944 | 0.8491 | 0.3955 |
| short_human_b | 0.0646 | 0.4659 | 1.4493 | 0.3121 | 0.4527 |
| low_f0_excerpt | 0.5203 | 0.0981 | 2.5375 | 0.3254 | 0.4989 |


Accidental silence and real speech overlap strongly. Real low voice has upper energy and time variation, but those do **not** uniquely distinguish this negative. The accidental file's band modulation (34.73) exceeds several low-voice positives; its flux (.556) lies among them. Its entropy (.452) nearly matches healthy short/human/native controls. A high speech-band minimum would reject the 110-ms human excerpt (ratio .065) and 200-ms excerpt (.046). Requiring strong envelope change within an already-cropped short vowel rejects real speech whose onset/offset is outside that window.

![Saved low-F0 recording](figures/c95673d3-spectrum.png)
![Confirmed human](figures/human_control-spectrum.png)
![Accepted phone playback take 1](figures/take_1-spectrum.png)

The low-voice whole recordings include actual saved 54–70-Hz support; no requirement raises that floor. Their high harmonics and changing structure are useful cues against stationary hum but overlap the accidental file. The protected proxy is baseline-relative and does not claim independent F0 gold.

## Exactly five policies

All policies read only waveform features. None sees transcript, target, characters, lexical tone, confidence, pitch windows, or a recording identity.

| Policy | Generic rule at nominal threshold |
| --- | --- |
| envelope | longest energy-active run ≥50 ms |
| band_envelope | band ratio ≥.10, band-active run ≥50 ms, band modulation ≥3 |
| spectral_temporal | envelope AND flux ≥.35 AND entropy ≥.20 |
| combined | band_envelope AND flux ≥.35 AND entropy ≥.20 |
| short_spectral | flux ≥.20 AND entropy ≥.20, with no required long envelope/run |

These are plausible bounded candidate gates, not certified VADs. The fifth explicitly relaxes the temporal constraint that rejected short genuine voice. At most these five policy families are tested; the feature-only reconnaissance is not a second policy search. No classifier fitting, high-dimensional search, exact-frequency signature, transcript blacklist or per-recording threshold is used.

Every numeric policy threshold is tested together at **0.8×, 1.0×, 1.2×**. Results remain bad over a broad neighborhood, rather than succeeding at a knife edge:

| Policy | Factor | Positive accepted | Negative rejected | Accidental rejected |
| --- | --- | --- | --- | --- |
| envelope | 0.8 | 31/37 | 9/10 | **no** |
| envelope | 1.0 | 31/37 | 9/10 | **no** |
| envelope | 1.2 | 31/37 | 9/10 | **no** |
| band_envelope | 0.8 | 32/37 | 9/10 | **no** |
| band_envelope | 1.0 | 32/37 | 9/10 | **no** |
| band_envelope | 1.2 | 32/37 | 9/10 | **no** |
| spectral_temporal | 0.8 | 31/37 | 9/10 | **no** |
| spectral_temporal | 1.0 | 31/37 | 9/10 | **no** |
| spectral_temporal | 1.2 | 31/37 | 9/10 | **no** |
| combined | 0.8 | 32/37 | 9/10 | **no** |
| combined | 1.0 | 32/37 | 9/10 | **no** |
| combined | 1.2 | 32/37 | 9/10 | **no** |
| short_spectral | 0.8 | 37/37 | 2/10 | **no** |
| short_spectral | 1.0 | 37/37 | 5/10 | **no** |
| short_spectral | 1.2 | 37/37 | 5/10 | **no** |


| Policy at nominal threshold | Ordinary /28 | Quiet RMS /12 | Short /6 | 54–70 Hz /5 | Native-like /4 | Phone TTS /4 | Sparse /8 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| envelope | 28 | 12 | 0 | 3 | 3 | 4 | 8 |
| band_envelope | 28 | 12 | 1 | 4 | 3 | 4 | 8 |
| spectral_temporal | 28 | 12 | 0 | 3 | 3 | 4 | 8 |
| combined | 28 | 12 | 1 | 4 | 3 | 4 | 8 |
| short_spectral | 28 | 12 | 6 | 5 | 4 | 4 | 8 |


The first/fourth policies' low-F0 totals include full recordings, which survive, and isolated excerpts, which expose the false rejects. Every policy accepts all 31 positive whole waveforms. Envelope/spectral-temporal lose all six short excerpts; band/combined retain only one of six. The short-compatible fifth retains 37/37, but at nominal thresholds rejects only 5/10 negatives, re-admitting the historical original/periodic negatives. At 0.8× it also admits stationary noise and more padding.

The accidental file passes every policy at every neighborhood value. No candidate satisfies even the central rejection requirement, let alone rejection plus category retention. A monotone modulation threshold high enough to reject it (>34.73) would lose many positive whole recordings. A flux threshold >.556 would likewise reject low-voice and quiet controls. A narrow spectral-ratio interval that happens to exclude .876 while keeping the accepted phone/TTS values would be an unsupported recording-specific rule. No such rule is promoted or evaluated as a sixth policy.

## Current retention / rejection

| Category (overlapping) | Waveforms | Accepted before | Accepted after |
| --- | --- | --- | --- |
| confirmed_human | 4 | 4 | 4 |
| low_f0_54_70_proxy | 5 | 5 | 5 |
| ordinary | 28 | 28 | 28 |
| quiet_gain_control | 1 | 1 | 1 |
| quiet_rms_proxy | 12 | 12 | 12 |
| short | 6 | 6 | 6 |
| sparse_pitch | 8 | 8 | 8 |
| tts_native_like | 4 | 4 | 4 |
| tts_phone | 4 | 4 | 4 |


| Negative | Before / after | Label provenance |
| --- | --- | --- |
| silence_original | rejected / rejected | user-identified no-speech |
| silence_periodic | rejected / rejected | user-identified no-speech |
| silence_accidental | accepted / accepted | user-identified no-speech |
| neg_digital_silence | rejected / rejected | deterministic local synthesis |
| neg_stationary_noise | rejected / rejected | deterministic local synthesis |
| neg_clicks | accepted / accepted | deterministic local synthesis |
| padding_human_head | accepted / accepted | Exact PCM crop of existing recording |
| padding_human_tail | accepted / accepted | Exact PCM crop of existing recording |
| padding_low_voice | accepted / accepted | Exact PCM crop of existing recording |
| padding_phone | accepted / accepted | Exact PCM crop of existing recording |


All table before/after counts use the existing post-transcript guard with saved raw ASR text where it exists. The four padding crops and stored digital/noise/click controls have no saved ASR, so they are measured without transcript. Separately, **all 37 positive cases** remain accepted under None/empty/nonsense/changed-Chinese metadata. Periodic negative rejection changes when the existing Han count changes; this is an explicit known failure, not concealed by the retention table.

## Latency

Seven warm paired runs ×48 waveforms =336 samples per operation, local CPU. Whole files and short excerpts are pooled; no end-to-end/device percentile claim is made.

| Operation | Median ms | p95 ms | Maximum ms |
| --- | --- | --- | --- |
| Existing presence | 3.779 | 8.514 | 11.008 |
| Candidate feature bundle only | 2.648 | 5.545 | 9.503 |
| Added production cost | 0 | 0 | 0 |

[Raw timings](latency.json). The feature measurement starts with decoded NumPy samples; it excludes WAV decoding and measures an additive feature bundle, not a replacement guard. No dependencies or model inference are added. Fast execution does not compensate for false accepts/rejects.
