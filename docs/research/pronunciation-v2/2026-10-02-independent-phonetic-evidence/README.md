# Independent phonetic evidence: offline reconnaissance

Completed on `pronunciation-v2-research`, following the committed timing/reading mapping
pass (`2f04fc5`). **Benma can obtain independent numeric acoustic evidence from the
supplied regions, but cannot yet identify or judge Mandarin segments from it.**
Production grading, schema, F0 extraction/selection, readings and provider timing logic
are unchanged. No network call, model download, training, deployment, commit or push.

## Results

- Twelve regions: nine requested cases, plus controls **S02 我**, **S03 你**, **S03 想**.
  Controls were ranked by saved usable-pitch coverage among eligible S02/S03 regions,
  excluding focal/user-reported/deliberately manipulated cases. Scores were not used.
- **12/12** have measurable waveform, duration, RMS and generic spectrum.
- **7/12** have a supported nucleus *candidate analysis window*; **5/12** have enough
  prefix FFT frames for generic spectral inspection. These are not phone boundaries.
- **6/12** yield finite raw F1/F2/F3 estimates; **0/12** pass the preregistered formant
  summary guards. Abstention does not diagnose a vowel error.
- Saved pitch is unchanged: **9/12** have any usable selected F0, **7/12** have at least
  five usable frames, **8/12** have heavy raw missingness, **3/12** have zero usable F0,
  and **1/12** has existing instability flags. Those counts are for this selected subset;
  the original whole-study **36 / 20 / 28 / 10 / 1** counts remain unchanged.
- Cached frozen wav2vec2 yielded **12 × 768** block-6 mean embeddings, deterministic
  across repeats, with unchanged weights and no gradients. They have no demonstrated
  interpretation as phones or correctness.
- **No learner-facing correctness judgment is supported**, including S02 饭 and S13 贵/州.

## Read the evidence

1. [Capability audit](capability-audit.md): inspected code, environments, cached model,
   available/unused tools and missing capabilities.
2. [Method](method.md): target independence, fixed parameters, windows, blinding and
   feature semantics. Written before the selected-region extraction.
3. [Blinded audit](blinded-audit.md): observation table and interpretation written before
   opening the separate identity key. **For an actual blind review, use the local packet
   alone; this documentation directory also contains identities.**
4. [Region results](region-results.md): exact spans, measurements, F0, formant feasibility,
   onset summaries, quality flags, control ranking and embedding frame counts.
5. [Segmental feasibility](segmental-feasibility.md): architectural assessment, requested
   special cases, limitations, and the one recommended next step.
6. [Validation](validation.md): checks, reproduction and remaining limits.

The next bounded step is a blinded Mandarin phonetic annotation of **these same twelve
regions**, centered on boundary plausibility, audible periodicity and resonance/noise
observability. No new recording, model selection or classifier is proposed in this step.

## Local artifacts and separation

All audio/figures/full numeric traces/embeddings remain under **`/tmp/benma-phonetic-audit/`**,
outside the repository:

| Path below that directory | Contents |
| --- | --- |
| `blinded/index.html` | Self-contained local review index with audio players and plots |
| `blinded/R01` … `blinded/R12` | Each has `crop.wav`, `waveform.svg`, `spectrogram.svg`, `pitch-energy.svg`, `evidence.json` |
| `blinded/summary.json`, `observations.md`, `seal.json` | Numeric summaries, blind table, SHA-256 seal covering the packet |
| `private/acoustic-manifest.json` | Strict allowlisted acoustic inputs, source audio identity and absolute spans; no targets/readings/scores |
| `private/unblinding-key.json` | Separate identity/selection key, control ranking and original/reviewed-record/audio provenance |
| `private/pre-unblinding-review.json`, `unblinding-receipt.json` | Seal verification and join receipt |
| `embeddings/embeddings.npz`, `receipt.json` | R-ID vectors, layer/pooling/checkpoint/determinism provenance |
| `blinded-initial/`, `embeddings-initial/` | Retained first artifact build before an explanatory reason-flag clarification; numeric observations and embeddings are identical |

Two local PNG render checks also remain at the artifact root. Generated listening crops
are PCM16, without gain normalization; analysis uses the decoded float samples. The
source WAVs and full study records were neither modified nor copied into Git. Voice
crops can identify a speaker, so the packet is pseudonymized, not de-identified audio.
No completed human phonetic annotation or listening judgment is claimed.

## New isolated research modules

- [phonetic_evidence.py](../../../../benchmark/pronunciation_v2/phonetic_evidence.py):
  strict `Span`/`SavedFrame` inputs, acoustic metrics, saved pitch, windows, Burg guards.
- [phonetic_prepare.py](../../../../benchmark/pronunciation_v2/phonetic_prepare.py):
  source/hash checks, control selection, pseudonyms and separate key.
- [phonetic_packet.py](../../../../benchmark/pronunciation_v2/phonetic_packet.py):
  isolated crops, deterministic SVGs, local HTML, target-free summaries and seal.
- [phonetic_embeddings.py](../../../../benchmark/pronunciation_v2/phonetic_embeddings.py):
  optional local-only frozen encoder extraction, with no experiment or trained-head entry point.
- [phonetic_report.py](../../../../benchmark/pronunciation_v2/phonetic_report.py):
  post-seal identity join, with no acoustic recomputation.
- [test_phonetic_evidence.py](../../../../benchmark/pronunciation_v2/test_phonetic_evidence.py):
  focused signal, leakage, deterministic-output and abstention tests.
