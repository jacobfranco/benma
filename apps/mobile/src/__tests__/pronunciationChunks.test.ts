import React from 'react';
import { StyleSheet } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { canonicalWave } from './canonicalWave';
import { chunkAnalysis, physicalChunk, physicalChunkAnalysis } from './pronunciationChunkFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { ExactPlaybackButton } from '@/audio/ExactPlaybackButton';
import { exactRecording } from '@/audio/exactRecording';
import { PitchPlot } from '@/components/PitchPlot';
import { PronunciationWorkspace } from '@/speech/PronunciationWorkspace';
import { chunkEvidence, chunkPitch, chunkReading, isTimedChunk, pronunciationChunks } from '@/speech/pronunciationChunks';
import { pronunciationUnits, unitPitch } from '@/speech/pronunciationWorkspace';
import { SpeechEvidence } from '@/speech/SpeechEvidence';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));

type Data = PerceivedSpeechAnalysis['data'];
const texts = (data: Data) => pronunciationChunks(data).map(c => c.text);
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));

it.each([
  ['我想买这个', ['我', '想', '买', '这个']], ['那个', ['那个']],
  ['我要一个苹果', ['我', '要', '一个', '苹', '果']], ['雨伞', ['雨伞']],
  ['不是', ['不', '是']], ['去吧', ['去', '吧']], ['你好吗', ['你', '好', '吗']],
  ['我们', ['我', '们']], ['三个人', ['三', '个', '人']], ['两本书', ['两', '本', '书']],
  ['我想', ['我', '想']], ['第一个', ['第', '一', '个']], ['一个个', ['一', '个', '个']],
  ['一共', ['一', '共']], ['这，个', ['这', '个']], ['这A个', ['这', '个']],
  ['这1个', ['这', '个']], ['这🙂个', ['这', '个']], ['贵州', ['贵', '州']],
] as [string, string[]][])('partitions %s using only reviewed API candidates', (text, expected) => {
  const data = chunkAnalysis(text).data, before = clone(data);
  expect(texts(data)).toEqual(expected);
  const chunks = pronunciationChunks(data);
  expect(chunks.flatMap(c => c.members)).toEqual(data.syllables);
  expect(new Set(chunks.flatMap(c => c.characterIndices)).size).toBe(data.syllables.length);
  expect(chunks.flatMap(c => c.constituentUnitIds)).toEqual(pronunciationUnits(data).map(u => u.id));
  expect(data).toEqual(before);
});

it('preserves each saved perceived reading and the quantity surface expectations', () => {
  const data = chunkAnalysis('我要一个苹果').data;
  const chunk = pronunciationChunks(data)[2]!;
  expect(chunkReading(chunk)).toBe('yīgè');
  expect(chunk.members[0]).toMatchObject({ pinyin: 'yī', lexical_tone: 1, expected_surface_tone: 2, surface_rule: 'yi_quantity' });
  expect(chunk.members[1]).toMatchObject({ pinyin: 'gè', expected_surface_tone: null, surface_rule: 'quantity_ge_reduction_optional' });
  expect(chunkReading(pronunciationChunks(physicalChunkAnalysis().data).at(-1)!)).toBe('zhège');
  expect(chunkReading(pronunciationChunks(chunkAnalysis('那个').data)[0]!)).toBe('nàge');
});

it('does not infer chunks from clean F0, touching timing, or reading phrase labels', () => {
  const data = chunkAnalysis('我想').data;
  data.syllables.forEach(s => { s.reading_source = 'phrase'; s.pitch_eligibility = { state: 'sufficient' }; });
  data.tone_graph!.filtered.segments = [[{ timestamp_seconds: .2, normalized_semitones: 0 }, { timestamp_seconds: .6, normalized_semitones: 0 }]];
  expect(texts(data)).toEqual(['我', '想']);
  for (const text of ['不是', '我们']) expect(texts(chunkAnalysis(text).data)).toEqual(Array.from(text));
});

it.each([.3, .6, 2])('uses the existing visible pause %s only as a veto', gap => {
  const data = chunkAnalysis('那个').data;
  data.syllables[1]!.start_seconds = .4 + gap;
  data.syllables[1]!.end_seconds = .8 + gap;
  data.duration_seconds = .8 + gap;
  expect(texts(data)).toEqual(['那', '个']);
  data.syllables[1]!.start_seconds = .4 + .299;
  expect(texts(data)).toEqual(['那个']);
});

it.each([0, 1])('keeps partial timing truthful when constituent %s is untimed', index => {
  const data = chunkAnalysis('那个').data;
  data.syllables[index]!.start_seconds = data.syllables[index]!.end_seconds = null;
  const chunks = pronunciationChunks(data);
  expect(chunks.map(c => c.text)).toEqual(['那', '个']);
  expect(chunks[index]).toMatchObject({ timingStatus: 'unavailable', start: null, end: null, constituents: [] });
});

