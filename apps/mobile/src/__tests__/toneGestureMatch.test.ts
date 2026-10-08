import { perceivedAnalysis } from './perceivedFixture';

import type { PerceivedSyllable } from '@/api/types';
import { toneGestureMatch } from '@/speech/toneGestureMatch';

const base: PerceivedSyllable = { ...perceivedAnalysis.data.syllables[1]!, observed_gesture: 'falling', observed_confidence: 'moderate',
  pitch_eligibility: { state: 'sufficient' }, tone_comparison_policy: 'experimental',
  observed_contour: { classification: '4-like', confidence: 'moderate', reason: 'acoustic_shape_only', features: {} } };

it.each(['rising', 'falling'] as const)('keeps even a sufficient %s gesture descriptive under experimental policy', gesture => {
  expect(toneGestureMatch({ ...base, observed_gesture: gesture })).toMatchObject({ observed_gesture: gesture, reference_tone: 2, comparison: 'uncertain' });
});

it.each(['incomplete', 'unstable', 'insufficient'] as const)('cannot revive confident feedback from a stale contour when backend evidence is %s', state => {
  for (const reference of [0, 1, 2, 3, 4, null] as const) {
    expect(toneGestureMatch({ ...base, expected_surface_tone: reference, pitch_eligibility: { state } })).toMatchObject({
      observed_gesture: 'unclear', observed_confidence: 'low', comparison: 'uncertain',
    });
  }
});

it('requires backend eligibility for old responses and leaves grouped words without character grades', () => {
  const legacy = { ...base };
  delete legacy.pitch_eligibility;
  expect(toneGestureMatch(legacy)).toMatchObject({ observed_gesture: 'unclear', comparison: 'uncertain' });
  expect(toneGestureMatch(base, false)).toMatchObject({ observed_gesture: 'unclear', comparison: 'uncertain' });
  expect(toneGestureMatch({ ...base, reading_source: 'unresolved' }).reference_tone).toBeNull();
});

it('keeps reference and target identity separate and never emits a pronunciation grade', () => {
  for (const [characters, reference, gesture] of [['贵', 4, 'dipping'], ['州', 1, 'falling']] as const) {
    const s = { ...base, characters, lexical_tone: reference, expected_surface_tone: reference, observed_gesture: gesture };
    const before = JSON.stringify(s);
    for (const target of ['广州', '贵州', 'nonsense']) {
      const result = toneGestureMatch({ ...s, intended_target: target } as typeof s);
      expect(result).toMatchObject({ observed_gesture: gesture, reference_tone: reference, comparison: 'uncertain' });
      expect(JSON.stringify(result)).not.toMatch(/pronunciation|score|correct|detected_tone/);
    }
    expect(JSON.stringify(s)).toBe(before);
  }
});
