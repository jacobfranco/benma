import type { PerceivedSyllable } from '@/api/types';
import type { ToneFamily, ToneLikenessResult } from '@/speech/toneLikeness';

export type LearnerAgreement = 'STRONG_MATCH' | 'PARTIAL_OR_WEAK' | 'CLEAR_DIFFERENCE' | 'UNAVAILABLE';
export interface LearnerPitchGrade {
  agreement: LearnerAgreement;
  reason: string;
  message: string;
  coaching: string | null;
}
export const pitchGradePresentation = {
  STRONG_MATCH: { color: 'green', ink: '#237047', background: '#eaf5ee', symbol: '✓', label: 'Pitch acceptable' },
  PARTIAL_OR_WEAK: { color: 'amber', ink: '#886000', background: '#fff5d9', symbol: '≈', label: 'Pitch may be off' },
  CLEAR_DIFFERENCE: { color: 'red', ink: '#a32332', background: '#fcecef', symbol: '≠', label: 'Pitch differs' },
  UNAVAILABLE: { color: 'gray', ink: '#64716e', background: '#eff2f1', symbol: '—', label: 'Pitch unavailable' },
} as const;
export interface PitchExpectation {
  tone: number | null;
  acceptableTones?: readonly number[];
  basis: 'resolved_surface' | 'acceptable_alternatives' | 'lexical_family' | 'neutral' | 'unresolved';
  label: string;
  coaching: string | null;
  reason: string;
}

