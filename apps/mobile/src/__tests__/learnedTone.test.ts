import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';
import { physicalChunkAnalysis } from './pronunciationChunkFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { ExactPlaybackButton } from '@/audio/ExactPlaybackButton';
import { registerPlayback } from '@/audio/session';
import { PitchPlot } from '@/components/PitchPlot';
import { gradeChunkPitch } from '@/speech/chunkPitchGrade';
import { learnedToneEvidence, toneRendering, workspaceChunkFeedback, workspaceExpectation } from '@/speech/learnedToneView';
import { pronunciationChunks } from '@/speech/pronunciationChunks';
import { PronunciationWorkspace } from '@/speech/PronunciationWorkspace';
import { submitSpeech, type SpeechCheckpoint, type SpeechWorkflowApi } from '@/speech/workflow';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));

function withLearned(base = perceivedAnalysis): PerceivedSpeechAnalysis {
  return { ...base, data: { ...base.data, dev_learned_tone: {
    expectation_basis: 'intended_target', target_text: base.alignment_reference_text, timings_ms: {}, runtime: { load_count: 1 },
    units: base.data.syllables.map(s => ({ index: s.index, characters: s.characters, target_pinyin: s.pinyin,
      lexical_tone: s.lexical_tone ?? null, expected_surface_tone: s.expected_surface_tone ?? null, surface_rule: s.surface_rule ?? null,
      heard_pinyin: s.pinyin, realization: { status: 'ok', prediction: 'T4', confidence: .999, azure_span: [s.start_seconds!, s.end_seconds!] },
      comparison: { state: s.expected_surface_tone === 0 ? 'neutral' : s.expected_surface_tone == null ? 'unresolved' : 'experimental_mismatch',
        correction: false, message: 'Experimental backend comparison' },
    })),
  } } };
}
function firstFeedback(value: PerceivedSpeechAnalysis) {
  return workspaceChunkFeedback(value, pronunciationChunks(value.data)[0]!);
}
let renderer: ReactTestRenderer;
async function mount(value = withLearned()) {
  await act(async () => { renderer = create(React.createElement(PronunciationWorkspace, {
    analysis: value, phraseActions: React.createElement(Text, { testID: 'phrase-action' }, 'Phrase action'),
  })); });
}
async function press(label: string) {
  await act(async () => renderer.root.findByProps({ accessibilityLabel: label }).props.onPress());
}
async function select(index: number) {
  await act(async () => renderer.root.findByProps({ testID: `pronunciation-unit-${index}` }).props.onPress());
}
afterEach(async () => { if (renderer) await act(async () => renderer.unmount()); });

it('restores compact chart styling, phrase actions, exact playback, selection and collapsed details', async () => {
  const value = withLearned();
  const before = JSON.stringify(value);
  await mount(value);
  expect(renderer.root.findByProps({ testID: 'pronunciation-workspace' })).toBeTruthy();
  expect(renderer.root.findAllByProps({ testID: 'learned-tone-workspace' })).toHaveLength(0);
  expect(renderer.root.findByProps({ testID: 'phrase-action' })).toBeTruthy();
  const chart = renderer.root.findByType(PitchPlot).props;
  expect(chart).toMatchObject({ showAxes: false, showPoints: true, plotHeight: 96, showMineLabel: false,
    startSeconds: 0, durationSeconds: .6 });
  expect(chart.display.segments).toEqual(perceivedAnalysis.data.tone_graph!.filtered.segments!.slice(0, 1));
  const button = renderer.root.findByProps({ testID: 'pronunciation-unit-0' });
  expect(StyleSheet.flatten(button.props.style)).toMatchObject({ minWidth: 44, minHeight: 48, borderBottomWidth: 4 });
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ start: 0, end: .6, text: '周' });
  const stop = jest.fn(), unregister = registerPlayback(stop);
  await select(1);
  expect(stop).toHaveBeenCalledTimes(1);
  expect(renderer.root.findByType(ExactPlaybackButton).props).toMatchObject({ start: .6, end: 1.2, text: '谋' });
  expect(renderer.root.findByType(PitchPlot).props.display.segments).toEqual(perceivedAnalysis.data.tone_graph!.filtered.segments!.slice(1));
  expect(JSON.stringify(renderer.toJSON())).toContain('Most like Tone 4');
  expect(JSON.stringify(renderer.toJSON())).not.toMatch(/Experimental tone realization|Dev evidence|confidence|HuBERT|accuracy|99.9/);
  unregister();
  expect(JSON.stringify(value)).toBe(before);
});