it.each(['unavailable', 'synthetic'] as const)('has no interactive chunks for %s timing', alignment_status => {
  const chunks = pronunciationChunks({ ...chunkAnalysis('那个').data, alignment_status });
  expect(chunks.filter(isTimedChunk)).toEqual([]);
  expect(chunks.flatMap(c => c.members).map(s => s.characters)).toEqual(['那', '个']);
});

it('rejects stale, partial, cross-punctuation, reversed and unsupported candidate metadata', () => {
  for (const change of [
    { character_end: 3 }, { character_start: 1 }, { text: '这个' }, { syllable_indices: [1, 0] },
  ]) {
    const data = chunkAnalysis('那个').data;
    data.pronunciation_chunk_candidates = [{ ...data.pronunciation_chunk_candidates![0]!, ...change }];
    expect(texts(data)).toEqual(['那', '个']);
  }
  for (const policy of [null, 'future-v2']) {
    expect(texts({ ...chunkAnalysis('那个').data, pronunciation_chunk_policy: policy })).toEqual(['那', '个']);
  }
  const data = chunkAnalysis('那个').data;
  data.syllables[0]!.start_seconds = .3; data.syllables[0]!.end_seconds = .6;
  data.syllables[1]!.start_seconds = .1; data.syllables[1]!.end_seconds = .4;
  expect(texts(data)).toEqual(['那', '个']);
});

it('never consumes half of an existing timing group to satisfy a candidate', () => {
  const data = chunkAnalysis('我想买这个').data;
  data.syllables.slice(2, 4).forEach(s => { s.start_seconds = s.end_seconds = null; });
  data.timing_groups = [{ text: '买这', character_start: 2, character_end: 4,
    start_seconds: .8, end_seconds: 1.6, timing_evidence_id: 'indivisible' }];
  expect(texts(data)).toEqual(['我', '想', '买这', '个']);
});

it('keeps repeated chunk instances distinct and history reconstruction identical', () => {
  const data = chunkAnalysis('这个……这个').data;
  const chunks = pronunciationChunks(data);
  expect(chunks.map(c => c.text)).toEqual(['这个', '这个']);
  expect(chunks[0]!.id).not.toBe(chunks[1]!.id);
  const reopened = clone(data), history = pronunciationChunks(reopened);
  expect(history).toEqual(chunks);
  expect(history.map(c => chunkPitch(reopened, c))).toEqual(chunks.map(c => chunkPitch(data, c)));
});

it('preserves the exact physical source-index union, missing 个 pitch and shared scale', () => {
  const data = physicalChunkAnalysis().data, before = clone(data);
  const units = pronunciationUnits(data), chunk = pronunciationChunks(data, units).at(-1)!;
  expect(chunk).toMatchObject({ text: '这个', start: 2.34, end: 3.04, timingStatus: 'timed', reason: 'demonstrative_classifier' });
  const evidence = chunkEvidence(data, chunk, units), graph = chunkPitch(data, chunk, units);
  expect(evidence.map(e => [e.unit.text, e.hasPitch])).toEqual([['这', true], ['个', false]]);
  expect(chunk.constituents).toEqual(units.slice(-2));
  const sourceIndices = graph.segments.flat().map(p => physicalChunk.track.frames.findIndex(f => f.timestamp_seconds === p.timestamp_seconds));
  expect(sourceIndices).toEqual([...Array.from({ length: 15 }, (_, i) => 245 + i), 263, 264, 265, 266, 267]);
  expect(graph.segments.flat()).toEqual(evidence.flatMap(e => e.pitch.segments.flat()));
  expect(graph.minimum_semitones).toBe(unitPitch(data, units[0]!).minimum_semitones);
  expect(graph.maximum_semitones).toBe(unitPitch(data, units[0]!).maximum_semitones);
  expect(data).toEqual(before);
});

it.each(['我想买这个', '那个', '我要一个苹果', '雨伞'])('preserves the selected evidence union for every %s chunk', text => {
  const data = chunkAnalysis(text).data, units = pronunciationUnits(data);
  for (const chunk of pronunciationChunks(data, units)) {
    const actual = chunkPitch(data, chunk, units).segments.flat();
    const expected = chunk.constituents.flatMap(u => unitPitch(data, u, units).segments.flat());
    expect(actual).toEqual(expected);
    for (const point of actual) expect(expected.some(p => p === point)).toBe(true);
  }
});

