import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import { ContourLines, PitchPlot, contourGeometry, normalizedGeometry } from '@/components/PitchPlot';
import { SentenceToneGraph } from '@/speech/SentenceToneGraph';
import { CELL_PLOT_INSET, normalizedMine, PAUSE_WIDTH, pitchSignal, toneReference } from '@/speech/sentenceToneGraph';

const base = perceivedAnalysis.data;
const point = (t: number, y = 0) => ({ timestamp_seconds: t, normalized_semitones: y });
function fixture(gap = 0) {
  return { ...base, duration_seconds: 3 + gap, syllables: [
    { ...base.syllables[0]!, characters: '去', start_seconds: 0, end_seconds: .25 },
    { ...base.syllables[1]!, characters: '吧', start_seconds: .25 + gap, end_seconds: 2.25 + gap },
  ], tone_graph: { ...base.tone_graph!, mine: { segments: [
    [point(0, -2), point(.05, -1)], [point(.2, 0)],
    [point(.25 + gap, -2), point(1.25 + gap, 2)], [point(2.25 + gap, 3)],
  ] } } };
}

it('normalizes unequal durations into equal cells without mutating timestamps or pitch', () => {
  const data = fixture(), before = JSON.stringify(data), mine = normalizedMine(data);
  expect(mine.regions.map(r => r.end-r.start)).toEqual([1, 1]);
  expect(mine.segments.flat().map(p => p.timestamp_seconds)).toEqual([0, .05, .2, .25, 1.25]);
  expect(mine.segments.flat().map(p => p.position)).toEqual([.12, .272, .7280000000000001, 1.12, 1.5]);
  expect(JSON.stringify(data)).toBe(before);
  const elapsed = contourGeometry(data.tone_graph.mine.segments, 225, 100, [-3, 3], 0, 2.25);
  expect(elapsed[2]![0]!.x).toBe(25);
  expect(elapsed[3]![0]!.x).toBe(225); // Final endpoint is still real-time evidence.
});

it('compresses long silence to a fixed separator and preserves short gaps without a pause marker', () => {
  const short = normalizedMine(fixture(.05)), threshold = normalizedMine(fixture(.3));
  expect(short.pauses).toEqual([]);
  expect(threshold.pauses).toEqual([1 + PAUSE_WIDTH / 2]);
  expect(normalizedMine(fixture(1)).regions).toEqual(normalizedMine(fixture(10)).regions);
  expect(threshold.extent).toBe(2 + PAUSE_WIDTH);
  const exact = fixture();
  exact.syllables[0]!.end_seconds = .4;
  exact.syllables[1]!.start_seconds = .7;
  expect(normalizedMine(exact).pauses).toHaveLength(1);
  exact.syllables[1]!.start_seconds = .6999999;
  expect(normalizedMine(exact).pauses).toHaveLength(0);
});

it('preserves internal evidence islands, singleton points and a shared utterance Y transform', () => {
  const mine = normalizedMine(fixture()), geometry = normalizedGeometry(mine, 200, 120, [-3, 3]);
  expect(geometry.map(s => s.length)).toEqual([2, 1, 2]);
  expect(geometry[0]!.at(-1)!.x).toBeCloseTo(27.2);
  expect(geometry[1]![0]!.x).toBeCloseTo(72.8); // No line bridges the internal gap.
  expect(geometry[0]![0]!.y).toBe(geometry[2]![0]!.y); // Same -2 st in both cells.
  const smallRise = Math.abs(geometry[0]![1]!.y-geometry[0]![0]!.y);
  const largeRise = Math.abs(geometry[2]![1]!.y-geometry[2]![0]!.y);
  expect(largeRise).toBe(smallRise * 4);
});

it('gives a shared boundary to the next unit once and excludes every final endpoint from cells', () => {
  const data = fixture();
  data.tone_graph.mine.segments = [[point(.249), point(.25), point(.251), point(2.25)]];
  const mine = normalizedMine(data);
  expect(mine.segments.map(s => s.map(p => p.timestamp_seconds))).toEqual([[.249], [.25, .251]]);
  expect(mine.segments[0]![0]!.position).toBeLessThan(1);
  expect(mine.segments[1]![0]!.position).toBe(1 + CELL_PLOT_INSET);
  expect(new Set(mine.segments.flat().map(p => p.timestamp_seconds)).size).toBe(3);
  expect(data.tone_graph.mine.segments[0]!.at(-1)!.timestamp_seconds).toBe(2.25);
});