it('uses downstream comparison and never turns raw confidence or family mismatch into red', () => {
  const value = withLearned();
  const unit = value.data.dev_learned_tone!.units[0]!;
  for (const confidence of [.26, .999]) {
    unit.realization.confidence = confidence;
    expect(firstFeedback(value).grade.agreement).toBe('PARTIAL_OR_WEAK');
  }
  // This deliberate counterfactual proves the adapter consumes the supplied
  // downstream comparison, rather than computing equality from the class itself.
  unit.comparison.state = 'experimental_match';
  expect(firstFeedback(value).grade.agreement).toBe('STRONG_MATCH');
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('TONE_4');
});

it('keeps unresolved surface expectation gray despite a lexical fallback or claimed match', async () => {
  const value = withLearned();
  const unit = value.data.dev_learned_tone!.units[0]!;
  unit.expected_surface_tone = null;
  unit.comparison.state = 'experimental_match';
  expect(workspaceExpectation(value.data, value.data.syllables[0]!)).toMatchObject({ tone: null, basis: 'unresolved' });
  expect(firstFeedback(value).grade).toMatchObject({ agreement: 'UNAVAILABLE', coaching: null });
  await mount(value);
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain('Most like Tone 4');
  expect(tree).toContain('No correction.');
  expect(renderer.root.findByProps({ testID: 'selected-pronunciation-detail' }).findAllByType(Text)
    .map(n => n.props.children).join(' ')).not.toMatch(/Pitch acceptable|Pitch differs|Pitch may be off/);
  expect(renderer.root.findByProps({ testID: 'pronunciation-unit-0' }).props.accessibilityLabel).toContain('Pitch not judged');
});

it('keeps abstention gray with playable audio and measured pitch, never a deterministic fallback', async () => {
  const value = withLearned();
  const unit = value.data.dev_learned_tone!.units[0]!;
  unit.realization = { status: 'abstained', reason: 'continuity_guard', prediction: 'T4' };
  unit.comparison.state = 'insufficient';
  expect(firstFeedback(value).grade.agreement).toBe('UNAVAILABLE');
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('UNCLEAR');
  expect(toneRendering(value.data.dev_learned_tone!).heard).toContain('[unclear]');
  await mount(value);
  expect(renderer.root.findByType(PitchPlot)).toBeTruthy();
  expect(renderer.root.findByType(ExactPlaybackButton)).toBeTruthy();
  expect(JSON.stringify(renderer.toJSON())).toContain('Tone unclear');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Most like Tone 4');
});

it('preserves contextual neutral non-veto in the original 这个 chunk and constituent interaction', async () => {
  const value = withLearned(physicalChunkAnalysis());
  const neutral = value.data.dev_learned_tone!.units[4]!;
  neutral.realization = { status: 'abstained', reason: 'neutral_out_of_scope' };
  const chunk = pronunciationChunks(value.data).find(c => c.text === '这个')!;
  const feedback = workspaceChunkFeedback(value, chunk);
  expect(feedback.hasNeutralNonVeto).toBe(true);
  expect(feedback.constituents[1]!.grade.agreement).toBe('UNAVAILABLE');
  expect(feedback.grade.agreement).toBe('PARTIAL_OR_WEAK');
  expect(toneRendering(value.data.dev_learned_tone!).heard).toMatch(/ge$/);
  await mount(value); await select(3);
  expect(renderer.root.findByType(ExactPlaybackButton).props.text).toBe('这个');
  await press('More details');
  await act(async () => renderer.root.findByProps({ testID: 'chunk-constituent-4' }).props.onPress());
  const detail = renderer.root.findByProps({ testID: 'selected-constituent-detail' });
  expect(detail.findByType(ExactPlaybackButton).props).toMatchObject({ text: '个', start: 2.74, end: 3.04 });
  expect(detail.findAllByType(Text).map(n => n.props.children).join(' ')).not.toContain('Most like Tone 4');
});

