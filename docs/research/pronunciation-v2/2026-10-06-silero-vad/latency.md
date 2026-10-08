# CPU deployment is practical; quality blocks integration

Measured on **Intel Core i7-10700F @ 2.90 GHz**, Linux x86-64, 16 logical CPUs available, using **ONNX Runtime 1.23.2 CPUExecutionProvider** with one intra-op and one inter-op thread per session. No GPU was used. Model size is **2.220 MiB**. [Raw timings](latency.json) retain every measurement and platform detail.

Primary results use the official wrapper. A minimal NumPy wrapper around the **same model** was already verified bit-for-bit against all official corpus probabilities. This tests the cost of removing Torch tensor conversions; it does not evaluate another model, weights file, threshold or VAD policy.

| Warm CPU measurement | Official wrapper | Same-model NumPy path |
| --- | --- | --- |
| Representative clip | `human_control`, 2.8560625 s | Same exact waveform/hash |
| Representative total median | **14.758 ms** | **10.944 ms** |
| Representative total p95 | 15.321 ms | 11.306 ms |
| Representative median real-time factor | **0.00517** | **0.00383** |
| Corpus total median | **11.590 ms** | **8.627 ms** |
| Corpus total p95 | **24.496 ms** | **18.214 ms** |
| Whole-waveform total median (excerpts excluded) | 13.989 ms | 10.335 ms |
| Whole-waveform total p95 | 33.801 ms | 25.082 ms |
| Raw inference median / p95 | 11.438 / 24.326 ms | 8.483 / 18.042 ms |
| Segmentation + summary median / p95 | 0.148 / 0.224 ms | 0.143 / 0.211 ms |
| Corpus median / p95 real-time factor | 0.00522 / 0.00671 | 0.00389 / 0.00519 |

Warm timing uses **nine sequential repeats ×48 cases ×2 wrappers =864 measurements**. Wrapper order alternates between repeats. Corpus quantiles pool cases and repeats; whole-waveform quantiles exclude all ten excerpts. Neither represents independent users or loaded server latency. Timing includes in-memory WAV decoding, normalization, recurrent inference, timestamp creation, and official segmentation/summary. The two cached 24 kHz variants include their 24-to-16 kHz polyphase resampling cost; the other 46 inputs and the representative human clip require no resampling. Timing excludes filesystem reads, artifact writes, ASR, network, audio capture and pitch extraction. Real-time factor is processing seconds divided by waveform seconds.

## Model load and memory

Five fresh processes per wrapper were measured before warm timing. OS filesystem caches were not flushed, so these are process-cold starts with likely warm file cache, not first-boot deployment measurements. “Import + load” includes backend import and ONNX session/weights construction; it is not a separately isolated session-load-only measurement.

| Cold measurement | Official wrapper median / p95 | Same-model NumPy path median / p95 |
| --- | --- | --- |
| Backend import + model load | **794.213 / 854.257 ms** | **70.068 / 70.308 ms** |
| First inference, representative clip | 14.923 / 15.191 ms | 11.127 / 11.396 ms |
| Whole child-process wall time | 1114.037 / 1161.533 ms | 190.328 / 205.994 ms |
| Process peak RSS | 293.434 / 293.512 MiB | 76.625 / 76.833 MiB |

Process wall time includes Python/NumPy startup, complete corpus hash verification, model setup, first inference and process exit. Peak RSS is the process high-water mark, not a model-only allocation. The very first default evaluation's recorded import/load was 960.168 ms; it is preserved separately in model provenance and is not substituted for the repeated cold measurements.

The NumPy cold process runs the Torch-free raw inference path only. Its warm totals use the official scalar segmentation helper in the parent research process. A real ONNX-only service would need to separate that helper from Torch imports and preserve exact behavior. This straightforward implementation consideration is distinct from the quality failure; there is no production integration in this pass.

## Scheduling implication (conceptual only)

A preloaded VAD **before ASR** would add roughly 11–15 ms on the measured 2.856 s clip before dispatching ASR, while avoiding ASR work on rejected audio. Running it **concurrently with ASR** could overlap almost all that computation and minimize valid-turn critical-path latency, at the cost of starting ASR for later-rejected clips. Pitch can remain independent alongside ASR. Actual savings depend on the deployment host and request load; no new ASR call or concurrency benchmark was made.

For streaming use, 32 ms input chunks, context, onset evidence, the >250 ms region minimum and the 100 ms silence rule are algorithmic delays distinct from CPU runtime. This pass measures uploaded whole utterances; it does not certify streaming responsiveness. A persistent CPU session avoids repeated cold loads, and recurrent state must be isolated per utterance.

**SILERO PRACTICAL FOR CONVERSATIONAL CPU USE** is the deployment decision. It does not override the failed presence criterion. No scheduling or production changes are recommended for this model under the current acceptance result; added production latency remains **0 ms**.