it('preserves a real gap, rejects unowned points, and never connects constituent lines', () => {
  const data = clone(physicalChunkAnalysis().data);
  const first = { timestamp_seconds: 2.72, normalized_semitones: 1 };
  const gap = { timestamp_seconds: 2.735, normalized_semitones: 12 };
  const second = { timestamp_seconds: 2.74, normalized_semitones: -1 };
  const endpoint = { timestamp_seconds: 3.04, normalized_semitones: 20 };
  data.tone_graph!.filtered.segments = [[first, gap, second, endpoint]];
  const chunk = pronunciationChunks(data).at(-1)!;
  expect(chunkPitch(data, chunk).segments).toEqual([[first], [second]]);
  expect(chunkPitch(data, chunk).segments[0]![0]).toBe(first);
  // A tiny accepted overlap keeps the existing later-start ownership rule.
  data.syllables[3]!.end_seconds = 2.7405;
  expect(chunkEvidence(data, pronunciationChunks(data).at(-1)!).map(e => e.pitch.segments)).toEqual([[[first, gap]], [[second]]]);
});

it('plays canonical PCM over 2.34–3.04 with zero padding and leaves both constituent crops exact', () => {
  const data = physicalChunkAnalysis().data, chunk = pronunciationChunks(data).at(-1)!;
  const bytes = canonicalWave(16000 * 4), before = new Uint8Array(bytes);
  for (const span of [chunk, ...chunk.constituents]) {
    const segment = exactRecording(bytes, span.start!, span.end!);
    expect(segment.subarray(44)).toEqual(bytes.subarray(44 + Math.round(span.start! * 16000) * 2, 44 + Math.round(span.end! * 16000) * 2));
  }
  expect(chunk.constituents.map(c => [c.start, c.end])).toEqual([[2.34, 2.73], [2.74, 3.04]]);
  expect(bytes).toEqual(before);
});

it('wraps saved 雨伞 as one timing identity without fake character timing, graph or playback', () => {
  const controls = require('./fixtures/workspaceTimingControls.json') as { id: string; data: Data }[];
  const data = controls.find(r => r.id === '40357072')!.data;
  const before = clone(data), units = pronunciationUnits(data), chunk = pronunciationChunks(data).at(-1)!;
  expect(chunk).toMatchObject({ text: '雨伞', reason: 'existing_timing_group', start: 3.56, end: 4.87 });
  expect(chunk.constituents).toHaveLength(1);
  expect(chunk.members.every(s => s.start_seconds === null && s.end_seconds === null)).toBe(true);
  expect(chunkPitch(data, chunk)).toEqual(unitPitch(data, units.at(-1)!));
  const bytes = canonicalWave(16000 * 6);
  expect(exactRecording(bytes, chunk.start!, chunk.end!)).toEqual(exactRecording(bytes, units.at(-1)!.start, units.at(-1)!.end));
  expect(data).toEqual(before);
  expect(pronunciationChunks(controls.find(r => r.id === 'd47274bc')!.data).filter(isTimedChunk)).toEqual([]);
});

let renderer: ReactTestRenderer;
afterEach(async () => { if (renderer) await act(async () => renderer.unmount()); });
async function mount(value = physicalChunkAnalysis()) {
  await act(async () => { renderer = create(React.createElement(PronunciationWorkspace, { analysis: value })); });
}
async function press(testID: string) {
  await act(async () => renderer.root.findByProps({ testID }).props.onPress());
}

it('offers one compact chunk target/panel and exposes exact constituents only in details', async () => {
  await mount();
  const overview = renderer.root.findByProps({ testID: 'perceived-sentence-overview' });
  expect(StyleSheet.flatten(overview.props.style).flexWrap).toBe('wrap');
  expect(renderer.root.findAllByProps({ testID: 'pronunciation-unit-4' })).toHaveLength(0);
  await press('pronunciation-unit-3');
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-3' }).props.accessibilityLabel).toBe('这个, pronunciation chunk, Pitch unavailable');
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '这个', start: 2.34, end: 3.04 });
  expect(renderer.root.findByType(PitchPlot).props).toMatchObject({ startSeconds: 2.34, durationSeconds: 3.04 });
  // This archived take has contradictory 这 fragments. Neutral 个 cannot make
  // it green; the fresh take is covered separately in toneFeedbackWorkspace.
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pitch detail is limited.');
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'Pitch unavailable' }).length).toBeGreaterThan(0);
  expect(renderer.root.findByType(PitchPlot).props.display.segments.flat()).toHaveLength(20);
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/No pitch signal|Not enough pitch signal|demonstrative_classifier|Pitch was measured for part of this chunk|Measurement:|experimental/i);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  for (const index of [3, 4, 3, 4]) {
    await press(`chunk-constituent-${index}`);
    const panel = renderer.root.findByProps({ testID: 'selected-constituent-detail' });
    const s = physicalChunk.data.syllables[index]!;
    expect(panel.findByType(ExactPlaybackButton).props).toMatchObject({ text: s.characters, start: s.start_seconds, end: s.end_seconds });
    expect(panel.findAllByType(PitchPlot)).toHaveLength(index === 3 ? 1 : 0);
    expect(JSON.stringify(renderer.toJSON())).toContain(index === 3 ? 'Pitch available' : 'Pitch unavailable');
  }
  expect(JSON.stringify(renderer.toJSON())).toContain('Pitch unavailable');
});

