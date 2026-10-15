import { familyGeometry, quantile, type ShapePoint, type ShapeResult } from '@/speech/pitchShape';

export type ToneFamily = 'TONE_1' | 'TONE_2' | 'TONE_3' | 'TONE_4';
export type ToneLikeness = ToneFamily | 'UNCLEAR';
export const toneLikenessLabels: Record<ToneLikeness, string> = {
  TONE_1: 'Most like Tone 1', TONE_2: 'Most like Tone 2', TONE_3: 'Most like Tone 3',
  TONE_4: 'Most like Tone 4', UNCLEAR: 'Tone unclear',
};
export interface ToneLikenessResult {
  tone: ToneLikeness;
  decision: 'NUMBERED' | 'UNCLEAR' | 'UNAVAILABLE';
  // Explainable support, NOT probabilities. Never learner percentages.
  fits: Record<ToneFamily, number>;
  best: ToneFamily | null;
  runnerUp: ToneFamily | null;
  margin: number;
  reason: string;
  strength: 'full' | 'weak' | 'unavailable';
  variant: 'ordinary' | 'reduced_valley' | 'completed_shallow_valley';
  features: Record<string, number>;
  evidence: 'trustworthy' | 'unavailable';
  strengthBasis?: string;
  perturbations?: Record<string, ToneLikeness>;
}
export const TONE_MARGIN = .12;
export const NATURAL_FAMILY = {
  minimumSupport: .42,
  movementScale: .12,
  noiseMultiplier: 3,
  noiseRangeFloor: .04,
  levelDriftScale: .35,
  levelRangeScale: 1.2,
  levelWanderScale: 2,
  valleyRatioStart: .08,
  valleyRatioWidth: .17,
  lowTailFraction: .4,
  plateauRangeRatio: .5,
  familyConsensus: .7,
  fullDirection: 2,
  fullValleyLimb: 1.5,
} as const;
const clamp = (v: number) => Math.max(0, Math.min(1, v));
const families: ToneFamily[] = ['TONE_1', 'TONE_2', 'TONE_3', 'TONE_4'];
const median = (v: number[]) => quantile(v, .5);
const zeroFits = (): Record<ToneFamily, number> => ({ TONE_1: 0, TONE_2: 0, TONE_3: 0, TONE_4: 0 });