// Context determines the expectation, never the measured family. Keep the saved
// surface decision intact: lexical fallback is a learner-grade basis only.
export function pitchExpectation(s: PerceivedSyllable, context: readonly PerceivedSyllable[] = []): PitchExpectation {
  if (s.reading_source === 'unresolved' || !s.pinyin) return {
    tone: null, basis: 'unresolved', label: 'Reading unresolved', coaching: null, reason: 'reading_unresolved',
  };
  const tone = s.expected_surface_tone ?? null;
  const labels: Record<number, string> = { 0: 'Neutral · flexible pitch', 1: 'Tone 1 — level',
    2: 'Tone 2 — rising', 3: 'Tone 3 — low or dipping; a full rise is optional', 4: 'Tone 4 — falling' };
  if (tone !== null && tone in labels) return { tone, basis: tone === 0 ? 'neutral' : 'resolved_surface',
    label: labels[tone]!, coaching: null, reason: s.surface_rule ?? 'saved_surface_tone' };
  const next = context.find(n => n.index === s.index + 1 && n.character_start === s.character_end);
  if (s.lexical_tone === 3 && s.surface_rule === 'prosodic_grouping_unresolved' &&
    next?.lexical_tone === 3 && next.pinyin && next.reading_source !== 'unresolved') return {
    tone: 3, acceptableTones: [3, 2], basis: 'lexical_family', label: 'Tone 3 family · Tone 2 sandhi also possible',
    coaching: 'Before another Tone 3, a low or dipping tone or a sandhi rise can fit the grouping.',
    reason: 'unresolved_third_tone_chain',
  };
  if (tone === null && s.lexical_tone != null && [1, 2, 3, 4].includes(s.lexical_tone)) return {
    tone: s.lexical_tone, basis: 'lexical_family', label: `Tone ${s.lexical_tone} family`,
    coaching: 'Connected-speech realization may vary here.', reason: 'lexical_family_fallback',
  };
  return { tone: null, basis: 'unresolved', label: 'Context unresolved', coaching: null,
    reason: s.surface_rule ?? 'context_unresolved' };
}
// Keep these agreement keys stable for existing consumers; presentation carries
// the learner meaning. Acoustic support is heuristic, never a probability.
export function pitchGrade(agreement: LearnerAgreement, reason: string, message: string,
  coaching: string | null = null): LearnerPitchGrade {
  return { agreement, reason, message, coaching };
}
export const CONSERVATIVE_RED = {
  support: .9, acceptableSupportMax: .2, acceptableMargin: .7, runnerUpMargin: .6,
  clarity: .9, minimumProbes: 7, consensus: 1,
} as const;
// Recorded weak mismatches end at .542 support; meaningful controls start at
// .711 with >=.488 runner-up separation. A score leader alone is not a concern.
// These are learner-policy safeguards, not acoustic classification thresholds.
export const MINIMUM_LEARNER_CONCERN = {
  support: .65, acceptableSupportMax: .4, acceptableMargin: .5, runnerUpMargin: .45,
  clarity: .9, minimumProbes: 7, consensus: 6 / 7,
} as const;
// A compatible family needs no extra support/excursion threshold. Two unstable
// probes are a meaningful concern even when the original ranking is compatible.
export const COMPATIBLE_PROBE_CONSENSUS = 6 / 7;
const families: ToneFamily[] = ['TONE_1', 'TONE_2', 'TONE_3', 'TONE_4'];
export function learnerPitchEvidence(observed: ToneLikenessResult, expected: PitchExpectation) {
  const acceptable = (expected.acceptableTones ?? [expected.tone])
    .filter(t => t !== null && t >= 1 && t <= 4).map(t => `TONE_${t}` as ToneFamily);
  const winner = observed.best;
  const probes = Object.values(observed.perturbations ?? {});
  const support = winner ? observed.fits[winner] : 0;
  const acceptableSupport = Math.max(0, ...acceptable.map(t => observed.fits[t]));
  const runnerUpSupport = Math.max(0, ...families.filter(t => t !== winner).map(t => observed.fits[t]));
  return { acceptable, winner, support, acceptableSupport, runnerUpSupport,
    acceptableMargin: support - acceptableSupport,
    runnerUpMargin: Math.min(observed.margin, support - runnerUpSupport),
    clarity: observed.features.family_clarity ?? 0,
    probeCount: probes.length, probeAgreement: probes.filter(t => t === winner).length,
    consensus: probes.length ? probes.filter(t => t === winner).length / probes.length : 0 };
}
// Advice describes the gesture independently of correctness, including green.
function gestureCoaching(observed: ToneLikenessResult): string | null {
  if (observed.strength !== 'weak' || observed.decision !== 'NUMBERED') return null;
  if (observed.variant === 'reduced_valley') return 'Low ending is compatible with a reduced Tone 3.';
  if (observed.tone === 'TONE_1') return 'Pitch movement was reduced.';
  if (observed.tone === 'TONE_2') return 'Rise is a little weak.';
  if (observed.tone === 'TONE_4') return 'Fall is a little weak.';
  return observed.features.fall_st! < 1.5 ? 'Dip is shallow.' : 'Recovery is weak.';
}
export function gradeLearnerPitch(observed: ToneLikenessResult, expected: PitchExpectation, hasPitch: boolean): LearnerPitchGrade {
  if (!hasPitch) return pitchGrade('UNAVAILABLE', 'no_retained_pitch', "Pitch couldn't be measured reliably.");
  if (observed.decision === 'UNAVAILABLE' || observed.evidence !== 'trustworthy')
    return pitchGrade('UNAVAILABLE', observed.reason, 'Tone unclear');
  if (expected.tone === null) return pitchGrade('UNAVAILABLE', expected.reason, 'Expected pitch is unresolved in this context.');
  // Neutral evidence and chunk non-veto policy stay separate from numbered tones.
  if (expected.tone === 0) return pitchGrade('UNAVAILABLE', 'neutral_has_no_fixed_shape', 'Neutral tone has no fixed pitch shape.');
  const e = learnerPitchEvidence(observed, expected);
  if (!e.acceptable.length || families.some(t => !Number.isFinite(observed.fits[t])) ||
    !Number.isFinite(e.runnerUpMargin) || !Number.isFinite(e.clarity))
    return pitchGrade('UNAVAILABLE', 'invalid_grading_evidence', 'Pitch feedback is unavailable for this evidence.');
  // A reliable measurement with competing interpretations is NOT unavailable.
  if (observed.decision === 'UNCLEAR' || observed.tone === 'UNCLEAR' || observed.best !== observed.tone)
    return pitchGrade('PARTIAL_OR_WEAK', 'ambiguous_family_interpretation',
      'The pitch has more than one plausible interpretation; a tone error is not clear.');
  const coaching = gestureCoaching(observed);
  if (e.acceptable.includes(observed.tone)) {
    if (e.probeCount < CONSERVATIVE_RED.minimumProbes || e.consensus < COMPATIBLE_PROBE_CONSENSUS)
      return pitchGrade('PARTIAL_OR_WEAK', 'compatible_perturbation_uncertainty',
        'The pitch family fits, but small changes in the evidence make the interpretation uncertain.', coaching);
    return pitchGrade('STRONG_MATCH', 'compatible_family_acceptable',
      'The pitch is reasonably acceptable here.', coaching);
  }
  const decisive = e.support >= CONSERVATIVE_RED.support &&
    e.acceptableSupport <= CONSERVATIVE_RED.acceptableSupportMax &&
    e.acceptableMargin >= CONSERVATIVE_RED.acceptableMargin &&
    e.runnerUpMargin >= CONSERVATIVE_RED.runnerUpMargin && e.clarity >= CONSERVATIVE_RED.clarity &&
    e.probeCount >= CONSERVATIVE_RED.minimumProbes && e.consensus >= CONSERVATIVE_RED.consensus;
  if (!decisive) {
    const concern = e.support >= MINIMUM_LEARNER_CONCERN.support &&
      e.acceptableSupport <= MINIMUM_LEARNER_CONCERN.acceptableSupportMax &&
      e.acceptableMargin >= MINIMUM_LEARNER_CONCERN.acceptableMargin &&
      e.runnerUpMargin >= MINIMUM_LEARNER_CONCERN.runnerUpMargin && e.clarity >= MINIMUM_LEARNER_CONCERN.clarity &&
      e.probeCount >= MINIMUM_LEARNER_CONCERN.minimumProbes && e.consensus >= MINIMUM_LEARNER_CONCERN.consensus;
    if (concern) return pitchGrade('PARTIAL_OR_WEAK', 'nondecisive_incompatible_family',
      'The pitch may differ from what is expected here, but a tone error is not clear.', coaching);
    return pitchGrade('STRONG_MATCH', 'insufficient_mismatch_concern',
      'There is not enough evidence of a pitch problem here.', coaching);
  }
  const actual: Record<string, string> = { TONE_1: 'stayed level', TONE_2: 'rose', TONE_3: 'dipped', TONE_4: 'fell' };
  const wanted: Record<number, string> = { 1: 'level pitch', 2: 'a rise', 3: 'low or dipping pitch', 4: 'a fall' };
  const alternatives = e.acceptable.map(t => wanted[Number(t.at(-1))]);
  return pitchGrade('CLEAR_DIFFERENCE', 'decisive_incompatible_family',
    `Expected ${alternatives.join(' or ')}; yours ${actual[observed.tone]}.`, coaching);
}
