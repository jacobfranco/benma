import React from 'react';
import { act, create, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import type { PerceivedSpeechAnalysis } from '@/api/types';
import { PitchPlot } from '@/components/PitchPlot';
import { toneRendering } from '@/speech/LearnedToneWorkspace';
import { PronunciationWorkspace } from '@/speech/PronunciationWorkspace';
import { submitSpeech, type SpeechCheckpoint, type SpeechWorkflowApi } from '@/speech/workflow';

jest.mock('@/audio/ExactPlaybackButton', () => ({ ExactPlaybackButton: () => null, useCanonicalRecording: () => jest.fn() }));

const learned: NonNullable<PerceivedSpeechAnalysis['data']['dev_learned_tone']> = {
  expectation_basis: 'intended_target', target_text: '我想买这个', timings_ms: {}, runtime: {},
  units: [
    { index: 0, characters: '我', target_pinyin: 'wǒ', lexical_tone: 3, expected_surface_tone: null,
      surface_rule: 'prosodic_grouping_unresolved', heard_pinyin: 'wó', realization: { status: 'ok', prediction: 'T2', azure_span: [0, .2] },
      comparison: { state: 'unresolved', message: 'Surface unresolved; no correction.' } },
    { index: 1, characters: '想', target_pinyin: 'xiǎng', lexical_tone: 3, expected_surface_tone: null,
      surface_rule: 'prosodic_grouping_unresolved', heard_pinyin: null, realization: { status: 'abstained' },
      comparison: { state: 'insufficient', message: 'Insufficient evidence; no correction.' } },
    { index: 2, characters: '个', target_pinyin: 'ge', lexical_tone: 0, expected_surface_tone: 0,
      surface_rule: 'neutral', heard_pinyin: null, realization: { status: 'abstained' },
      comparison: { state: 'neutral', message: 'Neutral: no numbered-tone correction.' } },
  ],
};

it('renders tone realization without inventing Hanzi or treating abstentions as matches', () => {
  expect(toneRendering(learned)).toEqual({ target: 'wǒ xiǎng ge', heard: 'wó [unclear] ge' });
});

it('routes learned output to experimental UI while keeping pitch and inspectable evidence', async () => {
  let renderer!: ReactTestRenderer;
  await act(async () => { renderer = create(React.createElement(PronunciationWorkspace, {
    analysis: { ...perceivedAnalysis, data: { ...perceivedAnalysis.data, dev_learned_tone: learned } },
  })); });
  expect(renderer.root.findByProps({ testID: 'learned-tone-workspace' })).toBeTruthy();
  expect(renderer.root.findAllByType(PitchPlot).length).toBeGreaterThan(0);
  const text = JSON.stringify(renderer.toJSON());
  expect(text).toContain('Surface unresolved; no correction.');
  expect(text).not.toContain('Pitch acceptable');
  await act(async () => renderer.unmount());
});

it('learned dev target flow shares one analysis request and skips the laboratory provider branch', async () => {
  const previous = process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE;
  process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE = 'true';
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
    expect(client.analyzePerceivedSpeech).toHaveBeenCalledWith('p', 't');
    expect(client.analyzePronunciation).not.toHaveBeenCalled();
  } finally {
    if (previous === undefined) delete process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE;
    else process.env.EXPO_PUBLIC_BENMA_DEV_LEARNED_TONE = previous;
  }
});