it('does not assign inter-syllable pitch to either cell or invent evidence for missing cells', () => {
  const data = fixture(1);
  data.tone_graph.mine.segments = [[point(.1)], [point(.25), point(.5)]];
  expect(normalizedMine(data).segments.flat().map(p => p.timestamp_seconds)).toEqual([.1]);
  expect(normalizedMine(data).regions).toHaveLength(2);
  data.tone_graph.mine.segments = [];
  expect(normalizedMine(data).segments).toEqual([]);
});

it('assigns a tolerated sub-millisecond overlap only to the later-starting unit', () => {
  const data = fixture();
  data.syllables[1]!.start_seconds = .2495;
  data.tone_graph.mine.segments = [[point(.249), point(.2495), point(.2499), point(.25)]];
  expect(normalizedMine(data).segments.map(s => s.map(p => p.timestamp_seconds))).toEqual([
    [.249], [.2495, .2499, .25],
  ]);
  data.tone_graph.raw = Array.from({ length: 5 }, (_, i) => ({
    timestamp_seconds: .2495 + i * .0001, f0_hz: 200, retained: true,
  }));
  expect(pitchSignal(data, 0, .25, 0)).toBe('Pitch signal: Not enough');
  expect(pitchSignal(data, .2495, 2.25, 1)).toBe('Pitch signal: Clear');
});

it('the saved 去吧 timestamp excerpt keeps every 去 point within 去 and leaves 吧 empty', () => {
  const data = fixture();
  data.syllables[0] = { ...data.syllables[0]!, start_seconds: .66, end_seconds: .78 };
  data.syllables[1] = { ...data.syllables[1]!, start_seconds: .79, end_seconds: 1.07 };
  data.tone_graph.mine.segments = [[.703, .713, .723, .743, .753, .773].map(t => point(t))];
  const mine = normalizedMine(data);
  expect(mine.segments).toHaveLength(1);
  expect(mine.segments[0]!.every(p => p.position >= 0 && p.position < 1)).toBe(true);
  expect(mine.segments[0]!.at(-1)!.position).toBeCloseTo(.12 + .76 * (.773-.66)/(.78-.66));
  expect(mine.pauses).toEqual([]);
});

it('keeps untimed and synthetic characters in cells without fabricating timing or pauses', () => {
  const data = { ...base, syllables: [base.syllables[0]!,
    { ...base.syllables[1]!, start_seconds: null, end_seconds: null },
    { ...base.syllables[1]!, index: 2, start_seconds: 5, end_seconds: 6 }] };
  expect(normalizedMine(data).regions.map(r => r.index)).toEqual([0, 1, 2]);
  expect(normalizedMine(data).pauses).toEqual([]);
  expect(normalizedMine({ ...data, alignment_status: 'synthetic' }).regions).toHaveLength(3);
  expect(normalizedMine({ ...data, alignment_status: 'synthetic' }).segments).toEqual([]);
});

it('retains lexical T3 for unresolved connected realization and reserves ? for unresolved readings', () => {
  const syllable = { ...base.syllables[0]!, pinyin: 'wǒ', lexical_tone: 3 as const, expected_surface_tone: null };
  expect(toneReference(syllable)).toMatchObject({ label: 'T3*', lexicalFallback: true });
  expect(toneReference({ ...syllable, pinyin: null, reading_source: 'unresolved' }).label).toBe('?');
  expect(toneReference({ ...syllable, expected_surface_tone: 2 }).label).toBe('T2');
  expect(toneReference({ ...syllable, lexical_tone: 0, expected_surface_tone: 0 }).label).toBe('N');
});

it('never lets lexical/contextual expectations change measured geometry or pitch signal', () => {
  const data = fixture(), mine = normalizedMine(data), signal = pitchSignal(data);
  for (const tone of [0, 1, 2, 3, 4, null] as const) {
    const changed = { ...data, syllables: data.syllables.map(s => ({ ...s, lexical_tone: tone, expected_surface_tone: tone })) };
    expect(normalizedMine(changed)).toEqual(mine);
    expect(pitchSignal(changed)).toBe(signal);
  }
  expect(pitchSignal(base, .1, .15)).toBe('Pitch signal: Clear');
  expect(pitchSignal(base)).toBe('Pitch signal: Limited');
  expect(pitchSignal(base, .15, .6)).toBe('Pitch signal: Not enough');
});

