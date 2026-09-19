import { perceivedAnalysis } from './perceivedFixture';

import { submitSpeech, type SpeechCheckpoint, type SpeechWorkflowApi } from '@/speech/workflow';
import { reconcileTurns } from '@/freeTalk/state';
import type { ConversationTurn } from '@/api/types';

function workflowApi(): jest.Mocked<SpeechWorkflowApi> {
  return {
    uploadUtterance: jest.fn().mockResolvedValue({ id: 'utterance-1' }),
    createPerception: jest.fn().mockResolvedValue({ id: 'perception-1', transcript: '今天聊周谋。' }),
    addConversationUserTurn: jest.fn().mockResolvedValue({ id: 'turn-1', assistant_turn: { id: 'assistant-1' } }),
    analyzePerceivedSpeech: jest.fn().mockResolvedValue(perceivedAnalysis),
    createAttempt: jest.fn().mockResolvedValue({ id: 'attempt-1' }),
    analyzePronunciation: jest.fn().mockResolvedValue({ attempt: { id: 'attempt-1' } }),
  } as unknown as jest.Mocked<SpeechWorkflowApi>;
}
beforeEach(() => { jest.spyOn(console, 'info').mockImplementation(() => {}); });
afterEach(() => jest.restoreAllMocks());

it('shows unchanged perception before the conversation request resolves', async () => {
  const client = workflowApi();
  let resolve!: (result: never) => void;
  client.addConversationUserTurn.mockReturnValue(new Promise((done) => { resolve = done; }));
  const heard = jest.fn(), stages = jest.fn();
  const pending = submitSpeech(client, { responseMode: 'conversation', conversationId: 'c1' },
    { uri: 'file:///one.m4a' }, 'audio/mp4', stages, heard);
  for (let i = 0; i < 10; i++) await Promise.resolve();
  expect(heard).toHaveBeenCalledWith(expect.objectContaining({ transcript: '今天聊周谋。' }));
  expect(client.createPerception).toHaveBeenCalledWith('utterance-1');
  expect(stages.mock.calls.map(([stage]) => stage)).toEqual(['uploading', 'perceiving', 'responding']);
  resolve({ id: 'turn-1' } as never);
  await pending;
});
it('free Practice stops after perception without assessing or responding', async () => {
  const client = workflowApi();
  const result = await submitSpeech(client, { responseMode: 'none' }, { uri: 'file:///one.m4a' },
    'audio/mp4', () => {}, () => {});
  expect(result).toEqual({ perception: { id: 'perception-1', transcript: '今天聊周谋。' } });
  expect(client.addConversationUserTurn).not.toHaveBeenCalled();
  expect(client.createAttempt).not.toHaveBeenCalled();
  expect(client.analyzePronunciation).not.toHaveBeenCalled();
});
it('known-target Practice perceives without hints and uses an explicit target attempt', async () => {
  const client = workflowApi();
  await submitSpeech(client, { responseMode: 'none', targetId: 'target-1' },
    { uri: 'file:///one.m4a' }, 'audio/mp4', () => {}, () => {});
  expect(client.createPerception).toHaveBeenCalledWith('utterance-1');
  expect(client.createAttempt).toHaveBeenCalledWith('utterance-1', 'target-1');
  expect(client.analyzePronunciation).toHaveBeenCalledWith('attempt-1');
  expect(client.addConversationUserTurn).not.toHaveBeenCalled();
});
it('retries perception on the existing uploaded utterance', async () => {
  const client = workflowApi();
  const checkpoint: SpeechCheckpoint = { uri: 'file:///one.m4a' };
  client.createPerception.mockRejectedValueOnce(new Error('secret provider detail'));
  await expect(submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/mp4', () => {}, () => {}))
    .rejects.toMatchObject({ stage: 'perception', message: expect.not.stringContaining('secret') });
  await submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/mp4', () => {}, () => {});
  expect(client.uploadUtterance).toHaveBeenCalledTimes(1);
  expect(client.createPerception).toHaveBeenCalledTimes(2);
});
it('reconciles server records by identity without duplicating history', () => {
  const user = { id: 'u', sequence_number: 1, perceived_text: '原文' } as ConversationTurn;
  const assistant = { id: 'a', sequence_number: 2, assistant_speech: null } as ConversationTurn;
  expect(reconcileTurns([user, assistant], [user, { ...assistant, assistant_text: '回复' }]))
    .toEqual([user, { ...assistant, assistant_text: '回复' }]);
});

function deferred<T>() {
  let resolve!: (value: T) => void, reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
async function flushWorkflow() { for (let i = 0; i < 20; i++) await Promise.resolve(); }

it('paints readings during alignment and ignores a preview that arrives after final analysis', async () => {
  const client = workflowApi(), preview = deferred<never>(), acoustic = deferred<never>();
  client.getPerceivedReadings = jest.fn().mockReturnValue(preview.promise);
  client.analyzePerceivedSpeech.mockReturnValue(acoustic.promise);
  const feedback = jest.fn(), checkpoint: SpeechCheckpoint = { uri: 'file:///one.m4a' };
  await submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/mp4', () => {}, () => {}, 0, feedback);
  preview.resolve({ syllables: perceivedAnalysis.data.syllables } as never);
  await flushWorkflow();
  expect(feedback).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'processing', readings: expect.any(Object) }));
  acoustic.resolve(perceivedAnalysis as never);
  await checkpoint.analysis;
  expect(feedback).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'ready', perceived: perceivedAnalysis }));

  const late = deferred<never>();
  client.getPerceivedReadings = jest.fn().mockReturnValue(late.promise);
  client.analyzePerceivedSpeech.mockResolvedValue(perceivedAnalysis);
  const second: SpeechCheckpoint = { uri: 'file:///two.m4a' };
  await submitSpeech(client, { responseMode: 'none' }, second, 'audio/mp4', () => {}, () => {}, 0, feedback);
  await second.analysis;
  const calls = feedback.mock.calls.length;
  late.resolve({ syllables: [] } as never);
  await flushWorkflow();
  expect(feedback).toHaveBeenCalledTimes(calls);
});

