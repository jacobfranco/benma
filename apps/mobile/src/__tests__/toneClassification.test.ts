import { copy, line, piecewise, replacePitch, freshToneAnalysis } from './toneFeedbackFixture';
import { chunkAnalysis } from './pronunciationChunkFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { classifyPitchShape, type ShapePoint } from '@/speech/pitchShape';
import { shapeDisplay } from '@/speech/pitchShapeDisplay';
import { pronunciationChunks } from '@/speech/pronunciationChunks';
import { classifyToneLikeness } from '@/speech/toneLikeness';

const physical = require('./fixtures/toneClassificationPhysical.json') as PerceivedSpeechAnalysis[];
const shallow: [number, number][] = [[0, .65], [.25, 0], [.82, 1.4], [1, .9]];
const classify = (segments: ShapePoint[][], flags: number[] = []) => {
  const shape = classifyPitchShape(segments, flags);
  return { shape, observed: classifyToneLikeness(shape, segments) };
};
const project = (a: PerceivedSpeechAnalysis) => pronunciationChunks(a.data).map(c => gradeChunkPitch(a, c));
const freeze = <T,>(value: T): T => {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
};

it.each([-24, 0, 24])('recognizes a completed shallow valley as weak T3 at register %s without changing the graph', shift => {
  const segments = freeze([line(x => piecewise(shallow)(x) + shift)]);
  const graph = shapeDisplay(segments, 0, .51), before = JSON.stringify(segments);
  const { shape, observed } = classify(segments);
  expect(shape).toMatchObject({ shape: 'DIP_RISE', reason: 'completed_shallow_valley', structurallyUsable: true });
  expect(Object.values(shape.perturbations)).toEqual(Array(6).fill('DIP_RISE'));
  expect(observed).toMatchObject({ tone: 'TONE_3', strength: 'weak', variant: 'completed_shallow_valley' });
  expect(JSON.stringify(segments)).toBe(before);
  expect(shapeDisplay(segments, 0, .51)).toEqual(graph);
});

it.each([
  ['onset jitter', [[0, .12], [.08, 0], [.85, 3], [1, 2.8]], 'TONE_2'],
  ['competing gesture duration', [[0, .65], [.25, 0], [.65, 1.8], [1, .15]], 'UNCLEAR'],
  ['substantial late retreat', [[0, .65], [.25, 0], [.82, 1.8], [1, .05]], 'UNCLEAR'],
] as [string, [number, number][], string][])('rejects a shallow-T3 claim for %s', (_, knots, tone) => {
  expect(classify([line(piecewise(knots))]).observed.tone).toBe(tone);
});

it('allows weak completed valleys but still requires onset support and raw corruption clearance', () => {
  for (const knots of [
    [[0, .65], [.25, 0], [.82, .7], [1, .4]],
    [[0, .65], [.7, 0], [.88, 1.8], [1, .9]],
  ] as [number, number][][]) expect(classify([line(piecewise(knots))]).observed)
    .toMatchObject({ tone: 'TONE_3', strength: 'weak' });
  expect(classify([line(piecewise([[0, .65], [.02, 0], [.82, 1.4], [1, .9]]))]).observed.tone).not.toBe('TONE_3');
  expect(classify([line(piecewise([[0, .2], [.25, 0], [.82, .3], [1, .2]]))]).observed.tone).toBe('UNCLEAR');
  const points = line(piecewise([[0, .65], [.25, 0], [.82, 1.8], [1, 1.1]]));
  expect(classify([points], [points[25]!.timestamp_seconds]).observed.tone).toBe('UNCLEAR');
  expect(classify([points.slice(0, 10), points.slice(20)]).observed.tone).toBe('UNCLEAR');
});

const islands = (family: 'fall' | 'valley', tailCount = 3, jump = 2): ShapePoint[][] => {
  const main = line(family === 'fall' ? x => -4 * x : x => Math.abs(2 * x - 1) * 4);
  const tail = line(x => main.at(-1)!.normalized_semitones + jump - .1 * x, tailCount, .53);
  return [main, tail];
};
it.each(['fall', 'valley'] as const)('uses a dominant %s island with a tiny late fragment, preserving both islands', family => {
  for (const shift of [-24, 0, 24]) {
    const segments = freeze(islands(family).map(s => s.map(p => ({ ...p, normalized_semitones: p.normalized_semitones + shift }))));
    const before = shapeDisplay(segments, 0, .56), result = classify(segments);
    expect(result.shape).toMatchObject({ reason: 'dominant_supported_island', structurallyUsable: true });
    expect(result.observed).toMatchObject({ tone: family === 'fall' ? 'TONE_4' : 'TONE_3', strength: 'full' });
    expect(result.observed.tone).toBe(classify([segments[0]!]).observed.tone);
    expect(shapeDisplay(segments, 0, .56)).toEqual(before);
    expect(before.layout.segments.map(s => s.length)).toEqual([51, 3]);
  }
});
it.each([
  ['comparable second island', islands('fall', 41)],
  ['large branch', islands('fall', 3, 6.5)],
  ['octave branch', islands('fall', 3, 12)],
  ['substantial secondary movement', [islands('fall')[0]!, line(x => -2 + 2 * x, 4, .53)]],
  ['repeated fragmentation', [...islands('fall'), line(x => x, 3, .59)]],
  ['early fragment', [line(x => 3 + x, 3), line(x => -4 * x, 51, .05)]],
] as [string, ShapePoint[][]][])('preserves hard abstention for %s', (_, segments) => {
  expect(classify(segments).observed.tone).toBe('UNCLEAR');
});
it('does not let a tiny island repair an ambiguous primary or raw branch flag', () => {
  const segments = islands('fall');
  expect(classify(segments, [.52]).observed.tone).toBe('UNCLEAR');
  const ambiguous = line(piecewise([[0, 0], [.5, 3], [1, 0]]));
  expect(classify([ambiguous, line(x => 2 + .1 * x, 3, .53)]).observed.tone).toBe('UNCLEAR');
});

