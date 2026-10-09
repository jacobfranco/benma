import React from 'react';
import { Platform } from 'react-native';
import { act, create, type ReactTestInstance, type ReactTestRenderer } from 'react-test-renderer';

import { perceivedAnalysis } from './perceivedFixture';

import { api } from '@/api/client';
import type { FreeTalkTurn } from '@/api/types';
import FreeTalkScreen from '@/app/free-talk';
import { SpeechEvidence } from '@/speech/SpeechEvidence';

jest.mock('@/audio/useCachedAudio', () => ({ useCachedAudio: () => ({ isPlaying: false, error: null, toggle: jest.fn() }) }));

jest.mock('@/audio/PlaybackButton', () => ({ PlaybackButton: () => null }));

const mockCapture = {
  permission: 'granted',
  requestPermission: jest.fn(),
  start: jest.fn<Promise<boolean>, []>(),
  stop: jest.fn<Promise<{ uri: string; durationMillis: number }>, []>(),
  isRecording: false,
  durationMillis: 1200,
  error: null as string | null,
};

const mockPlayback = {
  activeId: null as string | null,
  error: null as string | null,
  isPlaying: false,
  play: jest.fn<Promise<void>, [{ id: string; url: string }]>(),
  stop: jest.fn<void, []>(),
  toggle: jest.fn<void, [{ id: string; url: string }]>(),
};

jest.mock('@/audio/useAudioCapture', () => ({
  useAudioCapture: (options: unknown) => {
    mockUseAudioCaptureOptions(options);
    return mockCapture;
  },
}));

jest.mock('@/audio/useAssistantPlayback', () => ({
  useAssistantPlayback: () => mockPlayback,
}));

const mockUseAudioCaptureOptions = jest.fn();

function successfulTurn(
  status: 'succeeded' | 'failed' = 'succeeded',
  userSequence = 1,
): FreeTalkTurn {
  return {
    id: `user-turn-${userSequence}`,
    conversation_id: 'conversation-1',
    account_id: 'account-1',
    sequence_number: userSequence,
    role: 'user',
    assistant_text: null,
    resolved_text: '我想买水果。',
    perceived_text: '我想卖水果。',
    interpretation_decision: 'infer',
    utterance_id: 'utterance-1',
    perception_run_id: `perception-${userSequence}`,
    contextual_interpretation_run_id: 'interpretation-1',
    assistant_generation_run_id: null,
    assistant_speech: null,
    created_at: '2026-09-14T12:00:00Z',
    assistant_turn: {
      id: `assistant-turn-${userSequence}`,
      conversation_id: 'conversation-1',
      account_id: 'account-1',
      sequence_number: userSequence + 1,
      role: 'assistant',
      assistant_text: '你喜欢什么水果？',
      resolved_text: '你喜欢什么水果？',
      perceived_text: null,
      interpretation_decision: null,
      utterance_id: null,
      perception_run_id: null,
      contextual_interpretation_run_id: null,
      assistant_generation_run_id: 'generation-1',
      assistant_speech: {
        id: 'speech-1',
        account_id: 'account-1',
        conversation_id: 'conversation-1',
        assistant_generation_run_id: 'generation-1',
        assistant_turn_id: `assistant-turn-${userSequence}`,
        provider: 'azure',
        product: 'speech',
        provider_version: null,
        adapter_version: '1',
        model: 'azure-speech',
        voice: 'zh-CN-XiaoxiaoNeural',
        locale: 'zh-CN',
        generation_configuration: {},
        text_snapshot: '你喜欢什么水果？',
        audio_asset: null,
        audio_url: status === 'succeeded' ? '/v1/assistant-speeches/speech-1/audio' : null,
        latency_ms: 50,
        status,
        error_code: status === 'failed' ? 'assistant_speech_failed' : null,
        error_message: status === 'failed' ? 'speech unavailable' : null,
        created_at: '2026-09-14T12:00:01Z',
      },
      created_at: '2026-09-14T12:00:01Z',
    },
  };
}