it('renders equal cell widths, a pause marker, quiet default cells and original detail/raw time', async () => {
  const data = fixture(1);
  data.syllables[0] = { ...data.syllables[0]!, pinyin: 'wǒ', lexical_tone: 3, expected_surface_tone: null };
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SentenceToneGraph, { data })); });
  try {
    const a = renderer.root.findByProps({ testID: 'character-unit-0' });
    const b = renderer.root.findByProps({ testID: 'character-unit-1' });
    expect(StyleSheet.flatten(a.props.style).width).toBe(StyleSheet.flatten(b.props.style).width);
    expect(renderer.root.findByProps({ testID: 'pitch-pause' })).toBeTruthy();
    const text = renderer.root.findAllByType(Text).map(n => n.props.children).flat().join(' ');
    expect(text).not.toMatch(/T[1-4]/); expect(text).not.toContain('Pitch signal:');
    expect(text).not.toMatch(/\bGood\b|\bPartial\b|\bSparse\b|Perfect|Correct|Wrong|Tone score/);
    expect(text).not.toContain('wǒ'); // Pinyin is available on tap, not duplicated inline.
    await act(async () => a.props.onPress());
    expect(JSON.stringify(renderer.toJSON())).toContain('Contextual realization: unresolved');
    const tap = async (label: string) => act(async () => renderer.root.findByProps({ accessibilityLabel: label }).props.onPress());
    await tap('More detail');
    expect(renderer.root.findByType(PitchPlot).props.xLayout).toBeUndefined();
    expect(renderer.root.findByType(PitchPlot).props.display).toBe(data.tone_graph.filtered);
    expect(StyleSheet.flatten(renderer.root.findByProps({ testID: 'character-unit-1' }).props.style).width / StyleSheet.flatten(renderer.root.findByProps({ testID: 'character-unit-0' }).props.style).width).toBeCloseTo(8);
    await tap('Raw');
    const raw = renderer.root.findAllByType(PitchPlot)[1]!.props;
    expect(raw.xLayout).toBeUndefined();
    expect(raw.durationSeconds).toBe(data.duration_seconds);
    expect(raw.user[0].timestamp_seconds).toBe(.1);
  } finally { await act(async () => renderer.unmount()); }
});

it('draws a single supported point as a dot without a line', async () => {
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(ContourLines, {
    segments: [[{ x: 20, y: 30, confidence: 1 }]],
  })); });
  expect(renderer.root.findAllByProps({ testID: 'contour-line' })).toHaveLength(0);
  expect(renderer.toJSON()).toBeTruthy();
  await act(async () => renderer.unmount());
});

