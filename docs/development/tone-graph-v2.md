# Tone Graph V2 — current state and checkpoint decision

## Learner workspace update: October 8, 2026

The [pronunciation workspace](pronunciation-workspace.md) now replaces the default horizontal whole-sentence graph with wrapped perceived timing units and one selected-unit panel. Practice/Free Practice show one active attempt, with session-local History and a fixed New Attempt control. Conversation starts with pronunciation collapsed. Full pitch details retains the whole-utterance elapsed-time graph and optional Raw evidence; it is no longer the primary learner navigation surface.

Selected graphs use saved retained measurements on a shared attempt scale, and exact Mine playback uses the canonical audio timeline via the authenticated existing audio resource's `canonical=true` option. Groups remain atomic; no accepted timing means no bounded unit playback. Context playback is not in production. Learner comparison remains uncertain: all units use neutral measurement-quality labels, not positive/negative pronunciation grades. The known speech-presence deployment blocker remains.

The October 6 checkpoint below is preserved as historical research/policy context. Its description of the then-default graph hierarchy is superseded by this workspace update; its research conclusions and comparison guardrails are unchanged.

## Current state: October 6, 2026

**Checkpoint posture: Option B, architecture with conservative feature gating. Ready for a small final physical smoke before a separately authorized commit. Deployment: DO NOT DEPLOY YET.** The [checkpoint report](../research/pronunciation-v2/2026-10-06-checkpoint-scope/README.md) is the current decision authority. Older research readiness statements and proposed next experiments are historical, not current instructions.

Benma visualizes measured pitch aligned, where timing is available, to the text it perceived. Missing evidence stays missing; incomplete or unstable evidence suppresses gesture interpretation. Pitch gestures are experimental descriptions. Reference pronunciation is separate, and learner tone comparison stays uncertain. Neither the graph nor a successful request establishes that the recording contained intended user speech.

This is a perceived-speech pitch evidence architecture, **not a pronunciation grader or an independent phonetic/segmental recognizer**. It does not promise correct lexical tone detection, phonetic correctness, universal speech detection, or identification of the intended speaker.

## What is in the branch

- Character-free extraction produces one frozen `UtterancePitchTrack` per `AcousticRun`. Audio hash, content-derived evidence ID, tracker/configuration/selection provenance, timestamps and distinct raw/energy-gated/analyzer-selected/final-selected measurements remain available. No target, character, reading or reference tone enters extraction.
- Existing bounded pitch warmup, perceived analysis and target analysis reuse the same acoustic run. Worker sessions and PostgreSQL single-flight behavior remain; no migration or new production model/dependency was introduced.
- Character and word graphs are projections of that evidence. `PitchRegionProjection` records track ID, timing provenance and exact source indices in `[start,end)`. Word-only 雨伞 remains a single region without invented character boundaries. Missing timing, support and gaps remain missing.
- Backend eligibility checks completeness and stability relative to raw voiced support. Incomplete, unstable and insufficient regions abstain; sufficient regions may retain an experimental level/rising/dipping/falling description. Low F0 alone is not a rejection. Eligibility is not a speech-presence or learner-trust certificate.
- Practice, Free Practice and Conversation share `SpeechEvidence` → `TranscriptFeedback` → `SentenceToneGraph`. Character identity comes from perceived text. Target 广州 cannot replace perceived 贵州. Text differences are labeled as text differences.
- Current narrow reading rules retain contextual 要/yào before quantities, 一 sandhi, and unresolved surface realization for quantity 个. Lexical and contextual reference readings remain separate from acoustics.

The [immutable-evidence report](../research/pronunciation-v2/2026-10-05-utterance-evidence/README.md) records the saved replay: repeated 苹 cases with lost late voiced evidence abstain, 3/3 named healthy controls survive, and 37/50 formerly classifiable speech regions remain classifiable. These are fixed-corpus results, not general accuracy estimates or newly rerun research in this checkpoint pass.

## Product permission and presentation

`toneGestureMatch()` returns `uncertain` unconditionally for comparison, even for sufficient evidence or an unexpected future policy value. The backend's `tone_comparison_policy` has only the value `experimental`. Positive/warning style definitions and comparison vocabulary remain for future explicit policy work but are unreachable today. There is no runtime flag that promotes the primary graph to trusted grading.

