import { dominantCases, gestureKnots, piecewise } from './toneFeedbackFixture';

import { classifyPitchShape, type ShapePoint } from '@/speech/pitchShape';
import { shapeDisplay } from '@/speech/pitchShapeDisplay';
import { normalizedGeometry } from '@/components/PitchPlot';
import { expectedShapeLabel } from '@/speech/pitchShapeEvidence';
import type { PerceivedSyllable } from '@/api/types';

const line = (fn: (x: number) => number, n = 51): ShapePoint[] => Array.from({ length: n }, (_, i) =>
  ({ timestamp_seconds: i * .01, normalized_semitones: fn(i / (n - 1)) }));
const valley = (fall: number, rise: number) => line(x => x < .5 ? fall * (1 - x * 2) : rise * (x * 2 - 1));
it.each([
  ['LEVEL', line(x => .1 * Math.sin(x * 20))], ['RISING', line(x => x * 4)],
  ['FALLING', line(x => -x * 4)], ['DIP_RISE', valley(4, 4)],
  ['DIP_RISE', valley(3, 5)], ['DIP_RISE', valley(3, 1.5)],
  ['LEVEL', line(x => .2 * x)],
] as const)('describes %s from relative numeric geometry and survives perturbations', (shape, points) => {
  const result = classifyPitchShape([points]);
  expect(result.shape).toBe(shape);
  expect(Object.values(result.perturbations)).toHaveLength(6);
  expect(Object.values(result.perturbations).every(s => s === shape)).toBe(true);
  expect(classifyPitchShape([points.map(p => ({ ...p, normalized_semitones: p.normalized_semitones + 24 }))]).shape).toBe(shape);
});
it('keeps contradictory fragments, a missing valley and discontinuities unclear', () => {
  const v = valley(4, 4);
  expect(classifyPitchShape([v.slice(0, 17), v.slice(35)]).shape).toBe('UNCLEAR');
  const contradictory = line(x => x * -4);
  expect(classifyPitchShape([contradictory.slice(0, 23), contradictory.slice(27).map(p => ({ ...p, normalized_semitones: p.normalized_semitones + 4 }))]).shape).toBe('UNCLEAR');
  expect(classifyPitchShape([v.map((p, i) => ({ ...p, normalized_semitones: p.normalized_semitones + (i === 25 ? 12 : 0) }))]).shape).toBe('UNCLEAR');
  expect(classifyPitchShape([v.slice(0, 5)]).shape).toBe('UNCLEAR');
});

