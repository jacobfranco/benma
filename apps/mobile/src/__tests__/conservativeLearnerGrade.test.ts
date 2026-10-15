import { gradeLearnerPitch, type PitchExpectation } from '@/speech/learnerPitchGrade';
import type { ToneFamily, ToneLikenessResult } from '@/speech/toneLikeness';

// Policy controls inject classifier outputs, never manipulate measured contours.
const families: ToneFamily[] = ['TONE_1', 'TONE_2', 'TONE_3', 'TONE_4'];
const expectation = (tone: number): PitchExpectation => ({ tone, basis: 'resolved_surface',
  label: '', coaching: null, reason: 'control' });
function observed(tone: ToneFamily, support = .97, rival: ToneFamily = families.find(t => t !== tone)!, rivalSupport = .02): ToneLikenessResult {
  return { tone, decision: 'NUMBERED', evidence: 'trustworthy', best: tone, runnerUp: rival,
    fits: { TONE_1: 0, TONE_2: 0, TONE_3: 0, TONE_4: 0, [tone]: support, [rival]: rivalSupport },
    margin: support - rivalSupport, reason: 'best_fit', strength: 'full', variant: 'ordinary',
    features: { family_clarity: 1, fall_st: 1, recovery_st: 1 },
    perturbations: Object.fromEntries(['first', 'last', 'tenth', 'early', 'late', 'short', 'long'].map(k => [k, tone])) };
}
const grade = (o: ToneLikenessResult, tone: number) => gradeLearnerPitch(o, expectation(tone), true);

it.each(families)('accepts full and stable weak %s without requiring ideal strength or high match support', tone => {
  for (const support of [.6, .97]) for (const strength of ['full', 'weak'] as const) {
    const o = { ...observed(tone, support), strength }, before = JSON.stringify(o);
    const result = grade(o, Number(tone.at(-1)));
    expect(result.agreement).toBe('STRONG_MATCH');
    expect(!!result.coaching).toBe(strength === 'weak');
    expect(JSON.stringify(o)).toBe(before);
  }
});
it('accepts reduced valid T3 with independent coaching', () => {
  const result = grade({ ...observed('TONE_3', .73), strength: 'weak', variant: 'reduced_valley' }, 3);
  expect(result.agreement).toBe('STRONG_MATCH');
  expect(result.coaching).toContain('reduced Tone 3');
  expect(result.message).toContain('acceptable');
});
it.each(families.flatMap(tone => [1, 2, 3, 4].filter(t => tone !== `TONE_${t}`).map(t => [tone, t] as const)))(
  'corrects a decisive %s against expected %s, independent of gesture strength', (tone, expected) => {
    for (const strength of ['full', 'weak'] as const)
      expect(grade({ ...observed(tone), strength }, expected).agreement).toBe('CLEAR_DIFFERENCE');
  });
it.each([
  ['moderate winner', observed('TONE_4', .65)],
  ['expected remains plausible', observed('TONE_4', .95, 'TONE_3', .31)],
  ['third family competes', observed('TONE_4', .95, 'TONE_2', .4)],
  ['one probe disagrees', { ...observed('TONE_4'), perturbations: { ...observed('TONE_4').perturbations, first: 'TONE_3' } }],
  ['one probe abstains', { ...observed('TONE_4'), perturbations: { ...observed('TONE_4').perturbations, first: 'UNCLEAR' } }],
] as [string, ToneLikenessResult][])('withholds red when %s', (_, o) => {
  const result = grade(o, 3);
  expect(result.agreement).toBe('PARTIAL_OR_WEAK');
  expect(result.message).toContain('may differ');
});
it('maps trustworthy family competition to amber, and unavailable measurements to gray regardless of partial scores', () => {
  const o: ToneLikenessResult = { ...observed('TONE_3', .52, 'TONE_4', .49), tone: 'UNCLEAR', decision: 'UNCLEAR' };
  expect(grade(o, 3).agreement).toBe('PARTIAL_OR_WEAK');
  for (const unsafe of [{ ...o, evidence: 'unavailable' as const },
    { ...observed('TONE_4'), decision: 'UNAVAILABLE' as const }]) expect(grade(unsafe, 3).agreement).toBe('UNAVAILABLE');
  expect(gradeLearnerPitch(observed('TONE_4'), expectation(3), false).agreement).toBe('UNAVAILABLE');
  expect(gradeLearnerPitch(observed('TONE_4'), { ...expectation(3), tone: null }, true).agreement).toBe('UNAVAILABLE');
});
it('respects every acceptable family without changing the observation or licensing a fall', () => {
  const expected = { ...expectation(3), acceptableTones: [3, 2] };
  for (const tone of ['TONE_2', 'TONE_3', 'TONE_4'] as const) {
    const o = observed(tone), before = JSON.stringify(o);
    expect(gradeLearnerPitch(o, expected, true).agreement).toBe(tone === 'TONE_4' ? 'CLEAR_DIFFERENCE' : 'STRONG_MATCH');
    expect(JSON.stringify(o)).toBe(before);
  }
  expect(gradeLearnerPitch(observed('TONE_4', .97, 'TONE_2', .3), expected, true).agreement).toBe('PARTIAL_OR_WEAK');
});
it('keeps uncertainty and shallow coaching separate', () => {
  const o = { ...observed('TONE_3'), strength: 'weak' as const };
  const green = grade(o, 3);
  const amber = grade({ ...o, perturbations: { ...o.perturbations, first: 'UNCLEAR', last: 'UNCLEAR' } }, 3);
  expect(green.agreement).toBe('STRONG_MATCH');
  expect(amber.agreement).toBe('PARTIAL_OR_WEAK');
  expect(green.coaching).toBe('Dip is shallow.');
  expect(amber.coaching).toBe(green.coaching);
  expect(amber.reason).toBe('compatible_perturbation_uncertainty');
});

