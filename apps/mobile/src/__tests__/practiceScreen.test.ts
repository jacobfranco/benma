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
    assessment: { normalized_result: { pronunciation_score: 79 } },
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
  expect(rendered).toContain('Expected and mine by syllable');
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
  expect(JSON.stringify(renderer.toJSON())).toContain('Experimental pronunciation analysis');
  expect(JSON.stringify(renderer.toJSON())).toContain('Pronunciation accuracy vs target: 79 (experimental)');
  expect(api.analyzePerceivedSpeech).not.toHaveBeenCalled();
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
  expect(rendered).toContain('Expected here · acoustic shapes');
  expect(rendered).toContain('Expected and mine by syllable');
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
  expect(JSON.stringify(renderer.toJSON())).toContain('Speech analysis unavailable');
  await press('Tap to speak');
  expect(renderer.root.findByProps({ accessibilityLabel: 'Stop recording' })).toBeTruthy();
});
