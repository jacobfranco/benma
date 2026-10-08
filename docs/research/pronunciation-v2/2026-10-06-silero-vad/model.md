# Pinned official model and exact semantics

The evaluation uses the official [snakers4/silero-vad project](https://github.com/snakers4/silero-vad), published as [silero-vad 6.2.3](https://pypi.org/project/silero-vad/6.2.3/). The selected model is the normal stateful ONNX model selected by `load_silero_vad(onnx=True, opset_version=16)` in that package. No alternate weights, sequence model, JIT model or VAD family was evaluated.

## Provenance

| Item | Exact value |
| --- | --- |
| Package/version | `silero-vad==6.2.3` |
| Official repository | `https://github.com/snakers4/silero-vad` |
| Evaluated artifact | `silero_vad-6.2.3-py3-none-any.whl` |
| Wheel size | 11,317,527 bytes |
| Wheel SHA-256 | `7b7f5436cfcb02fae583a05b512ea96467fd449fe54cb49a5e4f06c51a1e43b8` |
| Published wheel timestamp | 2026-09-23 11:37:20.002180 UTC (saved package metadata) |
| Source commit | Not encoded in the published wheel; no Git checkout used. Exact package version and source/model hashes pin the evaluated implementation. No unverified commit is asserted. |
| Model filename | `silero_vad/data/silero_vad.onnx` |
| Model size | **2,327,524 bytes / 2.220 MiB** |
| Model SHA-256 | `1a153a22f4509e292a94e67d6f9b85e8deb25b4988682b7e174c65279d8788e3` |
| Official `utils_vad.py` SHA-256 | `15d0f6b3ef9590e22ca2f146e1436f6901da356cb552d3183df4100862b333cb` |
| Official `model.py` SHA-256 | `40762a80d1278605480f75f90c6510c1a4ab71bd230f45c334e4f9c5e402181d` |
| License | MIT; copyright 2020-present Silero Team |
| Packaged license SHA-256 | `2e63e9a38b6e8fc0c7bc37ce174caca1862870856c6daf5697cfb785e925520b` |
| Inference backend | `onnxruntime==1.23.2`, `CPUExecutionProvider` only |
| Official wrapper dependencies used | Python 3.12.13, Torch 2.8.0+cpu, NumPy 2.3.3 |
| Session configuration | One intra-op thread, one inter-op thread, batch size 1 |
| Input/output state | Audio `input`, recurrent `state` (2 × 1 × 128), int64 `sr`; probability and updated state |

[Machine provenance](model-provenance.json) records the exact wheel URL and download digest. The authorized one-time package and runtime setup was completed before the closing instruction. There were no later downloads. A wheel may contain other bundled formats; only the model named above was loaded or evaluated.

Weights and extracted upstream source remain under `services/api/var/silero-vad/upstream/`, ignored by Git. ONNX/plot/test packages are in `services/api/var/silero-vad/deps/`; the pre-existing research Torch/SciPy environment was reused. Production dependencies and runtime configuration were not edited. [Research package inventory](environment.json) lists installed versions without treating them as production dependencies.

## Audio preprocessing and probability meaning

The official model supports 8 kHz and 16 kHz, using 256 or 512 new samples respectively (32 ms in either case). At 16 kHz the upstream wrapper carries 64 preceding context samples (4 ms), initially zero, and recurrent state across chunks. Both reset between utterances. Context is not counted as additional audio duration.

All **48 frozen inputs are mono PCM16: 46 at 16 kHz, two at 24 kHz**. The two cached digital variants, `native_gain` and `native_bandlimit`, each contain 25,200 input samples (1.05 s), normalized to 16,800 samples at 16 kHz. The other 46 are sample-exact after numeric PCM decoding. Decoding divides signed int16 by 32768 into float32. There is no gain/peak normalization, denoising, DC removal, pitch-dependent transform, text conditioning or added speech padding. The last input chunk is zero-padded to 512 samples for inference only; its actual valid end and padded window end are recorded separately.

The audio adapter uses `scipy.signal.resample_poly` (SciPy 1.16.2, default Kaiser beta 5 window, constant padding) for those two 24 kHz variants. Unit tests additionally exercise 8/24/44.1/48 kHz normalization to 16 kHz and verify duration, sample count and preserved sinusoid frequency/amplitude. The numerical unit fixtures do not add evaluation recordings. This explicit resampling path differs from the upstream helper's simple strided decimation for integer multiples of 16 kHz, which is never invoked for this corpus. Official-helper parity checks use the same normalized float32 audio supplied to primary inference, not an unsupported direct 24 kHz call. The original 24 kHz identities remain preserved and hash-checked; no audio files are rewritten.

Each raw float is the model's speech score for one 32 ms step, conditioned on preceding audio/state. It is named a probability by upstream, but is **not a calibrated probability of the intended speaker being present**, nor independent proof of a human source. Report timestamps locate the input chunk; they are not ASR word times. Medians/quantiles weight each chunk equally, including the final partial chunk; time-above-threshold measurements clip that chunk to its actual valid duration.

All 48 timelines were written to disk **before** running any segmentation helper on that recording. They retain 3,681 full-precision probabilities, valid and padded timestamps, sample rates, window/context size, waveform hash and model/runtime provenance. Nothing was reduced to a boolean before preservation.

## Default segmentation, directly from the pinned implementation

The audit calls the unmodified official `get_speech_timestamps_from_probs`; tests compare it with the official `get_speech_timestamps` on every waveform.

| Parameter | Evaluated default and actual behavior |
| --- | --- |
| Speech threshold | **0.5**, start when probability **≥ threshold** (the docstring's wording “ABOVE” is less precise than the executable comparison) |
| Negative/exit threshold | `max(threshold - 0.15, 0.01)`, default **0.35**; silence starts at **p < exit threshold** |
| Minimum speech | **250 ms**, keep only when unpadded region length is **strictly greater than** this value |
| Minimum silence | **100 ms** below exit threshold; evaluated on the 32 ms grid (normally 128 ms between first low frame and confirmed exit) |
| Speech padding | **30 ms each side**, after minimum-length filtering, clipped to the actual waveform; adjacent padding is adjusted by upstream |
| Maximum speech | Infinity; no length-based splitting exercised |
| Chunk size | Fixed 512 samples at 16 kHz; `window_size_samples` in the official helper is deprecated and ignored |
| End of file | Still-triggered region is measured to actual audio length, not the padded window length, then subjected to the same strict minimum |
| Whole-utterance decision | At least one official speech region returned |

Threshold sweeps retain the upstream formula for the exit threshold; no second independently tuned parameter is introduced. Default raw probabilities are reused unchanged. Returned sample coordinates are divided by 16,000 directly, avoiding the upstream optional seconds-output rounding.

## Practical CPU path and equivalence

Primary evaluation uses the official `OnnxWrapper` with CPU enforced. The research `NumpySilero` adapter implements the same input/context/state operations using NumPy and the **same exact ONNX weights**. It matches every official probability and metadata frame bit-for-bit on all 48 cases. This is a runtime feasibility check, not another model experiment or decision policy.

The NumPy inference path can run without Torch. Its warm end-to-end timing still uses the official scalar segmentation helper in the research process; a production implementation would need to isolate that helper from the official module's Torch import while preserving tested semantics. No such integration is performed or recommended by this result. Runtime state must remain per utterance; the official mutable wrapper must not be shared unsafely between interleaved requests. The measured CPU is an Intel i7-10700F; production-host throughput and request concurrency were not benchmarked.