it('starts free-speech analysis after perception beside meaning and does not gate heard text or reply on it', async () => {
  const client = workflowApi(), audio = deferred<never>(), semantic = deferred<never>();
  client.analyzePerceivedSpeech.mockReturnValue(audio.promise);
  client.addConversationUserTurn.mockReturnValue(semantic.promise);
  const heard = jest.fn(), feedback = jest.fn();
  const checkpoint: SpeechCheckpoint = { uri: 'file:///one.m4a' };
  const submission = submitSpeech(client, { responseMode: 'conversation', conversationId: 'c' }, checkpoint,
    'audio/mp4', () => {}, heard, 0, feedback);
  await flushWorkflow();
  expect(client.analyzePerceivedSpeech).toHaveBeenCalledTimes(1);
  expect(heard).toHaveBeenCalledTimes(1);
  expect(client.addConversationUserTurn).toHaveBeenCalledTimes(1);
  expect(feedback).toHaveBeenLastCalledWith({ utteranceId: 'utterance-1', perceptionId: 'perception-1', state: 'processing' });
  semantic.resolve({ id: 'turn' } as never);
  expect((await submission).conversation).toEqual({ id: 'turn' });
  audio.reject(new Error('provider failure'));
  await checkpoint.analysis;
  expect(feedback).toHaveBeenLastCalledWith({ utteranceId: 'utterance-1', perceptionId: 'perception-1', state: 'failed' });
});

it('known-target assessment can finish while unknown-target perception is still pending', async () => {
  const client = workflowApi(), perception = deferred<never>();
  client.createPerception.mockReturnValue(perception.promise);
  const heard = jest.fn(), feedback = jest.fn();
  const submission = submitSpeech(client, { responseMode: 'none', targetId: 'explicit-target' },
    { uri: 'file:///one.m4a' }, 'audio/mp4', () => {}, heard, 0, feedback);
  await flushWorkflow();
  expect(heard).not.toHaveBeenCalled();
  expect(client.createAttempt).toHaveBeenCalledWith('utterance-1', 'explicit-target');
  expect(client.analyzePerceivedSpeech).not.toHaveBeenCalled(); // The server owns this branch for targets.
  expect(feedback).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'ready', pronunciation: expect.any(Object) }));
  perception.resolve({ id: 'p', transcript: '你好' } as never);
  await submission;
});

it('retrying perception starts exactly one transcript analysis after success', async () => {
  const client = workflowApi(), acoustic = deferred<never>();
  client.analyzePerceivedSpeech.mockReturnValue(acoustic.promise);
  client.createPerception.mockRejectedValueOnce(new Error('perception failed'));
  const checkpoint: SpeechCheckpoint = { uri: 'file:///one.m4a' };
  await expect(submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/mp4', () => {}, () => {}))
    .rejects.toMatchObject({ stage: 'perception' });
  await submitSpeech(client, { responseMode: 'none' }, checkpoint, 'audio/mp4', () => {}, () => {});
  expect(client.analyzePerceivedSpeech).toHaveBeenCalledTimes(1);
  acoustic.resolve(perceivedAnalysis as never);
  await checkpoint.analysis;
});

it.each(['preserve', 'infer', 'clarify'])('never manufactures a pronunciation target from a %s conversation', async (decision) => {
  const client = workflowApi();
  client.addConversationUserTurn.mockResolvedValue({ interpretation_decision: decision, resolved_text: '你好，今天我去北京。' } as never);
  await submitSpeech(client, { responseMode: 'conversation', conversationId: 'c' },
    { uri: 'file:///one.m4a' }, 'audio/mp4', () => {}, () => {});
  expect(client.createAttempt).not.toHaveBeenCalled();
  expect(client.analyzePronunciation).not.toHaveBeenCalled();
});

it('does not start transcript analysis before perception is committed; sends only its ID', async () => {
  const client = workflowApi(), perception = deferred<never>(), semantic = deferred<never>();
  client.createPerception.mockReturnValue(perception.promise);
  client.addConversationUserTurn.mockReturnValue(semantic.promise);
  const checkpoint: SpeechCheckpoint = { uri: 'file:///one.m4a' };
  const feedback = jest.fn();
  const submission = submitSpeech(client, { responseMode: 'conversation', conversationId: 'c' },
    checkpoint, 'audio/mp4', () => {}, () => {}, 0, feedback);
  await flushWorkflow();
  expect(client.analyzePerceivedSpeech).not.toHaveBeenCalled();
  perception.resolve({ id: 'persisted-perception', status: 'succeeded', transcript: '周谋' } as never);
  await flushWorkflow();
  expect(client.analyzePerceivedSpeech).toHaveBeenCalledWith('persisted-perception');
  expect(feedback).toHaveBeenLastCalledWith(expect.objectContaining({ state: 'ready', perceived: perceivedAnalysis }));
  semantic.reject(new Error('interpretation failed'));
  await expect(submission).rejects.toMatchObject({ stage: 'response' });
  await checkpoint.analysis;
  // Response retry uses the same analysis promise and persisted perception.
  client.addConversationUserTurn.mockResolvedValue({ id: 'turn' } as never);
  await submitSpeech(client, { responseMode: 'conversation', conversationId: 'c' },
    checkpoint, 'audio/mp4', () => {}, () => {});
  expect(client.analyzePerceivedSpeech).toHaveBeenCalledTimes(1);
});
