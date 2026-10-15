import type { PitchXLayout } from '@/components/PitchPlot';
import { quantile, type ShapePoint } from '@/speech/pitchShape';

// Display only. The timing span, not the first/last voiced sample, fills 0..1.
// Missing onset, internal intervals and tails remain empty; never stretch them away.
export function shapeDisplay(segments: readonly (readonly ShapePoint[])[], start: number, end: number,
  regions: readonly { label: string; start: number; end: number }[] = []) {
  if (!(end > start)) throw new Error('Shape display requires an accepted timing span');
  const values = segments.flat().map(p => p.normalized_semitones).filter(Number.isFinite);
  const center = (quantile(values, .1) + quantile(values, .9)) / 2;
  // Six semitones limits zoom: 0.2 st occupies at most 3.3% of plot height.
  // Robust center, but ALL retained extrema remain visible; no winsorizing/clipping.
  const radius = Math.max(3, ...values.map(v => Math.abs(v - center) + .5));
  const domain: [number, number] = [center - radius, center + radius];
  const position = (time: number) => (time - start) / (end - start);
  const layout: PitchXLayout = {
    extent: 1, pauses: [],
    segments: segments.map(s => s.map(p => ({ ...p, position: position(p.timestamp_seconds) }))),
    regions: regions.map((r, index) => ({ index, label: r.label, start: position(r.start), end: position(r.end) })),
  };
  return { domain, layout };
}
