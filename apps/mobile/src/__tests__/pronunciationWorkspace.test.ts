import React from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import { ExactPlaybackButton } from '@/audio/ExactPlaybackButton';
import { registerPlayback } from '@/audio/session';
import { PitchPlot } from '@/components/PitchPlot';
import { PronunciationWorkspace } from '@/speech/PronunciationWorkspace';
import { agreementLabels, defaultUnit, pronunciationUnits, unitPitch } from '@/speech/pronunciationWorkspace';
import { SpeechEvidence } from '@/speech/SpeechEvidence';
import type { PerceivedSpeechAnalysis } from '@/api/types';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));
const analysis: PerceivedSpeechAnalysis = { ...perceivedAnalysis, data: { ...perceivedAnalysis.data,
  duration_seconds: 4,
  syllables: Array.from('我想买五把雨伞').map((characters, index) => ({ ...perceivedAnalysis.data.syllables[0]!,
    index, characters, character_start: index, character_end: index + 1,
    start_seconds: index < 5 ? index * .5 : null, end_seconds: index < 5 ? (index + 1) * .5 : null,
    pitch_eligibility: { state: 'sufficient' }, observed_gesture: 'rising' })),
  timing_groups: [{ text: '雨伞', character_start: 5, character_end: 7, start_seconds: 2.5, end_seconds: 4,
    timing_evidence_id: 'group-evidence', pitch_eligibility: { state: 'unstable' } }],
} };
let renderer: ReactTestRenderer;
async function mount(value = analysis) {
  await act(async () => { renderer = create(React.createElement(PronunciationWorkspace, { analysis: value })); });
}
async function select(index: number) {
  await act(async () => renderer.root.findByProps({ testID: `pronunciation-unit-${index}` }).props.onPress());
}
afterEach(async () => { if (renderer) await act(async () => renderer.unmount()); });

const physicalProjection = require('../../../../services/api/tests/fixtures/pitch_projection_89cee47e.json') as {
  data: PerceivedSpeechAnalysis['data'];
  track: { evidence_id: string; frames: { timestamp_seconds: number; selected_f0_hz: number | null }[] };
};

it('replays the physical 这/个 evidence through selected graph, playback, and repeated unit switches', async () => {
  const value = { ...perceivedAnalysis, data: physicalProjection.data };
  await mount(value);
  for (const index of [3, 4, 3, 4]) {
    await select(index);
    const s = value.data.syllables[index]!;
    const graph = renderer.root.findAllByType(PitchPlot)[0]?.props;
    const playback = renderer.root.findByType(ExactPlaybackButton).props;
    if (index === 3) expect([graph?.startSeconds, graph?.durationSeconds]).toEqual([s.start_seconds, s.end_seconds]);
    else expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(0);
    expect([playback.start, playback.end, playback.text]).toEqual([s.start_seconds, s.end_seconds, s.characters]);
    const indices = (graph?.display.segments.flat() ?? []).map((p: { timestamp_seconds: number }) =>
      physicalProjection.track.frames.findIndex(f => f.timestamp_seconds === p.timestamp_seconds));
    const expected = index === 3 ? [...Array.from({ length: 15 }, (_, i) => 245 + i), 263, 264, 265, 266, 267] : [];
    expect(indices).toEqual(expected);
    expect(s.pitch_projection?.track_evidence_id).toBe(physicalProjection.track.evidence_id);
    expect(indices.every((i: number) => s.pitch_projection?.frame_indices?.includes(i))).toBe(true);
  }
  expect(JSON.stringify(renderer.toJSON())).toContain("Pitch couldn't be measured reliably.");
});

it('exposes B evidence after a gap and never leaks it into A, even when B is strictly ineligible', async () => {
  const data = JSON.parse(JSON.stringify(physicalProjection.data)) as PerceivedSpeechAnalysis['data'];
  // Deterministic counterfactual fixture, not a change to the physical recording.
  const b = [{ timestamp_seconds: 2.80, normalized_semitones: -2 },
    { timestamp_seconds: 2.81, normalized_semitones: -1 },
    { timestamp_seconds: 2.82, normalized_semitones: 0 }];
  data.tone_graph!.filtered.segments!.push(b);
  const before = JSON.stringify(data);
  await mount({ ...perceivedAnalysis, data });
  await select(3);
  expect(renderer.root.findByType(PitchPlot).props.display.segments.flat()
    .every((p: { timestamp_seconds: number }) => p.timestamp_seconds < 2.73)).toBe(true);
  await select(4);
  expect(renderer.root.findByType(PitchPlot).props.display.segments).toEqual([b]);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ start: 2.74, end: 3.04, text: '个' });
  await select(3);
  expect(renderer.root.findByType(PitchPlot).props.display.segments).not.toContainEqual(b);
  expect(JSON.stringify(data)).toBe(before);
});

