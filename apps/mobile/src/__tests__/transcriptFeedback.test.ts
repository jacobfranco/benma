import React from 'react';
import { Text } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { SpeechEvidence } from '@/speech/SpeechEvidence';
import { PitchPlot, contourGeometry } from '@/components/PitchPlot';
import { SentenceToneGraph } from '@/speech/SentenceToneGraph';
import { TranscriptFeedback } from '@/speech/TranscriptFeedback';
import { expectedLabel, graphWidth, pitchSignal, rawPitch } from '@/speech/sentenceToneGraph';

jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));
let renderer: ReactTestRenderer;
const data = perceivedAnalysis.data;
async function render(value = data) {
  await act(async () => { renderer = create(React.createElement(SentenceToneGraph, { data: value })); });
}
afterEach(async () => { if (renderer) await act(async () => renderer.unmount()); });
async function press(label: string) {
  await act(async () => renderer.root.findByProps({ accessibilityLabel: label }).props.onPress());
}

it.each(['preserve', 'infer', 'clarify'] as const)('keeps the measured sentence and immutable heard units during %s', async decision => {
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, {
    heard: '周谋', decision, understood: decision === 'infer' ? '周末' : null,
    analysis: { utteranceId: 'u', state: 'ready', perceived: perceivedAnalysis },
  })); });
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('What Benma heard');
  expect(tree).toContain('周'); expect(tree).toContain('谋');
  expect(tree).not.toMatch(/accuracy|Tone 2-like|mò/);
  expect(renderer.root.findByType(PitchPlot).props.display).toBe(data.tone_graph!.mine);
  expect(tree.includes('What Benma understood')).toBe(decision === 'infer');
  expect(tree.includes('Meaning')).toBe(decision === 'clarify');
});

it('S13 shows 贵州 units and a separate 广 → 贵 target comparison, even with legacy target analysis', async () => {
  const syllables = ['我', '要', '去', '贵', '州'].map((characters, index) => ({
    ...data.syllables[0]!, characters, index, character_start: index, character_end: index+1,
    pinyin: ['wǒ', 'yào', 'qù', 'guì', 'zhōu'][index]!,
    expected_surface_tone: ([3, 4, 4, 4, 1] as const)[index]!, start_seconds: index * .2, end_seconds: (index+1)*.2,
  }));
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, {
    heard: '我要去贵州。', intendedText: '我要去广州。',
    pronunciation: { target: { text: '我要去广州。' }, syllables: [{ characters: '广' }] } as never,
    analysis: { utteranceId: 'u', state: 'ready', perceived: { ...perceivedAnalysis,
      alignment_reference_text: '我要去贵州。', data: { ...data, syllables } } },
  })); });
  const graph = renderer.root.findByType(SentenceToneGraph);
  expect(graph.props.data.syllables.map((s: { characters: string }) => s.characters).join('')).toBe('我要去贵州');
  expect(JSON.stringify(renderer.toJSON())).toContain('广 → 贵');
  expect(graph.findByProps({ testID: 'character-unit-3' }).props.accessibilityLabel).not.toContain('T4');
  expect(JSON.stringify(graph.props)).not.toContain('guǎng');
});

it('timing and pitch survive unresolved readings while expected reference abstains', async () => {
  const s = { ...data.syllables[0]!, characters: '行', pinyin: null, lexical_tone: null,
    reading_source: 'unresolved' as const, expected_surface_tone: null };
  await render({ ...data, syllables: [s] });
  expect(renderer.root.findByProps({ testID: 'character-unit-0' })).toBeTruthy();
  expect(renderer.root.findByType(PitchPlot).props.display).toBe(data.tone_graph!.mine);
  await act(async () => renderer.root.findByProps({ testID: 'character-unit-0' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('Reading unresolved');
  expect(expectedLabel(s)).toBe('Reading unresolved');
  expect(expectedLabel({ ...s, reading_source: 'dictionary', lexical_tone: 3 })).toBe('Reading unresolved');
});

it('identical heard evidence keeps geometry and signal unchanged across different intended targets', async () => {
  const props = { heard: '周谋', analysis: { utteranceId: 'u', state: 'ready' as const, perceived: perceivedAnalysis } };
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, { ...props, intendedText: '周末' })); });
  const layout = renderer.root.findByType(PitchPlot).props.xLayout;
  const label = renderer.root.findByProps({ testID: 'character-unit-0' }).props.accessibilityLabel;
  await act(async () => renderer.update(React.createElement(SpeechEvidence, { ...props, intendedText: '广州' })));
  expect(renderer.root.findByType(PitchPlot).props.xLayout).toEqual(layout);
  expect(renderer.root.findByProps({ testID: 'character-unit-0' }).props.accessibilityLabel).toBe(label);
});

