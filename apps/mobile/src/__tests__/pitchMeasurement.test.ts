import type { PerceivedSpeechAnalysis } from '@/api/types';
import { normalizedGeometry } from '@/components/PitchPlot';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { classifyPitchShape, type ShapePoint } from '@/speech/pitchShape';
import { shapeDisplay } from '@/speech/pitchShapeDisplay';
import { unitShape } from '@/speech/pitchShapeEvidence';
import { chunkPitch, pronunciationChunks } from '@/speech/pronunciationChunks';
import { pronunciationUnits, unitPitch } from '@/speech/pronunciationWorkspace';
import { classifyToneLikeness } from '@/speech/toneLikeness';

const physical = require('../../../../services/api/tests/fixtures/pitch_measurement_430fcc2e.json') as PerceivedSpeechAnalysis;
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));
const freeze = <T,>(value: T): T => {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
};
const curve = (fn: (x: number) => number, start: number, count: number): ShapePoint[] =>
  Array.from({ length: count }, (_, i) => ({ timestamp_seconds: start + i * .01,
    normalized_semitones: fn(i / (count - 1)) }));
const valley = (x: number) => Math.abs(2 * x - 1) * 4;
const times = (segments: readonly (readonly ShapePoint[])[]) => segments.flat().map(p => p.timestamp_seconds);
function synthetic(bounds: number[][]) {
  const data = clone(physical.data);
  data.duration_seconds = bounds.at(-1)![1]! + .1;
  data.timing_groups = [];
  data.syllables = data.syllables.map((s, i) => ({ ...s, characters: 'ABCDE'[i]!, pinyin: 'control',
    start_seconds: bounds[i]![0]!, end_seconds: bounds[i]![1]!, pitch_projection: null }));
  data.pronunciation_chunk_candidates = [{ text: 'DE', character_start: 3, character_end: 5,
    syllable_indices: [3, 4], reason: 'lexical_word' }];
  data.measured_pitch = [];
  data.tone_graph = { raw: [], mine: { segments: [] }, filtered: { segments: [] } };
  return data;
}

it.each([0, 7.1234])('owns a continuous five-gesture recording at global offset %s without moving B/C evidence', offset => {
  const bounds = [[0, .3], [.3, .7], [.7, 1.1], [1.1, 1.4], [1.4, 1.5]].map(s => s.map(t => t + offset));
  const data = synthetic(bounds);
  const gestures = [(x: number) => x * 4, valley, valley, (x: number) => -x * 4, (x: number) => -x];
  const expected = bounds.map(([a, b], i) => curve(gestures[i]!, a!, Math.round((b! - a!) / .01)));
  // One global segment deliberately crosses every syllable boundary.
  data.tone_graph!.filtered.segments = [expected.flat()];
  freeze(data);
  const units = pronunciationUnits(data);
  units.forEach((u, i) => expect(unitPitch(data, u, units).segments).toEqual([expected[i]]));
  const chunks = pronunciationChunks(data, units);
  expect(chunks.map(c => c.text)).toEqual(['A', 'B', 'C', 'DE']);
  expect(chunkPitch(data, chunks[3]!, units).segments).toEqual(expected.slice(3));
  expect(new Set(units.flatMap(u => times(unitPitch(data, u, units).segments))).size).toBe(expected.flat().length);
});

it.each([.5, .5004, .50000001, .49999999])('handles exact and fractional boundary %s without millisecond rounding', boundary => {
  const data = synthetic([[0, boundary], [boundary, .8], [.8, 1], [1.0004, 1.3], [1.6, 1.7]]);
  const samples = [0, boundary - 1e-8, boundary, boundary + 1e-8, .79999999, .8, .99999999, 1, 1.0002,
    1.0004, 1.29999999, 1.3, 1.5, 1.6, 1.69999999, 1.7].map(t => ({ timestamp_seconds: t, normalized_semitones: t }));
  data.tone_graph!.filtered.segments = [samples];
  const units = pronunciationUnits(data);
  const assigned = units.map(u => times(unitPitch(data, u, units).segments));
  units.forEach((u, i) => expect(assigned[i]).toEqual(samples.filter(p => u.start <= p.timestamp_seconds && p.timestamp_seconds < u.end).map(p => p.timestamp_seconds)));
  expect(assigned[0]).not.toContain(boundary);
  expect(assigned[1]).toContain(boundary);
  expect(assigned.flat()).not.toEqual(expect.arrayContaining([1, 1.0002, 1.3, 1.5, 1.7]));
  for (const gap of [1, 1.0002, 1.3, 1.5, 1.7]) expect(assigned.flat()).not.toContain(gap);
  expect(new Set(assigned.flat()).size).toBe(assigned.flat().length);
  // The 300 ms pause vetoes DE merging; the sub-ms gap never invents a point.
  expect(pronunciationChunks(data).map(c => c.text)).toEqual(['A', 'B', 'C', 'D', 'E']);
});

