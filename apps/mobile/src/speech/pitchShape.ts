// Geometry of retained measurements. No text, lexical tones, eligibility, Hz,
// display coordinates or target enters this model. Saved diagnostics stay intact.
export type PitchShape = 'LEVEL' | 'RISING' | 'FALLING' | 'DIP_RISE' | 'UNCLEAR';
export interface ShapePoint { timestamp_seconds: number; normalized_semitones: number }
export interface ShapeResult {
  shape: PitchShape;
  reason: string;
  features: Record<string, number>;
  perturbations: Record<string, PitchShape>;
  // Numbered-family ambiguity is distinct from structurally unusable evidence.
  structurallyUsable?: boolean;
  // Numbered-family scoring checks stability in family space. A canonical shape
  // threshold crossing is not a measurement failure. Neutral keeps its existing
  // stricter structurallyUsable contract.
  familySafe?: boolean;
  familySafetyReason?: string;
}
export const shapeLabels: Record<PitchShape, string> = {
  LEVEL: 'Level', RISING: 'Rising', FALLING: 'Falling', DIP_RISE: 'Dip and rise', UNCLEAR: 'Shape unclear',
};
export function quantile(values: readonly number[], fraction: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return 0;
  const at = (sorted.length - 1) * fraction, lo = Math.floor(at), hi = Math.ceil(at);
  return sorted[lo]! + (sorted[hi]! - sorted[lo]!) * (at - lo);
}
const median = (values: number[]) => quantile(values, .5);
const result = (shape: PitchShape = 'UNCLEAR', reason = 'insufficient_support', features: Record<string, number> = {}): ShapeResult =>
  ({ shape, reason, features, perturbations: {} });

export const DOMINANT_GESTURE = {
  boundaryPosition: .72,
  maxCounterRatio: .25,
  minimumExcursion: 1.5,
  minimumSupportSeconds: .12,
  directionalConsistency: .8,
} as const;

export const COMPLETED_SHALLOW_VALLEY = {
  minimumFall: .2,
  minimumRecovery: 1,
  minimumFallRecoveryRatio: .15,
  minimumFallSeconds: .02,
  minimumRecoverySeconds: .04,
  minimumPrimarySeconds: .1,
  minimumValleyPosition: .1,
  maximumValleyPosition: .6,
  maximumTailFraction: .25,
  maximumRetreatRatio: .5,
  consistency: .8,
} as const;

export const SUBORDINATE_LATE_ISLAND = {
  minimumSupportFraction: .75,
  maximumFrames: 4,
  maximumSeconds: .04,
  minimumPosition: .75,
  maximumGapSeconds: .05,
  maximumJump: 3,
  maximumExcursion: .75,
} as const;

// A classification summary only: the caller and graph retain both islands.
// This exception cannot bridge a missing valley or a repeated/large branch.
function subordinateIsland(segments: readonly (readonly ShapePoint[])[], regionSeconds: number): ShapeResult | null {
  const islands = segments.filter(s => s.length);
  if (islands.length !== 2) return null;
  const [main, tail] = islands as [readonly ShapePoint[], readonly ShapePoint[]];
  const first = main[0]!, end = main.at(-1)!, next = tail[0]!, last = tail.at(-1)!;
  const extent = last.timestamp_seconds - first.timestamp_seconds;
  const fraction = main.length / (main.length + tail.length);
  const jump = Math.abs(next.normalized_semitones - end.normalized_semitones);
  const tailRange = Math.max(...tail.map(p => p.normalized_semitones)) - Math.min(...tail.map(p => p.normalized_semitones));
  const limits = SUBORDINATE_LATE_ISLAND;
  if (fraction < limits.minimumSupportFraction || tail.length > limits.maximumFrames ||
      last.timestamp_seconds - next.timestamp_seconds > limits.maximumSeconds + 1e-8 ||
      (next.timestamp_seconds - first.timestamp_seconds) / extent < limits.minimumPosition ||
      next.timestamp_seconds - end.timestamp_seconds > limits.maximumGapSeconds + 1e-8 ||
      jump > limits.maximumJump || tailRange > limits.maximumExcursion ||
      islands.some(s => s.slice(1).some((p, i) => p.timestamp_seconds - s[i]!.timestamp_seconds > .025 + 1e-8))) return null;
  const primary = geometry([main], regionSeconds, false);
  if (!primary.structurallyUsable || primary.shape === 'UNCLEAR' || tailRange > primary.features.excursion_st! * .25) return null;
  return { ...primary, reason: 'dominant_supported_island', features: { ...primary.features,
    subordinate_late_island: 1, primary_support_fraction: fraction, secondary_support_seconds: tail.length * .01,
    secondary_excursion_st: tailRange, inter_island_jump_st: jump,
    full_track_support_seconds: (main.length + tail.length) * .01, full_track_extent_seconds: extent,
    full_track_end_st: last.normalized_semitones } };
}

