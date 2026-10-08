import React from 'react';
import { Text } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import { api } from '@/api/client';
import PracticeScreen from '@/app/practice';
import { SpeechEvidence, changedWording } from '@/speech/SpeechEvidence';

const mockCapture = {
  start: jest.fn().mockResolvedValue(true),
  stop: jest.fn().mockResolvedValue({ uri: 'file:///speech.m4a', durationMillis: 1200 }),
  error: null, durationMillis: 1200,
};
jest.mock('@/audio/useAudioCapture', () => ({ useAudioCapture: () => mockCapture }));
const mockPlayback = jest.fn();
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: (props: unknown) => { mockPlayback(props); return null; } }));

let renderer: ReactTestRenderer;
async function press(label: string) {
  await act(async () => { renderer.root.findByProps({ accessibilityLabel: label }).props.onPress(); });
}
async function record() { await press('Tap to speak'); await press('Stop recording'); }
beforeEach(async () => {
  jest.restoreAllMocks(); jest.clearAllMocks();
  jest.spyOn(console, 'info').mockImplementation(() => {});
  jest.spyOn(api, 'uploadUtterance').mockResolvedValue({ id: 'utterance' } as never);
  jest.spyOn(api, 'createPerception').mockResolvedValue({ id: 'perception', utterance_id: 'utterance', transcript: '你好。' } as never);
  jest.spyOn(api, 'analyzePerceivedSpeech').mockResolvedValue(perceivedAnalysis);
  jest.spyOn(api, 'createConversation'); jest.spyOn(api, 'addConversationUserTurn');
  jest.spyOn(api, 'createAttempt').mockResolvedValue({ id: 'attempt' } as never);
  jest.spyOn(api, 'analyzePronunciation').mockResolvedValue({
    attempt: { id: 'attempt' }, target: { text: '你好', display_pinyin: 'nǐ hǎo' },
    assessment: { status: 'succeeded', normalized_result: { pronunciation_score: 79, evidence_status: 'live_provider' } },
    syllables: [], overall_evidence: {}, recording_audio_url: '/v1/utterances/utterance/audio',
  } as never);
  jest.spyOn(api, 'createTarget').mockResolvedValue({ id: 'target', text: '你好', display_pinyin: 'nǐ hǎo', pinyin_syllables: ['ni3', 'hao3'] } as never);
  jest.spyOn(api, 'createReferenceSpeech').mockResolvedValue({ id: 'ref', status: 'succeeded', audio_url: '/v1/reference-speech/ref/audio', generation_config: {} } as never);
  await act(async () => { renderer = create(React.createElement(PracticeScreen)); });
});
afterEach(async () => { await act(async () => renderer.unmount()); });

it('free Practice shows heard speech without a reply or target-relative score', async () => {
  await record();
  const rendered = JSON.stringify(renderer.toJSON());
  expect(rendered).toContain('你好。');
  expect(rendered).toContain('What Benma heard');
  expect(rendered).toContain('Your pitch');
  expect(rendered).not.toContain('target phrase is needed');
  const visibleText = renderer.root.findAllByType(Text).map((node) => node.props.children).flat().join(' ');
  expect(visibleText).not.toMatch(/BENMA|\d+%|accuracy score/);
  expect(api.createConversation).not.toHaveBeenCalled();
  expect(api.addConversationUserTurn).not.toHaveBeenCalled();
  expect(api.createAttempt).not.toHaveBeenCalled();
  expect(api.analyzePronunciation).not.toHaveBeenCalled();
});
it('target Practice prepares a reference, then invokes existing known-target assessment', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  expect(api.createTarget).toHaveBeenCalledWith('你好');
  expect(api.createReferenceSpeech).toHaveBeenCalledWith('target');
  expect(mockPlayback).toHaveBeenCalledWith({ label: '▶ Native reference', uri: '/v1/reference-speech/ref/audio', disabled: false });
  await record();
  expect(api.createPerception).toHaveBeenCalledWith('utterance');
  expect(api.createAttempt).toHaveBeenCalledWith('utterance', 'target');
  expect(api.analyzePronunciation).toHaveBeenCalledWith('attempt');
  expect(api.addConversationUserTurn).not.toHaveBeenCalled();
  expect(JSON.stringify(renderer.toJSON())).toContain('Your pitch');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pronunciation accuracy vs target: 79 (experimental)');
  await press('More detail');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pronunciation accuracy vs target: 79 (experimental)');
  expect(api.analyzePerceivedSpeech).toHaveBeenCalled();
});
it.each(['preserve', 'infer', 'clarify'] as const)('renders %s evidence distinctly with selectable Mandarin', async (decision) => {
  await act(async () => renderer.update(React.createElement(SpeechEvidence, {
    heard: '今天聊周谋。', decision, understood: decision === 'infer' ? '今天聊周末。' : decision === 'preserve' ? '今天聊周谋。' : null,
  })));
  const rendered = JSON.stringify(renderer.toJSON());
  expect(renderer.root.findByProps({ children: '今天聊周谋。' }).props.selectable).toBe(true);
  if (decision === 'infer') {
    expect(rendered).toContain('What Benma understood');
    expect(rendered).toContain('Benma heard');
    expect(rendered).not.toContain('pronounced');
  } else {
    expect(rendered).not.toContain('What Benma understood');
    if (decision === 'clarify') expect(rendered).toContain('unsure');
  }
});
it('describes exact changed characters without assigning pronunciation blame', () => {
  expect(changedWording('今天聊周谋。', '今天聊周末。')).toEqual({ heard: '谋', understood: '末' });
});

