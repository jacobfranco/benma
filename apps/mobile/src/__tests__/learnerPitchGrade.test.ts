import { line, valley } from './toneFeedbackFixture';
import { chunkAnalysis } from './pronunciationChunkFixture';

import type { PerceivedSyllable } from '@/api/types';
import { gradeLearnerPitch, pitchExpectation, pitchGradePresentation } from '@/speech/learnerPitchGrade';
import { classifyPitchShape } from '@/speech/pitchShape';
import { classifyToneLikeness } from '@/speech/toneLikeness';

const observe = (points: ReturnType<typeof line>) => classifyToneLikeness(classifyPitchShape([points]), [points]);
const grade = (points: ReturnType<typeof line>, tone: number | null) => gradeLearnerPitch(observe(points), { tone, basis: 'resolved_surface', label: '', coaching: null, reason: 'context_unresolved' }, !!points.length);
it.each([
  [line(x => x * .1), 1, 'STRONG_MATCH'], [line(() => 0), 1, 'STRONG_MATCH'], [line(x => x * 4), 2, 'STRONG_MATCH'],
  [valley(4, 4), 3, 'STRONG_MATCH'], [line(x => -x * 4), 4, 'STRONG_MATCH'],
  [line(x => x * 1.9), 2, 'STRONG_MATCH'], [line(x => -x * 1.9), 4, 'STRONG_MATCH'],
  [valley(1.4, 1.4), 3, 'STRONG_MATCH'], [valley(3, 1.4), 3, 'STRONG_MATCH'],
  [line(x => -x * 4), 3, 'CLEAR_DIFFERENCE'], [line(x => .1 * x), 3, 'STRONG_MATCH'],
  [line(x => x * 4), 4, 'CLEAR_DIFFERENCE'], [valley(4, 4), 2, 'CLEAR_DIFFERENCE'],
  [line(x => x * 4), null, 'UNAVAILABLE'], [[], 4, 'UNAVAILABLE'],
  [line(x => x * 4), 0, 'UNAVAILABLE'],
] as const)('grades relative geometry against contextual expectation (%s, %s)', (points, tone, state) => {
  expect(grade([...points], tone).agreement).toBe(state);
});
it('gives deterministic geometric coaching and distinguishes unavailable pitch from ambiguity', () => {
  expect(grade(line(x => 1.9 * x), 2).coaching).toBe('Rise is a little weak.');
  expect(grade(valley(1.4, 1.4), 3).coaching).toBe('Dip is shallow.');
  expect(grade(valley(3, 1.4), 3).coaching).toBe('Recovery is weak.');
  expect(grade(line(x => 4 * x), 4).message).toBe('Expected a fall; yours rose.');
  expect(grade([], 3).message).toBe("Pitch couldn't be measured reliably.");
  expect(grade(line(x => x, 4), 3).message).toBe('Tone unclear');
});
it('preserves lexical reading while existing 一/不 surface expectations alone drive grading', () => {
  const yi = chunkAnalysis('我要一个苹果').data.syllables[2]!;
  const bu = chunkAnalysis('不是').data.syllables[0]!;
  for (const s of [yi, bu]) {
    const before = JSON.stringify(s), expected = pitchExpectation(s);
    expect(expected.tone).toBe(2);
    expect(gradeLearnerPitch(observe(line(x => x * 4)), expected, true).agreement).toBe('STRONG_MATCH');
    expect(gradeLearnerPitch(observe(line(x => -x * 4)), expected, true).agreement).toBe('CLEAR_DIFFERENCE');
    expect(JSON.stringify(s)).toBe(before);
  }
  expect(yi.lexical_tone).toBe(1); expect(bu.lexical_tone).toBe(4);
  expect(pitchExpectation(chunkAnalysis('第一个').data.syllables[1]!).tone).toBe(1);
});
it('keeps T3 likeness independent of sandhi and uses lexical family only for unresolved surface context', () => {
  const pair = chunkAnalysis('我想').data.syllables;
  const observed = observe(valley(4, 4));
  expect(observed.tone).toBe('TONE_3');
  expect(gradeLearnerPitch(observed, pitchExpectation(pair[0]!), true).agreement).toBe('CLEAR_DIFFERENCE');
  expect(gradeLearnerPitch(observed, pitchExpectation(pair[1]!), true).agreement).toBe('STRONG_MATCH');
  const chain = chunkAnalysis('我想买这个').data.syllables[0]!;
  const before = JSON.stringify(chain);
  expect(pitchExpectation(chain)).toMatchObject({ tone: 3, basis: 'lexical_family', label: 'Tone 3 family' });
  expect(gradeLearnerPitch(observed, pitchExpectation(chain), true).agreement).toBe('STRONG_MATCH');
  expect(gradeLearnerPitch(observe(valley(1.4, 1.4)), pitchExpectation(chain), true).agreement).toBe('STRONG_MATCH');
  expect(gradeLearnerPitch(observe(line(x => -4 * x)), pitchExpectation(chain), true).agreement).toBe('CLEAR_DIFFERENCE');
  expect(JSON.stringify(chain)).toBe(before);
  expect(chain.expected_surface_tone).toBeNull();
});
it('does not grant correctness from a neutral contour or unresolved reading', () => {
  const s = { pinyin: 'ge', reading_source: 'unresolved', expected_surface_tone: 4 } as PerceivedSyllable;
  expect(pitchExpectation(s).tone).toBeNull();
  expect(gradeLearnerPitch(observe(line(x => -4 * x)), pitchExpectation(s), true).agreement).toBe('UNAVAILABLE');
  expect(pitchExpectation({ ...s, reading_source: 'phrase', expected_surface_tone: 0 }).tone).toBe(0);
});
it('maps only pitch agreement to green/amber/red/gray, with equivalent accessible meanings', () => {
  expect(Object.values(pitchGradePresentation).map(v => v.color)).toEqual(['green', 'amber', 'red', 'gray']);
  expect(Object.values(pitchGradePresentation).map(v => v.label)).toEqual(['Pitch acceptable', 'Pitch may be off', 'Pitch differs', 'Pitch unavailable']);
  expect(new Set(Object.values(pitchGradePresentation).map(v => v.symbol)).size).toBe(4);
});