it('shows the physical 我 dip and rise while preserving the old diagnostic under Technical details', async () => {
  const value = { ...perceivedAnalysis, data: physicalProjection.data };
  const before = JSON.stringify(value);
  await mount(value); await select(0);
  expect(value.data.syllables[0]!.characters).toBe('我');
  expect(value.data.syllables[0]!.observed_gesture).toBe('level');
  expect(JSON.stringify(renderer.toJSON())).toContain('Most like Tone 3');
  expect(renderer.root.findByType(PitchPlot).props.showAxes).toBe(false);
  expect(renderer.root.findByType(PitchPlot).props.display.segments.flat().length).toBeGreaterThan(0);
  expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('我');
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Mostly level|experimental|Measurement:|Gesture unavailable|Pitch detail is limited/i);
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-0' }).props.accessibilityLabel).toBe('我, pronunciation chunk, Pitch acceptable');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('Dip and rise');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Measurement evidence:');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Technical details' }).props.onPress());
  const details = JSON.stringify(renderer.toJSON());
  expect(details).toContain('Observed gesture: Mostly level · experimental');
  expect(details).toContain('Measurement: clear');
  expect(details).toContain('Measurement evidence: sufficient');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Raw' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('Raw tracker evidence · developer detail');
  expect(JSON.stringify(renderer.toJSON())).toContain('Exclusion reasons:');
  expect(JSON.stringify(value)).toBe(before);
});

it.each(['incomplete', 'unstable', 'insufficient'] as const)('keeps a usable graph quiet despite strict %s eligibility', async state => {
  const value = { ...perceivedAnalysis, data: { ...perceivedAnalysis.data,
    syllables: perceivedAnalysis.data.syllables.map(s => ({ ...s,
      pitch_eligibility: { state, reasons: ['raw_pitch_discontinuity'] } })),
  } };
  await mount(value); await select(0);
  expect(renderer.root.findByType(PitchPlot).props.display.segments.flat()).toHaveLength(5);
  expect(renderer.root.findByType(ExactPlaybackButton)).toBeTruthy();
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Measurement:|raw_pitch_discontinuity|experimental|Pitch detail is limited|couldn't be measured/i);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Measurement evidence:');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Technical details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain(`Measurement evidence: ${state}`);
  expect(JSON.stringify(renderer.toJSON())).toContain('raw_pitch_discontinuity');
});

it('announces pitch unavailability for the timed physical 个 without an empty graph or missing-speech claim', async () => {
  await mount({ ...perceivedAnalysis, data: physicalProjection.data }); await select(4);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(0);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '个', start: 2.74, end: 3.04 });
  const message = renderer.root.findAllByProps({ accessibilityRole: 'text' })
    .find(n => n.props.children === "Pitch couldn't be measured reliably.");
  expect(message).toBeTruthy();
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/not enough|not heard|didn't hear|no speech|Measurement:|Gesture unavailable/i);
});

it('keeps perceived 贵州 ownership independent of target 广州 and resets selection for a new analysis', async () => {
  const perceived = { ...perceivedAnalysis, alignment_reference_text: '贵州', data: { ...perceivedAnalysis.data,
    syllables: perceivedAnalysis.data.syllables.map((s, i) => ({ ...s, characters: ['贵', '州'][i]! })) } };
  const make = (id: string, intendedText = '广州') => React.createElement(SpeechEvidence, { heard: '贵州', intendedText,
    analysis: { utteranceId: id, state: 'ready' as const, perceived: { ...perceived, id, utterance_id: id } } });
  await act(async () => { renderer = create(make('first')); });
  await select(1);
  const selected = renderer.root.findByType(PitchPlot).props.display;
  await act(async () => { renderer.update(make('first', '北京')); });
  expect(renderer.root.findByType(PitchPlot).props.display).toEqual(selected);
  expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('州');
  await act(async () => { renderer.update(make('second')); });
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-0' }).props.accessibilityState.selected).toBe(true);
  await select(1);
  expect(renderer.root.findByType(PitchPlot).props.display).toEqual(selected);
});

