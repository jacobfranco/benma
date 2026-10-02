# Recording cd1b2ccd-7278-47f6-b016-983e929209d0

Evidence: recorded_audio

## Study notes

User report: perceived substitutions on a user-reported imperfect attempt; cause unresolved. 进去/说说 are not labeled ASR bugs. Azure scores and Mispronunciation flags are conditioned on the perceived reference; they do not identify an acoustic cause.

## Intended

今天天气不错，我们出去走走吧。

## What Benma heard

今天天气不错，我们进去说说吧。

## Alignment

| Unit | Perceived | Timing (ms) | Source |
| --- | --- | --- | --- |
| u0 | 今 | 2390-2660 | azure_provider_grapheme |
| u1 | 天 | 2670-2920 | azure_provider_grapheme |
| u2 | 天 | 2930-3200 | azure_provider_grapheme |
| u3 | 气 | 3210-3460 | azure_provider_grapheme |
| u4 | 不 | 3470-3820 | azure_provider_grapheme |
| u5 | 错 | 3830-4250 | azure_provider_grapheme |
| u6 | 我 | 4800-5020 | azure_provider_grapheme |
| u7 | 们 | 5030-5260 | azure_provider_grapheme |
| u8 | 进 | 5290-5540 | azure_provider_grapheme |
| u9 | 去 | 5550-5800 | azure_provider_grapheme |
| u10 | 说 | 5810-5900 | azure_provider_grapheme |
| u11 | 说 | 5910-6000 | azure_provider_grapheme |
| u12 | 吧 | 6010-6270 | azure_provider_grapheme |

Provider word regions (never equally subdivided):

- 今天: 2390-2920 ms; syllables mapped
- 天气: 2930-3460 ms; syllables mapped
- 不错: 3470-4250 ms; syllables mapped
- 我们: 4800-5260 ms; syllables mapped
- 进去: 5290-5800 ms; syllables mapped
- 说说: 5810-6000 ms; syllables mapped
- 吧: 6010-6270 ms; syllables mapped

## Recording acoustics

Whole recording: 179/720 frames with raw gated F0; 179 selected frames. Full contours and quality details are in record.json.
Untimed syllables cannot inherit these whole-recording measurements.

## Unit u0: 今

- Timing: 2390-2660 ms; source azure_provider_grapheme.
- Reading: jīn; lexical tone 1; source phrase.
- Perceived word context: 今天.
- Reference phones (reference-conditioned, not detected sounds): jin 1 (score 69.0)
- Observed pitch: 13/27 usable frames; raw F0 missing proportion 0.5185185185185186.
- Target relationship: match; intended 今; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: jīn; lexical 1, surface 1 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u1: 天

- Timing: 2670-2920 ms; source azure_provider_grapheme.
- Reading: tiān; lexical tone 1; source phrase.
- Perceived word context: 今天.
- Reference phones (reference-conditioned, not detected sounds): tian 1 (score 100.0)
- Observed pitch: 16/25 usable frames; raw F0 missing proportion 0.36.
- Target relationship: match; intended 天; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: tiān; lexical 1, surface 1 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u2: 天

- Timing: 2930-3200 ms; source azure_provider_grapheme.
- Reading: tiān; lexical tone 1; source dictionary.
- Perceived word context: 天气.
- Reference phones (reference-conditioned, not detected sounds): tian 1 (score 100.0)
- Observed pitch: 15/27 usable frames; raw F0 missing proportion 0.4444444444444444.
- Target relationship: match; intended 天; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: tiān; lexical 1, surface 1 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u3: 气

- Timing: 3210-3460 ms; source azure_provider_grapheme.
- Reading: unresolved; lexical tone None; source unresolved.
- Perceived word context: 天气.
- Reading alternatives: qi4, qi3.
- Reference phones: no accepted unit attachment; raw labels, if supplied, remain in alignment evidence (reference-conditioned, not detected sounds).
- Observed pitch: 0/25 usable frames; raw F0 missing proportion 1.0.
- Target relationship: match; intended 气; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: unresolved; lexical None, surface None (reading_unresolved).
- Evidence quality: ambiguous_reading, asr_uncertainty_available, heavy_f0_missingness, insufficient_voiced_frames, phone_evidence_unavailable, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: ambiguous_reading, connected_speech_diagnosis_unvalidated, contextual_expectation_unresolved, insufficient_voiced_pitch

## Unit u4: 不

- Timing: 3470-3820 ms; source azure_provider_grapheme.
- Reading: bù; lexical tone 4; source phrase.
- Perceived word context: 不错.
- Reference phones (reference-conditioned, not detected sounds): bu 2 (score 67.0)
- Observed pitch: 3/35 usable frames; raw F0 missing proportion 0.9142857142857143.
- Target relationship: match; intended 不; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: bù; lexical 4, surface 2 (bu_before_fourth).
- Evidence quality: asr_uncertainty_available, heavy_f0_missingness, insufficient_voiced_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch

## Unit u5: 错

