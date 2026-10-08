# Exact frozen corpus results

The manifest is a byte-for-byte copy of the prior presence manifest: **37 positives, 10 negatives, one unresolved**. All 48 SHA-256 identities and every excerpt's parent hash were checked before inference; none was added, removed or skipped. [Hashes](hash-verification.json), [unchanged manifest](corpus.json), [fresh baseline replay](baseline-replay.json).

These are 48 cases, not 48 independent recordings. Positives comprise 28 captures, three existing digital variants, and six exact excerpts. Negatives comprise three user-labelled captures, three stored synthetic non-speech controls, and four existing padding excerpts. The unresolved capture stays outside all positive/negative denominators. Every evaluated input is mono PCM16: 46 use 16 kHz; native_gain and native_bandlimit use 24 kHz and were normalized to 16 kHz by the documented resampler. Crops are reconstructed in memory without creating new audio files.

Speech duration and first/last boundaries below come from the official helper, including its 30 ms padding after the strict >250 ms pre-padding duration filter. Median probability covers all chunks, including silence and the zero-padded final chunk; it is not a conditional speech-region median. Speech present means at least one returned region. Full-precision values and interval lists are in [default-results.json](default-results.json); all raw frames are under [probabilities/](probabilities/).

## Ten negatives

Baseline: 4/10 rejected, 6 false accepts. Silero defaults: **9/10 rejected, one false accept**. The remaining false accept is the required newest accidental-silence case. Categories are 1 original silence, 1 periodic silence, 1 accidental silence, 1 digital silence, 1 stationary noise, 1 clicks/transients, 4 padding excerpts.

| File | Category | Old | Silero | Peak p | Median p | Speech s | Longest s | Regions | First s | Last s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| silence_original | original silence hallucination | reject | reject | 0.152673 | 0.002489 | 0.000 | 0.000 | 0 | — | — |
| silence_periodic | periodic-background silence | reject | reject | 0.048586 | 0.002841 | 0.000 | 0.000 | 0 | — | — |
| silence_accidental | newest accidental silence | accept | accept | 0.997681 | 0.867519 | 1.852 | 1.852 | 1 | 1.026 | 2.878 |
| neg_digital_silence | digital silence | reject | reject | 0.008911 | 0.003609 | 0.000 | 0.000 | 0 | — | — |
| neg_stationary_noise | stationary noise | reject | reject | 0.041519 | 0.006262 | 0.000 | 0.000 | 0 | — | — |
| neg_clicks | clicks/transients | accept | reject | 0.016714 | 0.005431 | 0.000 | 0.000 | 0 | — | — |
| padding_human_head | padding excerpt | accept | reject | 0.071564 | 0.015729 | 0.000 | 0.000 | 0 | — | — |
| padding_human_tail | padding excerpt | accept | reject | 0.029694 | 0.005399 | 0.000 | 0.000 | 0 | — | — |
| padding_low_voice | padding excerpt | accept | reject | 0.028758 | 0.003714 | 0.000 | 0.000 | 0 | — | — |
| padding_phone | padding excerpt | accept | reject | 0.041764 | 0.007701 | 0.000 | 0.000 | 0 | — | — |

## All 37 positives

Baseline retains 37/37; Silero defaults retain **33/37**. All 31 whole waveforms survive; four of six short excerpts fail.

