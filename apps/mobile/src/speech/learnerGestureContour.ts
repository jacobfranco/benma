import type { DisplayContour, ObservedContour } from '@/api/types';

export const LEARNER_GESTURE_METHOD = 'classifier-bin-gesture-v1';

// Certification is backend acoustic evidence, never a guess from gap duration or
// expected tone. Defensively check geometry too, including stale/malformed data.
export function certifiedShortGap(display: DisplayContour, observed?: ObservedContour): boolean {
  const f = observed?.features ?? {};
  const segments = display.segments ?? [];
  if (observed?.reason !== 'coherent_short_gap' || observed.confidence !== 'low' ||
    !['2-like', '4-like'].includes(observed.classification ?? '') ||
    f.coherent_short_gap !== 1 || f.gap_count !== 1 || f.discontinuous_gap_count !== 1 ||
    f.contaminated_fraction !== 0 || f.tracker_instability_rejected !== 0 || f.large_jump_count !== 0 ||
    !(f.longest_gap_seconds! > 0 && f.longest_gap_seconds! <= .0401) || segments.length !== 2) return false;
  const [left, right] = segments;
  const a = left?.at(-1), b = right?.[0];
  if (!a || !b) return false;
  const gap = b.timestamp_seconds-a.timestamp_seconds;
  const bins = Array.from({ length: 5 }, (_, i) => f[`bin_${i+1}_st`]);
  if (!bins.every(Number.isFinite)) return false;
  const delta = bins[4]!-bins[0]!, direction = Math.sign(delta);
  return gap > 0 && gap <= .0401 && Math.abs(delta) >= 2 &&
    (b.normalized_semitones-a.normalized_semitones)*direction > 0 &&
    bins.slice(1).every((value, i) => (value!-bins[i]!)*direction >= -.2501) &&
    segments.every(s => s.length >= 2 &&
      (s.at(-1)!.normalized_semitones-s[0]!.normalized_semitones)*direction >= 0);
}

// Display-only projection of the exact medians already computed by the grader.
// Times represent bin centers, not individual F0 samples. Straight interpolation
// preserves amplitude and introduces no overshoot or label-dependent shaping.
// No target, spelling, expected shape, or provider assessment is accepted here.
export function learnerGestureContour(display: DisplayContour | null | undefined, observed?: ObservedContour) {
  if (!display || !observed) return display;
  const f = observed.features ?? {};
  if (f.gap_count !== 0 && !certifiedShortGap(display, observed)) return display;
  if ((display.segments?.length ?? 0) > 1 && !certifiedShortGap(display, observed)) return display;
  const prefix = observed.reason === 'sustained_level_after_onset' ? 'core_bin' : 'bin';
  const points = Array.from({ length: 5 }, (_, i) => ({
    timestamp_seconds: f[`${prefix}_${i+1}_seconds`]!,
    normalized_semitones: f[`${prefix}_${i+1}_st`]!,
  }));
  if (!points.every((p, i) => Number.isFinite(p.timestamp_seconds) && Number.isFinite(p.normalized_semitones) &&
    (i === 0 || p.timestamp_seconds > points[i-1]!.timestamp_seconds))) return display;
  return { ...display, method: LEARNER_GESTURE_METHOD, segments: [points] };
}