const corpus = require('../../../../docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json') as {
  id: string; start: number; end: number; manual_geometry: string; current_gesture: string;
  segments: { index: number; t: number; st: number }[][]; flagged_indices: number[];
}[];
const evidence = (row: typeof corpus[number]) => row.segments.map(s => s.map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
it('replays all frozen evidence without mutation and retains every previously useful description', () => {
  const before = JSON.stringify(corpus);
  for (const row of corpus) {
    const shape = classifyPitchShape(evidence(row), row.segments.flat().filter(p => row.flagged_indices.includes(p.index)).map(p => p.t));
    const old = row.current_gesture === 'dipping' ? 'DIP_RISE' : row.current_gesture.toUpperCase();
    if (old !== 'UNCLEAR' && old === row.manual_geometry) expect(shape.shape).toBe(old);
  }
  expect(JSON.stringify(corpus)).toBe(before);
});
it.each(['7e6b6fe9:我', '7e6b6fe9:想', '7e6b6fe9:买', '89cee47e:我'])('recovers retained valley %s despite the saved strict result', id => {
  expect(classifyPitchShape(evidence(corpus.find(r => r.id === id)!)).shape).toBe('DIP_RISE');
});
it('abstains when the borderline valley changes under deletion', () => {
  const result = classifyPitchShape(evidence(corpus.find(r => r.id === '4b9dbd2b:苹')!));
  expect(result.shape).toBe('UNCLEAR');
  expect(result.reason).toBe('perturbation_sensitive');
});
it('normalizes timing endpoints independently of duration, retaining gaps and chunk proportions', () => {
  for (const duration of [.25, .6]) {
    const points = [[{ timestamp_seconds: 2, normalized_semitones: 0 }, { timestamp_seconds: 2 + duration, normalized_semitones: 1 }]];
    const { layout, domain } = shapeDisplay(points, 2, 2 + duration);
    expect(layout.segments[0]!.map(p => p.position)).toEqual([0, 1]);
    expect(normalizedGeometry(layout, 160, 96, domain)[0]!.map(p => p.x)).toEqual([0, 160]);
  }
  const segments = [[{ timestamp_seconds: 2.34, normalized_semitones: 2 }], [{ timestamp_seconds: 2.70, normalized_semitones: 0 }]];
  const before = JSON.stringify(segments);
  const { layout } = shapeDisplay(segments, 2.34, 3.04, [{ label: '这', start: 2.34, end: 2.73 }, { label: '个', start: 2.74, end: 3.04 }]);
  expect(layout.segments).toHaveLength(2);
  expect(layout.segments[1]![0]!.position).toBeCloseTo(.36 / .70);
  expect(layout.regions[0]!.end).toBeCloseTo(.39 / .70);
  expect(layout.regions[1]!.start).toBeCloseTo(.40 / .70);
  expect(layout.regions[1]!.end).toBe(1);
  expect(JSON.stringify(segments)).toBe(before);
});
it('preserves every selected value and gap; local scaling caps noise and includes outliers', () => {
  for (const row of corpus) {
    const input = evidence(row), before = JSON.stringify(input);
    const { domain, layout } = shapeDisplay(input, row.start, row.end);
    expect(layout.segments.map(s => s.map(({ position: _, ...p }) => p))).toEqual(input);
    expect(JSON.stringify(input)).toBe(before);
    expect(domain[1] - domain[0]).toBeGreaterThanOrEqual(6 - 1e-8);
    expect(input.flat().every(p => p.normalized_semitones >= domain[0] && p.normalized_semitones <= domain[1])).toBe(true);
  }
  const { domain } = shapeDisplay([line(x => .2 * Math.sin(x * 20))], 0, .5);
  expect(domain[1] - domain[0]).toBe(6);
});
it('uses contextual surface expectations with explicit family fallback and no audio tone inference', () => {
  const s = { pinyin: 'wǒ', reading_source: 'dictionary', lexical_tone: 3 } as PerceivedSyllable;
  expect(expectedShapeLabel({ ...s, expected_surface_tone: null })).toBe('Tone 3 family');
  expect(expectedShapeLabel({ ...s, expected_surface_tone: 3 })).toContain('full rise is optional');
  expect(expectedShapeLabel({ ...s, expected_surface_tone: 2, surface_rule: 'third_tone_pair' })).toBe('Rising');
  expect(expectedShapeLabel({ ...s, expected_surface_tone: 0 })).toContain('Flexible');
  expect(expectedShapeLabel({ ...s, expected_surface_tone: 4, surface_rule: 'yi_quantity' })).toBe('Falling');
  expect(expectedShapeLabel({ ...s, expected_surface_tone: 2, surface_rule: 'bu_before_fourth' })).toBe('Rising');
});

it.each(dominantCases)('keeps dominant %s geometry through transposition and all stability checks', (name, shape) => {
  for (const shift of [-24, 0, 24]) {
    const points = line(x => piecewise(gestureKnots[name])(x) + shift, 101);
    const result = classifyPitchShape([points]);
    expect(result.shape).toBe(shape);
    expect(Object.values(result.perturbations)).toEqual(Array(6).fill(shape));
    if (name !== 'textbook') {
      expect(result.reason).toBe('dominant_supported_gesture');
      expect(result.features.counter_excursion_st! / result.features.dominant_excursion_st!).toBeLessThan(.25);
    }
  }
});
it.each(['competing', 'competingValley'] as const)('does not discard the comparable opposing movement in %s', name => {
  expect(classifyPitchShape([line(piecewise(gestureKnots[name]), 101)]).shape).toBe('UNCLEAR');
});
it('does not let a dominant gesture bypass support, branches, fragment or deletion gates', () => {
  const points = line(piecewise(gestureKnots.lateFall), 101);
  for (const segments of [[points.slice(0, 5)], [points.slice(0, 25), points.slice(60)],
    [points.map((p, i) => ({ ...p, normalized_semitones: p.normalized_semitones + (i >= 60 ? 12 : 0) }))],
    [points.slice(0, 45), points.slice(49).map(p => ({ ...p, normalized_semitones: p.normalized_semitones + 4 }))]]) {
    expect(classifyPitchShape(segments).shape).toBe('UNCLEAR');
    expect(classifyPitchShape(segments).structurallyUsable).not.toBe(true);
  }
  expect(classifyPitchShape([points], points.slice(25, 60).map(p => p.timestamp_seconds)))
    .toMatchObject({ shape: 'UNCLEAR', reason: 'perturbation_sensitive', structurallyUsable: false });
});
