# Recording connected-guizhou

Evidence: synthetic_fixture

## Intended

我要去广州

## What Benma heard

我要去贵州

## Alignment

| Unit | Perceived | Timing (ms) | Source |
| --- | --- | --- | --- |
| u0 | 我 | unresolved | missing |
| u1 | 要 | unresolved | missing |
| u2 | 去 | unresolved | missing |
| u3 | 贵 | unresolved | missing |
| u4 | 州 | unresolved | missing |

Provider word regions (never equally subdivided):

- 我要去贵州: 100-2100 ms; syllables unresolved

## Unit u0: 我

Reading: wǒ; lexical tone 3; source dictionary.
Target relationship: match; intended 我; unique_minimum_edit. No acoustic cause inferred.
Expected pronunciation: wǒ; lexical 3, surface 3 (unchanged).
Evidence quality: asr_uncertainty_unavailable, insufficient_voiced_frames, phone_evidence_unavailable, syllable_timing_unresolved, synthetic_fixture_not_recorded_speech, tone_model_not_integrated
INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch, no_reliable_syllable_boundary, synthetic_evidence

## Unit u1: 要

Reading: unresolved; lexical tone None; source unresolved.
Reading alternatives: yao4, yao1, yao3.
Target relationship: match; intended 要; unique_minimum_edit. No acoustic cause inferred.
Expected pronunciation: unresolved; lexical None, surface None (reading_unresolved).
Evidence quality: ambiguous_reading, asr_uncertainty_unavailable, insufficient_voiced_frames, phone_evidence_unavailable, syllable_timing_unresolved, synthetic_fixture_not_recorded_speech, tone_model_not_integrated
INSUFFICIENT EVIDENCE: ambiguous_reading, connected_speech_diagnosis_unvalidated, contextual_expectation_unresolved, insufficient_voiced_pitch, no_reliable_syllable_boundary, synthetic_evidence

## Unit u2: 去

Reading: qù; lexical tone 4; source dictionary.
Target relationship: match; intended 去; unique_minimum_edit. No acoustic cause inferred.
Expected pronunciation: qù; lexical 4, surface 4 (unchanged).
Evidence quality: asr_uncertainty_unavailable, insufficient_voiced_frames, phone_evidence_unavailable, syllable_timing_unresolved, synthetic_fixture_not_recorded_speech, tone_model_not_integrated
INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch, no_reliable_syllable_boundary, synthetic_evidence

## Unit u3: 贵

Reading: guì; lexical tone 4; source dictionary.
Target relationship: substitution; intended 广; unique_minimum_edit. No acoustic cause inferred.
Expected pronunciation: guǎng; lexical 3, surface 3 (unchanged).
Evidence quality: asr_uncertainty_unavailable, insufficient_voiced_frames, phone_evidence_unavailable, syllable_timing_unresolved, synthetic_fixture_not_recorded_speech, tone_model_not_integrated
INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch, no_reliable_syllable_boundary, synthetic_evidence

## Unit u4: 州

Reading: zhōu; lexical tone 1; source dictionary.
Target relationship: match; intended 州; unique_minimum_edit. No acoustic cause inferred.
Expected pronunciation: zhōu; lexical 1, surface 1 (unchanged).
Evidence quality: asr_uncertainty_unavailable, insufficient_voiced_frames, phone_evidence_unavailable, syllable_timing_unresolved, synthetic_fixture_not_recorded_speech, tone_model_not_integrated
INSUFFICIENT EVIDENCE: connected_speech_diagnosis_unvalidated, insufficient_voiced_pitch, no_reliable_syllable_boundary, synthetic_evidence

## Limits

- ASR text is what the recognizer heard, not a gold phonetic transcription.
- Reference phone labels and scores do not establish observed phones or tones.
- Every pronunciation judgment abstains pending connected-speech validation.
- No learned tone model or target-relative provider assessment is run in v1.
- Timing is conditionally mapped provider evidence, not validated gold boundaries.
- Non-Han text is retained but has no pronunciation units; no erhua segmentation.