it('keeps trailing 雨 and 伞 in large cells beneath their empty pitch regions', async () => {
  const syllables = Array.from('我想买五把雨伞').map((characters, index) => ({
    ...base.syllables[0]!, characters, index, character_start: index, character_end: index + 1,
    lexical_tone: 3 as const, expected_surface_tone: null,
    start_seconds: index < 5 ? index * .2 : null, end_seconds: index < 5 ? index * .2 + .19 : null,
  }));
  const data = { ...base, syllables };
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SentenceToneGraph, { data })); });
  const plot = renderer.root.findByType(PitchPlot), layout = plot.props.xLayout;
  expect(layout.regions.map((r: { label: string }) => r.label).join('')).toBe('我想买五把雨伞');
  expect(layout.extent).toBe(7);
  expect(layout.segments.flat().every((p: { position: number }) => p.position < 5)).toBe(true);
  for (const index of [5, 6]) {
    const cell = renderer.root.findByProps({ testID: `character-unit-${index}` });
    const texts = cell.findAllByType(Text);
    expect(texts[0]!.props.children).toBe(syllables[index]!.characters);
    expect(StyleSheet.flatten(texts[0]!.props.style).fontSize).toBeGreaterThanOrEqual(32);
    expect(texts).toHaveLength(1);
    const style = StyleSheet.flatten(cell.props.style);
    expect(style.width).toBeGreaterThanOrEqual(96);
    expect(style.left + style.width).toBeLessThanOrEqual(style.width * 7 + 8);
  }
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree.indexOf('Relative pitch contour')).toBeLessThan(tree.indexOf('character-unit-0'));
  expect(tree).not.toMatch(/Pitch signal:|Equal syllable widths|relative pitch \(st\)|syllables →|Swipe sideways|Syllable timing is unavailable|Tap a character/);
  await act(async () => renderer.root.findByProps({ testID: 'character-unit-6' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('Timing unavailable');
  expect(renderer.root.findAllByType(Text).map(n => n.props.children).flat().join('')).toContain('Lexical tone: T3');
  await act(async () => renderer.unmount());
});

it('centers each plot box above its character without recentering measured onsets', () => {
  const data = fixture();
  data.tone_graph.mine.segments = [[point(.125, 1), point(.2, 2)], [point(1.25, 1)]];
  const layout = normalizedMine(data), geometry = normalizedGeometry(layout, 200, 100, [-3, 3]);
  expect(layout.regions.map(r => (r.start + r.end) / 2)).toEqual([.5, 1.5]);
  expect(geometry[0]![0]!.x).toBeCloseTo(50); // Halfway through first syllable.
  expect(geometry[0]![1]!.x).toBeCloseTo(72.8); // Late evidence remains late.
  expect(geometry[1]![0]!.x).toBeCloseTo(150);
  expect(geometry[0]![0]!.y).toBe(geometry[1]![0]!.y);
  const paddedStart = CELL_PLOT_INSET, paddedEnd = 1 - CELL_PLOT_INSET;
  expect((paddedStart + paddedEnd) / 2).toBe(.5);
});

it('keeps perceived 贵州 and arbitrary measurements independent of reference T4/T1', async () => {
  const data = fixture();
  data.syllables = data.syllables.map((s, i) => ({ ...s, characters: ['贵', '州'][i]!,
    pinyin: ['guì', 'zhōu'][i]!, lexical_tone: i === 0 ? 4 : 1, expected_surface_tone: i === 0 ? 4 : 1 }));
  for (const values of [[-2, 2], [2, -2], [0, 0]]) {
    data.tone_graph.mine.segments = [[point(.05, values[0]), point(.2, values[1])],
      [point(.5, values[0]), point(1, values[1])]];
    let renderer!: ReactTestRenderer;
    await act(async () => { renderer = create(React.createElement(SentenceToneGraph, { data })); });
    expect(renderer.root.findByType(PitchPlot).props.xLayout.regions.map((r: { label: string }) => r.label)).toEqual(['贵', '州']);
    const visible = () => renderer.root.findAllByType(Text).map(n => n.props.children).flat().join(' ');
    expect(visible()).not.toMatch(/T[1-4]|Detected|Correct|Wrong/);
    await act(async () => renderer.root.findByProps({ testID: 'character-unit-0' }).props.onPress());
    expect(visible()).toContain('Reference tone: T4');
    expect(visible()).toContain('Pitch gestures are experimental');
    await act(async () => renderer.root.findByProps({ testID: 'character-unit-1' }).props.onPress());
    expect(visible()).toContain('Reference tone: T1');
    expect(visible()).not.toMatch(/Detected tone:|Correct|Wrong/);
    await act(async () => renderer.unmount());
  }
});

it.each(['sufficient', 'incomplete', 'unstable', 'insufficient'] as const)('keeps %s evidence neutral and reports backend eligibility in detail', async state => {
  const data = fixture();
  data.syllables[0] = { ...data.syllables[0]!, characters: '苹', pinyin: 'píng', lexical_tone: 2, expected_surface_tone: 2,
    pitch_eligibility: { state }, tone_comparison_policy: 'experimental',
    observed_gesture: 'rising', observed_confidence: 'moderate',
    observed_contour: { classification: '2-like', confidence: 'moderate', reason: 'acoustic_shape_only', features: {} } };
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SentenceToneGraph, { data })); });
  try {
    const text = () => renderer.root.findAllByType(Text).map(n => n.props.children).flat().join(' ');
    const treatment = renderer.root.findByProps({ testID: 'tone-cell-state-0' });
    expect(treatment.props.accessibilityValue.text).toBe('uncertain');
    expect(StyleSheet.flatten(treatment.props.style)).toMatchObject({ top: 0, bottom: 0, position: 'absolute' });
    expect(renderer.root.findByType(PitchPlot).props.transparent).toBe(true);
    expect(text()).not.toMatch(/T[1-4]|Reference tone|Observed pitch/);
    const cell = renderer.root.findByProps({ testID: 'character-unit-0' });
    expect(cell.props.accessibilityLabel).toContain('tone gesture uncertain');
    await act(async () => cell.props.onPress());
    expect(text()).toContain(state === 'unstable' ? 'Pitch tracking: Uncertain' : `Observed pitch: ${state === 'incomplete' ? 'Incomplete evidence' : state === 'sufficient' ? 'rising' : 'unclear'}`);
    expect(text()).toContain('Reference tone: T2 (rising)');
    expect(text()).toContain(`Pitch evidence: ${state}`);
    expect(text()).toContain('Tone gesture:  uncertain');
    expect(text()).not.toMatch(/Detected tone:|Correct pronunciation|Wrong pronunciation/);
  } finally { await act(async () => renderer.unmount()); }
});

