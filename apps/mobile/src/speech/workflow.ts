import type { BenmaApiClient } from '@/api/client';
import type { PerceivedReadings, PerceivedSpeechAnalysis, ContextualInterpretationRun, FreeTalkTurn, PerceptionRun, PronunciationResult } from '@/api/types';

export type SpeechStage = 'stopping' | 'uploading' | 'perceiving' | 'responding' | 'assessing';
export type SpeechFailure = 'recording' | 'upload' | 'perception' | 'response' | 'assessment' | 'no_speech' | 'non_mandarin' | 'language_uncertain';
export const speechStageLabels: Record<SpeechStage, string> = {
  stopping: 'Finishing recording…', uploading: 'Sending recording…',
  perceiving: 'Processing speech…', responding: 'Understanding meaning…',
  assessing: 'Analyzing pronunciation…',
};
export const speechFailureLabels: Record<SpeechFailure, string> = {
  no_speech: "Didn't catch any speech. Try again.",
  non_mandarin: "This doesn't sound like Mandarin. Try again.",
  language_uncertain: "Couldn't identify the language. Try recording again.",
  recording: 'Recording interrupted. Please record again.',
  upload: 'Upload failed. Try sending the recording again.',
  perception: 'Could not understand speech. Try again or make a new recording.',
  response: 'Response unavailable. You can keep talking.',
  assessment: 'Speech feedback unavailable. Try analysis again.',
};
export class SpeechSubmissionError extends Error {
  constructor(public readonly stage: SpeechFailure) { super(speechFailureLabels[stage]); }
}

// Error plumbing only: the current server does not emit language rejections.
// Never infer source language from transcript text or constrained ASR metadata.
function recordingRejection(code: unknown): SpeechFailure | undefined {
  if (code === 'no_speech' || code === 'non_mandarin' || code === 'language_uncertain') return code;
}

export type SpeechWorkflowApi = Pick<BenmaApiClient,
  'uploadUtterance' | 'createPerception' | 'addConversationUserTurn' |
  'createAttempt' | 'analyzePronunciation' | 'analyzePerceivedSpeech'> & Partial<Pick<BenmaApiClient, 'getPerceivedReadings'>>;
export type SpeechMode = { responseMode: 'conversation'; conversationId: string } |
  { responseMode: 'none'; targetId?: string };

// Transport checkpoints enable retries without rerecording or resubmitting known uploads.
// Every semantic value here is an unchanged server response.
export interface SpeechCheckpoint {
  uri: string;
  utteranceId?: string;
  perception?: PerceptionRun;
  attemptId?: string;
  analysis?: Promise<void>;
  targetAnalysis?: Promise<void>;
  pronunciation?: PronunciationResult;
  feedback?: SpeechAnalysis;
}
export interface SpeechAnalysis {
  receivedAt?: number;
  startedAt?: number;
  utteranceId: string;
  targetId?: string;
  perceptionId?: string;
  state: 'processing' | 'ready' | 'failed';
  perceived?: PerceivedSpeechAnalysis;
  readings?: PerceivedReadings;
  pronunciation?: PronunciationResult;
}
export interface SpeechSubmission {
  perception: PerceptionRun;
  conversation?: FreeTalkTurn;
  pronunciation?: PronunciationResult;
}
export function logTiming(label: string, startedAt: number): void {
  if (__DEV__) console.info(`[speech timing] ${label} ms:`, Date.now() - startedAt);
}
export async function measureSpeech<T>(label: string, request: () => Promise<T>): Promise<T> {
  const startedAt = Date.now();
  try { return await request(); } finally { logTiming(label, startedAt); }
}