it('keeps the prepared reference mounted but disabled during recording so replay retains its cache', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  mockPlayback.mockClear();
  await press('Tap to speak');
  expect(mockPlayback).toHaveBeenCalledWith({
    label: '▶ Native reference', uri: '/v1/reference-speech/ref/audio', disabled: true,
  });
  await press('Stop recording');
  expect(mockPlayback).toHaveBeenCalledWith({
    label: '▶ Native reference', uri: '/v1/reference-speech/ref/audio', disabled: false,
  });
});

it('an incomplete CLARIFY utterance retains conservative speech feedback and separate unresolved meaning', async () => {
  await act(async () => renderer.update(React.createElement(SpeechEvidence, {
    heard: '你好，今天我……', decision: 'clarify', understood: null,
    recordingUrl: '/v1/utterances/u/audio',
    analysis: { utteranceId: 'u', state: 'ready', perceived: perceivedAnalysis },
  })));
  const rendered = JSON.stringify(renderer.toJSON());
  expect(rendered).toContain('你好，今天我……');
  expect(rendered).toContain('Your pitch');
  expect(rendered).toContain('Sentence pitch timeline');
  expect(rendered).toContain('Meaning');
  expect(rendered).toContain('unsure');
  expect(rendered).not.toMatch(/trailing off|accuracy|target phrase is needed/i);
  expect(mockPlayback).toHaveBeenCalledWith({ uri: '/v1/utterances/u/audio', label: '▶ Play mine' });
});

it('optional target-analysis failure leaves heard speech and the next recording available', async () => {
  jest.spyOn(api, 'analyzePronunciation').mockRejectedValue(new Error('analysis failed'));
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  await record();
  expect(JSON.stringify(renderer.toJSON())).toContain('你好。');
  expect(JSON.stringify(renderer.toJSON())).toContain('Your pitch');
  await press('Tap to speak');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Stop recording' })).toBeTruthy();
});

it('retains one prepared target through three completed turns and rerenders; changes explicitly', async () => {
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  for (let i = 0; i < 3; i++) {
    await record();
    await act(async () => renderer.update(React.createElement(PracticeScreen)));
    expect(JSON.stringify(renderer.toJSON())).toContain('Target active');
  }
  expect(api.createAttempt).toHaveBeenCalledTimes(3);
  expect(jest.mocked(api.createAttempt).mock.calls.map(call => call[1])).toEqual(['target', 'target', 'target']);
  expect(api.analyzePerceivedSpeech).toHaveBeenCalled();
  await press('Change target');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Tap to speak' }).props.disabled).toBe(true);
  await press('Clear target · use free practice');
  await record();
  expect(api.analyzePerceivedSpeech).toHaveBeenCalledTimes(4);
});