it('keeps gaps in Mine and detail and never overlays expected shapes', async () => {
  await render();
  const mine = renderer.root.findByType(PitchPlot).props;
  expect(mine.display.segments).toHaveLength(2);
  expect(mine.reference).toBeUndefined();
  const geometry = contourGeometry(mine.display.segments, 300, 100, [-3, 3], 0, 1.2);
  expect(geometry).toHaveLength(2);
  expect(geometry[0]!.at(-1)!.x).toBeLessThan(geometry[1]![0]!.x);
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Raw tracker evidence');
  await press('More detail');
  const detail = renderer.root.findByType(PitchPlot).props;
  expect(detail.display).toBe(data.tone_graph!.filtered);
  expect(detail.showPoints).toBe(true);
  expect(detail.reference).toBeUndefined();
  await press('Raw');
  const raw = renderer.root.findAllByType(PitchPlot)[1]!.props;
  expect(raw.pointsOnly).toBe(true);
  expect(raw.rejected).toHaveLength(110);
  expect(raw.reference).toBeUndefined();
});

it.each([0, 1, 2, 3, 4, null] as const)('contextual reference %s never mutates observed pitch', async tone => {
  const before = JSON.stringify(data.tone_graph);
  await render({ ...data, syllables: [{ ...data.syllables[0]!, lexical_tone: 3, expected_surface_tone: tone }] });
  expect(renderer.root.findByType(PitchPlot).props.display).toBe(data.tone_graph!.mine);
  expect(JSON.stringify(data.tone_graph)).toBe(before);
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Tone \d-like|Correct|Wrong|Perfect/);
});

it('shows partial evidence and deterministic quality independent of expected tone', () => {
  expect(pitchSignal(data)).toBe('Pitch signal: Limited');
  expect(pitchSignal(data, .15, .6)).toBe('Pitch signal: Not enough');
  expect(pitchSignal(data, .1, .15)).toBe('Pitch signal: Clear');
  const before = JSON.stringify(data);
  expect(rawPitch(data)).toEqual(rawPitch(data));
  expect(rawPitch(data).retained.every(p => p.normalized_semitones === 0)).toBe(true);
  expect(JSON.stringify(data)).toBe(before);
});

it('handles all-missing pitch while preserving every timed region and an empty raw graph', async () => {
  const missing = { ...data, tone_graph: { mine: { segments: [] }, filtered: { segments: [] },
    raw: data.tone_graph!.raw.map(p => ({ ...p, f0_hz: null, tracker_f0_hz: null, selected_f0_hz: null, retained: false })) } };
  await render(missing);
  expect(renderer.root.findByType(PitchPlot).props.display.segments).toEqual([]);
  expect(renderer.root.findByProps({ testID: 'character-unit-0' })).toBeTruthy();
  expect(renderer.root.findByProps({ testID: 'character-unit-1' })).toBeTruthy();
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Not enough pitch signal');
  await press('More detail'); await press('Raw');
  expect(rawPitch(missing).rejected.every(p => p.normalized_semitones === null)).toBe(true);
});

it('keeps a zero-F0 syllable empty even if its expected tone has a schematic shape', async () => {
  const zero = { ...data, tone_graph: { ...data.tone_graph!, mine: { segments: [data.tone_graph!.mine.segments![0]!] } } };
  await render(zero);
  const points = renderer.root.findByType(PitchPlot).props.display.segments.flat();
  expect(points.every((p: { timestamp_seconds: number }) => p.timestamp_seconds < .6)).toBe(true);
  expect(renderer.root.findByProps({ testID: 'character-unit-1' })).toBeTruthy();
});

it('handles one syllable, long sentences, mixed timing, and synthetic timing without fabricated partitions', async () => {
  await render({ ...data, syllables: [data.syllables[0]!] });
  expect(renderer.root.findByType(PitchPlot).props.regions).toHaveLength(1);
  const long = Array.from({ length: 60 }, (_, i) => ({ ...data.syllables[0]!, index: i, start_seconds: i*.3, end_seconds: i*.3+.2 }));
  await act(async () => renderer.update(React.createElement(SentenceToneGraph, { data: { ...data, duration_seconds: 20, syllables: long } })));
  expect(renderer.root.findByType(PitchPlot).props.regions).toHaveLength(60);
  expect(graphWidth(320, 20, 60)).toBeGreaterThan(320);
  expect(graphWidth(320, 100, 1000)).toBe(6000);
  await act(async () => renderer.update(React.createElement(SentenceToneGraph, { data: { ...data, syllables: [data.syllables[0]!, { ...data.syllables[1]!, start_seconds: null, end_seconds: null }] } })));
  expect(renderer.root.findByType(PitchPlot).props.regions).toHaveLength(1);
  expect(renderer.root.findByType(PitchPlot).props.xLayout.regions).toHaveLength(2);
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Syllable timing is unavailable');
  await act(async () => renderer.update(React.createElement(SentenceToneGraph, { data: { ...data, alignment_status: 'synthetic' } })));
  expect(renderer.root.findByType(PitchPlot).props.regions).toHaveLength(0);
});

