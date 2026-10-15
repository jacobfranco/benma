import { copy, freshToneAnalysis, replacePitch, dominantCases, gestureKnots, piecewise } from './toneFeedbackFixture';
import { chunkAnalysis } from './pronunciationChunkFixture';

import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { pronunciationChunks } from '@/speech/pronunciationChunks';
import type { PerceivedSpeechAnalysis } from '@/api/types';

const last = (a: PerceivedSpeechAnalysis) => gradeChunkPitch(a, pronunciationChunks(a.data).at(-1)!);
it('makes the fresh 这个 green with supported falling 这 and genuinely unmeasured neutral 个', () => {
  const before = JSON.stringify(freshToneAnalysis), result = last(freshToneAnalysis);
  expect(result.grade.agreement).toBe('STRONG_MATCH');
  expect(result.constituents.map(c => [c.unit.text, c.role, c.grade.agreement])).toEqual([
    ['这', 'grade_bearing', 'STRONG_MATCH'], ['个', 'neutral_unmeasured_nonveto', 'UNAVAILABLE'],
  ]);
  expect(JSON.stringify(freshToneAnalysis)).toBe(before);
});
it.each([
  [(x: number) => 4 * x, 'CLEAR_DIFFERENCE'], [undefined, 'UNAVAILABLE'],
  [(x: number) => .25 * -x, 'STRONG_MATCH'],
] as const)('never lets neutral exemption hide a grade-bearing difference, absence or borderline family evidence', (fn, state) => {
  for (const measuredNeutral of ['absent', 'trustworthy', 'corrupt']) {
    const a = copy(freshToneAnalysis); replacePitch(a, 3, fn);
    if (measuredNeutral === 'trustworthy') replacePitch(a, 4, x => .1 * x);
    if (measuredNeutral === 'corrupt') replacePitch(a, 4, x => x < .5 ? x * 4 : x * 4 + 12);
    expect(last(a).grade.agreement).toBe(state);
  }
});
it.each([(x: number) => 4 * x, (x: number) => -4 * x, (x: number) => .1 * x,
  (x: number) => 4 * Math.abs(x * 2 - 1), (x: number) => 2.2 * (1 - Math.abs(x * 2 - 1))])('does not invent a fixed canonical correctness target for measured neutral pitch', fn => {
  const a = copy(freshToneAnalysis); replacePitch(a, 4, fn);
  expect(last(a).grade.agreement).toBe('STRONG_MATCH');
  expect(last(a).constituents[1]!).toMatchObject({ role: 'neutral_measured_accepted', grade: { agreement: 'STRONG_MATCH', reason: 'supported_contextual_neutral' } });
});
it('makes contradictory measured neutral non-veto without awarding positive credit', () => {
  const a = copy(freshToneAnalysis); replacePitch(a, 4, x => x < .5 ? x * 4 : x * 4 + 12);
  expect(last(a).constituents[1]!).toMatchObject({ hasPitch: true, shape: { shape: 'UNCLEAR' },
    role: 'neutral_unreliable_nonveto', grade: { agreement: 'UNAVAILABLE', reason: 'unreliable_contextual_neutral' } });
  expect(last(a).grade.agreement).toBe('STRONG_MATCH');
});
it.each(['non-neutral', 'unresolved', 'no-policy', 'no-playback', 'no-timing'] as const)('bounds the neutral non-veto policy: %s', failure => {
  const a = copy(freshToneAnalysis);
  if (failure === 'non-neutral') a.data.syllables[4]!.expected_surface_tone = 4;
  if (failure === 'unresolved') a.data.syllables[4]!.reading_source = 'unresolved';
  if (failure === 'no-policy') a.data.pronunciation_chunk_policy = null;
  if (failure === 'no-playback') a.utterance_id = '';
  if (failure === 'no-timing') a.data.syllables[4]!.start_seconds = a.data.syllables[4]!.end_seconds = null;
  const result = last(a);
  expect(result.grade.agreement).toBe('UNAVAILABLE');
  expect(result.hasNeutralNonVeto).toBe(false);
});
it('applies the same semantic exemption to 那个 without using character identity', () => {
  const a = chunkAnalysis('那个'); replacePitch(a, 0, x => -4 * x); replacePitch(a, 1);
  expect(last(a).grade.agreement).toBe('STRONG_MATCH');
  expect(last(a).constituents[1]!.role).toBe('neutral_unmeasured_nonveto');
});
it('leaves 吧 as the existing standalone neutral unit without silently creating a new chunk', () => {
  const a = chunkAnalysis('去吧'); replacePitch(a, 0, x => -4 * x); replacePitch(a, 1);
  expect(pronunciationChunks(a.data).map(c => c.text)).toEqual(['去', '吧']);
  expect(last(a).grade.agreement).toBe('UNAVAILABLE');
  expect(last(a).hasNeutralNonVeto).toBe(false);
});
it('does not exempt optional quantity 个 or grouped 雨伞', () => {
  const quantity = chunkAnalysis('我要一个苹果');
  const chunk = pronunciationChunks(quantity.data).find(c => c.text === '一个')!;
  replacePitch(quantity, 2, x => 4 * x); replacePitch(quantity, 3);
  expect(gradeChunkPitch(quantity, chunk).grade.agreement).toBe('UNAVAILABLE');
  const controls = require('./fixtures/workspaceTimingControls.json') as { id: string; data: PerceivedSpeechAnalysis['data'] }[];
  const a = { ...freshToneAnalysis, data: controls.find(r => r.id === '40357072')!.data };
  expect(last(a).constituents).toHaveLength(1);
  expect(last(a).grade).toMatchObject({ agreement: 'UNAVAILABLE', reason: 'grouped_timing' });
});
it('keeps geometry, rankings and grades identical under intended-target-only changes', () => {
  const before = last(freshToneAnalysis);
  for (const target of ['广州', '贵州', '我想买这个', null]) {
    const a = { ...freshToneAnalysis, intended_text: target, target, data: { ...freshToneAnalysis.data, target } };
    expect(last(a)).toEqual(before);
  }
  const a = chunkAnalysis('贵州'); replacePitch(a, 0, x => -4 * x); replacePitch(a, 1, () => 0);
  expect(pronunciationChunks(a.data).map(c => gradeChunkPitch({ ...a, intended_text: '广州' } as PerceivedSpeechAnalysis, c).grade.agreement)).toEqual(['STRONG_MATCH', 'STRONG_MATCH']);
});
it.each(['sufficient', 'incomplete', 'unstable', 'insufficient'] as const)('does not allow strict %s status to pick a grade', state => {
  const a = copy(freshToneAnalysis); a.data.syllables.forEach(s => { s.pitch_eligibility = { state }; });
  expect(last(a).grade.agreement).toBe('STRONG_MATCH');
});