it('changing 嘛 to 麻 records against the visible new target and retains it for repeats', async () => {
  jest.mocked(api.createTarget)
    .mockResolvedValueOnce({ id: 'neutral', text: '嘛', display_pinyin: 'ma', pinyin_syllables: ['ma5'] } as never)
    .mockResolvedValueOnce({ id: 'rising', text: '麻', display_pinyin: 'má', pinyin_syllables: ['ma2'] } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('嘛'));
  await press('Prepare target');
  await record();
  expect(api.createAttempt).toHaveBeenLastCalledWith('utterance', 'neutral');
  await press('Change target');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Tap to speak' }).props.disabled).toBe(true);
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('麻'));
  await press('Prepare target');
  expect(api.createTarget).toHaveBeenLastCalledWith('麻');
  expect(renderer.root.findByProps({ children: '麻' })).toBeTruthy();
  for (let i = 0; i < 2; i++) {
    await record();
    expect(api.createAttempt).toHaveBeenLastCalledWith('utterance', 'rising');
  }
  expect(jest.mocked(api.createAttempt).mock.calls.map(call => call[1])).toEqual(['neutral', 'rising', 'rising']);
});

it('keeps the recorded target snapshot and perceived graph independent of legacy attempt data', async () => {
  jest.mocked(api.analyzePronunciation).mockResolvedValue({
    attempt: { id: 'attempt' }, target: { id: 'persisted-neutral', text: '嘛', display_pinyin: 'ma' },
    syllables: [], overall_evidence: {}, recording_audio_url: '/v1/utterances/utterance/audio',
  } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
  await press('Prepare target');
  await record();
  expect(api.createAttempt).toHaveBeenCalledWith('utterance', 'target');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('嘛');
  await press('More detail');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('persisted-neutral');
});

it.each(['synthetic_replay', 'unknown'])('never presents a %s provider score as real assessment', async evidence_status => {
  jest.mocked(api.analyzePronunciation).mockResolvedValue({
    attempt: { id: 'attempt' }, target: { text: '妈', display_pinyin: 'mā' },
    assessment: { normalized_result: { pronunciation_score: 79, evidence_status } },
    syllables: [{ syllable_index: 0, characters: '妈', expected_surface_tone: 1,
      observed_contour: { classification: '1-like', confidence: 'moderate', reason: 'acoustic_shape_only' } }],
    overall_evidence: {}, recording_audio_url: '/v1/utterances/utterance/audio',
  } as never);
  await press('Add a target phrase');
  await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('妈'));
  await press('Prepare target'); await record();
  expect(JSON.stringify(renderer.toJSON())).not.toContain('Pitch signal: Limited');
  await press('More detail');
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).not.toContain('Pronunciation accuracy vs target: 79');
  expect(tree).not.toMatch(/Good ·|Tone 1 ✓|Yours sounded|Correct|Perfect/);
});

it.each([false, true])('no speech leaves Practice ready to rerecord, with prepared target=%s intact', async withTarget => {
  if (withTarget) {
    await press('Add a target phrase');
    await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Target phrase' }).props.onChangeText('你好'));
    await press('Prepare target');
  }
  jest.mocked(api.uploadUtterance).mockRejectedValueOnce({ code: 'no_speech' });
  await record();
  const tree = JSON.stringify(renderer.toJSON());
  expect(tree).toContain("Didn't catch any speech. Try again.");
  expect(tree).not.toContain('What Benma heard'); expect(tree).not.toContain('Your pitch');
  expect(api.createPerception).not.toHaveBeenCalled(); expect(api.createAttempt).not.toHaveBeenCalled();
  expect(api.analyzePerceivedSpeech).not.toHaveBeenCalled(); expect(api.analyzePronunciation).not.toHaveBeenCalled();
  expect(renderer.root.findByProps({ accessibilityLabel: 'Tap to speak' }).props.disabled).toBe(false);
  expect(renderer.root.findAllByProps({ accessibilityLabel: 'Retry' })).toHaveLength(0);
  await record();
  expect(JSON.stringify(renderer.toJSON())).toContain('What Benma heard');
  if (withTarget) expect(api.createAttempt).toHaveBeenCalledWith('utterance', 'target');
});