it('does not re-filter or invent full evidence for old saved analyses', async () => {
  const old: PerceivedSpeechAnalysis['data'] = { ...data, tone_graph: null, display_contour: data.tone_graph!.mine };
  await render(old); await press('More detail'); await press('Raw');
  expect(JSON.stringify(renderer.toJSON())).toContain('Record again for full pitch detail');
  expect(JSON.stringify(renderer.toJSON())).toContain('Raw tracker evidence unavailable');
});

it('preserves a non-Han transcript without empty graph units', async () => {
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, { heard: 'Neal zaigan shima' })); });
  expect(JSON.stringify(renderer.toJSON())).toContain('Neal zaigan shima');
  expect(renderer.root.findAllByType(SentenceToneGraph)).toHaveLength(0);
});

it('detail uses real seconds for a bounded sentence domain and reserves readable widths for short syllables', async () => {
  const shifted = { ...data, duration_seconds: 6, syllables: data.syllables.map(s => ({ ...s,
    start_seconds: s.start_seconds! + 2, end_seconds: s.end_seconds! + 2 })), tone_graph: {
      ...data.tone_graph!, mine: { ...data.tone_graph!.mine, segments: data.tone_graph!.mine.segments!.map(s => s.map(p => ({ ...p, timestamp_seconds: p.timestamp_seconds + 2 }))) },
      filtered: { ...data.tone_graph!.filtered, segments: data.tone_graph!.filtered.segments!.map(s => s.map(p => ({ ...p, timestamp_seconds: p.timestamp_seconds + 2 }))) },
    } };
  await render(shifted); await press('More detail');
  const plot = renderer.root.findByType(PitchPlot).props;
  expect(plot.startSeconds).toBe(2);
  expect(plot.durationSeconds).toBe(3.2);
  expect(plot.display).toBe(shifted.tone_graph.filtered);
  expect(graphWidth(320, 3, 12, .09) * .09 / 3).toBeCloseTo(48);
  await act(async () => renderer.root.findByProps({ testID: 'character-unit-1' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('Reference tone: T2');
  expect(JSON.stringify(renderer.toJSON())).toContain('2.60–3.20 s');
});

it('a new analysis remounts the scroll strip at its first cell and clears detail/tap state', async () => {
  await act(async () => { renderer = create(React.createElement(TranscriptFeedback, { analysis: perceivedAnalysis })); });
  const old = renderer.root.findByType(SentenceToneGraph);
  await act(async () => renderer.root.findByProps({ testID: 'character-unit-1' }).props.onPress());
  await press('More detail'); await press('Raw');
  await act(async () => renderer.update(React.createElement(TranscriptFeedback, { analysis: { ...perceivedAnalysis, id: 'new-result' } })));
  expect(renderer.root.findByType(SentenceToneGraph)).not.toBe(old);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(1);
  expect(renderer.root.findByType(PitchPlot).props.xLayout.regions[0].start).toBe(0);
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Lexical tone:');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Raw tracker evidence');
});

it('hides identical target comparison and keeps a differing target compact', async () => {
  const props = { heard: '贵州。', intendedText: '贵州', analysis: { utteranceId: 'u', state: 'ready' as const, perceived: perceivedAnalysis } };
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, props)); });
  expect(renderer.root.findAllByProps({ testID: 'target-comparison' })).toHaveLength(0);
  await act(async () => renderer.update(React.createElement(SpeechEvidence, { ...props, intendedText: '广州' })));
  const comparison = renderer.root.findByProps({ testID: 'target-comparison' });
  expect(comparison.findAllByType(Text).map(n => n.props.children).flat().join('')).toContain('Target difference: 广 → 贵');
  expect(comparison.findAllByType(Text).map(n => n.props.children).flat().join('')).not.toContain('Target:');
});

it('uses the completed character strip as heard text while retaining uncovered mixed text', async () => {
  const props = { heard: '周谋', analysis: { utteranceId: 'u', state: 'ready' as const, perceived: perceivedAnalysis } };
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, props)); });
  expect(renderer.root.findAllByType(Text).filter(n => n.props.children === '周谋')).toHaveLength(0);
  expect(renderer.root.findByType(SentenceToneGraph).props.data.syllables.map((s: { characters: string }) => s.characters).join('')).toBe('周谋');
  await act(async () => renderer.update(React.createElement(SpeechEvidence, { ...props, heard: '周谋 ABC' })));
  expect(renderer.root.findAllByType(Text).filter(n => n.props.children === '周谋 ABC')).toHaveLength(1);
});
