import type { BenmaApiClient } from '@/api/client';
import type { PerceivedReadings, PerceivedSpeechAnalysis, ContextualInterpretationRun, FreeTalkTurn, PerceptionRun, PronunciationResult } from '@/api/types';

export type SpeechStage = 'stopping' | 'uploading' | 'perceiving' | 'responding' | 'assessing';
export type SpeechFailure = 'recording' | 'upload' | 'perception' | 'response' | 'assessment';
export const speechStageLabels: Record<SpeechStage, string> = {
  stopping: 'Finishing recording…', uploading: 'Sending recording…',
  perceiving: 'Processing speech…', responding: 'Understanding meaning…',
  assessing: 'Analyzing pronunciation…',
};
export const speechFailureLabels: Record<SpeechFailure, string> = {
  recording: 'Recording interrupted. Please record again.',
  upload: 'Upload failed. Try sending the recording again.',
  perception: 'Could not understand speech. Try again or make a new recording.',
  response: 'Response unavailable. You can keep talking.',
  assessment: 'Speech feedback unavailable. Try analysis again.',
};
export class SpeechSubmissionError extends Error {
  constructor(public readonly stage: SpeechFailure) { super(speechFailureLabels[stage]); }
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
    // These are independent public resources. Internal pronunciation evidence
    // fan-out and persistence belong to the server's analyze workflow.
    // Attach failure handling immediately and retain the promise across retries.
    const startAnalysis = () => checkpoint.analysis ??= (async () => {
      const utteranceId = checkpoint.utteranceId!;
      const identity = { utteranceId,
        ...(mode.responseMode === 'none' && mode.targetId ? { targetId: mode.targetId }
          : { perceptionId: checkpoint.perception!.id }) };
      onAnalysis({ ...identity, state: 'processing' });
      let complete = false;
      let readings: PerceivedReadings | undefined;
      try {
        if (mode.responseMode === 'none' && mode.targetId) {
          checkpoint.attemptId ??= (await client.createAttempt(utteranceId, mode.targetId)).id;
          const pronunciation = await measureSpeech('target-analysis branch wall', () =>
            client.analyzePronunciation(checkpoint.attemptId!));
          if (__DEV__) {
            for (const [branch, run] of Object.entries({ assessment: pronunciation.assessment,
              acoustic: pronunciation.acoustic, alignment: pronunciation.alignment })) {
              if (typeof run?.latency_ms === 'number') console.info(`[speech timing] ${branch} server compute ms:`, run.latency_ms);
            }
            if (typeof pronunciation.overall_evidence?.analysis_wall_ms === 'number') {
              console.info('[speech timing] target-analysis server wall ms:', pronunciation.overall_evidence.analysis_wall_ms);
            }
          }
          onAnalysis({ ...identity, state: 'ready', pronunciation });
        } else {
          void client.getPerceivedReadings?.(checkpoint.perception!.id).then(value => {
            readings = value;
            if (!complete) onAnalysis({ ...identity, state: 'processing', readings });
          }).catch(() => {});
          const requestStarted = Date.now();
          const perceived = await measureSpeech('transcript-conditioned analysis total', () =>
            client.analyzePerceivedSpeech(checkpoint.perception!.id));
          if (__DEV__) {
            console.info('[speech timing] pitch extraction server ms:', perceived.data.pitch_latency_ms);
            console.info('[speech timing] alignment server ms:', perceived.data.alignment_latency_ms);
            console.info('[speech timing] transcript analysis server ms:', perceived.latency_ms);
            console.info('[speech timing] request overhead ms (includes queue/serialization):', Math.max(0, Date.now()-requestStarted-perceived.latency_ms));
            console.info('[speech timing] analysis stage ms:', perceived.data.timings_ms);
          }
          complete = true;
          onAnalysis({ ...identity, receivedAt: Date.now(), startedAt, state: perceived.status === 'failed' ? 'failed' : 'ready', perceived });
          if (perceived.data.pitch_status === 'available') logTiming('total time to chart available', startedAt);
        }
      } catch { complete = true; onAnalysis({ ...identity, state: 'failed', ...(readings ? { readings } : {}) }); }
    })();
    if (mode.responseMode === 'none' && mode.targetId) startAnalysis();
    failure = 'perception';
    if (!checkpoint.perception) {
      onStage('perceiving');
      checkpoint.perception = await measureSpeech('perception', () =>
        client.createPerception(checkpoint.utteranceId!));
    }
    const perception = checkpoint.perception;
    if (perception.status === 'failed' || !perception.transcript?.trim()) {
      delete checkpoint.perception;
      throw new SpeechSubmissionError('perception');
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
    if (error instanceof SpeechSubmissionError) throw error;
    throw new SpeechSubmissionError(failure);
  }
}
