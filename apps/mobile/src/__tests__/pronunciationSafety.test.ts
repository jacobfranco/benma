import React from 'react';
import { Pressable } from 'react-native';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { api } from '@/api/client';
import PronunciationScreen from '@/app/pronunciation';

jest.mock('@/audio/useAudioCapture', () => ({ useAudioCapture: () => ({
  start: async () => true,
  stop: async () => ({ uri: 'file:///fixture.m4a', durationMillis: 1200 }),
  error: null, durationMillis: 1200,
}) }));
jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));

it('keeps cached evaluator claims out of default and A/B views, preserving labeled diagnostics', async () => {
  const target = { id: 'target', text: '麻', display_pinyin: 'má', pinyin_syllables: ['ma2'] };
  const legacyMessage = 'The evaluator detected Tone 4 here.';
  const result = {
    attempt: { id: 'a', created_at: '2026-10-06T00:00:00Z' }, target,
    recording_audio_url: '/v1/utterances/u/audio', overall_evidence: {},
    syllables: [{ syllable_index: 0, characters: '麻', pinyin: 'ma2', expected_surface_tone: 2,
      surface_tone_reason: [], provider_evidence: { detected_tone: 4 },
      interpretation: { message: legacyMessage }, tone_comparison_policy: 'experimental' }],
    interpretation: { structured_observations: [{ message: legacyMessage }] },
  };
  jest.spyOn(api, 'createTarget').mockResolvedValue(target as never);
  jest.spyOn(api, 'createReferenceSpeech').mockResolvedValue({ status: 'failed' } as never);
  jest.spyOn(api, 'listPronunciationAttempts').mockResolvedValue([
    result, { ...result, attempt: { ...result.attempt, id: 'b' } },
  ] as never);
  jest.spyOn(api, 'createPracticeSession').mockResolvedValue({ id: 'session' } as never);
  jest.spyOn(api, 'uploadUtterance').mockResolvedValue({ id: 'u' } as never);
  jest.spyOn(api, 'createAttempt').mockResolvedValue({ id: 'a' } as never);
  jest.spyOn(api, 'analyzePronunciation').mockResolvedValue(result as never);
  let renderer: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(PronunciationScreen)); });
  const press = async (label: string) => {
    await act(async () => renderer.root.findByProps({ accessibilityLabel: label }).props.onPress());
  };
  try {
    for (const label of ['Prepare target', 'Record attempt', 'Stop recording', 'Keep and upload', 'Analyze attempt']) await press(label);
    expect(JSON.stringify(renderer!.toJSON())).toContain('Tone comparison is unavailable');
    expect(JSON.stringify(renderer!.toJSON())).not.toContain(legacyMessage);
    expect(JSON.stringify(renderer!.toJSON())).not.toContain('Evaluator detected');
    const choices = renderer!.root.findAllByType(Pressable).filter(node => node.props.accessibilityRole === 'checkbox');
    for (const choice of choices) await act(async () => choice.props.onPress());
    expect(JSON.stringify(renderer!.toJSON())).toContain('A/B comparison');
    expect(JSON.stringify(renderer!.toJSON())).not.toContain(legacyMessage);
    await press('Show advanced evidence');
    expect(JSON.stringify(renderer!.toJSON())).toContain('Experimental diagnostics');
    expect(JSON.stringify(renderer!.toJSON())).toContain('not pronunciation grades');
    expect(JSON.stringify(renderer!.toJSON())).toContain(legacyMessage);
  } finally {
    await act(async () => renderer!.unmount());
    jest.restoreAllMocks();
  }
});
