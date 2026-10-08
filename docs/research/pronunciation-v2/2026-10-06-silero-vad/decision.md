# No integration; close the presence-model search

The required outcome was reliable rejection of the observed accidental silence while preserving legitimate short speech. Silero improves aggregate negative rejection from 4/10 to 9/10, but retains the exact production failure at peak **0.997681** for a long speech region and loses four short positives at default. It therefore **does not earn a production integration pass**.

## Six explicit decisions

1. **SILERO DOES NOT CLEARLY SEPARATE THEM.** This means the current false-accept problem as a product requirement, not an absence of useful model discrimination. Five of the six baseline false accepts are corrected; the critical sixth remains at every permitted threshold.
2. **MEANINGFUL FALSE-REJECT REGRESSION.** Default retention drops from 37/37 to 33/37, with short-speech retention 2/6. Quiet controls remain 12/12 and low-F0 5/5 at default; those positive findings do not erase the four short failures.
3. **SILERO IS LANGUAGE-INDEPENDENT BUT INSUFFICIENT.** No transcript, target, language, Han count, ASR success, semantic validity, pinyin or lexical tone enters the adapter. All 48 waveforms retain identical probabilities and decisions across six metadata contexts. Audio-only architecture is demonstrated; adequate presence quality is not. Genuine nonsense audio and broad language coverage are absent from this frozen evaluation.
4. **SILERO PRACTICAL FOR CONVERSATIONAL CPU USE.** The official CPU path takes 14.758 ms median for the 2.856 s representative clip, with a 2.220 MiB model. The same-model NumPy path confirms a practical smaller runtime. Production load/concurrency remains unmeasured.
5. **SILERO DOES NOT RESOLVE THE TRUST BLOCKER.** 9/10 negative rejection is insufficient because the remaining negative is the specific known failing successful turn. There is no integration recommendation.
6. **STOP PRESENCE-MODEL SEARCH AND REASSESS CHECKPOINT SCOPE.** This was the final authorized VAD-model experiment. Tracker search is also closed. No additional VAD, tracker, threshold search, duration sweep or acoustic combination is proposed or begun.

## Acceptance audit

| Criterion | Result |
| --- | --- |
| Reject newest accidental silence | **Fail**: accepted at 0.30–0.70 |
| Materially improve negative rejection | Pass: 9/10 versus 4/10 |
| Essentially all positives retained | **Fail**: 33/37 default, best tested 34/37 |
| Short speech preserved | **Fail**: 2/6 default |
| Quiet speech preserved | Pass on frozen proxies: 12/12 RMS and 1/1 gain control |
| Low-F0 preserved | Pass at default: 5/5; loses excerpts at higher thresholds |
| Text/target independence | Pass: 288/288 contexts identical; actual nonsense recall not established |
| Robust satisfactory operating region | **Fail**: no tested setting rejects the blocker |
| Conversational latency | Pass for local warm CPU timing |
| Practical CPU/ONNX path | Pass for research feasibility; no deployment performed |

## What reassessing checkpoint scope means

Prior checkpoint work established the pitch architecture, immutable character-free acoustic evidence, local pitch eligibility and conservative learner comparisons. Those architectural boundaries remain intact; this pass neither changes them nor re-evaluates pitch trackers. The preceding lightweight presence search found no safe rule. Silero now adds useful general negative discrimination but still confidently accepts the critical labelled silence and rejects short speech. **Both tracker and VAD-model searches are closed.** The next decision belongs to product and architecture scope, not another signal-processing comparison.

A future scope discussion can decide whether a checkpoint demonstrates acoustic diagnostics under explicitly limited interaction assumptions, or whether automatic successful-turn interpretation must remain blocked until the foreground/intended-speaker requirement is clarified. It should distinguish “plausible speech somewhere in this waveform” from “the learner intentionally supplied a response,” without assuming a VAD can establish intent or source identity. These are conceptual product options, not validated fixes or authorization for a new experiment. This pass does not recommend advancing the existing trust/physical-smoke gate as solved.

## Preserved production boundary

`presence.py`, `presence_service.py`, production dependency/runtime configuration, `UtterancePitchTrack`, pitch selection/eligibility, tone comparison and UI are unchanged from the start of this pass. The current negative-side Han-count fallback therefore remains a known product limitation; this failed experiment does not silently certify it as language-independent or remove it without a safe replacement.

Raw audio and immutable pitch evidence remain diagnostic evidence even when presence should reject a turn. Presence owns downstream interpretation permission, not mutation of acoustic evidence. Nothing in this research rewrites a pitch track, deletes evidence or changes learner feedback. [Preservation verification](validation.md).