it('applies all three new paths independently of intended text and preserves saved evidence exactly', () => {
  const synthetic = copy(freshToneAnalysis); replacePitch(synthetic, 1, piecewise(shallow));
  for (const analysis of [synthetic, ...physical]) {
    freeze(analysis);
    const before = JSON.stringify(analysis), baseline = project(analysis);
    for (const intended_text of ['广州', '贵州', '我想买这个', null]) {
      expect(project({ ...analysis, intended_text, target: intended_text,
        data: { ...analysis.data, target: intended_text } } as PerceivedSpeechAnalysis)).toEqual(baseline);
    }
    expect(JSON.stringify(analysis)).toBe(before);
  }
});
it('keeps Google shallow 想 weak T3 while raw branches remain unavailable and neutral cannot hide an unavailable head', () => {
  const chunks = project(physical[0]!);
  expect(chunks.flatMap(c => c.constituents).map(c => [c.unit.text, c.observed.tone, c.observed.strength, c.grade.agreement, c.role])).toEqual([
    ['我', 'UNCLEAR', 'unavailable', 'UNAVAILABLE', 'grade_bearing'],
    ['想', 'TONE_3', 'weak', 'STRONG_MATCH', 'grade_bearing'],
    ['买', 'UNCLEAR', 'unavailable', 'UNAVAILABLE', 'grade_bearing'],
    ['这', 'UNCLEAR', 'unavailable', 'UNAVAILABLE', 'grade_bearing'],
    ['个', 'UNCLEAR', 'unavailable', 'UNAVAILABLE', 'neutral_unreliable_nonveto'],
  ]);
  expect(chunks[1]!.constituents[0]!.shape.reason).toBe('completed_shallow_valley');
  expect(chunks.at(-1)!.grade.agreement).toBe('UNAVAILABLE');
});
it('recognizes human weak 我/想 families and keeps 买 strong and late 这 fragment subordinate', () => {
  const chunks = project(physical[1]!);
  expect(chunks.flatMap(c => c.constituents).map(c => [c.unit.text, c.observed.tone, c.grade.agreement, c.role])).toEqual([
    ['我', 'TONE_3', 'STRONG_MATCH', 'grade_bearing'],
    ['想', 'TONE_4', 'PARTIAL_OR_WEAK', 'grade_bearing'],
    ['买', 'TONE_3', 'STRONG_MATCH', 'grade_bearing'],
    ['这', 'TONE_4', 'STRONG_MATCH', 'grade_bearing'],
    ['个', 'UNCLEAR', 'UNAVAILABLE', 'neutral_unmeasured_nonveto'],
  ]);
  expect(chunks.at(-1)!.constituents[0]!.shape.reason).toBe('dominant_supported_island');
  expect(chunks.at(-1)!.grade.agreement).toBe('STRONG_MATCH');
});
it('preserves frozen corrupted 买 in both full saved analyses and the historical numeric corpus', () => {
  const sparse = require('../../../../services/api/tests/fixtures/pitch_measurement_430fcc2e.json') as PerceivedSpeechAnalysis;
  for (const analysis of [freshToneAnalysis, sparse]) expect(project(analysis)[2]!.grade.agreement).toBe('UNAVAILABLE');
  const corpus = require('../../../../docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json') as {
    id: string; segments: { t: number; st: number }[][]; flagged_indices: number[];
  }[];
  const row = corpus.find(r => r.id === '89cee47e:买')!;
  const segments = row.segments.map(s => s.map(p => ({ timestamp_seconds: p.t, normalized_semitones: p.st })));
  // These frozen raw flags are outside the retained projection; retain their
  // safety meaning instead of silently losing them during numeric replay.
  const shape = classifyPitchShape(segments, [], row.flagged_indices.length > 0);
  expect(classifyToneLikeness(shape, segments)).toMatchObject({ tone: 'UNCLEAR', evidence: 'unavailable' });
});
it('bounds unreliable neutral non-veto by semantic chunk context and head evidence', () => {
  for (const text of ['那个', '去吧', '我要一个苹果']) {
    const a = chunkAnalysis(text), head = text === '我要一个苹果' ? 2 : 0;
    replacePitch(a, head, x => text === '我要一个苹果' ? 4 * x : -4 * x);
    replacePitch(a, head + 1, x => x < .5 ? 4 * x : 12 + 4 * x);
    const chunk = pronunciationChunks(a.data).find(c => c.members.some(s => s.index === head + 1))!;
    const result = gradeChunkPitch(a, chunk);
    expect(result.constituents.at(-1)!.role).toBe(text === '那个' ? 'neutral_unreliable_nonveto' : 'grade_bearing');
    expect(result.grade.agreement).toBe(text === '那个' ? 'STRONG_MATCH' : 'UNAVAILABLE');
  }
});
