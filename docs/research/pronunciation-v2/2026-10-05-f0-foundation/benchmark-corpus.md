# One fixed offline corpus

The benchmark has **49 audio files**: all 32 canonical recordings in the prior frozen October 2–4 inventory, one exact cached digital reference, three deterministic derivatives of it, ten harmonic known-F0 controls, and three synthetic negatives. No recording was collected or uploaded. No database or provider was needed: the saved inventories and local bytes suffice.

[corpus.csv](corpus.csv) records every file's identifier, role, duration, sample rate, byte size, recomputed SHA-256, and available original/utterance/perception provenance. All 32 canonical **and original** capture hashes were verified against the frozen inventory before extraction. The one previously failed-perception recording is included as an unlabeled acoustic case; successful text is not a prerequisite to tracking.

Local absolute source paths and diagnostic time windows are in `/tmp/benma-f0-bakeoff/manifest.json`. Original audio stays in the pre-existing ignored `services/api/var/audio/` store. Generated audio stays under `/tmp/benma-f0-bakeoff/audio/`. No user audio, model weights, provider payload, or full raw frame output is added to tracked files.

## Direct digital control

`native_24k` is the exact 1.050-second, 24-kHz, mono PCM16 Azure cache asset for 我要一个苹果, reference ID `d1272f79-c791-4eb4-973c-3864cc1af03d`, voice `zh-CN-Xiaochen:DragonHDLatestNeural`. Its SHA-256 is `ec96b80ac58bab2941badf3401a135810eb8737b41816337af0f2a2d3b70e9c9`.

**No character timing is required or used.** Each estimator sees the entire file. This resolves the prior audit's character-calibration blockage for the present utterance-level question. The exact source contains late weak/irregular phonation: digital cleanliness does not make every frame a known, single-valued vocal fundamental.

Three fixed benign changes, with no augmentation sweep:

- `native_16k`: the exact ffmpeg command from app canonicalization; resulting hash `88e6b9325b545a1c16e893f18b65b7645d2cfd7ccab7f35fb5df1b6788228fbe` matches the previous independent canonical replay.
- `native_gain`: original samples multiplied by .25 (−12.04 dB), then PCM16 quantization at 24 kHz.
- `native_bandlimit`: third-order 100–3500-Hz Butterworth bandpass, forward/backward zero-phase application, PCM16 at 24 kHz. This is a controlled spectral perturbation, not a simulation or proof of a particular phone's capture chain.

Original-versus-derivative comparisons use the same actual times, without DTW. Each tracker's native sample-rate handling remains part of the test.

## Repeated and human controls

| Research label | Perception prefix | Role |
| --- | --- | --- |
| take_1 | 48c71bb4 | Newest clean playback, chronological first; exact provider not encoded |
| take_2 | cabf8d61 | Newest clean playback, chronological second; different timing/prosody possible |
| take_3 | 0cb79e67 | Newest clean playback, chronological third; closest acoustic match to take_1 in prior audit |
| google_old | c19a5a74 | User-identified Google playback with previous sustained low/subharmonic path |
| human_control | 422877d2 | User-identified human, previously healthy later rising region |
| 0f4107fe, 484e80c0, 5ca771a7, e0c56934 | Same prefixes | All earlier matching sentence captures in the inventory; persisted text alone does not prove playback source |

All nine speech captures in this lookup family are tracked whole. All 36 pairs receive audio-only spectral alignment, but the 33 pairs outside the newest trio are contextual comparisons, **not known repeated-source trials**. The three newest pair comparisons are reported individually; take_1/take_3 is the strongest repeatability check. No digital Azure source is presumed to be the source of Google or an unlinked capture. Cross-source absolute F0 differences are not called estimator error.

## Difficult speech and low F0

The full inventory includes historical/current 贵州 cases (`f5dc0cc1`, `9b1d959a`, `87ac7dd1`, `f47fadb3`), all four previous 吧 failures (`f3c642b5`, `e59a6350`, `209ef0c7`, `dccf8a63`), the T3-heavy sentence family including long low-register `7787300e`, and ordinary speech from the prior replay. Text is only a case-lookup label; tones and lexical expectations are never measured or scored.

Saved regions that happened to correspond to 一/苹/州/吧 are post-hoc diagnostic windows. They are evaluated **after** global extraction. Previous low-F0 protection criteria are replayed as a biased acoustic safety proxy and explicitly distinguished from independent F0 ground truth. A small additional set of clearly harmonic voiced regions and stationary pauses is marked by semi-blinded visual inspection, using only elapsed time and spectral structure; its provenance and uncertainty are in `benchmark/pronunciation_v2/f0_acoustic_windows.json`.

## Negative controls

All three known real controls are included, regardless of their hallucinated persisted text:

- `silence_original`: `de4b999e-a527-4613-8709-618c68716477`.
- `silence_periodic`: `ab6c16ab-ece9-4d00-a3f9-ca693d103624`.
- `silence_accidental`: `7e489fd3-c36d-41f6-a20b-300616ad1a42`, latest known accidental-silence false accept.

Digital silence, seeded stationary Gaussian noise, and two brief clicks supply additional negatives. The synthetic interrupted-voice signal supplies a known noise gap with voiced context on both sides. Real stationary pauses are evaluated separately from complete negative recordings. Periodic background can have a physical fundamental; calling it false speech pitch here means it is unsafe to present as vocal evidence, not that no periodic sound exists.

## Synthetic definitions

All ten controls are 2 seconds at 16 kHz, with active excitation from .2 to 1.8 seconds, 25-ms attack/release, peak amplitude .22, and twenty phase-coherent harmonics weighted by `1 / harmonic**1.2`. They are deterministic; no external data or language model is involved.

1. Four steady controls at 70, 110, 180 and 260 Hz.
2. Rise: 90 Hz × `2**(1.7*u)` over normalized active time `u`.
3. Fall: 280 Hz × `2**(-1.7*u)`.
4. Shallow valley: `120 + 55*(2*u-1)**2` Hz.
5. Octave-risk mixture: 110-Hz F0; second harmonic ×5; odd harmonic amplitudes vary continuously between .15 and 1 times their base values.
6. Weak fundamental: 110-Hz F0; first harmonic ×.03 and second harmonic ×5; higher odd harmonics remain, so the true waveform period is still 110 Hz.
7. Interrupted voice: 110 Hz with independent Gaussian noise (RMS .035) replacing .8–1.1 seconds.

Negatives are 2 seconds of zeros; seeded Gaussian noise with RMS .006; and impulses at .5 seconds (one sample, .5 amplitude) and 1 second (16-sample Hann pulse, .3 amplitude). The seed is 20261005. The analytic frequency laws, 10-ms truth grid and generated audio hashes are reproducible from the harness.

Synthetic accuracy excludes ±80 ms around each known excitation/gap edge to separate steady-state estimation from finite-window transition effects. Full raw/cleanup tracks and whole-file coverage remain available, and edge/gap behavior is visible in the viewer. Errors are absolute semitones; multiply by 100 for cents. Synthetic success cannot establish real-speech correctness.
