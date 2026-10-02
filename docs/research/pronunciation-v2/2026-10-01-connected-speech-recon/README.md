# Connected-speech diagnostic recon — 2026-10-01

The existing stack can produce an inspectable sentence evidence trace without passing intent into recognition. It cannot yet promise trustworthy syllable timing for every naturally spoken Mandarin sentence, independently identify the sounds actually produced, or explain a substitution as a tone/segment error.

Code inspected at `bd518d3a3e86df143962ea3f50ce25b31f28c373` on `pronunciation-v2-research`. This pass adds research files only. Experiment #3 and its conclusions/artifacts are untouched. No model training, tuning, deployment, commit, or push.

## Deliverables

- [Actual Conversation and Practice pipeline, timing capability matrix](current-pipeline.md)
- [Truth boundaries and existing conflations](truth-boundaries.md)
- [Diagnostic contract and evidence policy](diagnostic-schema.md)
- [Gaps, blocker, and next pass](gaps.md)
- [14-recording manual study packet](manual-sentence-study.md)
- [Validation and limits of this pass](validation.md)
- [Research CLI](../../../../benchmark/pronunciation_v2/connected_speech_probe.py)
- [JSON Schema](../../../../benchmark/pronunciation_v2/connected-speech-schema.json)
- [Executable contract](../../../../benchmark/pronunciation_v2/connected_schema.py)
- [Focused tests](../../../../benchmark/pronunciation_v2/test_connected_speech.py)
- [Synthetic mismatch fixture](../../../../benchmark/pronunciation_v2/fixtures/connected-guizhou.json)
- [Generated fixture JSON](example-guizhou/record.json) / [Markdown](example-guizhou/report.md)

## Run

From repository root, use the existing Python 3.12 API environment (production imports require it):

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/connected_speech_probe.py \
  --fixture benchmark/pronunciation_v2/fixtures/connected-guizhou.json \
  --target '我要去广州' --output /tmp/benma-connected-fixture
```

The output directory must be new. Every completed run writes `record.json` and `report.md`; no audio is copied into the output. The fixture is explicitly synthetic, has no audio hash, and establishes no acoustic accuracy.

For an actual recording, configure `BENMA_PERCEPTION_PROVIDER=openai` and `BENMA_OPENAI_API_KEY` through the existing environment/settings mechanism. Set `BENMA_AZURE_SPEECH_KEY` and `BENMA_AZURE_SPEECH_REGION` to use the explicit `--alignment azure` option. This invokes the existing paid provider transports; no live provider calls were made in this pass.

```sh
services/api/.venv/bin/python benchmark/pronunciation_v2/connected_speech_probe.py \
  --audio /absolute/path/to/recording.wav \
  --target '我昨天晚上跟朋友去吃饭了' \
  --alignment azure --context-ms 150 \
  --output /tmp/benma-connected-sentence-01
```

Omit `--target` for unknown-intent/free speech. `--mode free|practice` is metadata only; default is practice with a target, free otherwise. `--alignment none` is the default and still accepts exact native ASR token timing if supplied. Current live transcription adapter does not populate that timing. Azure calls use **only the exact perceived transcript**. Complete usable native character timing takes precedence over an Azure call; otherwise the Azure mapping is used as a separate alignment source. This first harness does not merge partial native/Azure timing sets.

Azure short-audio alignment is capped at 30 seconds by the existing adapter policy. Longer audio still retains perception and whole-utterance F0, with missing alignment. Production upload byte/duration limits and ffmpeg canonicalization are reused. Optional alignment/pitch failures produce partial evidence and explicit issue codes. ASR failure stops the run: there is no fallback to the target transcript.

“Offline” describes a CLI without UI, database, or app server. Fixture mode is fully offline; audio mode uses the configured ASR and optional Azure service. Production Praat analyzes the entire canonical waveform once, then the harness slices timestamped frames, preserving surrounding acoustic context and gaps.

## Findings

1. Conversation records/uploads, runs unknown-target ASR, then branches into perceived-text pitch/timing analysis and semantic interpretation → assistant generation → optional TTS.
2. Practice runs the same ASR separately from target assessment + target alignment + independent acoustics. Its normal client does not also request perceived-text analysis.
3. Intended text does not enter the current unknown-target input contract. Semantic reconstruction is separately persisted; it does not become the alignment reference.
4. Current ASR gives text and model-dependent token log probabilities, not sentence/word/syllable timing through its normalized adapter. Azure assessment/alignment can give 100 ns offsets/durations for words and SAPI entries.
5. One-character words can supply syllable candidate regions. Multi-character words require one matching full-pinyin SAPI entry per exact character. No count-only or equal-duration split is accepted. These are conditional provider boundaries, not validated gold timing.
6. SAPI reference labels can be attached to those regions under exact checks. They are not independent detected segmental productions. Unmapped phones and scores remain in raw provider evidence.
7. Production F0 works on the waveform and can be sliced at accepted regions. This pass validates signal plumbing and fixtures, not natural-sentence pitch accuracy.
8. The frozen tone model is **not integrated**. Existing feature extraction/head prediction could mechanically consume sufficiently long canonical crops, but model/checkpoint provenance and connected-crop evaluation need a separate adapter. No sentence-tone accuracy is claimed.
9. The v1 record separates perception, perceived-reference alignment, acoustic/phone evidence, intended-text edits/contextual expectations, and abstaining judgments.
10. The fixture keeps `我要去贵州` under “What Benma heard” while recording `广 → 贵` as a substitution. No tone cause is inferred.
11. Existing contextual rules cover conservative third-tone pairs, 不 before T4, restricted 一 quantity/ordinal cases, neutral-tone readings, and some contextual polyphones.
12. Prosodic grouping, half-third realization, broad neutral-tone lexicon/realization, general 一 grammar and independent segmental evidence remain incomplete.
13. The harness abstains on missing boundaries/pitch, ambiguous readings, timing conflicts, uncertain target correspondence/surface expectation, and tracker instability. Even plentiful evidence remains unvalidated for connected-speech diagnosis.
14. The next study contains 14 natural or deliberately manipulated attempts; the learner is not asked to supply native gold labels.
15. The largest immediate bottleneck is **validated perceived-syllable region coverage on real sentence speech**, especially multi-character words, coarticulation, ASR disagreement, and uncertain readings. Conditional mapping already exists; its practical reliability has not been established here.
16. Next: record the packet, run frozen perception + perceived-reference alignment + Praat, inspect coverage/conflicts/boundaries and known manipulations, then decide whether alignment repair/evaluation is needed. Do not start another tone architecture bakeoff.

## Saved-record mapping continuation

The four real captures are audited and replayed in [the mapping continuation](../2026-10-01-connected-speech-mapping/replay-results.md). Research v2 separates provider grapheme timing from reading resolution: 30/36 → 36/36 timed units, with reading coverage conservatively unchanged at 27/36. The original recon/example artifacts remain historical v1 evidence.