it('resolves tolerated overlap by later start and then perceived index, with no duplicate owned evidence', () => {
  const data = synthetic([[0, .5004], [.5, .8], [.8, 1], [1, 1.3], [1.3, 1.5]]);
  data.tone_graph!.filtered.segments = [[.4999, .5, .5002, .5004].map(t => ({ timestamp_seconds: t, normalized_semitones: 0 }))];
  let units = pronunciationUnits(data);
  expect(times(unitPitch(data, units[0]!, units).segments)).toEqual([.4999]);
  expect(times(unitPitch(data, units[1]!, units).segments)).toEqual([.5, .5002, .5004]);
  data.syllables[1]!.start_seconds = 0;
  units = pronunciationUnits(data);
  expect(unitPitch(data, units[0]!, units).segments).toEqual([]);
  expect(times(unitPitch(data, units[1]!, units).segments)).toEqual([.4999, .5, .5002, .5004]);
});

it.each(['rise', 'valley', 'fall', 'disconnected', 'sparse'] as const)('projects %s topology at mobile widths without deleting, joining or creating extrema', name => {
  const points = curve(name === 'rise' ? x => x * 4 : name === 'fall' ? x => -x * 4 : valley, 4.1234, 41);
  const segments = name === 'disconnected' ? [points.slice(0, 14), points.slice(23)] : name === 'sparse' ? [[points[0]!, points[20]!, points[40]!]] : [points];
  freeze(segments);
  for (const scale of [.5, 1, 2]) {
    const input = segments.map(s => s.map(p => ({ ...p, timestamp_seconds: 4 + (p.timestamp_seconds - 4) * scale })));
    const end = 4 + .6 * scale;
    const { layout, domain } = shapeDisplay(input, 4, end);
    for (const width of [156, 226, 248]) {
      const projected = normalizedGeometry(layout, width, 88, domain);
      expect(projected.map(s => s.length)).toEqual(input.map(s => s.length));
      projected.forEach((segment, i) => segment.forEach((p, j) => {
        const source = input[i]![j]!;
        expect(4 + p.x / width * (end - 4)).toBeCloseTo(source.timestamp_seconds, 12);
        expect(domain[0] + (88 - p.y) / 88 * (domain[1] - domain[0])).toBeCloseTo(source.normalized_semitones, 12);
        if (j) expect(p.x).toBeGreaterThan(segment[j - 1]!.x);
      }));
      if (name === 'valley' || name === 'sparse') {
        const ys = projected.flat().map(p => p.y);
        expect(Math.max(...ys)).toBeGreaterThan(Math.max(ys[0]!, ys.at(-1)!));
      }
      if (name === 'rise') expect(projected[0]!.at(-1)!.y).toBeLessThan(projected[0]![0]!.y);
      if (name === 'fall') expect(projected[0]!.at(-1)!.y).toBeGreaterThan(projected[0]![0]!.y);
    }
  }
});

it('dominant gesture feature extraction preserves a measured late fall in the learner graph', () => {
  const points = curve(x => x <= .45 ? 4 * (1 - x / .45) : x <= .85 ? 4 * (x - .45) / .4 : 4 - .45 * (x - .85) / .15, 0, 101);
  const segments = freeze([points]);
  const before = JSON.stringify(shapeDisplay(segments, 0, 1.01));
  const shape = classifyPitchShape(segments);
  expect(shape).toMatchObject({ shape: 'DIP_RISE', reason: 'dominant_supported_gesture' });
  expect(classifyToneLikeness(shape, segments).tone).toBe('TONE_3');
  expect(JSON.stringify(shapeDisplay(segments, 0, 1.01))).toBe(before);
  expect(segments[0]!.at(-1)!.normalized_semitones).toBeCloseTo(3.55);
  expect(segments[0]![85]!.normalized_semitones).toBeCloseTo(4);
  expect(segments[0]).toHaveLength(101);
});

it('reproduces the latest physical fragments from their own raw timestamps, before any classification', () => {
  const analysis = freeze(clone(physical)), data = analysis.data;
  const units = pronunciationUnits(data), chunks = pronunciationChunks(data, units);
  const before = units.map(u => unitPitch(data, u, units));
  expect(before.map(p => p.segments.map(s => s.length))).toEqual([[14, 3, 4], [14, 8], [3], [15], [18]]);
  units.forEach((u, i) => {
    const raw = data.tone_graph!.raw.filter(p => u.start <= p.timestamp_seconds && p.timestamp_seconds < u.end);
    expect(times(before[i]!.segments)).toEqual(raw.filter(p => p.retained).map(p => p.timestamp_seconds));
    expect(before[i]!.segments.flat().every(p => u.members[0]!.pitch_projection!.frame_indices!.includes(
      raw.find(r => r.timestamp_seconds === p.timestamp_seconds)!.source_frame_index!))).toBe(true);
    unitShape(data, u, before[i]!.segments);
  });
  const maiRaw = data.tone_graph!.raw.filter(p => 1.2 <= p.timestamp_seconds && p.timestamp_seconds < 1.47);
  expect(maiRaw.filter(p => p.tracker_f0_hz)).toHaveLength(3);
  expect(maiRaw.filter(p => !p.tracker_f0_hz)).toHaveLength(24);
  for (const chunk of chunks) gradeChunkPitch(analysis, chunk, units);
  expect(units.map(u => unitPitch(data, u, units))).toEqual(before);
  expect(chunks.map(c => c.text)).toEqual(['我', '想', '买', '这个']);
  expect(chunkPitch(data, chunks[3]!, units).segments.map(s => s.length)).toEqual([15, 18]);
});