it.each(dominantCases)('keeps clean %s observations invariant under intended-target-only changes', (name, shape, tone) => {
  const a = copy(freshToneAnalysis); replacePitch(a, 0, piecewise(gestureKnots[name]));
  const project = (analysis: PerceivedSpeechAnalysis) => pronunciationChunks(analysis.data).map(c => gradeChunkPitch(analysis, c));
  const before = project(a);
  expect(before[0]!.constituents[0]!).toMatchObject({ shape: { shape }, observed: { tone } });
  for (const target of ['广州', '贵州', '我想买这个', null]) {
    expect(project({ ...a, intended_text: target, target, data: { ...a.data, target } } as PerceivedSpeechAnalysis)).toEqual(before);
  }
});
it('positively accepts neutral family ambiguity but preserves structural and timing boundaries', () => {
  const a = copy(freshToneAnalysis); replacePitch(a, 4, x => 2.2 * (1 - Math.abs(x * 2 - 1)));
  expect(last(a).constituents[1]!).toMatchObject({ observed: { tone: 'UNCLEAR' }, shape: { structurallyUsable: true },
    role: 'neutral_measured_accepted', grade: { agreement: 'STRONG_MATCH' } });
  const before = JSON.stringify(a);
  for (const target of ['广州', '贵州', null]) {
    expect(last({ ...a, intended_text: target, target, data: { ...a.data, target } } as PerceivedSpeechAnalysis)).toEqual(last(a));
  }
  expect(JSON.stringify(a)).toBe(before);
  for (const failure of ['overlap', 'no-playback', 'no-policy', 'unresolved'] as const) {
    const b = copy(a);
    if (failure === 'overlap') b.data.syllables[4]!.start_seconds = b.data.syllables[3]!.end_seconds! - .02;
    if (failure === 'no-playback') b.utterance_id = '';
    if (failure === 'no-policy') b.data.pronunciation_chunk_policy = null;
    if (failure === 'unresolved') b.data.syllables[4]!.reading_source = 'unresolved';
    expect(last(b).constituents.every(c => c.role !== 'neutral_measured_accepted')).toBe(true);
  }
});
it('does not positively accept sparse or deletion-sensitive neutral support', () => {
  const a = copy(freshToneAnalysis); replacePitch(a, 4, x => 4 * x);
  const segment = a.data.tone_graph!.filtered.segments!.at(-1)!;
  segment.splice(8);
  expect(last(a).constituents[1]!).toMatchObject({ role: 'neutral_unreliable_nonveto', grade: { agreement: 'UNAVAILABLE' } });
  expect(last(a).grade.agreement).toBe('STRONG_MATCH');
});
it('keeps measured standalone and optional quantity neutrals bounded, and accepts measured 那个 semantically', () => {
  for (const text of ['去吧', '我要一个苹果', '那个']) {
    const a = chunkAnalysis(text);
    const head = text === '我要一个苹果' ? 2 : 0, dependent = head + 1;
    replacePitch(a, head, x => text === '我要一个苹果' ? 4 * x : -4 * x);
    // A decisive rise remains a real mismatch for the quantity's T4; a weak
    // incompatible leader can now be acceptable without gaining neutral status.
    replacePitch(a, dependent, x => 4 * x);
    const c = pronunciationChunks(a.data).find(c => c.members.some(s => s.index === dependent))!;
    const result = gradeChunkPitch(a, c);
    expect(result.constituents.at(-1)!.role).toBe(text === '那个' ? 'neutral_measured_accepted' : 'grade_bearing');
    if (text !== '那个') expect(result.grade.agreement).not.toBe('STRONG_MATCH');
  }
});