| File | Category | Old | Silero | Peak p | Median p | Speech s | Longest s | Regions | First s | Last s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6f56aef1 | ordinary | accept | accept | 0.999980 | 0.999325 | 3.704 | 1.884 | 2 | 0.482 | 4.350 |
| 5b995fff | ordinary | accept | accept | 0.999931 | 0.592955 | 1.308 | 1.308 | 1 | 0.482 | 1.790 |
| 7787300e | ordinary, quiet_rms_proxy, sparse_pitch, low_f0_54_70_proxy | accept | accept | 0.999984 | 0.032074 | 3.284 | 1.244 | 3 | 0.642 | 7.262 |
| c95673d3 | ordinary, low_f0_54_70_proxy | accept | accept | 0.999996 | 0.998188 | 3.090 | 3.090 | 1 | 0.834 | 3.924 |
| c5188fc3 | ordinary | accept | accept | 0.999997 | 0.993207 | 1.436 | 1.436 | 1 | 0.418 | 1.854 |
| 27ea3b92 | ordinary, low_f0_54_70_proxy | accept | accept | 0.999998 | 0.955868 | 1.624 | 0.892 | 2 | 0.866 | 2.590 |
| 0f4107fe | ordinary | accept | accept | 0.999933 | 0.972436 | 1.756 | 1.756 | 1 | 0.322 | 2.078 |
| f3c642b5 | ordinary, quiet_rms_proxy, sparse_pitch | accept | accept | 0.999975 | 0.024254 | 0.668 | 0.668 | 1 | 0.386 | 1.054 |
| f47fadb3 | ordinary, quiet_rms_proxy | accept | accept | 0.999991 | 0.944415 | 2.040 | 1.372 | 2 | 0.514 | 2.910 |
| a0270cee | ordinary | accept | accept | 0.999996 | 0.997439 | 2.772 | 1.052 | 3 | 0.418 | 3.582 |
| 484e80c0 | ordinary | accept | accept | 0.999901 | 0.990504 | 1.489 | 1.489 | 1 | 0.578 | 2.067 |
| e59a6350 | ordinary, sparse_pitch | accept | accept | 0.999995 | 0.013711 | 0.796 | 0.796 | 1 | 0.418 | 1.214 |
| f5dc0cc1 | ordinary, sparse_pitch | accept | accept | 0.999985 | 0.020888 | 0.700 | 0.700 | 1 | 0.738 | 1.438 |
| 370aa8f4 | ordinary, quiet_rms_proxy | accept | accept | 0.999991 | 0.947098 | 1.980 | 1.980 | 1 | 0.866 | 2.846 |
| 1a927887 | ordinary, quiet_rms_proxy | accept | accept | 0.999994 | 0.987499 | 2.808 | 1.788 | 2 | 0.962 | 4.286 |
| 5ca771a7 | ordinary, quiet_rms_proxy | accept | accept | 0.999830 | 0.994522 | 1.852 | 1.852 | 1 | 0.738 | 2.590 |
| 209ef0c7 | ordinary, quiet_rms_proxy, sparse_pitch | accept | accept | 0.999993 | 0.011649 | 0.796 | 0.796 | 1 | 0.674 | 1.470 |
| 87ac7dd1 | ordinary, quiet_rms_proxy, sparse_pitch | accept | accept | 0.999965 | 0.015279 | 0.668 | 0.668 | 1 | 0.738 | 1.406 |
| 02927481 | ordinary, quiet_rms_proxy | accept | accept | 0.999980 | 0.998097 | 3.099 | 3.099 | 1 | 0.802 | 3.901 |
| 90aa0d8d | ordinary, sparse_pitch | accept | accept | 0.993302 | 0.177715 | 0.668 | 0.668 | 1 | 0.738 | 1.406 |
| e0c56934 | ordinary | accept | accept | 0.999969 | 0.998867 | 2.044 | 2.044 | 1 | 0.578 | 2.622 |
| dccf8a63 | ordinary, sparse_pitch | accept | accept | 0.999991 | 0.101926 | 0.835 | 0.835 | 1 | 0.674 | 1.509 |
| 9b1d959a | ordinary | accept | accept | 0.999909 | 0.089888 | 0.892 | 0.892 | 1 | 0.674 | 1.566 |
| human_control | ordinary, confirmed_human | accept | accept | 0.999941 | 0.970743 | 1.852 | 1.852 | 1 | 0.770 | 2.622 |
| google_old | ordinary, tts_phone | accept | accept | 0.998181 | 0.946178 | 3.057 | 3.057 | 1 | 1.378 | 4.435 |
| take_1 | ordinary, tts_phone | accept | accept | 0.997111 | 0.914923 | 2.812 | 2.812 | 1 | 0.834 | 3.646 |
| take_2 | ordinary, tts_phone, quiet_rms_proxy | accept | accept | 0.996987 | 0.979835 | 1.871 | 1.871 | 1 | 0.706 | 2.577 |
| take_3 | ordinary, tts_phone, quiet_rms_proxy | accept | accept | 0.998976 | 0.846810 | 2.812 | 2.812 | 1 | 1.410 | 4.222 |
| native_16k | tts_native_like | accept | accept | 0.999964 | 0.998610 | 1.048 | 1.048 | 1 | 0.002 | 1.050 |
| native_gain | tts_native_like, quiet_gain_control, quiet_rms_proxy | accept | accept | 0.999807 | 0.997023 | 1.048 | 1.048 | 1 | 0.002 | 1.050 |
| native_bandlimit | tts_native_like | accept | accept | 0.999888 | 0.996377 | 1.048 | 1.048 | 1 | 0.002 | 1.050 |
| short_human_a | short, confirmed_human | accept | reject | 0.984687 | 0.952529 | 0.000 | 0.000 | 0 | — | — |
| short_human_b | short, confirmed_human | accept | reject | 0.712090 | 0.436189 | 0.000 | 0.000 | 0 | — | — |
| short_human_c | short, confirmed_human | accept | reject | 0.853795 | 0.597189 | 0.000 | 0.000 | 0 | — | — |
| short_native | short, tts_native_like | accept | reject | 0.985715 | 0.807908 | 0.000 | 0.000 | 0 | — | — |
| low_f0_excerpt | short, low_f0_54_70_proxy | accept | accept | 0.824517 | 0.666520 | 0.260 | 0.260 | 1 | 0.000 | 0.260 |
| low_f0_excerpt_2 | short, low_f0_54_70_proxy | accept | accept | 0.990420 | 0.985237 | 0.270 | 0.270 | 1 | 0.000 | 0.270 |