// No family receives a bonus from the canonical shape label. All four compete
// using the same retained geometry, direction, temporal support and local noise.
function support(shape: ShapeResult, segments: readonly (readonly ShapePoint[])[], regionScale = 1) {
  const primary = shape.features.subordinate_late_island ? segments.filter(s => s.length).slice(0, 1) : segments;
  const raw = primary.flat();
  const smooth = primary.flatMap(s => s.map((p, i) => ({ ...p, normalized_semitones:
    median(s.slice(Math.max(0, i - 1), i + 2).map(q => q.normalized_semitones)) })));
  const first = smooth[0]!.timestamp_seconds, last = smooth.at(-1)!.timestamp_seconds, extent = last - first;
  const time = (p: ShapePoint) => (p.timestamp_seconds - first) / extent;
  const values = smooth.map(p => p.normalized_semitones);
  const range = Math.max(...values) - Math.min(...values);
  const noise = quantile(raw.map((p, i) => Math.abs(p.normalized_semitones - values[i]!)), .75);
  const scale = Math.max(NATURAL_FAMILY.movementScale, noise * NATURAL_FAMILY.noiseMultiplier);
  const salience = (v: number) => Math.max(0, v) / (Math.max(0, v) + scale);
  // Short units get proportionally short endpoint regions, so a real short onset
  // is not swallowed by a fixed 40 ms median. Regions are varied below.
  const region = Math.min(.03, extent * .1) * regionScale;
  const start = median(smooth.filter(p => p.timestamp_seconds <= first + region + 1e-8).map(p => p.normalized_semitones));
  const end = median(smooth.filter(p => p.timestamp_seconds >= last - region - 1e-8).map(p => p.normalized_semitones));
  const byTime = new Map(smooth.map(p => [p.timestamp_seconds, p]));
  const steps = primary.flatMap(s => s.slice(1).flatMap((p, i) => {
    const a = byTime.get(s[i]!.timestamp_seconds)!;
    const b = byTime.get(p.timestamp_seconds)!;
    return p.timestamp_seconds - a.timestamp_seconds <= .025 + 1e-8 ? [{ a, b, d: b.normalized_semitones - a.normalized_semitones }] : [];
  }));
  const consistency = (direction: number, from = first, to = last) => {
    const selected = steps.filter(s => s.a.timestamp_seconds >= from - 1e-8 && s.b.timestamp_seconds <= to + 1e-8);
    return selected.reduce((sum, s) => sum + Math.max(0, direction * s.d), 0) /
      Math.max(1e-9, selected.reduce((sum, s) => sum + Math.abs(s.d), 0));
  };
  const minimum = Math.min(...values);
  const bottomTime = median(smooth.filter(p => p.normalized_semitones <= minimum + Math.min(.35, range * .1))
    .map(p => p.timestamp_seconds));
  const trough = { timestamp_seconds: bottomTime, normalized_semitones: minimum };
  const peak = smooth.filter(p => p.timestamp_seconds >= trough.timestamp_seconds)
    .reduce((a, b) => b.normalized_semitones > a.normalized_semitones ? b : a);
  const down = consistency(-1, first, trough.timestamp_seconds);
  const up = consistency(1, trough.timestamp_seconds, peak.timestamp_seconds);
  // Preserve a short coherent onset that a region median would suppress. This
  // is a measured landmark, not a bonus from a canonical valley decision.
  const onsetSupport = clamp((bottomTime - first) / .02) * clamp((down - .5) / .3);
  const shortOnset = clamp(1 - Math.max(0, bottomTime - first - .03) / .04);
  const onsetFall = Math.max(0, start - minimum) +
    Math.max(0, raw[0]!.normalized_semitones - start - 2 * noise) * onsetSupport * shortOnset;
  const fall = Math.max(0, start - minimum, onsetFall);
  const recovery = Math.max(0, peak.normalized_semitones - minimum);
  const position = time(trough), peakPosition = time(peak);
  const retreat = Math.max(0, peak.normalized_semitones - Math.min(...smooth.filter(p => p.timestamp_seconds >= peak.timestamp_seconds).map(p => p.normalized_semitones)));
  const limbRatio = Math.min(fall, recovery) / Math.max(1e-9, fall, recovery);
  // Time and relative excursion distinguish a supported valley from tiny onset
  // microprosody. Every penalty is continuous; no 1 st canonical contour gate.
  const interior = clamp((position - .06) / .09) * clamp((.9 - position) / .15);
  const limbTime = clamp((trough.timestamp_seconds - first) / .025) * clamp((peak.timestamp_seconds - trough.timestamp_seconds) / .04);
  const terminal = clamp(1 - Math.max(0, 1 - peakPosition - .25) * 4) *
    clamp(1 - Math.max(0, retreat / Math.max(recovery, scale) - .5) * 3);
  const lateRebound = clamp((position - .6) / .15) * clamp((.3 - recovery / Math.max(scale, fall)) / .15);
  const valley = (1 - lateRebound) * salience(Math.min(fall, recovery)) * Math.sqrt(down * up) *
    Math.sqrt(clamp((limbRatio - NATURAL_FAMILY.valleyRatioStart) / NATURAL_FAMILY.valleyRatioWidth)) * interior * limbTime * terminal;
  const tail = smooth.filter(p => time(p) >= 1 - NATURAL_FAMILY.lowTailFraction);
  const tailValues = tail.map(p => p.normalized_semitones);
  const tailRange = quantile(tailValues, .9) - quantile(tailValues, .1);
  const lowering = Math.max(0, start - median(tailValues));
  const plateau = clamp(1 - tailRange / Math.max(scale, lowering * NATURAL_FAMILY.plateauRangeRatio));
  const settled = smooth.find(p => p.normalized_semitones <= start - .8 * lowering);
  const earlyLowering = settled ? clamp((.75 - time(settled)) / .3) : 0;
  const reduced = (1 - lateRebound * (1 - plateau)) * salience(lowering) * plateau * earlyLowering * consistency(-1, first, tail[0]!.timestamp_seconds) *
    clamp(1 - Math.max(0, (range - lowering) / Math.max(scale, range) - .3));
  const dominantEnd = shape.features.dominant_excursion_st ? first + shape.features.gesture_end_position! * extent : last;
  const net = shape.features.dominant_excursion_st ? shape.features.net_st! : end - start;
  const upConsistency = consistency(1, first, dominantEnd), downConsistency = consistency(-1, first, dominantEnd);
  const durationConsistency = (direction: number) => {
    const active = steps.filter(s => s.b.timestamp_seconds <= dominantEnd + 1e-8 && Math.abs(s.d) > noise);
    return active.filter(s => s.d * direction > 0).reduce((sum, s) => sum + s.b.timestamp_seconds - s.a.timestamp_seconds, 0) /
      Math.max(1e-9, active.reduce((sum, s) => sum + s.b.timestamp_seconds - s.a.timestamp_seconds, 0));
  };
  const upSupport = .75 * upConsistency + .25 * durationConsistency(1);
  const downSupport = .75 * downConsistency + .25 * durationConsistency(-1);
  const fits = {
    TONE_1: Math.max(Math.exp(-Math.abs(net) / NATURAL_FAMILY.levelDriftScale) * Math.exp(-range / NATURAL_FAMILY.levelRangeScale),
      .95 * Math.exp(-range / NATURAL_FAMILY.levelWanderScale) * (1 - Math.abs(upSupport - downSupport))) *
      (1 - .6 * Math.max(valley, reduced)),
    TONE_2: salience(net) * upSupport ** 2 * (1 - .5 * valley),
    TONE_3: Math.max(valley, reduced),
    TONE_4: salience(-net) * downSupport ** 2 * (1 - .65 * reduced) * (1 - .5 * valley),
  };
  // Rapid alternating residuals cannot prove a level tone merely because the
  // excursion is small. This soft signal/noise term applies to every family.
  const clarity = 1 / (1 + (NATURAL_FAMILY.noiseMultiplier * noise / Math.max(NATURAL_FAMILY.noiseRangeFloor, range)) ** 2);
  for (const family of families) fits[family] *= clarity;
  return { fits, features: { ...shape.features, family_noise_st: noise, family_clarity: clarity, family_scale_st: scale,
    family_start_st: start, family_end_st: end, family_range_st: range, family_net_st: net,
    family_fall_st: fall, family_recovery_st: recovery, family_valley_position: position,
    family_peak_position: peakPosition, family_late_rebound: lateRebound, family_fall_consistency: down, family_rise_consistency: up,
    family_up_consistency: upConsistency, family_down_consistency: downConsistency,
    family_up_duration: durationConsistency(1), family_down_duration: durationConsistency(-1),
    family_valley_support: valley, family_reduced_support: reduced, family_tail_range_st: tailRange,
    family_lowering_st: lowering, family_early_lowering: earlyLowering, family_plateau: plateau, family_terminal_factor: terminal } };
}
function ranking(fits: Record<ToneFamily, number>) {
  const ordered = [...families].sort((a, b) => fits[b] - fits[a]);
  const best = ordered[0]!, runnerUp = ordered[1]!, margin = fits[best] - fits[runnerUp];
  return { best, runnerUp, margin, tone: fits[best] >= NATURAL_FAMILY.minimumSupport && margin >= TONE_MARGIN ? best : 'UNCLEAR' as ToneLikeness };
}

