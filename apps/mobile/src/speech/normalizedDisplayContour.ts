import type { DisplayContour, ObservedContour } from '@/api/types';
import { certifiedShortGap, LEARNER_GESTURE_METHOD } from '@/speech/learnerGestureContour';

// Presentation only. No measured frame or timestamp is written back. Fixed
// semitone scale preserves amplitude; wider outliers stay visible, without clipping.
export function normalizedDisplayContour(display: DisplayContour | null | undefined, observed?: ObservedContour) {
  if (!display) return display;
  const f = observed?.features ?? {};
  const coherent = /^[1-4]-like$/.test(observed?.classification ?? '') &&
    ['moderate', 'high'].includes(observed?.confidence ?? '') &&
    f.discontinuous_gap_count === 0 && f.contaminated_fraction === 0 &&
    f.tracker_instability_rejected === 0 && (f.large_jump_count ?? 0) === 0;
  const segments = (display.segments ?? []).map(segment => segment.map((p, i) => {
    if (display.method === LEARNER_GESTURE_METHOD) return { ...p };
    const previous = segment[i-1], next = segment[i+1];
    // Small three-point low-pass; keep endpoints and meaningful extrema exact.
    const extremum = previous && next && (p.normalized_semitones - previous.normalized_semitones) *
      (next.normalized_semitones - p.normalized_semitones) <= 0 &&
      Math.min(Math.abs(p.normalized_semitones - previous.normalized_semitones),
        Math.abs(next.normalized_semitones - p.normalized_semitones)) > .5;
    return { ...p, normalized_semitones: previous && next && !extremum ?
      .2*previous.normalized_semitones + .6*p.normalized_semitones + .2*next.normalized_semitones : p.normalized_semitones };
  })).filter(s => s.length);
  const values = segments.flat().map(p => p.normalized_semitones).sort((a,b) => a-b);
  const center = values.length ? (values[Math.floor((values.length-1)/2)]! + values[Math.floor(values.length/2)]!)/2 : 0;
  const merged: typeof segments = [];
  for (const segment of segments) {
    const previous = merged.at(-1), a = previous?.at(-1), b = segment[0]!;
    const gap = a ? b.timestamp_seconds-a.timestamp_seconds : 0;
    // Joining draws a straight display interpolation, never invented measured frames.
    if (a && ((coherent && gap > 0 && gap <= .09 && Math.abs(b.normalized_semitones-a.normalized_semitones) <= 1.5) ||
      certifiedShortGap(display, observed))) previous!.push(...segment);
    else merged.push(segment);
  }
  const extent = Math.max(4, ...values.map(v => Math.abs(v-center)));
  return { ...display, segments: merged.map(s => s.map(p => ({ ...p, normalized_semitones: p.normalized_semitones-center }))),
    minimum_semitones: -extent, maximum_semitones: extent };
}