Default: “Your pitch”, perceived characters, neutral cells, measured geometry and More detail. Tapping a character separates observed pitch/confidence, uncertain comparison, lexical/reference tone and experimental wording. Incomplete/unstable observations are withheld. T3, neutral and unresolved references are conservative. Grouped words have no individual verdict.

Mine smooths/simplifies existing retained evidence; More detail uses retained measurements in elapsed time; Raw shows tracker points, exclusions and missingness. No textbook contour replaces measurements. Equal-width Mine cells are a display projection, not equal timing; real timing is visible in detail. New analysis identity resets interaction state.

The reachable legacy `/pronunciation` screen also withholds default and A/B interpretation claims. Provider/saved interpretation data remains available under **Experimental diagnostics** with an explicit no-grading statement. Fresh backend messages say “Uncalibrated provider tone label” or “Experimental provider tone label”, never claim detected lexical tone. Historical stored messages are not rewritten.

`BENMA_ENABLE_EXPERIMENTAL_TONE_INTERPRETATION` now defaults to **false** in code and `.env.example`; it controls laboratory diagnostics only. The existing local, ignored `.env` explicitly sets it true and was left intact. Even with that opt-in, graph comparison stays uncertain and ordinary legacy views stay neutral. Categorical judgment remains disabled. No Silero, RMVPE or CREPE integration exists in production source.

## Closed research and the remaining release concern

The [pitch-reliability work](../research/pronunciation-v2/2026-10-02-pitch-reliability/README.md), [native-control calibration](../research/pronunciation-v2/2026-10-03-native-control-calibration/README.md) and [prelexical contract](../research/pronunciation-v2/2026-10-03-prelexical-speech/README.md) motivated conservative observed-gesture and identity boundaries. The [F0 foundation/RMVPE work](../research/pronunciation-v2/2026-10-05-f0-foundation/decision.md) did not establish a safe production replacement. **Tracker search is closed.** Existing Praat extraction/selection remains provisional.

The [speech-presence audit](../research/pronunciation-v2/2026-10-06-speech-presence/README.md) found no safe lightweight rule for the newest accidental silence. The [Silero decision](../research/pronunciation-v2/2026-10-06-silero-vad/decision.md) rejects integration: 9/10 negatives rejected and 33/37 positives retained; 5/5 low-F0 and 12/12 quiet preserved, but accidental silence accepted at 0.9977 for about 1.852 seconds. The 0.30–0.70 range never fixes it and short-speech false rejects matter. **VAD-model search is closed.** The production presence algorithm is unchanged in this pass.

**Graph safety and turn acceptance are different.** A graph can preserve its measurements honestly for a turn that should never have existed. The known negative can produce apparent ASR text and pitch; locally sufficient pitch is possible even there. Neutral comparison contains grading harm but does not remove false transcript/history or stop Conversation from generating a reply and requesting TTS. Conversation release acceptance therefore remains a separate concern; this branch checkpoint authorizes no deployment or broad Conversation disablement.

## Validation, retention and next decision

See [validation](../research/pronunciation-v2/2026-10-06-checkpoint-scope/validation.md) for exact counts, strict presence XFAILs, streaming exclusions and pre-existing formatting debt. No full-unbounded-suite or physical-device certification is claimed. Research results are reproducible subject to explicitly private audio and pinned optional environments; source, numeric manifests and concise findings belong in the checkpoint. Audio, weights, caches, generated figures/viewers and scratch logs do not. The HTML template in `benchmark/` is source and is retained.

**One next step: RUN FOUR-CASE FINAL PHYSICAL SMOKE**, using the four cases in the [commit plan](../research/pronunciation-v2/2026-10-06-checkpoint-scope/commit-plan.md). This is a graph/product-boundary smoke, not presence qualification. No new capture was performed in this pass; recording/provider use requires the later smoke session. A commit still requires explicit later authorization. Deployment remains blocked by turn acceptance and unvalidated general learner grading, regardless of the smoke result.