it.each([
  ['weak winner despite stable probes', observed('TONE_4', .48)],
  ['marginal support and separation', observed('TONE_4', .54, 'TONE_2', .18)],
  ['plausible acceptable alternative', observed('TONE_4', .95, 'TONE_3', .42)],
  ['small acceptable margin', observed('TONE_4', .8, 'TONE_3', .32)],
  ['competing incompatible alternative', observed('TONE_4', .8, 'TONE_2', .38)],
  ['low clarity', { ...observed('TONE_4'), features: { family_clarity: .89 } }],
  ['incomplete probes', { ...observed('TONE_4'), perturbations: { first: 'TONE_4' } }],
  ['unstable winner', { ...observed('TONE_4', .8), perturbations: {
    ...observed('TONE_4').perturbations, first: 'TONE_3', last: 'UNCLEAR' } }],
  ['classifier margin limits separation', { ...observed('TONE_4', .8), margin: .3 }],
] as [string, ToneLikenessResult][])('withholds a numbered mismatch warning for %s', (_, o) => {
  const before = JSON.stringify(o), result = grade(o, 3);
  expect(result.agreement).toBe('STRONG_MATCH');
  expect(result.reason).toBe('insufficient_mismatch_concern');
  expect(result.message).not.toContain('may differ');
  expect(JSON.stringify(o)).toBe(before);
});

it('progresses smoothly from weak evidence through meaningful concern to decisive correction', () => {
  const controls = Array.from({ length: 51 }, (_, i) => {
    const support = .45 + i * .01, acceptableSupport = .2 * (1 - i / 50);
    const o = observed('TONE_4', support, 'TONE_3', acceptableSupport);
    return { support, grade: grade(o, 3).agreement };
  });
  const levels = { STRONG_MATCH: 0, PARTIAL_OR_WEAK: 1, CLEAR_DIFFERENCE: 2, UNAVAILABLE: -1 };
  expect([...new Set(controls.map(c => c.grade))]).toEqual(['STRONG_MATCH', 'PARTIAL_OR_WEAK', 'CLEAR_DIFFERENCE']);
  for (let i = 1; i < controls.length; i++)
    expect(levels[controls[i]!.grade]).toBeGreaterThanOrEqual(levels[controls[i - 1]!.grade]);
  expect(controls[0]!.grade).toBe('STRONG_MATCH');
  expect(controls[30]!.grade).toBe('PARTIAL_OR_WEAK');
  expect(controls[50]!.grade).toBe('CLEAR_DIFFERENCE');
});

it('uses all contextually acceptable alternatives for the concern floor', () => {
  const o = observed('TONE_4', .8, 'TONE_2', .32);
  // Both numbered targets remain incompatible with T4; the extra acceptable
  // alternative changes the acceptable margin, not the acoustic leader.
  expect(grade(o, 3).agreement).toBe('PARTIAL_OR_WEAK');
  expect(gradeLearnerPitch(o, { ...expectation(3), acceptableTones: [3, 2] }, true).agreement).toBe('STRONG_MATCH');
});

it('keeps the complete decisive certificate red, ahead of the concern fallback', () => {
  const o = observed('TONE_4', .9, 'TONE_3', .2);
  o.features.family_clarity = .9;
  expect(grade(o, 3).agreement).toBe('CLEAR_DIFFERENCE');
  expect(grade({ ...o, margin: .59 }, 3).agreement).toBe('PARTIAL_OR_WEAK');
});
