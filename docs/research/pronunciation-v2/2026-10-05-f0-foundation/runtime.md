# CPU runtime and deployment cost

## Final RMVPE CPU measurement

On the same Intel i7-10700F CPU and one-thread protocol, pinned RMVPE requires **2.629 s explicit import/hash/model load**, **.222 s first native inference**, **.125 s warm 1.05-s native extraction**, and **.286 s warm extraction for the same 2.856-s human clip**. Human-only RTF is .100; median wall/CPU RTF across six warm calls is .113/.112. Peak verification-process RSS is **923.2 MiB**. Native frame packaging is included; activation compression and JSON writes are excluded from controlled timing.

The warm human path is approximately **101.5× faster** than saved CREPE's 29.059 s. A persistent CPU server worker is credible; GPU is not required by these measurements. Cold startup, concurrency and target deployment remain separate costs. Quality/safety failures block migration despite practical runtime.

Checkpoint size is **181,184,272 bytes (172.79 MiB)**; 90,423,165 parameters run in float32. No additional Python package was installed: the previous isolated Torch/librosa/scientific environment is reused, and production manifests remain unchanged. [Exact configuration](rmvpe.md), [individual warm calls](verification-rmvpe.json), [all 49 extraction timings](rmvpe-per-file-runtime.csv), and [six-tracker runtime CSV](runtime.csv). The original five-tracker timing narrative/table below remains the historical measurement, without reruns.

**CREPE full is not compatible with a prompt conversational response in the measured CPU implementation:** a warm 2.856-second utterance takes **29.06 seconds**, before other pipeline work. It is not rejected solely for being slower: the quality/safety failures already disqualify this configuration. Optimization could change runtime without resolving those failures.

Fresh worker processes ran each candidate serially on an Intel Core i7-10700F, 2.90 GHz, 8 cores/16 logical CPUs. Torch intra/inter-op threads were fixed to one; OpenMP/OpenBLAS/MKL environment limits were one. Praat's own internal native parallelism is not controlled by those settings, as its CPU time exceeding wall time confirms. No GPU, inference service or remote provider was used. This is one desktop CPU, not a phone or target-host benchmark.

After one first call, three warm extractions each of `native_24k` (1.050 s) and `human_control` (2.8560625 s) were measured without output serialization. First-call time includes lazy estimator import/JIT where applicable. CREPE import/checkpoint loading is measured separately before its first inference. Python startup and already-imported common harness/NumPy time are excluded; these are **not complete container cold-start measurements**. Numba's disk cache was warm from the corpus run. Peak RSS covers that tracker process's subsequent invariance checks too.

| Tracker | Explicit model import/load | First native call | Warm native median | Warm human median | Median wall RTF / CPU-time RTF | Peak process RSS |
| --- | --- | --- | --- | --- | --- | --- |
| AC | No model | .0216 s | .00303 s | .00447 s | .00226 / .00751 | 123.6 MiB |
| CC | No model | .0267 s | .00480 s | .00605 s | .00336 / .01712 | 122.7 MiB |
| pYIN | No model; lazy imports in first call | 1.3465 s | .2197 s | .5434 s | .19964 / .19919 | 275.5 MiB |
| Harvest | No model; lazy import in first call | .2359 s | .2043 s | .7309 s | .22582 / .22446 | 64.9 MiB |
| CREPE full | 1.2703 s | 11.9689 s | 10.7989 s | 29.0587 s | 10.23698 / 10.20643 | 933.8 MiB |

Wall RTF is elapsed extraction seconds divided by audio duration; CPU-time RTF uses process CPU seconds. Both are medians over the six warm runs, not the quotient of the two table medians. CREPE's measured cold model import/load plus first 1.05-second inference is ~13.24 seconds. Three repeated warm outputs per waveform are byte-identical for every tracker. [runtime.csv](runtime.csv) and `verification-*.json` retain the individual timing/hash evidence; first-pass timings for all 49 files remain in the local artifact directory.

| Tracker | Dependency/model burden | Server assessment | Mobile assessment |
| --- | --- | --- | --- |
| AC/CC | Existing Parselmouth 0.4.7 / Praat 6.1.38, 35.4-MiB installed distribution; no learned model | Existing deployment, negligible measured latency | No mobile port measured; native integration and license review required |
| pYIN | librosa 0.11.0 (~.95 MiB itself), NumPy/SciPy/Numba/LLVM dependencies; no model | CPU runtime plausible in a persistent worker; warmup/dependency cost material | Python/Numba stack is not a demonstrated mobile integration |
| Harvest | pyworld 0.3.5 (~2.78 MiB), compiled WORLD/NumPy; no model | CPU runtime plausible; voice/background quality currently poor | Native WORLD code is a possible implementation route, unmeasured |
| CREPE full | torchcrepe 0.0.24 pinned source, **84.87-MiB checkpoint**, reused Torch 2.8.0+cpu ~646.5 MiB, matching Torchaudio/resampling stack | Current full CPU path too slow and ~934-MiB RSS; acceleration/other runtimes unmeasured | No mobile export/quantization benchmark; this Python/full-model path is unsuitable as a claimed ready integration |

[Inventory](tracker-inventory.md) includes license links, exact source revision, configuration and model SHA-256. Installed distribution sizes exclude shared/transitive packages and are not compressed image/download forecasts. The full isolated added research environment is roughly 520 MiB and reuses the much larger pre-existing Torch environment through a research-only path.

CREPE uses native preprocessing, CPU batches of 128 frames, then one global Viterbi decode. Its upstream bin-to-Hz dithering is pinned to seed 20261005 and caller NumPy state restored. No audio-dependent seed, character rule or custom pitch decoder was used. The adapter's global RNG manipulation would need isolation/thread-safety work before any production use. Production dependencies and lockfiles are unchanged.

The corpus tracks initially recorded the CREPE model-hash configuration field as `see download receipt`: the extraction worker had loaded that adapter before the literal SHA was added. The downloaded weights themselves were fixed and hashed. Original raw artifacts are preserved; later fresh verification records the exact hash in canonical provenance. Do not expect those two complete JSON objects to have the same digest solely because their numeric frames agree. Within each fixed configuration, repeated extraction is byte-identical.
