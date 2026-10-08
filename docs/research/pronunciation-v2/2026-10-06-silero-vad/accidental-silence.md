# Critical accidental-silence false accept

**Silero confidently treats the labelled background as speech.** Default peak probability is **0.9976807833**, whole-clip median **0.8675193787**. It returns one padded region **1.026–2.878 s**, duration **1.852 s**. Raw scores are at least 0.50 for **1.792 s** and at least 0.90 for **1.440 s**. These are model scores, not independent source verification.

- Frozen identity: `silence_accidental`; perception `7e489fd3-c36d-41f6-a20b-300616ad1a42`.
- SHA-256: `fcaf551459dc957c7544e396858395e4214c2447aa23cc577a2f9c5261b28eaf`.
- Duration: **3.1346875 s**, mono PCM16 / 16 kHz.
- All **98 raw probability frames**, including the final partial chunk, are preserved in [the timeline](probabilities/silence_accidental.json).

![Waveform, spectrogram, Silero probability and the existing energy/periodicity cells](figures/silence_accidental.png)

## Relationship to the existing guard

| Interval | Position | Raw probability range | Median over overlapping chunks | Time p≥0.50 | Time p≥0.90 |
| --- | --- | --- | --- | --- | --- |
| Longest old energy activity | 2.390–2.680 s | 0.987175–0.997681 | 0.993976 | 0.290 s | 0.290 s |
| Longest old periodic run | 0.567344–1.037344 s | 0.004384–0.054756 | 0.009497 | 0 | 0 |
| Entire clip | 0–3.134688 s | 0.001670–0.997681 | 0.867519 | 1.792 s | 1.440 s |

The old guard's 290 ms energy event is completely inside Silero's speech region. Silero also stays ≥0.50 for **1.502 s outside that event**, and ≥0.90 for **1.150 s outside it**. The failure is therefore not an isolated energy spike triggering one neural frame. The model scores a much broader span of activity as speech.

The longest early periodic run that helps keep the existing absence guard open receives low Silero probabilities. Periodicity continues in later regions, but it is insufficient by itself to explain the neural response: Silero remains low during early periodic background, then rises at approximately **1.056 s** as the later bursts begin. The other frozen periodic-silence recording has peak **0.048586** and is rejected. This separates the old hum problem from the current speech-like false accept.

The overlay replays only the exact existing guard configuration. Energy uses centered RMS on 20 ms windows with a 10 ms hop and the existing 3×background threshold; orange spans depict start-aligned 10 ms decision cells. Thus the 290 ms run's analysis windows extend through approximately 2.690 s even though its counted cells end at 2.680 s. Purple spans depict 10 ms cells around the existing Praat presence-view timestamps. They are diagnostic intervals, not changes to `UtterancePitchTrack`, pitch eligibility, or another tracker evaluation. [Exact overlays](accidental-overlays.json), [probability interval measurements](accidental-analysis.json).

## Why a general VAD may respond this way

The waveform contains multiple changing bursts rather than only stationary low hum: visible events around 1.1–1.5 s, 1.75–1.9 s and 2.4–2.7 s. The spectrogram shows harmonic structure with moving energy concentrations extending well above the low-frequency floor. This temporal and spectral pattern overlaps properties of speech, including accepted phone/playback controls.

The preceding frozen feature report measured **87.57% of STFT power in 300–4000 Hz**, **8.63% below 150 Hz**, and a speech-band envelope p90/p20 ratio of **34.73**. Those existing measurements are quoted for context; the five acoustic policies were not rerun. Silero's rise with the changing higher-band structure is **consistent with a learned response to speech-like spectrotemporal patterns**. This is an inference from the plots, not a causal attribution to individual model features.

The evidence does **not** establish a precise physical source. It cannot distinguish distant/background speech, playback, another harmonic source, or a capture artifact with certainty. Silero probability is not proof that the user spoke, and it does not establish intended-speaker identity. The supplied negative label stays unchanged. Reinterpreting this file as a positive would evade the requested product criterion.

The previous saved text-conditioned alignment spans 0.96–2.96 s, broadly overlapping the response. There are no saved ASR token/word times, and alignment is not independent speech-presence truth. Neither alignment nor ASR was supplied to Silero or used to rescue any decision; no new provider call was made. [Prior forensics](../2026-10-06-speech-presence/failure-forensics.md).

The result supports a narrow conclusion: **this official VAD does not resolve this labelled trust failure**. It improves other negatives and preserves low-F0 controls, but cannot qualify for integration under the frozen acceptance criteria.
