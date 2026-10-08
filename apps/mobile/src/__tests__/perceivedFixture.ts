import type { PerceivedSpeechAnalysis } from '@/api/types';

export const perceivedAnalysis: PerceivedSpeechAnalysis = {
  id: 'analysis-1', perception_run_id: 'perception-1', utterance_id: 'utterance-1',
  alignment_reference_text: '周谋', reference_kind: 'perceived_text', analyzer_version: 'v1',
  status: 'succeeded', error_code: null, latency_ms: 14, created_at: '2026-09-17T12:00:00Z',
  data: {
    tone_graph: {
      mine: { baseline_hz: 200, segments: [
        [{ timestamp_seconds: .1, normalized_semitones: -2 }, { timestamp_seconds: .14, normalized_semitones: 0 }],
        [{ timestamp_seconds: .7, normalized_semitones: 1 }, { timestamp_seconds: .74, normalized_semitones: 2 }],
      ] },
      filtered: { baseline_hz: 200, segments: [
        Array.from({ length: 5 }, (_, i) => ({ timestamp_seconds: .1 + i * .01, normalized_semitones: -2 + i * .5 })),
        Array.from({ length: 5 }, (_, i) => ({ timestamp_seconds: .7 + i * .01, normalized_semitones: 1 + i * .25 })),
      ] },
      raw: Array.from({ length: 120 }, (_, i) => ({ timestamp_seconds: i / 100,
        tracker_f0_hz: i >= 10 && i < 15 || i >= 70 && i < 75 ? 200 : null,
        f0_hz: i >= 10 && i < 15 || i >= 70 && i < 75 ? 200 : null,
        selected_f0_hz: i >= 10 && i < 15 || i >= 70 && i < 75 ? 200 : null,
        retained: i >= 10 && i < 15 || i >= 70 && i < 75,
      })),
    },
    syllables: [
      { index: 0, character_start: 0, character_end: 1, characters: '周', pinyin: 'zhōu',
        observed_gesture: 'unclear', observed_confidence: 'low', lexical_tone: 1, expected_surface_tone: 1, reading_source: 'dictionary', alternatives: ['zhou1'], start_seconds: 0, end_seconds: 0.6,
        expected_tone: [{ position: 0, height: 1 }, { position: 1, height: 1 }] },
      { index: 1, character_start: 1, character_end: 2, characters: '谋', pinyin: 'móu',
        observed_gesture: 'unclear', observed_confidence: 'low', lexical_tone: 2, expected_surface_tone: 2, reading_source: 'dictionary', alternatives: ['mou2'], start_seconds: 0.6, end_seconds: 1.2,
        expected_tone: [{ position: 0, height: 0.5 }, { position: 1, height: 1 }] },
    ],
    measured_pitch: [
      { timestamp_seconds: 0.1, f0_hz: 170, normalized_semitones: -2, voicing_probability: 0.8 },
      { timestamp_seconds: 0.2, f0_hz: null, normalized_semitones: null, voicing_probability: 0.1 },
      { timestamp_seconds: 1.1, f0_hz: 210, normalized_semitones: 2, voicing_probability: 0.7 },
    ],
    duration_seconds: 1.2, voiced_fraction: 0.7, pitch_status: 'available', alignment_status: 'aligned',
    alignment_error_code: null, quality_issues: [], observations: ['Expected shapes show lexical tones.'],
    pitch_latency_ms: 10, alignment_latency_ms: 4, expected_tone_basis: 'schematic_lexical_tones',
    evidence_status: 'recorded_audio',
  },
};
