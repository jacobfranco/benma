// Historical contour helpers retained for offline regression/acceptance utilities.
// Tone Graph V2 does not import classifier-derived geometry.
import type { PerceivedSyllable } from '@/api/types';
import { learnerGestureContour } from '@/speech/learnerGestureContour';

export const lexicalShapes: Record<number, number[]> = { 1: [1, 1], 2: [.5, 1], 3: [.25, 0, .75], 4: [1, 0] };
type SyllableFields = Pick<PerceivedSyllable, 'index' | 'characters' | 'pinyin' | 'lexical_tone' |
  'expected_tone' | 'display_contour' | 'observed_contour' | 'start_seconds' | 'end_seconds'>;
export type ComparisonSyllable = Omit<SyllableFields, 'display_contour' | 'observed_contour'> & {
  expected_surface_tone?: number | null | undefined;
  expected_surface_shape?: PerceivedSyllable['expected_tone'] | undefined;
  display_contour?: SyllableFields['display_contour'] | undefined;
  observed_contour?: SyllableFields['observed_contour'] | undefined;
};

// Use only the classifier's selected evidence, never infer a nucleus from spelling.
// The complete display contour and original timestamps remain available in More detail.
export function primaryMineContour(syllable: Pick<ComparisonSyllable, 'display_contour' | 'observed_contour'>) {
  const display = syllable.display_contour;
  const observed = syllable.observed_contour;
  const gesture = learnerGestureContour(display, observed);
  if (gesture !== display) return gesture;
  const selected = observed?.features?.evidence_region_selected === 1;
  if (!display || (!selected && (observed?.reason !== 'sustained_level_after_onset' || observed.classification !== '1-like'))) return display;
  const start = selected ? observed?.features?.evidence_start_seconds : observed?.features?.first_reliable_core_seconds;
  const end = selected ? observed?.features?.evidence_end_seconds : observed?.features?.last_reliable_core_seconds;
  if (!Number.isFinite(start) || !Number.isFinite(end) || start! > end!) return display;
  // Features are rounded to four decimals; include the exact measured boundary.
  const segments = (display.segments ?? []).map(region => region.filter(p =>
    p.timestamp_seconds >= start! - .000051 && (selected ? p.timestamp_seconds < end! - .000051 : p.timestamp_seconds <= end! + .000051))).filter(region => region.length);
  if (!segments.length) return display;
  const values = segments.flat().map(p => p.normalized_semitones);
  return { ...display, segments, minimum_semitones: Math.min(-3, ...values.map(v => v - 1)),
    maximum_semitones: Math.max(3, ...values.map(v => v + 1)) };
}

export function unclearContourLabel(reason?: string): string {
  switch (reason) {
    case 'insufficient_voicing':
    case 'fragmented_voicing': return 'Not enough clear voice';
    case 'tracker_instability': return 'Pitch tracking was unstable';
    case 'noisy_contour': return 'Pitch was uneven';
    case 'low_frequency_contamination': return 'Background sound interfered';
    case 'ambiguous_shape': return 'Shape was ambiguous';
    case 'synthetic_timing': return 'Timing unavailable';
    default: return 'Could not read the pitch';
  }
}