## Exact overlapping positive category counts

| Frozen tag | Count | Old retained | Default retained |
| --- | --- | --- | --- |
| confirmed_human | 4 | 4 | 1 |
| low_f0_54_70_proxy | 5 | 5 | 5 |
| ordinary | 28 | 28 | 28 |
| quiet_gain_control | 1 | 1 | 1 |
| quiet_rms_proxy | 12 | 12 | 12 |
| short | 6 | 6 | 2 |
| sparse_pitch | 8 | 8 | 8 |
| tts_native_like | 4 | 4 | 3 |
| tts_phone | 4 | 4 | 4 |

`ordinary` includes the connected Mandarin captures. `sparse_pitch` is the existing voiced-fraction proxy, not independently labelled unvoiced-heavy speech. Quiet RMS and low-F0 are existing acoustic proxies. No independently labelled whisper or noisy-speech category exists. Categories overlap and must not be summed.

## Short speech is a blocking regression

Actual duration is the entire frozen speech excerpt. Peak margin is peak p minus 0.50; a positive margin does not guarantee the minimum region length.

| File | Actual ms | Detected ms | Peak p | Peak-0.50 | First p≥0.50 ms | Default | Accepted thresholds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| short_human_b | 110.0 | 0.0 | 0.712090 | 0.212090 | 64.0 | reject | none |
| short_human_a | 170.0 | 0.0 | 0.984687 | 0.484687 | 32.0 | reject | none |
| short_human_c | 200.0 | 0.0 | 0.853795 | 0.353795 | 32.0 | reject | none |
| low_f0_excerpt | 260.0 | 260.0 | 0.824517 | 0.324517 | 0.0 | accept | 0.30, 0.40, 0.50, 0.60 |
| low_f0_excerpt_2 | 270.0 | 270.0 | 0.990420 | 0.490420 | 0.0 | accept | 0.30, 0.40, 0.50 |
| short_native | 300.0 | 0.0 | 0.985715 | 0.485715 | 96.0 | reject | 0.30 |

Raw high-probability evidence is present even in the four false rejects. The table counts actual valid audio under each p>=0.50 chunk; the zero-padded tail is not counted as additional duration. These durations are distinct from hysteresis-based segmented durations.

| File | All frames | Frames p>=0.50 | Time p>=0.50 ms |
| --- | --- | --- | --- |
| short_human_b | 4 | 1 | 32.0 |
| short_human_a | 6 | 5 | 138.0 |
| short_human_c | 7 | 5 | 160.0 |
| low_f0_excerpt | 9 | 5 | 160.0 |
| low_f0_excerpt_2 | 9 | 9 | 270.0 |
| short_native | 10 | 7 | 204.0 |

