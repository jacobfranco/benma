import { line, piecewise, copy } from './toneFeedbackFixture';

import { classifyPitchShape, type ShapePoint } from '@/speech/pitchShape';
import { classifyToneLikeness, type ToneFamily, TONE_MARGIN } from '@/speech/toneLikeness';
import { pronunciationChunks } from '@/speech/pronunciationChunks';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import type { PerceivedSpeechAnalysis } from '@/api/types';

const cases = require('./fixtures/naturalToneContours.json') as {
  id: string; knots: [number, number][]; tone: string; strength: string;
}[];
const classify = (points: ShapePoint[], flags: number[] = []) =>
  classifyToneLikeness(classifyPitchShape([points], flags), [points]);

it.each(cases)('ranks natural $id with separate family and strength', c => {
  const observed = classify(line(piecewise(c.knots), 61));
  expect(observed).toMatchObject({ tone: c.tone, strength: c.strength, evidence: 'trustworthy' });
  if (c.tone === 'UNCLEAR' && c.id !== 'opposing-hump') {
    expect(observed.reason).toBe('close_candidates');
    expect(observed.margin).toBeLessThan(TONE_MARGIN);
  }
});

it.each(cases.filter(c => c.tone !== 'UNCLEAR'))('keeps $id through transposition, point deletion and timing perturbations', c => {
  const points = line(piecewise(c.knots), 61);
  const variants = [points.slice(1), points.slice(0, -1), points.filter((_, i) => i !== 11),
    points.filter((_, i) => i !== 35), points.filter((_, i) => i % 10 !== 9),
    points.map((p, i) => ({ ...p, timestamp_seconds: p.timestamp_seconds + (i === 25 ? .004 : 0) })),
    points.map(p => ({ ...p, timestamp_seconds: p.timestamp_seconds * 1.015 + .01 })),
    points.map((p, i) => ({ ...p, normalized_semitones: p.normalized_semitones + (i === 0 ? .015 : 0) })),
    ...[-24, -.3, .3, 24].map(shift => points.map(p => ({ ...p, normalized_semitones: p.normalized_semitones + shift }))),
  ];
  for (const variant of variants) expect(classify(variant).tone).toBe(c.tone);
});

it('keeps coherent movement distinct from equally small jitter', () => {
  expect(classify(line(x => .4 * x + .015 * Math.sin(x * 28)))).toMatchObject({ tone: 'TONE_2', strength: 'weak' });
  expect(classify(line(x => .05 * Math.sin(x * 80)))).toMatchObject({ tone: 'UNCLEAR', decision: 'UNCLEAR' });
  const alternating = line(() => 0).map((p, i) => ({ ...p, normalized_semitones: i % 2 ? .05 : -.05 }));
  expect(classify(alternating)).toMatchObject({ tone: 'UNCLEAR', decision: 'UNCLEAR', evidence: 'trustworthy' });
  expect(classify(line(x => .1 * x))).toMatchObject({ tone: 'TONE_1' });
});

it('changes support smoothly around the old 1 st excursion cliff', () => {
  for (const family of ['rise', 'fall', 'valley'] as const) {
    const observed = [.98, .99, 1, 1.01, 1.02].map(a => classify(line(x =>
      family === 'rise' ? a * x : family === 'fall' ? -a * x : a * Math.abs(2 * x - 1))));
    const tone: ToneFamily = family === 'rise' ? 'TONE_2' : family === 'fall' ? 'TONE_4' : 'TONE_3';
    for (const result of observed) expect(result).toMatchObject({ tone, strength: 'weak' });
    for (let i = 1; i < observed.length; i++) for (const key of Object.keys(observed[i]!.fits) as ToneFamily[])
      expect(Math.abs(observed[i]!.fits[key] - observed[i - 1]!.fits[key])).toBeLessThan(.02);
  }
});

it('retains structural and raw-branch vetoes even if canonical retained geometry is stable', () => {
  const points = line(x => .4 * x);
  expect(classify(points.slice(0, 5))).toMatchObject({ tone: 'UNCLEAR', evidence: 'unavailable' });
  expect(classify(points, [points[20]!.timestamp_seconds])).toMatchObject({ tone: 'UNCLEAR', evidence: 'unavailable', reason: 'raw_tracker_discontinuity' });
  expect(classify(points.map((p, i) => ({ ...p, normalized_semitones: p.normalized_semitones + (i >= 25 ? 12 : 0) }))))
    .toMatchObject({ tone: 'UNCLEAR', evidence: 'unavailable' });
  const segments = [points.slice(0, 22), points.slice(25).map(p => ({ ...p, normalized_semitones: 3 - p.normalized_semitones }))];
  expect(classifyToneLikeness(classifyPitchShape(segments), segments)).toMatchObject({ tone: 'UNCLEAR', evidence: 'unavailable' });
});

it('does not use target, reading or expected tone to select the acoustic family', () => {
  const physical = require('./fixtures/toneClassificationPhysical.json') as PerceivedSpeechAnalysis[];
  const project = (a: PerceivedSpeechAnalysis) => pronunciationChunks(a.data).flatMap(c =>
    gradeChunkPitch(a, c).constituents.map(e => e.observed));
  for (const analysis of physical) {
    const baseline = project(analysis), before = JSON.stringify(analysis);
    for (const intended of ['广州', '我想买这个', 'unrelated']) {
      const changed = { ...copy(analysis), intended_text: intended };
      changed.data.syllables.forEach(s => { s.lexical_tone = 1; s.expected_surface_tone = 4; });
      expect(project(changed)).toEqual(baseline);
    }
    expect(JSON.stringify(analysis)).toBe(before);
  }
});

it.each([.1, .2, .4])('weights coherent %s st movements proportionally in both directions', amplitude => {
  for (const sign of [-1, 1]) {
    const result = classify(line(x => sign * amplitude * x));
    expect(result.evidence).toBe('trustworthy');
    expect(result.tone).toBe(amplitude === .1 ? 'TONE_1' : amplitude === .2 ? 'UNCLEAR' : sign > 0 ? 'TONE_2' : 'TONE_4');
  }
});
it('varies small-movement scores continuously on either side of 0.2 st', () => {
  for (const sign of [-1, 1]) {
    const results = [.19, .195, .2, .205, .21].map(a => classify(line(x => sign * a * x)));
    for (let i = 1; i < results.length; i++) for (const key of Object.keys(results[i]!.fits) as ToneFamily[])
      expect(Math.abs(results[i]!.fits[key] - results[i - 1]!.fits[key])).toBeLessThan(.025);
  }
});