async function flush(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

function button(root: ReactTestInstance, label: string): ReactTestInstance {
  return root.findByProps({ accessibilityLabel: label });
}

async function renderScreen(): Promise<ReactTestRenderer> {
  let renderer!: ReactTestRenderer;
  await act(async () => {
    renderer = create(React.createElement(FreeTalkScreen));
    await flush();
  });
  return renderer;
}

async function recordAndStop(renderer: ReactTestRenderer): Promise<void> {
  await act(async () => {
    button(renderer.root, 'Tap to speak').props.onPress();
    await flush();
  });
  await act(async () => {
    button(renderer.root, 'Stop recording').props.onPress();
    await flush();
  });
}

describe('Free Talk screen', () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    jest.clearAllMocks();
    mockCapture.permission = 'granted';
    mockCapture.error = null;
    mockCapture.start.mockResolvedValue(true);
    mockCapture.stop.mockResolvedValue({ uri: 'file:///speech.m4a', durationMillis: 1200 });
    mockPlayback.activeId = null;
    mockPlayback.error = null;
    mockPlayback.isPlaying = false;
    mockPlayback.play.mockResolvedValue();
    jest.spyOn(console, 'info').mockImplementation(() => {});
    jest.spyOn(api, 'createConversation').mockResolvedValue({
      id: 'conversation-1',
      account_id: 'account-1',
      created_at: '2026-09-14T12:00:00Z',
      updated_at: '2026-09-14T12:00:00Z',
    });
    jest.spyOn(api, 'uploadUtterance').mockResolvedValue({ id: 'utterance-1' } as never);
    jest.spyOn(api, 'listConversationTurns').mockResolvedValue([]);
    jest.spyOn(api, 'createPerception').mockResolvedValue({
      id: 'perception-1', utterance_id: 'utterance-1',
      transcript: '我想卖水果。',
    } as never);
    jest.spyOn(api, 'addConversationUserTurn').mockResolvedValue(successfulTurn());
    jest.spyOn(api, 'analyzePerceivedSpeech').mockResolvedValue(perceivedAnalysis);
    jest.spyOn(api, 'createAssistantSpeech').mockResolvedValue(successfulTurn().assistant_turn.assistant_speech!);
  });

  it('no-speech shows retry copy without a transcript, graph or assistant response', async () => {
    jest.mocked(api.uploadUtterance).mockRejectedValueOnce({ code: 'no_speech' });
    const renderer = await renderScreen();
    await recordAndStop(renderer);
    expect(JSON.stringify(renderer.toJSON())).toContain("Didn't catch any speech. Try again.");
    expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(0);
    expect(api.createPerception).not.toHaveBeenCalled();
    expect(api.analyzePerceivedSpeech).not.toHaveBeenCalled();
    expect(api.addConversationUserTurn).not.toHaveBeenCalled();
    expect(api.createAssistantSpeech).not.toHaveBeenCalled();
    expect(button(renderer.root, 'Tap to speak').props.disabled).toBe(false);
    await act(async () => renderer.unmount());
  });

  it('future non-Mandarin rejection withholds a turn and pronunciation, then permits a fresh recording', async () => {
    jest.mocked(api.createPerception).mockRejectedValueOnce({ code: 'non_mandarin' });
    const renderer = await renderScreen();
    await recordAndStop(renderer);
    expect(JSON.stringify(renderer.toJSON())).toContain("This doesn't sound like Mandarin. Try again.");
    expect(renderer.root.findAllByType(SpeechEvidence)).toHaveLength(0);
    expect(api.analyzePerceivedSpeech).not.toHaveBeenCalled();
    expect(api.addConversationUserTurn).not.toHaveBeenCalled();
    expect(api.createAssistantSpeech).not.toHaveBeenCalled();
    expect(button(renderer.root, 'Tap to speak').props.disabled).toBe(false);
    await recordAndStop(renderer);
    expect(api.uploadUtterance).toHaveBeenCalledTimes(2);
    expect(api.addConversationUserTurn).toHaveBeenCalledTimes(1);
    await act(async () => renderer.unmount());
  });

  it('automatically creates a new persisted conversation and keeps captures temporary', async () => {
    const renderer = await renderScreen();

    expect(api.createConversation).toHaveBeenCalledTimes(1);
    expect(mockUseAudioCaptureOptions).toHaveBeenCalledWith({ directory: 'cache' });
    expect(button(renderer.root, 'Tap to speak')).toBeTruthy();
  });

  it('records, submits a successful first turn, and renders heard and inferred text separately', async () => {
    const renderer = await renderScreen();

    await act(async () => {
      button(renderer.root, 'Tap to speak').props.onPress();
      await flush();
    });
    expect(button(renderer.root, 'Stop recording')).toBeTruthy();

    await act(async () => {
      button(renderer.root, 'Stop recording').props.onPress();
      await flush();
    });

    expect(api.uploadUtterance).toHaveBeenCalledWith('file:///speech.m4a', Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4');
    expect(api.createPerception).toHaveBeenCalledWith('utterance-1');
    expect(api.addConversationUserTurn).toHaveBeenCalledWith(
      'conversation-1',
      'utterance-1',
      'perception-1',
      expect.any(Function),
    );
    const rendered = JSON.stringify(renderer.toJSON());
    expect(rendered).toContain('我想买水果。');
    expect(rendered).toContain('你喜欢什么水果？');
    expect(rendered).toContain('我想卖水果。');
    expect(rendered).toContain('What Benma heard');
    expect(rendered).toContain('What Benma understood');
    expect(rendered).toContain('Explore pronunciation');
    expect(rendered).not.toContain('Your pitch');
    expect(rendered).not.toMatch(/provider|logprob|evidence|uncertainty/i);

    const userText = renderer.root.findByProps({ children: '我想买水果。' });
    const assistantText = renderer.root.findByProps({ children: '你喜欢什么水果？' });
    expect(userText.props.selectable).toBe(true);
    expect(assistantText.props.selectable).toBe(true);
    expect(renderer.root.findByProps({ children: 'YOU' }).props.selectable).toBeUndefined();
  });

  it('reserves pronunciation and the assistant card at perception, then hydrates in place', async () => {
    let releaseResponse!: (result: FreeTalkTurn) => void;
    let releaseAnalysis!: (result: typeof perceivedAnalysis) => void;
    jest.spyOn(api, 'addConversationUserTurn').mockReturnValue(new Promise(resolve => { releaseResponse = resolve; }));
    jest.spyOn(api, 'analyzePerceivedSpeech').mockReturnValue(new Promise(resolve => { releaseAnalysis = resolve; }));
    const renderer = await renderScreen();
    await recordAndStop(renderer);
    expect(JSON.stringify(renderer.toJSON())).not.toContain('sentence-graph-placeholder');
    await act(async () => renderer.root.findByProps({ accessibilityLabel: 'Explore pronunciation' }).props.onPress());
    const section = renderer.root.findByProps({ testID: 'pronunciation-section' });
    const placeholder = renderer.root.findByProps({ testID: 'pronunciation-content' });
    expect(JSON.stringify(renderer.toJSON())).toContain('sentence-graph-placeholder');
    expect(JSON.stringify(renderer.toJSON())).toContain('Preparing response…');
    await act(async () => { releaseResponse(successfulTurn()); await flush(); });
    expect(renderer.root.findByProps({ testID: 'pronunciation-section' })).toBe(section);
    expect(renderer.root.findByProps({ testID: 'pronunciation-content' })).toBe(placeholder);
    expect(JSON.stringify(renderer.toJSON())).toContain('sentence-graph-placeholder');
    expect(JSON.stringify(renderer.toJSON())).toContain('你喜欢什么水果？');
    await act(async () => { releaseAnalysis(perceivedAnalysis); await flush(); });
    expect(renderer.root.findByProps({ testID: 'pronunciation-section' })).toBe(section);
    expect(renderer.root.findByProps({ testID: 'pronunciation-content' })).toBe(placeholder);
    const tree = JSON.stringify(renderer.toJSON());
    expect(tree).not.toContain('sentence-graph-placeholder');
    expect(tree.indexOf('Your pitch')).toBeLessThan(tree.indexOf('BENMA'));
    expect(api.analyzePerceivedSpeech).toHaveBeenCalledTimes(1);
    await act(async () => renderer.unmount());
  });

  it('autoplays successful persisted speech exactly once and replays its protected source', async () => {
    const renderer = await renderScreen();

    await recordAndStop(renderer);
    expect(mockPlayback.play).toHaveBeenCalledTimes(1);
    expect(mockPlayback.play).toHaveBeenCalledWith(expect.objectContaining({
      id: 'speech-1',
      url: '/v1/assistant-speeches/speech-1/audio',
    }));

    await act(async () => {
      renderer.update(React.createElement(FreeTalkScreen));
      await flush();
    });
    expect(mockPlayback.play).toHaveBeenCalledTimes(1);

    button(renderer.root, 'Play response').props.onPress();
    expect(mockPlayback.toggle).toHaveBeenCalledWith({
      id: 'speech-1',
      url: '/v1/assistant-speeches/speech-1/audio',
    });
  });

  it('stops playback before a new recording and can autoplay again afterward', async () => {
    jest
      .spyOn(api, 'addConversationUserTurn')
      .mockResolvedValueOnce(successfulTurn())
      .mockResolvedValueOnce(successfulTurn('succeeded', 3));
    const renderer = await renderScreen();
    await recordAndStop(renderer);
    mockPlayback.stop.mockClear();
    mockCapture.start.mockClear();

    await act(async () => {
      button(renderer.root, 'Tap to speak').props.onPress();
      await flush();
    });

    expect(mockPlayback.stop).toHaveBeenCalledTimes(1);
    expect(mockCapture.start).toHaveBeenCalledTimes(1);
    expect(mockPlayback.stop.mock.invocationCallOrder[0]).toBeLessThan(
      mockCapture.start.mock.invocationCallOrder[0]!,
    );

    await act(async () => {
      button(renderer.root, 'Stop recording').props.onPress();
      await flush();
    });
    expect(mockPlayback.play).toHaveBeenCalledTimes(2);
  });

  it('reuses the same conversation for a subsequent turn', async () => {
    jest
      .spyOn(api, 'addConversationUserTurn')
      .mockResolvedValueOnce(successfulTurn())
      .mockResolvedValueOnce(successfulTurn('succeeded', 3));
    const renderer = await renderScreen();

    await recordAndStop(renderer);
    await recordAndStop(renderer);

    expect(api.createConversation).toHaveBeenCalledTimes(1);
    expect(api.addConversationUserTurn).toHaveBeenNthCalledWith(
      1,
      'conversation-1',
      'utterance-1',
      'perception-1',
      expect.any(Function),
    );
    expect(api.addConversationUserTurn).toHaveBeenNthCalledWith(
      2,
      'conversation-1',
      'utterance-1',
      'perception-1',
      expect.any(Function),
    );
  });

  it('keeps assistant text and recording available when TTS fails', async () => {
    jest.spyOn(api, 'createAssistantSpeech').mockResolvedValue(successfulTurn('failed').assistant_turn.assistant_speech!);
    const renderer = await renderScreen();

    await recordAndStop(renderer);

    const rendered = JSON.stringify(renderer.toJSON());
    expect(rendered).toContain('你喜欢什么水果？');
    expect(rendered).toContain('Audio unavailable');
    expect(button(renderer.root, 'Tap to speak')).toBeTruthy();
    expect(mockPlayback.play).not.toHaveBeenCalled();
  });

  it('prevents duplicate stop taps from double-submitting', async () => {
    let releaseStop!: (recording: { uri: string; durationMillis: number }) => void;
    mockCapture.stop.mockReturnValue(
      new Promise((resolve) => {
        releaseStop = resolve;
      }),
    );
    const renderer = await renderScreen();
    await act(async () => {
      button(renderer.root, 'Tap to speak').props.onPress();
      await flush();
    });
    const onStop = button(renderer.root, 'Stop recording').props.onPress;

    await act(async () => {
      onStop();
      onStop();
      releaseStop({ uri: 'file:///speech.m4a', durationMillis: 1200 });
      await flush();
    });

    expect(mockCapture.stop).toHaveBeenCalledTimes(1);
    expect(api.uploadUtterance).toHaveBeenCalledTimes(1);
    expect(api.addConversationUserTurn).toHaveBeenCalledTimes(1);
  });

  it('shows a usable microphone denial state', async () => {
    mockCapture.start.mockResolvedValue(false);
    const renderer = await renderScreen();

    await act(async () => {
      button(renderer.root, 'Tap to speak').props.onPress();
      await flush();
    });

    expect(JSON.stringify(renderer.toJSON())).toContain('Microphone access is needed');
    expect(button(renderer.root, 'Try microphone again')).toBeTruthy();
  });

  it('recovers from processing and network failure so another recording can start', async () => {
    jest.spyOn(api, 'uploadUtterance').mockRejectedValue(new TypeError('fetch failed'));
    const renderer = await renderScreen();

    await recordAndStop(renderer);

    expect(JSON.stringify(renderer.toJSON())).toContain('Upload failed');
    expect(button(renderer.root, 'Tap to speak')).toBeTruthy();
  });

  it('reconciles a user turn persisted before response-generation failure', async () => {
    const result = successfulTurn();
    jest.spyOn(api, 'addConversationUserTurn').mockRejectedValue(new Error('Response failed'));
    jest.spyOn(api, 'listConversationTurns').mockResolvedValue([result]);
    const renderer = await renderScreen();

    await recordAndStop(renderer);

    expect(api.listConversationTurns).toHaveBeenCalledWith('conversation-1');
    expect(JSON.stringify(renderer.toJSON())).toContain('我想买水果。');
    expect(JSON.stringify(renderer.toJSON())).toContain('Response unavailable');
    expect(button(renderer.root, 'Tap to speak')).toBeTruthy();
  });

  it('recovers from recording failure and exposes playback failure non-blockingly', async () => {
    mockCapture.stop.mockRejectedValue(new Error('Recording could not stop'));
    mockPlayback.error = 'Benma’s audio could not be played. You can try again.';
    const renderer = await renderScreen();

    await recordAndStop(renderer);

    const rendered = JSON.stringify(renderer.toJSON());
    expect(rendered).toContain('Recording interrupted');
    expect(rendered).toContain('audio could not be played');
    expect(button(renderer.root, 'Tap to speak')).toBeTruthy();
  });
});