The 110/170/200 ms human excerpts cannot pass the default >250 ms rule, despite peaks above 0.5. The 300 ms native excerpt crosses 0.5 only at 96 ms, leaving 204 ms to EOF, so it also fails; threshold 0.30 starts at zero and retains it. The 260/270 ms low-F0 excerpts pass at 0.50 but are vulnerable to small onset delays at higher thresholds. Peak confidence alone conceals these failures. No minimum-duration policy is promoted or swept, because threshold-only evaluation already fails the critical negative requirement.

## All five low-F0 controls

These retain the frozen 54-70 Hz evidence labels; no tracker, floor or eligibility was changed. Quantiles cover all raw chunks (p10 / median / p90 / max). Whole recordings include leading/trailing silence.

| File | Default | Speech s | p10 | Median | p90 | Max | Accepted thresholds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7787300e | accept | 3.284 | 0.001193 | 0.032074 | 0.999639 | 0.999984 | 0.30, 0.40, 0.50, 0.60, 0.70 |
| c95673d3 | accept | 3.090 | 0.010092 | 0.998188 | 0.999946 | 0.999996 | 0.30, 0.40, 0.50, 0.60, 0.70 |
| 27ea3b92 | accept | 1.624 | 0.012221 | 0.955868 | 0.999964 | 0.999998 | 0.30, 0.40, 0.50, 0.60, 0.70 |
| low_f0_excerpt | accept | 0.260 | 0.284654 | 0.666520 | 0.815786 | 0.824517 | 0.30, 0.40, 0.50, 0.60 |
| low_f0_excerpt_2 | accept | 0.270 | 0.788921 | 0.985237 | 0.988681 | 0.990420 | 0.30, 0.40, 0.50 |

At default, Silero does not appear to confuse legitimate 54-70 Hz speech with non-speech in these five frozen controls. This is a positive result despite the overall failure. Silero distinguishes the earlier periodic hum (peak 0.048586) from all five low-F0 controls at default. It still gives the accidental negative a 0.997681 peak. At 0.60 one low-F0 excerpt fails; at 0.70 both fail. This is duration/onset sensitivity, not evidence for raising a pitch floor.

## Transcript-free and lexically unreliable cases

No transcript, intended target, language, character count, lexical tone, pinyin, ASR score or semantic validity enters either audio adapter or the primary decisions. Six metadata contexts over all 48 waveforms reproduce identical raw probabilities and intervals, including every false accept/reject. Invariance cannot turn a rejected valid waveform into a passing gibberish result.

| Absent-transcript positive | Default | Speech s | Peak p |
| --- | --- | --- | --- |
| native_16k | accept | 1.048 | 0.999964 |
| native_gain | accept | 1.048 | 0.999807 |
| native_bandlimit | accept | 1.048 | 0.999888 |
| short_human_a | reject | 0.000 | 0.984687 |
| short_human_b | reject | 0.000 | 0.712090 |
| short_human_c | reject | 0.000 | 0.853795 |
| short_native | reject | 0.000 | 0.985715 |
| low_f0_excerpt | accept | 0.260 | 0.824517 |
| low_f0_excerpt_2 | accept | 0.270 | 0.990420 |

**5/9 absent-transcript positives survive; four short excerpts fail acoustically/temporally.** The three full digital controls and two low-F0 excerpts succeed without any ASR rescue.

| Case | Saved text (comparison only) | Saved mean token logprob | Default | Speech s |
| --- | --- | --- | --- | --- |
| 5b995fff | 我是讲 | -2.006732 | accept | 1.308 |
| 370aa8f4 | 我想买五部 | -0.153587 | accept | 1.980 |
| 90aa0d8d | 我也啊 | -0.013729 | accept | 0.668 |

`5b995fff` is the weakest saved positive ASR by mean token logprob; the other two have fragmentary/lexically unreliable saved wording. These labels describe metadata, not new ground truth about what was spoken. All survive from audio alone. **No confirmed nonsense/nonlexical speech recording exists in the frozen corpus.** Metadata substitution proves text independence, not general gibberish recall. No claim of full language diversity validation is made.

## Unresolved case (not scored)

| File | Category | Old | Silero | Peak p | Median p | Speech s | Longest s | Regions | First s | Last s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 277e9941 | unresolved | reject | reject | 0.048610 | 0.002793 | 0.000 | 0.000 | 0 | — | — |

Its prior failed ASR does not justify changing the frozen label. No case is removed to improve the result.
