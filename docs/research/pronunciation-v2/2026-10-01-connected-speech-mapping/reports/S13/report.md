# Recording f7596060-2eb8-4e16-95ec-825b3f7c3c24

Evidence: recorded_audio

## Study notes

Declared word substitution: intended 广州; user deliberately said 贵州. Perception and alignment retain 贵州. The declared manipulation is not a gold phonetic realization label.

## Intended

我要去广州。

## What Benma heard

我要去贵州。

## Alignment

| Unit | Perceived | Timing (ms) | Source |
| --- | --- | --- | --- |
| u0 | 我 | 1370-1840 | azure_provider_grapheme |
| u1 | 要 | 1850-2180 | azure_provider_grapheme |
| u2 | 去 | 2190-2540 | azure_provider_grapheme |
| u3 | 贵 | 2550-2900 | azure_provider_grapheme |
| u4 | 州 | 2910-3370 | azure_provider_grapheme |

Provider word regions (never equally subdivided):

- 我: 1370-1840 ms; syllables mapped
- 要: 1850-2180 ms; syllables mapped
- 去: 2190-2540 ms; syllables mapped
- 贵州: 2550-3370 ms; syllables mapped

## Recording acoustics

Whole recording: 78/415 frames with raw gated F0; 78 selected frames. Full contours and quality details are in record.json.
Untimed syllables cannot inherit these whole-recording measurements.

## Unit u0: 我

- Timing: 1370-1840 ms; source azure_provider_grapheme.
- Reading: wǒ; lexical tone 3; source dictionary.
- Perceived word context: 我.
- Reference phones (reference-conditioned, not detected sounds): wo 3 (score 100.0)
- Observed pitch: 29/47 usable frames; raw F0 missing proportion 0.3829787234042553.
- Target relationship: match; intended 我; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: wǒ; lexical 3, surface 3 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u1: 要

- Timing: 1850-2180 ms; source azure_provider_grapheme.
- Reading: unresolved; lexical tone None; source unresolved.
- Perceived word context: 要.
- Reading alternatives: yao4, yao1, yao3.
- Reference phones: no accepted unit attachment; raw labels, if supplied, remain in alignment evidence (reference-conditioned, not detected sounds).
- Observed pitch: 5/33 usable frames; raw F0 missing proportion 0.8484848484848485.
- Target relationship: match; intended 要; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: unresolved; lexical None, surface None (reading_unresolved).
- Evidence quality: ambiguous_reading, asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, phone_evidence_unavailable, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: ambiguous_reading, connected_speech_diagnosis_unvalidated, contextual_expectation_unresolved

## Unit u2: 去

- Timing: 2190-2540 ms; source azure_provider_grapheme.
- Reading: qù; lexical tone 4; source dictionary.
- Perceived word context: 去.
- Reference phones (reference-conditioned, not detected sounds): qu 4 (score 100.0)
- Observed pitch: 0/35 usable frames; raw F0 missing proportion 1.0.
- Target relationship: match; intended 去; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: qù; lexical 4, surface 4 (unchanged).
- Evidence quality: asr_uncertainty_available, heavy_f0_missingness, insufficient_voiced_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch

## Unit u3: 贵

- Timing: 2550-2900 ms; source azure_provider_grapheme.
- Reading: guì; lexical tone 4; source dictionary.
- Perceived word context: 贵州.
- Reference phones (reference-conditioned, not detected sounds): gui 4 (score 94.0)
- Observed pitch: 14/35 usable frames; raw F0 missing proportion 0.6.
- Target relationship: substitution; intended 广; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: guǎng; lexical 3, surface 3 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u4: 州

- Timing: 2910-3370 ms; source azure_provider_grapheme.
- Reading: zhōu; lexical tone 1; source dictionary.
- Perceived word context: 贵州.
- Reference phones (reference-conditioned, not detected sounds): zhou 1 (score 87.0)
- Observed pitch: 15/46 usable frames; raw F0 missing proportion 0.6739130434782609.
- Target relationship: match; intended 州; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: zhōu; lexical 1, surface 1 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Limits

- ASR text is what the recognizer heard, not a gold phonetic transcription.
- Reference phone labels and scores do not establish observed phones or tones.
- Every pronunciation judgment abstains pending connected-speech validation.
- No learned tone model or target-relative provider assessment is run in this research harness.
- Timing is conditionally mapped provider evidence, not validated gold boundaries.
- Non-Han text is retained but has no pronunciation units; no erhua segmentation.
