import { line, valley, freshToneAnalysis, dominantCases, gestureKnots, piecewise } from './toneFeedbackFixture';

import { classifyPitchShape } from '@/speech/pitchShape';
import { classifyToneLikeness, TONE_MARGIN } from '@/speech/toneLikeness';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { pronunciationChunks } from '@/speech/pronunciationChunks';

const classify = (points: ReturnType<typeof line>) => classifyToneLikeness(classifyPitchShape([points]), [points]);
it.each([
  ['TONE_1', line(x => .1 * Math.sin(x * 20)), 'full'],
  ['TONE_2', line(x => 4 * x), 'full'], ['TONE_4', line(x => -4 * x), 'full'],
  ['TONE_3', valley(4, 4), 'full'], ['TONE_3', valley(3, 5), 'full'],
  ['TONE_2', line(x => 1.9 * x), 'weak'], ['TONE_4', line(x => -1.9 * x), 'weak'],
  ['TONE_3', valley(1.4, 1.4), 'weak'], ['TONE_3', valley(3, 1.4), 'weak'],
] as const)('ranks %s from stable geometry with %s strength', (tone, points, strength) => {
  const result = classify(points);
  expect(result).toMatchObject({ tone, best: tone, strength, reason: 'best_fit' });
  expect(result.margin).toBeGreaterThanOrEqual(TONE_MARGIN);
  const transposed = classify(points.map(p => ({ ...p, normalized_semitones: p.normalized_semitones + 24 })));
  expect(transposed.tone).toBe(result.tone);
  for (const key of Object.keys(result.fits) as (keyof typeof result.fits)[]) expect(transposed.fits[key]).toBeCloseTo(result.fits[key]);
});
it('recognizes an early fall and supported low tail as a reduced valley family acoustically', () => {
  const points = line(x => x < .35 ? 3 * (1 - x / .35) : .1 * (x - .35));
  expect(classifyPitchShape([points]).shape).toBe('FALLING');
  expect(classify(points)).toMatchObject({ tone: 'TONE_3', variant: 'reduced_valley', strength: 'weak' });
  expect(classify(line(x => -3 * x)).tone).toBe('TONE_4');
});
it('does not give a canonical shape label a family-score bonus', () => {
  const points = line(x => .4 * x), shape = classifyPitchShape([points]);
  for (const label of ['FALLING', 'RISING', 'DIP_RISE', 'LEVEL', 'UNCLEAR'] as const)
    expect(classifyToneLikeness({ ...shape, shape: label }, [points]).tone).toBe('TONE_2');
});
it('preserves support, contradiction and perturbation abstentions', () => {
  const v = valley(4, 4);
  for (const segments of [[v.slice(0, 5)], [v.slice(0, 17), v.slice(35)],
    [v.slice(0, 23), v.slice(27).map(p => ({ ...p, normalized_semitones: p.normalized_semitones + 8 }))]]) {
    expect(classifyToneLikeness(classifyPitchShape(segments), segments).tone).toBe('UNCLEAR');
  }
});
const corpus = require('../../../../docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json') as {
  id: string; segments: { index: number; t: number; st: number }[][]; flagged_indices: number[];
}[];
it('ranks frozen geometry independently of canonical labels while preserving raw safety and evidence', () => {
  const before = JSON.stringify(corpus);
  for (const row of corpus) {
    const segments = row.segments.map(s => s.map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
    const flags = row.segments.flat().filter(p => row.flagged_indices.includes(p.index)).map(p => p.t);
    const shape = classifyPitchShape(segments, flags, row.flagged_indices.length > 0), tone = classifyToneLikeness(shape, segments);
    if (!shape.familySafe) expect(tone).toMatchObject({ tone: 'UNCLEAR', evidence: 'unavailable' });
    if (tone.tone !== 'UNCLEAR') {
      expect(tone.evidence).toBe('trustworthy');
      expect(tone.margin).toBeGreaterThanOrEqual(TONE_MARGIN);
    }
    if (['7e6b6fe9:我', '7e6b6fe9:买', '89cee47e:我'].includes(row.id)) expect(tone.tone).toBe('TONE_3');
    if (row.id === '4b9dbd2b:苹') expect(tone).toMatchObject({ tone: 'TONE_3', strength: 'weak' });
  }
  expect(JSON.stringify(corpus)).toBe(before);
});
it('replays the fresh physical 我/想/poor 买/这/个 separately from the older corpus', () => {
  const results = pronunciationChunks(freshToneAnalysis.data).flatMap(c => gradeChunkPitch(freshToneAnalysis, c).constituents);
  expect(results.map(c => [c.unit.text, c.shape.shape, c.observed.tone])).toEqual([
    ['我', 'DIP_RISE', 'UNCLEAR'], ['想', 'DIP_RISE', 'TONE_3'], ['买', 'UNCLEAR', 'UNCLEAR'],
    ['这', 'FALLING', 'TONE_4'], ['个', 'UNCLEAR', 'UNCLEAR'],
  ]);
});

it.each(dominantCases)('ranks the supported dominant %s independently of pitch register', (name, _, tone) => {
  for (const shift of [-24, 0, 24]) expect(classify(line(x => piecewise(gestureKnots[name])(x) + shift, 101)))
    .toMatchObject({ tone, strength: 'full' });
});

it.each([
  ['TONE_2', [[0, 0], [.8, 2.2], [1, 1.7]]],
  ['TONE_4', [[0, 2.2], [.8, 0], [1, .5]]],
  ['TONE_3', [[0, 4.5], [.4, 0], [.8, 1.7], [1, 1.35]]],
] as [string, [number, number][]][])('uses the full supported %s gesture for strength despite a smaller boundary transition', (tone, knots) => {
  const points = line(piecewise(knots), 101), shape = classifyPitchShape([points]);
  expect(shape.reason).toBe('dominant_supported_gesture');
  expect(classify(points)).toMatchObject({ tone, strength: 'full' });
  // The old final endpoint would weaken these otherwise full primary gestures.
  if (tone !== 'TONE_3') expect(Math.abs(shape.features.measured_net_st!)).toBeLessThan(2);
  else expect(shape.features.end_st! - shape.features.minimum_st!).toBeLessThan(1.5);
});