function geometry(segments: readonly (readonly ShapePoint[])[], regionSeconds = .03, allowExtensions = true): ShapeResult {
  const points = segments.flat();
  if (points.length < 8 || points.some(p => !Number.isFinite(p.timestamp_seconds) || !Number.isFinite(p.normalized_semitones))) return result();
  const first = points[0]!.timestamp_seconds, last = points.at(-1)!.timestamp_seconds, extent = last - first;
  if (extent < .07 - 1e-8) return result();
  const intervals = points.slice(1).map((p, i) => p.timestamp_seconds - points[i]!.timestamp_seconds);
  // The retained track is sampled every 10 ms. A thinning check retains the same
  // source clock, and never fills missing time or joins original segments.
  if (intervals.some(dt => dt <= 0)) return result('UNCLEAR', 'invalid_order');
  if (Math.max(...intervals) > .09 + 1e-8 || points.length * .01 / (extent + .01) < .75) return result('UNCLEAR', 'missing_critical_support');
  const contradictory = points.slice(1).some((p, i) => intervals[i]! > .025 + 1e-8 &&
    Math.abs(p.normalized_semitones - points[i]!.normalized_semitones) > 1.5);
  if (contradictory) return (allowExtensions && subordinateIsland(segments, regionSeconds)) || result('UNCLEAR', 'contradictory_fragments');
  if (points.slice(1).some((p, i) => Math.abs(p.normalized_semitones - points[i]!.normalized_semitones) > 6)) return result('UNCLEAR', 'discontinuous_measurements');
  // A short, within-segment median removes isolated wobble from the summary;
  // the graph still renders every original point, without this summarization.
  const smoothSegments = segments.map(s => s.map((p, i) => ({ ...p,
    normalized_semitones: median(s.slice(Math.max(0, i - 1), i + 2).map(q => q.normalized_semitones)),
  })));
  const smooth = smoothSegments.flat();
  const start = median(points.filter(p => p.timestamp_seconds <= first + regionSeconds + 1e-8).map(p => p.normalized_semitones));
  const end = median(points.filter(p => p.timestamp_seconds >= last - regionSeconds - 1e-8).map(p => p.normalized_semitones));
  const low = Math.min(...smooth.map(p => p.normalized_semitones)), high = Math.max(...smooth.map(p => p.normalized_semitones));
  const minimumTime = median(smooth.filter(p => p.normalized_semitones <= low + .35).map(p => p.timestamp_seconds));
  const minimumPosition = (minimumTime - first) / extent;
  const steps = smoothSegments.flatMap(s => s.slice(1).flatMap((p, i) => {
    const previous = s[i]!;
    return p.timestamp_seconds - previous.timestamp_seconds <= .025 + 1e-8
      ? [{ start: previous.timestamp_seconds, end: p.timestamp_seconds, delta: p.normalized_semitones - previous.normalized_semitones }] : [];
  }));
  const consistency = (sign: number, from: number, to: number) => {
    const moves = steps.filter(p => p.start >= from && p.end <= to).map(p => p.delta);
    return moves.reduce((sum, v) => sum + Math.max(0, sign * v), 0) / Math.max(1e-9, moves.reduce((sum, v) => sum + Math.abs(v), 0));
  };
  // Summarize a supported primary gesture ending near the boundary. All points
  // have already passed the full-track gates above; none are trimmed or hidden.
  // The entire tail range bounds a counter-gesture, including a second wobble.
  const peak = smooth.filter(p => p.timestamp_seconds >= minimumTime)
    .reduce((best, p) => p.normalized_semitones > best.normalized_semitones ? p : best);
  const trough = smooth.reduce((best, p) => p.normalized_semitones < best.normalized_semitones ? p : best);
  let gestureEnd = end, gestureEndTime = last, counter = 0, dominant = 0;
  for (const [pivot, direction] of [[peak, 1], [trough, -1]] as const) {
    const position = (pivot.timestamp_seconds - first) / extent;
    const tail = smooth.filter(p => p.timestamp_seconds >= pivot.timestamp_seconds).map(p => p.normalized_semitones);
    const opposing = Math.max(...tail) - Math.min(...tail);
    const primary = direction === 1 ? peak.normalized_semitones - low : start - low;
    const isValley = direction === 1 && start - low >= 1 && minimumTime < pivot.timestamp_seconds;
    const coherent = isValley
      ? consistency(-1, first, minimumTime) >= .7 && consistency(1, minimumTime, pivot.timestamp_seconds) >= .7
      : consistency(direction, first, pivot.timestamp_seconds) >= DOMINANT_GESTURE.directionalConsistency;
    if (position >= DOMINANT_GESTURE.boundaryPosition && position < 1 &&
        pivot.timestamp_seconds - first >= DOMINANT_GESTURE.minimumSupportSeconds &&
        primary >= DOMINANT_GESTURE.minimumExcursion && opposing > 0 &&
        opposing / primary <= DOMINANT_GESTURE.maxCounterRatio && coherent) {
      gestureEnd = pivot.normalized_semitones;
      gestureEndTime = pivot.timestamp_seconds;
      counter = opposing;
      dominant = primary;
      break;
    }
  }
  const fall = start - low, recovery = gestureEnd - low;
  const features = { start_st: start, end_st: end, minimum_st: low, excursion_st: high - low,
    fall_st: fall, recovery_st: recovery, minimum_position: minimumPosition, net_st: gestureEnd - start,
    measured_net_st: end - start, dominant_excursion_st: dominant, counter_excursion_st: counter,
    gesture_end_position: (gestureEndTime - first) / extent,
    fall_consistency: consistency(-1, first, minimumTime), rise_consistency: consistency(1, minimumTime, gestureEndTime),
    support_seconds: points.length * .01, selected_extent_seconds: extent };
  let shape: PitchShape = 'UNCLEAR';
  // An internal valley precedes the net-trend rule. A very small rebound after
  // a dominant fall does not override the dominant direction (and vice versa).
  if (minimumPosition >= .1 && minimumPosition <= .9 && fall >= 1 && recovery >= 1 &&
      Math.min(fall, recovery) / Math.max(fall, recovery) >= .25 &&
      features.fall_consistency >= .7 && features.rise_consistency >= .7) shape = 'DIP_RISE';
  else if (high - low <= 1.5 && Math.abs(end - start) <= 1) shape = 'LEVEL';
  else if (gestureEnd - start >= 1.5 && (fall < 1 || fall < recovery * .25) && consistency(1, first, gestureEndTime) >= .75) shape = 'RISING';
  else if (start - gestureEnd >= 1.5 && (recovery < 1 || recovery < fall * .25) && consistency(-1, first, gestureEndTime) >= .75) shape = 'FALLING';
  // A short onset can be suppressed by the 20–40 ms start-region median. Use
  // local landmarks with the same interior median, retaining endpoint values.
  // Require a completed recovery BEFORE the terminal retreat; no fixed suffix
  // is discarded. Noise and the entire terminal range still bound the claim.
  if (allowExtensions && (shape === 'UNCLEAR' || shape === 'LEVEL') && segments.filter(s => s.length).length === 1) {
    const local = smooth.map((p, i) => i === 0 || i === smooth.length - 1 ? points[i]! : p);
    const bottom = local.reduce((best, p) => p.normalized_semitones < best.normalized_semitones ? p : best);
    const top = local.filter(p => p.timestamp_seconds > bottom.timestamp_seconds)
      .reduce<ShapePoint | null>((best, p) => !best || p.normalized_semitones >= best.normalized_semitones ? p : best, null);
    if (top) {
      const limits = COMPLETED_SHALLOW_VALLEY;
      const localFall = local[0]!.normalized_semitones - bottom.normalized_semitones;
      const localRecovery = top.normalized_semitones - bottom.normalized_semitones;
      const tail = local.filter(p => p.timestamp_seconds > top.timestamp_seconds);
      const retreat = top.normalized_semitones - Math.min(top.normalized_semitones, ...tail.map(p => p.normalized_semitones));
      const noise = quantile(points.map((p, i) => Math.abs(p.normalized_semitones - smooth[i]!.normalized_semitones)), .75);
      const coherent = (from: number, to: number, sign: number) => {
        const steps = local.slice(1).flatMap((p, i) => local[i]!.timestamp_seconds >= from && p.timestamp_seconds <= to
          ? [p.normalized_semitones - local[i]!.normalized_semitones] : []);
        return steps.reduce((sum, v) => sum + Math.max(0, sign * v), 0) /
          Math.max(1e-9, steps.reduce((sum, v) => sum + Math.abs(v), 0));
      };
      const down = coherent(first, bottom.timestamp_seconds, -1), up = coherent(bottom.timestamp_seconds, top.timestamp_seconds, 1);
      if (localFall >= Math.max(limits.minimumFall, 2 * noise) && localFall < 1.5 &&
          localRecovery >= Math.max(limits.minimumRecovery, 3 * noise) &&
          localFall / localRecovery >= limits.minimumFallRecoveryRatio &&
          bottom.timestamp_seconds - first >= limits.minimumFallSeconds - 1e-8 &&
          (bottom.timestamp_seconds - first) / extent >= limits.minimumValleyPosition &&
          (bottom.timestamp_seconds - first) / extent <= limits.maximumValleyPosition &&
          top.timestamp_seconds - bottom.timestamp_seconds >= limits.minimumRecoverySeconds - 1e-8 &&
          top.timestamp_seconds - first >= limits.minimumPrimarySeconds - 1e-8 &&
          (top.timestamp_seconds - first) / extent >= DOMINANT_GESTURE.boundaryPosition &&
          tail.length > 0 && tail.length / points.length <= limits.maximumTailFraction &&
          (last - top.timestamp_seconds) / extent <= limits.maximumTailFraction &&
          retreat > 0 && retreat / localRecovery <= limits.maximumRetreatRatio &&
          down >= limits.consistency && up >= limits.consistency) {
        return { ...result('DIP_RISE', 'completed_shallow_valley', { ...features,
          completed_shallow_valley: 1, local_fall_st: localFall, local_recovery_st: localRecovery,
          local_fall_consistency: down, local_rise_consistency: up, local_noise_st: noise,
          terminal_retreat_st: retreat, terminal_support_fraction: tail.length / points.length,
          local_valley_position: (bottom.timestamp_seconds - first) / extent,
          local_recovery_position: (top.timestamp_seconds - first) / extent }), structurallyUsable: true };
      }
    }
  }
  return { ...result(shape, shape === 'UNCLEAR' ? 'ambiguous_geometry' : dominant ? 'dominant_supported_gesture' : 'retained_geometry', features), structurallyUsable: true };
}

