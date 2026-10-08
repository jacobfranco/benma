# Segmental capability inventory

This is a repository/runtime/cache audit, not a claim about every capability currently offered by a vendor. No provider inference request, model download, package installation, training, data collection or fine-tuning occurred. Package presence was checked in all three existing environments; saved raw outputs were inspected for the four latest recordings.

| Capability inspected | Actual local output | Independent of target? | Independent segmental recognition? |
|---|---|---|---|
| OpenAI adapter `speech/providers/openai.py` | Fixed Mandarin verbatim profile, no target/word hints; saved payload keys `text`, `logprobs`, `usage`; token keys `token`, `logprob`, `bytes` | Yes, with respect to intended target | No. Lexical transcript/token likelihoods are not phone posterior distributions or pre-lexical syllables. No sound/pinyin/phone tier is returned in these recordings. |
| Azure alignment-only request | `ReferenceText` is perceived transcript; `Granularity=Phoneme`, SAPI labels, exact word/grapheme offsets | Independent of intended target, conditioned on perceived reference | No. Word/grapheme correspondence is useful placement evidence; labels are reference-conditioned. |
| Azure assessment adapter `speech/providers/azure.py` | Target reference text, phone labels and accuracy fields; saved latest phones have `Phoneme`, `Offset`, `Duration`, `AccuracyScore` | No for the known-target path | No independent recognized-phone alternatives found. Scores and reference phones do not identify produced sounds. |
| Azure `NBest` / `DisplayText` in saved alignment payloads | Recognition/lexical text inside a scripted request | Not independently established | A lexical alternative is still not a decoded observed phone sequence. No `NBestPhonemes` tier in these saved results; no unsupported Mandarin capability is assumed. |
| Current acoustic extractor and contour classifier | Waveform-only F0, periodicity, energy, selected/rejected frames, acoustic gesture | Yes for extraction/classification; spans are currently conditioned on lexical alignment | Pitch/quality only; no phone identity. |
| Existing Parselmouth spectral/formant research | Generic spectra and Burg estimates; previous 12-region feasibility audit had no accepted formant summary | Waveform measurements yes; old crops use provider boundaries | No validated vowel/final/initial labeler. Repeating it would not supply a recognizer. |
| Frozen wav2vec features (`benchmark/pronunciation_v2/features.py`) | Frozen acoustic hidden vectors; prior experiments pool 768-D block-6 output | Waveform encoder yes; previous crops may be reference-aligned | No phone/pinyin labels or phoneme posterior head. Mean pooling discards temporal detail. |
| Cached pretrained model | `facebook/wav2vec2-base`, snapshot `0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`; config architecture `Wav2Vec2ForPreTraining` | Encoder yes | No independent phone decoder. Snapshot contains weights, config, preprocessor config and README, **no tokenizer/vocabulary/phone decoding head**. `vocab_size=32` in a config is not evidence of a trained phone decoder. |
| Previously trained research heads | Local `selected-head.npz`, frozen features and tone experiment utilities | Acoustic features can be independent | Tone heads are not segmental recognizers and were not invoked or promoted. |
| Transformers library | 4.57.6 in isolated research environment; architecture classes available | Depends on actual model and inputs | Library availability is not a pretrained phoneme CTC model. Instantiating a random head cannot produce credible labels. |
| torchaudio | Absent in root, API and research environments | N/A | No local pipeline bundle/model to probe. Installing a library would not validate a Mandarin recognizer. |
| Other phone / CTC / pinyin recognizers | Searches found no established independent decoder; `phonemizer`, `allophant`, `speechbrain`, `espnet`, `vosk`, `whisper` modules absent in the three environments | N/A | None suitable already installed/cached. Text-to-phoneme software would still require lexical input and is not sound recognition. |
| MFA/TextGrid adapters | Explicit transcript + acoustic model/dictionary alignment; word/syllable tiers | No, transcript-conditioned | Aligned phones are not detected phones. No forced-aligner output is promoted to independent segmental evidence. |
| Existing benchmark scripted providers | Target-pinyin/phone assessment adapters, including Azure/Tencent-style reference serialization | Reference-conditioned | Unsuitable as independent observed segmental units. No provider was exercised. |

## Verified environment and cache

- API: NumPy 2.5.3, Parselmouth 0.4.7; no Torch, Transformers or torchaudio.
- Isolated `benchmark/pronunciation_v2/.venv`: NumPy 2.3.3, Torch 2.8.0+cpu, Transformers 4.57.6, SciPy 1.16.2; no Parselmouth or torchaudio.
- Root `.venv`: development environment, none of the preceding acoustic/model packages.
- Inspected model cache: `~/.cache/benma/pronunciation-v2-model/hf/`; only the wav2vec2-base snapshot was found. Default `~/.cache/huggingface` is absent. These are the configured/relevant local locations, not a claim to have indexed every unrelated disk.
- Existing base-weight receipt: SHA-256 `3249fe98bfc62fcbc26067f724716a6ec49d12c4728a2af1df659013905dff21`. Snapshot metadata and file listing were inspected; no weights were loaded for inference in this pass. The previous [capability audit](../2026-10-02-independent-phonetic-evidence/capability-audit.md) documents frozen-model/hash validation and English pretraining limitations.

## Realistic options and tradeoffs

1. **Research acoustic-unit interface using cached unpooled encoder frames:** immediately possible offline, with no text input or new model. Provides independent acoustic representation and provenance, **not decoded sounds**. Use null segmental identity and do not pretend a model frame is a phoneme boundary.
2. **Obtain/evaluate a pretrained phone-CTC decoder in a later authorized experiment:** potentially sound hypotheses without lexical ASR, but requires a suitable uncached checkpoint, phone inventory mapping, language coverage verification and validation on these recordings. Mandarin suitability and confidence cannot be inferred from the CTC architecture name. No specific uncached model is claimed suitable here.
3. **Provider phonetic recognition:** useful only if a verified unscripted Mandarin capability exposes genuinely observed phones or posterior alternatives. Existing saved Azure evidence does not establish that capability. A generic pronunciation assessment feature is insufficient.

**Optional local pre-lexical probe: SKIPPED.** No suitable independent sound/phone/syllable decoder is already installed or cached. Running the base encoder again would only reproduce unlabeled embeddings, not answer whether a method can emit sound identities. No fake recognizer is constructed to force a result.

**Decision 4:** choose option 1, the single bounded offline adapter described in the [contract](prelexical-contract.md#one-bounded-next-step). Keep Mandarin lexical ASR and reference-conditioned alignment as separate complementary layers.