it('wraps in sentence order with 44px targets, no horizontal scroll, and one atomic 雨伞 group', async () => {
  await mount();
  const overview = renderer.root.findByProps({ testID: 'perceived-sentence-overview' });
  expect(StyleSheet.flatten(overview.props.style)).toMatchObject({ flexDirection: 'row', flexWrap: 'wrap' });
  expect(renderer.root.findAllByType(ScrollView)).toHaveLength(0);
  const buttons = [0, 1, 2, 3, 4, 5].map(i => overview.findByProps({ testID: `pronunciation-unit-${i}` }));
  expect(buttons.map(b => b.props.accessibilityLabel.split(',')[0])).toEqual(['我', '想', '买', '五', '把', '雨伞']);
  for (const button of buttons) expect(StyleSheet.flatten(button.props.style)).toMatchObject({ minWidth: 44, minHeight: 48, flexShrink: 0 });
  await select(5);
  expect(renderer.root.findAllByType(ExactPlaybackButton)).toHaveLength(1);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ text: '雨伞', start: 2.5, end: 4 });
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-5' }).props.accessibilityLabel).toContain('grouped timing');
  expect(renderer.root.findAllByProps({ testID: 'pronunciation-unit-6' })).toHaveLength(0);
});

it('replaces one selected panel, exposes selection without color, and stops existing playback', async () => {
  await mount();
  const stop = jest.fn(), unregister = registerPlayback(stop);
  await select(1);
  expect(stop).toHaveBeenCalledTimes(1);
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-1' }).props.accessibilityState).toEqual({ selected: true });
  expect(StyleSheet.flatten(renderer.root.findByProps({ testID: 'pronunciation-unit-1' }).props.style).borderBottomWidth).toBe(4);
  await select(2);
  expect(renderer.root.findAllByProps({ testID: 'selected-pronunciation-detail' }).filter(n => typeof n.type !== 'string')).toHaveLength(1);
  expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('买');
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-1' }).props.accessibilityState.selected).toBe(false);
  unregister();
});

it.each(['sufficient', 'incomplete', 'unstable', 'insufficient'] as const)('keeps %s evidence neutral even with a claimed future policy', async state => {
  const value = { ...analysis, data: { ...analysis.data, syllables: analysis.data.syllables.map(s => ({ ...s,
    tone_comparison_policy: 'trusted', observed_confidence: 'moderate' as const, pitch_eligibility: { state } })) } };
  expect(pronunciationUnits(value.data).every(u => u.agreement === 'UNAVAILABLE')).toBe(true);
  await mount(value); await select(0);
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).not.toMatch(/Strong pitch match|Partial pitch match|Pitch differs|detected Tone|\d+%|tone score/i);
  expect(tree).not.toMatch(/Rising|experimental|Measurement:|Gesture unavailable/i);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(1);
});

it('reserves four semantic labels but has no approved positive or negative mapping', () => {
  expect(agreementLabels).toEqual({ STRONG_MATCH: 'Strong pitch match', PARTIAL_OR_FLEXIBLE: 'Partial pitch match',
    CLEAR_DIFFERENCE: 'Pitch differs', UNAVAILABLE: 'Pitch comparison unavailable' });
  const units = pronunciationUnits(analysis.data);
  expect(defaultUnit(units)).toBe(units[0]!.id);
  expect(defaultUnit(units.map(u => ({ ...u, eligibility: { state: 'unstable' } })))).toBe(units[0]!.id);
  expect(defaultUnit([])).toBeNull();
  expect(defaultUnit(units.map((u, i) => ({ ...u, agreement: i === 2 ? 'PARTIAL_OR_FLEXIBLE' : 'UNAVAILABLE' })))).toBe(units[2]!.id);
});

it('projects immutable half-open timestamps and gaps on a shared attempt scale', () => {
  const data = perceivedAnalysis.data, before = JSON.stringify(data), units = pronunciationUnits(data);
  const first = unitPitch(data, units[0]!), second = unitPitch(data, units[1]!);
  expect(first.segments).toEqual([data.tone_graph!.filtered.segments![0]]);
  expect(second.segments).toEqual([data.tone_graph!.filtered.segments![1]]);
  expect(first.minimum_semitones).toBe(second.minimum_semitones);
  expect(first.maximum_semitones).toBe(second.maximum_semitones);
  expect(JSON.stringify(data)).toBe(before);
});