it('keeps a healthy chunk quiet with graph and playback primary', async () => {
  // Existing layout fixture has five selected points in each constituent span.
  await mount(chunkAnalysis('那个'));
  expect(renderer.root.findByType(PitchPlot).props.display.segments.flat()).toHaveLength(10);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '那个', start: 0, end: .8 });
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Measurement:|experimental|Gesture unavailable|Pitch detail is limited|couldn't be measured/i);
});

it.each([true, false])('uses the same availability semantics for grouped 雨伞, pitch available: %s', async available => {
  const value = chunkAnalysis('雨伞');
  value.data.syllables.forEach(s => { s.start_seconds = s.end_seconds = null; });
  value.data.timing_groups = [{ text: '雨伞', character_start: 0, character_end: 2,
    start_seconds: 0, end_seconds: .8, timing_evidence_id: 'group', pitch_eligibility: { state: 'incomplete' } }];
  if (!available) { value.data.tone_graph = null; value.data.measured_pitch = []; }
  await mount(value);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(available ? 1 : 0);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '雨伞', start: 0, end: .8 });
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree.includes("Pitch couldn't be measured reliably.")).toBe(!available);
  expect(tree).not.toMatch(/Pitch detail is limited|Measurement:|experimental|Gesture unavailable/i);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  expect(renderer.root.findAllByProps({ testID: 'selected-constituent-detail' })).toHaveLength(0);
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Measurement evidence: incomplete');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Technical details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('Measurement evidence: incomplete');
});

it('preserves chunk identities/evidence across target changes, untargeted mode and history reopening', async () => {
  const analysis = physicalChunkAnalysis();
  const make = (target?: string, id = 'saved') => React.createElement(SpeechEvidence, { heard: analysis.alignment_reference_text,
    intendedText: target, analysis: { utteranceId: id, state: 'ready', perceived: { ...analysis, id, utterance_id: id } } });
  await act(async () => { renderer = create(make('广州')); });
  await press('pronunciation-unit-3');
  const graph = renderer.root.findByType(PitchPlot).props.display;
  for (const target of ['北京', undefined, '我想买这个']) {
    await act(async () => renderer.update(make(target)));
    expect(renderer.root.findByType(PitchPlot).props.display).toEqual(graph);
    expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('这个');
  }
  await act(async () => renderer.update(make(undefined, 'new-attempt')));
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-3' }).props.accessibilityState.selected).toBe(false);
  await act(async () => renderer.update(make('广州')));
  await press('pronunciation-unit-3');
  expect(renderer.root.findByType(PitchPlot).props.display).toEqual(graph);
});

it('repeated chunks remain independently selectable', async () => {
  await mount(chunkAnalysis('这个……这个'));
  await press('pronunciation-unit-2');
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '这个', start: .8, end: 1.6 });
  await press('pronunciation-unit-0');
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '这个', start: 0, end: .8 });
});

it('the grouped 雨伞 detail never offers individual character audio', async () => {
  const value = chunkAnalysis('雨伞');
  value.data.syllables.forEach(s => { s.start_seconds = s.end_seconds = null; });
  value.data.timing_groups = [{ text: '雨伞', character_start: 0, character_end: 2, start_seconds: 0, end_seconds: .8, timing_evidence_id: 'group' }];
  await mount(value);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  expect(renderer.root.findAllByType(ExactPlaybackButton).map(n => n.props.text)).toEqual(['雨伞', '雨伞']);
  expect(JSON.stringify(renderer.toJSON())).toContain('Separate character timing and playback are unavailable.');
});

it('no timing keeps whole-recording practice and no bounded chunk controls', async () => {
  const value = chunkAnalysis('我想买这个'); value.data.alignment_status = 'unavailable';
  await mount(value);
  expect(renderer.root.findAllByType(ExactPlaybackButton)).toHaveLength(0);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(0);
  expect(JSON.stringify(renderer.toJSON())).toContain('whole recording');
});

it('Conversation stays collapsed and uses the same chunks when opened', async () => {
  const analysis = physicalChunkAnalysis();
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, { compact: true, heard: analysis.alignment_reference_text,
    analysis: { utteranceId: analysis.utterance_id, state: 'ready', perceived: analysis } })); });
  expect(renderer.root.findAllByType(PronunciationWorkspace)).toHaveLength(0);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Explore pronunciation' }).props.onPress());
  await press('pronunciation-unit-3');
  expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('这个');
});
