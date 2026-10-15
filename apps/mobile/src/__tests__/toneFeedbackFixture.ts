import type { PerceivedSpeechAnalysis } from '@/api/types';
import type { ShapePoint } from '@/speech/pitchShape';

export const freshToneAnalysis = require('./fixtures/toneFeedbackPhysical.json') as PerceivedSpeechAnalysis;
export const copy = <T,>(value: T): T => JSON.parse(JSON.stringify(value));
export const line = (fn: (x: number) => number, n = 51, start = 0): ShapePoint[] => Array.from({ length: n }, (_, i) =>
  ({ timestamp_seconds: start + i * .01, normalized_semitones: fn(i / (n - 1)) }));
export const valley = (fall: number, recovery: number) => line(x => x < .5 ? fall * (1 - 2 * x) : recovery * (2 * x - 1));
// Counterfactual numeric controls; never attributed to the physical take.
export function replacePitch(analysis: PerceivedSpeechAnalysis, index: number, fn?: (x: number) => number) {
  const s = analysis.data.syllables[index]!;
  const start = s.start_seconds!, end = s.end_seconds!;
  const graph = analysis.data.tone_graph!;
  graph.raw = graph.raw.filter(p => p.timestamp_seconds < start || p.timestamp_seconds >= end);
  graph.filtered.segments = (graph.filtered.segments ?? []).map(segment => segment.filter(p => p.timestamp_seconds < start || p.timestamp_seconds >= end)).filter(s => s.length);
  if (fn) graph.filtered.segments.push(line(fn, Math.floor((end - start) / .01) - 1, start + .01));
  graph.filtered.segments.sort((a, b) => a[0]!.timestamp_seconds - b[0]!.timestamp_seconds);
}

// Clean synthetic observations, separate from the immutable physical recording.
export const gestureKnots = {
  textbook: [[0, 4.5], [.4, 0], [1, 4.5]],
  lateFall: [[0, 4.5], [.4, 0], [.8, 4.5], [1, 3.8]],
  wobble: [[0, 4.5], [.4, 0], [.8, 4.5], [.9, 3.8], [1, 4]],
  rise: [[0, 0], [.8, 4.5], [1, 3.8]],
  fall: [[0, 4.5], [.8, 0], [1, .7]],
  fallRebound: [[0, 4.5], [.76, 0], [1, .7]],
  competing: [[0, 0], [.8, 2.2], [1, .2]],
  competingValley: [[0, 4.5], [.35, 0], [.72, 4.5], [1, .4]],
} satisfies Record<string, [number, number][]>;
export const piecewise = (knots: [number, number][]) => (x: number) => {
  const j = knots.findIndex(k => k[0] >= x);
  const [b, yb] = knots[Math.max(0, j)]!, [a, ya] = knots[Math.max(0, j - 1)]!;
  return a === b ? yb : ya + (yb - ya) * (x - a) / (b - a);
};
export const dominantCases = [
  ['textbook', 'DIP_RISE', 'TONE_3'], ['lateFall', 'DIP_RISE', 'TONE_3'],
  ['wobble', 'DIP_RISE', 'TONE_3'], ['rise', 'RISING', 'TONE_2'], ['fall', 'FALLING', 'TONE_4'], ['fallRebound', 'FALLING', 'TONE_4'],
] as const;
