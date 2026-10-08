# Tracker inventory and dependency hygiene

Six fixed candidates after the final RMVPE extension. Only RMVPE is new in this pass; one predeclared native-confidence sweep of five nearby values is permitted. No per-character configuration, training, or production integration.

| Candidate | Family and fixed configuration | Exact implementation | License | Model / installed package bytes |
| --- | --- | --- | --- | --- |
| Praat AC | Current production native estimator; 50–550 Hz, 10 ms, jump cost .5, octave cost .01, V/UV cost .14, silence .03, voicing .45, 15 candidates, accurate=false | Parselmouth 0.4.7, embedded Praat 6.1.38 | GPLv3 | No model; Parselmouth 37,098,068 bytes |
| Praat CC | Cross-correlation with the same exposed parameters; native cadence/edge handling retained | Same Parselmouth/Praat | GPLv3 | Shared package, no model |
| pYIN | Probabilistic YIN + native Viterbi; 50–550 Hz, 64-ms window, 10-ms hop, centered constant padding; other 0.11.0 defaults | librosa 0.11.0 | ISC | No model; librosa itself 1,000,772 bytes, plus scientific/Numba stack |
| WORLD Harvest | Native Harvest output; 50–550 Hz, 10-ms frame period; no DIO or StoneMask extra candidate | pyworld 0.3.5 | MIT wrapper; bundled WORLD BSD-style license | No model; built package 2,913,486 bytes, NumPy |
| CREPE full | Fixed full model, 50–550 Hz, 10-ms hop, native preprocessing, CPU batches of 128, one global native Viterbi decode; fixed seed for upstream bin dithering | torchcrepe 0.0.24 source revision `19e2ec3d494c0797a5ff2a11408ec5838fba6681`; Torch 2.8.0+cpu | MIT implementation/converted weights; Torch BSD-3-Clause | **88,991,291-byte model**; existing Torch package 677,949,780 bytes |
| RMVPE | Whole utterance, CPU float32, 16 kHz, 10 ms, all 360 bins (31.7–2005.497 Hz), native local-average decode with max salience >.03; optional confidence-only >.05 view | RVC source `81eed5e8f68b6bed1789f682fe78cdd324495afc`, unmodified `infer/rmvpe.py`; Torch 2.8.0+cpu | MIT source; model repository declares MIT | **181,184,272-byte checkpoint (172.79 MiB)**; reused research Torch/librosa/scientific stack; no production dependencies added |

Package sizes above sum installed distribution RECORD files and exclude undeclared/shared transitive dependencies. They are not compressed download sizes or additive deployment-image forecasts. Parselmouth and Torch were reused from existing local environments. pYIN/Harvest/plotting dependencies were installed only in `/tmp/benma-f0-bakeoff/.venv`; app manifests and lockfiles were untouched.

## Original five-tracker inventory before installation

- API environment: NumPy 2.5.3 and Parselmouth 0.4.7 present; no SciPy, pYIN/librosa, WORLD, Torch, CREPE, RMVPE, matplotlib or ONNX Runtime.
- Existing isolated pronunciation research environment: NumPy 2.3.3, SciPy 1.16.2, Torch 2.8.0+cpu present. No installed pitch-model package/checkpoint. The cached wav2vec2 encoder is not an F0 estimator and was not used.
- Relevant UV/package/model caches: librosa package metadata/source and Torch/torchcrepe metadata existed; **no CREPE full/tiny or RMVPE weights** were found. Metadata is not a cached runnable model.
- The legacy Python normalized-autocorrelation fallback was not a serious extra candidate: it does not supply the requested independent mature/neural comparison. DIO, tiny CREPE and RMVPE were not run, preserving the five-candidate limit.

## Original five-tracker model download

Only `torchcrepe/assets/full.pth` was downloaded. Its SHA-256 is:

`133225604dedd2e4005f8bbd1bd0a2ec073ba8b7a6cd31ff6d5edbbfa3539986`

Size: **88,991,291 bytes / 84.87 MiB**. Source:
[pinned upstream checkpoint](https://github.com/maxrmorrison/torchcrepe/blob/19e2ec3d494c0797a5ff2a11408ec5838fba6681/torchcrepe/assets/full.pth).
The pinned MIT license, source files, setup metadata and per-file download/hash receipt are stored beside it in `/tmp/benma-f0-bakeoff/vendor/torchcrepe-source/`.

The PyPI torchcrepe package bundles two models. Instead of downloading that bundle, this pass fetched the small inference source files and **only the full checkpoint**. No second model, cloud inference, provider request, training, or fine-tuning occurred. Model loading uses upstream `torch.load(...,weights_only=True)`.

The selected source version reports 0.0.24 in `setup.py`; its exact Git revision is pinned because version alone does not identify an uninstalled source tree. The research `.pth` points to that local source. Torchaudio 2.8.0+cpu was installed without dependencies from the official CPU wheel index to match existing Torch. Resampy 0.4.3 supplies upstream resampling. No replacement Torch/CUDA runtime was downloaded.

## Confidence and decoding caveats

Praat strength is candidate periodicity, not speech probability. pYIN exposes native voiced decisions and voiced probabilities. Harvest's public wrapper exposes F0/voicing-by-zero but no comparable confidence. CREPE supplies a pitch for every frame and periodicity; its raw output has **no native unvoiced mask**. That behavior is preserved rather than hidden in normalization.

The common optional cleanup uses original native decisions, low native-confidence rejection where available, a common −60-dBFS RMS floor, and removal of islands shorter than 30 ms. Thresholds are fixed at Praat .45, pYIN .1, CREPE .21; none is invented for Harvest. They are conceptual counterparts, not calibrated equivalent probabilities. There is no smoothing, interpolation, octave correction, range adaptation, or character rule in cleanup. Raw results remain the primary comparison.

CREPE is a learned F0 baseline, not a claim to evaluate the newest possible architecture. A single model does not represent every neural estimator. Its implementation's global decoder and fixed dithering seed are specified in [architecture.md](architecture.md).

Primary implementation references: [Parselmouth API/version](https://parselmouth.readthedocs.io/en/stable/api_reference.html), [librosa pYIN API](https://librosa.org/doc/0.11.0/generated/librosa.pyin.html), [torchcrepe implementation and confidence guidance](https://github.com/maxrmorrison/torchcrepe), and [WORLD wrapper license](https://github.com/JeremyCCHsu/Python-Wrapper-for-World-Vocoder/blob/master/LICENSE). These were documentation/source reads, not inference API calls.

## Final authorized RMVPE download and native semantics

The one new model is `rmvpe.pt`, SHA-256 `6d62215f4306e3ca278246188607209f09af3dc77ed4232efdd069798c4ec193`, [pinned model source](https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/e6d0c1a17da07c33557852f9dfa2bd44cc75737d/rmvpe.pt). The [source implementation](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/81eed5e8f68b6bed1789f682fe78cdd324495afc/infer/rmvpe.py), licenses, source-file hashes and receipt are documented in [rmvpe.md](rmvpe.md) and [rmvpe-download-receipt.json](rmvpe-download-receipt.json).

RMVPE raw explicitly emits zero/unvoiced when the largest of 360 sigmoid saliences is ≤.03. This is represented as null with confidence retained. The maximum is not a calibrated speech/learner-presence probability. No high floor excludes 54–70 Hz. Full salience and ungated native decode are saved locally; the .01/.02/.03/.04/.05 sweep is one generic native-threshold sensitivity experiment. Native raw and optional .05 views never pass through Benma filters. Source/model bytes remain ignored research artifacts; no pip/production manifest change occurred.
