import React from 'react';
import { StyleSheet } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { copy, freshToneAnalysis, replacePitch } from './toneFeedbackFixture';

import { PronunciationWorkspace } from '@/speech/PronunciationWorkspace';
import { PitchPlot } from '@/components/PitchPlot';
import { pitchGradePresentation } from '@/speech/learnerPitchGrade';
import type { PerceivedSpeechAnalysis } from '@/api/types';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));
let renderer: ReactTestRenderer;
afterEach(async () => { if (renderer) await act(async () => renderer.unmount()); });
async function mount(a: PerceivedSpeechAnalysis = freshToneAnalysis) {
  await act(async () => { renderer = create(React.createElement(PronunciationWorkspace, { analysis: a })); });
}
async function select(index: number) {
  await act(async () => renderer.root.findByProps({ testID: `pronunciation-unit-${index}` }).props.onPress());
}
async function press(label: string) {
  await act(async () => renderer.root.findByProps({ accessibilityLabel: label }).props.onPress());
}
const tree = () => JSON.stringify(renderer.toJSON());
it('shows raw-flagged 我 unavailable, confident weak T3 想 green and poor 买 unclear', async () => {
  await mount();
  for (const index of [0, 1]) {
    await select(index);
    expect(tree()).toContain(index === 0 ? 'Tone unclear' : 'Most like Tone 3');
    expect(renderer.root.findByProps({ testID: `pronunciation-unit-${index}` }).props.accessibilityLabel).toContain(index === 0 ? 'Pitch unavailable' : 'Pitch acceptable');
  }
  await select(2); expect(tree()).toContain('Tone unclear');
  expect(tree()).not.toContain('Most like Tone 3');
  expect(tree()).not.toMatch(/fits|margin|probability|experimental|Measurement evidence/);
  expect(renderer.root.findByType(PitchPlot).props).toMatchObject({ plotHeight: 96, showAxes: false });
});
it('exposes green 这个 and separate T4-like 这/unmeasured neutral 个 without implying independent green 个', async () => {
  await mount(); await select(3);
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-3' }).props.accessibilityLabel).toBe('这个, pronunciation chunk, Pitch acceptable');
  expect(tree()).not.toContain('Pitch detail is limited.');
  await press('More details');
  expect(tree()).toContain('Colors describe pitch agreement, not consonants, vowels, or overall pronunciation.');
  expect(tree()).toContain('Most like Tone 4');
  expect(tree()).not.toContain('Measurement evidence:');
  await act(async () => renderer.root.findByProps({ testID: 'chunk-constituent-4' }).props.onPress());
  const panel = renderer.root.findByProps({ testID: 'selected-constituent-detail' });
  expect(panel.findAllByType(PitchPlot)).toHaveLength(0);
  expect(tree()).toContain("Pitch couldn't be measured reliably.");
  expect(tree()).toContain('Neutral dependent; this does not veto');
  expect(tree()).not.toContain('Tone unclear');
  await press('Technical details');
  expect(tree()).toContain('Measurement evidence:');
  expect(tree()).toContain('neutral_unmeasured_nonveto');
});
it.each([
  [(x: number) => 4 * x, 'CLEAR_DIFFERENCE', 'Expected a fall; yours rose.'],
  [(x: number) => -.25 * x, 'STRONG_MATCH', 'Fall is a little weak.'],
  [undefined, 'UNAVAILABLE', "Pitch couldn't be measured reliably."],
] as const)('renders color with a distinct visible symbol and accessible pitch meaning', async (fn, state, message) => {
  const a = copy(freshToneAnalysis); replacePitch(a, 3, fn);
  await mount(a); await select(3);
  const presentation = pitchGradePresentation[state];
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-3' }).props.accessibilityLabel).toContain(presentation.label);
  const status = renderer.root.findAllByProps({ accessibilityLabel: presentation.label })
    .find(n => n.props.accessibilityRole === 'text')!;
  expect(StyleSheet.flatten(status.props.style).color).toBe(presentation.ink);
  expect(tree()).toContain(presentation.symbol);
  expect(tree()).toContain(message);
});

it('explains lexical family fallback without claiming a resolved surface tone', async () => {
  await mount(); await select(0); await press('More details');
  expect(tree()).toContain('Tone 3 family');
  expect(tree()).toContain('Connected-speech realization may vary here.');
  expect(tree()).not.toContain('Context unresolved');
});
it('shows positive contextual neutral acceptance even without a numbered-family winner', async () => {
  const a = copy(freshToneAnalysis); replacePitch(a, 4, x => 2.2 * (1 - Math.abs(x * 2 - 1)));
  await mount(a); await select(3); await press('More details');
  await act(async () => renderer.root.findByProps({ testID: 'chunk-constituent-4' }).props.onPress());
  const panel = renderer.root.findByProps({ testID: 'selected-constituent-detail' });
  expect(panel.findAllByProps({ accessibilityLabel: 'Pitch acceptable' }).length).toBeGreaterThan(0);
  expect(tree()).toContain('Neutral syllable plausibly realized in this chunk.');
});