export function classifyPitchShape(segments: readonly (readonly ShapePoint[])[], flaggedTimestamps: readonly number[] = [],
  rawDiscontinuity = flaggedTimestamps.length > 0): ShapeResult {
  // New exceptions never use retained geometry to dismiss raw corruption flags.
  const rawFlagged = rawDiscontinuity || flaggedTimestamps.length > 0;
  const allowExtensions = !rawFlagged;
  const base = geometry(segments, .03, allowExtensions);
  if (!base.structurallyUsable) return { ...base, familySafe: false, familySafetyReason: base.reason };
  const points = segments.flat();
  const removals = {
    first_point: [points[0]!.timestamp_seconds], last_point: [points.at(-1)!.timestamp_seconds],
    every_tenth: points.filter((_, i) => i % 10 === 9).map(p => p.timestamp_seconds), flagged_discontinuities: flaggedTimestamps,
  };
  const perturbations: Record<string, PitchShape> = {
    region_20ms: geometry(segments, .02, allowExtensions).shape, region_40ms: geometry(segments, .04, allowExtensions).shape,
  };
  let structurallyUsable = !rawFlagged;
  for (const [name, removed] of Object.entries(removals)) {
    const variant = geometry(segments.map(s => s.filter(p => !removed.includes(p.timestamp_seconds))), .03, allowExtensions);
    perturbations[name] = variant.shape;
    structurallyUsable = structurallyUsable && !!variant.structurallyUsable;
  }
  const safety = { familySafe: structurallyUsable, familySafetyReason: rawFlagged
    ? 'raw_tracker_discontinuity' : structurallyUsable ? 'supported_measurements' : 'unstable_measurement_support' };
  // Neutral may use ambiguous but structurally supported geometry. It must not
  // bypass a deletion-sensitive numbered result or a raw tracker branch flag.
  if (base.shape === 'UNCLEAR') return { ...base, perturbations, structurallyUsable, ...safety };
  return Object.values(perturbations).every(shape => shape === base.shape)
    ? { ...base, perturbations, structurallyUsable, ...safety }
    : { ...base, shape: 'UNCLEAR', reason: 'perturbation_sensitive', perturbations, structurallyUsable: false, ...safety };
}

// Interpretation-only summaries for the family perturbation checks. This never
// alters source points, projection, timing ownership or the displayed contour.
export function familyGeometry(segments: readonly (readonly ShapePoint[])[], regionSeconds = .03): ShapeResult {
  return geometry(segments, regionSeconds);
}