// Safety is decided before family scoring. Shape-threshold instability can be
// reconsidered, raw branches or deletion-sensitive support cannot.
export function classifyToneLikeness(shape: ShapeResult, segments: readonly (readonly ShapePoint[])[]): ToneLikenessResult {
  if (!shape.familySafe) return { tone: 'UNCLEAR', decision: 'UNAVAILABLE', fits: zeroFits(), best: null, runnerUp: null, margin: 0,
    reason: shape.familySafetyReason ?? shape.reason, strength: 'unavailable', variant: 'ordinary',
    features: { ...shape.features }, evidence: 'unavailable', strengthBasis: 'unavailable_measurements', perturbations: {} };
  const scored = support(shape, segments), ranked = ranking(scored.fits);
  const points = segments.flat();
  const variants: Record<string, readonly (readonly ShapePoint[])[]> = {
    first_point: segments.map(s => s.filter(p => p !== points[0])),
    last_point: segments.map(s => s.filter(p => p !== points.at(-1))),
    every_tenth: segments.map(s => s.filter(p => points.indexOf(p) % 10 !== 9)),
    timing_early: segments.map(s => s.map((p, i) => ({ ...p, timestamp_seconds: p.timestamp_seconds + (i % 2 ? -.002 : 0) }))),
    timing_late: segments.map(s => s.map((p, i) => ({ ...p, timestamp_seconds: p.timestamp_seconds + (i % 2 ? .002 : 0) }))),
  };
  const perturbations: Record<string, ToneLikeness> = {};
  let unstableSupport = false;
  for (const [name, variant] of Object.entries(variants)) {
    const geometry = familyGeometry(variant);
    if (!geometry.structurallyUsable) { unstableSupport = true; perturbations[name] = 'UNCLEAR'; }
    else perturbations[name] = ranking(support(geometry, variant).fits).tone;
  }
  for (const scale of [.67, 1.33]) perturbations[`region_${scale}`] = ranking(support(shape, segments, scale).fits).tone;
  let reason = ranked.tone === 'UNCLEAR' ? scored.features.family_clarity < .5 ? 'noise_dominated_geometry' :
    scored.fits[ranked.best] < NATURAL_FAMILY.minimumSupport ? 'contradictory_geometry' : 'close_candidates' : 'best_fit';
  if (unstableSupport) reason = 'unstable_measurement_support';
  else if (ranked.tone !== 'UNCLEAR' && Object.values(perturbations).filter(t => t === ranked.tone).length /
    Object.keys(perturbations).length < NATURAL_FAMILY.familyConsensus) reason = 'family_perturbation_sensitive';
  const tone = reason === 'best_fit' ? ranked.tone : 'UNCLEAR';
  const f = scored.features;
  const reduced = tone === 'TONE_3' && f.family_reduced_support > f.family_valley_support;
  const variant = reduced ? 'reduced_valley' : tone === 'TONE_3' && shape.features.completed_shallow_valley ? 'completed_shallow_valley' : 'ordinary';
  // Family stability uses consensus (at least 5/7 probes), not a second binary
  // canonical veto. Losing most of a short onset in one endpoint probe cannot
  // outweigh the complete measured contour. EVERY structural probe must pass.
  // Strength is downstream of family. The established full-gesture excursion
  // criteria are retained, including a supported dominant boundary gesture.
  const weak = tone === 'TONE_2' || tone === 'TONE_4' ? Math.abs(shape.features.net_st!) < NATURAL_FAMILY.fullDirection :
    tone === 'TONE_3' ? variant !== 'ordinary' || shape.features.fall_st! < NATURAL_FAMILY.fullValleyLimb || shape.features.recovery_st! < NATURAL_FAMILY.fullValleyLimb : false;
  return { ...ranked, tone, decision: unstableSupport ? 'UNAVAILABLE' : tone === 'UNCLEAR' ? 'UNCLEAR' : 'NUMBERED', fits: scored.fits, reason, variant, features: scored.features, perturbations,
    evidence: unstableSupport ? 'unavailable' : 'trustworthy',
    strength: tone === 'UNCLEAR' ? 'unavailable' : weak ? 'weak' : 'full',
    strengthBasis: tone === 'UNCLEAR' ? reason : reduced ? 'supported_lowering_and_low_tail' :
      weak ? 'limited_excursion' : tone === 'TONE_1' ? 'stable_level' : 'full_supported_excursion' };
}