it('places target/heard readings in More details and dev evidence only in Technical details', async () => {
  const value = withLearned();
  value.data.dev_learned_tone!.units[0]!.heard_pinyin = 'zhòu';
  await mount(value);
  expect(renderer.root.findAllByProps({ testID: 'learned-target-rendering' })).toHaveLength(0);
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  await press('More details');
  expect(JSON.stringify(renderer.root.findByProps({ testID: 'learned-target-rendering' }).props.children)).toContain('zhōu');
  expect(JSON.stringify(renderer.root.findByProps({ testID: 'learned-heard-rendering' }).props.children)).toContain('zhòu');
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  expect(renderer.root.findAllByType(PitchPlot).some(p => p.props.plotHeight === 152)).toBe(true);
  expect(JSON.stringify(renderer.toJSON())).toContain('Tone 1 — level');
  await press('Technical details');
  expect(renderer.root.findByProps({ testID: 'learned-debug' })).toBeTruthy();
  await press('Close Full pitch details');
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
  await press('More details');
  expect(renderer.root.findAllByProps({ testID: 'learned-debug' })).toHaveLength(0);
});

it('fails closed for missing/misordered identities and unresolved target mappings without mutating data', () => {
  const value = withLearned();
  value.data.dev_learned_tone!.units.reverse();
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('TONE_4');
  value.data.dev_learned_tone!.target_mapping_resolved = false;
  expect(firstFeedback(value).grade.agreement).toBe('UNAVAILABLE');
  expect(toneRendering(value.data.dev_learned_tone!).referenceLabel).toBe('Transcript reading');
  value.data.dev_learned_tone!.units = [];
  const before = JSON.stringify(value);
  expect(firstFeedback(value).grade.agreement).toBe('UNAVAILABLE');
  expect(firstFeedback(value).constituents[0]!.observed.tone).toBe('UNCLEAR');
  expect(JSON.stringify(value)).toBe(before);
});

it('preserves feature-off grading and ignores learned payloads in production', () => {
  const chunk = pronunciationChunks(perceivedAnalysis.data)[0]!;
  expect(workspaceChunkFeedback(perceivedAnalysis, chunk)).toEqual(gradeChunkPitch(perceivedAnalysis, chunk));
  const previous = __DEV__;
  try {
    Object.assign(globalThis, { __DEV__: false });
    const value = withLearned();
    expect(learnedToneEvidence(value.data)).toBeNull();
    expect(workspaceChunkFeedback(value, chunk)).toEqual(gradeChunkPitch(value, chunk));
  } finally { Object.assign(globalThis, { __DEV__: previous }); }
});

it.each([true, false])('preserves the prepared-target workflow with the learned dev flag=%s', async enabled => {
  const previous = process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE;
  process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE = String(enabled);
  const client = {
    uploadUtterance: jest.fn().mockResolvedValue({ id: 'u' }),
    createPerception: jest.fn().mockResolvedValue({ id: 'p', transcript: '我想买这个' }),
    createAttempt: jest.fn().mockResolvedValue({ id: 'a' }),
    analyzePronunciation: jest.fn(), addConversationUserTurn: jest.fn(),
    analyzePerceivedSpeech: jest.fn().mockResolvedValue(perceivedAnalysis),
  } as unknown as jest.Mocked<SpeechWorkflowApi>;
  const checkpoint: SpeechCheckpoint = { uri: 'file:///recording.wav' };
  try {
    await submitSpeech(client, { responseMode: 'none', targetId: 't' }, checkpoint, 'audio/wav', () => {}, () => {});
    await Promise.all([checkpoint.analysis, checkpoint.targetAnalysis]);
    expect(client.createPerception).toHaveBeenCalledWith('u');
    expect(client.createAttempt).toHaveBeenCalledWith('u', 't');
    expect(client.analyzePerceivedSpeech).toHaveBeenCalledTimes(1);
    if (enabled) {
      expect(client.analyzePerceivedSpeech).toHaveBeenCalledWith('p', 't');
      expect(client.analyzePronunciation).not.toHaveBeenCalled();
    } else {
      expect(client.analyzePerceivedSpeech).toHaveBeenCalledWith('p');
      expect(client.analyzePronunciation).toHaveBeenCalledWith('a');
    }
  } finally {
    if (previous === undefined) delete process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE;
    else process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE = previous;
  }
});
