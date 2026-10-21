import { mediaFetch, readAudioResponse } from '@/audio/audioTransport';
import { createRecordingUploadSource } from '@/audio/recordingUploadSource';
import { resetAudioSession } from '@/audio/session';
import type { AudioDownload } from '@/audio/useCachedAudio';
import type {
  ApiErrorPayload,
  AcousticRun,
  AssessmentRun,
  AssistantSpeechRun,
  AttemptComparison,
  AuthToken,
  Conversation,
  ConversationTurn,
  ConversationStreamEvent,
  ContextualInterpretationRun,
  FreeTalkTurn,
  PerceptionRun,
  PerceivedSpeechAnalysis,
  PerceivedReadings,
  PracticeSession,
  PronunciationAttempt,
  PronunciationResult,
  PronunciationTarget,
  ReferenceSpeech,
  UserCorrection,
  Utterance,
} from '@/api/types';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';

type FetchImplementation = (input: string, init?: RequestInit) => Promise<Response>;

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly retryable: boolean,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class BenmaApiClient {
  private token: string | null = null;
  readonly baseUrl: string;

  constructor(baseUrl = process.env.EXPO_PUBLIC_BENMA_API_URL ?? DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  setToken(token: string | null): void {
    const changed = this.token !== token;
    this.token = token;
    if (changed) resetAudioSession();
  }

  private async request<T>(
    path: string,
    init: RequestInit = {},
    fetchImplementation: FetchImplementation = globalThis.fetch,
  ): Promise<T> {
    const response = await this.fetchResponse(path, init, fetchImplementation);
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  private async fetchResponse(
    path: string,
    init: RequestInit = {},
    fetchImplementation: FetchImplementation = globalThis.fetch,
  ): Promise<Response> {
    const headers = new Headers(init.headers);
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`);
    if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    const response = await fetchImplementation(`${this.baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      let payload: ApiErrorPayload | null = null;
      try {
        payload = (await response.json()) as ApiErrorPayload;
      } catch {
        // Stable fallback below; never expose a provider response body.
      }
      throw new ApiError(
        payload?.error?.code ?? 'internal_failure',
        payload?.error?.message ?? `Request failed with HTTP ${response.status}`,
        payload?.error?.retryable ?? response.status >= 500,
        payload?.error?.request_id,
      );
    }
    if (__DEV__) {
      const timing = response.headers?.get('Server-Timing');
      // Allow only known metric names and numeric values into development logs.
      for (const match of timing?.matchAll(/(interpretation|generation);dur=(\d+(?:\.\d+)?)/g) ?? []) {
        console.info(`[speech timing] ${match[1]} ms:`, Number(match[2]));
      }
    }
    return response;
  }

  devAuth(phoneNumber: string): Promise<AuthToken> {
    return this.request('/v1/dev/auth', {
      method: 'POST',
      body: JSON.stringify({ phone_number: phoneNumber }),
    });
  }

  me(): Promise<{ id: string; status: string }> {
    return this.request('/v1/me');
  }

  revokeSession(): Promise<void> {
    return this.request('/v1/auth/session', { method: 'DELETE' });
  }

  createPracticeSession(
    mode: 'perception_test' | 'pronunciation',
    metadata: Record<string, unknown> = {},
  ): Promise<PracticeSession> {
    return this.request('/v1/practice-sessions', {
      method: 'POST',
      body: JSON.stringify({ mode, metadata }),
    });
  }

  async uploadUtterance(
    uri: string,
    mimeType: string,
    practiceSessionId?: string,
  ): Promise<Utterance> {
    const source = await createRecordingUploadSource(uri, mimeType);
    try {
      if (practiceSessionId) source.body.append('practice_session_id', practiceSessionId);
      return await this.request('/v1/utterances', { method: 'POST', body: source.body }, source.fetch);
    } finally {
      source.release();
    }
  }

  listUtterances(): Promise<Utterance[]> {
    return this.request('/v1/utterances');
  }

  createPerception(utteranceId: string): Promise<PerceptionRun> {
    return this.request(`/v1/utterances/${utteranceId}/perceptions`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  analyzePerceivedSpeech(perceptionId: string, devLearnedTargetId?: string): Promise<PerceivedSpeechAnalysis> {
    return this.request(`/v1/perceptions/${perceptionId}/speech-analysis`, {
      method: 'POST', body: JSON.stringify(devLearnedTargetId ? { dev_learned_target_id: devLearnedTargetId } : {}),
    });
  }

  getPerceivedSpeechAnalysis(analysisId: string): Promise<PerceivedSpeechAnalysis> {
    return this.request(`/v1/perceived-speech-analyses/${analysisId}`);
  }

  getPerceivedReadings(perceptionId: string): Promise<PerceivedReadings> {
    return this.request(`/v1/perceptions/${perceptionId}/readings`);
  }

  analyzeAcoustics(utteranceId: string): Promise<AcousticRun> {
    return this.request(`/v1/utterances/${utteranceId}/acoustics`, { method: 'POST' });
  }

  createConversation(): Promise<Conversation> {
    return this.request('/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  listConversationTurns(conversationId: string): Promise<ConversationTurn[]> {
    return this.request(`/v1/conversations/${conversationId}/turns`);
  }

  async addConversationUserTurn(
    conversationId: string,
    utteranceId: string,
    perceptionRunId: string,
    onInterpretation?: (interpretation: ContextualInterpretationRun) => void,
  ): Promise<FreeTalkTurn> {
    if (onInterpretation) {
      const response = await this.fetchResponse(`/v1/conversations/${conversationId}/user-turns/stream`, {
        method: 'POST',
        body: JSON.stringify({ utterance_id: utteranceId, perception_run_id: perceptionRunId }),
      }, mediaFetch);
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Conversation progress unavailable');
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        while (true) {
          const chunk = await reader.read();
          buffer += decoder.decode(chunk.value, { stream: !chunk.done });
          let boundary: number;
          while ((boundary = buffer.indexOf('\n')) >= 0) {
            const line = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 1);
            if (!line.trim()) continue;
            const event = JSON.parse(line) as ConversationStreamEvent;
            if (__DEV__) {
              if (typeof event.interpretation_ms === 'number') console.info('[speech timing] interpretation server compute ms:', event.interpretation_ms);
              if (typeof event.generation_ms === 'number') console.info('[speech timing] generation server compute ms:', event.generation_ms);
            }
            if (event.type === 'interpretation' && event.interpretation?.perception_run_id === perceptionRunId) {
              onInterpretation(event.interpretation);
            } else if (event.type === 'complete' && event.result?.perception_run_id === perceptionRunId) {
              return event.result;
            } else if (event.type === 'error') {
              throw new Error('Conversation response unavailable');
            }
          }
          if (chunk.done) throw new Error('Conversation progress ended before completion');
        }
      } finally { await reader.cancel().catch(() => {}); }
    }
    return this.request(`/v1/conversations/${conversationId}/user-turns`, {
      method: 'POST',
      body: JSON.stringify({
        utterance_id: utteranceId,
        perception_run_id: perceptionRunId,
      }),
    });
  }

  createAssistantSpeech(generationId: string): Promise<AssistantSpeechRun> {
    return this.request(`/v1/assistant-generations/${generationId}/speech`, {
      method: 'POST', body: JSON.stringify({}),
    });
  }

  protectedAudioPath(uri: string): string {
    const path = uri.startsWith(`${this.baseUrl}/`) ? uri.slice(this.baseUrl.length) : uri;
    if (!/^\/v1\/(assistant-speeches|reference-speech|utterances)\/[A-Za-z0-9_-]{1,128}\/audio$/.test(path)) {
      throw new Error('Invalid protected audio path');
    }
    return path;
  }

  async downloadCanonicalRecording(utteranceId: string): Promise<Uint8Array> {
    const path = this.protectedAudioPath(`/v1/utterances/${utteranceId}/audio`);
    const response = await this.fetchResponse(`${path}?canonical=true`, {}, mediaFetch);
    return (await readAudioResponse(response)).bytes;
  }

  downloadAssistantSpeech(path: string): Promise<Uint8Array> {
    return this.downloadAudio(path);
  }

  async downloadAudio(path: string): Promise<Uint8Array> {
    return (await this.downloadAudioFile(path)).bytes;
  }

  async downloadAudioFile(path: string): Promise<AudioDownload> {
    const response = await this.fetchResponse(this.protectedAudioPath(path), {}, mediaFetch);
    return readAudioResponse(response);
  }

  createCorrection(
    utteranceId: string,
    perceptionRunId: string,
    intendedText: string,
  ): Promise<UserCorrection> {
    return this.request(`/v1/utterances/${utteranceId}/corrections`, {
      method: 'POST',
      body: JSON.stringify({ intended_text: intendedText, perception_run_id: perceptionRunId }),
    });
  }

  createTarget(text: string): Promise<PronunciationTarget> {
    return this.request('/v1/pronunciation-targets', {
      method: 'POST',
      body: JSON.stringify({ text, target_source: 'manual' }),
    });
  }

  correctTargetPinyin(targetId: string, pinyin: string): Promise<PronunciationTarget> {
    return this.request(`/v1/pronunciation-targets/${targetId}/pinyin-corrections`, {
      method: 'POST',
      body: JSON.stringify({ pinyin }),
    });
  }

  createReferenceSpeech(targetId: string, force = false): Promise<ReferenceSpeech> {
    return this.request(`/v1/pronunciation-targets/${targetId}/reference-speech`, {
      method: 'POST',
      body: JSON.stringify({ force }),
    });
  }

  createAttempt(utteranceId: string, targetId: string): Promise<PronunciationAttempt> {
    return this.request('/v1/pronunciation-attempts', {
      method: 'POST',
      body: JSON.stringify({ utterance_id: utteranceId, target_id: targetId }),
    });
  }

  getAttempt(attemptId: string): Promise<PronunciationAttempt> {
    return this.request(`/v1/pronunciation-attempts/${attemptId}`);
  }

  createAssessment(attemptId: string): Promise<AssessmentRun> {
    return this.request(`/v1/pronunciation-attempts/${attemptId}/assessments`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  analyzePronunciation(
    attemptId: string,
    rerun = false,
  ): Promise<PronunciationResult> {
    return this.request(`/v1/pronunciation-attempts/${attemptId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({
        reuse_existing: !rerun,
        rerun_provider: rerun,
        rerun_acoustics: rerun,
        rerun_alignment: rerun,
      }),
    });
  }

  getPronunciationResult(attemptId: string): Promise<PronunciationResult> {
    return this.request(`/v1/pronunciation-attempts/${attemptId}/result`);
  }

  listPronunciationAttempts(targetId: string): Promise<PronunciationResult[]> {
    return this.request(`/v1/pronunciation-targets/${targetId}/attempts`);
  }

  comparePronunciationAttempts(firstAttemptId: string, secondAttemptId: string) {
    return this.request<AttemptComparison>('/v1/pronunciation-attempts/compare', {
      method: 'POST',
      body: JSON.stringify({
        first_attempt_id: firstAttemptId,
        second_attempt_id: secondAttemptId,
      }),
    });
  }

  absoluteUrl(path: string): string {
    return path.startsWith('http') ? path : `${this.baseUrl}${path}`;
  }

  authenticatedHeaders(): Record<string, string> | undefined {
    return this.token ? { Authorization: `Bearer ${this.token}` } : undefined;
  }

  audioUrl(utterance: Utterance): string {
    return `${this.baseUrl}${utterance.audio_url}`;
  }
}

export const api = new BenmaApiClient();