it('renders heard text before reasoning and assistant text before TTS completes', async () => {
  // Explicit setup because this latency test sits outside the legacy describe setup.
  jest.spyOn(console, 'info').mockImplementation(() => {});
  mockCapture.start.mockResolvedValue(true);
  mockCapture.stop.mockResolvedValue({ uri: 'file:///speech.m4a', durationMillis: 1200 });
  jest.spyOn(api, 'createConversation').mockResolvedValue({ id: 'conversation-1' } as never);
  jest.spyOn(api, 'uploadUtterance').mockResolvedValue({ id: 'utterance-1' } as never);
  jest.spyOn(api, 'createPerception').mockResolvedValue({ id: 'perception-1', utterance_id: 'utterance-1', transcript: '我想卖水果。' } as never);
  let finishResponse!: (value: FreeTalkTurn) => void;
  let finishSpeech!: (value: NonNullable<FreeTalkTurn['assistant_turn']['assistant_speech']>) => void;
  jest.spyOn(api, 'addConversationUserTurn').mockReturnValue(new Promise((resolve) => { finishResponse = resolve; }));
  jest.spyOn(api, 'createAssistantSpeech').mockReturnValue(new Promise((resolve) => { finishSpeech = resolve; }));
  const renderer = await renderScreen();
  await recordAndStop(renderer);
  expect(JSON.stringify(renderer.toJSON())).toContain('我想卖水果。');
  expect(JSON.stringify(renderer.toJSON())).toContain('Understanding meaning');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('你喜欢什么水果？');
  const heardCard = renderer.root.findByType(SpeechEvidence);
  const interpret = jest.mocked(api.addConversationUserTurn).mock.calls.at(-1)![3]!;
  await act(async () => { interpret({ perception_run_id: 'perception-1', decision: 'infer', inferred_text: '我想买水果。' } as never); });
  expect(JSON.stringify(renderer.toJSON())).toContain('我想买水果。');
  expect(JSON.stringify(renderer.toJSON())).not.toContain('你喜欢什么水果？');
  expect(renderer.root.findByType(SpeechEvidence)).toBe(heardCard);
  await act(async () => { finishResponse(successfulTurn()); await flush(); });
  expect(JSON.stringify(renderer.toJSON())).toContain('你喜欢什么水果？');
  expect(JSON.stringify(renderer.toJSON())).toContain('Preparing voice');
  expect(renderer.root.findByType(SpeechEvidence)).toBe(heardCard);
  expect(api.createAssistantSpeech).toHaveBeenCalledWith('generation-1');
  const plays = mockPlayback.play.mock.calls.length;
  await act(async () => { button(renderer.root, 'Tap to speak').props.onPress(); await flush(); });
  await act(async () => { finishSpeech(successfulTurn().assistant_turn.assistant_speech!); await flush(); });
  expect(mockPlayback.play).toHaveBeenCalledTimes(plays); // No late autoplay over microphone.
  await act(async () => renderer.unmount());
});
