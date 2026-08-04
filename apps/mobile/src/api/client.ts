import type {
  ApiErrorPayload,
  AssessmentRun,
  AttemptComparison,
  AuthToken,
  PerceptionRun,
  PracticeSession,
  PronunciationAttempt,
  PronunciationResult,
  PronunciationTarget,
  ReferenceSpeech,
  UserCorrection,
  Utterance,
} from '@/api/types';

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';

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
    this.token = token;
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`);
    if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      let payload: ApiErrorPayload | null = null;
      try {
        payload = (await response.json()) as ApiErrorPayload;
      } catch {
        // Stable fallback below; never expose a provider response body.
      }
      throw new ApiError(
        payload?.error.code ?? 'internal_failure',
        payload?.error.message ?? `Request failed with HTTP ${response.status}`,
        payload?.error.retryable ?? response.status >= 500,
        payload?.error.request_id,
      );
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
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
    practiceSessionId: string,
  ): Promise<Utterance> {
    const body = new FormData();
    const extension = mimeType === 'audio/webm' ? 'webm' : 'm4a';
    body.append('file', { uri, name: `recording.${extension}`, type: mimeType } as unknown as Blob);
    body.append('practice_session_id', practiceSessionId);
    return this.request('/v1/utterances', { method: 'POST', body });
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
