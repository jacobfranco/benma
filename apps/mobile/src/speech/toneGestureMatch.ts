import type { PerceivedSyllable } from '@/api/types';

export type ToneGestureComparison = 'consistent' | 'different' | 'uncertain';
export type ToneGestureFeedback = {
  observed_gesture: PerceivedSyllable['observed_gesture'];
  observed_confidence: PerceivedSyllable['observed_confidence'];
  reference_tone: PerceivedSyllable['expected_surface_tone'];
  comparison: ToneGestureComparison;
};
export const gestureLabel = { level: 'level-like', rising: 'rising', dipping: 'dipping / valley-like', falling: 'falling', unclear: 'unclear' } as const;

// Product policy, not the historical laboratory verdict. No acoustic classification
// or display geometry here: the backend owns the observed gesture and confidence.
export function toneGestureMatch(s: PerceivedSyllable, characterEvidence = true): ToneGestureFeedback {
  const reference = s.reading_source !== 'unresolved' && s.pinyin && s.lexical_tone != null
    ? s.expected_surface_tone ?? null : null;
  const eligible = characterEvidence && s.pitch_eligibility?.state === 'sufficient';
  const feedback: ToneGestureFeedback = {
    observed_gesture: eligible ? s.observed_gesture ?? 'unclear' : 'unclear',
    observed_confidence: eligible ? s.observed_confidence ?? 'low' : 'low',
    reference_tone: reference,
    comparison: 'uncertain',
  };
  // Current backend policy is experimental. Acoustic completeness alone cannot
  // verify speech presence or exclude a sustained wrong tracker branch. Keep all
  // references descriptive until that independent product blocker is resolved.
  return feedback;
}
