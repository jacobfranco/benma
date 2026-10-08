# Silero fails the critical presence requirement; model search closed

**Do not integrate Silero.** The newest accidental-silence recording remains accepted with peak speech probability **0.997681** and a **1.852-second** detected region. Its probability exceeds 0.9 for **1.440 seconds**, including **1.150 seconds outside** the old 290 ms energy event.

| Measure | Current Benma | Silero default |
| --- | --- | --- |
| Newest accidental silence | Accepted incorrectly | Accepted incorrectly |
| Negatives rejected | 4/10 | **9/10** |
| Positives retained | 37/37 | **33/37** |
| Short excerpts retained | 6/6 | **2/6** |
| Quiet RMS controls retained | 12/12 | **12/12** |
| Low-F0 controls retained | 5/5 | **5/5** |

Silero substantially improves broad negative rejection, including clicks and padding that currently pass. However, the one remaining negative is the exact production trust blocker, and four legitimate short excerpts are lost. **9/10 is not success under this pass's acceptance criteria.**

All **48 frozen entries completed**: 37 positives, 10 negatives, one unresolved; **zero failed or skipped cases**. All hashes were checked before inference. The unresolved recording is rejected but excluded from positive/negative metrics. The complete 48 raw timelines preserve **3,681 probabilities**, timestamps, chunk boundaries, sample rates and model/runtime provenance.

Only thresholds **0.30, 0.40, 0.50, 0.60, 0.70** were evaluated. Every threshold accepts the accidental recording. Positive retention is **34, 33, 33, 32, 31 /37**, respectively. There is **no acceptable robust threshold region**. No minimum-duration sweep, acoustic combination, additional VAD, or tracker experiment was performed.

Six metadata contexts for each of 48 waveforms produced **identical probabilities and decisions (288/288 contexts)**. Silero's audio interface is independent of text, targets and language metadata; this does not establish adequate accuracy or universal language coverage. Nine positives lack transcript metadata: five pass and four short excerpts fail. The frozen corpus contains no confirmed nonsense recording, so metadata invariance is not a substitute for measured gibberish recall.

CPU operation is practical: the official ONNX wrapper processes the existing **2.8560625-second human clip in 14.758 ms median**, with **11.590 ms corpus median / 24.496 ms p95**. A research NumPy adapter for the **same weights** exactly matches all official probabilities and takes 10.944 ms for that clip. Quality, not runtime, prevents integration.

## Six decisions

1. **SILERO DOES NOT CLEARLY SEPARATE THEM.** Broad improvement does not separate the critical false accept.
2. **MEANINGFUL FALSE-REJECT REGRESSION.** Four valid short positives are rejected at default.
3. **SILERO IS LANGUAGE-INDEPENDENT BUT INSUFFICIENT.** Architecture and invariance pass; product accuracy fails.
4. **SILERO PRACTICAL FOR CONVERSATIONAL CPU USE.** Warm inference, model size and the CPU path are practical.
5. **SILERO DOES NOT RESOLVE THE TRUST BLOCKER.** No production integration pass is earned.
6. **STOP PRESENCE-MODEL SEARCH AND REASSESS CHECKPOINT SCOPE.** Both tracker and VAD-model searches are closed.

## Evidence and validation

- [Model, exact package, hashes, license and semantics](model.md)
- [All 48 results, category counts, short speech, low-F0 and metadata cases](corpus-results.md)
- [Critical false accept: waveform, spectrum and probability analysis](accidental-silence.md)
- [Five thresholds and why further tuning stopped](thresholds.md)
- [CPU timings and concurrency implications](latency.md)
- [Decision and checkpoint scope reassessment](decision.md)
- [Validation and preservation receipt](validation.md)
- [Small static diagnostic viewer](viewer.html), [raw accidental probability timeline](probabilities/silence_accidental.json)

Viewer path: `/home/jacob/benma/docs/research/pronunciation-v2/2026-10-06-silero-vad/viewer.html`. It opens locally without a server and contains eight representative plots. No production UI was modified.

Production presence, dependencies, pitch evidence/eligibility, tone comparison and mobile source remain unchanged. The existing large uncommitted working tree is preserved. No provider calls, new recordings, commit, push or deployment occurred. The one authorized package/runtime setup stays in ignored local research storage; no weights are added to versioned research artifacts.