it('shows one unsplit grouped word contour, both characters, no individual grade, and real elapsed detail', async () => {
  const data = { ...fixture(), syllables: [] as typeof base.syllables, timing_groups: [{ character_start: 0, character_end: 2, text: '雨伞', start_seconds: .25, end_seconds: 2.25,
    source: 'azure_word' as const, timing_evidence_id: 'word-evidence' }] };
  data.syllables = fixture().syllables.map((s, i) => ({ ...s, characters: ['雨', '伞'][i]!, character_start: i, character_end: i+1,
    start_seconds: null, end_seconds: null, observed_gesture: 'rising', observed_confidence: 'moderate' }));
  data.tone_graph.mine.segments = [[point(.25, -2), point(.75, 0), point(1.25, 2), point(2.24, -1)]];
  const before = JSON.stringify(data), layout = normalizedMine(data);
  expect(layout.regions.map(r => r.label)).toEqual(['雨', '伞']);
  expect(layout.evidenceRegions).toEqual([{ index: 0, label: '雨伞', start: 0, end: 2 }]);
  expect(layout.segments).toHaveLength(1);
  expect(layout.segments[0]!.map(p => p.timestamp_seconds)).toEqual([.25, .75, 1.25, 2.24]);
  expect(layout.segments[0]![0]!.position).toBe(.12);
  expect(layout.segments[0]![2]!.position).toBe(1); // Mid-word measurement, no boundary/split.
  expect(layout.segments[0]!.at(-1)!.position).toBeCloseTo(1.8712);
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(SentenceToneGraph, { data })); });
  try {
    expect(renderer.root.findByProps({ testID: 'tone-cell-state-0' }).props.accessibilityValue.text).toBe('grouped_evidence');
    expect(renderer.root.findAllByProps({ testID: 'tone-cell-state-1' })).toHaveLength(0);
    for (const i of [0, 1]) {
      const cell = renderer.root.findByProps({ testID: `character-unit-${i}` });
      expect(cell.props.accessibilityLabel).toContain('tone gesture uncertain');
      expect(cell.props.accessibilityLabel).toContain('no individual attribution');
      await act(async () => cell.props.onPress());
      const text = renderer.root.findAllByType(Text).map(n => n.props.children).flat().join(' ');
      expect(text).toContain('grouped word pitch');
      expect(text).toContain('No individual tone comparison');
    }
    await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More detail' }).props.onPress());
    const plot = renderer.root.findByType(PitchPlot).props;
    expect(plot.xLayout).toBeUndefined();
    expect(plot.display).toBe(data.tone_graph.filtered);
    expect(plot.regions).toEqual([{ label: '雨伞', start_seconds: .25, end_seconds: 2.25 }]);
    expect(renderer.root.findByProps({ testID: 'timing-group-0' }).props.accessibilityLabel).toContain('tone gesture uncertain');
    expect(JSON.stringify(data)).toBe(before);
  } finally { await act(async () => renderer.unmount()); }
  expect(normalizedMine({ ...data, alignment_status: 'synthetic' }).segments).toEqual([]);
});