it('separates borderline family evidence from subtle but confident realization', () => {
  for (const tone of [2, 4]) {
    const sign = tone === 2 ? 1 : -1;
    const barely = observe(line(x => sign * .25 * x));
    expect(barely).toMatchObject({ tone: `TONE_${tone}`, strength: 'weak' });
    expect(grade(line(x => sign * .25 * x), tone).agreement).toBe('STRONG_MATCH');
    expect(grade(line(x => sign * .2 * x), tone).agreement).toBe('PARTIAL_OR_WEAK');
    expect(grade(line(x => sign * .4 * x), tone).agreement).toBe('STRONG_MATCH');
  }
  const rows = require('../../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/baseline.json').historical;
  const barely = rows.find((r: { id: string }) => r.id === 'ee8a8b32:我');
  expect(gradeLearnerPitch(barely.observed, barely.expected, true).agreement).toBe('PARTIAL_OR_WEAK');
  const robust = observe(valley(1.4, 1.4));
  expect(robust.strength).toBe('weak');
  for (const changed of [
    { ...robust, perturbations: { ...robust.perturbations, first_point: 'UNCLEAR', last_point: 'UNCLEAR' } },
  ] as typeof robust[]) expect(gradeLearnerPitch(changed, pitchExpectation(chunkAnalysis('我想买这个').data.syllables[2]!), true).agreement).toBe('PARTIAL_OR_WEAK');
  expect(gradeLearnerPitch({ ...robust, evidence: 'unavailable' }, pitchExpectation(chunkAnalysis('我想买这个').data.syllables[2]!), true).agreement).toBe('UNAVAILABLE');
});

it('licenses only nonfinal T2/T3 in unresolved adjacent T3 chains, after explicit surface rules', () => {
  for (const text of ['我想买', '你很想']) {
    const data = chunkAnalysis('我想买这个').data;
    data.syllables = data.syllables.slice(0, 3).map((s, i) => ({ ...s, characters: text[i]! }));
    // Fixtures use the backend surface rules; no phrase identities enter grading.
    const first = data.syllables[0]!;
    const expected = pitchExpectation(first, data.syllables);
    expect(expected.acceptableTones).toEqual([3, 2]);
    for (const [points, state] of [[line(x => 4 * x), 'STRONG_MATCH'], [valley(4, 4), 'STRONG_MATCH'],
      [line(x => -4 * x), 'CLEAR_DIFFERENCE']] as const)
      expect(gradeLearnerPitch(observe([...points]), expected, true).agreement).toBe(state);
    const final = [...data.syllables].reverse().find(s => s.lexical_tone === 3)!;
    expect(pitchExpectation(final, data.syllables).acceptableTones).toBeUndefined();
    expect(pitchExpectation({ ...first, expected_surface_tone: 2 }, data.syllables).tone).toBe(2);
    expect(pitchExpectation({ ...first, expected_surface_tone: 2 }, data.syllables).acceptableTones).toBeUndefined();
    const gap = data.syllables.map((s, i) => i === 1 ? { ...s, character_start: s.character_start + 1 } : s);
    expect(pitchExpectation(first, gap).acceptableTones).toBeUndefined();
  }
});
