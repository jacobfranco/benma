import type { components } from '@/api/openapi.generated';

type Schemas = components['schemas'];

export type ApiErrorPayload = Schemas['ErrorResponse'];
export type AuthToken = Schemas['AuthTokenResponse'];
export type PracticeSession = Schemas['PracticeSessionResponse'];
export type AudioAsset = Schemas['AudioAssetResponse'];
export type Utterance = Schemas['UtteranceResponse'];
export type PerceptionRun = Schemas['PerceptionRunResponse'];
export type ContextualInterpretationRun = Schemas['ContextualInterpretationRunResponse'];
export type Conversation = Schemas['ConversationResponse'];
export type ConversationTurn = Schemas['ConversationTurnResponse'];
export type UserCorrection = Schemas['UserCorrectionResponse'];
export type PronunciationTarget = Schemas['PronunciationTargetResponse'];
export type PronunciationAttempt = Schemas['PronunciationAttemptResponse'];
export type ReferenceSpeech = Schemas['ReferenceSpeechResponse'];
export type AcousticRun = Schemas['AcousticRunResponse'];
export type AlignmentRun = Schemas['AlignmentRunResponse'];
export type InterpretationRun = Schemas['InterpretationRunResponse'];
export type PronunciationSyllable = Schemas['PronunciationSyllableResult'];
export type PronunciationResult = Schemas['PronunciationResultResponse'];
export type AttemptComparison = Schemas['AttemptComparisonResponse'];

export interface SyllableEvidence {
  text?: string;
  pinyin?: string;
  pronunciation_score?: number;
  detected_tone?: number;
  reference_tone?: number;
  tone_score?: number;
  phones?: Record<string, unknown>[];
  provider_errors?: string[];
}

export interface NormalizedAssessment {
  evidence_status: 'synthetic_replay' | 'live_provider' | string;
  overall_score?: number;
  pronunciation_score?: number;
  fluency_score?: number;
  completeness_score?: number;
  syllables?: SyllableEvidence[];
  unsupported_capabilities?: string[];
}

export type AssessmentRun = Omit<Schemas['AssessmentRunResponse'], 'normalized_result'> & {
  normalized_result: NormalizedAssessment | null;
};
