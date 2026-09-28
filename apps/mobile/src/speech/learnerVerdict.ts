import type { ObservedContour } from '@/api/types';

export type LearnerVerdict = 'matches' | 'close' | 'different' | 'unclear';
// Consumes classifier evidence only. Recording-wide coverage and display geometry
// are intentionally absent: the classifier has already gated the retained region.
export function learnerVerdict(expected: number | null | undefined, observed?: Omit<ObservedContour, 'confidence'> & { confidence?: 'high' | 'moderate' | 'low' }): LearnerVerdict {
  if (!expected || ![1, 2, 3, 4].includes(expected) || !observed || !/^[1-4]-like$/.test(observed.classification ?? '')) return 'unclear';
  if (!['acoustic_shape_only', 'sustained_level_after_onset', 'short_coherent_fall', 'isolated_filtered_glitch', 'shallow_coherent_valley', 'coherent_short_gap'].includes(observed.reason ?? '')) return 'unclear';
  const f = observed.features ?? {};
  const certifiedGap = observed.reason === 'coherent_short_gap' && f.coherent_short_gap === 1 && f.gap_count === 1;
  if ((f.contaminated_fraction ?? 0) >= .15 || (f.tracker_instability_rejected ?? 0) > 0 ||
    ((f.discontinuous_gap_count ?? 0) > 0 && !certifiedGap)) return 'unclear';
  const agrees = observed.classification === `${expected}-like`;
  if (observed.confidence === 'low') return agrees ? 'close' : 'unclear';
  if (observed.confidence !== 'moderate' && observed.confidence !== 'high') return 'unclear';
  return agrees ? 'matches' : 'different';
}
export const toneGesture: Record<number, string> = {
  1: 'Pitch stayed level overall', 2: 'Pitch rose overall',
  3: 'Pitch dipped and recovered', 4: 'Pitch fell clearly',
};
