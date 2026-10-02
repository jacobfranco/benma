# Capability inventory from the repository and local environments

Inspected locally; no web lookup, provider call, package installation, model or dataset
download. Started on clean `pronunciation-v2-research` at `2f04fc5` (timing/reading
separation), following `831f348` (connected-speech harness). Read the mapping architecture,
replay results, validation, schema and previous frozen-feature implementation. No mapping
logic was changed or rerun. Original `/tmp/benma-study-S{01,02,03,13}` records and their
referenced WAVs exist; hashes and unchanged evidence were checked against the completed
local `mapping-v2-reviewed` records.

## Code inventory

Paths below are repository-relative.

| Existing capability | Inspected code | What it supplies / limitation |
| --- | --- | --- |
| Whole-recording acoustics | `services/api/src/benma_api/pronunciation/acoustics.py` | Praat autocorrelation, alternate filtered track, raw/tracker/selected F0, energy, candidate strengths, spectral contamination and quality flags; numeric measurements, not observed phones |
| Alternative benchmark trackers | `benchmark/acoustics/pitch.py` | Autocorrelation, Parselmouth and optional torchcrepe adapters; not run or modified |
| Contour filtering and display | `services/api/src/benma_api/pronunciation/contours.py` | Reliability filtering, display contours, contour interpretation; display geometry is not a new measurement. No filtering/classification invoked here |
| Conservative pitch-region selector | `services/api/src/benma_api/pronunciation/evidence_region.py` | Signal-supported weak boundary exclusions; tone-evidence support, not phone segmentation. Inspected but not reused to alter saved evidence |
| Explicit mapped timing | `benchmark/pronunciation_v2/connected_mapping.py`, `connected_speech_probe.py` | Exact provider grapheme intervals, no equal subdivision. `pitch_region` slices saved frames using existing usability and missingness rules |
| Truth-separated schema | `connected_schema.py`, `connected-speech-schema.json` | Perception, nullable reading, timing, reference-conditioned phones, acoustics, target comparison and abstaining judgment are separate. No schema/API change |
| Forced alignment | `benchmark/acoustics/alignment.py` | TextGrid parser, Montreal forced-aligner wrapper and replay adapter. Requires transcript; an aligned phone is not independently recognized. No invocation |
| Previous local diagnostic graphics | `benchmark/acoustics/plot.py`, `benchmark/pronunciation_v2/forensics_plots.py`, `acoustic_forensics.py` | Deterministic SVG/pitch and waveform investigations. Reused only low-level SVG drawing; old target/prediction-bearing figure templates were unsuitable for blinding |
| Frozen pretrained features | `benchmark/pronunciation_v2/features.py` | Waveform-only ffmpeg decoding, frozen/eval encoder, output-after-block indexing, valid-frame mean pooling, repeat/state-hash checks. Reused without experiment entry points or fitted heads |
| Segmental utilities | Searches of production pronunciation and research modules | No established independent Mandarin phone decoder or validated vowel/initial classifier found; no existing accepted formant pipeline or reusable generic spectrogram extractor found |

## Installed environments

| Package/tool | API environment | Isolated research environment |
| --- | --- | --- |
| Python executable | `services/api/.venv/bin/python` | `benchmark/pronunciation_v2/.venv/bin/python` |
| NumPy | 2.5.3 | 2.3.3 |
| Praat/Parselmouth | 0.4.7, embedded Praat 6.1.38 | absent |
| SciPy | absent | 1.16.2 |
| Torch | absent | 2.8.0+cpu |
| Transformers | absent | 4.57.6 |
| scikit-learn | not needed | 1.7.2, unused here |
| pypinyin | 0.55.0, preparation already has resolved records | 0.55.0, unused here |
| pytest | 9.1.1 | absent |
| matplotlib / librosa / soundfile / torchaudio | absent | absent |

Root `.venv` has development tools and Pydantic, not the acoustic stack. Ruff 0.16.1
runs there. Local system ffmpeg n9.0.1 decodes audio; existing `rsvg-convert` rasterizes
SVG for visual checks. No plotting dependency was installed. SVG plots use the repo's
existing deterministic drawing helper and NumPy FFT.

The isolated research environment also lacks Pydantic. Consequently the embedding
launcher is run as a direct script using sibling research modules, avoiding
`benchmark.__init__` and API dependencies. The first attempted `python -m` launch failed
before loading the model; the corrected standalone launch succeeded without installs.

## Available now, unused, and missing

- **Already computable:** interval duration, waveform, digital RMS/peak, near-full-scale
  fraction, saved pitch and candidate strength, saved voiced support/missingness,
  normalized pitch and existing contamination/instability flags. This pass adds frame
  spectra, consistent spectrograms and constrained Burg feasibility using installed tools.
- **Installed but previously unused for this task:** Parselmouth `to_formant_burg` and
  formant bandwidth queries, now exercised; harmonicity/HNR methods remain unused.
  HNR would be a separate periodicity estimator with its own assumptions, not independent
  phone identity, and was not added merely because the method exists. SciPy and sklearn
  are installed in the model environment but unused in this audit.
- **New dependency if those specific conveniences were desired:** matplotlib, librosa,
  soundfile/torchaudio, or torchcrepe in the selected environments. None is necessary for
  the completed probe. Model/data requirements of optional adapters would need separate
  verification before any future use.
- **New model download:** any independently decoding Mandarin/multilingual phone model
  not found in the inspected cache. The default `~/.cache/huggingface/hub` is absent;
  the relevant existing cache is `~/.cache/benma/pronunciation-v2-model/hf/`.
- **Training / labeled validation:** converting generic features or base embeddings into
  Mandarin phone labels or learner-specific correctness estimates. A separately obtained
  pretrained decoder could avoid local training for recognition, but still needs empirical
  validation on this use case. This pass trains nothing.
- **Not obtainable independently with current validated tools:** observed phone identity,
  phone boundaries, vowel/final correctness, initial correctness, tone correctness, or
  an acoustic cause for a lexical substitution/self-reported issue. Reference phones,
  provider scores and intended readings cannot fill those gaps.

## Cached model and what was actually extracted

`facebook/wav2vec2-base`, revision
`0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`, is fully cached. Weight SHA-256:
`3249fe98bfc62fcbc26067f724716a6ec49d12c4728a2af1df659013905dff21`.
Weights, config and preprocessor hashes match the existing Experiment #1 checkpoint
receipt. The cached model card describes English/LibriSpeech audio pretraining and no
tokenizer: the base encoder does not independently emit Mandarin phones.

Extracted twelve **768-dimensional** vectors from **transformer block 6**, mean over
all unpadded hidden frames of each isolated crop. CPU FP32, frozen eval, eager attention,
checkpoint zero-mean/unit-variance waveform normalization, no augmentation, four Torch
threads, deterministic algorithms, one crop per forward. Crops use 4–22 hidden frames;
both 90 ms crops yield only four. Every crop was repeated bitwise identically. Encoder
state hashes match before/after; no gradients. Unused pretraining-head checkpoint keys
are expected; no acoustic encoder keys were missing/mismatched. No trained tone head,
Experiment #1/#2/#3 selection/evaluation, PCA or correctness calculation ran.

These embeddings are technically attachable as future model inputs. No coordinate has
an established phonetic meaning for this packet, and pooling removes temporal detail.
Short isolated crops lose neighboring context; English pretraining and connected-speech
transfer are unresolved limitations. The embeddings do not improve the current human
interpretation by themselves.