export async function submitSpeech(
  client: SpeechWorkflowApi, mode: SpeechMode, checkpoint: SpeechCheckpoint, mimeType: string,
  onStage: (stage: SpeechStage) => void,
  onPerception: (perception: PerceptionRun) => void,
  startedAt = Date.now(),
  onAnalysis: (analysis: SpeechAnalysis) => void = () => {},
  onInterpretation?: (interpretation: ContextualInterpretationRun) => void,
): Promise<SpeechSubmission> {
  let failure: SpeechFailure = 'upload';
  try {
    if (!checkpoint.utteranceId) {
      onStage('uploading');
      checkpoint.utteranceId = (await measureSpeech('utterance upload', () =>
        client.uploadUtterance(checkpoint.uri, mimeType))).id;
    }
    const startAnalysis = () => checkpoint.analysis ??= (async () => {
      const identity = { utteranceId: checkpoint.utteranceId!, perceptionId: checkpoint.perception!.id,
        ...(mode.responseMode === 'none' && mode.targetId ? { targetId: mode.targetId } : {}) };
      const publish = (value: SpeechAnalysis) => {
        checkpoint.feedback = { ...value, ...(checkpoint.pronunciation ? { pronunciation: checkpoint.pronunciation } : {}) };
        onAnalysis(checkpoint.feedback);
      };
      publish({ ...identity, state: 'processing' });
      let complete = false;
      let readings: PerceivedReadings | undefined;
      try {
        void client.getPerceivedReadings?.(checkpoint.perception!.id).then(value => {
          readings = value;
          if (!complete) publish({ ...identity, state: 'processing', readings });
        }).catch(() => {});
        const perceived = await measureSpeech('transcript-conditioned analysis total', () =>
          client.analyzePerceivedSpeech(checkpoint.perception!.id));
        complete = true;
        publish({ ...identity, receivedAt: Date.now(), startedAt,
          state: perceived.status === 'failed' ? 'failed' : 'ready', perceived });
        if (perceived.data.pitch_status === 'available') logTiming('total time to chart available', startedAt);
      } catch {
        complete = true;
        publish({ ...identity, state: 'failed', ...(readings ? { readings } : {}) });
      }
    })();
    failure = 'perception';
    if (!checkpoint.perception) {
      onStage('perceiving');
      checkpoint.perception = await measureSpeech('perception', () =>
        client.createPerception(checkpoint.utteranceId!));
    }
    const perception = checkpoint.perception;
    if (perception.status === 'failed' || !perception.transcript?.trim()) {
      delete checkpoint.perception;
      throw new SpeechSubmissionError(recordingRejection(perception.error_code) ?? 'perception');
    }
    // Keep existing target-attempt persistence independent from the perceived graph.
    // Target evidence can supply comparison metadata, never graph units or pitch.
    if (mode.responseMode === 'none' && mode.targetId) {
      const targetId = mode.targetId;
      checkpoint.targetAnalysis ??= (async () => {
        try {
          checkpoint.attemptId ??= (await client.createAttempt(checkpoint.utteranceId!, targetId)).id;
          checkpoint.pronunciation = await client.analyzePronunciation(checkpoint.attemptId);
          if (checkpoint.feedback) {
            checkpoint.feedback = { ...checkpoint.feedback, pronunciation: checkpoint.pronunciation };
            onAnalysis(checkpoint.feedback);
          }
        } catch { /* Optional target evidence cannot hide perceived pitch. */ }
      })();
    }
    onPerception(perception);
    logTiming('total time to heard transcript', startedAt);
    // The free-speech reference is now durable. Analysis and meaning branch independently.
    startAnalysis();
    if (mode.responseMode === 'conversation') {
      failure = 'response';
      onStage('responding');
      const conversation = await measureSpeech('interpretation/generation', () =>
        client.addConversationUserTurn(mode.conversationId, checkpoint.utteranceId!, perception.id, onInterpretation));
      logTiming('total time to assistant text', startedAt);
      return { perception, conversation };
    }
    return { perception };
  } catch (error) {
    if (error && typeof error === 'object' && 'code' in error) {
      const rejection = recordingRejection(error.code);
      if (rejection) throw new SpeechSubmissionError(rejection);
    }
    if (error instanceof SpeechSubmissionError) throw error;
    throw new SpeechSubmissionError(failure);
  }
}