- Timing: 3830-4250 ms; source azure_provider_grapheme.
- Reading: cuò; lexical tone 4; source phrase.
- Perceived word context: 不错.
- Reference phones (reference-conditioned, not detected sounds): cuo 4 (score 94.0)
- Observed pitch: 9/42 usable frames; raw F0 missing proportion 0.7857142857142857.
- Target relationship: match; intended 错; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: cuò; lexical 4, surface 4 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u6: 我

- Timing: 4800-5020 ms; source azure_provider_grapheme.
- Reading: wǒ; lexical tone 3; source phrase.
- Perceived word context: 我们.
- Reference phones (reference-conditioned, not detected sounds): wo 3 (score 88.0)
- Observed pitch: 13/22 usable frames; raw F0 missing proportion 0.40909090909090906.
- Target relationship: match; intended 我; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: wǒ; lexical 3, surface 3 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u7: 们

- Timing: 5030-5260 ms; source azure_provider_grapheme.
- Reading: men; lexical tone 0; source phrase.
- Perceived word context: 我们.
- Reference phones (reference-conditioned, not detected sounds): men 5 (score 100.0)
- Observed pitch: 9/23 usable frames; raw F0 missing proportion 0.6086956521739131.
- Target relationship: match; intended 们; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: men; lexical 0, surface 0 (lexical_neutral).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u8: 进

- Timing: 5290-5540 ms; source azure_provider_grapheme.
- Reading: jìn; lexical tone 4; source dictionary.
- Perceived word context: 进去.
- Reference phones (reference-conditioned, not detected sounds): jin 4 (score 34.0)
- Observed pitch: 6/25 usable frames; raw F0 missing proportion 0.76.
- Target relationship: substitution; intended 出; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: chū; lexical 1, surface 1 (unchanged).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Unit u9: 去

- Timing: 5550-5800 ms; source azure_provider_grapheme.
- Reading: qù; lexical tone 4; source dictionary.
- Perceived word context: 进去.
- Reference phones (reference-conditioned, not detected sounds): qu 4 (score 69.0)
- Observed pitch: 0/25 usable frames; raw F0 missing proportion 1.0.
- Target relationship: match; intended 去; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: qù; lexical 4, surface 4 (unchanged).
- Evidence quality: asr_uncertainty_available, heavy_f0_missingness, insufficient_voiced_frames, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch

## Unit u10: 说

- Timing: 5810-5900 ms; source azure_provider_grapheme.
- Reading: unresolved; lexical tone None; source unresolved.
- Perceived word context: 说说.
- Reading alternatives: shuo1, shui4, yue4.
- Reference phones: no accepted unit attachment; raw labels, if supplied, remain in alignment evidence (reference-conditioned, not detected sounds).
- Observed pitch: 5/9 usable frames; raw F0 missing proportion 0.4444444444444444.
- Target relationship: substitution; intended 走; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: zǒu; lexical 3, surface None (prosodic_grouping_unresolved).
- Evidence quality: ambiguous_reading, asr_uncertainty_available, at_least_five_usable_frames, phone_evidence_unavailable, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: ambiguous_reading, connected_speech_diagnosis_unvalidated, contextual_expectation_unresolved

## Unit u11: 说

- Timing: 5910-6000 ms; source azure_provider_grapheme.
- Reading: unresolved; lexical tone None; source unresolved.
- Perceived word context: 说说.
- Reading alternatives: shuo1, shui4, yue4.
- Reference phones: no accepted unit attachment; raw labels, if supplied, remain in alignment evidence (reference-conditioned, not detected sounds).
- Observed pitch: 2/9 usable frames; raw F0 missing proportion 0.7777777777777778.
- Target relationship: substitution; intended 走; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: zǒu; lexical 3, surface None (prosodic_grouping_unresolved).
- Evidence quality: ambiguous_reading, asr_uncertainty_available, heavy_f0_missingness, insufficient_voiced_frames, phone_evidence_unavailable, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: ambiguous_reading, connected_speech_diagnosis_unvalidated, contextual_expectation_unresolved, insufficient_voiced_pitch

## Unit u12: 吧

- Timing: 6010-6270 ms; source azure_provider_grapheme.
- Reading: ba; lexical tone 0; source grammar.
- Perceived word context: 吧.
- Reference phones (reference-conditioned, not detected sounds): ba 5 (score 100.0)
- Observed pitch: 12/26 usable frames; raw F0 missing proportion 0.5384615384615384.
- Target relationship: match; intended 吧; unique_minimum_edit. No acoustic cause inferred.
- Expected pronunciation: ba; lexical 0, surface 0 (lexical_neutral).
- Evidence quality: asr_uncertainty_available, at_least_five_usable_frames, heavy_f0_missingness, reference_phone_available, timing_available, tone_model_not_integrated
- INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated

## Limits

- ASR text is what the recognizer heard, not a gold phonetic transcription.
- Reference phone labels and scores do not establish observed phones or tones.
- Every pronunciation judgment abstains pending connected-speech validation.
- No learned tone model or target-relative provider assessment is run in this research harness.
- Timing is conditionally mapped provider evidence, not validated gold boundaries.
- Non-Han text is retained but has no pronunciation units; no erhua segmentation.