it.each(['unavailable', 'synthetic'] as const)('has no timing controls or segment playback when timing is %s', async alignment_status => {
  await mount({ ...analysis, data: { ...analysis.data, alignment_status } });
  expect(renderer.root.findAllByType(ExactPlaybackButton)).toHaveLength(0);
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(0);
  expect(JSON.stringify(renderer.toJSON())).toContain('whole recording');
  expect(renderer.root.findByProps({ accessibilityLabel: 'More details' })).toBeTruthy();
});

it('keeps missing readings and empty pitch missing, with exact timed audio still accessible', async () => {
  await mount({ ...analysis, data: { ...analysis.data, tone_graph: null, measured_pitch: [], syllables: analysis.data.syllables.map(s => ({
    ...s, reading_source: 'unresolved', pinyin: null, pitch_eligibility: { state: 'insufficient' },
  })) } });
  await select(0);
  expect(JSON.stringify(renderer.toJSON())).toContain('Reading unresolved');
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(0);
  expect(JSON.stringify(renderer.toJSON())).toContain("Pitch couldn't be measured reliably.");
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ start: 0, end: .5 });
});

it('conversation stays collapsed until explicitly opened and full utterance details are optional', async () => {
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, { compact: true, heard: '我想买五把雨伞',
    analysis: { utteranceId: analysis.utterance_id, state: 'ready', perceived: analysis } })); });
  expect(renderer.root.findAllByType(PronunciationWorkspace)).toHaveLength(0);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Explore pronunciation' }).props.onPress());
  expect(renderer.root.findAllByType(ScrollView)).toHaveLength(0);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Measurement evidence:');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Technical details' }).props.onPress());
  expect(renderer.root.findByProps({ accessibilityLabel: 'Sentence pitch timeline' })).toBeTruthy();
});

it('keeps the saved d47274bc control untimed and the saved 40357072 雨伞 span atomic', async () => {
  // Timing/identity-only extracts from the frozen six-take review; no synthesized timing.
  const controls = require('./fixtures/workspaceTimingControls.json') as { id: string; analysis_id: string; heard: string; data: PerceivedSpeechAnalysis['data'] }[];
  const missing = controls.find(r => r.id === 'd47274bc')!;
  expect(pronunciationUnits(missing.data)).toEqual([]);
  await act(async () => { renderer = create(React.createElement(SpeechEvidence, { heard: missing.heard,
    recordingUrl: '/v1/utterances/d47274bc/audio', analysis: { utteranceId: 'd47274bc', state: 'ready',
      perceived: { ...perceivedAnalysis, id: missing.analysis_id, data: missing.data } } })); });
  expect(JSON.stringify(renderer.toJSON())).toContain(missing.heard);
  expect(renderer.root.findAllByType(ExactPlaybackButton)).toHaveLength(0);
  const grouped = controls.find(r => r.id === '40357072')!;
  const units = pronunciationUnits(grouped.data);
  expect(units.map(u => u.text)).toEqual(['我', '想', '买', '五', '把', '雨伞']);
  expect(units.at(-1)).toMatchObject({ text: '雨伞', start: 3.56, end: 4.87, grouped: true });
});

it('distinguishes measurement uncertainty from gesture and keeps diagnostic reasons in the dialog', async () => {
  await mount({ ...analysis, data: { ...analysis.data, syllables: analysis.data.syllables.map(s => ({ ...s,
    pitch_eligibility: { state: 'unstable', reasons: ['raw_pitch_discontinuity'] }, observed_gesture: 'dipping',
  })) } });
  await select(0);
  const tree = JSON.stringify(renderer.toJSON());
  expect(renderer.root.findAllByType(PitchPlot)).toHaveLength(1);
  expect(tree).not.toMatch(/Measurement:|Some pitch measurements disagree|Gesture unavailable|Pitch detail is limited/);
  expect(tree).not.toMatch(/Pitch evidence unstable|raw_pitch_discontinuity|Dipping|Your pitch/);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'More details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Measurement evidence:');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Technical details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).toContain('raw_pitch_discontinuity');
  expect(JSON.stringify(renderer.toJSON())).toContain('Measurement evidence: unstable');
  expect(JSON.stringify(renderer.toJSON())).toContain('Measurement: mixed');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Close Full pitch details' }).props.onPress());
  expect(JSON.stringify(renderer.toJSON())).not.toContain('raw_pitch_discontinuity');
});
